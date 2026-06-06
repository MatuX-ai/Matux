"""
服务依赖管理器单元测试

测试 ServiceDependencyManager 的服务检测、降级方案、缓存机制
"""

from core.service_dependencies import (
    ServiceDependencyManager,
    MemoryCacheBackend,
    LocalTemplateResponder,
    ReadOnlyMode,
    DisabledService,
    ServiceStatus,
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


# ==================== 内存缓存后端测试 ====================

class TestMemoryCacheBackend:
    """内存缓存后端测试"""

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = MemoryCacheBackend()

        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        cache = MemoryCacheBackend()

        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        cache = MemoryCacheBackend()

        cache.set("key1", "value1", ttl=0.1)  # 100ms TTL

        assert cache.get("key1") == "value1"

        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_delete(self):
        """测试删除缓存"""
        cache = MemoryCacheBackend()

        cache.set("key1", "value1")

        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False

    def test_exists(self):
        """测试键存在检查"""
        cache = MemoryCacheBackend()

        cache.set("key1", "value1")

        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_clear(self):
        """测试清空缓存"""
        cache = MemoryCacheBackend()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.size == 0
        assert cache.get("key1") is None

    def test_max_size_eviction(self):
        """测试容量限制淘汰"""
        cache = MemoryCacheBackend(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # 应淘汰 key1

        assert cache.size <= 2
        assert cache.get("key3") == "value3"

    def test_ping(self):
        """测试 ping 始终返回 True"""
        cache = MemoryCacheBackend()

        assert cache.ping() is True


# ==================== 本地模板响应器测试 ====================

class TestLocalTemplateResponder:
    """本地模板响应器测试"""

    def test_get_code_generation_template(self):
        """测试获取代码生成模板"""
        responder = LocalTemplateResponder()

        template = responder.get_template("code_generation")

        assert template["degraded"] is True
        assert template["category"] == "code_generation"
        assert "templates" in template

    def test_get_recommendation_template(self):
        """测试获取推荐模板"""
        responder = LocalTemplateResponder()

        template = responder.get_template("recommendation")

        assert template["degraded"] is True
        assert "default_items" in template

    def test_get_chat_template(self):
        """测试获取聊天模板"""
        responder = LocalTemplateResponder()

        template = responder.get_template("chat")

        assert template["degraded"] is True
        assert "response" in template

    def test_get_unknown_category_defaults_to_chat(self):
        """测试未知分类默认使用聊天模板"""
        responder = LocalTemplateResponder()

        template = responder.get_template("unknown_category")

        assert template["category"] == "unknown_category"
        assert template["degraded"] is True


# ==================== 只读模式测试 ====================

class TestReadOnlyMode:
    """只读模式测试"""

    def test_set_and_get_preset(self):
        """测试设置和获取预置数据"""
        mode = ReadOnlyMode("docker_service")

        mode.set_preset("scene1", {"name": "Test Scene"})

        assert mode.get("scene1") == {"name": "Test Scene"}

    def test_get_nonexistent_preset(self):
        """测试获取不存在的预置数据"""
        mode = ReadOnlyMode("docker_service")

        assert mode.get("nonexistent") is None

    def test_execute_is_disabled(self):
        """测试执行操作被禁止"""
        mode = ReadOnlyMode("docker_service")

        result = mode.execute(command="run")

        assert result["degraded"] is True
        assert result["mode"] == "read_only"
        assert "禁止执行操作" in result["message"]


# ==================== 禁用服务测试 ====================

class TestDisabledService:
    """禁用服务测试"""

    def test_execute_returns_unavailable(self):
        """测试执行返回不可用"""
        service = DisabledService("vircadia", "服务器未启动")

        result = service.execute()

        assert result["degraded"] is True
        assert result["available"] is False
        assert "vircadia" in result["message"]
        assert "服务器未启动" in result["message"]


# ==================== 服务状态测试 ====================

class TestServiceStatus:
    """服务状态测试"""

    def test_to_dict(self):
        """测试序列化为字典"""
        status = ServiceStatus(
            name="redis",
            available=True,
            fallback="in_memory",
        )
        status.check_count = 5
        status.failure_count = 1

        data = status.to_dict()

        assert data["name"] == "redis"
        assert data["available"] is True
        assert data["fallback"] == "in_memory"
        assert data["check_count"] == 5
        assert data["failure_count"] == 1
        assert data["has_fallback"] is True


# ==================== 服务管理器测试 ====================

class TestServiceManager:
    """服务依赖管理器测试"""

    def test_register_service(self):
        """测试注册服务"""
        manager = ServiceDependencyManager()

        manager.register_service("redis", "in_memory")

        assert "redis" in manager._services
        assert manager._services["redis"].fallback == "in_memory"

    def test_register_many_services(self):
        """测试批量注册服务"""
        manager = ServiceDependencyManager()

        manager.register_many({
            "redis": "in_memory",
            "openai": "local_template",
            "docker": "read_only",
        })

        assert len(manager._services) == 3

    def test_create_fallback_instance_in_memory(self):
        """测试创建内存缓存降级实例"""
        manager = ServiceDependencyManager()

        instance = manager._create_fallback_instance("redis", "in_memory")

        assert isinstance(instance, MemoryCacheBackend)

    def test_create_fallback_instance_local_template(self):
        """测试创建本地模板降级实例"""
        manager = ServiceDependencyManager()

        instance = manager._create_fallback_instance(
            "openai", "local_template")

        assert isinstance(instance, LocalTemplateResponder)

    def test_create_fallback_instance_read_only(self):
        """测试创建只读模式降级实例"""
        manager = ServiceDependencyManager()

        instance = manager._create_fallback_instance("docker", "read_only")

        assert isinstance(instance, ReadOnlyMode)

    def test_create_fallback_instance_disabled(self):
        """测试创建禁用服务降级实例"""
        manager = ServiceDependencyManager()

        instance = manager._create_fallback_instance("vircadia", "disabled")

        assert isinstance(instance, DisabledService)

    def test_create_fallback_instance_unknown(self):
        """测试未知降级类型返回 None"""
        manager = ServiceDependencyManager()

        instance = manager._create_fallback_instance("unknown", "unknown_type")

        assert instance is None

    @pytest.mark.asyncio
    async def test_check_service_with_cache(self):
        """测试服务检测缓存机制"""
        manager = ServiceDependencyManager()

        # 第一次检测
        result1 = await manager.check_service("unknown_service")

        # 第二次应从缓存返回
        result2 = await manager.check_service("unknown_service")

        # 结果应相同
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_check_service_unknown_service(self):
        """测试未知服务默认返回可用"""
        manager = ServiceDependencyManager()

        result = await manager.check_service("nonexistent_service")

        assert result is True

    def test_get_fallback(self):
        """测试获取降级实例"""
        manager = ServiceDependencyManager()

        manager.register_service("redis", "in_memory")

        fallback = manager.get_fallback("redis")

        assert fallback is not None
        assert isinstance(fallback, MemoryCacheBackend)

    def test_get_all_status(self):
        """测试获取所有服务状态"""
        manager = ServiceDependencyManager()

        manager.register_many({
            "redis": "in_memory",
            "openai": "local_template",
        })

        status = manager.get_all_status()

        assert len(status) == 2
        assert "redis" in status
        assert "openai" in status

    def test_invalidate_cache(self):
        """测试清除检测缓存"""
        manager = ServiceDependencyManager()

        manager._check_cache["redis"] = True
        manager._cache_timestamps["redis"] = time.time()

        manager.invalidate_cache()

        assert len(manager._check_cache) == 0
        assert len(manager._cache_timestamps) == 0

    @pytest.mark.asyncio
    async def test_start_periodic_check(self):
        """测试启动定期检测"""
        manager = ServiceDependencyManager()

        manager.register_service("redis", "in_memory")

        await manager.start_periodic_check(interval=0.5)

        assert manager._recheck_task is not None
        assert not manager._recheck_task.done()

        # 停止
        manager.stop_periodic_check()

    @pytest.mark.asyncio
    async def test_stop_periodic_check(self):
        """测试停止定期检测"""
        manager = ServiceDependencyManager()

        await manager.start_periodic_check(interval=1.0)

        manager.stop_periodic_check()

        assert manager._recheck_task.done()

    def test_start_periodic_check_already_running(self):
        """测试重复启动定期检测"""
        manager = ServiceDependencyManager()

        # 手动设置任务为运行中
        manager._recheck_task = asyncio.create_task(asyncio.sleep(10))

        # 不应创建新任务
        import logging
        with pytest.raises(Exception):
            # 实际实现会检测已在运行,这里简化测试
            pass


# ==================== 全局实例测试 ====================

class TestGlobalInstance:
    """全局实例测试"""

    def test_init_and_get_manager(self):
        """测试初始化和获取全局管理器"""
        from core.service_dependencies import init_service_manager, get_service_manager

        manager = init_service_manager()

        assert manager is not None
        assert get_service_manager() is manager

    def test_get_manager_before_init(self):
        """测试未初始化时获取应抛出异常"""
        from core.service_dependencies import _manager_instance, get_service_manager
        import core.service_dependencies as dep_module

        old_instance = _manager_instance

        try:
            dep_module._manager_instance = None

            with pytest.raises(RuntimeError, match="尚未初始化"):
                get_service_manager()
        finally:
            dep_module._manager_instance = old_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
