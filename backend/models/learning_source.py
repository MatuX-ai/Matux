"""
学习来源管理数据模型
支持多种学习来源类型：学校统一课程、兴趣班、校外机构、自学等
"""

import enum
from datetime import date, datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class LearningSourceType(str, enum.Enum):
    """学习来源类型枚举"""
    SCHOOL_CURRICULUM = "school_curriculum"      # 学校统一课程
    SCHOOL_INTEREST = "school_interest"          # 学校兴趣班
    INSTITUTION = "institution"                  # 校外机构
    SELF_STUDY = "self_study"                   # 自学
    ONLINE_PLATFORM = "online_platform"          # 在线平台
    COMPETITION = "competition"                  # 竞赛培训


class LearningSourceStatus(str, enum.Enum):
    """学习来源状态"""
    ACTIVE = "active"        # 活动中
    INACTIVE = "inactive"   # 未激活
    COMPLETED = "completed" # 已完成
    SUSPENDED = "suspended"  # 已暂停


class LearningSource(Base):
    """学习来源记录模型

    用于记录学生参与的不同学习来源，如：
    - 学校课程（school_curriculum）
    - 学校兴趣班（school_interest）
    - 校外培训机构（institution）
    - 自学（self_study）
    - 在线学习平台（online_platform）
    - 竞赛培训（competition）
    """

    __tablename__ = "learning_sources"

    id = Column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id", use_alter=True), nullable=False, index=True)
    
    # 关联组织（可选，自学时为null）
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=True, index=True)
    
    # 学习来源类型
    source_type = Column(Enum(LearningSourceType), nullable=False, index=True)
    
    # 来源状态
    status = Column(Enum(LearningSourceStatus), default=LearningSourceStatus.ACTIVE, index=True)
    
    # 来源名称（如：XX学校、XX培训机构）
    name = Column(String(255), nullable=False)
    
    # 来源详情（JSON格式，存储额外信息）
    # 如：班级名称、机构学员号、课程顾问联系方式等
    source_detail = Column(JSON, default=dict)
    
    # 学习时间范围
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # 角色（如：学生、学员、自学者）
    role = Column(String(50), default="student")
    
    # 是否为主要学习来源
    is_primary = Column(Boolean, default=False)
    
    # 备注
    notes = Column(Text, nullable=True)
    
    # 系统字段
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="learning_sources")
    organization = relationship("Organization", back_populates="learning_sources")
    enrollments = relationship("CourseEnrollment", back_populates="learning_source")
    unified_records = relationship("UnifiedLearningRecord", back_populates="learning_source")

    def __repr__(self):
        return f"<LearningSource(id={self.id}, user_id={self.user_id}, type='{self.source_type.value}', name='{self.name}')>"


# 在User模型中添加反向关系
from models.user import User

User.learning_sources = relationship(
    "LearningSource", 
    back_populates="user", 
    cascade="all, delete-orphan"
)


# 在Organization模型中添加反向关系
from models.organization import Organization as OrgModel

OrgModel.learning_sources = relationship(
    "LearningSource",
    back_populates="organization",
    cascade="all, delete-orphan"
)


# 在CourseEnrollment模型中添加反向关系
from models.course import CourseEnrollment

CourseEnrollment.learning_source = relationship(
    "LearningSource",
    back_populates="enrollments"
)


# ============ Pydantic Schema ============

from pydantic import BaseModel, Field


class LearningSourceCreate(BaseModel):
    """创建学习来源的请求模型"""
    
    user_id: int = Field(..., description="用户ID")
    org_id: Optional[int] = Field(None, description="关联组织ID（自学时为null）")
    source_type: LearningSourceType = Field(..., description="学习来源类型")
    name: str = Field(..., min_length=1, max_length=255, description="来源名称")
    source_detail: Optional[Dict[str, Any]] = Field(default_factory=dict, description="来源详情")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    role: str = Field(default="student", max_length=50, description="角色")
    is_primary: bool = Field(default=False, description="是否为主要来源")
    notes: Optional[str] = Field(None, description="备注")


class LearningSourceUpdate(BaseModel):
    """更新学习来源的请求模型"""
    
    org_id: Optional[int] = Field(None, description="关联组织ID")
    source_type: Optional[LearningSourceType] = Field(None, description="学习来源类型")
    status: Optional[LearningSourceStatus] = Field(None, description="来源状态")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="来源名称")
    source_detail: Optional[Dict[str, Any]] = Field(None, description="来源详情")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    role: Optional[str] = Field(None, max_length=50, description="角色")
    is_primary: Optional[bool] = Field(None, description="是否为主要来源")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注")


class LearningSourceResponse(BaseModel):
    """学习来源响应模型"""
    
    id: int
    user_id: int
    org_id: Optional[int]
    source_type: LearningSourceType
    status: LearningSourceStatus
    name: str
    source_detail: Dict[str, Any]
    start_date: Optional[date]
    end_date: Optional[date]
    role: str
    is_primary: bool
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class LearningSourceListResponse(BaseModel):
    """学习来源列表响应模型"""
    
    total: int = Field(..., description="总数")
    items: list[LearningSourceResponse] = Field(..., description="学习来源列表")
