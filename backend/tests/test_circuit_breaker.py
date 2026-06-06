"""
模块级熔断器单元测试

测试 ModuleCircuitBreaker 的三态机转换、执行包装、降级调用
"""

from core.module_circuit_breaker import (
    ModuleCircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
    ModuleCircuitBreakerRegistry,
)
import asyncio
import sys
import os
import time

import pytest

# 确保 backend 目录在 sys.path 中
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))


# ==================== 状态转换测试 ====================

class TestStateTransitions:
    """熔断器状态转换测试"""

    def test_initial_state_is_closed(self):
        """测试初始状态为 CLOSED"""
        breaker = ModuleCircuitBreaker("test_module")

        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
        assert breaker.is_open is False
        assert breaker.is_half_open is False

    @pytest.mark.asyncio
    async def test_closed_to_open_on_failures(self):
        """测试连续失败应从 CLOSED 转为 OPEN"""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60.0)
        breaker = ModuleCircuitBreaker("test_module", config)

        async def failing_func():
            raise ValueError("Test error")

        # 连续失败 3 次
        for _ in range(3):
            try:
                await breaker.execute(failing_func)
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.total_failure == 3

    def test_open_to_half_open_after_timeout(self):
        """测试超时后应从 OPEN 转为 HALF_OPEN"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        breaker = ModuleCircuitBreaker("test_module", config)

        # 手动设置为 OPEN
        breaker._state = CircuitState.OPEN
        breaker._opened_at = time.time() - 0.2  # 200ms 前打开

        # 检查状态应自动转为 HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self):
        """测试 HALF_OPEN 状态下成功应关闭熔断器"""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.01,
            success_threshold=1,
        )
        breaker = ModuleCircuitBreaker("test_module", config)

        # 先触发熔断
        async def failing_func():
            raise ValueError("Test error")

        try:
            await breaker.execute(failing_func)
        except ValueError:
            pass

        assert breaker.state == CircuitState.OPEN

        # 等待超时进入 HALF_OPEN
        await asyncio.sleep(0.02)

        # 执行成功函数
        async def success_func():
            return "ok"

        result = await breaker.execute(success_func)

        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        """测试 HALF_OPEN 状态下失败应重新打开"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        breaker = ModuleCircuitBreaker("test_module", config)

        # 先触发熔断
        async def failing_func():
            raise ValueError("Test error")

        try:
            await breaker.execute(failing_func)
        except ValueError:
            pass

        # 等待超时进入 HALF_OPEN
        await asyncio.sleep(0.02)

        # 再次失败
        try:
            await breaker.execute(failing_func)
        except ValueError:
            pass

        assert breaker.state == CircuitState.OPEN


# ==================== 执行测试 ====================

class TestExecute:
    """熔断器执行测试"""

    @pytest.mark.asyncio
    async def test_execute_success_in_closed_state(self):
        """测试 CLOSED 状态下执行成功"""
        breaker = ModuleCircuitBreaker("test_module")

        async def success_func():
            return 42

        result = await breaker.execute(success_func)

        assert result == 42
        assert breaker.stats.total_calls == 1
        assert breaker.stats.total_success == 1

    @pytest.mark.asyncio
    async def test_execute_failure_in_closed_state(self):
        """测试 CLOSED 状态下执行失败"""
        breaker = ModuleCircuitBreaker("test_module")

        async def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await breaker.execute(failing_func)

        assert breaker.stats.total_failure == 1

    @pytest.mark.asyncio
    async def test_execute_fallback_in_open_state(self):
        """测试 OPEN 状态下应执行 fallback"""
        breaker = ModuleCircuitBreaker("test_module")
        breaker._state = CircuitState.OPEN
        breaker._opened_at = time.time()

        async def main_func():
            raise ValueError("Should not be called")

        async def fallback_func():
            return "fallback_result"

        result = await breaker.execute(main_func, fallback_func)

        assert result == "fallback_result"
        assert breaker.stats.total_fallback == 1

    @pytest.mark.asyncio
    async def test_execute_no_fallback_raises_exception(self):
        """测试 OPEN 状态且无 fallback 应抛出异常"""
        breaker = ModuleCircuitBreaker("test_module")
        breaker._state = CircuitState.OPEN
        breaker._opened_at = time.time()

        async def main_func():
            pass

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.execute(main_func)

    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        """测试执行同步函数"""
        breaker = ModuleCircuitBreaker("test_module")

        def sync_func():
            return "sync_result"

        result = await breaker.execute(sync_func)

        assert result == "sync_result"


# ==================== 统计测试 ====================

