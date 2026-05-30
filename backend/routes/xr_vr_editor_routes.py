"""
VR代码编辑器服务
提供完整的VR代码编辑功能API
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .models import CodeLanguage, VREditorConfig
from .vr_editor_core import VREditorCore
from .vr_input_handler import VRInputHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/xr/vr-editor", tags=["VR代码编辑器"])

# 全局编辑器实例管理
editor_instances: Dict[str, VREditorCore] = {}
input_handlers: Dict[str, VRInputHandler] = {}


class EditorStartRequest(BaseModel):
    """启动编辑器请求"""

    user_id: Optional[int] = None
    device_id: str = "default_vr_device"
    config: Optional[VREditorConfig] = None


class FileOperationRequest(BaseModel):
    """文件操作请求"""

    file_path: str
    content: Optional[str] = ""
    language: CodeLanguage = CodeLanguage.PYTHON


class CodeUpdateRequest(BaseModel):
    """代码更新请求"""

    file_id: str
    content: str
    cursor_line: int = 0
    cursor_column: int = 0


class WebSocketConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"VR编辑器WebSocket连接建立: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"VR编辑器WebSocket连接断开: {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict):
        """向会话广播消息"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"WebSocket消息发送失败: {e}")


# 全局连接管理器
connection_manager = WebSocketConnectionManager()


@router.post("/sessions/start")
async def start_editor_session(request: EditorStartRequest) -> Dict:
    """
    启动VR代码编辑器会话
    """
    try:
        # 创建编辑器核心实例
        editor = VREditorCore(request.config)

        # 初始化会话
        session_id = editor.initialize_session(request.user_id, request.device_id)

        # 创建输入处理器
        input_handler = VRInputHandler(editor.config.interaction_mode)

        # 存储实例
        editor_instances[session_id] = editor
        input_handlers[session_id] = input_handler

        # 设置回调函数
        def state_change_callback(state):
            import asyncio

            asyncio.create_task(
                connection_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "state_update",
                        "state": state.dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        def file_change_callback(file_obj):
            import asyncio

            asyncio.create_task(
                connection_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "file_update",
                        "file": file_obj.dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        editor.set_state_change_callback(state_change_callback)
        editor.set_file_change_callback(file_change_callback)

        return {
            "session_id": session_id,
            "message": "VR代码编辑器会话已启动",
            "supported_languages": editor.get_supported_languages(),
        }

    except Exception as e:
        logger.error(f"启动编辑器会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/files/open")
async def open_file(session_id: str, request: FileOperationRequest) -> Dict:
    """
    在编辑器中打开文件
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        file_id = editor.open_file(request.file_path, request.content, request.language)

        return {"file_id": file_id, "message": f"文件已打开: {request.file_path}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"打开文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/files/update")
async def update_file_content(session_id: str, request: CodeUpdateRequest) -> Dict:
    """
    更新文件内容
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        success = editor.update_file_content(
            request.file_id, request.content, request.cursor_line, request.cursor_column
        )

        if success:
            return {"message": "文件内容已更新"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/files")
async def list_opened_files(session_id: str) -> List[Dict]:
    """
    列出已打开的文件
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        session_info = editor.get_session_info()

        if not session_info:
            return []

        return [
            {
                "id": file_obj.id,
                "name": file_obj.name,
                "path": file_obj.path,
                "language": file_obj.language.value,
                "size": file_obj.size,
                "modified_at": file_obj.modified_at.isoformat(),
                "is_active": file_obj.id == session_info.active_file_id,
            }
            for file_obj in session_info.opened_files
        ]

    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/cursor/move")
async def move_cursor(session_id: str, position: Dict[str, int]) -> Dict:
    """
    移动光标位置
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        editor.set_cursor_position(position.get("line", 0), position.get("column", 0))

        return {"message": "光标位置已更新"}

    except Exception as e:
        logger.error(f"移动光标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/vr-state/update")
async def update_vr_state(session_id: str, state_data: Dict) -> Dict:
    """
    更新VR状态
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        editor.update_vr_state(
            head_position=state_data.get("head_position", {"x": 0, "y": 0, "z": 0}),
            head_rotation=state_data.get("head_rotation", {"x": 0, "y": 0, "z": 0}),
            left_controller=state_data.get("left_controller"),
            right_controller=state_data.get("right_controller"),
        )

        return {"message": "VR状态已更新"}

    except Exception as e:
        logger.error(f"更新VR状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str) -> Dict:
    """
    获取会话信息
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        editor = editor_instances[session_id]
        session_info = editor.get_session_info()

        if not session_info:
            raise HTTPException(status_code=404, detail="会话信息不可用")

        return {
            "session_id": session_info.session_id,
            "user_id": session_info.user_id,
            "device_id": session_info.device_id,
            "is_active": session_info.is_active,
            "created_at": session_info.created_at.isoformat(),
            "last_activity": session_info.last_activity.isoformat(),
            "config": session_info.config.dict(),
            "state": session_info.state.dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop")
async def stop_editor_session(session_id: str) -> Dict:
    """
    停止编辑器会话
    """
    try:
        if session_id not in editor_instances:
            raise HTTPException(status_code=404, detail="编辑器会话不存在")

        # 关闭编辑器
        editor = editor_instances[session_id]
        editor.close_session()

        # 清理输入处理器
        if session_id in input_handlers:
            del input_handlers[session_id]

        # 清理连接
        connection_manager.disconnect(session_id)

        # 移除实例
        del editor_instances[session_id]

        return {"session_id": session_id, "message": "VR代码编辑器会话已停止"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止编辑器会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def editor_websocket(websocket: WebSocket, session_id: str):
    """
    VR编辑器WebSocket连接
    """
    try:
        if session_id not in editor_instances:
            await websocket.close(code=4004, reason="编辑器会话不存在")
            return

        # 建立连接
        await connection_manager.connect(session_id, websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "input_event":
                    # 处理输入事件
                    await handle_input_event(session_id, data.get("event", {}))
                elif message_type == "get_state":
                    # 返回当前状态
                    editor = editor_instances[session_id]
                    session_info = editor.get_session_info()
                    if session_info:
                        await websocket.send_json(
                            {
                                "type": "state_response",
                                "state": session_info.state.dict(),
                            }
                        )

        except WebSocketDisconnect:
            logger.info(f"VR编辑器WebSocket连接断开: {session_id}")
        finally:
            connection_manager.disconnect(session_id)

    except Exception as e:
        logger.error(f"WebSocket连接处理失败: {e}")
        await websocket.close(code=1011, reason="服务器内部错误")


async def handle_input_event(session_id: str, event_data: Dict):
    """处理输入事件"""
    if session_id not in input_handlers:
        return

    input_handler = input_handlers[session_id]
    event_type = event_data.get("event_type")

    if event_type == "controller_button":
        input_handler.process_controller_input(
            event_data.get("controller_id", ""),
            event_data.get("button"),
            event_data.get("pressed", False),
            event_data.get("axis_values"),
        )
    elif event_type == "hand_gesture":
        input_handler.process_hand_gesture(
            event_data.get("hand_id", ""),
            event_data.get("gesture_type", ""),
            event_data.get("position", (0, 0, 0)),
            event_data.get("confidence", 0.0),
        )


@router.get("/health")
async def health_check() -> Dict:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "vr_3d_code_editor",
        "active_sessions": len(editor_instances),
        "timestamp": datetime.utcnow().isoformat(),
    }
