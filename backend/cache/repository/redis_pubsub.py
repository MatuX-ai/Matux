"""
【P3-D-2】Redis Pub/Sub 跨进程订阅桥

功能：
- 后台守护线程订阅 `ai_teacher:update` 通道
- 处理来自其他进程的写事件（set / delete / replace_all / clear）
- 防回声机制（publisher_id 标识）
- 指数退避自动重连

使用：
    from cache.repository.redis import RedisRepository
    from cache.repository.redis_pubsub import start_pubsub_bridge, stop_pubsub_bridge

    repos = {
        "profiles": RedisRepository("profiles", ...),
        "sessions": RedisRepository("sessions", ...),
        ...
    }
    publisher_id = start_pubsub_bridge(repos=repos)
    # 应用关闭时
    stop_pubsub_bridge()
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_CHANNEL = "ai_teacher:update"


class RedisPubSubBridge:
    """
    Pub/Sub 订阅桥（跨进程数据同步）

    - 单例模式（全局 _bridge 变量）
    - 后台守护线程
    - 启动时生成唯一 publisher_id（防回声）
    - 异常时指数退避重连
    """

    def __init__(
        self,
        redis_client: Any,
        repos: Dict[str, Any],
        channel: str = DEFAULT_CHANNEL,
    ):
        self._redis = redis_client
        self._repos = repos
        self._channel = channel
        self._publisher_id = f"proc-{uuid.uuid4().hex[:8]}"
        self._thread: Optional[Any] = None
        self._stop_event: Any = None
        self._started = False

    @property
    def publisher_id(self) -> str:
        return self._publisher_id

    def is_running(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    def start(self) -> str:
        """
        启动订阅线程

        Returns:
            publisher_id: 当前进程的唯一标识
        """
        if self._started:
            logger.warning("RedisPubSubBridge 已经启动，跳过重复启动")
            return self._publisher_id

        import threading

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="ai-teacher-pubsub-bridge",
        )
        self._thread.start()
        self._started = True
        logger.info(
            f"✅ Redis Pub/Sub 订阅已启动 "
            f"(channel={self._channel}, publisher={self._publisher_id})"
        )
        return self._publisher_id

    def stop(self, timeout: float = 5.0) -> None:
        """停止订阅线程"""
        if not self._started:
            return
        if self._stop_event is not None:
            self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._started = False
        logger.info("✅ Redis Pub/Sub 订阅已停止")

    def _run(self) -> None:
        """订阅循环（带指数退避重连）"""
        backoff = 1
        max_backoff = 30
        pubsub = None
        while not self._stop_event.is_set():
            try:
                pubsub = self._redis.pubsub()
                pubsub.subscribe(self._channel)
                logger.debug(
                    f"PubSub 订阅成功：{self._channel}"
                )
                backoff = 1  # 重置 backoff
                for message in pubsub.listen():
                    if self._stop_event.is_set():
                        break
                    if message.get("type") != "message":
                        continue
                    try:
                        self._handle_message(message["data"])
                    except Exception as e:
                        logger.warning(
                            f"PubSub 消息处理失败：{e}"
                        )
            except Exception as e:
                if self._stop_event.is_set():
                    break
                logger.warning(
                    f"PubSub 订阅异常（{backoff}s 后重连）: {e}"
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)
            finally:
                # 关闭 pubsub 连接（避免泄漏）
                try:
                    if pubsub is not None:
                        pubsub.close()
                        pubsub = None
                except Exception:
                    pass

    def _handle_message(self, raw: Any) -> None:
        """处理 Pub/Sub 消息"""
        import json

        try:
            raw_str = raw.decode() if isinstance(raw, bytes) else raw
            msg = json.loads(raw_str)
        except Exception as e:
            logger.warning(f"PubSub 消息反序列化失败：{e}")
            return

        # 防回声：忽略自己发布的消息
        if msg.get("publisher_id") == self._publisher_id:
            return

        table = msg.get("table")
        repo = self._repos.get(table)
        if repo is None:
            # 收到未知表的广播（其他服务可能也在用 channel）
            return

        action = msg.get("action")
        try:
            if action == "set":
                repo._apply_remote_set(msg["key"], msg["data"])
            elif action == "delete":
                repo._apply_remote_delete(msg["key"])
            elif action == "replace_all":
                repo._apply_remote_replace_all(msg.get("data") or {})
            elif action == "clear":
                repo._apply_remote_clear()
            else:
                logger.warning(
                    f"PubSub 未知 action：{action}（table={table}）"
                )
        except Exception as e:
            logger.warning(
                f"PubSub apply 失败（action={action}, table={table}）：{e}"
            )


# ==================== 全局单例 + 便捷方法 ====================

_bridge: Optional[RedisPubSubBridge] = None


def start_pubsub_bridge(
    redis_client: Any = None,
    repos: Optional[Dict[str, Any]] = None,
    channel: str = DEFAULT_CHANNEL,
) -> str:
    """
    启动全局 PubSub 订阅桥（单例）

    Args:
        redis_client: redis.Redis 客户端（默认使用 utils.redis_client.redis_client）
        repos: RedisRepository 实例字典（默认从 factory 全局单例获取）
        channel: Pub/Sub 通道名

    Returns:
        publisher_id: 当前进程的 publisher 标识
    """
    global _bridge
    if _bridge is not None and _bridge.is_running():
        logger.warning("PubSub bridge 已运行")
        return _bridge.publisher_id

    if redis_client is None:
        try:
            from utils.redis_client import redis_client as default_redis
            redis_client = default_redis
        except Exception as e:
            logger.warning(f"无法获取默认 Redis 客户端：{e}")
            return ""

    if repos is None:
        try:
            from cache.repository.factory import (
                get_profiles_repo,
                get_sessions_repo,
                get_memories_repo,
                get_personas_repo,
                get_live_settings_repo,
                get_event_history_repo,
                get_user_history_repo,
            )
            repos = {
                "profiles": get_profiles_repo(),
                "sessions": get_sessions_repo(),
                "memories": get_memories_repo(),
                "personas": get_personas_repo(),
                "live_settings": get_live_settings_repo(),
                "event_history": get_event_history_repo(),
                "user_history": get_user_history_repo(),
            }
        except Exception as e:
            logger.warning(f"无法获取全局 repos：{e}")
            return ""

    _bridge = RedisPubSubBridge(
        redis_client=redis_client,
        repos=repos,
        channel=channel,
    )
    return _bridge.start()


def stop_pubsub_bridge() -> None:
    """停止全局 PubSub 订阅桥"""
    global _bridge
    if _bridge is not None:
        _bridge.stop()
        _bridge = None


def get_pubsub_bridge() -> Optional[RedisPubSubBridge]:
    """获取全局 PubSub 订阅桥实例（用于测试）"""
    return _bridge


__all__ = [
    "RedisPubSubBridge",
    "DEFAULT_CHANNEL",
    "start_pubsub_bridge",
    "stop_pubsub_bridge",
    "get_pubsub_bridge",
]