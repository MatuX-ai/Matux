"""
AR/VR 课程内容数据模型
支持增强现实和虚拟现实课程内容的管理
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

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

if TYPE_CHECKING:
    from .license import Organization


class ARVRContentType(str, enum.Enum):
    """AR/VR内容类型"""

    UNITY_WEBGL = "unity_webgl"  # Unity WebGL构建
    THREEJS_SCENE = "threejs_scene"  # Three.js场景
    MODEL_VIEWER = "model_viewer"  # 3D模型查看器
    INTERACTIVE_DEMO = "interactive_demo"  # 交互式演示
    VIRTUAL_LAB = "virtual_lab"  # 虚拟实验室
    AR_MARKER = "ar_marker"  # AR标记识别


class ARVRPlatform(str, enum.Enum):
    """支持的AR/VR平台"""

    WEB_BROWSER = "web_browser"  # 网页浏览器
    MOBILE_AR = "mobile_ar"  # 移动端AR
    VR_HEADSET = "vr_headset"  # VR头显
    DESKTOP_VR = "desktop_vr"  # 桌面VR


class SensorType(str, enum.Enum):
    """传感器类型"""

    ACCELEROMETER = "accelerometer"  # 加速度计
    GYROSCOPE = "gyroscope"  # 陀螺仪
    MAGNETOMETER = "magnetometer"  # 磁力计
    GPS = "gps"  # GPS定位
    CAMERA = "camera"  # 摄像头
    MICROPHONE = "microphone"  # 麦克风
    TOUCH = "touch"  # 触摸屏
    CUSTOM = "custom"  # 自定义传感器


class InteractionMode(str, enum.Enum):
    """交互模式"""

    GESTURE = "gesture"  # 手势识别
    VOICE = "voice"  # 语音控制
    CONTROLLER = "controller"  # 控制器
    GAZE = "gaze"  # 注视点
    PHYSICAL = "physical"  # 物理交互


class ARVRContent(Base):
    """AR/VR内容模型"""

    __tablename__ = "ar_vr_contents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id",
                    use_alter=True), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey(
        "courses.id", use_alter=True), nullable=False, index=True)
    lesson_id = Column(
        Integer, ForeignKey("course_lessons.id", use_alter=True), nullable=True, index=True
    )

    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content_type = Column(Enum(ARVRContentType), nullable=False)
    platform = Column(Enum(ARVRPlatform), nullable=False)

    # 内容文件信息
    build_file_url = Column(String(500))  # 构建文件URL
    manifest_url = Column(String(500))  # 清单文件URL
    thumbnail_url = Column(String(500))  # 缩略图URL

    # 技术配置
    config = Column(JSON)  # 平台特定配置
    required_sensors = Column(JSON)  # 所需传感器列表
    interaction_modes = Column(JSON)  # 支持的交互模式
    compatibility_info = Column(JSON)  # 兼容性信息

    # 尺寸和性能
    file_size = Column(Integer)  # 文件大小(字节)
    estimated_load_time = Column(Float)  # 预估加载时间(秒)
    performance_profile = Column(JSON)  # 性能配置文件

    # 权限和访问控制
    is_public = Column(Boolean, default=False)
    access_level = Column(String(50), default="course")
    required_permissions = Column(JSON)

    # 元数据
    custom_metadata = Column(JSON)
    tags = Column(JSON)

    # 统计信息
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)

    # 状态
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    course = relationship("Course")
    lesson = relationship("CourseLesson")


class ARVRSensorData(Base):
    """AR/VR 传感器数据模型"""

    __tablename__ = "ar_vr_sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("ar_vr_contents.id", use_alter=True), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey(
        "users.id", use_alter=True), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey(
        "organizations.id", use_alter=True), nullable=False)

    # 传感器信息
    sensor_type = Column(Enum(SensorType), nullable=False)
    data_payload = Column(JSON, nullable=False)  # 传感器数据

    # 时间戳
    captured_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100))  # 会话ID

    # 位置信息（如果适用）
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    # content = relationship("ARVRContent")
    # user = relationship("User")
    # organization = relationship("Organization")


class ARVRInteractionLog(Base):
    """AR/VR 交互日志模型"""

    __tablename__ = "ar_vr_interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("ar_vr_contents.id", use_alter=True), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey(
        "users.id", use_alter=True), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey(
        "organizations.id", use_alter=True), nullable=False)

    # 交互信息
    interaction_type = Column(String(100), nullable=False)  # 交互类型
    interaction_data = Column(JSON)  # 交互详细数据
    interaction_mode = Column(Enum(InteractionMode))

    # 结果和反馈
    success = Column(Boolean, default=True)
    response_time = Column(Float)  # 响应时间(毫秒)
    feedback_score = Column(Float)  # 用户反馈评分

    # 会话信息
    session_id = Column(String(100))
    duration = Column(Float)  # 交互持续时间(秒)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    content = relationship("ARVRContent")
    user = relationship("User")
    organization = relationship("Organization")


class ARVRProgressTracking(Base):
    """AR/VR 学习进度跟踪模型"""

    __tablename__ = "ar_vr_progress_tracking"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer, ForeignKey("ar_vr_contents.id", use_alter=True), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey(
        "users.id", use_alter=True), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey(
        "organizations.id", use_alter=True), nullable=False)

    # 进度信息
    progress_percentage = Column(Float, default=0.0)  # 完成百分比
    current_state = Column(JSON)  # 当前状态数据
    milestones_reached = Column(JSON)  # 达成的里程碑

    # 时间信息
    started_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 学习效果
    time_spent = Column(Float, default=0.0)  # 总耗时(分钟)
    interaction_count = Column(Integer, default=0)  # 交互次数
    assessment_score = Column(Float)  # 评估分数

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # 关系
    content = relationship("ARVRContent")
    user = relationship("User")
    organization = relationship("Organization")


# Pydantic模型用于API请求/响应


class ARVRContentCreate(BaseModel):
    """创建AR/VR内容的请求模型"""

    course_id: int
    lesson_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content_type: ARVRContentType
    platform: ARVRPlatform
    build_file_url: Optional[str] = None
    manifest_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    required_sensors: Optional[List[SensorType]] = None
    interaction_modes: Optional[List[InteractionMode]] = None
    is_public: bool = False
    access_level: str = "course"
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class ARVRContentUpdate(BaseModel):
    """更新AR/VR内容的请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    build_file_url: Optional[str] = None
    manifest_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    required_sensors: Optional[List[SensorType]] = None
    interaction_modes: Optional[List[InteractionMode]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    access_level: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class ARVRContentResponse(BaseModel):
    """AR/VR内容响应模型"""

    id: int
    org_id: int
    course_id: int
    lesson_id: Optional[int]
    title: str
    description: Optional[str]
    content_type: ARVRContentType
    platform: ARVRPlatform
    build_file_url: Optional[str]
    manifest_url: Optional[str]
    thumbnail_url: Optional[str]
    config: Optional[Dict[str, Any]]
    required_sensors: Optional[List[SensorType]]
    interaction_modes: Optional[List[InteractionMode]]
    file_size: Optional[int]
    estimated_load_time: Optional[float]
    is_active: bool
    is_public: bool
    access_level: str
    view_count: int
    completion_count: int
    average_rating: float
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SensorDataCreate(BaseModel):
    """创建传感器数据的请求模型"""

    content_id: int
    sensor_type: SensorType
    data_payload: Dict[str, Any]
    session_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None


class SensorDataResponse(BaseModel):
    """传感器数据响应模型"""

    id: int
    content_id: int
    user_id: int
    org_id: int
    sensor_type: SensorType
    data_payload: Dict[str, Any]
    captured_at: datetime
    session_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]

    model_config = {"from_attributes": True}


