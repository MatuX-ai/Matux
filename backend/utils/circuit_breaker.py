"""
熔断器模式实现
用于处理区块链服务的容错和降级
"""

import asyncio
from datetime import datetime
from enum import Enum
from functools import wraps
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态枚举"""

    CLOSED = "closed"  # 关闭状态 - 正常工作
    OPEN = "open"  # 开启状态 - 熔断中
    HALF_OPEN = "half_open"  # 半开状态 - 尝试恢复


class CircuitBreaker:
    """熔断器类"""

    def __init__(
        self, failure_threshold: int = 5, timeout: int = 60, half_open_attempts: int = 3
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败阈值，超过此数量进入OPEN状态
            timeout: 熔断超时时间（秒），超时后进入HALF_OPEN状态
            half_open_attempts: 半开状态下允许的尝试次数
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化熔断器"""
        logger.info(
            f"熔断器初始化完成 - 阈值: {self.failure_threshold}, 超时: {self.timeout}s"
        )

    def get_state(self) -> str:
        """获取当前状态"""
        return self.state.value

    async def _can_execute(self) -> bool:
        """检查是否可以执行操作"""
        async with self._lock:
            current_time = datetime.now()

            if self.state == CircuitState.CLOSED:
                return True

            elif self.state == CircuitState.OPEN:
                # 检查是否超时
                if (current_time - self.last_failure_time).seconds >= self.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("熔断器进入半开状态")
                    return True
                return False

            elif self.state == CircuitState.HALF_OPEN:
                return self.success_count < self.half_open_attempts

    async def _on_success(self):
        """操作成功时的处理"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_attempts:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("熔断器恢复正常状态")

    async def _on_failure(self):
        """操作失败时的处理"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"熔断器开启 - 连续失败 {self.failure_count} 次")

            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("熔断器重新开启 - 半开状态测试失败")

    async def reset(self):
        """重置熔断器"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info("熔断器已重置")

    @classmethod
    def protected(cls, func: Callable = None, *, fallback: Callable = None):
        """
        装饰器：保护函数免受连续失败影响

        Args:
            func: 被装饰的函数
            fallback: 降级函数
        """

        def decorator(f):
            @wraps(f)
            async def wrapper(self, *args, **kwargs):
                # 获取熔断器实例
                circuit_breaker = getattr(self, "circuit_breaker", None)
                if not circuit_breaker:
                    # 如果没有熔断器，直接执行原函数
                    return await f(self, *args, **kwargs)

                # 检查是否可以执行
                if not await circuit_breaker._can_execute():
                    if fallback:
                        logger.warning("熔断器开启，执行降级逻辑")
                        return await fallback(self, *args, **kwargs)
                    else:
                        raise Exception("服务暂时不可用，请稍后再试")

                try:
                    # 执行原函数
                    result = await f(self, *args, **kwargs)
                    # 记录成功
                    await circuit_breaker._on_success()
                    return result

                except Exception as e:
                    # 记录失败
                    await circuit_breaker._on_failure()
                    logger.error(f"受保护的函数执行失败: {e}")
                    if fallback:
                        logger.info("执行降级逻辑")
                        return await fallback(self, *args, **kwargs)
                    else:
                        raise

            return wrapper

        if func is None:
            return decorator
        else:
            return decorator(func)


# 默认熔断器配置
DEFAULT_CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,
    "timeout": 60,
    "half_open_attempts": 3,
}
