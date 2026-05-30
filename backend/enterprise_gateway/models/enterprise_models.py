"""
企业API网关数据模型
定义企业客户、设备白名单和访问日志等相关数据模型
"""

from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class EnterpriseClient(Base):
    """
    企业客户模型
    存储企业客户的OAuth2.0认证信息和API访问配置
    """

    __tablename__ = "enterprise_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False, comment="企业客户名称")
    client_id = Column(
        String(50), unique=True, nullable=False, comment="OAuth2 client_id"
    )
    client_secret = Column(String(100), nullable=False, comment="OAuth2 client_secret")
    redirect_uris = Column(Text, comment="允许的回调地址，多个地址用逗号分隔")
    is_active = Column(Boolean, default=True, comment="客户账户是否激活")
    api_quota_limit = Column(Integer, default=10000, comment="API调用配额限制")
    current_usage = Column(Integer, default=0, comment="当前API使用量")
    contact_email = Column(String(100), comment="联系邮箱")
    company_info = Column(JSON, comment="企业详细信息")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    devices = relationship("DeviceWhitelist", back_populates="enterprise_client")
    api_logs = relationship("EnterpriseAPILog", back_populates="enterprise_client")

    def verify_client_secret(self, secret: str) -> bool:
        """验证客户端密钥"""
        return pwd_context.verify(secret, self.client_secret)

    def set_client_secret(self, secret: str) -> None:
        """设置客户端密钥"""
        self.client_secret = pwd_context.hash(secret)

    @classmethod
    def create_hashed_secret(cls, secret: str) -> str:
        """创建哈希密钥"""
        return pwd_context.hash(secret)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "client_name": self.client_name,
            "client_id": self.client_id,
            "redirect_uris": self.redirect_uris,
            "is_active": self.is_active,
            "api_quota_limit": self.api_quota_limit,
            "current_usage": self.current_usage,
            "contact_email": self.contact_email,
            "company_info": self.company_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_quota_available(self) -> bool:
        """检查是否有可用配额"""
        return (
            self.current_usage < self.api_quota_limit if self.api_quota_limit else True
        )

    def increment_usage(self) -> None:
        """增加API使用计数"""
        self.current_usage += 1


class DeviceWhitelist(Base):
    """
    设备白名单模型
    管理企业客户允许访问API的设备列表
    """

    __tablename__ = "device_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    enterprise_client_id = Column(
        Integer, ForeignKey("enterprise_clients.id"), comment="关联的企业客户ID"
    )
    device_id = Column(String(100), nullable=False, comment="设备唯一标识")
    device_name = Column(String(100), comment="设备名称")
    ip_address = Column(String(45), comment="IP地址（支持IPv6）")
    mac_address = Column(String(17), comment="MAC地址")
    user_agent = Column(String(500), comment="用户代理信息")
    is_approved = Column(Boolean, default=False, comment="是否已批准")
    approved_by = Column(Integer, comment="审批人用户ID")
    approved_at = Column(DateTime(timezone=True), comment="审批时间")
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    # 关联关系
    enterprise_client = relationship("EnterpriseClient", back_populates="devices")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enterprise_client_id": self.enterprise_client_id,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "user_agent": self.user_agent,
            "is_approved": self.is_approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_expired(self) -> bool:
        """检查设备是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

    def is_valid(self) -> bool:
        """检查设备是否有效（已批准且未过期）"""
        return self.is_approved and not self.is_expired()


class EnterpriseAPILog(Base):
    """
    企业API访问日志模型
    记录企业客户的API调用详情用于监控和审计
    """

    __tablename__ = "enterprise_api_logs"

    id = Column(Integer, primary_key=True, index=True)
    enterprise_client_id = Column(
        Integer, ForeignKey("enterprise_clients.id"), comment="企业客户ID"
    )
    device_id = Column(String(100), comment="设备标识")
    api_endpoint = Column(String(200), comment="API端点")
    http_method = Column(String(10), comment="HTTP方法")
    status_code = Column(Integer, comment="HTTP状态码")
    response_time = Column(Float, comment="响应时间(毫秒)")
    request_size = Column(Integer, comment="请求大小(字节)")
    response_size = Column(Integer, comment="响应大小(字节)")
    user_agent = Column(String(500), comment="用户代理")
    ip_address = Column(String(45), comment="IP地址")
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), comment="访问时间"
    )

    # 关联关系
    enterprise_client = relationship("EnterpriseClient", back_populates="api_logs")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "enterprise_client_id": self.enterprise_client_id,
            "device_id": self.device_id,
            "api_endpoint": self.api_endpoint,
            "http_method": self.http_method,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


from typing import Optional

# 请求模型定义
from pydantic import BaseModel


class EnterpriseClientCreate(BaseModel):
    """企业客户创建请求模型"""

    client_name: str
    redirect_uris: Optional[str] = None
    api_quota_limit: Optional[int] = None
    contact_email: Optional[str] = None
    company_info: Optional[dict] = None


class EnterpriseClientUpdate(BaseModel):
    """企业客户更新请求模型"""

    client_name: Optional[str] = None
    redirect_uris: Optional[str] = None
    is_active: Optional[bool] = None
    api_quota_limit: Optional[int] = None
    contact_email: Optional[str] = None
    company_info: Optional[dict] = None


class DeviceApprovalRequest(BaseModel):
    """设备审批请求模型"""

    enterprise_client_id: int
    device_id: str
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    user_agent: Optional[str] = None
    approval_period_days: Optional[int] = None


class DeviceWhitelistUpdate(BaseModel):
    """设备白名单更新模型"""

    device_name: Optional[str] = None
    is_approved: Optional[bool] = None
    expires_at: Optional[datetime] = None


class OAuthTokenRequest(BaseModel):
    """OAuth2.0令牌请求模型"""

    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"
    scope: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth2.0令牌响应模型"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None


class EnterpriseAPIStats(BaseModel):
    """企业API统计模型"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time: float
    total_data_transferred: int
    active_devices: int
    period_start: datetime
    period_end: datetime
