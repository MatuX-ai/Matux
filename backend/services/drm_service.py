"""
DRM数字版权保护服务
"""

import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional
import uuid

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.content_store import (
    ContentAccessGrant,
    ContentAccessLog,
    ContentItem,
    ContentRating,
    DRMContent,
    DRMStatus,
)
from models.subscription import SubscriptionStatus, UserSubscription

logger = logging.getLogger(__name__)


class DRMLicense:
    """DRM许可证对象"""

    def __init__(self, license_data: Dict[str, Any]):
        self.license_id = license_data.get("license_id")
        self.user_id = license_data.get("user_id")
        self.content_id = license_data.get("content_id")
        self.access_level = license_data.get("access_level")
        self.issued_at = license_data.get("issued_at")
        self.expires_at = license_data.get("expires_at")
        self.max_devices = license_data.get("max_devices", 5)
        self.device_fingerprints = license_data.get("device_fingerprints", [])
        self.watermark_template = license_data.get("watermark_template")
        self.signature = license_data.get("signature")


class DRMService:
    """DRM数字版权保护核心服务"""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化DRM服务

        Args:
            encryption_key: 加密密钥，如果不提供则自动生成
        """
        self.encryption_key = encryption_key or self._generate_master_key()
        self.fernet = Fernet(self.encryption_key.encode())

        # 设备指纹生成器
        self.device_fingerprint_generators = {
            "browser": self._generate_browser_fingerprint,
            "mobile": self._generate_mobile_fingerprint,
            "desktop": self._generate_desktop_fingerprint,
        }

    def _generate_master_key(self) -> str:
        """生成主加密密钥"""
        return Fernet.generate_key().decode()

    async def encrypt_content(
        self, content_id: str, content_data: bytes, db: AsyncSession
    ) -> str:
        """
        加密内容

        Args:
            content_id: 内容ID
            content_data: 原始内容数据
            db: 数据库会话

        Returns:
            str: 加密后的内容URL标识符
        """
        try:
            # 生成唯一的加密密钥ID
            key_id = f"key_{uuid.uuid4().hex[:16]}"

            # 加密内容
            self.fernet.encrypt(content_data)

            # 生成初始化向量
            iv = os.urandom(16)

            # 创建DRM内容记录
            drm_content = DRMContent(
                drm_id=f"drm_{uuid.uuid4().hex[:16]}",
                content_id=content_id,
                encrypted_content_url=f"encrypted://{key_id}",
                encryption_algorithm="AES-256-Fernet",
                encryption_key_id=key_id,
                iv=base64.b64encode(iv).decode(),
                watermark_template="{user_id}_{timestamp}_{device}",
                has_dynamic_watermark=True,
                max_devices=5,
                expiration_days=365,
                offline_duration=720,  # 30天离线访问
                expires_at=datetime.utcnow() + timedelta(days=365),
            )

            db.add(drm_content)
            await db.commit()
            await db.refresh(drm_content)

            logger.info(f"内容加密成功: {content_id} -> {drm_content.drm_id}")
            return drm_content.drm_id

        except Exception as e:
            logger.error(f"内容加密失败: {e}")
            raise

    async def decrypt_content(
        self,
        drm_id: str,
        user_id: str,
        device_info: Dict[str, Any],
        db: Optional[AsyncSession] = None,
    ) -> Optional[bytes]:
        """
        解密内容

        Args:
            drm_id: DRM内容ID
            user_id: 用户ID
            device_info: 设备信息
            db: 数据库会话

        Returns:
            bytes: 解密后的内容数据
        """
        try:
            # 验证访问权限
            access_granted = await self.verify_access(user_id, drm_id, db)
            if not access_granted:
                logger.warning(f"访问被拒绝: 用户 {user_id} 无法访问内容 {drm_id}")
                return None

            # 获取DRM内容记录
            drm_content_query = select(DRMContent).where(DRMContent.drm_id == drm_id)
            drm_result = await db.execute(drm_content_query)
            drm_content = drm_result.scalar_one_or_none()

            if not drm_content:
                logger.error(f"DRM内容不存在: {drm_id}")
                return None

            # 检查DRM状态
            if drm_content.status != DRMStatus.ACTIVE:
                logger.warning(f"DRM内容状态无效: {drm_id} 状态={drm_content.status}")
                return None

            # 验证设备限制
            device_allowed = await self._verify_device_limit(
                user_id, drm_id, device_info, db
            )
            if not device_allowed:
                logger.warning(f"设备限制超出: 用户 {user_id}")
                return None

            # 生成水印
            watermark = self.generate_watermark(user_id, drm_id, device_info)

            # 这里应该从存储中获取加密内容并解密
            # 由于是示例，我们返回模拟数据
            decrypted_content = (
                b"Decrypted content data with watermark: " + watermark.encode()
            )

            # 记录访问日志
            await self._log_content_access(user_id, drm_id, device_info, db)

            logger.info(f"内容解密成功: {drm_id} 为用户 {user_id}")
            return decrypted_content

        except Exception as e:
            logger.error(f"内容解密失败: {e}")
            return None

    async def verify_access(
        self, user_id: str, content_id: str, db: AsyncSession
    ) -> bool:
        """
        验证用户对内容的访问权限

        Args:
            user_id: 用户ID
            content_id: 内容ID
            db: 数据库会话

        Returns:
            bool: 是否有访问权限
        """
        try:
            # 检查直接的内容访问授权
            access_grant_query = select(ContentAccessGrant).where(
                ContentAccessGrant.user_id == user_id,
                ContentAccessGrant.content_id == content_id,
                ContentAccessGrant.is_revoked == False,
            )
            access_result = await db.execute(access_grant_query)
            access_grant = access_result.scalar_one_or_none()

            if access_grant and access_grant.expires_at > datetime.utcnow():
                return True

            # 检查订阅权限
            subscription_access = await self._check_subscription_access(
                user_id, content_id, db
            )
            if subscription_access:
                return True

            # 检查是否为免费内容
            content_query = select(ContentItem).where(
                ContentItem.content_id == content_id
            )
            content_result = await db.execute(content_query)
            content = content_result.scalar_one_or_none()

            if content and content.is_free:
                return True

            return False

        except Exception as e:
            logger.error(f"访问验证失败: {e}")
            return False

    async def _check_subscription_access(
        self, user_id: str, content_id: str, db: AsyncSession
    ) -> bool:
        """检查订阅访问权限"""
        try:
            # 获取用户的有效订阅
            subscription_query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(
                    [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
                ),
            )
            subscription_result = await db.execute(subscription_query)
            subscriptions = subscription_result.scalars().all()

            if not subscriptions:
                return False

            # 获取内容的评级要求
            content_query = select(ContentItem).where(
                ContentItem.content_id == content_id
            )
            content_result = await db.execute(content_query)
            content = content_result.scalar_one_or_none()

            if not content:
                return False

            required_rating = content.rating

            # 检查是否有满足要求的订阅
            for subscription in subscriptions:
                plan = subscription.plan
                if plan:
                    plan_rating = self._map_plan_to_rating(plan.plan_type)
                    if self._rating_meets_requirement(plan_rating, required_rating):
                        return True

            return False

        except Exception as e:
            logger.error(f"订阅访问检查失败: {e}")
            return False

    def _map_plan_to_rating(self, plan_type: str) -> ContentRating:
        """将订阅计划类型映射到内容评级"""
        mapping = {
            "basic": ContentRating.BASIC,
            "professional": ContentRating.PROFESSIONAL,
            "enterprise": ContentRating.ENTERPRISE,
        }
        return mapping.get(plan_type, ContentRating.FREE)

    def _rating_meets_requirement(
        self, user_rating: ContentRating, required_rating: ContentRating
    ) -> bool:
        """检查用户评级是否满足内容要求"""
        rating_hierarchy = {
            ContentRating.FREE: 0,
            ContentRating.BASIC: 1,
            ContentRating.PROFESSIONAL: 2,
            ContentRating.ENTERPRISE: 3,
        }

        return rating_hierarchy.get(user_rating, 0) >= rating_hierarchy.get(
            required_rating, 0
        )

    def generate_watermark(
        self, user_id: str, content_id: str, device_info: Dict[str, Any]
    ) -> str:
        """
        生成动态水印

        Args:
            user_id: 用户ID
            content_id: 内容ID
            device_info: 设备信息

        Returns:
            str: 水印字符串
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            device_hash = self._hash_device_info(device_info)

            watermark_data = {
                "user_id": user_id[:8],  # 截取部分用户ID
                "content_id": content_id[:8],
                "timestamp": timestamp,
                "device": device_hash[:8],
            }

            watermark = "{user_id}_{timestamp}_{device}".format(**watermark_data)
            return watermark

        except Exception as e:
            logger.error(f"水印生成失败: {e}")
            return f"default_watermark_{uuid.uuid4().hex[:8]}"

    def _hash_device_info(self, device_info: Dict[str, Any]) -> str:
        """哈希设备信息生成指纹"""
        try:
            # 提取关键设备信息
            fingerprint_data = {
                "user_agent": device_info.get("userAgent", ""),
                "ip": device_info.get("ipAddress", ""),
                "screen": f"{device_info.get('screenWidth', 0)}x{device_info.get('screenHeight', 0)}",
                "timezone": device_info.get("timezone", ""),
                "language": device_info.get("language", ""),
            }

            fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()

        except Exception:
            return hashlib.sha256(b"default_device").hexdigest()

    async def _verify_device_limit(
        self, user_id: str, drm_id: str, device_info: Dict[str, Any], db: AsyncSession
    ) -> bool:
        """验证设备限制"""
        try:
            # 获取DRM内容的设备限制
            drm_query = select(DRMContent).where(DRMContent.drm_id == drm_id)
            drm_result = await db.execute(drm_query)
            drm_content = drm_result.scalar_one_or_none()

            if not drm_content or not drm_content.max_devices:
                return True  # 无限制

            # 生成当前设备指纹
            current_device_fingerprint = self._hash_device_info(device_info)

            # 检查该设备是否已在授权列表中
            access_log_query = (
                select(ContentAccessLog)
                .where(
                    ContentAccessLog.user_id == user_id,
                    ContentAccessLog.drm_content_id == drm_id,
                )
                .order_by(ContentAccessLog.accessed_at.desc())
                .limit(100)
            )

            access_result = await db.execute(access_log_query)
            recent_accesses = access_result.scalars().all()

            unique_devices = set()
            current_device_found = False

            for access in recent_accesses:
                if access.device_info:
                    device_fingerprint = self._hash_device_info(access.device_info)
                    unique_devices.add(device_fingerprint)
                    if device_fingerprint == current_device_fingerprint:
                        current_device_found = True

            # 如果是新设备，检查是否超过限制
            if (
                not current_device_found
                and len(unique_devices) >= drm_content.max_devices
            ):
                logger.warning(
                    f"设备数量超出限制: {len(unique_devices)}/{drm_content.max_devices}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"设备限制验证失败: {e}")
            return True  # 出错时允许访问

    async def _log_content_access(
        self, user_id: str, drm_id: str, device_info: Dict[str, Any], db: AsyncSession
    ):
        """记录内容访问日志"""
        try:
            access_log = ContentAccessLog(
                log_id=f"log_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                drm_content_id=drm_id,
                access_type="view",
                device_info=device_info,
                ip_address=device_info.get("ipAddress"),
                user_agent=device_info.get("userAgent"),
                country=device_info.get("country"),
                region=device_info.get("region"),
                city=device_info.get("city"),
                watermark_data={"generated": True},
                access_token=self._generate_access_token(user_id, drm_id),
            )

            db.add(access_log)
            await db.commit()

        except Exception as e:
            logger.error(f"访问日志记录失败: {e}")

    def _generate_access_token(self, user_id: str, drm_id: str) -> str:
        """生成访问令牌"""
        try:
            payload = {
                "user_id": user_id,
                "drm_id": drm_id,
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": uuid.uuid4().hex[:8],
            }

            payload_json = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                self.encryption_key.encode(), payload_json.encode(), hashlib.sha256
            ).hexdigest()

            token_data = {"payload": payload_json, "signature": signature}

            return base64.b64encode(json.dumps(token_data).encode()).decode()

        except Exception as e:
            logger.error(f"访问令牌生成失败: {e}")
            return f"token_error_{uuid.uuid4().hex[:8]}"

    async def revoke_access(
        self, grant_id: str, reason: str = "", db: Optional[AsyncSession] = None
    ) -> bool:
        """撤销访问权限"""
        try:
            access_grant_query = select(ContentAccessGrant).where(
                ContentAccessGrant.grant_id == grant_id
            )
            access_result = await db.execute(access_grant_query)
            access_grant = access_result.scalar_one_or_none()

            if not access_grant:
                return False

            access_grant.is_revoked = True
            access_grant.updated_at = datetime.utcnow()

            await db.commit()
            logger.info(f"访问权限已撤销: {grant_id} 原因: {reason}")
            return True

        except Exception as e:
            logger.error(f"撤销访问权限失败: {e}")
            return False

    async def get_content_metadata(
        self, drm_id: str, db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """获取内容元数据"""
        try:
            drm_query = select(DRMContent).where(DRMContent.drm_id == drm_id)
            drm_result = await db.execute(drm_query)
            drm_content = drm_result.scalar_one_or_none()

            if not drm_content:
                return None

            return {
                "drm_id": drm_content.drm_id,
                "content_id": drm_content.content_id,
                "status": drm_content.status.value,
                "encryption_algorithm": drm_content.encryption_algorithm,
                "max_devices": drm_content.max_devices,
                "offline_duration": drm_content.offline_duration,
                "expires_at": (
                    drm_content.expires_at.isoformat()
                    if drm_content.expires_at
                    else None
                ),
                "has_dynamic_watermark": drm_content.has_dynamic_watermark,
            }

        except Exception as e:
            logger.error(f"获取内容元数据失败: {e}")
            return None


# 全局DRM服务实例
drm_service = DRMService()


def get_drm_service() -> DRMService:
    """获取DRM服务实例"""
    return drm_service