class TestStatistics:
    """统计数据测试"""

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """测试统计数据追踪"""
        breaker = ModuleCircuitBreaker("test_module")

        async def success_func():
            return "ok"

        async def failing_func():
            raise ValueError("Error")

        # 执行 3 次成功,2 次失败
        for _ in range(3):
            await breaker.execute(success_func)

        for _ in range(2):
            try:
                await breaker.execute(failing_func)
            except ValueError:
                pass

        assert breaker.stats.total_calls == 5
        assert breaker.stats.total_success == 3
        assert breaker.stats.total_failure == 2
        assert breaker.stats.last_success_time is not None
        assert breaker.stats.last_failure_time is not None

    def test_get_status(self):
        """测试获取熔断器状态"""
        breaker = ModuleCircuitBreaker("test_module")

        status = breaker.get_status()

        assert status["name"] == "test_module"
        assert status["state"] == "closed"
        assert "failure_threshold" in status
        assert "stats" in status


# ==================== 重置测试 ====================

class TestReset:
    """重置测试"""

    def test_reset_breaker(self):
        """测试手动重置熔断器"""
        breaker = ModuleCircuitBreaker("test_module")
        breaker._state = CircuitState.OPEN
        breaker._failure_count = 5
        breaker.stats.total_calls = 10

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0
        assert breaker.stats.total_calls == 0


# ==================== 注册表测试 ====================

class TestRegistry:
    """熔断器注册表测试"""

    def test_get_or_create_breaker(self):
        """测试获取或创建熔断器"""
        registry = ModuleCircuitBreakerRegistry()

        breaker1 = registry.get_or_create("module_a")
        breaker2 = registry.get_or_create("module_a")

        # 同一模块应返回相同实例
        assert breaker1 is breaker2

    def test_get_nonexistent_breaker(self):
        """测试获取不存在的熔断器"""
        registry = ModuleCircuitBreakerRegistry()

        breaker = registry.get("nonexistent")

        assert breaker is None

    def test_get_all_status(self):
        """测试获取所有熔断器状态"""
        registry = ModuleCircuitBreakerRegistry()

        registry.get_or_create("module_a")
        registry.get_or_create("module_b")

        status = registry.get_all_status()

        assert len(status) == 2
        assert "module_a" in status
        assert "module_b" in status

    def test_reset_all_breakers(self):
        """测试重置所有熔断器"""
        registry = ModuleCircuitBreakerRegistry()

        breaker_a = registry.get_or_create("module_a")
        breaker_b = registry.get_or_create("module_b")

        breaker_a._state = CircuitState.OPEN
        breaker_b._state = CircuitState.HALF_OPEN

        registry.reset_all()

        assert breaker_a.state == CircuitState.CLOSED
        assert breaker_b.state == CircuitState.CLOSED

    def test_open_count(self):
        """测试 OPEN 状态计数"""
        registry = ModuleCircuitBreakerRegistry()

        breaker_a = registry.get_or_create("module_a")
        breaker_b = registry.get_or_create("module_b")
        breaker_c = registry.get_or_create("module_c")

        breaker_a._state = CircuitState.OPEN
        breaker_b._state = CircuitState.OPEN

        assert registry.open_count == 2

    def test_degraded_modules(self):
        """测试获取降级模块列表"""
        registry = ModuleCircuitBreakerRegistry()

        breaker_a = registry.get_or_create("module_a")
        breaker_b = registry.get_or_create("module_b")
        breaker_c = registry.get_or_create("module_c")

        breaker_a._state = CircuitState.OPEN
        breaker_b._state = CircuitState.HALF_OPEN

        degraded = registry.degraded_modules

        assert len(degraded) == 2
        assert "module_a" in degraded
        assert "module_b" in degraded
        assert "module_c" not in degraded


# ==================== 全局实例测试 ====================

class TestGlobalInstance:
    """全局实例测试"""

    def test_init_and_get_registry(self):
        """测试初始化和获取全局注册表"""
        from core.module_circuit_breaker import init_breaker_registry, get_breaker_registry

        registry = init_breaker_registry()

        assert registry is not None
        assert get_breaker_registry() is registry

    def test_get_registry_before_init(self):
        """测试未初始化时获取应抛出异常"""
        from core.module_circuit_breaker import _registry_instance, get_breaker_registry
        import core.module_circuit_breaker as breaker_module

        old_instance = _registry_instance

        try:
            breaker_module._registry_instance = None

            with pytest.raises(RuntimeError, match="尚未初始化"):
                get_breaker_registry()
        finally:
            breaker_module._registry_instance = old_instance


# ==================== 配置测试 ====================

class TestConfiguration:
    """配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 3
        assert config.timeout == 60.0
        assert config.half_open_max_calls == 1
        assert config.success_threshold == 1

    def test_custom_config(self):
        """测试自定义配置"""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=120.0,
            half_open_max_calls=3,
            success_threshold=2,
        )

        assert config.failure_threshold == 5
        assert config.timeout == 120.0
        assert config.half_open_max_calls == 3
        assert config.success_threshold == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
