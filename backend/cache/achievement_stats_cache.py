"""
【P3-A-1】成就统计缓存层

使用 Redis 缓存成就的全局统计信息（unlock_rate、total_holders 等），
避免每次请求都查询数据库。带内存降级（Redis 不可用时使用进程内字典）。
"""

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 缓存 TTL（秒）
DEFAULT_TTL_SECONDS = 60


class AchievementStatsCache:
    """
    成就统计缓存（Redis 优先，内存降级）

    特性：
    1. 优先使用 Redis（如果已配置）
    2. Redis 不可用时自动降级到内存字典
    3. TTL 过期自动失效
    4. 线程安全（内存分支使用 RLock）
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._ttl = ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._memory_expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
        # Redis 客户端延迟注入（避免循环依赖）
        self._redis_client: Optional[Any] = None

    def set_redis_client(self, client: Any) -> None:
        """注入 Redis 客户端（由调用方在启动时设置）"""
        self._redis_client = client
        if client is not None:
            logger.info("✅ AchievementStatsCache 已连接 Redis")
        else:
            logger.info("ℹ️ AchievementStatsCache 使用内存模式")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期返回 None"""
        # 优先 Redis
        if self._redis_client is not None:
            try:
                raw = self._redis_client.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as e:
                logger.warning(f"Redis get 失败，降级内存: {e}")
                self._redis_client = None

        # 内存分支
        with self._lock:
            if key not in self._memory_cache:
                return None
            expiry = self._memory_expiry.get(key, 0)
            if time.time() > expiry:
                # 已过期
                del self._memory_cache[key]
                del self._memory_expiry[key]
                return None
            return self._memory_cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self._ttl
        payload = json.dumps(value, default=str)

        # 优先 Redis
        if self._redis_client is not None:
            try:
                self._redis_client.setex(key, ttl, payload)
                return
            except Exception as e:
                logger.warning(f"Redis set 失败，降级内存: {e}")
                self._redis_client = None

        # 内存分支
        with self._lock:
            self._memory_cache[key] = value
            self._memory_expiry[key] = time.time() + ttl

    def delete(self, key: str) -> None:
        """删除单个 key"""
        if self._redis_client is not None:
            try:
                self._redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete 失败: {e}")

        with self._lock:
            self._memory_cache.pop(key, None)
            self._memory_expiry.pop(key, None)

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配 pattern 的所有 key（仅内存支持）"""
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._memory_cache if pattern in k]
            for k in keys_to_delete:
                del self._memory_cache[k]
                self._memory_expiry.pop(k, None)
                count += 1
        return count

    def clear(self) -> None:
        """清空所有缓存（主要用于测试）"""
        with self._lock:
            self._memory_cache.clear()
            self._memory_expiry.clear()
        if self._redis_client is not None:
            try:
                self._redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear 失败: {e}")

    def is_using_redis(self) -> bool:
        """是否使用 Redis 后端"""
        return self._redis_client is not None


# 全局单例
achievement_stats_cache = AchievementStatsCache()


# ==================== 便捷方法 ====================


def get_batch_stats_cache_key() -> str:
    """批量统计的缓存 key"""
    return "achievement:stats:batch:v1"


def get_single_stats_cache_key(achievement_id: int) -> str:
    """单个成就统计的缓存 key"""
    return f"achievement:stats:single:{achievement_id}:v1"


def get_cached_batch_stats() -> Optional[List[Dict[str, Any]]]:
    """获取缓存的批量统计"""
    return achievement_stats_cache.get(get_batch_stats_cache_key())


def set_cached_batch_stats(stats: List[Dict[str, Any]], ttl: int = 60) -> None:
    """缓存批量统计"""
    achievement_stats_cache.set(get_batch_stats_cache_key(), stats, ttl)


def invalidate_achievement_stats(achievement_id: Optional[int] = None) -> None:
    """失效缓存（用于成就解锁后）"""
    if achievement_id is not None:
        achievement_stats_cache.delete(get_single_stats_cache_key(achievement_id))
    # 总是清掉 batch（因为可能影响整体排序）
    achievement_stats_cache.delete(get_batch_stats_cache_key())
