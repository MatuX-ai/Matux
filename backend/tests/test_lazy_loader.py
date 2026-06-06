"""
模块懒加载引擎单元测试

测试 ModuleLazyLoader 的注册、激活、状态管理、并发安全
"""

from core.module_spec import ModuleSpec, ModuleState, ModuleTier
from core.lazy_loader import ModuleLazyLoader, ModuleActivationError
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, APIRouter

# 确保 backend 目录在 sys.path 中
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))


# ==================== Fixtures ====================

@pytest.fixture
def app():
    """创建 FastAPI 应用实例"""
    return FastAPI()


@pytest.fixture
def loader(app):
    """创建懒加载引擎实例"""
    return ModuleLazyLoader(app)


@pytest.fixture
def mock_router():
    """创建模拟路由"""
    router = APIRouter()

    @router.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return router


@pytest.fixture
def tier0_spec(mock_router):
    """Tier 0 模块规格"""
    return ModuleSpec(
        name="auth",
        tier=ModuleTier.TIER_0_CORE,
        router_factory=lambda: mock_router,
        prefix="/api/v1/auth",
        tags=["认证"],
    )


@pytest.fixture
def tier1_spec(mock_router):
    """Tier 1 模块规格"""
    return ModuleSpec(
        name="ai_service",
        tier=ModuleTier.TIER_1_HIGH,
        router_factory=lambda: mock_router,
        prefix="/api/v1/ai",
        tags=["AI"],
        required_services=["openai"],
        fallback_services={"openai": "local_template"},
    )


@pytest.fixture
def tier2_spec(mock_router):
    """Tier 2 模块规格"""
    return ModuleSpec(
        name="blockchain",
        tier=ModuleTier.TIER_2_ON_DEMAND,
        router_factory=lambda: mock_router,
        prefix="/api/v1/blockchain",
        tags=["区块链"],
        required_services=["hyperledger"],
        fallback_services={"hyperledger": "cache_mode"},
        dependencies=["auth"],
    )


# ==================== 注册测试 ====================

class TestModuleRegistration:
    """模块注册测试"""

    def test_register_single_module(self, loader, tier0_spec):
        """测试注册单个模块"""
        loader.register(tier0_spec)

        assert "auth" in loader.modules
        assert loader.modules["auth"] == tier0_spec
        assert loader.modules["auth"].state == ModuleState.UNLOADED

    def test_register_duplicate_module(self, loader, tier0_spec):
        """测试重复注册应抛出异常"""
        loader.register(tier0_spec)

        with pytest.raises(ValueError, match="已注册"):
            loader.register(tier0_spec)

    def test_register_many_modules(self, loader, tier0_spec, tier1_spec, tier2_spec):
        """测试批量注册模块"""
        loader.register_many([tier0_spec, tier1_spec, tier2_spec])

        assert len(loader.modules) == 3
        assert "auth" in loader.modules
        assert "ai_service" in loader.modules
        assert "blockchain" in loader.modules

    def test_register_establishes_prefix_mapping(self, loader, tier0_spec):
        """测试注册时建立 prefix → module 映射"""
        loader.register(tier0_spec)

        module_name = loader.find_module_by_path("/api/v1/auth/login")
        assert module_name == "auth"


# ==================== 激活测试 ====================

