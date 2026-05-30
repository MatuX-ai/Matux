"""
教室与课程安排模型
"""

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time, JSON
from sqlalchemy.orm import relationship

from utils.database import Base


class Classroom(Base):
    """教室模型"""

    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    room_number = Column(String(50), nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(Integer, default=1)
    capacity = Column(Integer, default=30)
    room_type = Column(String(50), default="standard")
    has_projector = Column(Boolean, default=False)
    has_computer = Column(Boolean, default=False)
    has_audio_system = Column(Boolean, default=False)
    has_whiteboard = Column(Boolean, default=True)
    equipment_list = Column(JSON, default=list)
    is_available = Column(Boolean, default=True)
    maintenance_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClassSchedule(Base):
    """课程安排模型"""

    __tablename__ = "class_schedules"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True, index=True)
    day_of_week = Column(Integer, nullable=False)  # 1-7, 周一到周日
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    duration_minutes = Column(Integer, default=0)
    recurrence_pattern = Column(String(50), default="weekly")
    is_active = Column(Boolean, default=True)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    course = relationship("Course", backref="schedules")
    classroom = relationship("Classroom", backref="schedules")
    teacher = relationship("Teacher", backref="schedules")


# ==================== Pydantic Schemas ====================


class ClassroomCreate(BaseModel):
    """教室创建请求"""
    org_id: int
    room_number: str = Field(..., description="教室编号")
    building: str = Field(..., description="所在楼宇")
    floor: int = Field(1, description="楼层")
    capacity: int = Field(30, description="容纳人数")
    room_type: str = Field("standard", description="教室类型")
    has_projector: bool = False
    has_computer: bool = False
    has_audio_system: bool = False
    has_whiteboard: bool = True
    equipment_list: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None


class ClassroomResponse(BaseModel):
    """教室响应"""
    id: int
    org_id: int
    room_number: str
    building: str
    floor: int
    capacity: int
    room_type: str
    has_projector: bool
    has_computer: bool
    has_audio_system: bool
    has_whiteboard: bool
    equipment_list: Optional[List[Dict[str, Any]]] = None
    is_available: bool
    maintenance_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassScheduleCreate(BaseModel):
    """课程安排创建请求"""
    org_id: int
    classroom_id: int
    course_id: int
    teacher_id: Optional[int] = None
    day_of_week: int = Field(..., ge=1, le=7, description="星期几(1-7)")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    recurrence_pattern: str = "weekly"


class ClassScheduleResponse(BaseModel):
    """课程安排响应"""
    id: int
    org_id: int
    classroom_id: int
    course_id: int
    teacher_id: Optional[int] = None
    day_of_week: int
    start_time: time
    end_time: time
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_minutes: int
    recurrence_pattern: str
    is_active: bool
    is_confirmed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
