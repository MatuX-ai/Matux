"""
硬件告警管理API路由
提供硬件异常上报和管理的相关接口
"""

from datetime import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from config.settings import settings
from models.hardware_alert import AlertSeverity, AlertSource, AlertType
from services.hardware_alert_detection_service import HardwareAlertManager
from services.hardware_alert_mqtt_service import HardwareAlertMQTTService, MQTTConfig

logger = logging.getLogger(__name__)

# 创建路由路由器
router = APIRouter(prefix="/api/v1/hardware-alerts", tags=["Hardware Alerts"])

# 全局服务实例
hardware_alert_manager: Optional[HardwareAlertManager] = None
mqtt_service: Optional[HardwareAlertMQTTService] = None


class AlertCreateRequest(BaseModel):
    """创建告警请求"""

    device_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: Optional[dict] = None
    metrics: Optional[dict] = None


class AlertResponse(BaseModel):
    """告警响应"""

    alert_id: str
    device_id: str
    device_name: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    source: AlertSource
    timestamp: datetime
    resolved: bool
    details: Optional[dict]


class DeviceStatusResponse(BaseModel):
    """设备状态响应"""

    device_id: str
    device_name: Optional[str]
    status: str
    last_seen: datetime
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    temperature: Optional[float]
    alert_count: int
    error_count: int


def get_hardware_alert_manager() -> HardwareAlertManager:
    """获取硬件告警管理器依赖"""
    global hardware_alert_manager
    if hardware_alert_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="硬件告警服务未初始化",
        )
    return hardware_alert_manager


def get_mqtt_service() -> HardwareAlertMQTTService:
    """获取MQTT服务依赖"""
    global mqtt_service
    if mqtt_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MQTT服务未初始化"
        )
    return mqtt_service


