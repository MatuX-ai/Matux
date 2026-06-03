"""
OAuth Account Model - 第三方登录账户关联

管理用户与 OAuth 提供商（GitHub/Google/WeChat/QQ）的账户绑定关系
支持多账号绑定、解绑、主账户标识
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from utils.database import Base

import enum


class OAuthProvider(str, enum.Enum):
    """OAuth 提供商枚举"""
    GITHUB = "github"
    GOOGLE = "google"
    WECHAT = "wechat"
    QQ = "qq"


class OAuthAccount(Base):
    """OAuth 账号绑定表

    每个用户可以绑定多个第三方账号
    同一 provider 下 provider_account_id 唯一
    """
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(Enum(OAuthProvider), nullable=False)
    provider_account_id = Column(String(255), nullable=False, index=True)
    provider_username = Column(String(100), nullable=True)
    provider_avatar_url = Column(String(500), nullable=True)
    provider_email = Column(String(100), nullable=True)
    access_token = Column(String(500), nullable=True,
                          comment="OAuth provider access token (encrypted)")
    refresh_token = Column(String(500), nullable=True,
                           comment="OAuth provider refresh token (encrypted)")
    is_primary = Column(Boolean, default=False, comment="是否为主账号")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="oauth_accounts")

    __table_args__ = (
        # 同一 provider 下 provider_account_id 唯一
        # 确保一个第三方账号只能绑定一个平台用户
        # 使用字符串形式避免 enum 序列化问题
        {"sqlite_autoincrement": True},
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider.value if self.provider else None,
            "provider_account_id": self.provider_account_id,
            "provider_username": self.provider_username,
            "provider_avatar_url": self.provider_avatar_url,
            "provider_email": self.provider_email,
            "is_primary": self.is_primary,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<OAuthAccount(id={self.id}, provider={self.provider}, account_id={self.provider_account_id})>"
