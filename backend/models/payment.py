"""
支付系统数据模型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class PaymentMethod(str, Enum):
    """支付方式枚举"""

    WECHAT_PAY = "wechat_pay"
    ALIPAY = "alipay"
    BANK_CARD = "bank_card"
    BALANCE = "balance"


class PaymentStatus(str, Enum):
    """支付状态枚举"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDING = "refunding"
    REFUNDED = "refunded"


class OrderStatus(str, Enum):
    """订单状态枚举"""

    PENDING_PAYMENT = "pending_payment"
    PENDING_SHIPMENT = "pending_shipment"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Payment(Base):
    """支付记录模型"""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, nullable=False, index=True)  # 支付ID
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False)  # 订单ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    amount = Column(Float, nullable=False)  # 支付金额
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)  # 支付方式
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)  # 支付状态
    transaction_id = Column(String)  # 第三方交易ID
    payment_proof = Column(String)  # 支付凭证
    gateway_response = Column(JSON)  # 网关响应数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)  # 完成时间

    # 关联关系
    order = relationship("Order", back_populates="payments")
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_payment_user", "user_id"),
        Index("idx_payment_order", "order_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_created", "created_at"),
    )


class Order(Base):
    """订单模型"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)  # 订单ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    items = Column(
        JSON, nullable=False
    )  # 订单项目 [{product_id, quantity, price, ...}]
    total_amount = Column(Float, nullable=False)  # 总金额
    paid_amount = Column(Float, default=0.0)  # 实际支付金额
    status = Column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING_PAYMENT
    )  # 订单状态
    payment_status = Column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING
    )  # 支付状态
    shipping_address = Column(JSON)  # 收货地址
    note = Column(String)  # 用户备注
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)  # 完成时间
    cancelled_at = Column(DateTime)  # 取消时间

    # 关联关系
    payments = relationship("Payment", back_populates="order")
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_order_user", "user_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_payment_status", "payment_status"),
        Index("idx_order_created", "created_at"),
    )


class Product(Base):
    """商品模型"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, nullable=False, index=True)  # 商品ID
    name = Column(String, nullable=False)  # 商品名称
    description = Column(String)  # 商品描述
    price = Column(Float, nullable=False)  # 价格
    stock = Column(Integer, default=0)  # 库存
    image_url = Column(String)  # 图片URL
    category = Column(String)  # 分类
    tags = Column(JSON)  # 标签
    is_active = Column(Integer, default=1)  # 是否上架 (1=上架, 0=下架)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index("idx_product_category", "category"),
        Index("idx_product_active", "is_active"),
        Index("idx_product_price", "price"),
    )


class ShoppingCart(Base):
    """购物车模型"""

    __tablename__ = "shopping_carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    product_id = Column(
        String, ForeignKey("products.product_id"), nullable=False
    )  # 商品ID
    quantity = Column(Integer, default=1)  # 数量
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User")
    product = relationship("Product")

    # 索引
    __table_args__ = (
        Index("idx_cart_user", "user_id"),
        Index("idx_cart_product", "product_id"),
        Index("idx_cart_user_product", "user_id", "product_id"),
    )


class PaymentNotification(Base):
    """支付通知记录模型"""

    __tablename__ = "payment_notifications"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, ForeignKey("payments.payment_id"))  # 支付ID
    notification_type = Column(String, nullable=False)  # 通知类型
    content = Column(JSON, nullable=False)  # 通知内容
    processed = Column(Integer, default=0)  # 是否已处理 (0=未处理, 1=已处理)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)  # 处理时间

    # 关联关系
    payment = relationship("Payment")

    # 索引
    __table_args__ = (
        Index("idx_notification_payment", "payment_id"),
        Index("idx_notification_type", "notification_type"),
        Index("idx_notification_processed", "processed"),
    )
