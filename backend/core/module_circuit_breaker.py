"""
模块级熔断器

三态机: CLOSED → OPEN → HALF_OPEN → CLOSED
- CLOSED: 正常状态，请求直接通过
- OPEN: 熔断状态，直接执行 fallback
- HALF_OPEN: 半开状态，允许一个探测请求通过

与 ActivationMiddleware 集成：当模块熔断时自动调用降级方案。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """熔断器状态"""

    CLOSED = "closed"         # 正常
    OPEN = "open"             # 熔断
    HALF_OPEN = "half_open"   # 半开探测


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 3        # 连续失败多少次触发熔断
    timeout: float = 60.0             # 熔断后多少秒进入半开状态
    half_open_max_calls: int = 1      # 半开状态允许的最大探测请求数
    success_threshold: int = 1        # 半开状态连续成功多少次关闭熔断


@dataclass
class CircuitBreakerStats:
    """熔断器统计数据"""

    total_calls: int = 0
    total_success: int = 0
    total_failure: int = 0
    total_fallback: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_success": self.total_success,
            "total_failure": self.total_failure,
            "total_fallback": self.total_fallback,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "state_changes": self.state_changes,
        }


class ModuleCircuitBreaker:
    """
    模块级熔断器

    用法：
        breaker = ModuleCircuitBreaker("my_module")
        result = await breaker.execute(my_async_func, fallback_func)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: float = 0.0
        self._opened_at: float = 0.0
        self._lock = asyncio.Lock()
        self.stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """当前状态（自动检查是否应该从 OPEN 转为 HALF_OPEN）"""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._opened_at
            if elapsed >= self.config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN

    def _transition_to(self, new_state: CircuitState) -> None:
        """状态转换"""
        old_state = self._state
        if old_state == new_state:
            return
        self._state = new_state
        self.stats.state_changes += 1

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0

        logger.info(
            f"🔌 熔断器状态变更: {self.name} "
            f"{old_state.value} → {new_state.value}"
        )

    async def execute(
        self,
        func: Callable,
        fallback: Optional[Callable] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        通过熔断器执行目标函数

        Args:
            func: 目标异步函数
            fallback: 降级函数（熔断时调用）
            *args, **kwargs: 传递给 func 的参数

        Returns:
            func 或 fallback 的返回值
        """
        self.stats.total_calls += 1
        current_state = self.state

        # OPEN 状态：直接执行 fallback
        if current_state == CircuitState.OPEN:
            self.stats.total_fallback += 1
            logger.warning(
                f"🔌 熔断器 OPEN，执行降级: {self.name}"
            )
            if fallback:
                return await self._call(fallback, *args, **kwargs)
            raise CircuitBreakerOpenError(
                self.name, self.config.timeout
            )

        # HALF_OPEN 状态：限制探测请求数
        if current_state == CircuitState.HALF_OPEN:
            async with self._lock:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    # 探测请求已满，走 fallback
                    self.stats.total_fallback += 1
                    if fallback:
                        return await self._call(fallback, *args, **kwargs)
                    raise CircuitBreakerOpenError(
                        self.name, self.config.timeout
                    )
                self._half_open_calls += 1

        # CLOSED 或 HALF_OPEN：尝试执行目标函数
        try:
            result = await self._call(func, *args, **kwargs)
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            # 失败后如果熔断器打开了，尝试 fallback
            if self._state == CircuitState.OPEN and fallback:
                self.stats.total_fallback += 1
                logger.warning(
                    f"🔌 调用失败后熔断器 OPEN，执行降级: {self.name}"
                )
                return await self._call(fallback, *args, **kwargs)
            raise

    async def _call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """调用函数（支持同步和异步）"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    async def _on_success(self) -> None:
        """调用成功时的处理"""
        async with self._lock:
            self.stats.total_success += 1
            self.stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    # 探测成功，关闭熔断器
                    self._failure_count = 0
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(
                        f"✅ 熔断器关闭（探测成功）: {self.name}"
                    )

            elif self._state == CircuitState.CLOSED:
                # 成功时重置失败计数
                self._failure_count = 0

    async def _on_failure(self) -> None:
        """调用失败时的处理"""
        async with self._lock:
            self.stats.total_failure += 1
            self._failure_count += 1
            self.stats.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # 半开状态探测失败，重新打开
                self._transition_to(CircuitState.OPEN)
                self._opened_at = time.time()
                logger.warning(
                    f"🔌 熔断器重新 OPEN（探测失败）: {self.name}"
                )

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    # 连续失败达到阈值，打开熔断器
                    self._transition_to(CircuitState.OPEN)
                    self._opened_at = time.time()
                    logger.warning(
                        f"🔌 熔断器 OPEN（连续失败 "
                        f"{self._failure_count} 次）: {self.name}"
                    )

    def reset(self) -> None:
        """手动重置熔断器"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self.stats = CircuitBreakerStats()
        logger.info(f"🔄 熔断器已重置: {self.name}")

    def get_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.config.failure_threshold,
            "timeout": self.config.timeout,
            "stats": self.stats.to_dict(),
        }


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""

    def __init__(self, module_name: str, timeout: float):
        self.module_name = module_name
        self.timeout = timeout
        super().__init__(
            f"模块 '{module_name}' 熔断器已打开，"
            f"请 {timeout:.0f} 秒后重试"
        )


class ModuleCircuitBreakerRegistry:
    """
    熔断器注册表

    管理所有模块的熔断器实例，提供统一的查询和操作接口。
    """

    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, ModuleCircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()

    def get_or_create(
        self,
        module_name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> ModuleCircuitBreaker:
        """获取或创建模块熔断器"""
        if module_name not in self._breakers:
            self._breakers[module_name] = ModuleCircuitBreaker(
                module_name, config or self._default_config
            )
        return self._breakers[module_name]

    def get(self, module_name: str) -> Optional[ModuleCircuitBreaker]:
        """获取模块熔断器（不存在返回 None）"""
        return self._breakers.get(module_name)

    def get_all_status(self) -> Dict[str, Any]:
        """获取所有熔断器状态"""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self) -> None:
        """重置所有熔断器"""
        for breaker in self._breakers.values():
            breaker.reset()

    @property
    def open_count(self) -> int:
        """当前处于 OPEN 状态的熔断器数量"""
        return sum(
            1 for b in self._breakers.values() if b.state == CircuitState.OPEN
        )

    @property
    def degraded_modules(self) -> list:
        """当前降级运行的模块列表"""
        return [
            name
            for name, b in self._breakers.items()
            if b.state != CircuitState.CLOSED
        ]


# ==================== 全局实例 ====================

_registry_instance: Optional[ModuleCircuitBreakerRegistry] = None


def get_breaker_registry() -> ModuleCircuitBreakerRegistry:
    """获取全局熔断器注册表"""
    if _registry_instance is None:
        raise RuntimeError(
            "ModuleCircuitBreakerRegistry 尚未初始化，"
            "请先调用 init_breaker_registry()"
        )
    return _registry_instance


def init_breaker_registry(
    config: Optional[CircuitBreakerConfig] = None,
) -> ModuleCircuitBreakerRegistry:
    """初始化全局熔断器注册表"""
    global _registry_instance
    _registry_instance = ModuleCircuitBreakerRegistry(config)
    logger.info("🔧 ModuleCircuitBreakerRegistry 已初始化")
    return _registry_instance
