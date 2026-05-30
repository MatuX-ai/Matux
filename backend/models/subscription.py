"""
订阅系统数据模型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BillingCycle(str, Enum):
    """计费周期枚举"""

    WEEKLY = "weekly"  # 每周
    MONTHLY = "monthly"  # 每月
    QUARTERLY = "quarterly"  # 每季度
    YEARLY = "yearly"  # 每年
    CUSTOM = "custom"  # 自定义周期


class SubscriptionStatus(str, Enum):
    """订阅状态枚举"""

    TRIAL = "trial"  # 试用期
    ACTIVE = "active"  # 激活中
    PENDING = "pending"  # 待激活
    CANCELLED = "cancelled"  # 已取消
    EXPIRED = "expired"  # 已过期
    SUSPENDED = "suspended"  # 已暂停
    GRACE_PERIOD = "grace_period"  # 宽限期


class SubscriptionPlanType(str, Enum):
    """订阅计划类型枚举"""

    BASIC = "basic"  # 基础版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"  # 企业版
    CUSTOM = "custom"  # 自定义


class SubscriptionPlan(Base):
    """订阅计划模型"""

    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(String, unique=True, nullable=False, index=True)  # 计划ID
    name = Column(String, nullable=False)  # 计划名称
    description = Column(String)  # 计划描述
    plan_type = Column(SQLEnum(SubscriptionPlanType), nullable=False)  # 计划类型

    # 价格配置
    price = Column(Float, nullable=False)  # 价格
    billing_cycle = Column(SQLEnum(BillingCycle), nullable=False)  # 计费周期
    currency = Column(String, default="CNY")  # 货币单位

    # 功能特性
    features = Column(JSON)  # 功能列表
    limits = Column(JSON)  # 限制配置
    is_popular = Column(Boolean, default=False)  # 是否推荐
    is_active = Column(Boolean, default=True)  # 是否启用

    # 时间相关
    trial_period_days = Column(Integer, default=0)  # 试用期天数
    setup_fee = Column(Float, default=0.0)  # 开通费用

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    subscriptions = relationship("UserSubscription", back_populates="plan")

    # 索引
    __table_args__ = (
        Index("idx_plan_type", "plan_type"),
        Index("idx_plan_active", "is_active"),
        Index("idx_plan_billing", "billing_cycle"),
    )


class UserSubscription(Base):
    """用户订阅模型"""

    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(String, unique=True, nullable=False, index=True)  # 订阅ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    plan_id = Column(
        String, ForeignKey("subscription_plans.plan_id"), nullable=False
    )  # 计划ID

    # 订阅状态
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING)

    # 时间配置
    start_date = Column(DateTime, nullable=False)  # 开始日期
    end_date = Column(DateTime)  # 结束日期
    next_billing_date = Column(DateTime)  # 下次计费日期
    cancelled_at = Column(DateTime)  # 取消时间

    # 试用期配置
    trial_start_date = Column(DateTime)  # 试用开始日期
    trial_end_date = Column(DateTime)  # 试用结束日期

    # 宽限期配置
    grace_period_end = Column(DateTime)  # 宽限期结束时间

    # 自动续费设置
    auto_renew = Column(Boolean, default=True)  # 是否自动续费
    renewal_count = Column(Integer, default=0)  # 续费次数

    # 试用期设置
    has_trial = Column(Boolean, default=False)  # 是否有试用期
    trial_used = Column(Boolean, default=False)  # 是否已使用试用期

    # 升级降级历史
    upgrade_history = Column(JSON)  # 升级历史记录
    downgrade_history = Column(JSON)  # 降级历史记录

    # 价格快照
    price_snapshot = Column(Float)  # 订阅时的价格快照
    currency_snapshot = Column(String)  # 货币快照

    # 附加配置
    custom_config = Column(JSON)  # 自定义配置
    custom_metadata = Column(JSON)  # 元数据

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription")

    # 索引
    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_plan", "plan_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_next_billing", "next_billing_date"),
        Index("idx_subscription_dates", "start_date", "end_date"),
    )


class SubscriptionPayment(Base):
    """订阅支付记录模型"""

    __tablename__ = "subscription_payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, nullable=False, index=True)  # 支付ID
    subscription_id = Column(
        String, ForeignKey("user_subscriptions.subscription_id"), nullable=False
    )  # 订阅ID

    # 支付信息
    amount = Column(Float, nullable=False)  # 支付金额
    currency = Column(String, default="CNY")  # 货币
    payment_method = Column(String)  # 支付方式

    # 周期信息
    billing_cycle_start = Column(DateTime, nullable=False)  # 计费周期开始
    billing_cycle_end = Column(DateTime, nullable=False)  # 计费周期结束

    # 状态信息
    status = Column(String, nullable=False)  # 支付状态
    transaction_id = Column(String)  # 第三方交易ID
    payment_proof = Column(String)  # 支付凭证

    # 回调和通知
    gateway_response = Column(JSON)  # 网关响应
    notification_received = Column(Boolean, default=False)  # 是否收到通知

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)  # 处理时间

    # 关联关系
    subscription = relationship("UserSubscription", back_populates="payments")

    # 索引
    __table_args__ = (
        Index("idx_payment_subscription", "subscription_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_cycle", "billing_cycle_start", "billing_cycle_end"),
        Index("idx_payment_created", "created_at"),
    )


class SubscriptionCycle(Base):
    """订阅周期配置模型"""

    __tablename__ = "subscription_cycles"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(String, unique=True, nullable=False, index=True)  # 周期ID
    plan_id = Column(
        String, ForeignKey("subscription_plans.plan_id"), nullable=False
    )  # 计划ID

    # 周期配置
    billing_cycle = Column(SQLEnum(BillingCycle), nullable=False)  # 计费周期
    interval_count = Column(Integer, default=1)  # 间隔数量

    # 价格配置（支持不同周期的不同价格）
    price_multiplier = Column(Float, default=1.0)  # 价格倍数
    discount_rate = Column(Float, default=0.0)  # 折扣率

    # 生效时间
    effective_from = Column(DateTime, nullable=False)  # 生效开始时间
    effective_to = Column(DateTime)  # 生效结束时间

    is_active = Column(Boolean, default=True)  # 是否激活

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    plan = relationship("SubscriptionPlan")

    # 索引
    __table_args__ = (
        Index("idx_cycle_plan", "plan_id"),
        Index("idx_cycle_billing", "billing_cycle"),
        Index("idx_cycle_active", "is_active"),
        Index("idx_cycle_effective", "effective_from", "effective_to"),
    )


# 导出所有模型
__all__ = [
    "BillingCycle",
    "SubscriptionStatus",
    "SubscriptionPlanType",
    "SubscriptionPlan",
    "UserSubscription",
    "SubscriptionPayment",
    "SubscriptionCycle",
]
