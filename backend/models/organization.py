"""
Organization SQLAlchemy 模型
机构/组织基础数据模型
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from utils.database import Base


class Organization(Base):
    """机构/组织表"""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="机构名称")
    code = Column(String(50), unique=True, nullable=True, comment="机构代码")
    description = Column(String(500), nullable=True, comment="机构描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系（使用字符串延迟引用，避免循环依赖）
    user_organizations = relationship(
        "UserOrganization", back_populates="organization", lazy="dynamic"
    )
    learning_sources = relationship(
        "LearningSource", back_populates="organization", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
