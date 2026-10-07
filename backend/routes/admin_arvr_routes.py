"""
Admin 后台 AR/VR 课程管理 API 路由

提供管理员后台对 AR/VR 课程的完整 CRUD + 文件上传能力：
- GET    /api/v1/admin/arvr/courses                 列出课程（支持过滤/分页）
- POST   /api/v1/admin/arvr/courses                 创建课程（支持同时上传构建/缩略图）
- GET    /api/v1/admin/arvr/courses/{course_id}     课程详情
- PUT    /api/v1/admin/arvr/courses/{course_id}     更新课程元数据
- DELETE /api/v1/admin/arvr/courses/{course_id}     删除课程（含构建/缩略图文件）
- PATCH  /api/v1/admin/arvr/courses/{course_id}/status  切换 is_active
- POST   /api/v1/admin/arvr/courses/{course_id}/upload-build      上传/替换构建文件
- POST   /api/v1/admin/arvr/courses/{course_id}/upload-thumbnail  上传/替换缩略图
- GET    /api/v1/admin/arvr/courses/{course_id}/statistics        课程统计
- GET    /api/v1/admin/arvr/stats                                  全局统计

设计要点:
1. 使用异步数据库会话 (AsyncSession + get_db) 以匹配其他路由
2. 使用 Bearer JWT 鉴权 + 管理员角色校验（User.is_admin）
3. 文件写入路径复用 ARVRContentService 中的目录约定（保证前端静态路径一致）
4. 默认 org_id=1（MatuX 自有租户），与前端 ARVRCoursePlayerComponent 行为一致

Author: Admin 后台补齐
"""

import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import get_current_user
from models.ar_vr_content import (
    ARVRContent,
    ARVRContentResponse,
    ARVRContentType,
    ARVRContentUpdate,
    ARVRPlatform,
)
from models.user import User, UserRole
from utils.database import get_db

logger = logging.getLogger(__name__)


