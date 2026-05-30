"""
教师模型
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from utils.database import Base


class Teacher(Base):
    """教师档案模型"""

    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    employee_id = Column(String(50), nullable=False, index=True)  # 工号
    department = Column(String(100), nullable=True)  # 部门
    position = Column(String(100), nullable=True)  # 职位
    hire_date = Column(Date, nullable=True)  # 入职日期
    qualification = Column(String(200), nullable=True)  # 资质
    specialization = Column(String(200), nullable=True)  # 专长
    teaching_subjects = Column(Text, nullable=True)  # 教学科目(JSON字符串)
    max_classes = Column(Integer, default=10)  # 最大课程数
    current_classes = Column(Integer, default=0)  # 当前课程数
    teaching_load = Column(Integer, default=0)  # 教学负荷(分钟)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="teacher_profile")

    def __repr__(self):
        return f"<Teacher(id={self.id}, employee_id='{self.employee_id}')>"


class TeacherCreate(BaseModel):
    """教师创建请求"""
    user_id: int
    employee_id: str = Field(..., description="工号")
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    teaching_subjects: Optional[str] = None
    max_classes: int = 10


class TeacherResponse(BaseModel):
    """教师响应"""
    id: int
    org_id: int
    user_id: int
    employee_id: str
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    teaching_subjects: Optional[str] = None
    max_classes: int
    current_classes: int
    teaching_load: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
