"""
应用配置设置模块
使用Pydantic BaseSettings管理环境变量
"""

import logging
import os
from pathlib import Path
import secrets
import sys
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ============================================================================
# 运行时目录解析（开发模式 / 桌面端冻结模式）
# ----------------------------------------------------------------------------
# 两种模式的「可写目录」语义不同：
#   - 开发模式：以 backend/.env、backend/ai_service.db（相对 CWD）为准，行为不变
#   - 桌面端（PyInstaller 冻结）：安装目录可能只读，且升级会整体覆盖，因此配置与
#     数据库必须落在用户数据目录（%APPDATA%\\matux-desktop，与 Electron
#     app.getPath('userData') 同名）。否则会出现两个上线级缺陷：
#       1. 没有 .env → SECRET_KEY 每次启动随机 → 重启后 JWT 全部失效（强制重登）
#       2. DATABASE_URL 相对 CWD → 数据库写进安装目录（随包分发的开发库）
# ============================================================================
IS_FROZEN = bool(getattr(sys, "frozen", False))


def _resolve_user_data_dir() -> Path:
    """桌面端用户数据目录（可写，跨版本升级保留）。"""
    override = os.getenv("IMATO_USER_DATA_DIR", "").strip()
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "matux-desktop"
    return Path.home() / ".matux-desktop"


def _bundle_dir() -> Path:
    """只读资源目录：冻结态为 _internal/，开发态为 backend/。"""
    if IS_FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


# 只读资源根目录（打包内置只读文件）
BUNDLE_DIR = _bundle_dir()
# 用户数据目录（仅冻结态启用；开发模式为 None，完全沿用旧行为）
USER_DATA_DIR: Optional[Path] = _resolve_user_data_dir() if IS_FROZEN else None
# 打包内置 .env（只读，随包携带非敏感默认配置）
BUNDLE_ENV_FILE = BUNDLE_DIR / ".env"
# 用户数据目录下的 .env（可写，持久化 SECRET_KEY / DATABASE_URL）
USER_ENV_FILE: Optional[Path] = (
    (USER_DATA_DIR / ".env") if USER_DATA_DIR is not None else None
)


def _upsert_env_key(text: str, key: str, value: str) -> str:
    """在 dotenv 文本中设置 key：存在则整行替换，不存在则追加。"""
    lines = text.splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        if stripped.split("=", 1)[0].strip() == key:
            lines[idx] = f"{key}={value}"
            replaced = True
    if not replaced:
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def _read_env_value(text: str, key: str) -> str:
    """从 dotenv 文本读取单个键的值（忽略注释与空行）。"""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, _, v = stripped.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return ""


def _migrate_legacy_database(target_db: Path) -> None:
    """把旧版本落在安装目录的数据库迁移到用户数据目录（只做一次）。

    1.0.x 的 cwd=resources/backend，数据库路径为相对 CWD 的 ./ai_service.db。
    升级到用户数据目录后必须把老库搬过去，否则用户已有的账号与学习记录会「消失」。
    """
    if target_db.exists():
        return
    candidates = [
        # exe 布局：resources/backend/dist/main_ai_edu/main_ai_edu.exe → resources/backend
        Path(sys.executable).resolve().parent.parent.parent / "ai_service.db",
        # 兼容直接从 backend/ 启动的旧部署（cwd=resources/backend）
        Path.cwd() / "ai_service.db",
        # 1.0.4 安装器的兜底暂存：per-machine 安装时 SetShellVarContext all 会把
        # "$APPDATA" 解析成 C:\ProgramData，旧库被复制到公共 AppData 而应用读不到。
        # 安装器已在用户 Roaming 写主副本；这里再兜底读一次公共暂存。
        Path(os.getenv("ProgramData", "C:\\ProgramData")) / "matux-desktop" / "ai_service.db",
    ]
    for legacy in candidates:
        try:
            if legacy.is_file() and legacy.stat().st_size > 0:
                target_db.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy2(legacy, target_db)
                logger.warning("已把旧版本数据库迁移到用户数据目录：%s -> %s", legacy, target_db)
                return
        except OSError:  # pragma: no cover - 迁移失败不应阻断启动
            continue


