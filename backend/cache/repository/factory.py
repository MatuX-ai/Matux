"""
【P3-D-1】仓储工厂

根据配置（环境变量 / Settings）返回对应的实现：
- file  -> FileJsonRepository（P3-B 默认，向后兼容）
- sql   -> SqlAlchemyRepository（P3-D 新实现）

切换 backend 不影响调用方代码（routes / services）。

配置项：
- 环境变量 AI_TEACHER_PERSISTENCE_BACKEND（file / sql）
- 默认 file（与 P3-B 行为一致）
"""

import logging
import os
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# 7 个 AI 教师持久化仓库名（与 P3-B 完全一致）
REPOSITORY_REGISTRY: Dict[str, str] = {
    "profiles": "ai_teacher_profiles",
    "sessions": "ai_teacher_sessions",
    "memories": "ai_teacher_memories",
    "personas": "ai_teacher_personas",
    "live_settings": "ai_teacher_live_settings",
    "event_history": "ai_teacher_event_history",
    "user_history": "ai_teacher_user_history",
}


def _resolve_backend() -> str:
    """
    解析 backend 类型

    优先级：环境变量 > Settings.AI_TEACHER_PERSISTENCE_BACKEND > 默认值 file
    """
    env = os.getenv("AI_TEACHER_PERSISTENCE_BACKEND")
    if env:
        return env.lower()
    try:
        from config.settings import get_settings

        return get_settings().AI_TEACHER_PERSISTENCE_BACKEND.lower()
    except Exception:
        return "file"


def create_repository(name: str, **kwargs: Any) -> Any:
    """
    创建仓储实例（根据 backend 配置选择实现）

    Args:
        name: 仓库名（必须在 REPOSITORY_REGISTRY 中）
        **kwargs: 传递给具体实现的参数
            - FileJsonRepository: data_dir, flush_debounce_seconds
            - SqlAlchemyRepository: session_factory

    Returns:
        Repository 实例（FileJsonRepository 或 SqlAlchemyRepository）
    """
    if name not in REPOSITORY_REGISTRY:
        raise KeyError(
            f"未知仓库名：{name}。"
            f"有效值：{list(REPOSITORY_REGISTRY.keys())}"
        )

    backend = _resolve_backend()
    if backend == "sql":
        from cache.repository.sql import SqlAlchemyRepository

        return SqlAlchemyRepository(name, **kwargs)
    elif backend == "redis":
        # 【P3-D-2】Redis 后端：跨进程持久化
        from cache.repository.redis import RedisRepository

        # 默认注入全局 Redis 客户端（来自 utils.redis_client）
        if "redis_client" not in kwargs:
            try:
                from utils.redis_client import redis_client

                kwargs["redis_client"] = redis_client
            except Exception:
                logger.warning("无法导入 utils.redis_client.redis_client，Redis backend 将以纯内存模式运行")
                kwargs["redis_client"] = None
        return RedisRepository(name, **kwargs)
    elif backend == "file":
        from cache.repository.file_json import FileJsonRepository

        # 兼容旧调用：filename 而非 name
        if "filename" not in kwargs:
            kwargs["filename"] = f"{REPOSITORY_REGISTRY[name]}.json"
        return FileJsonRepository(**kwargs)
    else:
        raise ValueError(
            f"未知 backend：{backend}（有效值：file / sql / redis）"
        )


# ==================== 全局单例（向后兼容 P3-B 接口）====================

_lock = threading.RLock()
_profiles_repo: Optional[Any] = None
_sessions_repo: Optional[Any] = None
_memories_repo: Optional[Any] = None
_personas_repo: Optional[Any] = None
_live_settings_repo: Optional[Any] = None
_event_history_repo: Optional[Any] = None
_user_history_repo: Optional[Any] = None


def get_profiles_repo() -> Any:
    global _profiles_repo
    with _lock:
        if _profiles_repo is None:
            _profiles_repo = create_repository("profiles")
        return _profiles_repo


def get_sessions_repo() -> Any:
    global _sessions_repo
    with _lock:
        if _sessions_repo is None:
            _sessions_repo = create_repository("sessions")
        return _sessions_repo


def get_memories_repo() -> Any:
    global _memories_repo
    with _lock:
        if _memories_repo is None:
            _memories_repo = create_repository("memories")
        return _memories_repo


def get_personas_repo() -> Any:
    global _personas_repo
    with _lock:
        if _personas_repo is None:
            _personas_repo = create_repository("personas")
        return _personas_repo


def get_live_settings_repo() -> Any:
    global _live_settings_repo
    with _lock:
        if _live_settings_repo is None:
            _live_settings_repo = create_repository("live_settings")
        return _live_settings_repo


def get_event_history_repo() -> Any:
    global _event_history_repo
    with _lock:
        if _event_history_repo is None:
            _event_history_repo = create_repository("event_history")
        return _event_history_repo


def get_user_history_repo() -> Any:
    global _user_history_repo
    with _lock:
        if _user_history_repo is None:
            _user_history_repo = create_repository("user_history")
        return _user_history_repo


def reset_all_repos_for_testing() -> None:
    """重置所有仓储（仅用于测试）"""
    global _profiles_repo, _sessions_repo, _memories_repo, _personas_repo
    global _live_settings_repo, _event_history_repo, _user_history_repo
    with _lock:
        _profiles_repo = None
        _sessions_repo = None
        _memories_repo = None
        _personas_repo = None
        _live_settings_repo = None
        _event_history_repo = None
        _user_history_repo = None


def flush_all_repos() -> None:
    """强制立即落盘所有仓储（用于优雅关闭 / 测试）"""
    repos = [
        get_profiles_repo(),
        get_sessions_repo(),
        get_memories_repo(),
        get_personas_repo(),
        get_live_settings_repo(),
        get_event_history_repo(),
        get_user_history_repo(),
    ]
    for repo in repos:
        try:
            repo.flush()
        except Exception as e:
            logger.warning(f"flush 仓储失败：{e}")


__all__ = [
    "REPOSITORY_REGISTRY",
    "create_repository",
    "get_profiles_repo",
    "get_sessions_repo",
    "get_memories_repo",
    "get_personas_repo",
    "get_live_settings_repo",
    "get_event_history_repo",
    "get_user_history_repo",
    "reset_all_repos_for_testing",
    "flush_all_repos",
]