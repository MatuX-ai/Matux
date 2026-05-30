"""
AR/VR内容管理服务
处理Unity WebGL内容的上传、部署和管理
"""

from datetime import datetime
import logging
import os
import shutil
from typing import Any, Dict, List, Optional
import zipfile

import aiofiles
from sqlalchemy.orm import Session

from models.ar_vr_content import (
    ARVRContent,
    ARVRContentCreate,
    ARVRContentType,
    ARVRContentUpdate,
)
from models.course import Course, CourseLesson
from utils.file_storage import FileStorageManager

logger = logging.getLogger(__name__)


class ARVRContentService:
    """AR/VR内容管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.storage_manager = FileStorageManager()
        self.arvr_content_path = os.path.join(os.getcwd(), "arvr_contents")
        self.build_output_path = os.path.join(self.arvr_content_path, "builds")
        self.thumbnail_path = os.path.join(self.arvr_content_path, "thumbnails")

        # 确保必要的目录存在
        os.makedirs(self.build_output_path, exist_ok=True)
        os.makedirs(self.thumbnail_path, exist_ok=True)

    def create_arvr_content(
        self, org_id: int, content_data: ARVRContentCreate, current_user
    ) -> ARVRContent:
        """
        创建AR/VR内容

        Args:
            org_id: 组织ID
            content_data: 内容创建数据
            current_user: 当前用户

        Returns:
            ARVRContent: 创建的内容对象
        """
        try:
            # 验证关联的课程和课时是否存在
            course = (
                self.db.query(Course)
                .filter(Course.id == content_data.course_id, Course.org_id == org_id)
                .first()
            )

            if not course:
                raise ValueError(f"课程不存在: {content_data.course_id}")

            if content_data.lesson_id:
                lesson = (
                    self.db.query(CourseLesson)
                    .filter(
                        CourseLesson.id == content_data.lesson_id,
                        CourseLesson.course_id == content_data.course_id,
                    )
                    .first()
                )

                if not lesson:
                    raise ValueError(f"课时不存在: {content_data.lesson_id}")

            # 创建内容记录
            content = ARVRContent(
                org_id=org_id,
                course_id=content_data.course_id,
                lesson_id=content_data.lesson_id,
                title=content_data.title,
                description=content_data.description,
                content_type=content_data.content_type,
                platform=content_data.platform,
                config=content_data.config or {},
                required_sensors=(
                    [s.value for s in content_data.required_sensors]
                    if content_data.required_sensors
                    else []
                ),
                interaction_modes=(
                    [im.value for im in content_data.interaction_modes]
                    if content_data.interaction_modes
                    else []
                ),
                is_public=content_data.is_public,
                access_level=content_data.access_level,
                tags=content_data.tags or [],
                custom_metadata=content_data.custom_metadata or {},
            )

            self.db.add(content)
            self.db.commit()
            self.db.refresh(content)

            logger.info(f"AR/VR内容创建成功: {content.id} - {content.title}")
            return content

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建AR/VR内容失败: {e}")
            raise

    def update_arvr_content(
        self, content_id: int, org_id: int, update_data: ARVRContentUpdate
    ) -> ARVRContent:
        """
        更新AR/VR内容

        Args:
            content_id: 内容ID
            org_id: 组织ID
            update_data: 更新数据

        Returns:
            ARVRContent: 更新后的内容对象
        """
        try:
            content = (
                self.db.query(ARVRContent)
                .filter(ARVRContent.id == content_id, ARVRContent.org_id == org_id)
                .first()
            )

            if not content:
                raise ValueError(f"AR/VR内容不存在: {content_id}")

            # 更新字段
            update_fields = update_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if hasattr(content, field):
                    if field in ["required_sensors", "interaction_modes"] and value:
                        # 转换枚举值为字符串
                        setattr(
                            content,
                            field,
                            [
                                item.value if hasattr(item, "value") else item
                                for item in value
                            ],
                        )
                    else:
                        setattr(content, field, value)

            content.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(content)

            logger.info(f"AR/VR内容更新成功: {content_id}")
            return content

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新AR/VR内容失败: {e}")
            raise

    def delete_arvr_content(self, content_id: int, org_id: int) -> bool:
        """
        删除AR/VR内容

        Args:
            content_id: 内容ID
            org_id: 组织ID

        Returns:
            bool: 是否删除成功
        """
        try:
            content = (
                self.db.query(ARVRContent)
                .filter(ARVRContent.id == content_id, ARVRContent.org_id == org_id)
                .first()
            )

            if not content:
                raise ValueError(f"AR/VR内容不存在: {content_id}")

            # 删除相关文件
            if content.build_file_url:
                self._delete_build_files(content.build_file_url)

            if content.thumbnail_url:
                self._delete_thumbnail(content.thumbnail_url)

            # 删除数据库记录
            self.db.delete(content)
            self.db.commit()

            logger.info(f"AR/VR内容删除成功: {content_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除AR/VR内容失败: {e}")
            raise

    async def upload_unity_build(
        self, content_id: int, org_id: int, build_file, thumbnail_file=None
    ) -> Dict[str, Any]:
        """
        上传Unity WebGL构建文件

        Args:
            content_id: 内容ID
            org_id: 组织ID
            build_file: 构建文件（ZIP格式）
            thumbnail_file: 缩略图文件（可选）

        Returns:
            Dict: 上传结果
        """
        try:
            content = (
                self.db.query(ARVRContent)
                .filter(ARVRContent.id == content_id, ARVRContent.org_id == org_id)
                .first()
            )

            if not content:
                raise ValueError(f"AR/VR内容不存在: {content_id}")

            if content.content_type != ARVRContentType.UNITY_WEBGL:
                raise ValueError("只有Unity WebGL内容支持构建文件上传")

            # 处理构建文件
            build_info = await self._process_unity_build(content_id, build_file)

            # 处理缩略图（如果有）
            thumbnail_url = None
            if thumbnail_file:
                thumbnail_url = await self._process_thumbnail(
                    content_id, thumbnail_file
                )

            # 更新内容记录
            content.build_file_url = build_info["index_url"]
            content.manifest_url = build_info["manifest_url"]
            content.thumbnail_url = thumbnail_url
            content.file_size = build_info["total_size"]
            content.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content)

            logger.info(f"Unity构建文件上传成功: {content_id}")

            return {
                "success": True,
                "content_id": content_id,
                "build_info": build_info,
                "thumbnail_url": thumbnail_url,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"上传Unity构建文件失败: {e}")
            raise

    async def _process_unity_build(self, content_id: int, build_file) -> Dict[str, Any]:
        """
        处理Unity WebGL构建文件

        Args:
            content_id: 内容ID
            build_file: 构建文件

        Returns:
            Dict: 构建信息
        """
        try:
            # 创建内容专属目录
            content_build_dir = os.path.join(
                self.build_output_path, f"content_{content_id}"
            )
            os.makedirs(content_build_dir, exist_ok=True)

            # 保存上传的ZIP文件
            zip_filename = f"build_{content_id}.zip"
            zip_filepath = os.path.join(content_build_dir, zip_filename)

            async with aiofiles.open(zip_filepath, "wb") as f:
                content = await build_file.read()
                await f.write(content)

            # 解压ZIP文件
            extracted_dir = os.path.join(content_build_dir, "extracted")
            os.makedirs(extracted_dir, exist_ok=True)

            with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                zip_ref.extractall(extracted_dir)

            # 查找Unity WebGL构建目录结构
            build_dir = self._find_unity_build_directory(extracted_dir)
            if not build_dir:
                raise ValueError("未找到有效的Unity WebGL构建目录")

            # 移动构建文件到最终位置
            final_build_dir = os.path.join(content_build_dir, "build")
            if os.path.exists(final_build_dir):
                shutil.rmtree(final_build_dir)
            shutil.move(build_dir, final_build_dir)

            # 删除临时文件
            os.remove(zip_filepath)
            shutil.rmtree(extracted_dir)

            # 生成构建信息
            build_info = self._generate_build_info(content_id, final_build_dir)

            logger.info(f"Unity构建处理完成: {content_id}")
            return build_info

        except Exception as e:
            logger.error(f"处理Unity构建失败: {e}")
            # 清理临时文件
            content_build_dir = os.path.join(
                self.build_output_path, f"content_{content_id}"
            )
            if os.path.exists(content_build_dir):
                shutil.rmtree(content_build_dir)
            raise

    def _find_unity_build_directory(self, extracted_dir: str) -> Optional[str]:
        """
        查找Unity WebGL构建目录

        Args:
            extracted_dir: 解压目录

        Returns:
            Optional[str]: 构建目录路径
        """
        # 常见的Unity构建目录结构
        possible_patterns = [
            "Build",  # 标准Unity构建目录
            "*",  # 任何包含index.html的目录
        ]

        for pattern in possible_patterns:
            if pattern == "*":
                # 递归搜索包含index.html的目录
                for root, dirs, files in os.walk(extracted_dir):
                    if "index.html" in files:
                        return root
            else:
                build_path = os.path.join(extracted_dir, pattern)
                if os.path.exists(build_path) and os.path.isdir(build_path):
                    index_path = os.path.join(build_path, "index.html")
                    if os.path.exists(index_path):
                        return build_path

        return None

    def _generate_build_info(self, content_id: int, build_dir: str) -> Dict[str, Any]:
        """
        生成构建信息

        Args:
            content_id: 内容ID
            build_dir: 构建目录

        Returns:
            Dict: 构建信息
        """
        # 计算总文件大小
        total_size = 0
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                filepath = os.path.join(root, file)
                total_size += os.path.getsize(filepath)

        # 构建URL路径
        base_url = f"/arvr/builds/content_{content_id}"
        index_url = f"{base_url}/build/index.html"
        manifest_url = f"{base_url}/build/Build/content_{content_id}.json"

        return {
            "total_size": total_size,
            "file_count": sum([len(files) for _, _, files in os.walk(build_dir)]),
            "index_url": index_url,
            "manifest_url": manifest_url,
            "build_timestamp": datetime.utcnow().isoformat(),
        }

    async def _process_thumbnail(self, content_id: int, thumbnail_file) -> str:
        """
        处理缩略图文件

        Args:
            content_id: 内容ID
            thumbnail_file: 缩略图文件

        Returns:
            str: 缩略图URL
        """
        try:
            # 生成文件名
            file_extension = thumbnail_file.filename.split(".")[-1].lower()
            thumbnail_filename = f"thumb_{content_id}.{file_extension}"
            thumbnail_filepath = os.path.join(self.thumbnail_path, thumbnail_filename)

            # 保存文件
            async with aiofiles.open(thumbnail_filepath, "wb") as f:
                content = await thumbnail_file.read()
                await f.write(content)

            # 返回URL
            return f"/arvr/thumbnails/{thumbnail_filename}"

        except Exception as e:
            logger.error(f"处理缩略图失败: {e}")
            raise

    def _delete_build_files(self, build_file_url: str):
        """删除构建文件"""
        try:
            if build_file_url:
                # 从URL提取内容ID
                import re

                match = re.search(r"content_(\d+)", build_file_url)
                if match:
                    content_id = match.group(1)
                    build_dir = os.path.join(
                        self.build_output_path, f"content_{content_id}"
                    )
                    if os.path.exists(build_dir):
                        shutil.rmtree(build_dir)
                        logger.info(f"构建文件已删除: content_{content_id}")
        except Exception as e:
            logger.error(f"删除构建文件失败: {e}")

    def _delete_thumbnail(self, thumbnail_url: str):
        """删除缩略图文件"""
        try:
            if thumbnail_url:
                filename = thumbnail_url.split("/")[-1]
                thumbnail_filepath = os.path.join(self.thumbnail_path, filename)
                if os.path.exists(thumbnail_filepath):
                    os.remove(thumbnail_filepath)
                    logger.info(f"缩略图已删除: {filename}")
        except Exception as e:
            logger.error(f"删除缩略图失败: {e}")

    def get_arvr_content(self, content_id: int, org_id: int) -> ARVRContent:
        """获取AR/VR内容详情"""
        content = (
            self.db.query(ARVRContent)
            .filter(ARVRContent.id == content_id, ARVRContent.org_id == org_id)
            .first()
        )

        if not content:
            raise ValueError(f"AR/VR内容不存在: {content_id}")

        return content

    def list_arvr_contents(
        self,
        org_id: int,
        course_id: Optional[int] = None,
        lesson_id: Optional[int] = None,
    ) -> List[ARVRContent]:
        """列出AR/VR内容"""
        query = self.db.query(ARVRContent).filter(ARVRContent.org_id == org_id)

        if course_id:
            query = query.filter(ARVRContent.course_id == course_id)

        if lesson_id:
            query = query.filter(ARVRContent.lesson_id == lesson_id)

        return query.order_by(ARVRContent.created_at.desc()).all()

    def get_build_static_files(self, content_id: int) -> Optional[str]:
        """
        获取构建文件的静态文件路径

        Args:
            content_id: 内容ID

        Returns:
            Optional[str]: 静态文件目录路径
        """
        build_dir = os.path.join(
            self.build_output_path, f"content_{content_id}", "build"
        )
        if os.path.exists(build_dir):
            return build_dir
        return None


# 静态文件服务辅助函数
def get_arvr_static_file_handler():
    """获取AR/VR静态文件处理器"""
    import os

    from fastapi.staticfiles import StaticFiles

    arvr_content_path = os.path.join(os.getcwd(), "arvr_contents")

    if not os.path.exists(arvr_content_path):
        os.makedirs(arvr_content_path)

    return StaticFiles(directory=arvr_content_path, html=True)
