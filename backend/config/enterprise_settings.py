"""
企业API网关配置设置模块
使用Pydantic BaseSettings管理企业网关环境变量
"""

from typing import List

from pydantic import validator
from pydantic_settings import BaseSettings


class EnterpriseSettings(BaseSettings):
    # 应用基本信息
    APP_NAME: str = "iMato企业API网关"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # 数据库配置
    ENTERPRISE_DATABASE_URL: str = "sqlite+aiosqlite:///./enterprise_gateway.db"

    # JWT配置
    ENTERPRISE_JWT_SECRET: str = "enterprise-secret-key-change-this-in-production"
    ENTERPRISE_JWT_ALGORITHM: str = "HS256"
    ENTERPRISE_TOKEN_EXPIRE_HOURS: int = 24

    # OAuth2.0配置
    OAUTH2_AUTHORIZE_ENDPOINT: str = "/api/enterprise/oauth/authorize"
    OAUTH2_TOKEN_ENDPOINT: str = "/api/enterprise/oauth/token"
    OAUTH2_REVOKE_ENDPOINT: str = "/api/enterprise/oauth/revoke"

    # 设备白名单配置
    DEVICE_WHITELIST_ENABLED: bool = True
    DEFAULT_DEVICE_APPROVAL_PERIOD_DAYS: int = 365

    # API配额配置
    DEFAULT_API_QUOTA_LIMIT: int = 10000
    API_RATE_LIMIT_PER_HOUR: int = 1000

    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "https://enterprise.imato.com",
        "http://localhost:3000",
    ]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/enterprise_gateway.log"

    # 安全配置
    ENABLE_DEVICE_FINGERPRINT: bool = True
    ENABLE_IP_RESTRICTION: bool = False
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    class Config:
        env_file = ".env.enterprise"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("ALLOWED_ORIGINS", pre=True)
    def validate_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# 创建全局企业设置实例
enterprise_settings = EnterpriseSettings()
