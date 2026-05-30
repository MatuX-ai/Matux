"""
Redis客户端工具类
用于许可证存储和缓存管理
"""

from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, Optional

import redis

from config.license_config import load_sentinel_config

logger = logging.getLogger(__name__)


class RedisLicenseStore:
    """Redis许可证存储管理类"""

    def __init__(self):
        """初始化Redis连接"""
        self.config = load_sentinel_config()
        self.client = None
        self.connect()

    def connect(self):
        """建立 Redis 连接"""
        try:
            self.client = redis.Redis(
                host=self.config.storage.host,
                port=self.config.storage.port,
                db=self.config.storage.db,
                password=self.config.storage.password,
                ssl=self.config.storage.ssl,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self.client.ping()
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis 未启用或不可用，将使用内存存储模式：{e}")
            self.client = None

    def is_connected(self) -> bool:
        """检查 Redis 连接状态"""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except (ConnectionError, TimeoutError, RuntimeError):
            return False

    def store_license(self, license_key: str, license_data: Dict[str, Any]) -> bool:
        """
        存储许可证到Redis

        Args:
            license_key: 许可证密钥
            license_data: 许可证数据

        Returns:
            bool: 存储是否成功
        """
        if not self.is_connected():
            logger.warning("Redis未连接，无法存储许可证")
            return False

        try:
            # 设置过期时间
            expire_time = timedelta(hours=self.config.license.expiration_hours)

            # 存储许可证数据
            key = f"license:{license_key}"
            self.client.setex(key, expire_time, json.dumps(license_data, default=str))

            logger.info(f"许可证已存储到Redis: {license_key}")
            return True
        except Exception as e:
            logger.error(f"存储许可证失败: {e}")
            return False

    def get_license(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        从Redis获取许可证

        Args:
            license_key: 许可证密钥

        Returns:
            Dict: 许可证数据，如果不存在返回None
        """
        if not self.is_connected():
            logger.warning("Redis未连接，无法获取许可证")
            return None

        try:
            key = f"license:{license_key}"
            data = self.client.get(key)

            if data:
                license_data = json.loads(data)
                # 转换时间字符串为datetime对象
                if "expires_at" in license_data:
                    license_data["expires_at"] = datetime.fromisoformat(
                        license_data["expires_at"]
                    )
                if "issued_at" in license_data:
                    license_data["issued_at"] = datetime.fromisoformat(
                        license_data["issued_at"]
                    )

                logger.debug(f"从Redis获取许可证: {license_key}")
                return license_data
            else:
                logger.debug(f"许可证不存在: {license_key}")
                return None
        except Exception as e:
            logger.error(f"获取许可证失败: {e}")
            return None

    def delete_license(self, license_key: str) -> bool:
        """
        从Redis删除许可证

        Args:
            license_key: 许可证密钥

        Returns:
            bool: 删除是否成功
        """
        if not self.is_connected():
            logger.warning("Redis未连接，无法删除许可证")
            return False

        try:
            key = f"license:{license_key}"
            result = self.client.delete(key)

            if result:
                logger.info(f"许可证已从Redis删除: {license_key}")
                return True
            else:
                logger.warning(f"许可证不存在或删除失败: {license_key}")
                return False
        except Exception as e:
            logger.error(f"删除许可证失败: {e}")
            return False

    def update_license_status(self, license_key: str, status: str) -> bool:
        """
        更新许可证状态

        Args:
            license_key: 许可证密钥
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        license_data = self.get_license(license_key)
        if not license_data:
            return False

        try:
            license_data["status"] = status
            return self.store_license(license_key, license_data)
        except Exception as e:
            logger.error(f"更新许可证状态失败: {e}")
            return False

    def get_license_ttl(self, license_key: str) -> Optional[int]:
        """
        获取许可证剩余生存时间

        Args:
            license_key: 许可证密钥

        Returns:
            int: 剩余秒数，如果不存在返回None
        """
        if not self.is_connected():
            return None

        try:
            key = f"license:{license_key}"
            ttl = self.client.ttl(key)
            return ttl if ttl >= 0 else None
        except Exception as e:
            logger.error(f"获取许可证TTL失败: {e}")
            return None

    def flush_expired_licenses(self) -> int:
        """
        清理过期的许可证缓存

        Returns:
            int: 清理的数量
        """
        if not self.is_connected():
            return 0

        try:
            # 获取所有许可证键
            pattern = "license:*"
            keys = self.client.keys(pattern)

            cleaned_count = 0
            for key in keys:
                if self.client.ttl(key) == -2:  # 键已过期
                    self.client.delete(key)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个过期许可证")

            return cleaned_count
        except Exception as e:
            logger.error(f"清理过期许可证失败: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取许可证存储统计信息

        Returns:
            Dict: 统计信息
        """
        if not self.is_connected():
            return {"error": "Redis未连接"}

        try:
            pattern = "license:*"
            keys = self.client.keys(pattern)

            stats = {
                "total_licenses": len(keys),
                "active_licenses": 0,
                "expired_licenses": 0,
                "redis_info": self.client.info("memory"),
            }

            # 统计各状态的许可证数量
            for key in keys:
                try:
                    data = self.client.get(key)
                    if data:
                        license_data = json.loads(data)
                        status = license_data.get("status", "unknown")
                        if status == "active":
                            stats["active_licenses"] += 1
                        elif status == "expired":
                            stats["expired_licenses"] += 1
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}


# 全局 Redis 客户端实例
redis_license_store = RedisLicenseStore()

# 简单的 Redis 客户端实例（用于通用缓存）
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis 连接失败：{e}")
    redis_client = None
