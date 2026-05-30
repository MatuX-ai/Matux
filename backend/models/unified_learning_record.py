"""
统一学习记录数据模型
跨来源汇总学生的学习进度、成绩和活动记录
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
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class LearningRecordStatus(str, enum.Enum):
    """学习记录状态"""
    NOT_STARTED = "not_started"     # 未开始
    IN_PROGRESS = "in_progress"    # 进行中
    COMPLETED = "completed"        # 已完成
    PAUSED = "paused"              # 已暂停
    DROPPED = "dropped"            # 已放弃


class UnifiedLearningRecord(Base):
    """统一学习记录模型

    用于汇总学生在不同来源的学习数据：
    - 跨学校/机构的课程进度
    - 统一的成绩单和进度追踪
    - 各来源学习时长统计
    - 综合学习分析数据
    """

    __tablename__ = "unified_learning_records"

    id = Column(Integer, primary_key=True, index=True)
    
    # 用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 课程ID（可选，某些学习活动可能没有课程）
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    
    # 学习来源ID（关联到LearningSource）
    learning_source_id = Column(Integer, ForeignKey("learning_sources.id"), nullable=False, index=True)
    
    # 原始选课记录ID（可选，用于追溯原始选课）
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), nullable=True, index=True)
    
    # 学习记录状态
    status = Column(Enum(LearningRecordStatus), default=LearningRecordStatus.NOT_STARTED, index=True)
    
    # 学习进度（0-100）
    progress_percentage = Column(Float, default=0.0, index=True)
    
    # 学习时长（分钟）
    total_time_minutes = Column(Integer, default=0)
    
    # 成绩
    score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0)
    
    # 成绩等级
    grade_letter = Column(String(5), nullable=True)
    
    # 完成信息
    completion_date = Column(DateTime, nullable=True)
    certificate_url = Column(String(500), nullable=True)
    
    # 学习活动详情（JSON格式）
    activity_detail = Column(JSON, default=dict)
    
    # 备注
    notes = Column(Text, nullable=True)
    
    # 系统字段
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="unified_learning_records")
    course = relationship("Course", back_populates="unified_learning_records")
    learning_source = relationship("LearningSource", back_populates="unified_records")
    enrollment = relationship("CourseEnrollment")

    def __repr__(self):
        return f"<UnifiedLearningRecord(id={self.id}, user_id={self.user_id}, course_id={self.course_id}, progress={self.progress_percentage}%)>"


# 在User模型中添加反向关系
from models.user import User

User.unified_learning_records = relationship(
    "UnifiedLearningRecord",
    back_populates="user",
    cascade="all, delete-orphan"
)


# 在Course模型中添加反向关系
from models.course import Course

Course.unified_learning_records = relationship(
    "UnifiedLearningRecord",
    back_populates="course",
    cascade="all, delete-orphan"
)


# ============ Pydantic Schema ============

from pydantic import BaseModel, Field


class UnifiedLearningRecordCreate(BaseModel):
    """创建统一学习记录的请求模型"""
    
    user_id: int = Field(..., description="用户ID")
    course_id: Optional[int] = Field(None, description="课程ID")
    learning_source_id: int = Field(..., description="学习来源ID")
    enrollment_id: Optional[int] = Field(None, description="原始选课记录ID")
    status: LearningRecordStatus = Field(default=LearningRecordStatus.NOT_STARTED, description="学习状态")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="进度百分比")
    total_time_minutes: int = Field(default=0, ge=0, description="学习时长（分钟）")
    score: Optional[float] = Field(None, ge=0, description="成绩")
    max_score: float = Field(default=100.0, ge=0, description="满分")
    grade_letter: Optional[str] = Field(None, max_length=5, description="成绩等级")
    activity_detail: Optional[Dict[str, Any]] = Field(default_factory=dict, description="活动详情")
    notes: Optional[str] = Field(None, description="备注")


class UnifiedLearningRecordUpdate(BaseModel):
    """更新统一学习记录的请求模型"""
    
    course_id: Optional[int] = Field(None, description="课程ID")
    learning_source_id: Optional[int] = Field(None, description="学习来源ID")
    enrollment_id: Optional[int] = Field(None, description="原始选课记录ID")
    status: Optional[LearningRecordStatus] = Field(None, description="学习状态")
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="进度百分比")
    total_time_minutes: Optional[int] = Field(None, ge=0, description="学习时长（分钟）")
    score: Optional[float] = Field(None, ge=0, description="成绩")
    max_score: Optional[float] = Field(None, ge=0, description="满分")
    grade_letter: Optional[str] = Field(None, max_length=5, description="成绩等级")
    completion_date: Optional[datetime] = Field(None, description="完成日期")
    certificate_url: Optional[str] = Field(None, max_length=500, description="证书URL")
    activity_detail: Optional[Dict[str, Any]] = Field(None, description="活动详情")
    is_active: Optional[bool] = Field(None, description="是否激活")
    notes: Optional[str] = Field(None, description="备注")


class UnifiedLearningRecordResponse(BaseModel):
    """统一学习记录响应模型"""
    
    id: int
    user_id: int
    course_id: Optional[int]
    learning_source_id: int
    enrollment_id: Optional[int]
    status: LearningRecordStatus
    progress_percentage: float
    total_time_minutes: int
    score: Optional[float]
    max_score: float
    grade_letter: Optional[str]
    completion_date: Optional[datetime]
    certificate_url: Optional[str]
    activity_detail: Dict[str, Any]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UnifiedLearningRecordListResponse(BaseModel):
    """统一学习记录列表响应模型"""
    
    total: int = Field(..., description="总数")
    items: list[UnifiedLearningRecordResponse] = Field(..., description="记录列表")


class UnifiedProgressStats(BaseModel):
    """跨来源学习进度统计"""
    
    total_courses: int = Field(..., description="总课程数")
    completed_courses: int = Field(..., description="已完成课程数")
    in_progress_courses: int = Field(..., description="进行中课程数")
    total_time_minutes: int = Field(..., description="总学习时长")
    average_score: Optional[float] = Field(None, description="平均成绩")
    source_breakdown: list[Dict[str, Any]] = Field(default_factory=list, description="各来源统计")
