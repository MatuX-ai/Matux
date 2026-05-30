"""
课程聚合数据模型
用于跨机构、跨来源聚合学生的所有课程学习记录
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.database import Base


class CourseSource(str, enum.Enum):
    """课程来源枚举"""
    EDU_INST = "edu_inst"      # OpenMTEduInst 机构课程
    SCIED = "scied"            # OpenMTSciEd 自学课件
    IMATO = "imato"            # iMato 自有课程


class CourseStatus(str, enum.Enum):
    """课程学习状态"""
    ENROLLED = "enrolled"      # 已报名
    IN_PROGRESS = "in_progress"  # 学习中
    COMPLETED = "completed"    # 已完成
    DROPPED = "dropped"        # 已退出


class StudentCourseAggregation(Base):
    """学生课程聚合表

    聚合来自多个来源的课程学习记录，为学生端提供统一的"我的课程"视图。
    数据通过子项目回调推送 + 定时同步拉取两种方式更新。
    """

    __tablename__ = "student_course_aggregation"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
        comment="学生用户ID（iMato统一用户）"
    )
    org_id = Column(
        String(100), nullable=True, index=True,
        comment="来源机构ID（OpenMTEduInst的organization.id）"
    )
    org_name = Column(
        String(200), nullable=True,
        comment="来源机构名称（冗余，便于展示）"
    )
    course_id = Column(
        String(100), nullable=False, index=True,
        comment="来源系统中的课程ID"
    )
    course_name = Column(
        String(200), nullable=False,
        comment="课程名称（冗余，便于展示）"
    )
    source = Column(
        Enum(CourseSource), nullable=False, index=True,
        comment="课程来源：edu_inst / scied / imato"
    )
    status = Column(
        Enum(CourseStatus), default=CourseStatus.ENROLLED,
        comment="学习状态"
    )
    progress = Column(
        Float, default=0.0,
        comment="学习进度（0-100）"
    )
    extra_data = Column(
        Text, nullable=True,
        comment="扩展数据（JSON格式：教师名、课时等）"
    )
    synced_at = Column(
        DateTime(timezone=True), server_default=func.now(),
        comment="最后同步时间"
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # 关联关系
    student = relationship("User", backref="aggregated_courses")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "org_id": self.org_id,
            "org_name": self.org_name,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "source": self.source.value if self.source else None,
            "status": self.status.value if self.status else None,
            "progress": self.progress,
            "extra_data": self.extra_data,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============ Pydantic Schemas ============

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CourseSyncRequest(BaseModel):
    """子项目推送课程数据请求"""

    student_phone: str = Field(..., description="学生手机号（用于匹配iMato用户）")
    org_id: Optional[str] = Field(None, description="机构ID")
    org_name: Optional[str] = Field(None, description="机构名称")
    course_id: str = Field(..., description="课程ID")
    course_name: str = Field(..., description="课程名称")
    source: str = Field(..., description="来源：edu_inst / scied / imato")
    status: Optional[str] = Field("enrolled", description="状态")
    progress: Optional[float] = Field(0.0, description="进度0-100")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="扩展数据")


class CourseSyncResponse(BaseModel):
    """课程同步响应"""

    id: int
    student_id: int
    course_id: str
    course_name: str
    source: str
    status: str
    message: str


class AggregatedCourseItem(BaseModel):
    """聚合课程项"""

    id: int
    org_id: Optional[str]
    org_name: Optional[str]
    course_id: str
    course_name: str
    source: str
    status: str
    progress: float
    synced_at: Optional[str]


class AggregatedCourseListResponse(BaseModel):
    """聚合课程列表响应"""

    student_id: int
    total: int
    by_source: Dict[str, int]  # 按来源统计
    courses: list[AggregatedCourseItem]
