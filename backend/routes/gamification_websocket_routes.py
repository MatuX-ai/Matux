"""
【P3-A-2】游戏化 WebSocket 路由

提供 /ws/gamification 端点，将成就解锁 / 节点状态更新事件
实时推送给前端。
"""

from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

from config.license_config import load_sentinel_config
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from services.gamification_event_bus import (
    gamification_event_bus,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/ws/gamification", tags=["游戏化 WebSocket"])


class GamificationConnectionManager:
    """
    游戏化 WebSocket 连接管理器

    参考 `ai_edu_websocket_routes.py:LearningProgressConnectionManager` 模式。
    """

    def __init__(self):
        # {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # {user_id: [handler1, ...]} — 事件总线订阅 handler
        self._bus_handlers: Dict[int, List] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """接受连接并注册到管理器"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

        # 注册到事件总线（每用户 1 个 handler，分发给该用户所有连接）
        handler = self._make_handler(user_id)
        gamification_event_bus.subscribe(user_id, handler)
        self._bus_handlers.setdefault(user_id, []).append(handler)

        logger.info(f"✅ 用户 {user_id} 的游戏化 WebSocket 已建立")

        # 欢迎消息
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "message": "游戏化实时同步服务已连接",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """断开连接并清理订阅"""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # 清理事件总线订阅
                if user_id in self._bus_handlers:
                    for handler in self._bus_handlers[user_id]:
                        gamification_event_bus.unsubscribe(user_id, handler)
                    del self._bus_handlers[user_id]

        logger.info(f"ℹ️  用户 {user_id} 的游戏化 WebSocket 已断开")

    def _make_handler(self, user_id: int):
        """为该用户创建一个总线 handler（推送给所有连接）"""
        import asyncio

        def handler(event_type: str, data: dict):
            # 异步推送给该用户的所有 WebSocket 连接
            for ws in list(self.active_connections.get(user_id, [])):
                try:
                    message = {
                        "type": event_type,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    # 在事件循环中调度
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.send_personal_message(ws, message))
                        else:
                            loop.run_until_complete(
                                self.send_personal_message(ws, message)
                            )
                    except RuntimeError:
                        logger.warning("WebSocket handler 无法获取 event loop")
                except Exception as e:
                    logger.error(f"推送事件给 user={user_id} 失败: {e}")
                    # 连接已断，清理
                    self.disconnect(ws, user_id)

        return handler

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """向单个连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送 WebSocket 消息失败: {e}")

    async def broadcast_to_user(self, user_id: int, message: dict) -> None:
        """向用户的所有连接广播"""
        if user_id not in self.active_connections:
            return
        disconnected = []
        for ws in self.active_connections[user_id]:
            try:
                await self.send_personal_message(ws, message)
            except Exception as e:
                logger.error(f"广播失败: {e}")
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws, user_id)

    def is_user_connected(self, user_id: int) -> bool:
        return user_id in self.active_connections and bool(
            self.active_connections[user_id]
        )


# 全局连接管理器
manager = GamificationConnectionManager()


# ==================== JWT 鉴权 ====================


def _verify_token(token: str) -> Optional[int]:
    """
    验证 JWT token 并返回 user_id

    使用与 auth_routes.py 一致的密钥与算法。
    """
    try:
        config = load_sentinel_config()
        secret = (
            config.security.jwt_secret if hasattr(config, "security") else "dev-secret"
        )
        algorithm = "HS256"
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        user_id = payload.get("sub") or payload.get("user_id")
        return int(user_id) if user_id is not None else None
    except (JWTError, ValueError, TypeError) as e:
        logger.warning(f"WebSocket token 验证失败: {e}")
        return None


# ==================== WebSocket 端点 ====================


@router.websocket("")
async def gamification_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT 认证 token"),
):
    """
    游戏化实时同步 WebSocket

    连接示例（前端）：
    ```typescript
    const ws = new WebSocket(
      `ws://localhost:8000/ws/gamification?token=${encodeURIComponent(jwt)}`
    );
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'achievement_unlocked') { ... }
    };
    ```

    消息类型（服务端 → 客户端）：
    - `connected`: 连接确认
    - `achievement_unlocked`: 成就解锁
    - `node_status_updated`: 节点状态更新
    - `set_completed`: 套装完成
    - `error`: 错误
    """
    user_id = _verify_token(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # 接收客户端消息（心跳 / 业务）
            try:
                raw = await websocket.receive_text()
                # 解析客户端消息（心跳 / 订阅请求）
                try:
                    msg = json.loads(raw)
                    msg_type = msg.get("type", "ping")
                    if msg_type == "ping":
                        await websocket.send_json(
                            {
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    # 其他类型：目前不处理，预留给后续
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        }
                    )
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
    finally:
        manager.disconnect(websocket, user_id)


# ==================== 管理接口（HTTP 调试用） ====================


@router.get("/stats")
async def get_websocket_stats():
    """获取当前 WebSocket 连接统计（调试用）"""
    return {
        "success": True,
        "data": {
            "connected_users": list(manager.active_connections.keys()),
            "total_connections": sum(
                len(ws_list) for ws_list in manager.active_connections.values()
            ),
        },
    }
