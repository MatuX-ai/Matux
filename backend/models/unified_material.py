"""
统一课件库模型
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from utils.database import Base


class UnifiedMaterial(Base):
    """统一课件库模型"""

    __tablename__ = "unified_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    material_type = Column(String(50), nullable=False, index=True)  # document, video, audio, image, interactive
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    file_format = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, default=0)
    cover_image_url = Column(String(500), nullable=True)
    tags = Column(JSON, default=list)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(50), default="intermediate")
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    lesson_id = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    version = Column(String(20), default="1.0")
    language = Column(String(20), default="zh-CN")
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_materials")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_materials")

    def __repr__(self):
        return f"<UnifiedMaterial(id={self.id}, title='{self.title}', type='{self.material_type}')>"
