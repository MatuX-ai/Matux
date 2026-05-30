"""
MQTT客户端服务封装
提供硬件异常上报的MQTT通信能力
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any, Callable, Dict, Optional
import uuid

try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("警告: paho-mqtt未安装，请运行 'pip install paho-mqtt'")

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    """MQTT配置"""

    broker_host: str = "localhost"  # MQTT代理主机
    broker_port: int = 1883  # MQTT代理端口
    username: Optional[str] = None  # 用户名
    password: Optional[str] = None  # 密码
    client_id: Optional[str] = None  # 客户端ID
    keepalive: int = 60  # 心跳间隔(秒)
    qos: int = 1  # 服务质量等级
    retain: bool = False  # 是否保留消息
    tls_enabled: bool = False  # 是否启用TLS
    ca_cert: Optional[str] = None  # CA证书路径
    client_cert: Optional[str] = None  # 客户端证书路径
    client_key: Optional[str] = None  # 客户端密钥路径


class MQTTService:
    """MQTT服务类"""

    def __init__(self, config: MQTTConfig):
        if not MQTT_AVAILABLE:
            raise RuntimeError("MQTT功能不可用，请安装paho-mqtt库")

        self.config = config
        self.client = None
        self.connected = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.subscriptions: Dict[str, Callable] = {}

        # 回调函数
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        self.on_message_callback: Optional[Callable] = None

    def initialize(self):
        """初始化MQTT客户端"""
        try:
            # 生成客户端ID
            client_id = (
                self.config.client_id or f"hardware_alert_{uuid.uuid4().hex[:8]}"
            )

            # 创建MQTT客户端
            self.client = mqtt.Client(
                client_id=client_id,
                clean_session=True,
                userdata=None,
                protocol=mqtt.MQTTv311,
                transport="tcp",
            )

            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe

            # 设置认证
            if self.config.username and self.config.password:
                self.client.username_pw_set(self.config.username, self.config.password)

            # 配置TLS
            if self.config.tls_enabled:
                self._configure_tls()

            logger.info(f"MQTT客户端初始化完成: {client_id}")
            return True

        except Exception as e:
            logger.error(f"MQTT客户端初始化失败: {str(e)}")
            return False

    def _configure_tls(self):
        """配置TLS连接"""
        try:
            if self.config.ca_cert:
                self.client.tls_set(
                    ca_certs=self.config.ca_cert,
                    certfile=self.config.client_cert,
                    keyfile=self.config.client_key,
                )
            else:
                self.client.tls_set()

            logger.info("MQTT TLS配置完成")
        except Exception as e:
            logger.error(f"MQTT TLS配置失败: {str(e)}")
            raise

    def connect(self) -> bool:
        """连接到MQTT代理"""
        if not self.client:
            logger.error("MQTT客户端未初始化")
            return False

        try:
            logger.info(
                f"正在连接MQTT代理: {self.config.broker_host}:{self.config.broker_port}"
            )
            self.client.connect(
                host=self.config.broker_host,
                port=self.config.broker_port,
                keepalive=self.config.keepalive,
            )

            # 启动网络循环
            self.client.loop_start()
            return True

        except Exception as e:
            logger.error(f"MQTT连接失败: {str(e)}")
            return False

    def disconnect(self):
        """断开MQTT连接"""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT连接已断开")
            except Exception as e:
                logger.error(f"MQTT断开连接失败: {str(e)}")

        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.connected = True
            self.reconnect_delay = 1
            logger.info("MQTT连接成功")

            # 重新订阅主题
            self._resubscribe_topics()

            if self.on_connect_callback:
                self.on_connect_callback()
        else:
            logger.error(f"MQTT连接失败，返回码: {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.connected = False
        logger.warning(f"MQTT连接断开，返回码: {rc}")

        if self.on_disconnect_callback:
            self.on_disconnect_callback(rc)

        # 自动重连
        if rc != 0:  # 非正常断开
            self._attempt_reconnect()

    def _attempt_reconnect(self):
        """尝试重连"""
        if not self.client:
            return

        try:
            logger.info(f"尝试重连MQTT，延迟 {self.reconnect_delay} 秒...")
            asyncio.sleep(self.reconnect_delay)

            self.client.reconnect()
            self.reconnect_delay = min(
                self.reconnect_delay * 2, self.max_reconnect_delay
            )

        except Exception as e:
            logger.error(f"MQTT重连失败: {str(e)}")

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            payload = msg.payload.decode("utf-8")
            logger.debug(f"收到MQTT消息 - Topic: {msg.topic}, Payload: {payload}")

            # 调用订阅回调
            if msg.topic in self.subscriptions:
                callback = self.subscriptions[msg.topic]
                try:
                    callback(msg.topic, payload)
                except Exception as e:
                    logger.error(f"订阅回调执行失败: {str(e)}")

            # 调用全局消息回调
            if self.on_message_callback:
                self.on_message_callback(msg.topic, payload)

        except Exception as e:
            logger.error(f"处理MQTT消息失败: {str(e)}")

    def _on_publish(self, client, userdata, mid):
        """消息发布回调"""
        logger.debug(f"消息发布确认，mid: {mid}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅确认回调"""
        logger.info(f"订阅确认，mid: {mid}, QoS: {granted_qos}")

    def subscribe(
        self, topic: str, callback: Callable[[str, str], None] = None
    ) -> bool:
        """订阅主题"""
        if not self.connected:
            logger.warning("MQTT未连接，无法订阅主题")
            return False

        try:
            result, mid = self.client.subscribe(topic, qos=self.config.qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if callback:
                    self.subscriptions[topic] = callback
                logger.info(f"成功订阅主题: {topic}")
                return True
            else:
                logger.error(f"订阅主题失败: {topic}, 错误码: {result}")
                return False

        except Exception as e:
            logger.error(f"订阅主题异常: {str(e)}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """取消订阅主题"""
        if not self.connected:
            return False

        try:
            result, mid = self.client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscriptions:
                    del self.subscriptions[topic]
                logger.info(f"成功取消订阅主题: {topic}")
                return True
            else:
                logger.error(f"取消订阅失败: {topic}, 错误码: {result}")
                return False

        except Exception as e:
            logger.error(f"取消订阅异常: {str(e)}")
            return False

    def publish(
        self, topic: str, payload: Any, qos: int = None, retain: bool = None
    ) -> bool:
        """发布消息"""
        if not self.connected:
            logger.warning("MQTT未连接，无法发布消息")
            return False

        try:
            # 处理载荷
            if isinstance(payload, (dict, list)):
                payload_str = json.dumps(payload, ensure_ascii=False)
            else:
                payload_str = str(payload)

            # 使用配置的默认值
            publish_qos = qos if qos is not None else self.config.qos
            publish_retain = retain if retain is not None else self.config.retain

            result, mid = self.client.publish(
                topic=topic, payload=payload_str, qos=publish_qos, retain=publish_retain
            )

            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"消息发布成功 - Topic: {topic}")
                return True
            else:
                logger.error(f"消息发布失败 - Topic: {topic}, 错误码: {result}")
                return False

        except Exception as e:
            logger.error(f"消息发布异常 - Topic: {topic}, Error: {str(e)}")
            return False

    def _resubscribe_topics(self):
        """重新订阅所有主题"""
        for topic in list(self.subscriptions.keys()):
            self.subscribe(topic)

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "connected": self.connected,
            "broker": f"{self.config.broker_host}:{self.config.broker_port}",
            "client_id": (
                self.client._client_id.decode()
                if self.client and self.client._client_id
                else None
            ),
            "subscriptions": list(self.subscriptions.keys()),
            "config": {
                "qos": self.config.qos,
                "keepalive": self.config.keepalive,
                "tls_enabled": self.config.tls_enabled,
            },
        }


class HardwareAlertMQTTService:
    """硬件告警MQTT服务"""

    def __init__(
        self, mqtt_config: MQTTConfig, alert_topic_prefix: str = "hardware/alerts"
    ):
        self.mqtt_service = MQTTService(mqtt_config)
        self.alert_topic_prefix = alert_topic_prefix.rstrip("/")
        self.initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            if self.mqtt_service.initialize():
                self.initialized = True
                logger.info("硬件告警MQTT服务初始化成功")
                return True
            else:
                logger.error("硬件告警MQTT服务初始化失败")
                return False
        except Exception as e:
            logger.error(f"硬件告警MQTT服务初始化异常: {str(e)}")
            return False

    def connect(self) -> bool:
        """连接服务"""
        if not self.initialized:
            logger.error("服务未初始化")
            return False
        return self.mqtt_service.connect()

    def disconnect(self):
        """断开连接"""
        self.mqtt_service.disconnect()
        self.initialized = False

    def send_alert(self, device_id: str, alert_data: Dict[str, Any]) -> bool:
        """发送硬件告警"""
        if not self.initialized or not self.mqtt_service.is_connected():
            logger.warning("MQTT服务未就绪，无法发送告警")
            return False

        try:
            # 构建主题
            topic = f"{self.alert_topic_prefix}/{device_id}"

            # 添加时间戳
            alert_data["timestamp"] = datetime.now().isoformat()

            # 发布告警
            success = self.mqtt_service.publish(topic, alert_data)

            if success:
                logger.info(f"硬件告警发送成功 - 设备: {device_id}, 主题: {topic}")
            else:
                logger.error(f"硬件告警发送失败 - 设备: {device_id}")

            return success

        except Exception as e:
            logger.error(f"发送硬件告警异常: {str(e)}")
            return False

    def send_device_status(self, device_id: str, status_data: Dict[str, Any]) -> bool:
        """发送设备状态"""
        if not self.initialized or not self.mqtt_service.is_connected():
            return False

        try:
            topic = f"{self.alert_topic_prefix}/{device_id}/status"
            status_data["timestamp"] = datetime.now().isoformat()

            return self.mqtt_service.publish(topic, status_data)
        except Exception as e:
            logger.error(f"发送设备状态异常: {str(e)}")
            return False

    def subscribe_to_alerts(self, callback: Callable[[str, Dict], None]) -> bool:
        """订阅告警消息"""
        if not self.initialized:
            return False

        def message_handler(topic: str, payload: str):
            try:
                # 解析设备ID
                parts = topic.split("/")
                if len(parts) >= 3:
                    device_id = parts[2]

                    # 解析载荷
                    alert_data = json.loads(payload)

                    # 调用回调
                    callback(device_id, alert_data)

            except Exception as e:
                logger.error(f"处理告警消息失败: {str(e)}")

        topic = f"{self.alert_topic_prefix}/+"
        return self.mqtt_service.subscribe(topic, message_handler)

    def is_ready(self) -> bool:
        """检查服务是否就绪"""
        return self.initialized and self.mqtt_service.is_connected()

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "initialized": self.initialized,
            "connected": (
                self.mqtt_service.is_connected() if self.initialized else False
            ),
            "alert_topic_prefix": self.alert_topic_prefix,
            "mqtt_info": (
                self.mqtt_service.get_connection_info() if self.initialized else {}
            ),
        }
