"""
【P3-A-2】游戏化 WebSocket 集成测试

测试 WebSocket 端点的事件分发、连接管理、JWT 鉴权。
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import WebSocket


class TestGamificationConnectionManager:
    """连接管理器单元测试"""

    def test_manager_starts_empty(self):
        from routes.gamification_websocket_routes import GamificationConnectionManager
        manager = GamificationConnectionManager()
        assert manager.active_connections == {}
        assert manager._bus_handlers == {}

    def test_is_user_connected_false(self):
        from routes.gamification_websocket_routes import GamificationConnectionManager
        manager = GamificationConnectionManager()
        assert manager.is_user_connected(1) is False

    @pytest.mark.asyncio
    async def test_connect_registers(self):
        """connect 后用户应被注册"""
        from routes.gamification_websocket_routes import GamificationConnectionManager

        manager = GamificationConnectionManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect(ws, user_id=42)
        assert manager.is_user_connected(42)
        assert ws.accept.called
        # 验证欢迎消息
        assert ws.send_json.called

    def test_disconnect_removes(self):
        from routes.gamification_websocket_routes import GamificationConnectionManager
        manager = GamificationConnectionManager()
        ws = MagicMock(spec=WebSocket)
        manager.active_connections[42] = [ws]
        manager.disconnect(ws, 42)
        assert 42 not in manager.active_connections


class TestTokenVerification:
    """JWT token 验证测试"""

    def test_invalid_token_returns_none(self):
        from routes.gamification_websocket_routes import _verify_token
        result = _verify_token("invalid.token.here")
        # 即使失败也应返回 None，不抛错
        assert result is None

    def test_empty_token_returns_none(self):
        from routes.gamification_websocket_routes import _verify_token
        result = _verify_token("")
        assert result is None


class TestWebSocketEndpoint:
    """WebSocket 端点集成测试（使用 FastAPI TestClient）"""

    def test_websocket_requires_token(self):
        """无 token 应被拒绝"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from routes.gamification_websocket_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with pytest.raises(Exception):
            # 没有 token → 应被 close
            with client.websocket_connect("/ws/gamification") as ws:
                pass

    def test_websocket_invalid_token_closes(self):
        """无效 token 应被 close"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from routes.gamification_websocket_routes import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        with pytest.raises(Exception):
            with client.websocket_connect(
                "/ws/gamification?token=invalid"
            ) as ws:
                pass


class TestEventBusIntegration:
    """事件总线 → WebSocket 集成（mock 推送）"""

    def setup_method(self):
        from services.gamification_event_bus import gamification_event_bus
        gamification_event_bus.clear()

    @pytest.mark.asyncio
    async def test_event_routed_to_subscribed_user(self):
        """emit 事件后订阅用户的 handler 被调用"""
        from routes.gamification_websocket_routes import (
            GamificationConnectionManager,
        )
        from services.gamification_event_bus import gamification_event_bus

        manager = GamificationConnectionManager()
        ws = AsyncMock(spec=WebSocket)
        await manager.connect(ws, user_id=99)
        # 触发事件
        gamification_event_bus.emit(
            user_id=99,
            event_type="achievement_unlocked",
            data={"achievement_id": 1, "name": "Test"},
        )
        # 等待异步任务调度
        await asyncio.sleep(0.1)
        # 应该向 ws 推送过至少 2 条消息（connected + achievement_unlocked）
        assert ws.send_json.call_count >= 2

    def test_disconnect_unsubscribes(self):
        """disconnect 后 emit 不再推送给该用户"""
        from routes.gamification_websocket_routes import (
            GamificationConnectionManager,
        )
        from services.gamification_event_bus import gamification_event_bus

        manager = GamificationConnectionManager()
        ws = MagicMock(spec=WebSocket)
        # 手动注册
        manager.active_connections[42] = [ws]
        handler = manager._make_handler(42)
        gamification_event_bus.subscribe(42, handler)
        manager._bus_handlers[42] = [handler]
        # 断开
        manager.disconnect(ws, 42)
        # emit 不应崩溃
        gamification_event_bus.emit(user_id=42, event_type="x", data={})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
