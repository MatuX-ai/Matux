"""
多媒体资源管理服务
处理视频上传、存储、转码和文档处理等业务逻辑
"""

from datetime import datetime
import logging
import os
from typing import Any, Dict, List
import uuid

import boto3
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database.tenant_aware_session import TenantQueryHelper
from models.course import Course, CourseLesson
from models.multimedia import (
    DocumentFormat,
    MediaTranscodingJob,
    MediaType,
    MultimediaResource,
    MultimediaResourceCreate,
    VideoStatus,
)
from models.user import User

logger = logging.getLogger(__name__)


class StorageConfig:
    """存储配置类"""

    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")  # local, s3, azure
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./uploads")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_bucket = os.getenv("AWS_S3_BUCKET", "imato-multimedia")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.cdn_domain = os.getenv("CDN_DOMAIN", "")

    def get_s3_client(self):
        """获取S3客户端"""
        if not self.aws_access_key or not self.aws_secret_key:
            raise ValueError("AWS credentials not configured")

        return boto3.client(
            "s3",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        )


class MultimediaService:
    """多媒体资源管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.storage_config = StorageConfig()
        self.tenant_helper = TenantQueryHelper()

    def create_multimedia_resource(
        self, org_id: int, resource_data: MultimediaResourceCreate, current_user: User
    ) -> MultimediaResource:
        """
        创建多媒体资源记录

        Args:
            org_id: 组织ID
            resource_data: 资源创建数据
            current_user: 当前用户

        Returns:
            MultimediaResource: 创建的资源对象
        """
        try:
            # 验证课程和课时存在性
            course = (
                self.db.query(Course)
                .filter(
                    and_(Course.id == resource_data.course_id, Course.org_id == org_id)
                )
                .first()
            )

            if not course:
                raise ValueError("课程不存在")

            if resource_data.lesson_id:
                lesson = (
                    self.db.query(CourseLesson)
                    .filter(
                        and_(
                            CourseLesson.id == resource_data.lesson_id,
                            CourseLesson.course_id == resource_data.course_id,
                        )
                    )
                    .first()
                )

                if not lesson:
                    raise ValueError("课时不存在")

            # 创建资源记录
            resource = MultimediaResource(
                org_id=org_id,
                course_id=resource_data.course_id,
                lesson_id=resource_data.lesson_id,
                title=resource_data.title,
                description=resource_data.description,
                media_type=resource_data.media_type,
                file_name=resource_data.file_name,
                file_size=resource_data.file_size,
                mime_type=resource_data.mime_type,
                is_public=resource_data.is_public,
                access_level=resource_data.access_level,
                tags=resource_data.tags or [],
                custom_metadata=resource_data.custom_metadata or {},
            )

            self.db.add(resource)
            self.db.commit()
            self.db.refresh(resource)

            logger.info(f"多媒体资源创建成功: {resource.id} - {resource.title}")
            return resource

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建多媒体资源失败: {e}")
            raise

    def get_upload_presigned_url(
        self, org_id: int, resource_id: int, current_user: User
    ) -> Dict[str, Any]:
        """
        获取文件上传的预签名URL

        Args:
            org_id: 组织ID
            resource_id: 资源ID
            current_user: 当前用户

        Returns:
            Dict: 包含上传URL和字段的字典
        """
        try:
            # 验证资源存在性和权限
            resource = (
                self.db.query(MultimediaResource)
                .filter(
                    and_(
                        MultimediaResource.id == resource_id,
                        MultimediaResource.org_id == org_id,
                    )
                )
                .first()
            )

            if not resource:
                raise ValueError("资源不存在")

            # 检查用户权限
            if not self._can_manage_resource(current_user, resource):
                raise ValueError("无权管理此资源")

            if self.storage_config.storage_type == "s3":
                return self._get_s3_presigned_url(resource)
            else:
                return self._get_local_upload_info(resource)

        except Exception as e:
            logger.error(f"获取上传URL失败: {e}")
            raise

    def _get_s3_presigned_url(self, resource: MultimediaResource) -> Dict[str, Any]:
        """获取S3预签名上传URL"""
        try:
            s3_client = self.storage_config.get_s3_client()

            # 生成唯一的文件键
            file_extension = resource.file_extension
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_key = (
                f"multimedia/{resource.org_id}/{resource.course_id}/{unique_filename}"
            )

            # 生成预签名POST URL
            presigned_post = s3_client.generate_presigned_post(
                Bucket=self.storage_config.aws_bucket,
                Key=file_key,
                Fields={
                    "Content-Type": resource.mime_type or "application/octet-stream"
                },
                Conditions=[
                    ["content-length-range", 1, 5368709120],  # 1 byte to 5GB
                    {"Content-Type": resource.mime_type or "application/octet-stream"},
                ],
                ExpiresIn=3600,  # 1小时过期
            )

            # 更新资源记录
            resource.original_url = f"https://{self.storage_config.aws_bucket}.s3.{self.storage_config.aws_region}.amazonaws.com/{file_key}"
            self.db.commit()

            return {
                "resource_id": resource.id,
                "upload_url": presigned_post["url"],
                "upload_fields": presigned_post["fields"],
                "file_key": file_key,
                "max_file_size": 5368709120,
            }

        except Exception as e:
            logger.error(f"S3预签名URL生成失败: {e}")
            raise

    def _get_local_upload_info(self, resource: MultimediaResource) -> Dict[str, Any]:
        """获取本地存储上传信息"""
        try:
            # 确保上传目录存在
            upload_dir = os.path.join(
                self.storage_config.local_storage_path,
                str(resource.org_id),
                str(resource.course_id),
            )
            os.makedirs(upload_dir, exist_ok=True)

            # 生成唯一文件名
            file_extension = resource.file_extension
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)

            # 更新资源记录
            if self.storage_config.cdn_domain:
                resource.original_url = f"https://{self.storage_config.cdn_domain}/uploads/{resource.org_id}/{resource.course_id}/{unique_filename}"
            else:
                resource.original_url = (
                    f"/uploads/{resource.org_id}/{resource.course_id}/{unique_filename}"
                )

            self.db.commit()

            return {
                "resource_id": resource.id,
                "upload_path": file_path,
                "relative_url": f"/uploads/{resource.org_id}/{resource.course_id}/{unique_filename}",
                "max_file_size": 5368709120,
            }

        except Exception as e:
            logger.error(f"本地上传信息生成失败: {e}")
            raise

    def complete_upload(
        self,
        org_id: int,
        resource_id: int,
        file_info: Dict[str, Any],
        current_user: User,
    ) -> MultimediaResource:
        """
        完成文件上传

        Args:
            org_id: 组织ID
            resource_id: 资源ID
            file_info: 文件信息
            current_user: 当前用户

        Returns:
            MultimediaResource: 更新后的资源对象
        """
        try:
            # 验证资源存在性
            resource = (
                self.db.query(MultimediaResource)
                .filter(
                    and_(
                        MultimediaResource.id == resource_id,
                        MultimediaResource.org_id == org_id,
                    )
                )
                .first()
            )

            if not resource:
                raise ValueError("资源不存在")

            # 更新文件信息
            if "file_size" in file_info:
                resource.file_size = file_info["file_size"]

            if "mime_type" in file_info:
                resource.mime_type = file_info["mime_type"]

            # 根据媒体类型设置初始状态
            if resource.media_type == MediaType.VIDEO:
                resource.video_status = VideoStatus.UPLOADED
            elif resource.media_type == MediaType.DOCUMENT:
                resource.document_format = self._detect_document_format(
                    resource.file_name
                )

            self.db.commit()
            self.db.refresh(resource)

            logger.info(f"文件上传完成: {resource.id}")
            return resource

        except Exception as e:
            self.db.rollback()
            logger.error(f"完成上传失败: {e}")
            raise

    def initiate_video_transcoding(
        self,
        org_id: int,
        resource_id: int,
        quality_profiles: List[str] = None,
        current_user: User = None,
    ) -> MediaTranscodingJob:
        """
        启动视频转码任务

        Args:
            org_id: 组织ID
            resource_id: 资源ID
            quality_profiles: 质量配置列表
            current_user: 当前用户

        Returns:
            MediaTranscodingJob: 转码任务对象
        """
        try:
            # 验证资源存在性
            resource = (
                self.db.query(MultimediaResource)
                .filter(
                    and_(
                        MultimediaResource.id == resource_id,
                        MultimediaResource.org_id == org_id,
                    )
                )
                .first()
            )

            if not resource:
                raise ValueError("资源不存在")

            if resource.media_type != MediaType.VIDEO:
                raise ValueError("只能对视频资源进行转码")

            if not resource.original_url:
                raise ValueError("原始文件URL未设置")

            # 创建转码任务记录
            job_id = f"job_{uuid.uuid4().hex[:12]}"

            transcoding_job = MediaTranscodingJob(
                org_id=org_id,
                resource_id=resource_id,
                job_id=job_id,
                status=VideoStatus.PROCESSING,
                input_file_url=resource.original_url,
                output_configs={
                    "quality_profiles": quality_profiles or ["1080p", "720p", "480p"],
                    "output_formats": ["hls", "mp4"],
                },
            )

            self.db.add(transcoding_job)

            # 更新资源状态
            resource.video_status = VideoStatus.TRANSCODING
            resource.transcoding_job_id = job_id

            self.db.commit()
            self.db.refresh(transcoding_job)

            logger.info(f"视频转码任务启动: {job_id} for resource {resource_id}")
            return transcoding_job

        except Exception as e:
            self.db.rollback()
            logger.error(f"启动视频转码失败: {e}")
            raise

    def update_transcoding_status(
        self,
        job_id: str,
        status: VideoStatus,
        progress: float = None,
        error_message: str = None,
    ) -> MediaTranscodingJob:
        """
        更新转码任务状态

        Args:
            job_id: 任务ID
            status: 状态
            progress: 进度百分比
            error_message: 错误信息

        Returns:
            MediaTranscodingJob: 更新后的任务对象
        """
        try:
            job = (
                self.db.query(MediaTranscodingJob)
                .filter(MediaTranscodingJob.job_id == job_id)
                .first()
            )

            if not job:
                raise ValueError("转码任务不存在")

            # 更新任务状态
            job.status = status
            if progress is not None:
                job.progress_percent = progress

            if error_message:
                job.error_message = error_message

            if status in [VideoStatus.READY, VideoStatus.FAILED]:
                job.completed_at = datetime.utcnow()

            # 更新关联资源状态
            resource = (
                self.db.query(MultimediaResource)
                .filter(MultimediaResource.id == job.resource_id)
                .first()
            )

            if resource:
                resource.video_status = status
                if status == VideoStatus.READY:
                    resource.processed_url = self._generate_processed_url(job)

            self.db.commit()
            self.db.refresh(job)

            logger.info(f"转码任务状态更新: {job_id} -> {status}")
            return job

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新转码状态失败: {e}")
            raise

    def _generate_processed_url(self, job: MediaTranscodingJob) -> str:
        """生成处理后的文件URL"""
        if self.storage_config.storage_type == "s3":
            # S3 HLS流媒体URL
            return f"https://{self.storage_config.aws_bucket}.s3.{self.storage_config.aws_region}.amazonaws.com/output/{job.job_id}/playlist.m3u8"
        else:
            # 本地存储URL
            return f"/processed/{job.job_id}/playlist.m3u8"

    def _detect_document_format(self, filename: str) -> DocumentFormat:
        """检测文档格式"""
        extension = filename.lower().split(".")[-1] if "." in filename else ""

        format_mapping = {
            "pdf": DocumentFormat.PDF,
            "md": DocumentFormat.MARKDOWN,
            "markdown": DocumentFormat.MARKDOWN,
            "pptx": DocumentFormat.PPTX,
            "docx": DocumentFormat.DOCX,
            "txt": DocumentFormat.TXT,
            "html": DocumentFormat.HTML,
        }

        return format_mapping.get(extension, DocumentFormat.TXT)

    def _can_manage_resource(self, user: User, resource: MultimediaResource) -> bool:
        """检查用户是否有权限管理资源"""
        # 课程创建者或管理员可以管理资源
        course = self.db.query(Course).filter(Course.id == resource.course_id).first()
        if course and (
            course.instructor_id == user.id
            or user.role.name in ["admin", "super_admin"]
        ):
            return True
        return False

    def get_course_multimedia(
        self, org_id: int, course_id: int, media_type: MediaType = None
    ) -> List[MultimediaResource]:
        """
        获取课程的所有多媒体资源

        Args:
            org_id: 组织ID
            course_id: 课程ID
            media_type: 媒体类型过滤

        Returns:
            List[MultimediaResource]: 资源列表
        """
        try:
            query = self.db.query(MultimediaResource).filter(
                and_(
                    MultimediaResource.org_id == org_id,
                    MultimediaResource.course_id == course_id,
                    MultimediaResource.is_active == True,
                )
            )

            if media_type:
                query = query.filter(MultimediaResource.media_type == media_type)

            return query.order_by(MultimediaResource.created_at.desc()).all()

        except Exception as e:
            logger.error(f"获取课程多媒体资源失败: {e}")
            raise

    def delete_multimedia_resource(
        self, org_id: int, resource_id: int, current_user: User
    ) -> bool:
        """
        删除多媒体资源

        Args:
            org_id: 组织ID
            resource_id: 资源ID
            current_user: 当前用户

        Returns:
            bool: 删除是否成功
        """
        try:
            resource = (
                self.db.query(MultimediaResource)
                .filter(
                    and_(
                        MultimediaResource.id == resource_id,
                        MultimediaResource.org_id == org_id,
                    )
                )
                .first()
            )

            if not resource:
                raise ValueError("资源不存在")

            if not self._can_manage_resource(current_user, resource):
                raise ValueError("无权删除此资源")

            # 逻辑删除
            resource.is_active = False
            self.db.commit()

            logger.info(f"多媒体资源已删除: {resource_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除多媒体资源失败: {e}")
            raise
