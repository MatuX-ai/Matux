"""
企业赞助管理系统配置文件
包含性能优化和安全加固相关配置
"""

from dataclasses import dataclass
import os
from typing import Any, Dict


@dataclass
class PerformanceConfig:
    """性能配置"""

    # 数据库连接池配置
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # 缓存配置
    REDIS_CACHE_TTL: int = 3600  # 1小时
    REDIS_ANALYTICS_TTL: int = 7200  # 2小时
    REDIS_RATE_LIMIT_TTL: int = 3600  # 1小时

    # API限流配置
    API_RATE_LIMIT: str = "100/minute"  # 每分钟100次请求
    API_BULK_OPERATIONS_LIMIT: int = 1000  # 批量操作限制

    # 查询优化
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    QUERY_TIMEOUT_SECONDS: int = 30


@dataclass
class SecurityConfig:
    """安全配置"""

    # 输入验证
    MAX_STRING_LENGTH: int = 1000
    MAX_JSON_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 认证安全
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_DAYS: int = 30
    FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    # 数据安全
    ENCRYPT_SENSITIVE_DATA: bool = True
    AUDIT_LOG_ENABLED: bool = True
    DATA_RETENTION_DAYS: int = 365 * 3  # 3年

    # CORS配置
    ALLOWED_ORIGINS: list = None
    ALLOWED_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: list = ["*"]


@dataclass
class BusinessConfig:
    """业务逻辑配置"""

    # 积分规则
    BASE_POINTS_PER_VIEW: float = 0.1
    MIN_CLICK_RATE_FOR_BONUS: float = 0.05  # 5%
    ENGAGEMENT_BONUS_PER_ACTION: float = 0.5

    # 转换规则
    MIN_SPONSORSHIP_AMOUNT_DEFAULT: float = 10000.0
    POINTS_EXPIRATION_DAYS: int = 730  # 2年

    # 统计配置
    ANALYTICS_REFRESH_INTERVAL: int = 300  # 5分钟
    REALTIME_METRICS_WINDOW: int = 3600  # 1小时

    # 通知配置
    ALERT_THRESHOLD_CONVERSION_RATE: float = 1.0
    ALERT_THRESHOLD_POINTS_BALANCE: float = 100.0


class SponsorshipSettings:
    """赞助系统设置管理类"""

    def __init__(self):
        self.performance = PerformanceConfig()
        self.security = SecurityConfig()
        self.business = BusinessConfig()

        # 动态配置加载
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 性能配置
        self.performance.DATABASE_POOL_SIZE = int(
            os.getenv("DB_POOL_SIZE", self.performance.DATABASE_POOL_SIZE)
        )
        self.performance.REDIS_CACHE_TTL = int(
            os.getenv("REDIS_CACHE_TTL", self.performance.REDIS_CACHE_TTL)
        )
        self.performance.API_RATE_LIMIT = os.getenv(
            "API_RATE_LIMIT", self.performance.API_RATE_LIMIT
        )

        # 安全配置
        self.security.JWT_EXPIRATION_HOURS = int(
            os.getenv("JWT_EXPIRES_HOURS", self.security.JWT_EXPIRATION_HOURS)
        )
        self.security.FAILED_LOGIN_ATTEMPTS = int(
            os.getenv("FAILED_LOGIN_ATTEMPTS", self.security.FAILED_LOGIN_ATTEMPTS)
        )

        # 业务配置
        self.business.BASE_POINTS_PER_VIEW = float(
            os.getenv("BASE_POINTS_PER_VIEW", self.business.BASE_POINTS_PER_VIEW)
        )
        self.business.POINTS_EXPIRATION_DAYS = int(
            os.getenv("POINTS_EXPIRATION_DAYS", self.business.POINTS_EXPIRATION_DAYS)
        )

    def get_exposure_multiplier(self, exposure_type: str) -> float:
        """获取曝光类型积分倍数"""
        multipliers = {
            "banner": 1.0,
            "sidebar": 0.8,
            "popup": 1.2,
            "email": 1.5,
            "social_media": 1.3,
            "content_integration": 2.0,
        }
        return multipliers.get(exposure_type, 1.0)

    def get_conversion_rule_limits(self, rule_name: str) -> Dict[str, Any]:
        """获取转换规则限制"""
        limits = {
            "educational_resources": {
                "min_sponsorship": 10000.0,
                "personal_limit": 5,
                "validity_days": 365,
            },
            "environmental_project": {
                "min_sponsorship": 20000.0,
                "personal_limit": 3,
                "validity_days": 730,
            },
            "technology_fund": {
                "min_sponsorship": 50000.0,
                "personal_limit": 2,
                "validity_days": 1095,
            },
        }
        return limits.get(rule_name, limits["educational_resources"])


# 全局配置实例
sponsorship_settings = SponsorshipSettings()


def get_sponsorship_config() -> SponsorshipSettings:
    """获取赞助系统配置实例"""
    return sponsorship_settings
