"""
路由激活中间件单元测试

测试 ModuleActivationMiddleware 的路径匹配、状态拦截、自动激活
"""

from core.activation_middleware import (
    ModuleActivationMiddleware,
    WHITELIST_PATHS,
    WHITELIST_PREFIXES,
)
from core.module_spec import ModuleState, ModuleTier
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# 确保 backend 目录在 sys.path 中，支持 `from core.lazy_loader import ...` 的内部导入
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))


def _make_scope(path: str, method: str = "GET") -> dict:
    """创建模拟的 ASGI scope"""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
    }


class MockSend:
    """模拟 ASGI send"""

    def __init__(self):
        self.messages = []

    async def __call__(self, message):
        self.messages.append(message)

    @property
    def status_code(self):
        for m in self.messages:
            if m.get("type") == "http.response.start":
                return m.get("status")
        return None

    @property
    def body(self):
        for m in self.messages:
            if m.get("type") == "http.response.body":
                return m.get("body", b"").decode("utf-8", errors="replace")
        return ""


class TestWhitelist:
    """白名单路径测试"""

    def test_root_is_whitelisted(self):
        assert "/" in WHITELIST_PATHS

    def test_health_is_whitelisted(self):
        assert "/health" in WHITELIST_PATHS

    def test_system_prefix_is_whitelisted(self):
        assert any("/api/v1/system/" in p for p in WHITELIST_PREFIXES)

    def test_auth_prefix_is_whitelisted(self):
        assert any("/api/v1/auth/" in p for p in WHITELIST_PREFIXES)


class TestMiddlewareWhitelist:
    """中间件白名单逻辑测试"""

    @pytest.fixture
    def middleware(self):
        inner_app = AsyncMock()
        mw = ModuleActivationMiddleware(inner_app)
        return mw, inner_app

    @pytest.mark.asyncio
    async def test_whitelisted_path_passes_through(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/health")
        send = MockSend()
        await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_path_passes_through(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/system/modules")
        send = MockSend()
        await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_http_passes_through(self, middleware):
        mw, inner_app = middleware
        scope = {"type": "lifespan"}
        send = MockSend()
        await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()


class TestMiddlewareModuleLookup:
    """中间件模块查找和状态拦截测试"""

    @pytest.fixture
    def middleware(self):
        inner_app = AsyncMock()
        mw = ModuleActivationMiddleware(inner_app)
        return mw, inner_app

    @pytest.mark.asyncio
    async def test_unregistered_path_passes_through(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/unknown/path")

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = None

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_tier0_always_passes(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/auth/token")

        mock_spec = MagicMock()
        mock_spec.tier = ModuleTier.TIER_0_CORE
        mock_spec.state = ModuleState.ACTIVE

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = "auth"
        mock_loader.get_module.return_value = mock_spec

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_active_module_passes(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/exams")

        mock_spec = MagicMock()
        mock_spec.tier = ModuleTier.TIER_1_HIGH
        mock_spec.state = ModuleState.ACTIVE

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = "exam"
        mock_loader.get_module.return_value = mock_spec

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_loading_module_returns_503(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/blockchain")

        mock_spec = MagicMock()
        mock_spec.tier = ModuleTier.TIER_2_ON_DEMAND
        mock_spec.state = ModuleState.LOADING
        mock_spec.error_message = None

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = "blockchain"
        mock_loader.get_module.return_value = mock_spec

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        assert send.status_code == 503
        inner_app.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_module_returns_503(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/blockchain")

        mock_spec = MagicMock()
        mock_spec.tier = ModuleTier.TIER_2_ON_DEMAND
        mock_spec.state = ModuleState.FAILED
        mock_spec.error_message = "import error"

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = "blockchain"
        mock_loader.get_module.return_value = mock_spec

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        assert send.status_code == 503

    @pytest.mark.asyncio
    async def test_unloaded_triggers_auto_activate(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/ar-vr/content")

        mock_spec = MagicMock()
        mock_spec.tier = ModuleTier.TIER_2_ON_DEMAND
        mock_spec.state = ModuleState.UNLOADED
        mock_spec.error_message = None

        mock_loader = MagicMock()
        mock_loader.find_module_by_path.return_value = "ar_vr"
        mock_loader.get_module.return_value = mock_spec
        mock_loader.activate = AsyncMock(return_value=True)

        with patch(
            "core.lazy_loader.get_lazy_loader",
            return_value=mock_loader,
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)

        mock_loader.activate.assert_called_once_with("ar_vr")
        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_loader_not_initialized_passes_through(self, middleware):
        mw, inner_app = middleware
        scope = _make_scope("/api/v1/anything")

        with patch(
            "core.lazy_loader.get_lazy_loader",
            side_effect=RuntimeError("not initialized"),
            create=True,
        ):
            send = MockSend()
            await mw(scope, AsyncMock(), send)
        inner_app.assert_called_once()