def _read_user_env_text() -> str:
    """读取已有用户级 .env；不存在时返回空文本。

    注意：不把打包内的 .env.example 当模板 —— 它含占位符
    （SECRET_KEY=your-secret-key-here...），一旦“继承”会让所有安装包共用同一个
    已知密钥，比随机密钥更危险。
    """
    if USER_ENV_FILE is None or not USER_ENV_FILE.exists():
        return ""
    try:
        return USER_ENV_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""


# 已知占位符标记：出现任一项则视为无效密钥，必须重新生成
_PLACEHOLDER_SECRET_MARKERS = (
    "your-secret-key",
    "change-in-production",
    "changeme",
    "placeholder",
    "dev-secret",
    "test-secret",
)


def _is_valid_secret(value: str) -> bool:
    """SECRET_KEY 有效性：足够长且不是已知占位符。"""
    if len(value) < 32:
        return False
    lowered = value.lower()
    return not any(marker in lowered for marker in _PLACEHOLDER_SECRET_MARKERS)


def _write_user_env(text: str) -> bool:
    """把配置写入用户数据目录（失败仅告警，不阻断启动）。"""
    if USER_ENV_FILE is None or USER_DATA_DIR is None:
        return False
    try:
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        USER_ENV_FILE.write_text(text, encoding="utf-8")
        return True
    except OSError as exc:  # pragma: no cover - 只读用户目录时降级为进程内密钥
        logger.warning("无法写入用户级 .env（%s）：%s", USER_ENV_FILE, exc)
        return False


def _bootstrap_user_env() -> None:
    """冻结态首次启动生成用户级 .env（固定 SECRET_KEY、绝对 DATABASE_URL）。

    幂等：已存在且有效时只做键值纠偏，不会重新生成密钥。
    开发模式（非冻结）直接返回，不产生任何副作用。
    """
    if USER_ENV_FILE is None or USER_DATA_DIR is None:
        return

    text = _read_user_env_text()

    # 1) SECRET_KEY：缺失/过短/占位符时生成一次并持久化
    if not _is_valid_secret(_read_env_value(text, "SECRET_KEY")):
        text = _upsert_env_key(text, "SECRET_KEY", secrets.token_urlsafe(48))

    # 2) DATABASE_URL：固定为绝对路径，避免写进安装目录
    db_path = USER_DATA_DIR / "ai_service.db"
    text = _upsert_env_key(
        text, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}"
    )

    if not _write_user_env(text):
        return

    _migrate_legacy_database(db_path)


_bootstrap_user_env()

# 应用环境变量文件路径（供日志/诊断使用）
# 说明：pydantic-settings 的 env_file 若使用相对路径，是相对于「当前工作目录」
# 解析的 —— 从仓库根目录启动后端时 .env 会静默失效（配置全部退回默认值）。
# 这里固定为绝对路径，保证任意 CWD 下配置加载行为一致。
ENV_FILE_PATH = str(USER_ENV_FILE if USER_ENV_FILE is not None else BUNDLE_ENV_FILE)

# 多个 env_file 按顺序加载，后者覆盖前者：打包内置默认值 < 用户数据目录持久化值
ENV_FILES: tuple = (
    (str(BUNDLE_ENV_FILE), str(USER_ENV_FILE))
    if USER_ENV_FILE is not None
    else (str(BUNDLE_ENV_FILE),)
)

# 数据库默认地址：冻结态绝对路径（用户数据目录），开发态保持相对 CWD
_DEFAULT_DATABASE_URL = (
    f"sqlite+aiosqlite:///{(USER_DATA_DIR / 'ai_service.db').as_posix()}"
    if USER_DATA_DIR is not None
    else "sqlite+aiosqlite:///./ai_service.db"
)


