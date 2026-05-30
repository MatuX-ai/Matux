"""
企业赞助管理系统数据模型
包含赞助活动、品牌曝光、社会影响力和积分转换相关的核心数据结构
"""

from datetime import datetime
import enum
from typing import Any, Dict, Optional

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
from sqlalchemy.orm import relationship, validates

# 使用统一的Base，避免多个declarative_base()导致的mapper初始化错误
from utils.database import Base


class SponsorshipStatus(str, enum.Enum):
    """赞助活动状态枚举"""

    ACTIVE = "active"  # 活动中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ExposureType(str, enum.Enum):
    """曝光类型枚举"""

    BANNER = "banner"  # 横幅广告
    SIDEBAR = "sidebar"  # 侧边栏
    POPUP = "popup"  # 弹窗
    EMAIL = "email"  # 邮件推广
    SOCIAL_MEDIA = "social_media"  # 社交媒体
    CONTENT_INTEGRATION = "content_integration"  # 内容植入


class PointTransactionType(str, enum.Enum):
    """积分交易类型枚举"""

    EARNED = "earned"  # 获得积分
    CONVERTED = "converted"  # 转换积分
    EXPIRED = "expired"  # 积分过期
    ADJUSTED = "adjusted"  # 积分调整


class ImpactCategory(str, enum.Enum):
    """社会影响力类别枚举"""

    EDUCATION = "education"  # 教育支持
    ENVIRONMENT = "environment"  # 环境保护
    CHARITY = "charity"  # 慈善公益
    TECHNOLOGY = "technology"  # 技术发展
    COMMUNITY = "community"  # 社区建设


class Sponsorship(Base):
    """赞助活动模型"""

    __tablename__ = "sponsorships"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)  # 赞助活动名称

    # 赞助详情
    description = Column(Text, nullable=True)  # 活动描述
    sponsor_amount = Column(Float, nullable=False)  # 赞助金额
    currency = Column(String(10), default="CNY")  # 货币单位
    start_date = Column(DateTime, nullable=False)  # 开始日期
    end_date = Column(DateTime, nullable=False)  # 结束日期

    # 活动配置
    exposure_types = Column(JSON, default=list)  # 曝光类型列表
    target_audience = Column(JSON, default=dict)  # 目标受众配置
    branding_guidelines = Column(JSON, default=dict)  # 品牌规范

    # 状态和统计
    status = Column(String(50), default=SponsorshipStatus.ACTIVE)
    total_exposures = Column(Integer, default=0)  # 总曝光次数
    total_points_earned = Column(Float, default=0.0)  # 总获得积分
    conversion_rate = Column(Float, default=0.0)  # 转换率

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)  # 激活时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间

    # 关系
    # organization = relationship("Organization", back_populates="sponsorships")  # 注释掉：Organization 模型不存在
    # organization = relationship("Organization")  # 注释掉以避免 NameError
    exposures = relationship(
        "BrandExposure", back_populates="sponsorship", cascade="all, delete-orphan"
    )
    point_transactions = relationship(
        "PointTransaction", back_populates="sponsorship", cascade="all, delete-orphan"
    )
    social_impacts = relationship(
        "SocialImpact", back_populates="sponsorship", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Sponsorship(id={self.id}, name='{self.name}', org_id={self.org_id})>"

    @validates("name")
    def validate_name(self, key, name):
        """验证赞助活动名称"""
        if not name or len(name.strip()) < 2:
            raise ValueError("赞助活动名称至少需要2个字符")
        return name.strip()

    @validates("sponsor_amount")
    def validate_amount(self, key, amount):
        """验证赞助金额"""
        if amount <= 0:
            raise ValueError("赞助金额必须大于0")
        return amount


class BrandExposure(Base):
    """品牌曝光记录模型"""

    __tablename__ = "brand_exposures"

    id = Column(Integer, primary_key=True, index=True)
    sponsorship_id = Column(
        Integer, ForeignKey("sponsorships.id"), nullable=False, index=True
    )
    exposure_type = Column(String(50), nullable=False)  # 曝光类型

    # 曝光详情
    platform = Column(String(100), nullable=True)  # 平台名称
    placement = Column(String(255), nullable=True)  # 具体位置
    creative_asset = Column(String(500), nullable=True)  # 创意素材URL

    # 统计数据
    view_count = Column(Integer, default=0)  # 展示次数
    click_count = Column(Integer, default=0)  # 点击次数
    engagement_count = Column(Integer, default=0)  # 互动次数
    conversion_count = Column(Integer, default=0)  # 转化次数

    # 时间和地理位置
    exposed_at = Column(DateTime, default=datetime.utcnow)  # 曝光时间
    duration_seconds = Column(Integer, default=0)  # 持续时间
    geo_location = Column(JSON, default=dict)  # 地理位置信息

    # 关系
    sponsorship = relationship("Sponsorship", back_populates="exposures")

    __table_args__ = (
        Index("idx_exposure_sponsorship_type", "sponsorship_id", "exposure_type"),
        Index("idx_exposure_timestamp", "exposed_at"),
    )

    def __repr__(self):
        return f"<BrandExposure(id={self.id}, type='{self.exposure_type}', views={self.view_count})>"

    @property
    def ctr(self) -> float:
        """Click-through rate"""
        vc: int = self.view_count  # type: ignore[assignment]
        if vc == 0:
            return 0.0
        cc: int = self.click_count  # type: ignore[assignment]
        return round((cc / vc) * 100, 2)

    @property
    def engagement_rate(self) -> float:
        """Engagement rate"""
        vc: int = self.view_count  # type: ignore[assignment]
        if vc == 0:
            return 0.0
        ec: int = self.engagement_count  # type: ignore[assignment]
        return round((ec / vc) * 100, 2)


class PointTransaction(Base):
    """积分交易记录模型"""

    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True)
    sponsorship_id = Column(
        Integer, ForeignKey("sponsorships.id"), nullable=False, index=True
    )
    transaction_type = Column(String(50), nullable=False)  # 交易类型

    # 积分详情
    points_amount = Column(Float, nullable=False)  # 积分数额
    balance_before = Column(Float, default=0.0)  # 交易前余额
    balance_after = Column(Float, default=0.0)  # 交易后余额

    # 交易信息
    reference_id = Column(String(100), nullable=True)  # 关联 ID
    description = Column(Text, nullable=True)  # 交易描述
    transaction_metadata = Column(JSON, default=dict)  # 元数据

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    sponsorship = relationship("Sponsorship", back_populates="point_transactions")

    __table_args__ = (
        Index("idx_transaction_sponsorship_type", "sponsorship_id", "transaction_type"),
        Index("idx_transaction_timestamp", "created_at"),
    )

    def __repr__(self):
        return f"<PointTransaction(id={self.id}, type='{self.transaction_type}', amount={self.points_amount})>"


class SocialImpact(Base):
    """社会影响力记录模型"""

    __tablename__ = "social_impacts"

    id = Column(Integer, primary_key=True, index=True)
    sponsorship_id = Column(
        Integer, ForeignKey("sponsorships.id"), nullable=False, index=True
    )
    category = Column(String(50), nullable=False)  # 影响力类别

    # 影响详情
    title = Column(String(255), nullable=False)  # 项目标题
    description = Column(Text, nullable=True)  # 项目描述
    target_beneficiaries = Column(Integer, default=0)  # 目标受益人数
    actual_beneficiaries = Column(Integer, default=0)  # 实际受益人数

    # 成果指标
    metrics = Column(JSON, default=dict)  # 成果指标数据
    evidence_documents = Column(JSON, default=list)  # 证明材料URL列表

    # 时间和状态
    start_date = Column(DateTime, nullable=False)  # 项目开始日期
    end_date = Column(DateTime, nullable=True)  # 项目结束日期
    is_completed = Column(Boolean, default=False)  # 是否已完成
    completion_percentage = Column(Float, default=0.0)  # 完成百分比

    # 关系
    sponsorship = relationship("Sponsorship", back_populates="social_impacts")

    __table_args__ = (
        Index("idx_impact_sponsorship_category", "sponsorship_id", "category"),
        Index("idx_impact_completion", "is_completed"),
    )

    def __repr__(self):
        return f"<SocialImpact(id={self.id}, category='{self.category}', title='{self.title}')>"

    @property
    def impact_score(self) -> float:
        """Impact score"""
        tb: int = self.target_beneficiaries  # type: ignore[assignment]
        if tb == 0:
            return 0.0
        ab: int = self.actual_beneficiaries  # type: ignore[assignment]
        return round((ab / tb) * 100, 2)


