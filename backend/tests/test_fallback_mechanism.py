"""
降级机制单元测试
测试 Fallback Mechanism 的各种场景和边界情况
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from backend.middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    default_fallback_response,
    cached_response_fallback
)


class TestFallbackStrategies:
    """降级策略测试"""

    @pytest.fixture
    def mock_cache(self):
        """模拟缓存系统"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        return cache

    @pytest.mark.asyncio
    async def test_default_fallback_returns_valid_response(self):
        """测试默认降级返回有效响应"""
        result = await default_fallback_response()

        assert result["fallback"] == True
        assert "message" in result
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)

    @pytest.mark.asyncio
    async def test_cached_fallback_with_hit(self, mock_cache):
        """测试缓存降级命中"""
        # 设置缓存数据
        cached_data = {"data": "cached_value", "timestamp": "2024-01-01"}
        mock_cache.get.return_value = str(cached_data).replace("'", '"')

        result = await cached_response_fallback("test_key")

        assert result is not None
        mock_cache.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cached_fallback_with_miss(self, mock_cache):
        """测试缓存降级未命中"""
        mock_cache.get.return_value = None

        result = await cached_response_fallback("non_existent_key")

        assert result is None
        mock_cache.get.assert_called_once_with("non_existent_key")


class TestFallbackWithCircuitBreaker:
    """熔断器与降级集成测试"""

    @pytest.fixture
    def breaker_config_with_fallback(self):
        """创建带降级的配置"""
        async def custom_fallback(*args, **kwargs):
            return {
                "fallback": True,
                "strategy": "custom",
                "args": args,
                "kwargs": kwargs
            }

        return CircuitBreakerConfig(
            failure_threshold=2,
            timeout=1.0,
            fallback_function=custom_fallback
        )

    @pytest.mark.asyncio
    async def test_fallback_called_on_failure(self, breaker_config_with_fallback):
        """测试失败时调用降级"""
        breaker = CircuitBreaker(
            "Test_Fail", config=breaker_config_with_fallback)

        async def failing_func():
            raise Exception("Always fails")

        result = await breaker.call(failing_func)

        assert result["fallback"] == True
        assert result["strategy"] == "custom"

    @pytest.mark.asyncio
    async def test_fallback_called_when_open(self, breaker_config_with_fallback):
        """测试熔断器打开时调用降级"""
        breaker = CircuitBreaker(
            "Test_Open", config=breaker_config_with_fallback)

        async def failing_func():
            raise Exception("Fail")

        # 让熔断器打开
        for i in range(2):
            try:
                await breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # 打开状态下应该调用降级
        async def normal_func():
            return "normal"

        result = await breaker.call(normal_func)

        assert result["fallback"] == True
        assert breaker.total_fallbacks >= 1

    @pytest.mark.asyncio
    async def test_fallback_preserves_original_args(self, breaker_config_with_fallback):
        """测试降级保留原始参数"""
        breaker = CircuitBreaker(
            "Test_Args", config=breaker_config_with_fallback)

        async def failing_func(arg1, arg2, kwarg1=None):
            raise Exception("Fail")

        result = await breaker.call(failing_func, "value1", "value2", kwarg1="value3")

        assert "value1" in result["args"]
        assert "value2" in result["args"]
        assert result["kwargs"].get("kwarg1") == "value3"


class TestAdvancedFallbackScenarios:
    """高级降级场景测试"""

    @pytest.fixture
    def multi_level_fallback_config(self):
        """创建多级降级配置"""
        async def level1_fallback(*args, **kwargs):
            # 第一级：尝试缓存
            return {"level": 1, "type": "cache"}

        async def level2_fallback(*args, **kwargs):
            # 第二级：备用服务
            return {"level": 2, "type": "backup_service"}

        async def level3_fallback(*args, **kwargs):
            # 第三级：友好提示
            return {"level": 3, "type": "friendly_message"}

        return {
            "level1": level1_fallback,
            "level2": level2_fallback,
            "level3": level3_fallback
        }

    @pytest.mark.asyncio
    async def test_cascading_fallback_levels(self, multi_level_fallback_config):
        """测试级联降级"""
        call_sequence = []

        async def service_call():
            call_sequence.append("service")
            raise Exception("Service down")

        # 模拟三级降级依次调用
        breaker = CircuitBreaker(
            "Test_Cascade",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=multi_level_fallback_config["level1"]
            )
        )

        result = await breaker.call(service_call)

        assert "service" in call_sequence
        assert result["level"] == 1

    @pytest.mark.asyncio
    async def test_fallback_with_retry_logic(self):
        """测试带重试的降级"""
        retry_count = 0
        max_retries = 3

        async def retry_fallback(*args, **kwargs):
            nonlocal retry_count
            retry_count += 1

            if retry_count < max_retries:
                raise Exception("Retry failed")

            return {"success": True, "retries": retry_count}

        breaker = CircuitBreaker(
            "Test_Retry",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=retry_fallback
            )
        )

        async def failing_service():
            raise Exception("Service failed")

        result = await breaker.call(failing_service)

        assert result["success"] == True
        assert result["retries"] == max_retries

    @pytest.mark.asyncio
    async def test_fallback_timeout_protection(self):
        """测试降级超时保护"""
        async def slow_fallback(*args, **kwargs):
            await asyncio.sleep(10)  # 模拟很慢的降级
            return {"fallback": "completed"}

        breaker = CircuitBreaker(
            "Test_Timeout",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=slow_fallback
            )
        )

        async def failing_service():
            raise Exception("Service failed")

        # 应该快速失败而不是等待 10 秒
        with pytest.raises(Exception):
            await asyncio.wait_for(
                breaker.call(failing_service),
                timeout=2.0
            )


