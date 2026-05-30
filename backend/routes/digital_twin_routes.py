"""
数字孪生实验室后端API服务
提供物理状态同步和多人协作接口
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.tenant_aware_session import TenantAwareSession
from utils.database import get_sync_db
from models.user import User
from utils.redis_client import redis_client
from utils.dependencies import get_current_user_sync

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/digital-twin", tags=["数字孪生实验室"])


class CircuitElementState(BaseModel):
    """电路元件状态模型"""

    element_id: str
    element_type: str
    voltage: float
    current: float
    power: float
    node1: str
    node2: str
    parameter_value: float
    timestamp: datetime


class CircuitState(BaseModel):
    """完整电路状态模型"""

    session_id: str
    elements: List[CircuitElementState]
    total_power: float
    total_current: float
    simulation_time: float
    timestamp: datetime


class DeviceState(BaseModel):
    """设备状态模型"""

    device_id: str
    device_type: str
    voltage: float
    current: float
    temperature: float
    is_connected: bool
    custom_properties: Optional[Dict[str, Any]] = None
    timestamp: datetime


class SessionInfo(BaseModel):
    """会话信息模型"""

    session_id: str
    host_user_id: int
    participant_count: int
    created_at: datetime
    is_active: bool


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.session_states: Dict[str, CircuitState] = {}
        self.device_states: Dict[str, DeviceState] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"用户 {user_id} 连接到会话 {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"用户断开连接，会话: {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {e}")


manager = ConnectionManager()


@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, session_id: str, user_id: str, db: Session = Depends(get_sync_db)
):
    """WebSocket会话连接端点"""
    await manager.connect(websocket, session_id, user_id)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "circuit_state_update":
                # 处理电路状态更新
                await handle_circuit_state_update(session_id, data, websocket)

            elif message_type == "device_state_update":
                # 处理设备状态更新
                await handle_device_state_update(session_id, data, websocket)

            elif message_type == "sync_request":
                # 处理同步请求
                await handle_sync_request(session_id, websocket)

            elif message_type == "ping":
                # 心跳检测
                await websocket.send_json(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
        manager.disconnect(websocket, session_id)


async def handle_circuit_state_update(
    session_id: str, data: Dict, websocket: WebSocket
):
    """处理电路状态更新"""
    try:
        # 验证数据格式
        circuit_state = CircuitState(**data.get("state", {}))

        # 更新会话状态
        manager.session_states[session_id] = circuit_state

        # 广播给其他客户端
        broadcast_data = {
            "type": "circuit_state_broadcast",
            "session_id": session_id,
            "state": circuit_state.dict(),
            "sender": data.get("sender", "unknown"),
        }

        await manager.broadcast_to_session(session_id, broadcast_data)

        # 缓存到Redis
        cache_key = f"digital_twin:circuit:{session_id}"
        await redis_client.setex(
            cache_key, 3600, json.dumps(circuit_state.dict(), default=str)  # 1小时过期
        )

        logger.info(f"电路状态已更新并广播，会话: {session_id}")

    except Exception as e:
        logger.error(f"处理电路状态更新失败: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"电路状态更新失败: {str(e)}"}
        )


async def handle_device_state_update(session_id: str, data: Dict, websocket: WebSocket):
    """处理设备状态更新"""
    try:
        device_state = DeviceState(**data.get("state", {}))

        # 更新设备状态
        device_key = f"{session_id}:{device_state.device_id}"
        manager.device_states[device_key] = device_state

        # 广播设备状态
        broadcast_data = {
            "type": "device_state_broadcast",
            "session_id": session_id,
            "device_id": device_state.device_id,
            "state": device_state.dict(),
        }

        await manager.broadcast_to_session(session_id, broadcast_data)

        # 缓存设备状态
        device_cache_key = f"digital_twin:device:{device_key}"
        await redis_client.setex(
            device_cache_key,
            1800,  # 30分钟过期
            json.dumps(device_state.dict(), default=str),
        )

        logger.info(f"设备状态已更新: {device_state.device_id}")

    except Exception as e:
        logger.error(f"处理设备状态更新失败: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"设备状态更新失败: {str(e)}"}
        )


async def handle_sync_request(session_id: str, websocket: WebSocket):
    """处理同步请求"""
    try:
        # 获取当前会话状态
        circuit_state = manager.session_states.get(session_id)
        device_states = {
            k: v
            for k, v in manager.device_states.items()
            if k.startswith(f"{session_id}:")
        }

        response = {
            "type": "sync_response",
            "session_id": session_id,
            "circuit_state": circuit_state.dict() if circuit_state else None,
            "device_states": [state.dict() for state in device_states.values()],
            "timestamp": datetime.utcnow().isoformat(),
        }

        await websocket.send_json(response)

    except Exception as e:
        logger.error(f"处理同步请求失败: {e}")
        await websocket.send_json(
            {"type": "error", "message": f"同步请求失败: {str(e)}"}
        )


@router.post("/sessions", response_model=SessionInfo)
async def create_session(
    current_user: User = Depends(get_current_user_sync), db: Session = Depends(get_sync_db)
):
    """创建新的数字孪生会话"""
    try:
        import uuid

        session_id = str(uuid.uuid4())

        session_info = SessionInfo(
            session_id=session_id,
            host_user_id=current_user.id,
            participant_count=1,
            created_at=datetime.utcnow(),
            is_active=True,
        )

        # 缓存会话信息
        cache_key = f"digital_twin:session:{session_id}"
        await redis_client.setex(
            cache_key, 86400, json.dumps(session_info.dict(), default=str)  # 24小时过期
        )

        logger.info(f"创建数字孪生会话: {session_id}")
        return session_info

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """获取会话信息"""
    try:
        cache_key = f"digital_twin:session:{session_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            session_data = json.loads(cached_data)
            return SessionInfo(**session_data)
        else:
            raise HTTPException(status_code=404, detail="会话不存在")

    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取会话信息失败")


@router.post("/sessions/{session_id}/states")
async def update_circuit_state(
    session_id: str,
    state: CircuitState,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """更新电路状态（HTTP接口）"""
    try:
        # 更新内存状态
        manager.session_states[session_id] = state

        # 缓存到Redis
        cache_key = f"digital_twin:circuit:{session_id}"
        await redis_client.setex(cache_key, 3600, json.dumps(state.dict(), default=str))

        # 广播给WebSocket客户端
        broadcast_data = {
            "type": "circuit_state_broadcast",
            "session_id": session_id,
            "state": state.dict(),
        }
        await manager.broadcast_to_session(session_id, broadcast_data)

        return {"success": True, "message": "电路状态已更新"}

    except Exception as e:
        logger.error(f"更新电路状态失败: {e}")
        raise HTTPException(status_code=500, detail="更新电路状态失败")


@router.get("/sessions/{session_id}/states", response_model=CircuitState)
async def get_circuit_state(
    session_id: str,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """获取电路状态"""
    try:
        # 先从内存查找
        if session_id in manager.session_states:
            return manager.session_states[session_id]

        # 从Redis查找
        cache_key = f"digital_twin:circuit:{session_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            state_data = json.loads(cached_data)
            return CircuitState(**state_data)
        else:
            raise HTTPException(status_code=404, detail="电路状态不存在")

    except Exception as e:
        logger.error(f"获取电路状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取电路状态失败")


@router.post("/devices/states")
async def update_device_state(
    state: DeviceState,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """更新设备状态"""
    try:
        # 更新内存状态
        manager.device_states[state.device_id] = state

        # 缓存到Redis
        cache_key = f"digital_twin:device:{state.device_id}"
        await redis_client.setex(cache_key, 1800, json.dumps(state.dict(), default=str))

        return {"success": True, "message": "设备状态已更新"}

    except Exception as e:
        logger.error(f"更新设备状态失败: {e}")
        raise HTTPException(status_code=500, detail="更新设备状态失败")


@router.get("/devices/{device_id}/states", response_model=DeviceState)
async def get_device_state(
    device_id: str,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """获取设备状态"""
    try:
        # 先从内存查找
        if device_id in manager.device_states:
            return manager.device_states[device_id]

        # 从Redis查找
        cache_key = f"digital_twin:device:{device_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            state_data = json.loads(cached_data)
            return DeviceState(**state_data)
        else:
            raise HTTPException(status_code=404, detail="设备状态不存在")

    except Exception as e:
        logger.error(f"获取设备状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取设备状态失败")


@router.get("/sessions/{session_id}/participants")
async def get_session_participants(
    session_id: str,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """获取会话参与者列表"""
    try:
        participants = []
        if session_id in manager.active_connections:
            # 这里应该从用户服务获取详细信息
            participants = [
                {"user_id": f"user_{i}", "joined_at": datetime.utcnow().isoformat()}
                for i in range(len(manager.active_connections[session_id]))
            ]

        return {
            "session_id": session_id,
            "participant_count": len(participants),
            "participants": participants,
        }

    except Exception as e:
        logger.error(f"获取参与者列表失败：{e}")
        raise HTTPException(status_code=500, detail="获取参与者列表失败")

# 更新时间：2026-03-25