# ==================== Admin 鉴权依赖 ====================


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """校验当前用户为管理员（admin / org_admin / superuser 任意一种）"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已停用",
        )

    if current_user.is_admin() or current_user.is_superuser:
        return current_user

    # 检查 RBAC 角色（适配新权限模型）
    if current_user.has_any_role(
        [UserRole.ADMIN, UserRole.ORG_ADMIN, UserRole.SCHOOL_ADMIN]
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要管理员权限才能访问 AR/VR 课程管理后台",
    )


# ==================== 路由前缀 ====================

router = APIRouter(
    prefix="/api/v1/admin/arvr",
    tags=["Admin - AR/VR 课程管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"},
    },
)


# ==================== 内部常量 ====================


DEFAULT_ORG_ID = 1  # 与前端 ARVRCoursePlayerComponent 保持一致
MAX_BUILD_SIZE_BYTES = 500 * 1024 * 1024  # 500MB
MAX_THUMBNAIL_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_BUILD_EXT = {".zip"}
ALLOWED_THUMB_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _get_arvr_paths():
    """
    获取 AR/VR 静态文件路径常量（不依赖 DB session 类型）

    Returns:
        (build_output_path, thumbnail_path)
    """
    base = os.path.join(os.getcwd(), "arvr_contents")
    return (
        os.path.join(base, "builds"),
        os.path.join(base, "thumbnails"),
    )


# ==================== Pydantic 响应模型 ====================


class AdminCourseListItem(BaseModel):
    """后台课程列表项"""

    id: int
    title: str
    description: Optional[str] = None
    content_type: str
    platform: str
    course_id: int
    lesson_id: Optional[int] = None
    build_file_url: Optional[str] = None
    manifest_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_active: bool
    is_public: bool
    is_featured: bool
    view_count: int
    completion_count: int
    average_rating: float
    file_size: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class AdminCourseListResponse(BaseModel):
    """后台课程列表分页响应"""

    items: List[AdminCourseListItem]
    total: int
    page: int
    page_size: int


class UploadResult(BaseModel):
    """文件上传结果"""

    success: bool
    course_id: int
    build_file_url: Optional[str] = None
    manifest_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    estimated_load_time: Optional[float] = None
    message: str


class AdminCourseStats(BaseModel):
    """后台课程统计"""

    total_courses: int
    active_courses: int
    inactive_courses: int
    featured_courses: int
    by_content_type: Dict[str, int] = Field(default_factory=dict)
    by_platform: Dict[str, int] = Field(default_factory=dict)
    total_size_bytes: int = 0
    total_view_count: int = 0
    total_completion_count: int = 0
    avg_rating: float = 0.0


# ==================== 辅助函数 ====================


def _enum_value(value: Any) -> str:
    """枚举 -> 字符串（兼容 str 枚举 / Enum）"""
    if value is None:
        return ""
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _arvr_content_to_dict(content: ARVRContent) -> Dict[str, Any]:
    """ARVRContent -> 字典（保证所有 enum 字段可序列化）"""
    return {
        "id": content.id,
        "org_id": content.org_id,
        "course_id": content.course_id,
        "lesson_id": content.lesson_id,
        "title": content.title,
        "description": content.description,
        "content_type": _enum_value(content.content_type),
        "platform": _enum_value(content.platform),
        "build_file_url": content.build_file_url,
        "manifest_url": content.manifest_url,
        "thumbnail_url": content.thumbnail_url,
        "config": content.config,
        "required_sensors": content.required_sensors or [],
        "interaction_modes": content.interaction_modes or [],
        "compatibility_info": content.compatibility_info,
        "file_size": content.file_size,
        "estimated_load_time": content.estimated_load_time,
        "performance_profile": content.performance_profile,
        "is_public": bool(content.is_public),
        "access_level": content.access_level,
        "required_permissions": content.required_permissions,
        "custom_metadata": content.custom_metadata,
        "tags": content.tags or [],
        "view_count": content.view_count or 0,
        "completion_count": content.completion_count or 0,
        "average_rating": content.average_rating or 0.0,
        "is_active": bool(content.is_active),
        "is_featured": bool(content.is_featured),
        "created_at": (
            content.created_at.isoformat() if content.created_at else None
        ),
        "updated_at": (
            content.updated_at.isoformat() if content.updated_at else None
        ),
    }


async def _save_upload(
    upload: UploadFile, dest_path: str, max_size: int
) -> int:
    """
    保存 UploadFile 到目标路径，限制大小，返回写入字节数

    Raises:
        HTTPException: 文件超过大小限制或写入失败
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    total = 0
    chunk_size = 1024 * 1024  # 1MB
    try:
        async with aiofiles.open(dest_path, "wb") as out:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_size:
                    # 超限：删半成品并抛错
                    await out.close()
                    try:
                        os.remove(dest_path)
                    except OSError:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件超过大小限制 {max_size} 字节",
                    )
                await out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存上传文件失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {e}",
        )
    finally:
        await upload.close()
    return total


def _ensure_extension(filename: str, allowed: set) -> str:
    """校验文件后缀，返回标准化小写后缀"""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名为空",
        )
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型 {ext}, 允许: {', '.join(sorted(allowed))}",
        )
    return ext


def _safe_filename(filename: str) -> str:
    """去除路径分隔符，避免路径穿越"""
    base = os.path.basename(filename or "")
    return base.replace(" ", "_")


# ==================== API 端点 ====================