class PointConversionRule(Base):
    """积分转换规则模型"""

    __tablename__ = "point_conversion_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 规则名称

    # 转换配置
    points_required = Column(Float, nullable=False)  # 所需积分数
    reward_type = Column(String(50), nullable=False)  # 奖励类型
    reward_value = Column(JSON, nullable=False)  # 奖励值配置

    # 规则条件
    min_sponsorship_amount = Column(Float, default=0.0)  # 最小赞助金额
    applicable_categories = Column(JSON, default=list)  # 适用类别
    validity_period_days = Column(Integer, default=365)  # 有效期(天)

    # 状态和限制
    is_active = Column(Boolean, default=True)  # 是否激活
    max_conversions_per_user = Column(
        Integer, default=-1
    )  # 每用户最大转换次数(-1为无限制)
    total_limit = Column(Integer, default=-1)  # 总转换次数限制

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PointConversionRule(id={self.id}, name='{self.name}', points={self.points_required})>"

    @validates("points_required")
    def validate_points(self, key, points):
        """验证所需积分数"""
        if points <= 0:
            raise ValueError("所需积分数必须大于0")
        return points


# Pydantic模型用于API请求/响应
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SponsorshipCreate(BaseModel):
    """创建赞助活动请求模型"""

    name: str = Field(..., min_length=2, max_length=255, description="赞助活动名称")
    description: Optional[str] = Field(None, description="活动描述")
    sponsor_amount: float = Field(..., gt=0, description="赞助金额")
    currency: str = Field("CNY", description="货币单位")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    exposure_types: List[str] = Field(default=[], description="曝光类型列表")
    target_audience: Dict[str, Any] = Field(default={}, description="目标受众配置")


class SponsorshipUpdate(BaseModel):
    """更新赞助活动请求模型"""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    sponsor_amount: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    exposure_types: Optional[List[str]] = None
    target_audience: Optional[Dict[str, Any]] = None


class SponsorshipResponse(BaseModel):
    """赞助活动响应模型"""

    id: int
    org_id: int
    name: str
    description: Optional[str]
    sponsor_amount: float
    currency: str
    start_date: datetime
    end_date: datetime
    status: str
    total_exposures: int
    total_points_earned: float
    conversion_rate: float
    created_at: datetime
    updated_at: datetime


class ExposureRecordCreate(BaseModel):
    """创建曝光记录请求模型"""

    exposure_type: str = Field(..., description="曝光类型")
    platform: Optional[str] = Field(None, description="平台名称")
    placement: Optional[str] = Field(None, description="具体位置")
    view_count: int = Field(0, ge=0, description="展示次数")
    click_count: int = Field(0, ge=0, description="点击次数")


class PointTransactionCreate(BaseModel):
    """创建积分交易请求模型"""

    transaction_type: str = Field(..., description="交易类型")
    points_amount: float = Field(..., description="积分数额")
    reference_id: Optional[str] = Field(None, description="关联ID")
    description: Optional[str] = Field(None, description="交易描述")


class SocialImpactCreate(BaseModel):
    """创建社会影响力记录请求模型"""

    category: str = Field(..., description="影响力类别")
    title: str = Field(..., min_length=1, max_length=255, description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    target_beneficiaries: int = Field(0, ge=0, description="目标受益人数")
    start_date: datetime = Field(..., description="项目开始日期")
