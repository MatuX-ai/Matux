"""
缓存管理器
简单的内存缓存实现
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SimpleCacheManager:
    """简单缓存管理器"""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            # 检查是否过期（默认5分钟）
            if key in self._timestamps:
                if datetime.now() - self._timestamps[key] > timedelta(minutes=5):
                    self.delete(key)
                    return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, expire_minutes: int = 5) -> None:
        """设置缓存值"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    def delete(self, key: str) -> None:
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._timestamps.clear()


# 全局缓存实例
cache_manager = SimpleCacheManager()
