"""
内容商店数据模型
"""

from datetime import datetime
import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLEnum

from database import Base


# 内容类型枚举
class ContentType(enum.Enum):
    """内容类型"""

    COURSE = "course"  # 课程
    RESOURCE_PACK = "resource_pack"  # 资源包
    TEMPLATE = "template"  # 模板
    PLUGIN = "plugin"  # 插件
    MODULE = "module"  # 模块


# 内容状态枚举
class ContentStatus(enum.Enum):
    """内容状态"""

    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


# 内容评级枚举
class ContentRating(enum.Enum):
    """内容评级"""

    FREE = "free"  # 免费
    BASIC = "basic"  # 基础版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"  # 企业版


# 订单状态枚举
class OrderStatus(enum.Enum):
    """订单状态"""

    PENDING = "pending"  # 待处理
    PAID = "paid"  # 已支付
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


# DRM内容状态枚举
class DRMStatus(enum.Enum):
    """DRM内容状态"""

    ACTIVE = "active"  # 活跃
    EXPIRED = "expired"  # 过期
    REVOKED = "revoked"  # 撤销
    SUSPENDED = "suspended"  # 暂停


class ContentCategory(Base):
    """内容分类模型"""

    __tablename__ = "content_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(String, unique=True, nullable=False, index=True)  # 分类ID
    name = Column(String, nullable=False)  # 分类名称
    description = Column(Text)  # 分类描述
    parent_id = Column(String, ForeignKey("content_categories.category_id"))  # 父分类
    icon = Column(String)  # 图标
    sort_order = Column(Integer, default=0)  # 排序
    is_active = Column(Boolean, default=True)  # 是否启用

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    parent = relationship(
        "ContentCategory", remote_side=[category_id], back_populates="children"
    )
    children = relationship("ContentCategory", back_populates="parent")
    contents = relationship("ContentItem", back_populates="category")

    # 索引
    __table_args__ = (
        Index("idx_category_parent", "parent_id"),
        Index("idx_category_active", "is_active"),
        Index("idx_category_sort", "sort_order"),
    )


class ContentTag(Base):
    """内容标签模型"""

    __tablename__ = "content_tags"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(String, unique=True, nullable=False, index=True)  # 标签ID
    name = Column(String, nullable=False)  # 标签名称
    description = Column(Text)  # 标签描述
    color = Column(String(7))  # 标签颜色 (#FFFFFF格式)
    is_system = Column(Boolean, default=False)  # 是否系统标签

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    contents = relationship("ContentTagAssociation", back_populates="tag")

    # 索引
    __table_args__ = (
        Index("idx_tag_name", "name"),
        Index("idx_tag_system", "is_system"),
    )


class ContentTagAssociation(Base):
    """内容标签关联模型"""

    __tablename__ = "content_tag_associations"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    tag_id = Column(String, ForeignKey("content_tags.tag_id"), nullable=False)  # 标签ID

    # 关系
    content = relationship("ContentItem", back_populates="tags")
    tag = relationship("ContentTag", back_populates="contents")

    # 索引
    __table_args__ = (
        Index("idx_content_tag_unique", "content_id", "tag_id", unique=True),
        Index("idx_tag_content", "tag_id", "content_id"),
    )


