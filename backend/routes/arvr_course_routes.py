"""
AR/VR 课程 REST 路由（前端简化路径）

提供前端 ARVRCoursePlayerComponent 调用的简化路径：
- GET /api/v1/arvr-courses/{id} - 获取 AR/VR 课程详情（不要求 org_id 前缀）

设计原则:
1. 与 backend/routes/ar_vr_routes.py 共享数据源（ARVRContent 模型）
2. 但使用简化的请求路径（无 org_id），方便前端调用
3. 默认 org_id=1（MatuX 默认租户）
4. 返回前端期望的 ARVRCourseData 结构
5. 使用异步数据库会话（与项目其他路由一致）

Author: P1-Backend 修复
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ar_vr_content import ARVRContent, ARVRContentType
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/arvr-courses", tags=["AR/VR 课程（前端简化路径）"])


# ==================== Pydantic 响应模型 ====================


class ARVRCourseMaterialResponse(BaseModel):
    """AR/VR 课程材料响应"""
    id: int = Field(..., description="材料 ID")
    title: str = Field(..., description="材料标题")
    type: str = Field(..., description="材料类型")
    content: str = Field(..., description="材料内容")
    order: int = Field(..., description="排序")


class ARVRCourseResponse(BaseModel):
    """AR/VR 课程响应（前端 ARVRCoursePlayerComponent 直接消费）"""
    id: int = Field(..., description="课程 ID")
    title: str = Field(..., description="课程标题")
    description: str = Field(..., description="课程描述")
    model_url: Optional[str] = Field(None, description="3D 模型 URL（Unity WebGL 构建地址）")
    scene_config: Optional[str] = Field(None, description="场景配置 JSON 字符串")
    content_type: str = Field(..., description="内容类型：3d_model / ar_scene / vr_scene")
    course_materials: List[ARVRCourseMaterialResponse] = Field(
        default_factory=list, description="课程材料列表"
    )
    org_id: int = Field(..., description="所属组织 ID")
    is_active: bool = Field(..., description="是否激活")
    created_at: str = Field(..., description="创建时间 ISO 格式")


# ==================== 类型映射 ====================


def _map_content_type(arvr_type: Optional[ARVRContentType]) -> str:
    """
    将后端 ARVRContentType 枚举映射到前端期望的简化类型

    后端枚举值:
        UNITY_WEBGL = "unity_webgl"
        THREEJS_SCENE = "threejs_scene"
        MODEL_VIEWER = "model_viewer"
        INTERACTIVE_DEMO = "interactive_demo"
        VIRTUAL_LAB = "virtual_lab"
        AR_MARKER = "ar_marker"

    前端期望值:
        3d_model | ar_scene | vr_scene
    """
    if arvr_type is None:
        return "3d_model"
    type_str = arvr_type.value if hasattr(arvr_type, "value") else str(arvr_type)
    if type_str in ("unity_webgl", "threejs_scene", "model_viewer", "interactive_demo", "virtual_lab"):
        return "vr_scene"
    if type_str == "ar_marker":
        return "ar_scene"
    return "3d_model"


def _build_default_materials(content: ARVRContent) -> List[Dict[str, Any]]:
    """
    从 ARVRContent 构造课程材料列表

    后端 ARVRContent 没有专门的 course_materials 字段；
    我们从 config / description / tags 派生示例材料，
    保证前端能渲染出基本的材料导航面板。
    """
    materials: List[Dict[str, Any]] = []

    # 材料 1: 课程概览（基于 description）
    if content.description:
        materials.append({
            "id": content.id * 100 + 1,
            "title": "课程概览",
            "type": "overview",
            "content": content.description,
            "order": 1,
        })

    # 材料 2: 操作指南（基于 content_type）
    op_guide = {
        "3d_model": "使用鼠标拖拽旋转模型，滚轮缩放，右键平移视角。",
        "ar_scene": "将相机对准 AR 标记，等待场景加载。",
        "vr_scene": "佩戴 VR 头显，使用控制器进行交互。",
    }
    mapped_type = _map_content_type(content.content_type)
    materials.append({
        "id": content.id * 100 + 2,
        "title": "操作指南",
        "type": "guide",
        "content": op_guide.get(mapped_type, "请按照页面提示进行交互操作。"),
        "order": 2,
    })

    # 材料 3: 知识点（基于 tags）
    if content.tags and isinstance(content.tags, list) and len(content.tags) > 0:
        tag_text = "、".join(str(t) for t in content.tags)
        materials.append({
            "id": content.id * 100 + 3,
            "title": "相关知识点",
            "type": "knowledge",
            "content": f"本课程涵盖以下知识点：{tag_text}",
            "order": 3,
        })

    return materials


def _build_response(content: ARVRContent) -> ARVRCourseResponse:
    """从 ARVRContent 构造 ARVRCourseResponse（避免重复代码）"""
    materials = _build_default_materials(content)
    return ARVRCourseResponse(
        id=content.id,
        title=content.title or "未命名 AR/VR 课程",
        description=content.description or "",
        model_url=content.build_file_url,
        scene_config=content.manifest_url,
        content_type=_map_content_type(content.content_type),
        course_materials=[ARVRCourseMaterialResponse(**m) for m in materials],
        org_id=content.org_id,
        is_active=bool(content.is_active),
        created_at=(
            content.created_at.isoformat()
            if hasattr(content, "created_at") and content.created_at
            else datetime.utcnow().isoformat()
        ),
    )


# ==================== API 端点 ====================


@router.get("/{course_id}", response_model=ARVRCourseResponse)
async def get_arvr_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取 AR/VR 课程详情

    前端 ARVRCoursePlayerComponent 调用路径:
        GET /api/v1/arvr-courses/{id}

    说明:
        - 默认 org_id=1（MatuX 自有学生端租户）
        - 后端 ARVRContent 是按 (org_id, id) 唯一；这里简化按 id 查找并自动归属到 org_id=1
        - 若该课程不存在，返回 404 并附带友好提示
    """
    try:
        DEFAULT_ORG_ID = 1

        # 查询 ARVRContent（异步）
        stmt = select(ARVRContent).where(
            ARVRContent.id == course_id,
            ARVRContent.org_id == DEFAULT_ORG_ID,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        # 如果 org_id=1 没有，尝试跨 org 兜底查询
        if content is None:
            stmt_fallback = select(ARVRContent).where(ARVRContent.id == course_id)
            result_fallback = await db.execute(stmt_fallback)
            content = result_fallback.scalar_one_or_none()
            if content is not None:
                logger.warning(
                    f"ARVR course {course_id} not in default org {DEFAULT_ORG_ID}, "
                    f"fallback to org {content.org_id}"
                )

        if content is None:
            logger.info(f"ARVR course {course_id} not found")
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ARVR_COURSE_NOT_FOUND",
                    "message": f"AR/VR 课程 {course_id} 不存在或已被删除",
                    "course_id": course_id,
                    "suggestion": "请返回课程列表选择其他课程，或联系管理员上传新内容。",
                },
            )

        response = _build_response(content)
        logger.info(
            f"ARVR course {course_id} returned to client (org_id={content.org_id})"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ARVR course {course_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ARVR_COURSE_FETCH_FAILED",
                "message": "获取 AR/VR 课程失败",
                "error": str(e),
            },
        )


@router.get("/", response_model=List[ARVRCourseResponse])
async def list_arvr_courses(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    列出可用的 AR/VR 课程

    前端如果需要列出所有 AR/VR 课程可以用此端点。
    """
    try:
        DEFAULT_ORG_ID = 1
        stmt = (
            select(ARVRContent)
            .where(ARVRContent.org_id == DEFAULT_ORG_ID, ARVRContent.is_active == True)
            .order_by(ARVRContent.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        contents = result.scalars().all()

        results = [_build_response(c) for c in contents]
        return results
    except Exception as e:
        logger.error(f"Failed to list ARVR courses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="列出 AR/VR 课程失败")