@router.get(
    "/courses",
    response_model=AdminCourseListResponse,
    summary="列出 AR/VR 课程",
)
async def list_admin_arvr_courses(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="标题/描述关键字"),
    content_type: Optional[ARVRContentType] = Query(
        None, description="按内容类型过滤",
    ),
    platform: Optional[ARVRPlatform] = Query(None, description="按平台过滤"),
    is_active: Optional[bool] = Query(None, description="按启用状态过滤"),
    is_featured: Optional[bool] = Query(None, description="按精选过滤"),
    course_id: Optional[int] = Query(None, description="按课程 ID 过滤"),
    org_id: int = Query(DEFAULT_ORG_ID, description="组织 ID"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    后台列出 AR/VR 课程（分页 + 多条件过滤）
    """
    try:
        conditions = [ARVRContent.org_id == org_id]
        if keyword:
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    ARVRContent.title.ilike(like),
                    ARVRContent.description.ilike(like),
                )
            )
        if content_type is not None:
            conditions.append(ARVRContent.content_type == content_type)
        if platform is not None:
            conditions.append(ARVRContent.platform == platform)
        if is_active is not None:
            conditions.append(ARVRContent.is_active == is_active)
        if is_featured is not None:
            conditions.append(ARVRContent.is_featured == is_featured)
        if course_id is not None:
            conditions.append(ARVRContent.course_id == course_id)

        # 总数
        count_stmt = (
            select(func.count(ARVRContent.id)).where(and_(*conditions))
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        # 分页数据（Query 对象需显式转 int，避免 SQLAlchemy 类型错误）
        offset = (int(page) - 1) * int(page_size)
        stmt = (
            select(ARVRContent)
            .where(and_(*conditions))
            .order_by(ARVRContent.created_at.desc())
            .offset(offset)
            .limit(int(page_size))
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        items = [AdminCourseListItem(**_arvr_content_to_dict(r)) for r in rows]
        return AdminCourseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"列出 AR/VR 课程失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出课程失败: {e}",
        )


@router.post(
    "/courses",
    response_model=AdminCourseListItem,
    summary="创建 AR/VR 课程",
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_arvr_course(
    course_id: int = Form(..., description="关联课程 ID"),
    title: str = Form(..., min_length=1, max_length=255),
    content_type: ARVRContentType = Form(..., description="内容类型"),
    platform: ARVRPlatform = Form(..., description="目标平台"),
    description: Optional[str] = Form(None),
    lesson_id: Optional[int] = Form(None),
    access_level: str = Form("course"),
    is_public: bool = Form(False),
    is_featured: bool = Form(False),
    tags: Optional[str] = Form(
        None, description="标签 JSON 字符串或逗号分隔",
    ),
    config_json: Optional[str] = Form(
        None, description="config 的 JSON 字符串",
    ),
    required_sensors_json: Optional[str] = Form(
        None, description="所需传感器列表 JSON",
    ),
    interaction_modes_json: Optional[str] = Form(
        None, description="交互模式列表 JSON",
    ),
    custom_metadata_json: Optional[str] = Form(
        None, description="自定义元数据 JSON",
    ),
    build_file: Optional[UploadFile] = File(
        None, description="Unity WebGL 构建 ZIP（可选）",
    ),
    thumbnail_file: Optional[UploadFile] = File(
        None, description="缩略图文件（可选）",
    ),
    org_id: int = Form(DEFAULT_ORG_ID),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    创建 AR/VR 课程。

    可同时上传构建包（ZIP）和缩略图。如后续需要替换，可调用
    /courses/{id}/upload-build 与 /courses/{id}/upload-thumbnail。
    """
    try:
        import json

        def _parse_json(raw: Optional[str], field: str) -> Any:
            if raw is None or raw == "":
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field} 不是合法 JSON: {e}",
                )

        def _parse_tags(raw: Optional[str]) -> Optional[List[str]]:
            if raw is None or raw == "":
                return None
            # 支持 JSON 数组 / 逗号分隔字符串
            parsed = _parse_json(raw, "tags")
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
            return [t.strip() for t in raw.split(",") if t.strip()]

        config = _parse_json(config_json, "config_json")
        required_sensors = _parse_json(required_sensors_json, "required_sensors_json")
        interaction_modes = _parse_json(interaction_modes_json, "interaction_modes_json")
        custom_metadata = _parse_json(custom_metadata_json, "custom_metadata_json")
        tag_list = _parse_tags(tags)

        # 1. 创建数据库记录
        content = ARVRContent(
            org_id=org_id,
            course_id=course_id,
            lesson_id=lesson_id,
            title=title,
            description=description,
            content_type=content_type,
            platform=platform,
            is_public=is_public,
            access_level=access_level,
            is_featured=is_featured,
            tags=tag_list or [],
            config=config or {},
            required_sensors=required_sensors or [],
            interaction_modes=interaction_modes or [],
            custom_metadata=custom_metadata or {},
            is_active=True,
        )
        db.add(content)
        await db.flush()  # 获取 content.id
        course_pk = content.id

        # 2. 处理构建文件
        if build_file is not None:
            ext = _ensure_extension(build_file.filename, ALLOWED_BUILD_EXT)
            build_dir_base, _ = _get_arvr_paths()
            build_dir = os.path.join(build_dir_base, f"content_{course_pk}")
            os.makedirs(build_dir, exist_ok=True)
            zip_path = os.path.join(build_dir, f"build_{course_pk}{ext}")
            size = await _save_upload(build_file, zip_path, MAX_BUILD_SIZE_BYTES)
            # 解压
            try:
                await _extract_zip(zip_path, os.path.join(build_dir, "extracted"))
                final_build = _find_unity_build_dir(
                    os.path.join(build_dir, "extracted")
                )
                if final_build:
                    final = os.path.join(build_dir, "build")
                    if os.path.exists(final):
                        shutil.rmtree(final)
                    shutil.move(final_build, final)
                    total_size = _dir_size(final)
                    content.build_file_url = (
                        f"/arvr/builds/content_{course_pk}/build/index.html"
                    )
                    content.manifest_url = (
                        f"/arvr/builds/content_{course_pk}/build/Build/"
                        f"content_{course_pk}.json"
                    )
                    content.file_size = total_size or size
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="未在 ZIP 中找到 Unity WebGL 构建目录（含 index.html）",
                    )
            finally:
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                except OSError:
                    pass

        # 3. 处理缩略图
        if thumbnail_file is not None:
            ext = _ensure_extension(thumbnail_file.filename, ALLOWED_THUMB_EXT)
            _, thumb_dir = _get_arvr_paths()
            os.makedirs(thumb_dir, exist_ok=True)
            fname = f"thumb_{course_pk}{ext}"
            dest = os.path.join(thumb_dir, fname)
            await _save_upload(thumbnail_file, dest, MAX_THUMBNAIL_SIZE_BYTES)
            content.thumbnail_url = f"/arvr/thumbnails/{fname}"

        content.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(content)

        logger.info(
            f"AR/VR 课程已创建: id={content.id}, title={content.title}, "
            f"operator_admin={True}"
        )
        return AdminCourseListItem(**_arvr_content_to_dict(content))

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建 AR/VR 课程失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建课程失败: {e}",
        )


