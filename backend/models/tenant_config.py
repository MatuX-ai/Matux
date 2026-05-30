"""
租户配置管理数据模型
用于存储和管理各个租户的个性化配置
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class TenantConfig(Base):
    """租户配置模型"""

    __tablename__ = "tenant_configs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(
        Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, unique=True, index=True
    )
    config_key = Column(String(100), nullable=False, index=True)  # 配置键
    config_value = Column(Text)  # 配置值
    config_type = Column(
        String(20), default="string"
    )  # 配置类型：string, integer, boolean, json
    description = Column(Text)  # 配置描述
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")

    def __repr__(self):
        return f"<TenantConfig(id={self.id}, org_id={self.org_id}, key='{self.config_key}')>"

    def get_typed_value(self) -> Any:
        """根据配置类型返回相应类型的值"""
        cv: str = self.config_value  # type: ignore[assignment]
        ct: str = self.config_type  # type: ignore[assignment]
        if not cv:
            return None

        import json

        try:
            if ct == "integer":
                return int(cv)
            elif ct == "boolean":
                return cv.lower() in ("true", "1", "yes", "on")
            elif ct == "json":
                return json.loads(cv)
            else:  # string
                return cv
        except (ValueError, TypeError, json.JSONDecodeError):
            return cv


class TenantFeatureFlag(Base):
    """租户功能开关模型"""

    __tablename__ = "tenant_feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    feature_name = Column(String(100), nullable=False, index=True)  # 功能名称
    is_enabled = Column(Boolean, default=False)  # 是否启用
    config = Column(JSON)  # 功能特定配置
    description = Column(Text)  # 功能描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")

    def __repr__(self):
        return f"<TenantFeatureFlag(id={self.id}, org_id={self.org_id}, feature='{self.feature_name}', enabled={self.is_enabled})>"


class TenantResourceQuota(Base):
    """租户资源配额模型"""

    __tablename__ = "tenant_resource_quotas"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # 资源类型
    max_limit = Column(Integer, default=0)  # 最大限制
    current_usage = Column(Integer, default=0)  # 当前使用量
    warning_threshold = Column(Integer)  # 警告阈值
    reset_period = Column(String(20))  # 重置周期：daily, weekly, monthly, yearly
    last_reset_at = Column(DateTime)  # 上次重置时间
    is_unlimited = Column(Boolean, default=False)  # 是否无限制
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")

    def __repr__(self):
        return f"<TenantResourceQuota(id={self.id}, org_id={self.org_id}, resource='{self.resource_type}')>"

    @property
    def usage_percentage(self) -> float:
        """计算使用百分比"""
        iu: bool = self.is_unlimited  # type: ignore[assignment]
        ml: int = self.max_limit  # type: ignore[assignment]
        if iu or ml <= 0:
            return 0.0
        cu: int = self.current_usage  # type: ignore[assignment]
        return (cu / ml) * 100

    @property
    def is_over_limit(self) -> bool:
        """检查是否超出限制"""
        iu: bool = self.is_unlimited  # type: ignore[assignment]
        if iu:
            return False
        cu: int = self.current_usage  # type: ignore[assignment]
        ml: int = self.max_limit  # type: ignore[assignment]
        return cu >= ml

    @property
    def is_warning_threshold_reached(self) -> bool:
        """检查是否达到警告阈值"""
        iu: bool = self.is_unlimited  # type: ignore[assignment]
        wt: int = self.warning_threshold  # type: ignore[assignment]
        if wt is None or iu:
            return False
        cu: int = self.current_usage  # type: ignore[assignment]
        return cu >= wt


from datetime import datetime
from typing import Optional, Union

# Pydantic模型用于API请求/响应
from pydantic import BaseModel, Field, validator


class TenantConfigCreate(BaseModel):
    """创建租户配置的请求模型"""

    config_key: str = Field(..., min_length=1, max_length=100)
    config_value: str = Field(..., max_length=1000)
    config_type: str = Field(default="string")
    description: Optional[str] = Field(None, max_length=500)

    @validator("config_type")
    def validate_config_type(cls, v):
        allowed_types = ["string", "integer", "boolean", "json"]
        if v not in allowed_types:
            raise ValueError(f"配置类型必须是以下之一: {allowed_types}")
        return v


class TenantConfigUpdate(BaseModel):
    """更新租户配置的请求模型"""

    config_value: Optional[str] = Field(None, max_length=1000)
    config_type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @validator("config_type")
    def validate_config_type(cls, v):
        if v is not None:
            allowed_types = ["string", "integer", "boolean", "json"]
            if v not in allowed_types:
                raise ValueError(f"配置类型必须是以下之一: {allowed_types}")
        return v


class TenantConfigResponse(BaseModel):
    """租户配置响应模型"""

    id: int
    org_id: int
    config_key: str
    config_value: str
    config_type: str
    typed_value: Union[str, int, bool, dict, None]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagCreate(BaseModel):
    """创建功能开关的请求模型"""

    feature_name: str = Field(..., min_length=1, max_length=100)
    is_enabled: bool = False
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = Field(None, max_length=500)


class FeatureFlagUpdate(BaseModel):
    """更新功能开关的请求模型"""

    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = Field(None, max_length=500)


class FeatureFlagResponse(BaseModel):
    """功能开关响应模型"""

    id: int
    org_id: int
    feature_name: str
    is_enabled: bool
    config: Optional[Dict[str, Any]]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResourceQuotaCreate(BaseModel):
    """创建资源配额的请求模型"""

    resource_type: str = Field(..., min_length=1, max_length=50)
    max_limit: int = Field(..., ge=0)
    warning_threshold: Optional[int] = Field(None, ge=0)
    reset_period: Optional[str] = None
    is_unlimited: bool = False


class ResourceQuotaUpdate(BaseModel):
    """更新资源配额的请求模型"""

    max_limit: Optional[int] = Field(None, ge=0)
    warning_threshold: Optional[int] = Field(None, ge=0)
    reset_period: Optional[str] = None
    is_unlimited: Optional[bool] = None
    current_usage: Optional[int] = Field(None, ge=0)


class ResourceQuotaResponse(BaseModel):
    """资源配额响应模型"""

    id: int
    org_id: int
    resource_type: str
    max_limit: int
    current_usage: int
    warning_threshold: Optional[int]
    reset_period: Optional[str]
    last_reset_at: Optional[datetime]
    is_unlimited: bool
    usage_percentage: float
    is_over_limit: bool
    is_warning_threshold_reached: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# 默认配置模板
DEFAULT_TENANT_CONFIGS = {
    "course": {
        "max_courses_per_instructor": {
            "value": "10",
            "type": "integer",
            "description": "每位讲师最多可创建的课程数",
        },
        "default_course_duration": {
            "value": "16",
            "type": "integer",
            "description": "默认课程学时（小时）",
        },
        "enable_course_reviews": {
            "value": "true",
            "type": "boolean",
            "description": "是否启用课程评价功能",
        },
        "max_students_per_course": {
            "value": "50",
            "type": "integer",
            "description": "每门课程最大学生数",
        },
    },
    "enrollment": {
        "auto_approve_enrollments": {
            "value": "false",
            "type": "boolean",
            "description": "是否自动批准选课申请",
        },
        "enrollment_deadline_days": {
            "value": "7",
            "type": "integer",
            "description": "选课截止天数",
        },
        "allow_drop_course": {
            "value": "true",
            "type": "boolean",
            "description": "是否允许退课",
        },
    },
    "notification": {
        "email_notifications": {
            "value": "true",
            "type": "boolean",
            "description": "是否启用邮件通知",
        },
        "sms_notifications": {
            "value": "false",
            "type": "boolean",
            "description": "是否启用短信通知",
        },
        "push_notifications": {
            "value": "true",
            "type": "boolean",
            "description": "是否启用推送通知",
        },
    },
}

# 默认功能开关
DEFAULT_FEATURE_FLAGS = {
    "course_management": {"enabled": True, "description": "课程管理功能"},
    "student_portal": {"enabled": True, "description": "学生门户功能"},
    "instructor_dashboard": {"enabled": True, "description": "讲师仪表板功能"},
    "analytics_reporting": {"enabled": False, "description": "数据分析报告功能"},
    "mobile_app": {"enabled": False, "description": "移动应用功能"},
    "video_conferencing": {"enabled": False, "description": "视频会议功能"},
}

# 默认资源配额
DEFAULT_RESOURCE_QUOTAS = {
    "courses": {"max_limit": 100, "warning_threshold": 80, "reset_period": "yearly"},
    "students": {"max_limit": 1000, "warning_threshold": 800, "reset_period": "yearly"},
    "storage_gb": {
        "max_limit": 100,
        "warning_threshold": 80,
        "reset_period": "monthly",
    },
    "api_requests": {
        "max_limit": 10000,
        "warning_threshold": 8000,
        "reset_period": "monthly",
    },
}
