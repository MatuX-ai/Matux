"""
用户-组织关联模型
"""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from utils.database import Base


class UserOrganizationRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"


class UserOrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserOrganization(Base):
    """用户-组织关联模型"""

    __tablename__ = "user_organizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    role = Column(Enum(UserOrganizationRole), default=UserOrganizationRole.STUDENT)
    status = Column(Enum(UserOrganizationStatus), default=UserOrganizationStatus.ACTIVE)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="user_organizations")
    organization = relationship("Organization", back_populates="user_organizations")

    def __repr__(self):
        return (
            f"<UserOrganization(id={self.id}, user_id={self.user_id}, "
            f"org_id={self.org_id}, role='{self.role.value}')>"
        )


# 在User模型中添加反向关系
from models.user import User  # noqa: E402

User.user_organizations = relationship(
    "UserOrganization",
    back_populates="user",
    cascade="all, delete-orphan"
)


# 在Organization模型中添加反向关系
from models.organization import Organization as OrgModel  # noqa: E402

OrgModel.user_organizations = relationship(
    "UserOrganization",
    back_populates="organization",
    cascade="all, delete-orphan"
)


# ============ Pydantic Schema ============


class UserOrganizationCreate(BaseModel):
    user_id: int
    org_id: int
    role: UserOrganizationRole = UserOrganizationRole.STUDENT
    is_primary: bool = False


class UserOrganizationUpdate(BaseModel):
    role: Optional[UserOrganizationRole] = None
    status: Optional[UserOrganizationStatus] = None
    is_primary: Optional[bool] = None


class UserOrganizationResponse(BaseModel):
    id: int
    user_id: int
    org_id: int
    role: UserOrganizationRole
    status: UserOrganizationStatus
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserOrganizationListResponse(BaseModel):
    total: int
    items: list[UserOrganizationResponse]
