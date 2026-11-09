"""
【P3-C】社交化分享数据模型

包含 3 张表：
- ShareCard：分享卡片（短链 + 二维码 + 统计）
- InviteCode：邀请码（生成、限制、奖励）
- InviteRecord：邀请记录（使用留痕）
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 复用 utils.database.Base（与 User / Achievement 等模型一致，保证 FK 可解析）
from utils.database import Base

logger = logging.getLogger(__name__)


# ==================== 卡片类型常量 ====================

class ShareCardType:
    """分享卡片类型"""
    ACHIEVEMENT = "achievement"            # 成就
    COURSE = "course"                      # 课程
    USER_PROFILE = "user_profile"          # 用户主页
    LEARNING_RECORD = "learning_record"    # 学习记录


class ShareCardStatus:
    """分享卡片状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"


class InviteCodeStatus:
    """邀请码状态"""
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    DISABLED = "disabled"


class InviteRecordStatus:
    """邀请记录状态"""
    PENDING = "pending"
    REGISTERED = "registered"
    REWARDED = "rewarded"


class RewardType:
    """奖励类型"""
    POINTS = "points"
    DISCOUNT = "discount"
    GIFT = "gift"


# ==================== ShareCard ====================


class ShareCard(Base):
    """分享卡片表"""

    __tablename__ = "share_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 卡片基本信息
    card_type = Column(String(50), nullable=False, index=True,
                       comment="achievement/course/user_profile/learning_record")
    target_id = Column(Integer, nullable=False, index=True, comment="目标对象 ID")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                        comment="创建者用户 ID")

    # 卡片内容
    title = Column(String(200), nullable=False, comment="卡片标题")
    subtitle = Column(String(500), nullable=True, comment="卡片副标题")
    cover_image = Column(String(500), nullable=True, comment="封面图 URL")
    description = Column(Text, nullable=True, comment="描述文案")
    metadata_ = Column("metadata", MutableDict.as_mutable(JSON), nullable=True, default=dict,
                        comment="扩展元数据")

    # 短链 + 二维码
    short_code = Column(String(16), nullable=False, unique=True, index=True,
                        comment="短链代码（8 字符 base62）")
    qr_code_path = Column(String(500), nullable=True, comment="二维码图片路径")

    # 统计
    view_count = Column(Integer, nullable=True, default=0, comment="浏览次数")
    share_count = Column(Integer, nullable=True, default=0, comment="分享次数")

    # 状态
    status = Column(String(20), nullable=True, default="active",
                    comment="active/expired/disabled")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(),
                        onupdate=func.now())

    # 关系
    creator = relationship("User", backref="share_cards", foreign_keys=[creator_id])

    def is_active(self) -> bool:
        """卡片是否可用"""
        if self.status != ShareCardStatus.ACTIVE:
            return False
        if self.expires_at:
            # 兼容 SQLite 测试场景：naive vs aware datetime 比较
            now = datetime.now(timezone.utc)
            expires = self.expires_at
            if expires.tzinfo is None:
                now = now.replace(tzinfo=None)
            if expires < now:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 延迟导入避免循环依赖
        from config.settings import get_settings
        try:
            base_url = get_settings().SHARE_BASE_URL
        except Exception:
            base_url = "http://localhost:8000"

        return {
            "id": self.id,
            "card_type": self.card_type,
            "target_id": self.target_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "cover_image": self.cover_image,
            "description": self.description,
            "metadata": self.metadata_ or {},
            "short_code": self.short_code,
            "short_url": f"{base_url.rstrip('/')}/share/{self.short_code}",
            "qr_code_url": f"{base_url.rstrip('/')}/api/v1/share/cards/{self.id}/qr"
                          if self.qr_code_path else None,
            "view_count": self.view_count or 0,
            "share_count": self.share_count or 0,
            "status": self.status,
            "is_active": self.is_active(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ==================== InviteCode ====================


class InviteCode(Base):
    """邀请码表"""

    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), nullable=False, unique=True, index=True,
                  comment="邀请码（8 字符 base62）")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                        comment="生成者用户 ID")

    # 使用限制
    usage_limit = Column(Integer, nullable=True, comment="使用上限（NULL=无限）")
    used_count = Column(Integer, nullable=True, default=0, comment="已使用次数")

    # 奖励配置
    reward_type = Column(String(20), nullable=True, default="points",
                         comment="points/discount/gift")
    reward_value = Column(Integer, nullable=True, default=100, comment="奖励值")

    # 渠道
    channel = Column(String(50), nullable=True, comment="wechat/weibo/x/link")

    # 状态
    status = Column(String(20), nullable=True, default="active",
                    comment="active/exhausted/expired/disabled")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    creator = relationship("User", backref="invite_codes", foreign_keys=[creator_id])

    def is_available(self) -> bool:
        """邀请码是否可用"""
        if self.status != InviteCodeStatus.ACTIVE:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        if self.expires_at:
            # 兼容 SQLite 测试场景：naive vs aware datetime 比较
            now = datetime.now(timezone.utc)
            expires = self.expires_at
            if expires.tzinfo is None:
                now = now.replace(tzinfo=None)
            if expires < now:
                return False
        return True

    def remaining(self) -> Optional[int]:
        """剩余使用次数（None = 无限）"""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - (self.used_count or 0))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "creator_id": self.creator_id,
            "usage_limit": self.usage_limit,
            "used_count": self.used_count or 0,
            "remaining": self.remaining(),
            "reward_type": self.reward_type,
            "reward_value": self.reward_value,
            "channel": self.channel,
            "status": self.status,
            "is_available": self.is_available(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==================== InviteRecord ====================


class InviteRecord(Base):
    """邀请记录表"""

    __tablename__ = "invite_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey("invite_codes.id"), nullable=False,
                     comment="邀请码 ID")
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                        comment="邀请人用户 ID")
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=True,
                        comment="被邀请人用户 ID（NULL 直到注册）")

    status = Column(String(20), nullable=True, default="pending",
                    comment="pending/registered/rewarded")
    registered_at = Column(DateTime(timezone=True), nullable=True, comment="注册时间")
    rewarded_at = Column(DateTime(timezone=True), nullable=True, comment="奖励发放时间")
    extra_metadata = Column("metadata", MutableDict.as_mutable(JSON), nullable=True, default=dict,
                            comment="扩展元数据（IP、设备等）")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    invite_code = relationship("InviteCode", backref="records", foreign_keys=[code_id])
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "code": self.invite_code.code if self.invite_code else None,
            "inviter_id": self.inviter_id,
            "invitee_id": self.invitee_id,
            "status": self.status,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "rewarded_at": self.rewarded_at.isoformat() if self.rewarded_at else None,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


__all__ = [
    "ShareCard",
    "ShareCardType",
    "ShareCardStatus",
    "InviteCode",
    "InviteCodeStatus",
    "InviteRecord",
    "InviteRecordStatus",
    "RewardType",
]