"""
模块化硬件租赁系统数据模型
支持1元/个的配件租赁功能
"""

from datetime import datetime
import enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class HardwareModuleStatus(str, enum.Enum):
    """硬件模块状态枚举"""

    AVAILABLE = "available"  # 可租赁
    RENTED = "rented"  # 已租赁
    MAINTENANCE = "maintenance"  # 维护中
    DAMAGED = "damaged"  # 损坏
    RETIRED = "retired"  # 已退役


class ModuleRentalStatus(str, enum.Enum):
    """模块租赁记录状态枚举"""

    ACTIVE = "active"  # 租赁中
    COMPLETED = "completed"  # 已完成
    OVERDUE = "overdue"  # 已逾期
    CANCELLED = "cancelled"  # 已取消
    RETURNED = "returned"  # 已归还


class DamageLevel(str, enum.Enum):
    """损坏等级枚举"""

    NONE = "none"  # 无损坏
    MINOR = "minor"  # 轻微损坏
    MODERATE = "moderate"  # 中等损坏
    SEVERE = "severe"  # 严重损坏
    DESTROYED = "destroyed"  # 完全损毁


class HardwareModule(Base):
    """硬件模块模型"""

    __tablename__ = "hardware_modules"

    id = Column(Integer, primary_key=True, index=True)
    module_type = Column(
        String(100), nullable=False, index=True
    )  # 模块类型，如"ESP32", "DHT22"等
    serial_number = Column(
        String(100), unique=True, nullable=False, index=True
    )  # 序列号
    name = Column(String(200), nullable=False)  # 模块显示名称

    # 状态和价格信息
    status = Column(Enum(HardwareModuleStatus), default=HardwareModuleStatus.AVAILABLE)
    price_per_day = Column(Float, default=1.0)  # 日租金1元
    deposit_amount = Column(Float, default=50.0)  # 押金金额

    # 库存和位置信息
    quantity_available = Column(Integer, default=1)  # 可用数量
    total_quantity = Column(Integer, default=1)  # 总数量
    location = Column(String(200))  # 存放位置
    description = Column(Text)  # 模块描述

    # 技术规格
    specifications = Column(Text)  # 技术参数
    compatible_models = Column(Text)  # 兼容型号

    # 状态和时间戳
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    rental_records = relationship(
        "ModuleRentalRecord", back_populates="module", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<HardwareModule(id={self.id}, type='{self.module_type}', sn='{self.serial_number}')>"

    @property
    def is_available(self) -> bool:
        """检查模块是否可租赁"""
        return (
            self.status == HardwareModuleStatus.AVAILABLE
            and self.quantity_available > 0
            and self.is_active
        )

    @property
    def utilization_rate(self) -> float:
        """计算利用率"""
        if self.total_quantity > 0:
            rented_count = sum(
                1
                for record in self.rental_records
                if record.status == ModuleRentalStatus.ACTIVE
            )
            return rented_count / self.total_quantity
        return 0.0

    @property
    def revenue_generated(self) -> float:
        """计算产生的总收入"""
        total_revenue = 0.0
        for record in self.rental_records:
            if record.status in [
                ModuleRentalStatus.COMPLETED,
                ModuleRentalStatus.RETURNED,
            ]:
                total_revenue += record.total_amount
        return total_revenue


class ModuleRentalRecord(Base):
    """模块租赁记录模型"""

    __tablename__ = "module_rental_records"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("hardware_modules.id"), nullable=False)
    user_license_id = Column(Integer, ForeignKey("user_licenses.id"), nullable=False)

    # 租赁时间信息
    rental_start_date = Column(DateTime, nullable=False)  # 租赁开始时间
    rental_end_date = Column(DateTime, nullable=False)  # 预计归还时间
    actual_return_date = Column(DateTime)  # 实际归还时间

    # 财务信息
    daily_rate = Column(Float, nullable=False)  # 日租金
    total_amount = Column(Float, nullable=False)  # 总金额
    deposit_paid = Column(Float, default=0.0)  # 已付押金
    deposit_refunded = Column(Float, default=0.0)  # 已退押金

    # 损坏和赔偿信息
    is_damaged = Column(Boolean, default=False)  # 是否损坏
    damage_level = Column(Enum(DamageLevel), default=DamageLevel.NONE)  # 损坏等级
    damage_description = Column(Text)  # 损坏描述
    compensation_amount = Column(Float, default=0.0)  # 赔偿金额

    # 状态信息
    status = Column(Enum(ModuleRentalStatus), default=ModuleRentalStatus.ACTIVE)
    cancellation_reason = Column(Text)  # 取消原因

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    module = relationship("HardwareModule", back_populates="rental_records")
    user_license = relationship("UserLicense")  # 从user_license.py导入

    def __repr__(self):
        return f"<ModuleRentalRecord(id={self.id}, module_id={self.module_id}, status='{self.status}')>"

    @property
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.status == ModuleRentalStatus.ACTIVE:
            return datetime.utcnow() > self.rental_end_date
        return False

    @property
    def overdue_days(self) -> int:
        """计算逾期天数"""
        if self.is_overdue:
            delta = datetime.utcnow() - self.rental_end_date
            return delta.days
        return 0

    @property
    def rental_duration(self) -> int:
        """计算租赁天数"""
        if self.actual_return_date:
            delta = self.actual_return_date - self.rental_start_date
        else:
            delta = datetime.utcnow() - self.rental_start_date
        return max(1, delta.days)  # 至少1天

    @property
    def net_amount(self) -> float:
        """计算净收入（总金额-赔偿金额）"""
        return self.total_amount - self.compensation_amount

    def calculate_compensation(self) -> float:
        """根据损坏等级计算赔偿金额"""
        if not self.is_damaged or self.damage_level == DamageLevel.NONE:
            return 0.0

        compensation_rates = {
            DamageLevel.MINOR: 0.2,  # 轻微损坏：20%
            DamageLevel.MODERATE: 0.5,  # 中等损坏：50%
            DamageLevel.SEVERE: 0.8,  # 严重损坏：80%
            DamageLevel.DESTROYED: 1.0,  # 完全损毁：100%
        }

        rate = compensation_rates.get(self.damage_level, 0.0)
        return self.module.deposit_amount * rate


