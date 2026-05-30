"""
自适应学习路径引擎性能优化配置
包含缓存策略、并发配置和资源管理设置
"""

import asyncio
from dataclasses import dataclass
from functools import lru_cache
import threading
import time
from typing import Any, Dict, Optional


@dataclass
class PerformanceConfig:
    """性能配置类"""

    # 缓存配置
    cache_ttl_seconds: int = 300  # 5分钟缓存
    max_cache_size: int = 1000

    # 并发配置
    max_concurrent_requests: int = 100
    semaphore_timeout_seconds: int = 30

    # 内存管理
    max_memory_mb: int = 500
    cleanup_interval_seconds: int = 60

    # 响应时间目标
    target_response_time_ms: float = 150.0
    slow_query_threshold_ms: float = 500.0


class AdaptiveLearningOptimizer:
    """自适应学习引擎优化器"""

    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.stats = {
            "requests_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "slow_queries": 0,
        }
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """启动定期清理任务"""

        def cleanup_loop():
            while True:
                time.sleep(self.config.cleanup_interval_seconds)
                self._cleanup_expired_cache()
                self._log_performance_stats()

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        with self.cache_lock:
            for key, (timestamp, _) in self.cache.items():
                if current_time - timestamp > self.config.cache_ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

    def _log_performance_stats(self):
        """记录性能统计"""
        total_requests = self.stats["requests_processed"]
        if total_requests > 0:
            hit_rate = self.stats["cache_hits"] / total_requests
            avg_response = self.stats["average_response_time"]
            print(
                f"[性能统计] 总请求: {total_requests}, 缓存命中率: {hit_rate:.2%}, "
                f"平均响应时间: {avg_response:.2f}ms"
            )

    async def execute_with_optimization(
        self, func, *args, cache_key: Optional[str] = None, **kwargs
    ):
        """
        执行优化后的函数调用

        Args:
            func: 要执行的函数
            cache_key: 缓存键（如果需要缓存）
            *args, **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        start_time = time.time()

        # 使用信号量控制并发
        async with self.semaphore:
            try:
                # 检查缓存
                if cache_key and self._is_cache_valid(cache_key):
                    self.stats["cache_hits"] += 1
                    result = self._get_from_cache(cache_key)
                else:
                    self.stats["cache_misses"] += 1
                    # 执行实际函数
                    result = await func(*args, **kwargs)
                    # 缓存结果
                    if cache_key:
                        self._set_cache(cache_key, result)

                # 更新统计信息
                self._update_stats(start_time, result)
                return result

            except Exception as e:
                # 记录慢查询
                execution_time = (time.time() - start_time) * 1000
                if execution_time > self.config.slow_query_threshold_ms:
                    self.stats["slow_queries"] += 1
                    print(
                        f"[慢查询警告] {func.__name__} 执行时间: {execution_time:.2f}ms"
                    )
                raise e

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        with self.cache_lock:
            if key in self.cache:
                timestamp, _ = self.cache[key]
                return time.time() - timestamp <= self.config.cache_ttl_seconds
            return False

    def _get_from_cache(self, key: str) -> Any:
        """从缓存获取数据"""
        with self.cache_lock:
            _, value = self.cache[key]
            return value

    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        with self.cache_lock:
            # 如果缓存满了，移除最旧的条目
            if len(self.cache) >= self.config.max_cache_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
                del self.cache[oldest_key]

            self.cache[key] = (time.time(), value)

    def _update_stats(self, start_time: float, result: Any):
        """更新性能统计"""
        execution_time = (time.time() - start_time) * 1000
        self.stats["requests_processed"] += 1

        # 更新平均响应时间（使用移动平均）
        alpha = 0.1  # 平滑因子
        current_avg = self.stats["average_response_time"]
        self.stats["average_response_time"] = (
            alpha * execution_time + (1 - alpha) * current_avg
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total_requests = self.stats["requests_processed"]
        hit_rate = self.stats["cache_hits"] / max(total_requests, 1)

        return {
            "requests_processed": total_requests,
            "cache_hit_rate": hit_rate,
            "average_response_time_ms": self.stats["average_response_time"],
            "slow_queries": self.stats["slow_queries"],
            "concurrent_limit": self.config.max_concurrent_requests,
            "cache_size": len(self.cache),
        }


# 全局优化器实例
optimizer = AdaptiveLearningOptimizer()


# 便捷装饰器
def optimized(cache_key_prefix: str = ""):
    """优化装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = (
                f"{cache_key_prefix}_{hash(str(args) + str(sorted(kwargs.items())))}"
            )
            return await optimizer.execute_with_optimization(
                func, *args, cache_key=cache_key, **kwargs
            )

        return wrapper

    return decorator


# 预定义的优化配置
HIGH_PERFORMANCE_CONFIG = PerformanceConfig(
    cache_ttl_seconds=600,  # 10分钟缓存
    max_cache_size=2000,  # 更大的缓存
    max_concurrent_requests=200,  # 更高的并发
    target_response_time_ms=100.0,  # 更严格的时间要求
)

MEMORY_CONSERVATIVE_CONFIG = PerformanceConfig(
    cache_ttl_seconds=120,  # 2分钟缓存
    max_cache_size=100,  # 较小的缓存
    max_concurrent_requests=20,  # 较低的并发
    max_memory_mb=100,  # 内存限制
)


# 缓存友好的函数示例
@lru_cache(maxsize=128)
def calculate_difficulty_cached(success_rate: float) -> float:
    """带LRU缓存的难度计算"""
    if success_rate <= 0:
        return float("inf")
    if success_rate >= 1:
        return 0.1
    return 1 / (success_rate**2)


# 使用示例
"""
# 在推荐引擎中使用优化器
async def get_optimized_recommendations(self, user_id: str, db: AsyncSession):
    @optimized("recommendations")
    async def _get_recommendations_impl():
        # 原有的推荐逻辑
        return await self._original_recommendation_logic(user_id, db)
    
    return await _get_recommendations_impl()

# 获取性能指标
metrics = optimizer.get_performance_metrics()
print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
print(f"平均响应时间: {metrics['average_response_time_ms']:.2f}ms")
"""
