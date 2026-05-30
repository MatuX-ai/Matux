"""
学生模型
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from utils.database import Base


class Student(Base):
    """学生档案模型"""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    student_id = Column(String(50), nullable=False, index=True)  # 学号
    grade = Column(String(50), nullable=True)  # 年级
    class_name = Column(String(100), nullable=True)  # 班级
    enrollment_date = Column(Date, nullable=True)  # 入学日期
    graduation_date = Column(Date, nullable=True)  # 毕业日期
    major = Column(String(100), nullable=True)  # 专业
    advisor_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)  # 导师
    parent_name = Column(String(100), nullable=True)  # 家长姓名
    parent_phone = Column(String(20), nullable=True)  # 家长电话
    emergency_contact = Column(String(100), nullable=True)  # 紧急联系人
    emergency_phone = Column(String(20), nullable=True)  # 紧急联系电话
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="student_profile")
    advisor = relationship("Teacher", backref="students")

    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}')>"


class StudentCreate(BaseModel):
    """学生创建请求"""
    user_id: int
    student_id: str = Field(..., description="学号")
    grade: Optional[str] = None
    class_name: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    major: Optional[str] = None
    advisor_id: Optional[int] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class StudentResponse(BaseModel):
    """学生响应"""
    id: int
    org_id: int
    user_id: int
    student_id: str
    grade: Optional[str] = None
    class_name: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    major: Optional[str] = None
    advisor_id: Optional[int] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