from datetime import datetime
from typing import Optional

# Pydantic模型用于API请求/响应
from pydantic import BaseModel, Field, validator


class HardwareModuleCreate(BaseModel):
    """创建硬件模块的请求模型"""

    module_type: str = Field(..., min_length=1, max_length=100)
    serial_number: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    price_per_day: float = Field(default=1.0, ge=0)
    deposit_amount: float = Field(default=50.0, ge=0)
    total_quantity: int = Field(default=1, ge=1)
    location: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[str] = None
    compatible_models: Optional[str] = None

    @validator("serial_number")
    def validate_serial_number(cls, v):
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("序列号只能包含字母、数字、连字符和下划线")
        return v


class HardwareModuleUpdate(BaseModel):
    """更新硬件模块的请求模型"""

    module_type: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[HardwareModuleStatus] = None
    price_per_day: Optional[float] = Field(None, ge=0)
    deposit_amount: Optional[float] = Field(None, ge=0)
    quantity_available: Optional[int] = Field(None, ge=0)
    total_quantity: Optional[int] = Field(None, ge=1)
    location: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[str] = None
    compatible_models: Optional[str] = None
    is_active: Optional[bool] = None


class RentModuleRequest(BaseModel):
    """租赁模块的请求模型"""

    module_id: int
    user_license_id: int
    rental_days: int = Field(..., ge=1, le=30)  # 最多租赁30天
    expected_return_date: Optional[datetime] = None


class ReturnModuleRequest(BaseModel):
    """归还模块的请求模型"""

    actual_return_date: Optional[datetime] = None
    is_damaged: bool = False
    damage_level: Optional[DamageLevel] = None
    damage_description: Optional[str] = None


class HardwareModuleResponse(BaseModel):
    """硬件模块响应模型"""

    id: int
    module_type: str
    serial_number: str
    name: str
    status: HardwareModuleStatus
    price_per_day: float
    deposit_amount: float
    quantity_available: int
    total_quantity: int
    location: Optional[str]
    description: Optional[str]
    specifications: Optional[str]
    compatible_models: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_available: bool
    utilization_rate: float
    revenue_generated: float

    class Config:
        orm_mode = True


class ModuleRentalRecordResponse(BaseModel):
    """模块租赁记录响应模型"""

    id: int
    module_id: int
    user_license_id: int
    rental_start_date: datetime
    rental_end_date: datetime
    actual_return_date: Optional[datetime]
    daily_rate: float
    total_amount: float
    deposit_paid: float
    deposit_refunded: float
    is_damaged: bool
    damage_level: Optional[DamageLevel]
    damage_description: Optional[str]
    compensation_amount: float
    status: ModuleRentalStatus
    cancellation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_overdue: bool
    overdue_days: int
    rental_duration: int
    net_amount: float

    class Config:
        orm_mode = True
