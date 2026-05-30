"""
Sentinel 熔断器单元测试
测试熔断器的状态转换、降级策略和统计功能
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from backend.middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerManager,
    CircuitState,
    CircuitBreakerOpenError,
    default_fallback_response,
    circuit_breaker
)


class TestCircuitBreakerBasic:
    """基础功能测试"""

    @pytest.fixture
    def breaker(self):
        """创建默认熔断器"""
        return CircuitBreaker(
            "Test_Breaker",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout=1.0,  # 缩短超时时间用于测试
                half_open_max_calls=2
            )
        )

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, breaker):
        """测试初始状态为关闭"""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    @pytest.mark.asyncio
    async def test_successful_call_increments_success_count(self, breaker):
        """测试成功调用增加成功计数"""
        async def successful_func():
            return "success"

        result = await breaker.call(successful_func)

        assert result == "success"
        assert breaker.total_calls == 1
        assert breaker.total_successes == 1
        assert breaker.total_failures == 0

    @pytest.mark.asyncio
    async def test_failed_call_increments_failure_count(self, breaker):
        """测试失败调用增加失败计数"""
        async def failing_func():
            raise Exception("Test exception")

        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.total_failures == 1
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_stats_collection(self, breaker):
        """测试统计信息收集"""
        async def successful_func():
            return "ok"

        await breaker.call(successful_func)
        await breaker.call(successful_func)

        stats = breaker.get_stats()

        assert stats["name"] == "Test_Breaker"
        assert stats["state"] == CircuitState.CLOSED
        assert stats["total_calls"] == 2
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 0


class TestCircuitBreakerStateTransitions:
    """状态转换测试"""

    @pytest.fixture
    def breaker_config(self):
        """创建测试配置"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,
            half_open_max_calls=2
        )

    @pytest.mark.asyncio
    async def test_closed_to_open_on_failures(self, breaker_config):
        """测试连续失败导致熔断器打开"""
        breaker = CircuitBreaker("Test_Open", config=breaker_config)

        async def failing_func():
            raise Exception("Failure")

        # 连续失败 3 次
        for i in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        # 应该变为打开状态
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_open_rejects_requests(self, breaker_config):
        """测试打开状态拒绝请求"""
        breaker = CircuitBreaker("Test_Reject", config=breaker_config)

        async def failing_func():
            raise Exception("Failure")

        # 先让熔断器打开
        for i in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # 后续请求应该被拒绝（触发降级）
        async def normal_func():
            return "should not reach"

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(normal_func)

    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self, breaker_config):
        """测试超时后从打开转为半开"""
        breaker = CircuitBreaker("Test_Half_Open", config=breaker_config)

        async def failing_func():
            raise Exception("Failure")

        # 让熔断器打开
        for i in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # 等待超时
        await asyncio.sleep(1.5)  # timeout=1.0

        # 下一个请求应该触发转为半开
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self, breaker_config):
        """测试半开状态成功恢复为关闭"""
        breaker = CircuitBreaker("Test_Recover", config=breaker_config)

        async def failing_func():
            raise Exception("Failure")

        # 让熔断器打开
        for i in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        # 等待超时
        await asyncio.sleep(1.5)

        # 在半开状态成功调用
        async def success_func():
            return "success"

        # 第一次成功
        await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.success_count == 1

        # 第二次成功（达到阈值）
        await breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self, breaker_config):
        """测试半开状态失败重新打开"""
        breaker = CircuitBreaker("Test_Retry_Fail", config=breaker_config)

        async def failing_func():
            raise Exception("Failure")

        # 让熔断器打开
        for i in range(3):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        # 等待超时
        await asyncio.sleep(1.5)

        # 半开状态再次失败
        try:
            await breaker.call(failing_func)
        except Exception:
            pass

        # 应该立即回到打开状态
        assert breaker.state == CircuitState.OPEN


class TestFallbackMechanism:
    """降级机制测试"""

    @pytest.fixture
    def breaker_with_fallback(self):
        """创建带降级的熔断器"""
        async def fallback_func(*args, **kwargs):
            return {"fallback": True, "data": "fallback_data"}

        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=1.0,
            fallback_function=fallback_func
        )

        return CircuitBreaker("Test_Fallback", config=config)

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, breaker_with_fallback):
        """测试失败时触发降级"""
        async def failing_func():
            raise Exception("Failure")

        result = await breaker_with_fallback.call(failing_func)

        assert result["fallback"] == True
        assert result["data"] == "fallback_data"
        assert breaker_with_fallback.total_fallbacks == 1

    @pytest.mark.asyncio
    async def test_fallback_when_open(self, breaker_with_fallback):
        """测试熔断器打开时使用降级"""
        async def failing_func():
            raise Exception("Failure")

        # 让熔断器打开
        for i in range(2):
            try:
                await breaker_with_fallback.call(failing_func)
            except Exception:
                pass

        assert breaker_with_fallback.state == CircuitState.OPEN

        # 打开状态下调用应该使用降级
        async def normal_func():
            return "normal"

        result = await breaker_with_fallback.call(normal_func)

        assert result["fallback"] == True
        assert breaker_with_fallback.total_fallbacks == 3  # 2 次失败 + 1 次打开

    @pytest.mark.asyncio
    async def test_default_fallback_response(self):
        """测试默认降级响应"""
        result = await default_fallback_response()

        assert result["fallback"] == True
        assert "message" in result
        assert "timestamp" in result


