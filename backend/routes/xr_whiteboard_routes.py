"""
白板协作服务
提供完整的白板协作功能API
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .models import StrokeType, WhiteboardColor, WhiteboardConfig, WhiteboardElement
from .whiteboard_core import WhiteboardCore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/xr/whiteboard", tags=["白板协作"])

# 全局白板实例管理
whiteboard_instances: Dict[str, WhiteboardCore] = {}


class WhiteboardCreateRequest(BaseModel):
    """创建白板请求"""

    owner_id: int
    board_name: str = "协作白板"
    config: Optional[WhiteboardConfig] = None


class JoinWhiteboardRequest(BaseModel):
    """加入白板请求"""

    user_id: int


class StrokeStartRequest(BaseModel):
    """开始绘制笔画请求"""

    x: float
    y: float
    pressure: float = 1.0
    stroke_type: Optional[StrokeType] = None
    color: Optional[WhiteboardColor] = None
    width: Optional[float] = None
    user_id: int


class StrokePointRequest(BaseModel):
    """添加笔画点请求"""

    x: float
    y: float
    pressure: float = 1.0


class ElementModifyRequest(BaseModel):
    """修改元素请求"""

    element_id: str
    updates: Dict


class WebSocketConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"白板WebSocket连接建立: {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"白板WebSocket连接断开: {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict):
        """向会话广播消息"""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id][
                :
            ]:  # 创建副本以防修改
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"WebSocket消息发送失败: {e}")
                    # 从连接列表中移除失效的连接
                    if connection in self.active_connections[session_id]:
                        self.active_connections[session_id].remove(connection)


# 全局连接管理器
connection_manager = WebSocketConnectionManager()


@router.post("/create")
async def create_whiteboard(request: WhiteboardCreateRequest) -> Dict:
    """
    创建新的白板会话
    """
    try:
        # 创建白板核心实例
        whiteboard = WhiteboardCore(request.config)

        # 创建会话
        session_id = whiteboard.create_session(request.owner_id, request.board_name)

        # 存储实例
        whiteboard_instances[session_id] = whiteboard

        # 设置回调函数
        def element_added_callback(element: WhiteboardElement):
            import asyncio

            asyncio.create_task(
                connection_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "element_added",
                        "element": element.dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        def element_modified_callback(element: WhiteboardElement):
            import asyncio

            asyncio.create_task(
                connection_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "element_modified",
                        "element": element.dict(),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        def element_removed_callback(element_id: str):
            import asyncio

            asyncio.create_task(
                connection_manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "element_removed",
                        "element_id": element_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            )

        whiteboard.set_element_callbacks(
            added=element_added_callback,
            modified=element_modified_callback,
            removed=element_removed_callback,
        )

        return {
            "session_id": session_id,
            "message": "白板会话创建成功",
            "board_name": request.board_name,
            "owner_id": request.owner_id,
        }

    except Exception as e:
        logger.error(f"创建白板会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/join")
async def join_whiteboard(session_id: str, request: JoinWhiteboardRequest) -> Dict:
    """
    加入白板会话
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        success = whiteboard.join_session(session_id, request.user_id)

        if success:
            # 通知其他用户有新用户加入
            await connection_manager.broadcast_to_session(
                session_id,
                {
                    "type": "user_joined",
                    "user_id": request.user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return {
                "session_id": session_id,
                "user_id": request.user_id,
                "message": "成功加入白板会话",
            }
        else:
            raise HTTPException(status_code=400, detail="加入会话失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加入白板会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/strokes/start")
async def start_stroke(session_id: str, request: StrokeStartRequest) -> Dict:
    """
    开始绘制笔画
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        stroke_id = whiteboard.start_stroke(
            x=request.x,
            y=request.y,
            pressure=request.pressure,
            stroke_type=request.stroke_type,
            color=request.color,
            width=request.width,
            user_id=request.user_id,
        )

        return {"stroke_id": stroke_id, "message": "笔画开始绘制"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始绘制笔画失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/strokes/add-point")
async def add_stroke_point(session_id: str, request: StrokePointRequest) -> Dict:
    """
    添加笔画点
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        success = whiteboard.add_stroke_point(
            x=request.x, y=request.y, pressure=request.pressure
        )

        if success:
            return {"message": "笔画点已添加"}
        else:
            raise HTTPException(status_code=400, detail="没有正在进行的笔画")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加笔画点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/strokes/end")
async def end_stroke(session_id: str) -> Dict:
    """
    结束绘制笔画
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        element = whiteboard.end_stroke()

        if element:
            return {"element_id": element.id, "message": "笔画绘制完成"}
        else:
            raise HTTPException(status_code=400, detail="没有有效的笔画")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"结束绘制笔画失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/shapes/add")
async def add_shape(session_id: str, shape_data: Dict) -> Dict:
    """
    添加形状
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        shape_id = whiteboard.add_shape(
            shape_type=shape_data.get("shape_type", "rectangle"),
            start_x=shape_data.get("start_x", 0),
            start_y=shape_data.get("start_y", 0),
            end_x=shape_data.get("end_x", 100),
            end_y=shape_data.get("end_y", 100),
            user_id=shape_data.get("user_id"),
        )

        return {"shape_id": shape_id, "message": "形状已添加"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加形状失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/text/add")
async def add_text(session_id: str, text_data: Dict) -> Dict:
    """
    添加文本
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        text_id = whiteboard.add_text(
            x=text_data.get("x", 0),
            y=text_data.get("y", 0),
            content=text_data.get("content", ""),
            user_id=text_data.get("user_id"),
        )

        return {"text_id": text_id, "message": "文本已添加"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加文本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}/elements/{element_id}")
async def modify_element(
    session_id: str, element_id: str, request: ElementModifyRequest
) -> Dict:
    """
    修改元素
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        success = whiteboard.modify_element(element_id, request.updates)

        if success:
            return {"message": "元素修改成功"}
        else:
            raise HTTPException(status_code=404, detail="元素不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改元素失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}/elements/{element_id}")
async def remove_element(session_id: str, element_id: str) -> Dict:
    """
    删除元素
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        success = whiteboard.remove_element(element_id)

        if success:
            return {"message": "元素删除成功"}
        else:
            raise HTTPException(status_code=404, detail="元素不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除元素失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/elements")
async def get_elements(
    session_id: str, page_number: Optional[int] = None
) -> List[Dict]:
    """
    获取页面元素
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        elements = whiteboard.get_elements(page_number)

        return [element.dict() for element in elements]

    except Exception as e:
        logger.error(f"获取元素失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/pages/add")
async def add_page(session_id: str) -> Dict:
    """
    添加新页面
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        page_number = whiteboard.add_page()

        # 通知所有连接的客户端
        await connection_manager.broadcast_to_session(
            session_id,
            {
                "type": "page_added",
                "page_number": page_number,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return {"page_number": page_number, "message": "新页面已添加"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加页面失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/pages/switch")
async def switch_page(session_id: str, page_data: Dict) -> Dict:
    """
    切换页面
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        page_number = page_data.get("page_number", 0)
        success = whiteboard.switch_page(page_number)

        if success:
            # 通知所有连接的客户端
            await connection_manager.broadcast_to_session(
                session_id,
                {
                    "type": "page_switched",
                    "page_number": page_number,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return {"page_number": page_number, "message": "页面切换成功"}
        else:
            raise HTTPException(status_code=400, detail="无效的页面编号")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换页面失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/info")
async def get_whiteboard_info(session_id: str) -> Dict:
    """
    获取白板会话信息
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        whiteboard = whiteboard_instances[session_id]
        session_info = whiteboard.get_session_info()

        if not session_info:
            raise HTTPException(status_code=404, detail="会话信息不可用")

        return {
            "session_id": session_info.session_id,
            "board_name": session_info.board_name,
            "owner_id": session_info.owner_id,
            "participants": session_info.participants,
            "current_page": session_info.current_page,
            "total_pages": len(session_info.pages),
            "is_active": session_info.is_active,
            "created_at": session_info.created_at.isoformat(),
            "last_activity": session_info.last_activity.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取白板信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/close")
async def close_whiteboard(session_id: str) -> Dict:
    """
    关闭白板会话
    """
    try:
        if session_id not in whiteboard_instances:
            raise HTTPException(status_code=404, detail="白板会话不存在")

        # 通知所有参与者会话即将关闭
        await connection_manager.broadcast_to_session(
            session_id,
            {
                "type": "session_closing",
                "message": "白板会话即将关闭",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # 关闭白板
        whiteboard = whiteboard_instances[session_id]
        whiteboard.close_session()

        # 清理连接
        if session_id in connection_manager.active_connections:
            for websocket in connection_manager.active_connections[session_id][:]:
                await websocket.close(code=1000, reason="会话已关闭")
            del connection_manager.active_connections[session_id]

        # 移除实例
        del whiteboard_instances[session_id]

        return {"session_id": session_id, "message": "白板会话已关闭"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关闭白板会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def whiteboard_websocket(websocket: WebSocket, session_id: str):
    """
    白板协作WebSocket连接
    """
    try:
        if session_id not in whiteboard_instances:
            await websocket.close(code=4004, reason="白板会话不存在")
            return

        # 建立连接
        await connection_manager.connect(session_id, websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()
                message_type = data.get("type")

                # 处理不同类型的消息
                if message_type == "cursor_move":
                    # 处理光标移动
                    await handle_cursor_move(session_id, data)
                elif message_type == "tool_change":
                    # 处理工具切换
                    await handle_tool_change(session_id, data)
                elif message_type == "get_elements":
                    # 返回当前页面元素
                    await handle_get_elements(session_id, websocket)

        except WebSocketDisconnect:
            logger.info(f"白板WebSocket连接断开: {session_id}")
        finally:
            connection_manager.disconnect(session_id, websocket)

    except Exception as e:
        logger.error(f"WebSocket连接处理失败: {e}")
        await websocket.close(code=1011, reason="服务器内部错误")


async def handle_cursor_move(session_id: str, data: Dict):
    """处理光标移动"""
    user_id = data.get("user_id")
    position = data.get("position", {"x": 0, "y": 0})

    # 广播光标位置给其他用户
    await connection_manager.broadcast_to_session(
        session_id,
        {
            "type": "cursor_update",
            "user_id": user_id,
            "position": position,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def handle_tool_change(session_id: str, data: Dict):
    """处理工具切换"""
    user_id = data.get("user_id")
    tool = data.get("tool")

    # 广播工具切换信息
    await connection_manager.broadcast_to_session(
        session_id,
        {
            "type": "tool_change",
            "user_id": user_id,
            "tool": tool,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def handle_get_elements(session_id: str, websocket: WebSocket):
    """处理获取元素请求"""
    if session_id in whiteboard_instances:
        whiteboard = whiteboard_instances[session_id]
        elements = whiteboard.get_elements()

        await websocket.send_json(
            {
                "type": "elements_response",
                "elements": [element.dict() for element in elements],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get("/health")
async def health_check() -> Dict:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "whiteboard_collaboration",
        "active_sessions": len(whiteboard_instances),
        "connected_users": sum(
            len(conns) for conns in connection_manager.active_connections.values()
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }
