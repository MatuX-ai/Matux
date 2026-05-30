"""
Permission system model definitions
Implements RBAC (Role-Based Access Control) permission management
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.database import Base


class PermissionCategory(str, enum.Enum):
    """Permission category enumeration"""

    SYSTEM = "system"
    USER = "user"
    LICENSE = "license"
    COURSE = "course"
    PAYMENT = "payment"
    AI = "ai"
    REPORT = "report"
    CONFIG = "config"


class PermissionAction(str, enum.Enum):
    """Permission action enumeration"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"


class Permission(Base):
    """Permission model"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    resource = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "category": self.category,
            "action": self.action,
            "resource": self.resource,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }

    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', name='{self.name}')>"


class Role(Base):
    """Role model"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id"
    )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }

    def __repr__(self):
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"


# Role-Permission association table
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


# User-Role association table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("assigned_by", Integer, ForeignKey("users.id")),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
    Column("expires_at", DateTime(timezone=True)),
    Column("is_active", Boolean, default=True),
)


class UserRoleAssignment(Base):
    """User role assignment detail model (for recording assignment history)"""

    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    reason = Column(Text)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    assigner = relationship("User", foreign_keys=[assigned_by])
    revoker = relationship("User", foreign_keys=[revoked_by])

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at is not None else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at is not None else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at is not None else None,
            "revoked_by": self.revoked_by,
            "is_active": self.is_active,
            "reason": self.reason,
        }


class PermissionLog(Base):
    """Permission change log model"""

    __tablename__ = "permission_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    permission_code = Column(String(100))
    role_code = Column(String(50))
    old_value = Column(Text)
    new_value = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_user_id": self.target_user_id,
            "action_type": self.action_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "permission_code": self.permission_code,
            "role_code": self.role_code,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


# Predefined system permissions
SYSTEM_PERMISSIONS = [
    # System management permissions
    {
        "code": "system.admin",
        "name": "System Admin",
        "category": "system",
        "action": "manage",
    },
    {
        "code": "system.config",
        "name": "System Config",
        "category": "config",
        "action": "manage",
    },
    {
        "code": "system.logs",
        "name": "View System Logs",
        "category": "system",
        "action": "view",
    },
    # User management permissions
    {"code": "user.create", "name": "Create User", "category": "user", "action": "create"},
    {"code": "user.read", "name": "View User", "category": "user", "action": "read"},
    {"code": "user.update", "name": "Edit User", "category": "user", "action": "update"},
    {"code": "user.delete", "name": "Delete User", "category": "user", "action": "delete"},
    {
        "code": "user.manage_roles",
        "name": "Manage User Roles",
        "category": "user",
        "action": "manage",
    },
    # License management permissions
    {
        "code": "license.create",
        "name": "Create License",
        "category": "license",
        "action": "create",
    },
    {
        "code": "license.read",
        "name": "View License",
        "category": "license",
        "action": "read",
    },
    {
        "code": "license.update",
        "name": "Edit License",
        "category": "license",
        "action": "update",
    },
    {
        "code": "license.delete",
        "name": "Delete License",
        "category": "license",
        "action": "delete",
    },
    {
        "code": "license.assign",
        "name": "Assign License",
        "category": "license",
        "action": "manage",
    },
    # Course management permissions
    {
        "code": "course.create",
        "name": "Create Course",
        "category": "course",
        "action": "create",
    },
    {"code": "course.read", "name": "View Course", "category": "course", "action": "read"},
    {
        "code": "course.update",
        "name": "Edit Course",
        "category": "course",
        "action": "update",
    },
    {
        "code": "course.delete",
        "name": "Delete Course",
        "category": "course",
        "action": "delete",
    },
    # Payment management permissions
    {
        "code": "payment.read",
        "name": "View Payments",
        "category": "payment",
        "action": "read",
    },
    {
        "code": "payment.refund",
        "name": "Refund Operations",
        "category": "payment",
        "action": "manage",
    },
    # AI service permissions
    {"code": "ai.use", "name": "Use AI Service", "category": "ai", "action": "use"},
    {"code": "ai.manage", "name": "Manage AI Service", "category": "ai", "action": "manage"},
    # Report/statistics permissions
    {"code": "report.view", "name": "View Reports", "category": "report", "action": "view"},
    {
        "code": "report.export",
        "name": "Export Reports",
        "category": "report",
        "action": "export",
    },
]

# Predefined roles
SYSTEM_ROLES = [
    {
        "code": "super_admin",
        "name": "Super Admin",
        "description": "Has all system permissions",
        "is_system": True,
        "priority": 100,
        "permissions": [perm["code"] for perm in SYSTEM_PERMISSIONS],
    },
    {
        "code": "admin",
        "name": "Admin",
        "description": "Manages main system functions",
        "is_system": True,
        "priority": 90,
        "permissions": [
            "user.read",
            "user.update",
            "user.manage_roles",
            "license.read",
            "license.update",
            "license.assign",
            "course.read",
            "course.update",
            "payment.read",
            "report.view",
        ],
    },
    {
        "code": "org_admin",
        "name": "Organization Admin",
        "description": "Manages organization-related functions",
        "is_system": True,
        "priority": 80,
        "permissions": ["user.read", "license.read", "course.read", "report.view"],
    },
    {
        "code": "teacher",
        "name": "Teacher",
        "description": "Course teaching related permissions",
        "is_system": True,
        "priority": 50,
        "permissions": ["course.create", "course.read", "course.update", "ai.use"],
    },
    {
        "code": "student",
        "name": "Student",
        "description": "Learning related permissions",
        "is_system": True,
        "priority": 30,
        "permissions": ["course.read", "ai.use"],
    },
]