class ContentItem(Base):
    """内容商品模型"""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, unique=True, nullable=False, index=True)  # 内容ID
    title = Column(String, nullable=False)  # 标题
    description = Column(Text)  # 描述
    content_type = Column(SQLEnum(ContentType), nullable=False)  # 内容类型
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT)  # 状态
    rating = Column(SQLEnum(ContentRating), default=ContentRating.FREE)  # 评级要求

    # 价格信息
    price = Column(Float, default=0.0)  # 价格
    original_price = Column(Float)  # 原价
    currency = Column(String(3), default="CNY")  # 货币
    is_free = Column(Boolean, default=False)  # 是否免费

    # 分类和标签
    category_id = Column(String, ForeignKey("content_categories.category_id"))  # 分类ID
    thumbnail_url = Column(String)  # 缩略图URL
    preview_url = Column(String)  # 预览URL
    demo_url = Column(String)  # 演示URL

    # 统计信息
    view_count = Column(Integer, default=0)  # 查看次数
    download_count = Column(Integer, default=0)  # 下载次数
    purchase_count = Column(Integer, default=0)  # 购买次数
    rating_score = Column(Float, default=0.0)  # 评分
    rating_count = Column(Integer, default=0)  # 评分人数

    # DRM相关信息
    has_drm = Column(Boolean, default=False)  # 是否有DRM保护
    drm_provider = Column(String)  # DRM提供商
    encryption_key_id = Column(String)  # 加密密钥ID

    # 元数据
    version = Column(String, default="1.0.0")  # 版本号
    file_size = Column(Integer)  # 文件大小(字节)
    file_format = Column(String)  # 文件格式
    compatibility = Column(JSON)  # 兼容性信息

    # SEO和营销
    seo_keywords = Column(JSON)  # SEO关键词
    meta_description = Column(Text)  # Meta描述
    is_featured = Column(Boolean, default=False)  # 是否推荐
    featured_order = Column(Integer, default=0)  # 推荐排序

    # 时间戳
    published_at = Column(DateTime)  # 发布时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    category = relationship("ContentCategory", back_populates="contents")
    tags = relationship("ContentTagAssociation", back_populates="content")
    reviews = relationship("ContentReview", back_populates="content")
    drm_contents = relationship("DRMContent", back_populates="content")
    cart_items = relationship("ShoppingCartItem", back_populates="content")
    order_items = relationship("OrderItem", back_populates="content")

    # 索引
    __table_args__ = (
        Index("idx_content_type", "content_type"),
        Index("idx_content_status", "status"),
        Index("idx_content_rating", "rating"),
        Index("idx_content_category", "category_id"),
        Index("idx_content_featured", "is_featured", "featured_order"),
        Index("idx_content_price", "price"),
        Index("idx_content_published", "published_at"),
        Index("idx_content_search", "title", "description", postgresql_using="gin"),
    )


class ContentReview(Base):
    """内容评价模型"""

    __tablename__ = "content_reviews"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String, unique=True, nullable=False, index=True)  # 评价ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    rating = Column(Integer, nullable=False)  # 评分(1-5星)
    title = Column(String)  # 评价标题
    content = Column(Text)  # 评价内容
    is_verified = Column(Boolean, default=False)  # 是否已验证购买
    is_helpful_count = Column(Integer, default=0)  # 觉得有用的人数

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    content = relationship("ContentItem", back_populates="reviews")
    user = relationship("User")  # 需要导入User模型

    # 索引
    __table_args__ = (
        Index("idx_review_content", "content_id"),
        Index("idx_review_user", "user_id"),
        Index("idx_review_rating", "rating"),
        Index("idx_review_verified", "is_verified"),
    )


class ShoppingCartItem(Base):
    """购物车项目模型"""

    __tablename__ = "shopping_cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_item_id = Column(String, unique=True, nullable=False, index=True)  # 购物车项ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    quantity = Column(Integer, default=1)  # 数量
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User")  # 需要导入User模型
    content = relationship("ContentItem", back_populates="cart_items")

    # 索引
    __table_args__ = (
        Index("idx_cart_user", "user_id"),
        Index("idx_cart_content", "content_id"),
        Index("idx_cart_user_content", "user_id", "content_id", unique=True),
    )


class Order(Base):
    """订单模型"""

    __tablename__ = "content_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)  # 订单ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)  # 订单状态

    # 价格信息
    subtotal = Column(Float, nullable=False)  # 小计
    discount_amount = Column(Float, default=0.0)  # 折扣金额
    tax_amount = Column(Float, default=0.0)  # 税费
    total_amount = Column(Float, nullable=False)  # 总金额
    currency = Column(String(3), default="CNY")  # 货币

    # 支付信息
    payment_method = Column(String)  # 支付方式
    payment_transaction_id = Column(String)  # 支付交易ID
    paid_at = Column(DateTime)  # 支付时间

    # 地址信息（如果需要）
    billing_address = Column(JSON)  # 账单地址
    shipping_address = Column(JSON)  # 配送地址

    # 备注
    note = Column(Text)  # 订单备注
    admin_note = Column(Text)  # 管理员备注

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)  # 完成时间

    # 关系
    user = relationship("User")  # 需要导入User模型
    items = relationship("OrderItem", back_populates="order")
    access_grants = relationship("ContentAccessGrant", back_populates="order")

    # 索引
    __table_args__ = (
        Index("idx_order_user", "user_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_created", "created_at"),
        Index("idx_order_paid", "paid_at"),
    )


class OrderItem(Base):
    """订单项目模型"""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(String, unique=True, nullable=False, index=True)  # 订单项ID
    order_id = Column(
        String, ForeignKey("content_orders.order_id"), nullable=False
    )  # 订单ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID

    # 价格信息
    unit_price = Column(Float, nullable=False)  # 单价
    quantity = Column(Integer, default=1)  # 数量
    subtotal = Column(Float, nullable=False)  # 小计

    # 内容快照
    content_title = Column(String)  # 内容标题快照
    content_version = Column(String)  # 内容版本快照

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    order = relationship("Order", back_populates="items")
    content = relationship("ContentItem", back_populates="order_items")

    # 索引
    __table_args__ = (
        Index("idx_order_item_order", "order_id"),
        Index("idx_order_item_content", "content_id"),
    )