class InteractionLogCreate(BaseModel):
    """创建交互日志的请求模型"""

    content_id: int
    interaction_type: str
    interaction_data: Optional[Dict[str, Any]] = None
    interaction_mode: Optional[InteractionMode] = None
    success: bool = True
    response_time: Optional[float] = None
    feedback_score: Optional[float] = None
    session_id: Optional[str] = None
    duration: Optional[float] = None


class ProgressTrackingCreate(BaseModel):
    """创建进度跟踪的请求模型"""

    content_id: int
    progress_percentage: float = Field(..., ge=0, le=100)
    current_state: Optional[Dict[str, Any]] = None
    milestones_reached: Optional[List[str]] = None
    time_spent: Optional[float] = None
    interaction_count: Optional[int] = None
    assessment_score: Optional[float] = None


class ProgressTrackingResponse(BaseModel):
    """进度跟踪响应模型"""

    id: int
    content_id: int
    user_id: int
    org_id: int
    progress_percentage: float
    current_state: Optional[Dict[str, Any]]
    milestones_reached: Optional[List[str]]
    started_at: datetime
    last_accessed_at: datetime
    completed_at: Optional[datetime]
    time_spent: float
    interaction_count: int
    assessment_score: Optional[float]

    model_config = {"from_attributes": True}