class TestModuleActivation:
    """模块激活测试"""

    @pytest.mark.asyncio
    async def test_activate_tier0_module(self, loader, tier0_spec, app):
        """测试激活 Tier 0 模块"""
        loader.register(tier0_spec)

        success = await loader.activate("auth")

        assert success is True
        assert tier0_spec.state == ModuleState.ACTIVE
        assert tier0_spec.load_time_ms > 0
        assert tier0_spec.activation_count == 1

    @pytest.mark.asyncio
    async def test_activate_already_active_module(self, loader, tier0_spec):
        """测试激活已激活的模块应跳过"""
        loader.register(tier0_spec)
        tier0_spec.state = ModuleState.ACTIVE

        success = await loader.activate("auth")

        assert success is True
        assert tier0_spec.activation_count == 0  # 未增加

    @pytest.mark.asyncio
    async def test_activate_nonexistent_module(self, loader):
        """测试激活未注册模块应抛出异常"""
        with pytest.raises(ModuleActivationError, match="未注册"):
            await loader.activate("nonexistent")

    @pytest.mark.asyncio
    async def test_activate_with_failed_factory(self, loader, app):
        """测试路由工厂失败时应标记为 FAILED"""
        failing_spec = ModuleSpec(
            name="failing_module",
            tier=ModuleTier.TIER_1_HIGH,
            router_factory=lambda: (_ for _ in ()).throw(
                Exception("Factory error")),
            prefix="/api/v1/failing",
        )
        loader.register(failing_spec)

        with pytest.raises(ModuleActivationError):
            await loader.activate("failing_module")

        assert failing_spec.state == ModuleState.FAILED
        assert "Factory error" in failing_spec.error_message

    @pytest.mark.asyncio
    async def test_activate_triggers_dependency_activation(self, loader, tier0_spec, tier2_spec, app):
        """测试激活模块应递归激活依赖"""
        loader.register(tier0_spec)
        loader.register(tier2_spec)

        await loader.activate("blockchain")

        # blockchain 依赖 auth,应自动激活
        assert tier0_spec.state == ModuleState.ACTIVE
        assert tier2_spec.state in (ModuleState.ACTIVE, ModuleState.DEGRADED)


# ==================== 批量激活测试 ====================

class TestTierActivation:
    """层级批量激活测试"""

    @pytest.mark.asyncio
    async def test_activate_tier0(self, loader, tier0_spec, app):
        """测试批量激活 Tier 0"""
        loader.register(tier0_spec)

        results = await loader.activate_tier(ModuleTier.TIER_0_CORE)

        assert "auth" in results
        assert results["auth"] is True

    @pytest.mark.asyncio
    async def test_activate_empty_tier(self, loader):
        """测试激活空层级应返回空结果"""
        results = await loader.activate_tier(ModuleTier.TIER_3_DELAYED)

        assert results == {}


# ==================== 状态查询测试 ====================

class TestStatusQuery:
    """状态查询测试"""

    def test_get_status_empty(self, loader):
        """测试空注册表状态"""
        status = loader.get_status()

        assert status["summary"]["total"] == 0
        assert status["summary"]["active"] == 0

    def test_get_status_with_modules(self, loader, tier0_spec, tier1_spec):
        """测试有模块时的状态"""
        loader.register(tier0_spec)
        loader.register(tier1_spec)
        tier0_spec.state = ModuleState.ACTIVE
        tier1_spec.state = ModuleState.DEGRADED

        status = loader.get_status()

        assert status["summary"]["total"] == 2
        assert status["summary"]["active"] == 1
        assert status["summary"]["degraded"] == 1
        assert len(status["modules"]) == 2

    def test_get_module(self, loader, tier0_spec):
        """测试获取单个模块"""
        loader.register(tier0_spec)

        spec = loader.get_module("auth")

        assert spec == tier0_spec
        assert loader.get_module("nonexistent") is None

    def test_is_module_active(self, loader, tier0_spec):
        """测试模块激活状态检查"""
        loader.register(tier0_spec)

        assert loader.is_module_active("auth") is False

        tier0_spec.state = ModuleState.ACTIVE
        assert loader.is_module_active("auth") is True

        tier0_spec.state = ModuleState.DEGRADED
        assert loader.is_module_active("auth") is True

        tier0_spec.state = ModuleState.FAILED
        assert loader.is_module_active("auth") is False


# ==================== 路径匹配测试 ====================

class TestPathMatching:
    """路径匹配测试"""

    def test_find_module_by_exact_prefix(self, loader, tier0_spec):
        """测试精确前缀匹配"""
        loader.register(tier0_spec)

        assert loader.find_module_by_path("/api/v1/auth/login") == "auth"
        assert loader.find_module_by_path(
            "/api/v1/auth/token/refresh") == "auth"

    def test_find_module_no_match(self, loader, tier0_spec):
        """测试无匹配路径"""
        loader.register(tier0_spec)

        assert loader.find_module_by_path("/api/v1/unknown") is None
        assert loader.find_module_by_path("/health") is None


