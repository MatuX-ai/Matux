"""
硬件异常检测和上报服务
基于性能监控数据检测硬件异常并自动上报
"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
import uuid

from hardware.hal.performance_monitor import PerformanceMonitor
import numpy as np

from models.hardware_alert import (
    AlertSeverity,
    AlertSource,
    AlertType,
    HardwareAlert,
    HardwareDeviceStatus,
)
from services.hardware_alert_mqtt_service import HardwareAlertMQTTService

logger = logging.getLogger(__name__)


class HardwareAlertDetector:
    """硬件异常检测器"""

    def __init__(self, mqtt_service: HardwareAlertMQTTService):
        self.mqtt_service = mqtt_service
        self.detectors = []
        self.alert_history = deque(maxlen=1000)  # 保留最近1000条告警
        self.device_status = {}  # 设备状态缓存
        self.suppression_rules = {}  # 告警抑制规则

        # 注册默认检测器
        self._register_default_detectors()

    def _register_default_detectors(self):
        """注册默认的异常检测器"""
        # 设备离线检测
        self.register_detector(DeviceOfflineDetector())

        # 性能下降检测
        self.register_detector(PerformanceDegradationDetector())

        # 温度异常检测
        self.register_detector(TemperatureAnomalyDetector())

        # 内存泄漏检测
        self.register_detector(MemoryLeakDetector())

        # 连接稳定性检测
        self.register_detector(ConnectionStabilityDetector())

    def register_detector(self, detector):
        """注册异常检测器"""
        self.detectors.append(detector)
        logger.info(f"已注册检测器: {detector.__class__.__name__}")

    def detect_anomalies(
        self, device_id: str, metrics: Dict[str, Any]
    ) -> List[HardwareAlert]:
        """检测硬件异常"""
        alerts = []

        # 更新设备状态
        self._update_device_status(device_id, metrics)

        # 运行所有检测器
        for detector in self.detectors:
            try:
                detector_alerts = detector.detect(
                    device_id, metrics, self.device_status
                )
                alerts.extend(detector_alerts)
            except Exception as e:
                logger.error(f"检测器 {detector.__class__.__name__} 执行失败: {str(e)}")

        # 处理和发送告警
        processed_alerts = self._process_alerts(alerts)

        return processed_alerts

    def _update_device_status(self, device_id: str, metrics: Dict[str, Any]):
        """更新设备状态"""
        current_time = datetime.now()

        if device_id not in self.device_status:
            self.device_status[device_id] = HardwareDeviceStatus(
                device_id=device_id,
                status="online",
                last_seen=current_time,
                alert_count=0,
                error_count=0,
            )

        status = self.device_status[device_id]
        status.last_seen = current_time
        status.status = "online"

        # 更新性能指标
        if "cpu_usage" in metrics:
            status.cpu_usage = metrics["cpu_usage"]
        if "memory_usage" in metrics:
            status.memory_usage = metrics["memory_usage"]
        if "temperature" in metrics:
            status.temperature = metrics["temperature"]

        # 更新连接信息
        if "connection_status" in metrics:
            status.connection_status = metrics["connection_status"]

    def _process_alerts(self, alerts: List[HardwareAlert]) -> List[HardwareAlert]:
        """处理告警：去重、抑制、发送"""
        processed_alerts = []

        for alert in alerts:
            # 检查告警抑制
            if self._should_suppress_alert(alert):
                logger.debug(f"告警被抑制: {alert.alert_id}")
                continue

            # 添加到历史记录
            self.alert_history.append(alert)

            # 更新设备告警计数
            if alert.device_id in self.device_status:
                self.device_status[alert.device_id].alert_count += 1
                if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
                    self.device_status[alert.device_id].error_count += 1
                    self.device_status[alert.device_id].last_error_time = (
                        alert.timestamp
                    )

            # 发送到MQTT
            self._send_alert_via_mqtt(alert)

            processed_alerts.append(alert)

        return processed_alerts

    def _should_suppress_alert(self, alert: HardwareAlert) -> bool:
        """检查是否应该抑制告警"""
        # 基于时间的抑制
        suppression_key = f"{alert.device_id}_{alert.alert_type}"

        if suppression_key in self.suppression_rules:
            rule = self.suppression_rules[suppression_key]
            if datetime.now() < rule["suppress_until"]:
                return True

        # 相同告警短时间内抑制
        recent_similar_alerts = [
            a
            for a in list(self.alert_history)[-10:]  # 检查最近10条
            if (
                a.device_id == alert.device_id
                and a.alert_type == alert.alert_type
                and (alert.timestamp - a.timestamp).total_seconds() < 300
            )  # 5分钟内
        ]

        return len(recent_similar_alerts) > 2

    def _send_alert_via_mqtt(self, alert: HardwareAlert):
        """通过MQTT发送告警"""
        try:
            alert_dict = alert.dict()
            self.mqtt_service.send_alert(alert.device_id, alert_dict)
        except Exception as e:
            logger.error(f"通过MQTT发送告警失败: {str(e)}")

    def set_suppression_rule(
        self, device_id: str, alert_type: AlertType, duration_seconds: int
    ):
        """设置告警抑制规则"""
        suppression_key = f"{device_id}_{alert_type}"
        self.suppression_rules[suppression_key] = {
            "suppress_until": datetime.now() + timedelta(seconds=duration_seconds),
            "duration": duration_seconds,
        }
        logger.info(f"设置告警抑制规则: {suppression_key}, 持续 {duration_seconds} 秒")


class BaseAnomalyDetector:
    """基础异常检测器"""

    def __init__(self, name: str):
        self.name = name
        self.history = {}  # 每个设备的历史数据

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        """检测异常"""
        raise NotImplementedError("子类必须实现detect方法")

    def _get_device_history(self, device_id: str, max_points: int = 100) -> deque:
        """获取设备历史数据"""
        if device_id not in self.history:
            self.history[device_id] = deque(maxlen=max_points)
        return self.history[device_id]

    def _add_to_history(self, device_id: str, data_point: Any):
        """添加数据到历史记录"""
        history = self._get_device_history(device_id)
        history.append({"timestamp": datetime.now(), "data": data_point})


class DeviceOfflineDetector(BaseAnomalyDetector):
    """设备离线检测器"""

    def __init__(self):
        super().__init__("DeviceOfflineDetector")
        self.offline_threshold = 120  # 2分钟无数据认为离线

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        alerts = []

        # 检查最后在线时间
        if device_id in device_status:
            last_seen = device_status[device_id].last_seen
            time_since_seen = (datetime.now() - last_seen).total_seconds()

            if time_since_seen > self.offline_threshold:
                alert = HardwareAlert(
                    alert_id=str(uuid.uuid4()),
                    device_id=device_id,
                    device_name=device_status[device_id].device_name,
                    alert_type=AlertType.DEVICE_OFFLINE,
                    severity=AlertSeverity.ERROR,
                    message=f"设备 {device_id} 已离线 {int(time_since_seen)} 秒",
                    source=AlertSource.SYSTEM_MONITOR,
                    timestamp=datetime.now(),
                    details={
                        "offline_duration": time_since_seen,
                        "last_seen": last_seen.isoformat(),
                    },
                )
                alerts.append(alert)

        return alerts


class PerformanceDegradationDetector(BaseAnomalyDetector):
    """性能下降检测器"""

    def __init__(self):
        super().__init__("PerformanceDegradationDetector")
        self.cpu_threshold = 85.0  # CPU使用率阈值
        self.memory_threshold = 85.0  # 内存使用率阈值
        self.degradation_window = 10  # 检测窗口大小

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        alerts = []

        # CPU性能下降检测
        if "cpu_usage" in metrics:
            cpu_usage = metrics["cpu_usage"]
            self._add_to_history(device_id + "_cpu", cpu_usage)

            if cpu_usage > self.cpu_threshold:
                # 检查是否持续高负载
                cpu_history = list(self._get_device_history(device_id + "_cpu"))
                if len(cpu_history) >= self.degradation_window:
                    recent_avg = np.mean([h["data"] for h in cpu_history[-5:]])
                    if recent_avg > self.cpu_threshold:
                        alert = HardwareAlert(
                            alert_id=str(uuid.uuid4()),
                            device_id=device_id,
                            alert_type=AlertType.PERFORMANCE_DEGRADATION,
                            severity=AlertSeverity.WARNING,
                            message=f"CPU使用率过高: {cpu_usage:.1f}%",
                            source=AlertSource.PERFORMANCE_MONITOR,
                            timestamp=datetime.now(),
                            details={
                                "metric": "cpu_usage",
                                "current_value": cpu_usage,
                                "threshold": self.cpu_threshold,
                                "recent_average": float(recent_avg),
                            },
                            metrics={"cpu_usage": cpu_usage},
                        )
                        alerts.append(alert)

        # 内存性能下降检测
        if "memory_usage" in metrics:
            memory_usage = metrics["memory_usage"]
            self._add_to_history(device_id + "_memory", memory_usage)

            if memory_usage > self.memory_threshold:
                memory_history = list(self._get_device_history(device_id + "_memory"))
                if len(memory_history) >= self.degradation_window:
                    recent_avg = np.mean([h["data"] for h in memory_history[-5:]])
                    if recent_avg > self.memory_threshold:
                        alert = HardwareAlert(
                            alert_id=str(uuid.uuid4()),
                            device_id=device_id,
                            alert_type=AlertType.PERFORMANCE_DEGRADATION,
                            severity=AlertSeverity.WARNING,
                            message=f"内存使用率过高: {memory_usage:.1f}%",
                            source=AlertSource.PERFORMANCE_MONITOR,
                            timestamp=datetime.now(),
                            details={
                                "metric": "memory_usage",
                                "current_value": memory_usage,
                                "threshold": self.memory_threshold,
                                "recent_average": float(recent_avg),
                            },
                            metrics={"memory_usage": memory_usage},
                        )
                        alerts.append(alert)

        return alerts


class TemperatureAnomalyDetector(BaseAnomalyDetector):
    """温度异常检测器"""

    def __init__(self):
        super().__init__("TemperatureAnomalyDetector")
        self.high_temp_threshold = 75.0  # 高温阈值
        self.critical_temp_threshold = 85.0  # 临界温度阈值

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        alerts = []

        if "temperature" in metrics:
            temperature = metrics["temperature"]

            if temperature >= self.critical_temp_threshold:
                alert = HardwareAlert(
                    alert_id=str(uuid.uuid4()),
                    device_id=device_id,
                    alert_type=AlertType.TEMPERATURE_WARNING,
                    severity=AlertSeverity.CRITICAL,
                    message=f"设备温度严重过高: {temperature:.1f}°C",
                    source=AlertSource.SYSTEM_MONITOR,
                    timestamp=datetime.now(),
                    details={
                        "temperature": temperature,
                        "threshold": self.critical_temp_threshold,
                        "status": "critical",
                    },
                    metrics={"temperature": temperature},
                )
                alerts.append(alert)

            elif temperature >= self.high_temp_threshold:
                alert = HardwareAlert(
                    alert_id=str(uuid.uuid4()),
                    device_id=device_id,
                    alert_type=AlertType.TEMPERATURE_WARNING,
                    severity=AlertSeverity.WARNING,
                    message=f"设备温度偏高: {temperature:.1f}°C",
                    source=AlertSource.SYSTEM_MONITOR,
                    timestamp=datetime.now(),
                    details={
                        "temperature": temperature,
                        "threshold": self.high_temp_threshold,
                        "status": "warning",
                    },
                    metrics={"temperature": temperature},
                )
                alerts.append(alert)

        return alerts


class MemoryLeakDetector(BaseAnomalyDetector):
    """内存泄漏检测器"""

    def __init__(self):
        super().__init__("MemoryLeakDetector")
        self.leak_detection_window = 20  # 检测窗口
        self.leak_threshold = 2.0  # 内存增长阈值(%/分钟)

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        alerts = []

        if "memory_usage" in metrics:
            memory_usage = metrics["memory_usage"]
            self._add_to_history(device_id + "_memory_trend", memory_usage)

            memory_history = list(self._get_device_history(device_id + "_memory_trend"))

            if len(memory_history) >= self.leak_detection_window:
                # 计算内存使用趋势
                timestamps = [h["timestamp"] for h in memory_history]
                values = [h["data"] for h in memory_history]

                # 计算线性趋势斜率
                if len(set(timestamps)) > 1:  # 确保时间戳不同
                    time_diffs = [
                        (t - timestamps[0]).total_seconds() / 60 for t in timestamps
                    ]  # 转换为分钟
                    slope = np.polyfit(time_diffs, values, 1)[0]  # 线性回归斜率

                    if slope > self.leak_threshold:
                        alert = HardwareAlert(
                            alert_id=str(uuid.uuid4()),
                            device_id=device_id,
                            alert_type=AlertType.MEMORY_LEAK,
                            severity=AlertSeverity.ERROR,
                            message=f"检测到内存泄漏趋势: {slope:.2f}%/分钟",
                            source=AlertSource.SYSTEM_MONITOR,
                            timestamp=datetime.now(),
                            details={
                                "trend_slope": float(slope),
                                "threshold": self.leak_threshold,
                                "window_size": self.leak_detection_window,
                                "current_usage": memory_usage,
                            },
                            metrics={
                                "memory_usage": memory_usage,
                                "trend_slope": float(slope),
                            },
                        )
                        alerts.append(alert)

        return alerts


class ConnectionStabilityDetector(BaseAnomalyDetector):
    """连接稳定性检测器"""

    def __init__(self):
        super().__init__("ConnectionStabilityDetector")
        self.disconnection_threshold = 3  # 短时间内断连次数阈值
        self.time_window = 300  # 时间窗口(秒)

    def detect(
        self,
        device_id: str,
        metrics: Dict[str, Any],
        device_status: Dict[str, HardwareDeviceStatus],
    ) -> List[HardwareAlert]:
        alerts = []

        if "connection_status" in metrics:
            connection_status = metrics["connection_status"]

            if connection_status == "disconnected":
                self._add_to_history(device_id + "_disconnect", 1)

                # 统计时间窗口内的断连次数
                disconnect_history = list(
                    self._get_device_history(device_id + "_disconnect")
                )
                window_start = datetime.now() - timedelta(seconds=self.time_window)

                recent_disconnects = [
                    d for d in disconnect_history if d["timestamp"] > window_start
                ]

                if len(recent_disconnects) >= self.disconnection_threshold:
                    alert = HardwareAlert(
                        alert_id=str(uuid.uuid4()),
                        device_id=device_id,
                        alert_type=AlertType.CONNECTION_LOST,
                        severity=AlertSeverity.WARNING,
                        message=f"设备连接不稳定，{self.time_window}秒内断连{len(recent_disconnects)}次",
                        source=AlertSource.SYSTEM_MONITOR,
                        timestamp=datetime.now(),
                        details={
                            "disconnect_count": len(recent_disconnects),
                            "time_window": self.time_window,
                            "threshold": self.disconnection_threshold,
                        },
                    )
                    alerts.append(alert)

        return alerts


class HardwareAlertManager:
    """硬件告警管理器"""

    def __init__(self, mqtt_service: HardwareAlertMQTTService):
        self.alert_detector = HardwareAlertDetector(mqtt_service)
        self.performance_monitor = PerformanceMonitor()
        self.is_running = False
        self.monitoring_task = None

    def start_monitoring(self, interval_seconds: int = 30):
        """开始监控"""
        if self.is_running:
            logger.warning("监控已在运行")
            return

        self.is_running = True
        self.performance_monitor.start_monitoring()
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(f"硬件告警监控已启动，间隔: {interval_seconds}秒")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.performance_monitor.stop_monitoring()

        if self.monitoring_task:
            self.monitoring_task.cancel()

        logger.info("硬件告警监控已停止")

    async def _monitoring_loop(self, interval_seconds: int):
        """监控循环"""
        while self.is_running:
            try:
                await self._check_all_devices()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {str(e)}")
                await asyncio.sleep(interval_seconds)

    async def _check_all_devices(self):
        """检查所有设备"""
        # 获取系统指标
        self.performance_monitor.get_system_metrics()

        # 为每个已知设备生成指标并检测异常
        for device_id, device_status in self.alert_detector.device_status.items():
            # 生成模拟指标数据（实际项目中应从真实设备获取）
            simulated_metrics = self._generate_device_metrics(device_id, device_status)

            # 检测异常
            alerts = self.alert_detector.detect_anomalies(device_id, simulated_metrics)

            if alerts:
                logger.info(f"设备 {device_id} 检测到 {len(alerts)} 个异常")

    def _generate_device_metrics(
        self, device_id: str, device_status: HardwareDeviceStatus
    ) -> Dict[str, Any]:
        """生成设备指标数据（模拟）"""
        # 实际项目中应该从真实设备采集数据
        import random

        return {
            "cpu_usage": random.uniform(10, 90),
            "memory_usage": random.uniform(20, 80),
            "temperature": random.uniform(30, 80),
            "connection_status": random.choice(["connected", "disconnected"]),
            "uptime": random.randint(3600, 86400),
        }

    def report_manual_alert(
        self,
        device_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Optional[Dict] = None,
    ) -> HardwareAlert:
        """手动报告告警"""
        alert = HardwareAlert(
            alert_id=str(uuid.uuid4()),
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            source=AlertSource.HARDWARE_DEVICE,
            timestamp=datetime.now(),
            details=details,
        )

        self.alert_detector._process_alerts([alert])
        return alert

    def get_device_alerts(self, device_id: str, limit: int = 50) -> List[HardwareAlert]:
        """获取设备的告警历史"""
        return [
            alert
            for alert in reversed(list(self.alert_detector.alert_history))
            if alert.device_id == device_id
        ][:limit]

    def get_active_alerts(self) -> List[HardwareAlert]:
        """获取活跃告警"""
        return [
            alert for alert in self.alert_detector.alert_history if not alert.resolved
        ]
