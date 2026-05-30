"""
Redis许可证存储配置模块
提供Redis连接和许可证存储配置
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RedisStorageConfig:
    """Redis存储配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False


@dataclass
class RedisLicenseConfig:
    """Redis许可证配置"""
    expiration_hours: int = 24


@dataclass
class SentinelConfig:
    """哨兵模式配置"""
    storage: RedisStorageConfig = field(default_factory=RedisStorageConfig)
    license: RedisLicenseConfig = field(default_factory=RedisLicenseConfig)


def load_sentinel_config() -> SentinelConfig:
    """
    加载Redis哨兵配置
    优先从环境变量读取，否则使用默认值

    Returns:
        SentinelConfig: 哨兵配置对象
    """
    config = SentinelConfig()

    # 从环境变量加载Redis存储配置
    config.storage.host = os.getenv("REDIS_HOST", config.storage.host)
    config.storage.port = int(os.getenv("REDIS_PORT", str(config.storage.port)))
    config.storage.db = int(os.getenv("REDIS_DB", str(config.storage.db)))
    config.storage.password = os.getenv("REDIS_PASSWORD", config.storage.password)
    config.storage.ssl = os.getenv("REDIS_SSL", "false").lower() == "true"

    # 从环境变量加载许可证配置
    config.license.expiration_hours = int(
        os.getenv("LICENSE_EXPIRATION_HOURS", str(config.license.expiration_hours))
    )

    return config