# ==================== 去激活测试 ====================

class TestDeactivation:
    """去激活测试"""

    @pytest.mark.asyncio
    async def test_deactivate_non_core_module(self, loader, tier1_spec):
        """测试去激活非核心模块"""
        loader.register(tier1_spec)
        tier1_spec.state = ModuleState.ACTIVE

        success = await loader.deactivate("ai_service")

        assert success is True
        assert tier1_spec.state == ModuleState.UNLOADED

    @pytest.mark.asyncio
    async def test_deactivate_core_module_not_allowed(self, loader, tier0_spec):
        """测试不允许去激活核心模块"""
        loader.register(tier0_spec)
        tier0_spec.state = ModuleState.ACTIVE

        success = await loader.deactivate("auth")

        assert success is False
        assert tier0_spec.state == ModuleState.ACTIVE  # 状态不变


# ==================== 并发安全测试 ====================

class TestConcurrency:
    """并发安全测试"""

    @pytest.mark.asyncio
    async def test_concurrent_activation_same_module(self, loader, tier0_spec, app):
        """测试并发激活同一模块不应重复加载"""
        loader.register(tier0_spec)

        # 同时发起 10 个激活请求
        tasks = [loader.activate("auth") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 所有任务应成功
        assert all(results)
        # activation_count 应为 1 (只激活一次)
        assert tier0_spec.activation_count == 1


# ==================== 序列化测试 ====================

class TestSerialization:
    """序列化测试"""

    def test_module_spec_to_dict(self, tier0_spec):
        """测试 ModuleSpec 序列化为字典"""
        tier0_spec.state = ModuleState.ACTIVE
        tier0_spec.load_time_ms = 123.45

        data = tier0_spec.to_dict()

        assert data["name"] == "auth"
        assert data["tier"] == 0
        assert data["state"] == "active"
        assert data["load_time_ms"] == 123.45
        assert "router_factory" not in data  # 不应序列化函数

    def test_module_spec_validate_dependencies(self):
        """测试依赖关系验证"""
        modules = {
            "auth": ModuleSpec(name="auth", tier=ModuleTier.TIER_0_CORE, router_factory=lambda: None),
            "course": ModuleSpec(
                name="course",
                tier=ModuleTier.TIER_0_CORE,
                router_factory=lambda: None,
                dependencies=["auth"],
            ),
        }

        issues = ModuleSpec.validate_dependencies(modules)

        assert issues == []  # 无问题

    def test_module_spec_validate_circular_dependency(self):
        """测试循环依赖检测"""
        modules = {
            "a": ModuleSpec(
                name="a",
                tier=ModuleTier.TIER_0_CORE,
                router_factory=lambda: None,
                dependencies=["b"],
            ),
            "b": ModuleSpec(
                name="b",
                tier=ModuleTier.TIER_0_CORE,
                router_factory=lambda: None,
                dependencies=["a"],
            ),
        }

        issues = ModuleSpec.validate_dependencies(modules)

        assert len(issues) > 0
        assert any("循环依赖" in issue for issue in issues)


# ==================== 全局实例测试 ====================

class TestGlobalInstance:
    """全局实例测试"""

    def test_init_and_get_lazy_loader(self, app):
        """测试初始化和获取全局实例"""
        from core.lazy_loader import init_lazy_loader, get_lazy_loader

        loader = init_lazy_loader(app)

        assert loader is not None
        assert get_lazy_loader() is loader

    def test_get_lazy_loader_before_init(self):
        """测试未初始化时获取应抛出异常"""
        from core.lazy_loader import _loader_instance, get_lazy_loader

        # 保存旧实例
        old_instance = _loader_instance

        try:
            # 临时设为 None
            import core.lazy_loader as lazy_loader_module
            lazy_loader_module._loader_instance = None

            with pytest.raises(RuntimeError, match="尚未初始化"):
                get_lazy_loader()
        finally:
            # 恢复旧实例
            lazy_loader_module._loader_instance = old_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
