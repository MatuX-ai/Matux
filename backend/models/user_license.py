"""
用户许可证关联模型（存根）
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship, backref

from utils.database import Base


class TokenPackageType(str, Enum):
    """Token套餐类型枚举"""
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class TokenPackage(Base):
    """Token套餐模型"""

    __tablename__ = "token_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    package_type = Column(SAEnum(TokenPackageType), default=TokenPackageType.ONE_TIME)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TokenPackage(id={self.id}, name='{self.name}', price={self.price})>"


class UserTokenBalance(Base):
    """用户Token余额模型"""

    __tablename__ = "user_token_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_tokens = Column(Integer, default=0)
    used_tokens = Column(Integer, default=0)
    remaining_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="token_balance")
    recharge_records = relationship("TokenRechargeRecord", back_populates="user_balance", cascade="all, delete-orphan")
    usage_records = relationship("TokenUsageRecord", back_populates="user_balance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserTokenBalance(id={self.id}, user_id={self.user_id}, remaining={self.remaining_tokens})>"


class TokenRechargeRecord(Base):
    """Token充值记录模型"""

    __tablename__ = "token_recharge_records"

    id = Column(Integer, primary_key=True, index=True)
    user_balance_id = Column(Integer, ForeignKey("user_token_balances.id"), nullable=False, index=True)
    package_id = Column(Integer, ForeignKey("token_packages.id"), nullable=True)
    token_amount = Column(Integer, nullable=False, default=0)
    payment_amount = Column(Numeric(10, 2), nullable=False, default=0)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(50), default="pending")
    order_no = Column(String(100), nullable=True, index=True)
    payment_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user_balance = relationship("UserTokenBalance", back_populates="recharge_records")
    package = relationship("TokenPackage", backref="recharge_records")

    def __repr__(self):
        return f"<TokenRechargeRecord(id={self.id}, amount={self.token_amount}, status='{self.payment_status}')>"


class TokenUsageRecord(Base):
    """Token使用记录模型"""

    __tablename__ = "token_usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_balance_id = Column(Integer, ForeignKey("user_token_balances.id"), nullable=False, index=True)
    token_amount = Column(Integer, nullable=False, default=0)
    usage_type = Column(String(50), nullable=False)  # ai_teacher, course_generation, etc.
    usage_description = Column(Text, nullable=True)
    resource_id = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user_balance = relationship("UserTokenBalance", back_populates="usage_records")

    def __repr__(self):
        return f"<TokenUsageRecord(id={self.id}, amount={self.token_amount}, type='{self.usage_type}')>"


class UserLicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class UserLicense(Base):
    """用户许可证关联模型"""

    __tablename__ = "user_licenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    license_id = Column(Integer, nullable=False, index=True)  # ForeignKey("licenses.id") - licenses 表不存在
    status = Column(SAEnum(UserLicenseStatus), default=UserLicenseStatus.ACTIVE)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    # license = relationship("License", back_populates="user_licenses")  # License 是 Pydantic 模型

    def __repr__(self):
        return f"<UserLicense(id={self.id}, user_id={self.user_id})>"


from models.user import User  # noqa: E402

User.user_licenses = relationship(
    "UserLicense", back_populates="user", cascade="all, delete-orphan"
)

from models.license import License  # noqa: E402

License.user_licenses = relationship(  # type: ignore[attr-defined]
    "UserLicense", back_populates="license", cascade="all, delete-orphan"
)


class UserLicenseResponse(BaseModel):
    id: int
    user_id: int
    license_id: int
    status: UserLicenseStatus
    assigned_at: datetime
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignUserLicenseRequest(BaseModel):
    user_id: int
    license_id: int


class UpdateUserLicenseRequest(BaseModel):
    status: Optional[UserLicenseStatus] = None


class HardwareRentalSummary(BaseModel):
    total_rentals: int = 0
    active_rentals: int = 0
    total_cost: float = 0.0
