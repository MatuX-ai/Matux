"""
应用配置设置模块
使用Pydantic BaseSettings管理环境变量
"""

from typing import Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用基本信息
    APP_NAME: str = "iMato AI Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True  # 开发环境启用测试数据
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_service.db"

    # Supabase 配置（可选）
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000

    # Lingma配置
    LINGMA_API_KEY: str = ""
    LINGMA_MODEL: str = "lingma-code-pro"
    LINGMA_TEMPERATURE: float = 0.7
    LINGMA_MAX_TOKENS: int = 2000

    # DeepSeek配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-coder"
    DEEPSEEK_TEMPERATURE: float = 0.7
    DEEPSEEK_MAX_TOKENS: int = 2000

    # Anthropic配置
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 2000

    # Google配置
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-pro"
    GOOGLE_TEMPERATURE: float = 0.7
    GOOGLE_MAX_TOKENS: int = 2000

    # 动态课程生成配置
    DYNAMIC_COURSE_MODEL: str = "gpt-3.5-turbo"
    DYNAMIC_COURSE_TEMPERATURE: float = 0.7
    DYNAMIC_COURSE_MAX_TOKENS: int = 1500
    DYNAMIC_COURSE_CACHE_TTL: int = 3600  # 缓存时间(秒)
    DYNAMIC_COURSE_RATE_LIMIT: int = 10  # 每小时请求限制

    # CORS配置
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:4200"

    # 许可证验证配置
    ENABLE_LICENSE_CHECK: bool = True  # 生产环境启用，DEBUG模式可禁用

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/ai_service.log"

    # 速率限制配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1小时

    # 熔断器配置
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # 秒
    CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS: int = 3
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 30  # 秒

    # Celery任务熔断器配置
    CELERY_TASK_CIRCUIT_BREAKER_ENABLED: bool = True
    CELERY_TASK_DEFAULT_TIMEOUT: int = 30  # 秒，默认任务超时时间
    CELERY_TASK_SOFT_TIMEOUT: int = 25  # 秒，默认软超时时间
    CELERY_TASK_HARD_TIMEOUT: int = 60  # 秒，默认硬超时时间
    CELERY_TASK_FAILURE_THRESHOLD: int = 3  # 任务失败阈值
    CELERY_TASK_CIRCUIT_TIMEOUT: int = 30  # 秒，熔断超时时间
    CELERY_TASK_HALF_OPEN_ATTEMPTS: int = 2  # 半开状态尝试次数
    CELERY_ENABLE_TIMEOUT_PROTECTION: bool = True  # 启用超时保护
    CELERY_ENABLE_FAILURE_PROTECTION: bool = True  # 启用失败保护

    # 监控配置
    MONITORING_ENABLED: bool = True
    PROMETHEUS_METRICS_ENDPOINT: str = "/metrics"

    # 硬件告警MQTT配置
    HARDWARE_ALERT_MQTT_ENABLED: bool = True
    HARDWARE_ALERT_MQTT_BROKER: str = "localhost"
    HARDWARE_ALERT_MQTT_PORT: int = 1883
    HARDWARE_ALERT_MQTT_USERNAME: Optional[str] = None
    HARDWARE_ALERT_MQTT_PASSWORD: Optional[str] = None
    HARDWARE_ALERT_MQTT_TOPIC_PREFIX: str = "hardware/alerts"
    HARDWARE_ALERT_MQTT_QOS: int = 1
    HARDWARE_ALERT_MQTT_TLS_ENABLED: bool = False
    HARDWARE_ALERT_MQTT_CA_CERT: Optional[str] = None
    HARDWARE_ALERT_MQTT_CLIENT_CERT: Optional[str] = None
    HARDWARE_ALERT_MQTT_CLIENT_KEY: Optional[str] = None

    # 硬件告警检测配置
    HARDWARE_ALERT_DETECTION_ENABLED: bool = True
    HARDWARE_ALERT_MONITORING_INTERVAL: int = 30  # 监控间隔(秒)
    HARDWARE_ALERT_CPU_THRESHOLD: float = 85.0  # CPU阈值(%)
    HARDWARE_ALERT_MEMORY_THRESHOLD: float = 85.0  # 内存阈值(%)
    HARDWARE_ALERT_TEMP_THRESHOLD: float = 75.0  # 温度阈值(°C)
    HARDWARE_ALERT_CRITICAL_TEMP: float = 85.0  # 临界温度(°C)
    HARDWARE_ALERT_OFFLINE_THRESHOLD: int = 120  # 离线阈值(秒)

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
    CELERY_WORKER_SEND_TASK_EVENTS: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_RESULT_EXPIRES: int = 86400  # 24 小时

    # Neo4j 图数据库配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"  # Neo4j Desktop 实例名称 (如 iMato-DB)
    NEO4J_ENABLED: bool = False  # 设置为 True 可启用 Neo4j

    # 可选路由配置 (通过环境变量控制功能模块的启用/禁用)
    ENABLE_AR_VR_ROUTES: bool = False  # AR/VR课程内容管理
    ENABLE_AR_VR_MOCK_ROUTES: bool = False  # AR/VR Mock 服务
    ENABLE_DIGITAL_TWIN_ROUTES: bool = False  # 数字孪生实验室
    ENABLE_FEDERATED_ROUTES: bool = False  # 联邦学习 API
    ENABLE_MODEL_UPDATE_ROUTES: bool = False  # AI 模型热更新
    # XR 手势识别 (与 gesture_recognition 重复)
    ENABLE_XR_GESTURE_ROUTES: bool = False

    # OAuth 配置（第三方登录）
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    QQ_APP_ID: str = ""
    QQ_APP_KEY: str = ""

    # OpenHydra 集成配置
    OPENHYDRA_API_URL: str = "http://localhost:8080"  # OpenHydra API 地址
    OPENHYDRA_API_KEY: str = "openhydra-test-key"  # OpenHydra API 密钥
    OPENHYDRA_ENABLED: bool = True  # 是否启用 OpenHydra 集成
    JUPYTERHUB_URL: str = "http://localhost:8000"  # JupyterHub 基础 URL

    # === 模块懒加载架构配置 ===
    # 是否启用懒加载架构（True=新模式，False=旧模式全量加载）
    ENABLE_LAZY_LOADING: bool = True
    # 启动时自动预加载的 Tier 层级（0=Tier0, 1=Tier0+Tier1）
    AUTO_PRELOAD_TIER: int = 1
    # 后台预加载延迟（秒），避免与启动竞争资源
    PRELOAD_DELAY_SECONDS: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",")]
            if "*" in origins:
                raise ValueError("Wildcard '*' not allowed in ALLOWED_ORIGINS")
            return origins
        return v

    @validator("PRELOAD_DELAY_SECONDS")
    def validate_preload_delay(cls, v):
        if v < 0 or v > 60:
            raise ValueError("PRELOAD_DELAY_SECONDS must be between 0 and 60")
        return v

    @validator("OPENHYDRA_API_KEY")
    def validate_openhydra_key(cls, v):
        if v and "test" in v.lower():
            import warnings
            warnings.warn("OPENHYDRA_API_KEY contains 'test', please set production key")
        return v


# 创建全局设置实例
settings = Settings()