class DRMContent(Base):
    """DRM加密内容模型"""

    __tablename__ = "drm_contents"

    id = Column(Integer, primary_key=True, index=True)
    drm_id = Column(String, unique=True, nullable=False, index=True)  # DRM ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    status = Column(SQLEnum(DRMStatus), default=DRMStatus.ACTIVE)  # DRM状态

    # 加密信息
    encrypted_content_url = Column(String)  # 加密内容URL
    encryption_algorithm = Column(String, default="AES-256")  # 加密算法
    encryption_key_id = Column(String)  # 密钥ID
    iv = Column(String)  # 初始化向量

    # 水印信息
    watermark_template = Column(Text)  # 水印模板
    has_dynamic_watermark = Column(Boolean, default=True)  # 是否动态水印

    # 访问控制
    max_devices = Column(Integer, default=5)  # 最大设备数
    expiration_days = Column(Integer)  # 过期天数
    offline_duration = Column(Integer, default=30)  # 离线时长(小时)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # 过期时间

    # 关系
    content = relationship("ContentItem", back_populates="drm_contents")
    access_logs = relationship("ContentAccessLog", back_populates="drm_content")

    # 索引
    __table_args__ = (
        Index("idx_drm_content", "content_id"),
        Index("idx_drm_status", "status"),
        Index("idx_drm_expires", "expires_at"),
    )


class ContentAccessGrant(Base):
    """内容访问授权模型"""

    __tablename__ = "content_access_grants"

    id = Column(Integer, primary_key=True, index=True)
    grant_id = Column(String, unique=True, nullable=False, index=True)  # 授权ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    order_id = Column(String, ForeignKey("content_orders.order_id"))  # 订单ID

    # 授权类型
    grant_type = Column(String, nullable=False)  # purchase/subscription/gift/trial
    access_level = Column(SQLEnum(ContentRating), nullable=False)  # 访问级别

    # 时间控制
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # 过期时间
    is_revoked = Column(Boolean, default=False)  # 是否撤销

    # 使用统计
    access_count = Column(Integer, default=0)  # 访问次数
    last_accessed_at = Column(DateTime)  # 最后访问时间

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User")  # 需要导入User模型
    content = relationship("ContentItem")
    order = relationship("Order", back_populates="access_grants")

    # 索引
    __table_args__ = (
        Index("idx_grant_user", "user_id"),
        Index("idx_grant_content", "content_id"),
        Index("idx_grant_order", "order_id"),
        Index("idx_grant_expires", "expires_at"),
        Index("idx_grant_active", "is_revoked"),
    )


class ContentAccessLog(Base):
    """内容访问日志模型"""

    __tablename__ = "content_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String, unique=True, nullable=False, index=True)  # 日志ID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户ID
    content_id = Column(
        String, ForeignKey("content_items.content_id"), nullable=False
    )  # 内容ID
    drm_content_id = Column(String, ForeignKey("drm_contents.drm_id"))  # DRM内容ID

    # 访问信息
    access_type = Column(String, nullable=False)  # view/download/stream
    device_info = Column(JSON)  # 设备信息
    ip_address = Column(String)  # IP地址
    user_agent = Column(Text)  # User-Agent
    session_id = Column(String)  # 会话ID

    # 地理位置
    country = Column(String(2))  # 国家代码
    region = Column(String)  # 地区
    city = Column(String)  # 城市

    # 水印信息
    watermark_data = Column(JSON)  # 水印数据
    access_token = Column(String)  # 访问令牌

    accessed_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User")  # 需要导入User模型
    content = relationship("ContentItem")
    drm_content = relationship("DRMContent", back_populates="access_logs")

    # 索引
    __table_args__ = (
        Index("idx_access_log_user", "user_id"),
        Index("idx_access_log_content", "content_id"),
        Index("idx_access_log_time", "accessed_at"),
        Index("idx_access_log_ip", "ip_address"),
    )


# 导出所有模型
__all__ = [
    "ContentType",
    "ContentStatus",
    "ContentRating",
    "OrderStatus",
    "DRMStatus",
    "ContentCategory",
    "ContentTag",
    "ContentTagAssociation",
    "ContentItem",
    "ContentReview",
    "ShoppingCartItem",
    "Order",
    "OrderItem",
    "DRMContent",
    "ContentAccessGrant",
    "ContentAccessLog",
]