@router.get(
    "/courses/{course_id}",
    response_model=AdminCourseListItem,
    summary="获取 AR/VR 课程详情",
)
async def get_admin_arvr_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )
        return AdminCourseListItem(**_arvr_content_to_dict(content))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 AR/VR 课程详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取课程详情失败: {e}",
        )


@router.put(
    "/courses/{course_id}",
    response_model=AdminCourseListItem,
    summary="更新 AR/VR 课程元数据",
)
async def update_admin_arvr_course(
    course_id: int,
    payload: ARVRContentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    更新课程元数据（标题、描述、平台、config、tags、is_active 等）。

    文件相关字段（build_file_url、thumbnail_url）请使用专用上传端点。
    """
    try:
        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )

        update_fields = payload.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if field in ("required_sensors", "interaction_modes") and value:
                # 枚举值统一转字符串
                value = [
                    v.value if hasattr(v, "value") else str(v) for v in value
                ]
            if hasattr(content, field):
                setattr(content, field, value)

        content.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(content)
        logger.info(
            f"AR/VR 课程已更新: id={content.id}, fields={list(update_fields.keys())}"
        )
        return AdminCourseListItem(**_arvr_content_to_dict(content))

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新 AR/VR 课程失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新课程失败: {e}",
        )


@router.patch(
    "/courses/{course_id}/status",
    response_model=AdminCourseListItem,
    summary="切换课程启用状态",
)
async def toggle_admin_arvr_course_status(
    course_id: int,
    is_active: bool = Form(..., description="新的启用状态"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """快速切换 is_active，便于前端启用/下架课程"""
    try:
        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )
        content.is_active = is_active
        content.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(content)
        logger.info(
            f"AR/VR 课程状态切换: id={content.id}, is_active={is_active}"
        )
        return AdminCourseListItem(**_arvr_content_to_dict(content))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"切换课程状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换状态失败: {e}",
        )


@router.delete(
    "/courses/{course_id}",
    summary="删除 AR/VR 课程（含文件）",
)
async def delete_admin_arvr_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除课程记录，并清理构建包/缩略图文件"""
    try:
        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )

        build_dir_base, thumb_dir = _get_arvr_paths()

        # 删除构建文件目录
        if content.build_file_url:
            try:
                build_dir = os.path.join(
                    build_dir_base, f"content_{course_id}"
                )
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)
            except Exception as e:
                logger.warning(f"删除构建文件失败: {e}")

        # 删除缩略图
        if content.thumbnail_url:
            try:
                fname = os.path.basename(content.thumbnail_url)
                path = os.path.join(thumb_dir, fname)
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"删除缩略图失败: {e}")

        await db.delete(content)
        await db.commit()
        logger.info(f"AR/VR 课程已删除: id={course_id}")
        return {"success": True, "deleted_id": course_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除 AR/VR 课程失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除课程失败: {e}",
        )


