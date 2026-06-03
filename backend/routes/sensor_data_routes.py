"""
传感器数据 API 路由
提供模拟传感器数据，供 AR 实验室前端使用
实际硬件连接时可通过 ESP32 串口服务获取真实数据
"""

import logging
from datetime import datetime
from random import uniform

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sensor-data", tags=["传感器数据"])


@router.get("/latest")
async def get_latest_sensor_data():
    """
    获取最新传感器模拟数据
    返回温度、湿度、气压、光照等常见传感器读数
    """
    return {
        "temperature": round(uniform(20.0, 35.0), 2),
        "humidity": round(uniform(40.0, 80.0), 2),
        "pressure": round(uniform(1000.0, 1020.0), 2),
        "light": round(uniform(100.0, 1000.0), 2),
        "sound": round(uniform(30.0, 80.0), 2),
        "pm25": round(uniform(0.0, 50.0), 2),
        "timestamp": datetime.now().isoformat(),
    }
