"""
多媒体资源管理数据模型
支持视频、3D模型、文档等多种格式的课件资源
"""

from datetime import datetime
import enum
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class MediaType(str, enum.Enum):
    """媒体类型枚举"""

    VIDEO = "video"  # 视频文件
    AUDIO = "audio"  # 音频文件
    IMAGE = "image"  # 图片文件
    DOCUMENT = "document"  # 文档文件
    THREE_D_MODEL = "3d_model"  # 3D模型
    PRESENTATION = "presentation"  # 演示文稿
    INTERACTIVE = "interactive"  # 交互式内容


class VideoStatus(str, enum.Enum):
    """视频处理状态"""

    UPLOADED = "uploaded"  # 已上传
    PROCESSING = "processing"  # 处理中
    TRANSCODING = "transcoding"  # 转码中
    READY = "ready"  # 就绪
    FAILED = "failed"  # 失败


class DocumentFormat(str, enum.Enum):
    """文档格式枚举"""

    PDF = "pdf"
    MARKDOWN = "markdown"
    PPTX = "pptx"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"


class MultimediaResource(Base):
    """多媒体资源模型"""

    __tablename__ = "multimedia_resources"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", use_alter=True), nullable=False, index=True)
    lesson_id = Column(
        Integer, ForeignKey("course_lessons.id", use_alter=True), nullable=True, index=True
    )

    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text)
    media_type = Column(Enum(MediaType), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)  # 文件大小(字节)
    mime_type = Column(String(100))

    # 存储信息
    original_url = Column(String(500))  # 原始文件URL
    processed_url = Column(String(500))  # 处理后的文件URL
    thumbnail_url = Column(String(500))  # 缩略图URL

    # 视频特定字段
    duration_seconds = Column(Float)  # 时长(秒)
    video_status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADED)
    transcoding_job_id = Column(String(100))  # 转码任务ID
    quality_profiles = Column(JSON)  # 质量配置

    # 文档特定字段
    document_format = Column(Enum(DocumentFormat))
    page_count = Column(Integer)  # 页数
    word_count = Column(Integer)  # 字数

    # 3D模型特定字段
    model_format = Column(String(50))  # 模型格式(glb, gltf, obj等)
    model_dimensions = Column(JSON)  # 模型尺寸信息
    preview_config = Column(JSON)  # 预览配置

    # 权限和访问控制
    is_public = Column(Boolean, default=False)
    access_level = Column(String(50), default="course")  # course, lesson, public
    required_permissions = Column(JSON)  # 所需权限列表

    # 元数据
    custom_metadata = Column(JSON)  # 自定义元数据
    tags = Column(JSON)  # 标签列表

    # 统计信息
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    course = relationship("Course")
    lesson = relationship("CourseLesson")

    def __repr__(self):
        return f"<MultimediaResource(id={self.id}, title='{self.title}', type='{self.media_type}')>"

    @property
    def is_ready(self) -> bool:
        """检查资源是否就绪可用"""
        if self.media_type == MediaType.VIDEO:
            return self.video_status == VideoStatus.READY
        return self.processed_url is not None and self.is_active

    @property
    def file_extension(self) -> str:
        """获取文件扩展名"""
        if "." in self.file_name:
            return self.file_name.split(".")[-1].lower()
        return ""


class MediaTranscodingJob(Base):
    """媒体转码任务模型"""

    __tablename__ = "media_transcoding_jobs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False)
    resource_id = Column(Integer, ForeignKey("multimedia_resources.id"), nullable=False)

    # 任务信息
    job_id = Column(String(100), unique=True, nullable=False)  # AWS MediaConvert Job ID
    status = Column(Enum(VideoStatus), default=VideoStatus.PROCESSING)
    progress_percent = Column(Float, default=0.0)

    # 输入输出配置
    input_file_url = Column(String(500), nullable=False)
    output_configs = Column(JSON)  # 输出配置列表

    # 错误信息
    error_message = Column(Text)
    error_details = Column(JSON)

    # 时间信息
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    resource = relationship("MultimediaResource")


from datetime import datetime
from typing import List, Optional

# Pydantic模型用于API请求/响应
from pydantic import BaseModel, Field


class MultimediaResourceCreate(BaseModel):
    """创建多媒体资源的请求模型"""

    course_id: int
    lesson_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    media_type: MediaType
    file_name: str = Field(..., max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_public: bool = False
    access_level: str = "course"
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class MultimediaResourceUpdate(BaseModel):
    """更新多媒体资源的请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    access_level: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class MultimediaResourceResponse(BaseModel):
    """多媒体资源响应模型"""

    id: int
    org_id: int
    course_id: int
    lesson_id: Optional[int]
    title: str
    description: Optional[str]
    media_type: MediaType
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    original_url: Optional[str]
    processed_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[float]
    video_status: Optional[VideoStatus]
    document_format: Optional[DocumentFormat]
    page_count: Optional[int]
    is_active: bool
    is_public: bool
    access_level: str
    view_count: int
    download_count: int
    like_count: int
    is_ready: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoUploadResponse(BaseModel):
    """视频上传响应模型"""

    resource_id: int
    upload_url: str
    upload_fields: Dict[str, str]
    max_file_size: int = 5368709120  # 5GB


class VideoTranscodingRequest(BaseModel):
    """视频转码请求模型"""

    resource_id: int
    quality_profiles: List[str] = ["1080p", "720p", "480p"]
    output_formats: List[str] = ["hls", "mp4"]


class TranscodingJobResponse(BaseModel):
    """转码任务响应模型"""

    job_id: str
    resource_id: int
    status: VideoStatus
    progress_percent: float
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class DocumentProcessingRequest(BaseModel):
    """文档处理请求模型"""

    resource_id: int
    convert_to_pdf: bool = True
    generate_thumbnails: bool = True
    extract_text: bool = True


class ThreeDModelPreviewConfig(BaseModel):
    """3D模型预览配置"""

    model_url: str
    container_id: str
    width: int = 800
    height: int = 600
    background_color: str = "#ffffff"
    auto_rotate: bool = True
    controls: bool = True