class TestFallbackDataConsistency:
    """降级数据一致性测试"""

    @pytest.fixture
    def stateful_fallback_config(self):
        """创建有状态降级"""
        state = {"call_count": 0, "last_result": None}

        async def stateful_fallback(*args, **kwargs):
            state["call_count"] += 1
            state["last_result"] = {
                "fallback": True,
                "call_count": state["call_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
            return state["last_result"]

        return stateful_fallback, state

    @pytest.mark.asyncio
    async def test_fallback_maintains_state(self, stateful_fallback_config):
        """测试降级维护状态"""
        fallback_func, state = stateful_fallback_config

        breaker = CircuitBreaker(
            "Test_State",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=fallback_func
            )
        )

        async def failing_service():
            raise Exception("Fail")

        # 第一次调用
        result1 = await breaker.call(failing_service)
        count1 = state["call_count"]

        # 第二次调用
        result2 = await breaker.call(failing_service)
        count2 = state["call_count"]

        assert count2 > count1
        assert result2["call_count"] > result1["call_count"]

    @pytest.mark.asyncio
    async def test_fallback_idempotency(self):
        """测试降级幂等性"""
        call_results = []

        async def idempotent_fallback(*args, **kwargs):
            result = {"fallback": True, "value": "constant"}
            call_results.append(result.copy())
            return result

        breaker = CircuitBreaker(
            "Test_Idempotent",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=idempotent_fallback
            )
        )

        async def failing_service():
            raise Exception("Fail")

        # 多次调用应该返回相同结果
        result1 = await breaker.call(failing_service)
        result2 = await breaker.call(failing_service)
        result3 = await breaker.call(failing_service)

        assert result1 == result2 == result3
        assert len(call_results) == 3  # 但实际调用了 3 次


class TestFallbackPerformance:
    """降级性能测试"""

    @pytest.mark.asyncio
    async def test_fallback_execution_time(self):
        """测试降级执行时间"""
        async def fast_fallback(*args, **kwargs):
            return {"fallback": "fast"}

        breaker = CircuitBreaker(
            "Test_Perf",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=fast_fallback
            )
        )

        async def failing_service():
            raise Exception("Fail")

        start = datetime.utcnow()
        result = await breaker.call(failing_service)
        elapsed = (datetime.utcnow() - start).total_seconds()

        assert elapsed < 1.0  # 应该在 1 秒内完成
        assert result["fallback"] == "fast"

    @pytest.mark.asyncio
    async def test_concurrent_fallback_calls(self):
        """测试并发降级调用"""
        call_count = 0

        async def concurrent_fallback(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟短暂延迟
            return {"fallback": True, "id": call_count}

        breaker = CircuitBreaker(
            "Test_Concurrent",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=concurrent_fallback
            )
        )

        async def failing_service():
            raise Exception("Fail")

        # 并发调用 10 次
        tasks = [breaker.call(failing_service) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["fallback"] == True for r in results)
        assert call_count == 10  # 每次都调用降级函数


class TestFallbackErrorHandling:
    """降级错误处理测试"""

    @pytest.mark.asyncio
    async def test_fallback_itself_fails(self):
        """测试降级函数本身失败"""
        async def failing_fallback(*args, **kwargs):
            raise Exception("Fallback also failed")

        breaker = CircuitBreaker(
            "Test_Fallback_Fail",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=failing_fallback
            )
        )

        async def original_service():
            raise Exception("Original failed")

        # 原始服务和降级都失败，应该抛出异常
        with pytest.raises(Exception) as exc_info:
            await breaker.call(original_service)

        assert "Fallback also failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fallback_with_partial_success(self):
        """测试降级部分成功"""
        attempt_count = 0

        async def partial_fallback(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count == 1:
                raise Exception("First attempt fails")

            return {"partial": True, "attempt": attempt_count}

        breaker = CircuitBreaker(
            "Test_Partial",
            config=CircuitBreakerConfig(
                failure_threshold=1,
                fallback_function=partial_fallback
            )
        )

        async def failing_service():
            raise Exception("Fail")

        result = await breaker.call(failing_service)

        assert result["partial"] == True
        assert result["attempt"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
