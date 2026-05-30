"""
硬件设备异常告警数据模型
定义硬件异常上报的数据结构和枚举类型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AlertSeverity(str, Enum):
    """告警严重程度"""

    INFO = "info"  # 信息级别
    WARNING = "warning"  # 警告级别
    ERROR = "error"  # 错误级别
    CRITICAL = "critical"  # 严重级别


class AlertType(str, Enum):
    """告警类型"""

    DEVICE_OFFLINE = "device_offline"  # 设备离线
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    TEMPERATURE_WARNING = "temperature_warning"  # 温度警告
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    CONNECTION_LOST = "connection_lost"  # 连接丢失
    AUTHENTICATION_FAILED = "authentication_failed"  # 认证失败
    HARDWARE_FAULT = "hardware_fault"  # 硬件故障
    FIRMWARE_ERROR = "firmware_error"  # 固件错误
    RESOURCE_EXHAUSTED = "resource_exhausted"  # 资源耗尽
    UNKNOWN_ERROR = "unknown_error"  # 未知错误


class AlertSource(str, Enum):
    """告警来源"""

    HARDWARE_DEVICE = "hardware_device"  # 硬件设备直接上报
    SYSTEM_MONITOR = "system_monitor"  # 系统监控检测
    PERFORMANCE_MONITOR = "performance_monitor"  # 性能监控检测
    THIRD_PARTY_SERVICE = "third_party_service"  # 第三方服务


class HardwareAlert(BaseModel):
    """硬件告警模型"""

    alert_id: str  # 告警唯一标识
    device_id: str  # 设备ID
    device_name: Optional[str] = None  # 设备名称
    alert_type: AlertType  # 告警类型
    severity: AlertSeverity  # 告警严重程度
    message: str  # 告警消息
    source: AlertSource  # 告警来源
    timestamp: datetime  # 告警时间戳
    resolved: bool = False  # 是否已解决
    resolved_at: Optional[datetime] = None  # 解决时间
    resolved_by: Optional[str] = None  # 解决人

    # 告警详情
    details: Optional[Dict[str, Any]] = None  # 详细信息
    metrics: Optional[Dict[str, float]] = None  # 相关指标数据
    tags: Optional[List[str]] = None  # 标签

    # 上下文信息
    context: Optional[Dict[str, Any]] = None  # 上下文环境信息
    stack_trace: Optional[str] = None  # 堆栈跟踪（如有）

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AlertNotification(BaseModel):
    """告警通知模型"""

    notification_id: str  # 通知ID
    alert_id: str  # 关联的告警ID
    recipients: List[str]  # 接收者列表
    channels: List[str]  # 通知渠道（email, sms, webhook等）
    subject: str  # 通知主题
    content: str  # 通知内容
    sent_at: datetime  # 发送时间
    status: str = "pending"  # 发送状态
    retry_count: int = 0  # 重试次数


class HardwareDeviceStatus(BaseModel):
    """硬件设备状态模型"""

    device_id: str  # 设备ID
    device_name: Optional[str] = None  # 设备名称
    status: str  # 设备状态 (online/offline/maintenance/error)
    last_seen: datetime  # 最后在线时间
    ip_address: Optional[str] = None  # IP地址
    location: Optional[str] = None  # 位置信息
    firmware_version: Optional[str] = None  # 固件版本
    hardware_version: Optional[str] = None  # 硬件版本

    # 性能指标
    cpu_usage: Optional[float] = None  # CPU使用率 (%)
    memory_usage: Optional[float] = None  # 内存使用率 (%)
    temperature: Optional[float] = None  # 温度 (°C)
    uptime: Optional[int] = None  # 运行时间 (秒)

    # 连接信息
    connection_status: str = "disconnected"  # 连接状态
    connection_type: Optional[str] = None  # 连接类型 (wifi/ethernet/bluetooth)
    signal_strength: Optional[int] = None  # 信号强度

    # 告警统计
    alert_count: int = 0  # 当前活跃告警数
    error_count: int = 0  # 错误计数
    last_error_time: Optional[datetime] = None  # 最后错误时间

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AlertRule(BaseModel):
    """告警规则模型"""

    rule_id: str  # 规则ID
    name: str  # 规则名称
    description: str  # 规则描述
    enabled: bool = True  # 是否启用
    severity: AlertSeverity  # 触发的告警严重程度

    # 触发条件
    conditions: List[Dict[str, Any]]  # 条件列表
    threshold: float  # 阈值
    duration: int  # 持续时间(秒)

    # 抑制和分组
    suppress_for: int = 300  # 抑制时间(秒)
    group_by: List[str] = []  # 分组字段

    # 通知配置
    notify_channels: List[str] = []  # 通知渠道
    notify_recipients: List[str] = []  # 通知接收者

    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
