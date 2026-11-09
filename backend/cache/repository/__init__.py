"""Repository 抽象层。

P3-D-1 引入的仓储抽象，包含：
- Repository[T]：抽象基类
- FileJsonRepository：JSON 文件实现（P3-B 迁移过来）
- SqlAlchemyRepository：SQLAlchemy ORM 实现（P3-D 新增）
- RedisRepository：Redis Hash + Pub/Sub 实现（P3-D-2 新增）
- factory：依据环境变量选择实现
"""

from cache.repository.base import Repository
from cache.repository.factory import (
    REPOSITORY_REGISTRY,
    create_repository,
    flush_all_repos,
    get_event_history_repo,
    get_live_settings_repo,
    get_memories_repo,
    get_personas_repo,
    get_profiles_repo,
    get_sessions_repo,
    get_user_history_repo,
    reset_all_repos_for_testing,
)
from cache.repository.file_json import FileJsonRepository
from cache.repository.sql import SqlAlchemyRepository


def __getattr__(name):
    """
    延迟加载、避免未启用时强依赖 redis 库

    支持的属性：
    - RedisRepository：Redis Hash + Pub/Sub 实现
    - RedisPubSubBridge：跨进程订阅桥
    - start_pubsub_bridge / stop_pubsub_bridge / get_pubsub_bridge：
      全局单例便捷函数（用于 lifespan hook 启动 / 测试）
    - DEFAULT_CHANNEL / DEFAULT_KEY_PREFIX：Redis 实现常量
    """
    if name == "RedisRepository":
        from cache.repository.redis import RedisRepository
        return RedisRepository
    if name == "DEFAULT_CHANNEL":
        from cache.repository.redis import DEFAULT_CHANNEL
        return DEFAULT_CHANNEL
    if name == "DEFAULT_KEY_PREFIX":
        from cache.repository.redis import DEFAULT_KEY_PREFIX
        return DEFAULT_KEY_PREFIX
    if name in (
        "RedisPubSubBridge",
        "start_pubsub_bridge",
        "stop_pubsub_bridge",
        "get_pubsub_bridge",
    ):
        from cache.repository import redis_pubsub as _pubsub_mod
        return getattr(_pubsub_mod, name)
    raise AttributeError(f"module 'cache.repository' has no attribute {name!r}")


__all__ = [
    # 抽象接口
    "Repository",
    # 工厂
    "REPOSITORY_REGISTRY",
    "create_repository",
    # 实现
    "FileJsonRepository",
    "SqlAlchemyRepository",
    "RedisRepository",
    # Pub/Sub（P3-D-2）
    "RedisPubSubBridge",
    "start_pubsub_bridge",
    "stop_pubsub_bridge",
    "get_pubsub_bridge",
    # 常量
    "DEFAULT_CHANNEL",
    "DEFAULT_KEY_PREFIX",
    # 全局单例
    "get_profiles_repo",
    "get_sessions_repo",
    "get_memories_repo",
    "get_personas_repo",
    "get_live_settings_repo",
    "get_event_history_repo",
    "get_user_history_repo",
    # 工具
    "flush_all_repos",
    "reset_all_repos_for_testing",
]