@router.on_event("startup")
async def startup_event():
    """应用启动事件 - 初始化服务"""
    global hardware_alert_manager, mqtt_service

    try:
        if settings.HARDWARE_ALERT_MQTT_ENABLED:
            # 初始化MQTT服务
            mqtt_config = MQTTConfig(
                broker_host=settings.HARDWARE_ALERT_MQTT_BROKER,
                broker_port=settings.HARDWARE_ALERT_MQTT_PORT,
                username=settings.HARDWARE_ALERT_MQTT_USERNAME,
                password=settings.HARDWARE_ALERT_MQTT_PASSWORD,
                qos=settings.HARDWARE_ALERT_MQTT_QOS,
                tls_enabled=settings.HARDWARE_ALERT_MQTT_TLS_ENABLED,
                ca_cert=settings.HARDWARE_ALERT_MQTT_CA_CERT,
                client_cert=settings.HARDWARE_ALERT_MQTT_CLIENT_CERT,
                client_key=settings.HARDWARE_ALERT_MQTT_CLIENT_KEY,
            )

            mqtt_service = HardwareAlertMQTTService(
                mqtt_config=mqtt_config,
                alert_topic_prefix=settings.HARDWARE_ALERT_MQTT_TOPIC_PREFIX,
            )

            if mqtt_service.initialize() and mqtt_service.connect():
                logger.info("硬件告警MQTT服务初始化成功")
            else:
                logger.error("硬件告警MQTT服务初始化失败")
                return

        # 初始化告警管理器
        if mqtt_service:
            hardware_alert_manager = HardwareAlertManager(mqtt_service)

            if settings.HARDWARE_ALERT_DETECTION_ENABLED:
                hardware_alert_manager.start_monitoring(
                    interval_seconds=settings.HARDWARE_ALERT_MONITORING_INTERVAL
                )
                logger.info("硬件告警检测服务已启动")

    except Exception as e:
        logger.error(f"硬件告警服务启动失败: {str(e)}")


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件 - 清理资源"""
    global hardware_alert_manager, mqtt_service

    try:
        if hardware_alert_manager:
            hardware_alert_manager.stop_monitoring()
            logger.info("硬件告警检测服务已停止")

        if mqtt_service:
            mqtt_service.disconnect()
            logger.info("硬件告警MQTT服务已断开")

    except Exception as e:
        logger.error(f"硬件告警服务关闭失败: {str(e)}")


@router.post(
    "/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED
)
async def create_alert(
    alert_request: AlertCreateRequest,
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """手动创建硬件告警"""
    try:
        alert = alert_manager.report_manual_alert(
            device_id=alert_request.device_id,
            alert_type=alert_request.alert_type,
            severity=alert_request.severity,
            message=alert_request.message,
            details=alert_request.details,
        )

        return AlertResponse(**alert.dict())

    except Exception as e:
        logger.error(f"创建告警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建告警失败: {str(e)}",
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    device_id: Optional[str] = Query(None, description="设备ID过滤"),
    alert_type: Optional[AlertType] = Query(None, description="告警类型过滤"),
    severity: Optional[AlertSeverity] = Query(None, description="严重程度过滤"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """获取告警列表"""
    try:
        # 获取活跃告警
        alerts = alert_manager.get_active_alerts()

        # 应用过滤条件
        if device_id:
            alerts = [a for a in alerts if a.device_id == device_id]

        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # 限制返回数量
        alerts = alerts[:limit]

        return [AlertResponse(**alert.dict()) for alert in alerts]

    except Exception as e:
        logger.error(f"获取告警列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警列表失败: {str(e)}",
        )


@router.get("/alerts/device/{device_id}", response_model=List[AlertResponse])
async def get_device_alerts(
    device_id: str,
    limit: int = Query(20, ge=1, le=100),
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """获取指定设备的告警历史"""
    try:
        alerts = alert_manager.get_device_alerts(device_id, limit=limit)
        return [AlertResponse(**alert.dict()) for alert in alerts]

    except Exception as e:
        logger.error(f"获取设备告警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备告警失败: {str(e)}",
        )


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: Optional[str] = None,
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """解决告警"""
    try:
        # 在实际实现中，这里应该更新数据库中的告警状态
        # 目前只是简单地记录日志
        logger.info(f"告警已解决: {alert_id}, 解决人: {resolved_by or 'system'}")

        return {"message": "告警已标记为已解决", "alert_id": alert_id}

    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解决告警失败: {str(e)}",
        )


@router.get("/devices/status", response_model=List[DeviceStatusResponse])
async def list_device_status(
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """获取所有设备状态"""
    try:
        device_statuses = []

        for device_id, status_obj in alert_manager.alert_detector.device_status.items():
            device_statuses.append(
                DeviceStatusResponse(
                    device_id=status_obj.device_id,
                    device_name=status_obj.device_name,
                    status=status_obj.status,
                    last_seen=status_obj.last_seen,
                    cpu_usage=status_obj.cpu_usage,
                    memory_usage=status_obj.memory_usage,
                    temperature=status_obj.temperature,
                    alert_count=status_obj.alert_count,
                    error_count=status_obj.error_count,
                )
            )

        return device_statuses

    except Exception as e:
        logger.error(f"获取设备状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备状态失败: {str(e)}",
        )


@router.get("/devices/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: str,
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """获取指定设备状态"""
    try:
        if device_id not in alert_manager.alert_detector.device_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"设备不存在: {device_id}"
            )

        status_obj = alert_manager.alert_detector.device_status[device_id]

        return DeviceStatusResponse(
            device_id=status_obj.device_id,
            device_name=status_obj.device_name,
            status=status_obj.status,
            last_seen=status_obj.last_seen,
            cpu_usage=status_obj.cpu_usage,
            memory_usage=status_obj.memory_usage,
            temperature=status_obj.temperature,
            alert_count=status_obj.alert_count,
            error_count=status_obj.error_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备状态失败: {str(e)}",
        )


@router.post("/devices/{device_id}/metrics")
async def report_device_metrics(
    device_id: str,
    metrics: dict,
    alert_manager: HardwareAlertManager = Depends(get_hardware_alert_manager),
):
    """上报设备指标数据"""
    try:
        # 检测异常
        alerts = alert_manager.alert_detector.detect_anomalies(device_id, metrics)

        return {
            "message": f"设备 {device_id} 指标已接收",
            "detected_alerts": len(alerts),
            "alerts": [AlertResponse(**alert.dict()) for alert in alerts],
        }

    except Exception as e:
        logger.error(f"处理设备指标失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理设备指标失败: {str(e)}",
        )


@router.get("/service/info")
async def get_service_info(
    mqtt_service: HardwareAlertMQTTService = Depends(get_mqtt_service),
):
    """获取服务状态信息"""
    try:
        return {
            "mqtt_service": mqtt_service.get_service_info(),
            "settings": {
                "mqtt_enabled": settings.HARDWARE_ALERT_MQTT_ENABLED,
                "detection_enabled": settings.HARDWARE_ALERT_DETECTION_ENABLED,
                "monitoring_interval": settings.HARDWARE_ALERT_MONITORING_INTERVAL,
            },
        }

    except Exception as e:
        logger.error(f"获取服务信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取服务信息失败: {str(e)}",
        )


@router.post("/test-alert")
async def send_test_alert(
    device_id: str = Query(..., description="测试设备ID"),
    alert_type: AlertType = Query(AlertType.UNKNOWN_ERROR, description="告警类型"),
    severity: AlertSeverity = Query(AlertSeverity.INFO, description="严重程度"),
    mqtt_service: HardwareAlertMQTTService = Depends(get_mqtt_service),
):
    """发送测试告警"""
    try:
        test_alert = {
            "alert_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "device_id": device_id,
            "alert_type": alert_type.value,
            "severity": severity.value,
            "message": f"测试告警 - {alert_type.value}",
            "source": AlertSource.HARDWARE_DEVICE.value,
            "timestamp": datetime.now().isoformat(),
            "test": True,
        }

        success = mqtt_service.send_alert(device_id, test_alert)

        if success:
            return {"message": "测试告警发送成功", "alert": test_alert}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="测试告警发送失败",
            )

    except Exception as e:
        logger.error(f"发送测试告警失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送测试告警失败: {str(e)}",
        )
