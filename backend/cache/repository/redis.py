"""
【P3-D-2】Redis 仓储实现

继承 Repository[T] 抽象接口，提供 Redis Hash + Pub/Sub 跨进程持久化。

特点：
- 本地内存缓存（dict）加速读写（与 SqlAlchemyRepository 行为一致）
- Redis Hash 持久化（HSET / HGETALL / HDEL）
- Pub/Sub 跨进程通知（ai_teacher:update 通道）
- 防回声机制（publisher_id 标识）
- 优雅降级：Redis 不可用 → 仅内存
- 线程安全（threading.RLock）

数据模型：
- 每张表 = 一个 Redis Hash
  - Key:    ai_teacher:{table_name}:kv
  - Field:  user_id (str)
  - Value:  JSON-serialized data
- Pub/Sub 通道：
  - Channel: ai_teacher:update
  - Message: JSON {table, action, key, data, publisher_id, timestamp}

使用：
    from utils.redis_client import redis_client
    repo = RedisRepository("profiles", redis_client=redis_client)
    repo.set("user_1", {"name": "Alice"})
    val = repo.get("user_1")
"""

import json
import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from cache.repository.base import Repository

logger = logging.getLogger(__name__)


# 全局 channel 名称（与 P3-D-2 计划一致）
DEFAULT_CHANNEL = "ai_teacher:update"
DEFAULT_KEY_PREFIX = "ai_teacher"


