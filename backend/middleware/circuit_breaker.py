"""
Sentinel 熔断器集成
为第三方服务调用提供容错保护、降级策略和流量控制
"""

from fastapi.responses import JSONResponse
from fastapi import Request, Response
from functools import wraps
import time
import asyncio
from typing import Optional, Callable, Any, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============================================
# 熔断器状态枚举
# ============================================

class CircuitState:
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态，允许请求通过
    OPEN = "open"         # 熔断状态，拒绝所有请求
    HALF_OPEN = "half_open"  # 半开状态，允许部分请求测试


# ============================================
# 熔断器配置
# ============================================

class CircuitBreakerConfig:
    """熔断器配置"""

    def __init__(
        self,
        failure_threshold: int = 5,          # 失败次数阈值
        success_threshold: int = 2,          # 成功次数阈值（半开→关闭）
        timeout: float = 60.0,               # 熔断超时（秒）
        half_open_max_calls: int = 3,        # 半开状态最大请求数
        expected_exceptions: tuple = (Exception,),  # 预期异常类型
        fallback_function: Optional[Callable] = None,  # 降级函数
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exceptions = expected_exceptions
        self.fallback_function = fallback_function


# ============================================
# 熔断器类
# ============================================

class CircuitBreaker:
    """
    熔断器实现

    用法:
        breaker = CircuitBreaker("OpenAI_API", failure_threshold=5)

        @breaker
        async def call_openai_api(prompt: str):
            return await openai.ChatCompletion.create(...)
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        初始化熔断器

        Args:
            name: 熔断器名称（用于日志和监控）
            config: 熔断器配置
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # 状态管理
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change_time = datetime.utcnow()

        # 半开状态请求计数
        self.half_open_calls = 0

        # 统计信息
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_fallbacks = 0

        # 锁（用于线程安全）
        self._lock = asyncio.Lock()

    async def __call__(self, func: Callable) -> Callable:
        """装饰器调用"""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await self.call(func, *args, **kwargs)
        return wrapper

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 熔断器打开时或函数执行失败
        """
        async with self._lock:
            # 检查是否允许请求通过
            if not self._allow_request():
                # 尝试降级处理
                return await self._handle_fallback(*args, **kwargs)

        try:
            # 执行实际调用
            result = await func(*args, **kwargs)

            # 记录成功
            await self._on_success()

            return result

        except self.config.expected_exceptions as e:
            # 记录失败
            await self._on_failure(e)

            # 尝试降级处理
            return await self._handle_fallback(*args, **kwargs, original_exception=e)

    def _allow_request(self) -> bool:
        """
        检查是否允许请求通过

        Returns:
            True 允许，False 拒绝
        """
        now = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # 检查是否超过超时时间
            if now - self.last_state_change_time > timedelta(seconds=self.config.timeout):
                logger.info(f"[{self.name}] 熔断器从打开状态转为半开状态")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            else:
                remaining = self.config.timeout - \
                    (now - self.last_state_change_time).total_seconds()
                logger.warning(
                    f"[{self.name}] 熔断器处于打开状态，拒绝请求（剩余 {remaining:.1f} 秒）")
                return False

        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态只允许有限的请求
            if self.half_open_calls < self.config.half_open_max_calls:
                self.half_open_calls += 1
                return True
            else:
                logger.warning(f"[{self.name}] 半开状态已达到最大请求数，拒绝额外请求")
                return False

        return False

    async def _on_success(self):
        """处理成功响应"""
        async with self._lock:
            self.total_calls += 1
            self.total_successes += 1

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1

                # 达到成功阈值，恢复到关闭状态
                if self.success_count >= self.config.success_threshold:
                    logger.info(
                        f"[{self.name}] 熔断器从半开状态恢复为关闭状态（成功 {self.success_count} 次）")
                    self._reset_state()
            else:
                # 重置失败计数
                self.failure_count = 0

    async def _on_failure(self, exception: Exception):
        """处理失败响应"""
        async with self._lock:
            self.total_calls += 1
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            logger.error(f"[{self.name}] 调用失败：{str(exception)}")

            if self.state == CircuitState.CLOSED:
                # 达到失败阈值，打开熔断器
                if self.failure_count >= self.config.failure_threshold:
                    logger.warning(
                        f"[{self.name}] 熔断器打开（失败 {self.failure_count} 次）")
                    self.state = CircuitState.OPEN
                    self.last_state_change_time = datetime.utcnow()

            elif self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，立即回到打开状态
                logger.warning(f"[{self.name}] 半开状态调用失败，重新打开熔断器")
                self.state = CircuitState.OPEN
                self.last_state_change_time = datetime.utcnow()

    async def _handle_fallback(self, *args, original_exception: Exception = None, **kwargs) -> Any:
        """
        处理降级逻辑

        Returns:
            降级结果或抛出异常
        """
        async with self._lock:
            self.total_fallbacks += 1

        # 如果配置了降级函数，使用降级函数
        if self.config.fallback_function:
            try:
                logger.info(f"[{self.name}] 执行降级函数")
                return await self.config.fallback_function(*args, **kwargs)
            except Exception as e:
                logger.error(f"[{self.name}] 降级函数执行失败：{str(e)}")

        # 如果没有降级函数或降级失败，根据状态决定
        if self.state == CircuitState.OPEN:
            # 熔断器打开，返回友好错误
            raise CircuitBreakerOpenError(
                f"服务暂时不可用，请稍后重试（熔断器：{self.name}）",
                original_exception
            )
        else:
            # 重新抛出原始异常
            raise original_exception if original_exception else Exception(
                "Unknown error")

    def _reset_state(self):
        """重置熔断器状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_state_change_time = datetime.utcnow()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "total_fallbacks": self.total_fallbacks,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change_time": self.last_state_change_time.isoformat(),
        }


# ============================================
# 自定义异常
# ============================================

class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message


# ============================================
# 熔断器管理器
# ============================================

class CircuitBreakerManager:
    """
    熔断器管理器（单例模式）

    用法:
        manager = CircuitBreakerManager.get_instance()
        breaker = manager.get_breaker("OpenAI_API")
    """

    _instance: Optional['CircuitBreakerManager'] = None
    _breakers: Dict[str, CircuitBreaker] = {}

    def __new__(cls) -> 'CircuitBreakerManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'CircuitBreakerManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        获取或创建熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置

        Returns:
            熔断器实例
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
            logger.info(f"创建新的熔断器：{name}")

        return self._breakers[name]

    def get_all_breakers(self) -> Dict[str, CircuitBreaker]:
        """获取所有熔断器"""
        return self._breakers.copy()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的统计信息"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """重置所有熔断器"""
        for breaker in self._breakers.values():
            breaker._reset_state()
        logger.info("重置所有熔断器")


# ============================================
# 预定义的降级函数
# ============================================

async def default_fallback_response(*args, **kwargs) -> Any:
    """默认降级响应"""
    return {
        "fallback": True,
        "message": "服务暂时不可用，已返回缓存数据",
        "timestamp": datetime.utcnow().isoformat()
    }


async def cached_response_fallback(cache_key: str, *args, **kwargs) -> Any:
    """
    从缓存获取降级响应

    Args:
        cache_key: 缓存键
    """
    # 这里应该集成实际的缓存系统（如 Redis）
    # 示例实现：
    # from backend.core.redis import redis_client
    # cached = await redis_client.get(cache_key)
    # if cached:
    #     return json.loads(cached)

    logger.warning(f"缓存未命中：{cache_key}")
    return None


# ============================================
# 便捷装饰器
# ============================================

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    fallback: Optional[Callable] = None
):
    """
    便捷的熔断器装饰器

    用法:
        @circuit_breaker("OpenAI_API", failure_threshold=3, timeout=30)
        async def call_openai(...):
            ...
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        timeout=timeout,
        fallback_function=fallback
    )

    manager = CircuitBreakerManager.get_instance()
    breaker = manager.get_breaker(name, config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await breaker.call(func, *args, **kwargs)
        return wrapper

    return decorator


# ============================================
# FastAPI 中间件（可选）
# ============================================


async def circuit_breaker_middleware(request: Request, call_next) -> Response:
    """
    FastAPI 熔断器中间件

    可以全局监控 API 调用状态
    """
    start_time = time.time()

    try:
        response = await call_next(request)

        # 记录成功请求
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except CircuitBreakerOpenError as e:
        # 熔断器打开，返回 503
        logger.warning(f"熔断器打开：{str(e)}")

        return JSONResponse(
            status_code=503,
            content={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after": 60  # 建议 60 秒后重试
            }
        )

    except Exception as e:
        # 其他异常
        logger.error(f"未处理的异常：{str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "内部服务器错误"
            }
        )
