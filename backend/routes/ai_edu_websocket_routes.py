"""
AI-Edu-for-Kids 学习进度实时同步 WebSocket 服务
支持多客户端实时学习进度同步
"""

from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync
from services.ai_edu_progress_service import AIEduProgressService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/ws/ai-edu", tags=["AI 教育 WebSocket"])


class LearningProgressConnectionManager:
    """学习进度 WebSocket 连接管理器"""

    def __init__(self):
        # 存储所有活跃的连接 {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # 存储用户当前的学习状态 {user_id: {"lesson_id": int, "progress": float, "last_update": datetime}}
        self.user_learning_states: Dict[int, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """接受 WebSocket 连接并注册到管理器"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        logger.info(f"✅ 用户 {user_id} 的学习进度 WebSocket 连接已建立")

        # 发送欢迎消息
        await self.send_personal_message(
            websocket,
            {
                "type": "connected",
                "message": "学习进度同步服务已连接",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开 WebSocket 连接并从管理器移除"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

            # 如果没有更多连接，清理用户状态
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_learning_states:
                    del self.user_learning_states[user_id]

        logger.info(f"ℹ️  用户 {user_id} 的 WebSocket 连接已断开")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """向特定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败：{e}")

    async def broadcast_to_user(self, user_id: int, message: dict):
        """向特定用户的所有连接广播消息"""
        if user_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await self.send_personal_message(websocket, message)
            except Exception as e:
                logger.error(f"广播消息失败：{e}")
                disconnected.append(websocket)

        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws, user_id)

    async def update_learning_state(
        self, user_id: int, lesson_id: int, progress_data: dict
    ):
        """更新用户学习状态并广播给所有连接"""
        # 更新状态
        self.user_learning_states[user_id] = {
            "lesson_id": lesson_id,
            "progress": progress_data.get("progress_percentage", 0),
            "status": progress_data.get("status", "in_progress"),
            "time_spent_seconds": progress_data.get("time_spent_seconds", 0),
            "last_update": datetime.utcnow(),
        }

        # 广播给该用户的所有连接
        message = {
            "type": "progress_update",
            "data": {
                "lesson_id": lesson_id,
                **progress_data,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        await self.broadcast_to_user(user_id, message)

    def get_user_state(self, user_id: int) -> Optional[dict]:
        """获取用户当前学习状态"""
        state = self.user_learning_states.get(user_id)
        if state:
            return {
                **state,
                "last_update": (
                    state["last_update"].isoformat()
                    if state.get("last_update")
                    else None
                ),
            }
        return None


# 全局连接管理器实例
manager = LearningProgressConnectionManager()


@router.websocket("/progress/{user_id}")
async def learning_progress_websocket(
    websocket: WebSocket,
    user_id: int,
    org_id: int = Query(..., description="组织 ID"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    学习进度实时同步 WebSocket 端点

    功能:
    - 实时更新学习进度
    - 多设备同步
    - 即时消息推送
    - 心跳检测
    """
    # 验证用户权限（只能订阅自己的进度）
    if current_user.id != user_id:  # type: ignore[comparison-overlap]
        await websocket.send_json(
            {
                "type": "error",
                "error": "无权限访问其他用户的学习进度",
                "code": "PERMISSION_DENIED",
            }
        )
        await websocket.close()
        return

    # 建立连接
    await manager.connect(websocket, user_id)

    try:
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理不同类型的消息
                await handle_client_message(
                    websocket=websocket,
                    user_id=user_id,
                    org_id=org_id,
                    message=message,
                    db=db,
                )

            except WebSocketDisconnect:
                logger.info(f"用户 {user_id} 主动断开 WebSocket 连接")
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": "无效的消息格式",
                        "code": "INVALID_FORMAT",
                    }
                )
            except Exception as e:
                logger.error(f"处理 WebSocket 消息失败：{e}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": str(e),
                        "code": "MESSAGE_PROCESSING_ERROR",
                    }
                )

    finally:
        # 清理连接
        manager.disconnect(websocket, user_id)


async def handle_client_message(
    websocket: WebSocket, user_id: int, org_id: int, message: dict, db: Session
):
    """处理客户端发送的 WebSocket 消息"""
    msg_type = message.get("type")
    data = message.get("data", {})

    if msg_type == "ping":
        # 心跳检测
        await websocket.send_json(
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        )

    elif msg_type == "update_progress":
        # 更新学习进度
        lesson_id = data.get("lesson_id")
        progress_data = data.get("progress", {})

        if not lesson_id:
            await websocket.send_json(
                {
                    "type": "error",
                    "error": "缺少 lesson_id 参数",
                    "code": "MISSING_LESSON_ID",
                }
            )
            return

        try:
            service = AIEduProgressService(db)
            progress = await service.report_progress(user_id, lesson_id, progress_data)

            # 通过 WebSocket 确认更新
            await websocket.send_json(
                {
                    "type": "progress_confirmed",
                    "data": {
                        "progress_id": progress.id,
                        "lesson_id": progress.lesson_id,
                        "progress_percentage": progress.progress_percentage,
                        "status": progress.status,
                        "time_spent_seconds": progress.time_spent_seconds,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            )

            # 广播给该用户的其他连接
            await manager.update_learning_state(
                user_id,
                lesson_id,
                {
                    "progress_percentage": progress.progress_percentage,
                    "status": progress.status,
                    "time_spent_seconds": progress.time_spent_seconds,
                },
            )

        except Exception as e:
            logger.error(f"WebSocket 更新进度失败：{e}")
            await websocket.send_json(
                {
                    "type": "error",
                    "error": f"更新进度失败：{str(e)}",
                    "code": "PROGRESS_UPDATE_FAILED",
                }
            )

    elif msg_type == "get_state":
        # 获取当前学习状态
        state = manager.get_user_state(user_id)
        await websocket.send_json(
            {"type": "current_state", "data": state or {"message": "暂无活跃学习状态"}}
        )

    elif msg_type == "subscribe_lesson":
        # 订阅特定课程的进度更新
        lesson_id = data.get("lesson_id")
        if lesson_id:
            await websocket.send_json(
                {
                    "type": "subscribed",
                    "data": {"lesson_id": lesson_id},
                    "message": f"已订阅课程 {lesson_id} 的进度更新",
                }
            )

    elif msg_type == "unsubscribe_lesson":
        # 取消订阅
        lesson_id = data.get("lesson_id")
        if lesson_id:
            await websocket.send_json(
                {
                    "type": "unsubscribed",
                    "data": {"lesson_id": lesson_id},
                    "message": f"已取消订阅课程 {lesson_id}",
                }
            )

    else:
        await websocket.send_json(
            {
                "type": "error",
                "error": f"未知的消息类型：{msg_type}",
                "code": "UNKNOWN_MESSAGE_TYPE",
            }
        )


# 工具函数：从外部触发进度更新广播
async def broadcast_progress_update(user_id: int, lesson_id: int, progress_data: dict):
    """
    从外部触发学习进度更新广播

    使用场景:
    - HTTP API 更新后通知 WebSocket 客户端
    - 定时任务触发进度同步
    - 教师端监控学生学习进度
    """
    await manager.update_learning_state(user_id, lesson_id, progress_data)


def get_connection_manager() -> LearningProgressConnectionManager:
    """获取连接管理器单例"""
    return manager
