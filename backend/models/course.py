"""
课程与课程报名模型
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float,
    ForeignKey, Integer, String, Text, JSON,
)
from sqlalchemy.orm import relationship
from utils.database import Base


class Course(Base):
    """课程模型"""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(50), default="intermediate")
    duration_minutes = Column(Integer, default=0)
    status = Column(String(50), default="draft")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    unified_learning_records = relationship(
        "UnifiedLearningRecord", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}')>"


class CourseEnrollment(Base):
    """课程报名记录模型"""

    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    learning_source_id = Column(
        Integer, ForeignKey("learning_sources.id"), nullable=True, index=True
    )
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    progress_percentage = Column(Float, default=0.0)
    score = Column(Float, nullable=True)
    status = Column(String(50), default="active")
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<CourseEnrollment(id={self.id}, user_id={self.user_id}, "
            f"course_id={self.course_id})>"
        )


class CourseLesson(Base):
    """课程课时模型"""

    __tablename__ = "course_lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=0)
    content_type = Column(String(50), default="video")
    content_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CourseLesson(id={self.id}, title='{self.title}')>"


class CourseAssignment(Base):
    """课程作业/任务模型"""

    __tablename__ = "course_assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignment_type = Column(String(50), default="homework")  # homework, quiz, project, exam
    max_score = Column(Float, default=100.0)
    pass_score = Column(Float, default=60.0)
    deadline = Column(DateTime, nullable=True)
    is_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CourseAssignment(id={self.id}, title='{self.title}')>"