class TestCircuitBreakerManager:
    """熔断器管理器测试"""

    @pytest.fixture(autouse=True)
    def reset_manager(self):
        """每个测试前重置管理器"""
        manager = CircuitBreakerManager.get_instance()
        manager._breakers = {}
        yield
        manager._breakers = {}

    def test_get_instance_singleton(self):
        """测试单例模式"""
        manager1 = CircuitBreakerManager.get_instance()
        manager2 = CircuitBreakerManager.get_instance()

        assert manager1 is manager2

    def test_get_breaker_creates_new(self):
        """测试获取熔断器会创建新的实例"""
        manager = CircuitBreakerManager.get_instance()

        breaker = manager.get_breaker("New_Breaker")

        assert breaker.name == "New_Breaker"
        assert len(manager.get_all_breakers()) == 1

    def test_get_breaker_returns_existing(self):
        """测试获取已存在的熔断器返回同一实例"""
        manager = CircuitBreakerManager.get_instance()

        breaker1 = manager.get_breaker("Existing_Breaker")
        breaker2 = manager.get_breaker("Existing_Breaker")

        assert breaker1 is breaker2
        assert len(manager.get_all_breakers()) == 1

    def test_get_all_stats(self):
        """测试获取所有统计信息"""
        manager = CircuitBreakerManager.get_instance()

        breaker1 = manager.get_breaker("Breaker_1")
        breaker2 = manager.get_breaker("Breaker_2")

        stats = manager.get_all_stats()

        assert len(stats) == 2
        assert "Breaker_1" in stats
        assert "Breaker_2" in stats

    def test_reset_all(self):
        """测试重置所有熔断器"""
        manager = CircuitBreakerManager.get_instance()

        breaker = manager.get_breaker("To_Reset")
        breaker.failure_count = 5
        breaker.state = CircuitState.OPEN

        manager.reset_all()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerDecorator:
    """装饰器语法测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置测试环境"""
        manager = CircuitBreakerManager.get_instance()
        manager._breakers = {}
        yield
        manager._breakers = {}

    @pytest.mark.asyncio
    async def test_decorator_basic_usage(self):
        """测试装饰器基本用法"""
        call_count = 0

        @circuit_breaker(name="Decorated_Service", failure_threshold=3)
        async def decorated_service():
            nonlocal call_count
            call_count += 1
            return "result"

        result = await decorated_service()

        assert result == "result"
        assert call_count == 1

        # 验证熔断器已创建
        manager = CircuitBreakerManager.get_instance()
        assert "Decorated_Service" in manager.get_all_breakers()

    @pytest.mark.asyncio
    async def test_decorator_with_fallback(self):
        """测试带降级的装饰器"""
        async def my_fallback(*args, **kwargs):
            return {"fallback": True}

        @circuit_breaker(
            name="Service_With_Fallback",
            failure_threshold=1,
            fallback=my_fallback
        )
        async def service_with_fallback():
            raise Exception("Always fails")

        result = await service_with_fallback()

        assert result["fallback"] == True


class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self):
        """测试半开状态最大请求数限制"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.5,
            half_open_max_calls=2
        )

        breaker = CircuitBreaker("Test_Limit", config=config)

        async def failing_func():
            raise Exception("Fail")

        # 让熔断器打开
        for i in range(2):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        # 等待超时
        await asyncio.sleep(0.6)

        async def success_func():
            return "ok"

        # 允许 2 个请求
        await breaker.call(success_func)
        await breaker.call(success_func)

        # 第 3 个请求应该被拒绝
        with pytest.raises(Exception):
            await breaker.call(success_func)

    @pytest.mark.asyncio
    async def test_concurrent_calls_thread_safety(self):
        """测试并发调用的线程安全性"""
        breaker = CircuitBreaker(
            "Test_Concurrent",
            config=CircuitBreakerConfig(failure_threshold=10)
        )

        call_count = 0

        async def increment_func():
            nonlocal call_count
            await asyncio.sleep(0.01)
            call_count += 1
            return call_count

        # 并发调用 10 次
        tasks = [breaker.call(increment_func) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 所有调用都应该成功
        assert len(results) == 10
        assert all(isinstance(r, int) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