class Settings(BaseSettings):
    # ========================================================================
    # 安全配置（生产环境必须设置）
    # ========================================================================

    # JWT 密钥 - 生产环境必须设置，否则自动生成（仅用于开发）
    SECRET_KEY: str = Field(
        default="",
        description="JWT签名密钥，生产环境必须设置"
    )

    # DEBUG 模式 - 生产环境必须设为 False
    DEBUG: bool = Field(
        default=False,
        description="调试模式，生产环境必须关闭"
    )

    # 应用基本信息
    APP_NAME: str = "iMato AI Service"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置（冻结态默认落用户数据目录，开发态保持相对 CWD）
    DATABASE_URL: str = _DEFAULT_DATABASE_URL

    # Supabase 配置（可选）
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # JWT配置
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
    DEEPSEEK_MODEL: str = "deepseek-chat"
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

    # Hermes Agent 配置 (Nous Research)
    HERMES_HOST: str = "http://localhost:8080"
    HERMES_API_KEY: str = ""
    HERMES_MODEL: str = "hermes-3-llama-3.1-8b"
    HERMES_TEMPERATURE: float = 0.7
    HERMES_MAX_TOKENS: int = 2000

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

    # 【P3-E】风控系统配置
    RISK_CONTROL_ENABLED: bool = True
    RISK_CONTROL_AUTO_BLOCK_HOURS: int = 1
    CAPTCHA_PROVIDER: str = "noop"  # noop / hcaptcha / recaptcha / tencent
    CAPTCHA_HCAPTCHA_SECRET: str = ""
    CAPTCHA_HCAPTCHA_SITE_KEY: str = ""
    CAPTCHA_TENCENT_SECRET_ID: str = ""
    CAPTCHA_TENCENT_SECRET_KEY: str = ""
    CAPTCHA_TENCENT_CAPTCHA_APP_ID: str = ""
    CAPTCHA_TOKEN_TTL_SECONDS: int = 300  # 一次性 token 默认 5 分钟

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
    NEO4J_PASSWORD: str = Field(
        default="",
        description="Neo4j密码，生产环境必须设置"
    )
    NEO4J_DATABASE: str = "neo4j"  # Neo4j Desktop 实例名称 (如 iMato-DB)
    NEO4J_ENABLED: bool = False  # 设置为 True 可启用 Neo4j

    # 可选路由配置 (通过环境变量控制功能模块的启用/禁用)
    ENABLE_AR_VR_ROUTES: bool = False  # AR/VR课程内容管理
    ENABLE_AR_VR_MOCK_ROUTES: bool = False  # AR/VR Mock 服务
    ENABLE_DIGITAL_TWIN_ROUTES: bool = False  # 数字孪生实验室
    ENABLE_FEDERATED_ROUTES: bool = False  # 联邦学习 API
    ENABLE_MODEL_UPDATE_ROUTES: bool = False  # AI 模型热更新
    # AI 模型版本文件存储目录：默认 backend/data/models（基于 __file__ 解析，
    # 与启动 CWD 无关），可用环境变量 MODEL_STORAGE_PATH 覆盖。
    # ModelUpdateService 初始化时会按该路径 mkdir(parents=True, exist_ok=True)。
    MODEL_STORAGE_PATH: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "data" / "models"),
        description="AI 模型版本文件的存储目录",
    )
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

    # 【P3修复】OAuth 配置验证：占位符检测
    _PLACEHOLDER_PATTERNS = [
        "your_",
        "placeholder",
        "example",
        "xxx",
        "test_",
    ]

    # OpenHydra 集成配置
    OPENHYDRA_API_URL: str = "http://localhost:8080"  # OpenHydra API 地址
    OPENHYDRA_API_KEY: str = Field(
        default="",
        description="OpenHydra API密钥，生产环境必须设置"
    )
    OPENHYDRA_ENABLED: bool = True  # 是否启用 OpenHydra 集成
    JUPYTERHUB_URL: str = "http://localhost:8000"  # JupyterHub 基础 URL

    # === 模块懒加载架构配置 ===
    # 是否启用懒加载架构（True=新模式，False=旧模式全量加载）
    # 启用后所有模块支持按需加载，ModuleActiveGuard 可正常获取模块状态
    ENABLE_LAZY_LOADING: bool = True
    # 启动时自动预加载的 Tier 层级（0=Tier0, 1=Tier0+Tier1）
    AUTO_PRELOAD_TIER: int = 1
    # 后台预加载延迟（秒），避免与启动竞争资源
    PRELOAD_DELAY_SECONDS: float = 2.0

    # === AI 教师持久化配置 ===
    # 【P3-D-1】持久化后端选择
    # - file: 默认，JSON 文件持久化（P3-B 引入）
    # - sql:  SQLAlchemy ORM + SQLite 持久化（P3-D 新增）
    # - redis: Redis Hash + Pub/Sub 跨进程持久化（P3-D-2 新增）
    # 运行时也可通过环境变量 AI_TEACHER_PERSISTENCE_BACKEND 覆盖
    AI_TEACHER_PERSISTENCE_BACKEND: str = "file"
    AI_TEACHER_REDIS_URL: str = "redis://localhost:6379/0"  # Redis 连接 URL
    AI_TEACHER_PERSISTENCE_USE_PUBSUB: bool = True  # 是否启用跨进程通知

    # === 社交化分享配置 ===
    # 【P3-C】分享平台基础 URL（用于生成短链 + 二维码）
    SHARE_BASE_URL: str = "http://localhost:8000"
    # 二维码存储目录（相对于项目根目录）
    QR_CODE_STORAGE_DIR: str = "backend/static/qrcodes"
    # 默认邀请奖励积分
    DEFAULT_INVITE_REWARD_POINTS: int = 100
    # 邀请码默认有效期（天，None=永不过期）
    DEFAULT_INVITE_EXPIRY_DAYS: Optional[int] = 30

    # === 服务器配置 ===
    # 最大 worker 进程数（生产环境），避免高配机器上资源耗尽
    MAX_WORKERS: int = Field(default=8, ge=1, le=32)
    # 强制单进程模式（调试用）
    FORCE_SINGLE_WORKER: bool = False

    # ========================================================================
    # Pydantic v2 配置
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 忽略额外的环境变量
    )

    # ========================================================================
    # 字段验证器（使用 Pydantic v2 语法）
    # ========================================================================

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        import os
        is_production = os.getenv(
            "ENVIRONMENT", "development").lower() == "production"

        if not v:
            if is_production:
                # 【P1修复】生产环境必须设置 SECRET_KEY
                raise ValueError(
                    "SECRET_KEY is required in production environment. "
                    "Set a secure random key in .env file. "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            else:
                # 开发环境仅警告
                import warnings
                warnings.warn(
                    "SECRET_KEY not set! Using auto-generated key. "
                    "This is NOT safe for production. Set SECRET_KEY in .env",
                    RuntimeWarning,
                    stacklevel=2
                )
                return secrets.token_urlsafe(32)
        if len(v) < 32:
            if is_production:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters for production. "
                    f"Current length: {len(v)}"
                )
            else:
                import warnings
                warnings.warn(
                    f"SECRET_KEY is too short ({len(v)} chars). Use at least 32 characters.",
                    RuntimeWarning,
                    stacklevel=2
                )
        return v

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def validate_origins(cls, v):
        """
        验证 ALLOWED_ORIGINS（支持字符串或列表）
        - 字符串：逗号分隔的 origins
        - 列表：直接使用
        """
        import os
        is_production = os.getenv(
            "ENVIRONMENT", "development").lower() == "production"

        if isinstance(v, str):
            origins = [origin.strip()
                       for origin in v.split(",") if origin.strip()]
            if "*" in origins:
                raise ValueError("Wildcard '*' not allowed in ALLOWED_ORIGINS")
            # 【P2修复】生产环境警告 localhost 配置
            if is_production and any("localhost" in origin for origin in origins):
                import warnings
                warnings.warn(
                    "ALLOWED_ORIGINS contains localhost in production environment. "
                    "This is insecure and should be changed to production domains.",
                    UserWarning,
                    stacklevel=2
                )
            return origins
        elif isinstance(v, list):
            if "*" in v:
                raise ValueError("Wildcard '*' not allowed in ALLOWED_ORIGINS")
            # 【P2修复】生产环境警告 localhost 配置
            if is_production and any("localhost" in origin for origin in v):
                import warnings
                warnings.warn(
                    "ALLOWED_ORIGINS contains localhost in production environment. "
                    "This is insecure and should be changed to production domains.",
                    UserWarning,
                    stacklevel=2
                )
            return v
        return v if v else []

    @field_validator("PRELOAD_DELAY_SECONDS")
    @classmethod
    def validate_preload_delay(cls, v: float) -> float:
        if v < 0 or v > 60:
            raise ValueError("PRELOAD_DELAY_SECONDS must be between 0 and 60")
        return v

    @field_validator("OPENHYDRA_API_KEY")
    @classmethod
    def validate_openhydra_key(cls, v: str) -> str:
        if v and "test" in v.lower():
            import warnings
            warnings.warn(
                "OPENHYDRA_API_KEY contains 'test', please set production key",
                UserWarning,
                stacklevel=2
            )
        return v

    @field_validator("NEO4J_PASSWORD")
    @classmethod
    def validate_neo4j_password(cls, v: str) -> str:
        if not v:
            import warnings
            warnings.warn(
                "NEO4J_PASSWORD not set! Neo4j connection will fail. "
                "Set NEO4J_PASSWORD in .env for production.",
                RuntimeWarning,
                stacklevel=2
            )
        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v: bool) -> bool:
        if v:
            import warnings
            warnings.warn(
                "DEBUG mode is ON! This is insecure for production. "
                "Set DEBUG=false in production environment.",
                RuntimeWarning,
                stacklevel=2
            )
        return v

    @field_validator("GITHUB_CLIENT_ID", "GOOGLE_CLIENT_ID", "WECHAT_APP_ID", "QQ_APP_ID")
    @classmethod
    def validate_oauth_client_id(cls, v: str) -> str:
        """【P3修复】检测 OAuth Client ID 是否为占位符"""
        if not v:
            return v
        v_lower = v.lower()
        # 检查是否匹配占位符模式
        for pattern in Settings._PLACEHOLDER_PATTERNS:
            if pattern in v_lower:
                import warnings
                warnings.warn(
                    f"OAuth Client ID '{v[:20]}...' appears to be a placeholder. "
                    f"Set a real Client ID from your OAuth provider.",
                    UserWarning,
                    stacklevel=2
                )
                break
        return v


def _generate_secret_key() -> str:
    """生成安全的随机密钥（仅用于开发）"""
    return secrets.token_urlsafe(32)


# ========================================================================
# 创建全局设置实例（延迟初始化，避免循环导入）
# ========================================================================
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取设置实例（延迟初始化）"""
    global settings
    if settings is None:
        settings = Settings()
    return settings


# 为向后兼容，提供全局 settings 实例
# 注意：在模块首次导入时会触发 Settings() 实例化
# 如果需要延迟初始化，使用 get_settings() 函数
# 【P3-D-1 修复】移除 pytest 分支——pytest 也需要 settings 完整加载
# （utils/database.py 在导入时就引用 settings.DATABASE_URL）
try:
    settings = Settings()
except Exception:
    # 【P1修复】配置加载失败必须显式暴露：静默降级为 settings=None 会让下游
    # 模块拿到 None 后抛出 'NoneType' has no attribute 之类的误导性错误。
    logger.error(
        "Settings 初始化失败：无法加载应用配置（env_file=%s）。"
        "已终止启动，避免以静默失效的默认配置继续运行。",
        ENV_FILE_PATH,
        exc_info=True,
    )
    raise
