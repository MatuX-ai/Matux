from datetime import datetime
import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync

logger = logging.getLogger(__name__)

# 创建AR实验室专用路由器
router = APIRouter(prefix="/api/v1/org/{org_id}/ar-lab", tags=["AR实验室"])


# 硬件连接相关API
@router.get("/hardware/ports", response_model=List[str])
async def get_available_ports(org_id: int = Depends(lambda: 1)):
    """
    获取可用的串口设备列表
    """
    try:
        # 模拟可用端口列表（实际应用中应该扫描系统串口）
        available_ports = [
            "COM3",
            "COM4",
            "/dev/ttyUSB0",
            "/dev/ttyUSB1",
            "/dev/cu.usbserial-A123456",
        ]
        return available_ports
    except Exception as e:
        logger.error(f"获取串口列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取设备列表失败")


@router.post("/hardware/connect")
async def connect_hardware(
    port_data: dict,
    org_id: int = Depends(lambda: 1),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    连接硬件设备
    """
    try:
        port = port_data.get("port")
        if not port:
            raise HTTPException(status_code=400, detail="请指定串口端口")

        # 模拟硬件连接逻辑
        # 实际应用中应该实现真实的串口通信
        logger.info(f"用户 {current_user.username} 尝试连接到端口 {port}")

        # 模拟连接成功
        connected = True
        message = "硬件连接成功" if connected else "硬件连接失败"

        return {
            "connected": connected,
            "port": port,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"硬件连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hardware/disconnect")
async def disconnect_hardware(
    org_id: int = Depends(lambda: 1),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    断开硬件连接
    """
    try:
        # 模拟断开连接逻辑
        logger.info(f"用户 {current_user.username} 断开硬件连接")

        return {
            "disconnected": True,
            "message": "硬件已断开连接",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"断开连接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 传感器数据API
@router.get("/sensor-data/latest")
async def get_latest_sensor_data(
    org_id: int = Depends(lambda: 1),
    limit: int = Query(10, description="返回最新数据条数", le=100),
):
    """
    获取最新的传感器数据
    """
    try:
        # 模拟传感器数据
        import random

        sensor_data = {
            "temperature": round(random.uniform(20.0, 35.0), 2),  # 温度
            "humidity": round(random.uniform(30.0, 80.0), 2),  # 湿度
            "light_intensity": round(random.uniform(0, 1000), 2),  # 光照强度
            "distance": round(random.uniform(5.0, 200.0), 2),  # 距离
            "voltage": round(random.uniform(0, 5.0), 2),  # 电压
            "current": round(random.uniform(0, 0.1), 3),  # 电流
            "timestamp": datetime.now().isoformat(),
        }

        return sensor_data
    except Exception as e:
        logger.error(f"获取传感器数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取传感器数据失败")


@router.get("/sensor-data/history")
async def get_sensor_history(
    org_id: int = Depends(lambda: 1),
    sensor_type: Optional[str] = Query(None, description="传感器类型"),
    hours: int = Query(24, description="查询小时数", le=168),
):
    """
    获取传感器历史数据
    """
    try:
        # 模拟历史数据
        from datetime import timedelta
        import random

        history_data = []
        now = datetime.now()

        for i in range(hours):
            timestamp = now - timedelta(hours=i)
            data_point = {
                "timestamp": timestamp.isoformat(),
                "temperature": round(random.uniform(22.0, 32.0), 2),
                "humidity": round(random.uniform(40.0, 70.0), 2),
                "light_intensity": round(random.uniform(100, 800), 2),
            }
            history_data.append(data_point)

        return {"data": history_data, "count": len(history_data)}
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史数据失败")


# 实验管理API
@router.post("/experiments/start")
async def start_experiment(
    experiment_data: dict = None,
    org_id: int = Depends(lambda: 1),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    开始新的实验
    """
    try:
        # 创建实验记录
        experiment = {
            "id": f"exp_{int(datetime.now().timestamp())}",
            "name": experiment_data.get("name", "默认实验"),
            "description": experiment_data.get("description", "AR硬件实验"),
            "user_id": current_user.id,
            "org_id": org_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "parameters": experiment_data.get("parameters", {}),
        }

        logger.info(f"用户 {current_user.username} 开始实验: {experiment['name']}")

        return experiment
    except Exception as e:
        logger.error(f"启动实验失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/stop")
async def stop_experiment(
    org_id: int = Depends(lambda: 1),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    停止当前实验
    """
    try:
        # 更新实验状态
        result = {
            "stopped": True,
            "message": "实验已停止",
            "end_time": datetime.now().isoformat(),
        }

        logger.info(f"用户 {current_user.username} 停止实验")

        return result
    except Exception as e:
        logger.error(f"停止实验失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/history")
async def get_experiment_history(
    org_id: int = Depends(lambda: 1),
    user_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
):
    """
    获取实验历史记录
    """
    try:
        # 模拟实验历史
        history = [
            {
                "id": "exp_12345",
                "name": "温度传感器实验",
                "start_time": "2026-02-28T10:00:00",
                "end_time": "2026-02-28T10:30:00",
                "duration": 1800,
                "status": "completed",
                "results": {"temperature_range": "22.5-28.3°C"},
            },
            {
                "id": "exp_12346",
                "name": "光照强度测试",
                "start_time": "2026-02-28T11:00:00",
                "end_time": "2026-02-28T11:15:00",
                "duration": 900,
                "status": "completed",
                "results": {"light_range": "150-850 lux"},
            },
        ]

        return {"experiments": history, "count": len(history)}
    except Exception as e:
        logger.error(f"获取实验历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取实验历史失败")


# Unity构建管理API
@router.get("/unity/builds")
async def list_unity_builds(org_id: int = Depends(lambda: 1)):
    """
    列出可用的Unity构建版本
    """
    try:
        builds = [
            {
                "id": "build_001",
                "name": "ARLabMain",
                "version": "1.0.0",
                "platform": "WebGL",
                "size": "45.2 MB",
                "upload_time": "2026-02-28T12:00:00",
                "download_url": "/ar-lab/builds/ARLabMain",
            }
        ]
        return {"builds": builds}
    except Exception as e:
        logger.error(f"获取构建列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取构建列表失败")


@router.post("/unity/builds/upload")
async def upload_unity_build(
    org_id: int = Depends(lambda: 1),
    current_user: User = Depends(get_current_user_sync),
):
    """
    上传新的Unity构建
    """
    try:
        # 这里应该实现文件上传逻辑
        return {
            "uploaded": True,
            "message": "构建上传成功",
            "build_id": f"build_{int(datetime.now().timestamp())}",
        }
    except Exception as e:
        logger.error(f"上传构建失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# WebSocket连接用于实时数据传输
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/sensor-stream")
async def sensor_data_stream(websocket: WebSocket, org_id: int):
    """
    传感器数据实时流WebSocket连接
    """
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            await websocket.receive_text()

            # 模拟发送传感器数据
            import json
            import random

            sensor_update = {
                "type": "sensor_data",
                "data": {
                    "temperature": round(random.uniform(20.0, 35.0), 2),
                    "humidity": round(random.uniform(30.0, 80.0), 2),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            await websocket.send_text(json.dumps(sensor_update))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket连接断开: org_id={org_id}")
    except Exception as e:
        logger.error(f"WebSocket通信错误: {e}")
        manager.disconnect(websocket)