@router.post(
    "/courses/{course_id}/upload-build",
    response_model=UploadResult,
    summary="上传/替换 Unity WebGL 构建包",
)
async def upload_admin_arvr_build(
    course_id: int,
    build_file: UploadFile = File(..., description="Unity WebGL ZIP 包"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """上传或替换课程构建 ZIP，自动解压并写入 build_file_url/manifest_url"""
    try:
        ext = _ensure_extension(build_file.filename, ALLOWED_BUILD_EXT)

        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )

        build_dir_base, _ = _get_arvr_paths()
        build_dir = os.path.join(build_dir_base, f"content_{course_id}")
        os.makedirs(build_dir, exist_ok=True)

        # 先清旧文件，避免残留
        old_build = os.path.join(build_dir, "build")
        if os.path.exists(old_build):
            shutil.rmtree(old_build)
        for f in os.listdir(build_dir):
            if f.startswith(f"build_{course_id}") and f.endswith(".zip"):
                try:
                    os.remove(os.path.join(build_dir, f))
                except OSError:
                    pass

        zip_path = os.path.join(build_dir, f"build_{course_id}{ext}")
        zip_size = await _save_upload(build_file, zip_path, MAX_BUILD_SIZE_BYTES)

        try:
            await _extract_zip(zip_path, os.path.join(build_dir, "extracted"))
            final_build = _find_unity_build_dir(
                os.path.join(build_dir, "extracted")
            )
            if not final_build:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="未在 ZIP 中找到 Unity WebGL 构建目录（含 index.html）",
                )
            final = os.path.join(build_dir, "build")
            if os.path.exists(final):
                shutil.rmtree(final)
            shutil.move(final_build, final)
            total_size = _dir_size(final)
        finally:
            try:
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except OSError:
                pass

        content.build_file_url = (
            f"/arvr/builds/content_{course_id}/build/index.html"
        )
        content.manifest_url = (
            f"/arvr/builds/content_{course_id}/build/Build/"
            f"content_{course_id}.json"
        )
        content.file_size = total_size or zip_size
        content.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(content)

        logger.info(
            f"AR/VR 课程构建已上传: id={course_id}, size={content.file_size}"
        )
        return UploadResult(
            success=True,
            course_id=course_id,
            build_file_url=content.build_file_url,
            manifest_url=content.manifest_url,
            file_size=content.file_size,
            message="构建包上传成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"上传构建包失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传构建包失败: {e}",
        )


@router.post(
    "/courses/{course_id}/upload-thumbnail",
    response_model=UploadResult,
    summary="上传/替换课程缩略图",
)
async def upload_admin_arvr_thumbnail(
    course_id: int,
    thumbnail_file: UploadFile = File(..., description="缩略图文件"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        ext = _ensure_extension(thumbnail_file.filename, ALLOWED_THUMB_EXT)

        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )

        _, thumb_dir = _get_arvr_paths()
        os.makedirs(thumb_dir, exist_ok=True)

        # 删除旧缩略图
        if content.thumbnail_url:
            try:
                old = os.path.join(
                    thumb_dir,
                    os.path.basename(content.thumbnail_url),
                )
                if os.path.exists(old):
                    os.remove(old)
            except OSError:
                pass

        fname = f"thumb_{course_id}{ext}"
        dest = os.path.join(thumb_dir, fname)
        size = await _save_upload(thumbnail_file, dest, MAX_THUMBNAIL_SIZE_BYTES)

        content.thumbnail_url = f"/arvr/thumbnails/{fname}"
        content.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(content)

        logger.info(
            f"AR/VR 课程缩略图已上传: id={course_id}, size={size}"
        )
        return UploadResult(
            success=True,
            course_id=course_id,
            thumbnail_url=content.thumbnail_url,
            file_size=size,
            message="缩略图上传成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"上传缩略图失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传缩略图失败: {e}",
        )


@router.get(
    "/courses/{course_id}/statistics",
    summary="课程统计",
)
async def get_admin_arvr_course_statistics(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        from models.ar_vr_content import ARVRInteractionLog, ARVRProgressTracking

        stmt = select(ARVRContent).where(ARVRContent.id == course_id)
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AR/VR 课程 {course_id} 不存在",
            )

        completion_stmt = (
            select(func.count(ARVRProgressTracking.id))
            .where(
                ARVRProgressTracking.content_id == course_id,
                ARVRProgressTracking.completed_at.isnot(None),
            )
        )
        completion_count = (await db.execute(completion_stmt)).scalar() or 0

        interaction_count = (
            await db.execute(
                select(func.count(ARVRInteractionLog.id))
                .where(ARVRInteractionLog.content_id == course_id)
            )
        ).scalar() or 0

        avg_rating = (
            await db.execute(
                select(func.avg(ARVRInteractionLog.feedback_score))
                .where(
                    ARVRInteractionLog.content_id == course_id,
                    ARVRInteractionLog.feedback_score.isnot(None),
                )
            )
        ).scalar() or 0.0

        return {
            "course_id": course_id,
            "view_count": content.view_count or 0,
            "completion_count": completion_count,
            "interaction_count": interaction_count,
            "average_rating": round(float(avg_rating), 2),
            "is_active": bool(content.is_active),
            "file_size": content.file_size,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取课程统计失败: {e}",
        )


@router.get(
    "/stats",
    response_model=AdminCourseStats,
    summary="AR/VR 课程全局统计",
)
async def get_admin_arvr_global_stats(
    org_id: int = Query(DEFAULT_ORG_ID, description="组织 ID"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        total = (
            await db.execute(
                select(func.count(ARVRContent.id)).where(
                    ARVRContent.org_id == org_id
                )
            )
        ).scalar() or 0
        active = (
            await db.execute(
                select(func.count(ARVRContent.id)).where(
                    ARVRContent.org_id == org_id,
                    ARVRContent.is_active == True,  # noqa: E712
                )
            )
        ).scalar() or 0
        featured = (
            await db.execute(
                select(func.count(ARVRContent.id)).where(
                    ARVRContent.org_id == org_id,
                    ARVRContent.is_featured == True,  # noqa: E712
                )
            )
        ).scalar() or 0

        # 按类型 / 平台分布
        type_rows = (
            await db.execute(
                select(ARVRContent.content_type, func.count(ARVRContent.id))
                .where(ARVRContent.org_id == org_id)
                .group_by(ARVRContent.content_type)
            )
        ).all()
        by_content_type = {_enum_value(k): v for k, v in type_rows}

        platform_rows = (
            await db.execute(
                select(ARVRContent.platform, func.count(ARVRContent.id))
                .where(ARVRContent.org_id == org_id)
                .group_by(ARVRContent.platform)
            )
        ).all()
        by_platform = {_enum_value(k): v for k, v in platform_rows}

        size_rows = (
            await db.execute(
                select(
                    func.coalesce(func.sum(ARVRContent.file_size), 0),
                    func.coalesce(func.sum(ARVRContent.view_count), 0),
                    func.coalesce(func.sum(ARVRContent.completion_count), 0),
                    func.coalesce(func.avg(ARVRContent.average_rating), 0.0),
                ).where(ARVRContent.org_id == org_id)
            )
        ).one()

        total_size, total_view, total_complete, avg_rating = size_rows

        return AdminCourseStats(
            total_courses=total,
            active_courses=active,
            inactive_courses=total - active,
            featured_courses=featured,
            by_content_type=by_content_type,
            by_platform=by_platform,
            total_size_bytes=int(total_size or 0),
            total_view_count=int(total_view or 0),
            total_completion_count=int(total_complete or 0),
            avg_rating=float(avg_rating or 0.0),
        )
    except Exception as e:
        logger.error(f"获取 AR/VR 全局统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取全局统计失败: {e}",
        )


# ==================== 内部工具函数（解 ZIP / 找构建目录） ====================


async def _extract_zip(zip_path: str, dest_dir: str) -> None:
    """异步解 ZIP 到目标目录"""
    import zipfile

    os.makedirs(dest_dir, exist_ok=True)
    # zipfile 本身是同步的，使用 to_thread 避免阻塞事件循环
    import asyncio

    def _extract() -> None:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)

    await asyncio.to_thread(_extract)


def _find_unity_build_dir(extracted_dir: str) -> Optional[str]:
    """查找 Unity WebGL 构建目录（含 index.html）"""
    # 优先匹配标准 Build 目录（Build/ 与 index.html 同级）
    standard = os.path.join(extracted_dir, "Build")
    if os.path.isdir(standard) and os.path.exists(
        os.path.join(extracted_dir, "index.html")
    ):
        return extracted_dir

    # 回退：递归找 index.html 所在目录
    for root, _, files in os.walk(extracted_dir):
        if "index.html" in files:
            return root
    return None


def _dir_size(path: str) -> int:
    """累计目录内文件总字节数"""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                continue
    return total

