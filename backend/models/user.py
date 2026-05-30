"""
User model
"""

import enum
from typing import List

from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, enum.Enum):
    """User role enumeration"""

    USER = "user"
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"
    ORG_ADMIN = "org_admin"
    SCHOOL_ADMIN = "school_admin"
    EDUCATION_BUREAU = "education_bureau"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_materials = relationship(
        "UnifiedMaterial",
        foreign_keys="UnifiedMaterial.created_by",
        back_populates="creator"
    )
    updated_materials = relationship(
        "UnifiedMaterial",
        foreign_keys="UnifiedMaterial.updated_by",
        back_populates="updater"
    )

    # RBAC role relationships (via user_roles association table)
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="Role.id == user_roles.c.role_id",
        lazy="selectin"
    )

    def verify_password(self, password: str) -> bool:
        """Verify password"""
        hp: str = self.hashed_password  # type: ignore[assignment]
        return pwd_context.verify(password, hp)

    def set_password(self, password: str) -> None:
        """Set password"""
        self.hashed_password = pwd_context.hash(password)

    @classmethod
    def create_hashed_password(cls, password: str) -> str:
        """Create hashed password"""
        return pwd_context.hash(password)

    def to_dict(self) -> dict:
        """Convert to dict"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value if self.role is not None else None,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }

    def to_detail_dict(self) -> dict:
        """Convert to detailed dict"""
        base_dict = self.to_dict()
        return base_dict

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specified role"""
        r: UserRole = self.role  # type: ignore[assignment]
        return r == role

    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles"""
        r: UserRole = self.role  # type: ignore[assignment]
        return r in roles

    def can_manage_licenses(self) -> bool:
        """Check if user can manage licenses"""
        r: UserRole = self.role  # type: ignore[assignment]
        return r in [UserRole.ADMIN, UserRole.ORG_ADMIN]

    def is_admin(self) -> bool:
        """Check if user is admin"""
        r: UserRole = self.role  # type: ignore[assignment]
        su: bool = self.is_superuser  # type: ignore[assignment]
        return r in [UserRole.ADMIN, UserRole.ORG_ADMIN] or su

    # RBAC methods
    def get_roles(self) -> List["Role"]:  # type: ignore[name-defined]
        """Get all roles for the user (new RBAC system)"""
        if hasattr(self, "roles") and self.roles:
            return [role for role in self.roles if role.is_active]
        return []

    def get_permissions(self) -> List["Permission"]:  # type: ignore[name-defined]
        """Get all permissions for the user"""
        permissions = set()
        for role in self.get_roles():
            permissions.update(role.permissions)
        return list(permissions)

    def has_permission(self, permission_code: str) -> bool:
        """Check if user has specified permission"""
        permissions = self.get_permissions()
        return any(perm.code == permission_code for perm in permissions)

    def has_any_permission(self, permission_codes: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = {perm.code for perm in self.get_permissions()}
        return bool(user_permissions.intersection(set(permission_codes)))

    def has_all_permissions(self, permission_codes: List[str]) -> bool:
        """Check if user has all specified permissions"""
        user_permissions = {perm.code for perm in self.get_permissions()}
        return user_permissions.issuperset(set(permission_codes))