class RedisRepository(Repository[Any]):
    """
    Redis 后端仓储实现（跨进程一致）

    - 内存缓存 + Redis Hash 双层架构
    - Pub/Sub 通知其他进程（可选）
    - Redis 不可用时自动降级到纯内存模式
    """

    def __init__(
        self,
        name: str,
        redis_client: Optional[Any] = None,
        key_prefix: str = DEFAULT_KEY_PREFIX,
        channel: str = DEFAULT_CHANNEL,
        enable_pubsub: bool = True,
    ) -> None:
        self._name = name
        self._key_prefix = key_prefix
        self._hash_key = f"{key_prefix}:{name}:kv"
        self._channel = channel
        self._enable_pubsub = enable_pubsub
        self._redis = redis_client
        self._local_cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._publisher_id = f"proc-{uuid.uuid4().hex[:8]}"
        # 启动时尝试从 Redis 加载
        self._load_from_redis()
        logger.info(
            f"RedisRepository 已初始化：{self._hash_key} "
            f"({len(self._local_cache)} 条历史数据, redis={'OK' if self._redis_available() else 'OFF'})"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def hash_key(self) -> str:
        return self._hash_key

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def publisher_id(self) -> str:
        return self._publisher_id

    def _redis_available(self) -> bool:
        """Redis 客户端是否可用（不为 None）"""
        return self._redis is not None

    def _load_from_redis(self) -> None:
        """从 Redis Hash 加载初始数据到本地缓存"""
        if not self._redis_available():
            return
        try:
            raw_items = self._redis.hgetall(self._hash_key)
            loaded = {}
            for field, value in raw_items.items():
                field_str = field.decode() if isinstance(field, bytes) else field
                value_str = value.decode() if isinstance(value, bytes) else value
                loaded[field_str] = json.loads(value_str)
            with self._lock:
                self._local_cache = loaded
            logger.info(
                f"从 Redis 加载 {self._hash_key}：{len(loaded)} 条"
            )
        except Exception as e:
            logger.warning(
                f"RedisRepository[{self._name}] 加载失败：{e}（纯内存模式）"
            )

    def _publish(self, action: str, key: Optional[str] = None, data: Any = None) -> None:
        """
        Pub/Sub 发布事件（仅在 enable_pubsub=True 时发布）

        Args:
            action: set | delete | replace_all | clear
            key: 受影响的 key（set/delete 时）
        """
        if not self._enable_pubsub or not self._redis_available():
            return
        try:
            message = {
                "table": self._name,
                "action": action,
                "key": key,
                "data": data,
                "publisher_id": self._publisher_id,
                "timestamp": time.time(),
            }
            payload = json.dumps(message, default=str)
            self._redis.publish(self._channel, payload)
        except Exception as e:
            logger.warning(
                f"RedisRepository[{self._name}] publish 失败：{e}"
            )

    # ---------- 远程操作方法（被 PubSubBridge 调用）----------

    def _apply_remote_set(self, key: str, value: Any) -> None:
        """Pub/Sub 接收方：应用远程 set 事件"""
        with self._lock:
            self._local_cache[key] = value

    def _apply_remote_delete(self, key: str) -> None:
        """Pub/Sub 接收方：应用远程 delete 事件"""
        with self._lock:
            self._local_cache.pop(key, None)

    def _apply_remote_replace_all(self, data: Dict[str, Any]) -> None:
        """Pub/Sub 接收方：应用远程 replace_all 事件"""
        with self._lock:
            self._local_cache = dict(data)

    def _apply_remote_clear(self) -> None:
        """Pub/Sub 接收方：应用远程 clear 事件"""
        with self._lock:
            self._local_cache = {}

    # ---------- 公共 API（Repository 接口）----------

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._local_cache.get(key, default)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._local_cache

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._local_cache.keys())

    def values(self) -> List[Any]:
        with self._lock:
            return list(self._local_cache.values())

    def items(self) -> List[Any]:
        with self._lock:
            return list(self._local_cache.items())

    def __len__(self) -> int:
        with self._lock:
            return len(self._local_cache)

    def snapshot(self) -> Dict[str, Any]:
        """返回深拷贝快照"""
        with self._lock:
            return json.loads(json.dumps(self._local_cache, default=str))

    # ---------- 写操作（Redis 写穿透 + Pub/Sub 通知）----------

    def set(self, key: str, value: Any) -> None:
        """写入：本地缓存 + Redis Hash + Pub/Sub 通知"""
        with self._lock:
            self._local_cache[key] = value
        # Redis Hash 写入
        if self._redis_available():
            try:
                payload = json.dumps(value, default=str)
                self._redis.hset(self._hash_key, key, payload)
            except Exception as e:
                logger.warning(
                    f"RedisRepository[{self._name}] hset({key}) 失败：{e}"
                )
        # Pub/Sub 通知
        self._publish("set", key=key, data=value)

    def delete(self, key: str) -> bool:
        """删除：本地缓存 + Redis Hash + Pub/Sub 通知"""
        with self._lock:
            existed = key in self._local_cache
            self._local_cache.pop(key, None)
        if existed:
            # Redis Hash 删除
            if self._redis_available():
                try:
                    self._redis.hdel(self._hash_key, key)
                except Exception as e:
                    logger.warning(
                        f"RedisRepository[{self._name}] hdel({key}) 失败：{e}"
                    )
            # Pub/Sub 通知
            self._publish("delete", key=key)
        return existed

    def clear(self) -> None:
        """清空：本地缓存 + Redis Hash + Pub/Sub 通知"""
        with self._lock:
            self._local_cache = {}
        # Redis Hash 删除
        if self._redis_available():
            try:
                self._redis.delete(self._hash_key)
            except Exception as e:
                logger.warning(
                    f"RedisRepository[{self._name}] clear 失败：{e}"
                )
        # Pub/Sub 通知
        self._publish("clear")

    def flush(self) -> None:
        """
        强制刷盘

        Redis 模式下写入已即时落库，本方法主要用于校验一致性。
        可用于：
        - 测试场景：触发 reload 校验
        - 调试场景：从 Redis 重新同步本地缓存
        """
        if self._redis_available():
            self._load_from_redis()

    def replace_all(self, data: Dict[str, Any]) -> None:
        """
        整体替换：清空 + 批量写入

        兼容性：
        - Redis 4.0+ 支持 HSET 多字段语法（HSET key f1 v1 f2 v2 ...）
        - Redis 3.2 仅支持单字段 HSET（HSET key f v）
        - 此实现用 pipeline 单字段循环，兼容 Redis 3.2 / 4.x / 5.x
        """
        with self._lock:
            self._local_cache = dict(data)
        # Redis Hash 整体替换（pipeline 单字段循环）
        if self._redis_available():
            try:
                pipe = self._redis.pipeline()
                pipe.delete(self._hash_key)
                for k, v in data.items():
                    payload = json.dumps(v, default=str)
                    pipe.hset(self._hash_key, k, payload)
                pipe.execute()
            except Exception as e:
                logger.warning(
                    f"RedisRepository[{self._name}] replace_all 失败：{e}"
                )
        # Pub/Sub 通知
        self._publish("replace_all", data=data)

    # ---------- 调试辅助 ----------

    def is_using_redis(self) -> bool:
        """是否使用 Redis 后端（用于健康检查）"""
        return self._redis_available()


__all__ = [
    "RedisRepository",
    "DEFAULT_CHANNEL",
    "DEFAULT_KEY_PREFIX",
]
