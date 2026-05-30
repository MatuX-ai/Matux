from dataclasses import dataclass
from enum import Enum
import json
import logging
import threading
import time
from typing import Callable, Dict, List, Optional

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


class HardwareEventType(Enum):
    """硬件事件类型"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DATA_RECEIVED = "data_received"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class SensorReading:
    """传感器读数数据结构"""

    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: float
    raw_data: str


class ESP32SerialCommunicator:
    """ESP32串口通信管理器"""

    def __init__(self, baud_rate: int = 115200, timeout: float = 2.0):
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_listening = False
        self.listener_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.heartbeat_interval = 0.5  # 500ms心跳间隔
        self.last_heartbeat_time = 0
        self.event_handlers: Dict[HardwareEventType, List[Callable]] = {}
        self.supported_commands = {
            "GET_SENSOR_DATA": "GET_SENSORS",
            "SET_PIN_MODE": "SET_PIN",
            "DIGITAL_WRITE": "DIGITAL_WRITE",
            "ANALOG_READ": "ANALOG_READ",
            "PING": "PING",
        }

    def register_event_handler(self, event_type: HardwareEventType, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def unregister_event_handler(
        self, event_type: HardwareEventType, handler: Callable
    ):
        """注销事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)

    def trigger_event(self, event_type: HardwareEventType, data: any = None):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"事件处理器执行错误: {e}")

    def list_available_ports(self) -> List[str]:
        """列出可用的串口"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect(self, port: str) -> bool:
        """连接到指定串口"""
        try:
            if self.is_connected and self.serial_connection:
                self.disconnect()

            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )

            # 等待连接稳定
            time.sleep(2)

            # 测试连接
            if self.ping_device():
                self.is_connected = True
                self.trigger_event(HardwareEventType.CONNECTED, {"port": port})
                logger.info(f"成功连接到设备: {port}")
                return True
            else:
                self.disconnect()
                return False

        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.trigger_event(HardwareEventType.ERROR, {"error": str(e)})
            return False

    def disconnect(self):
        """断开连接"""
        try:
            # 停止监听和心跳线程
            if self.is_listening:
                self.is_listening = False
                if self.listener_thread:
                    self.listener_thread.join(timeout=1.0)
                if self.heartbeat_thread:
                    self.heartbeat_thread.join(timeout=1.0)

            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()

            self.is_connected = False
            self.trigger_event(HardwareEventType.DISCONNECTED)
            logger.info("设备连接已断开")

        except Exception as e:
            logger.error(f"断开连接时出错: {e}")

    def ping_device(self) -> bool:
        """测试设备连接"""
        try:
            response = self.send_command(self.supported_commands["PING"], timeout=1.0)
            return response.strip() == "PONG"
        except (Exception, TimeoutError):
            return False

    def send_command(self, command: str, data: str = "", timeout: float = None) -> str:
        """发送命令到设备"""
        if not self.is_connected or not self.serial_connection:
            raise Exception("设备未连接")

        try:
            # 构造完整命令
            full_command = f"{command}:{data}\n" if data else f"{command}\n"

            # 发送命令
            self.serial_connection.write(full_command.encode())
            self.serial_connection.flush()

            # 读取响应
            read_timeout = timeout or self.timeout
            response = ""
            start_time = time.time()

            while time.time() - start_time < read_timeout:
                if self.serial_connection.in_waiting > 0:
                    char = self.serial_connection.read().decode(
                        "utf-8", errors="ignore"
                    )
                    if char == "\n":
                        break
                    response += char

            return response.strip()

        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            raise

    def start_listening(self):
        """开始监听串口数据"""
        if not self.is_connected:
            raise Exception("设备未连接")

        if self.is_listening:
            return

        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        logger.info("开始监听串口数据")

        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self.heartbeat_thread.start()
        logger.info("心跳机制已启动")

    def _listen_loop(self):
        """监听循环"""
        buffer = ""

        while self.is_listening and self.is_connected:
            try:
                if self.serial_connection.in_waiting > 0:
                    # 读取数据
                    data = self.serial_connection.read(
                        self.serial_connection.in_waiting
                    )
                    buffer += data.decode("utf-8", errors="ignore")

                    # 处理完整的消息
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if line:
                            self._process_incoming_data(line)

                time.sleep(0.01)  # 短暂休眠避免过度占用CPU

            except Exception as e:
                logger.error(f"监听过程中出错: {e}")
                self.trigger_event(HardwareEventType.ERROR, {"error": str(e)})
                break

    def _heartbeat_loop(self):
        """心跳循环 - 每500ms发送一次ping"""
        while self.is_listening and self.is_connected:
            try:
                current_time = time.time()
                if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
                    if self.ping_device():
                        self.last_heartbeat_time = current_time
                        logger.debug("心跳包发送成功")
                    else:
                        logger.warning("心跳包发送失败")
                        # 可以在这里添加重连逻辑

                time.sleep(0.01)  # 10ms检查间隔

            except Exception as e:
                logger.error(f"心跳循环出错: {e}")
                break

    def _process_incoming_data(self, data: str):
        """处理接收到的数据"""
        try:
            # 尝试解析JSON数据
            if data.startswith("{") and data.endswith("}"):
                json_data = json.loads(data)
                self.trigger_event(HardwareEventType.DATA_RECEIVED, json_data)
            else:
                # 普通文本数据
                self.trigger_event(HardwareEventType.DATA_RECEIVED, {"raw": data})

        except json.JSONDecodeError:
            # 非JSON数据
            self.trigger_event(HardwareEventType.DATA_RECEIVED, {"text": data})
        except Exception as e:
            logger.error(f"处理数据时出错: {e}")

    def get_sensor_data(self) -> List[SensorReading]:
        """获取传感器数据"""
        try:
            response = self.send_command(self.supported_commands["GET_SENSOR_DATA"])

            if response.startswith("{"):
                data = json.loads(response)
                readings = []

                # 解析传感器数据
                for sensor_key, sensor_data in data.items():
                    if isinstance(sensor_data, dict):
                        reading = SensorReading(
                            sensor_id=sensor_key,
                            sensor_type=sensor_data.get("type", "unknown"),
                            value=float(sensor_data.get("value", 0)),
                            unit=sensor_data.get("unit", ""),
                            timestamp=time.time(),
                            raw_data=json.dumps(sensor_data),
                        )
                        readings.append(reading)

                return readings
            else:
                # 返回原始数据
                return [
                    SensorReading(
                        sensor_id="raw",
                        sensor_type="raw",
                        value=0,
                        unit="",
                        timestamp=time.time(),
                        raw_data=response,
                    )
                ]

        except Exception as e:
            logger.error(f"获取传感器数据失败: {e}")
            return []

    def set_pin_mode(self, pin: int, mode: str) -> bool:
        """设置引脚模式"""
        try:
            mode_code = "1" if mode.upper() == "OUTPUT" else "0"
            response = self.send_command(
                self.supported_commands["SET_PIN_MODE"], f"{pin},{mode_code}"
            )
            return response.strip() == "OK"
        except Exception as e:
            logger.error(f"设置引脚模式失败: {e}")
            return False

    def digital_write(self, pin: int, value: bool) -> bool:
        """数字输出"""
        try:
            value_code = "1" if value else "0"
            response = self.send_command(
                self.supported_commands["DIGITAL_WRITE"], f"{pin},{value_code}"
            )
            return response.strip() == "OK"
        except Exception as e:
            logger.error(f"数字输出失败: {e}")
            return False

    def analog_read(self, pin: int) -> Optional[int]:
        """模拟读取"""
        try:
            response = self.send_command(
                self.supported_commands["ANALOG_READ"], str(pin)
            )
            return int(response) if response.isdigit() else None
        except Exception as e:
            logger.error(f"模拟读取失败: {e}")
            return None

    def get_device_info(self) -> Dict:
        """获取设备信息"""
        try:
            # 发送设备信息查询命令（需要在ESP32端实现）
            response = self.send_command("GET_DEVICE_INFO")
            if response.startswith("{"):
                return json.loads(response)
            else:
                return {"raw_response": response}
        except Exception as e:
            logger.error(f"获取设备信息失败: {e}")
            return {"error": str(e)}

    @property
    def connection_status(self) -> Dict:
        """获取连接状态"""
        return {
            "connected": self.is_connected,
            "listening": self.is_listening,
            "port": self.serial_connection.port if self.serial_connection else None,
            "baud_rate": self.baud_rate,
            "bytes_in_buffer": (
                self.serial_connection.in_waiting if self.serial_connection else 0
            ),
        }


# 使用示例和服务包装器
class HardwareService:
    """硬件服务包装器"""

    def __init__(self):
        self.communicator = ESP32SerialCommunicator()
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """设置事件处理器"""
        self.communicator.register_event_handler(
            HardwareEventType.CONNECTED,
            lambda data: logger.info(f"硬件连接成功: {data}"),
        )

        self.communicator.register_event_handler(
            HardwareEventType.DISCONNECTED, lambda: logger.info("硬件连接断开")
        )

        self.communicator.register_event_handler(
            HardwareEventType.DATA_RECEIVED, self.handle_sensor_data
        )

        self.communicator.register_event_handler(
            HardwareEventType.ERROR, lambda data: logger.error(f"硬件错误: {data}")
        )

    def handle_sensor_data(self, data):
        """处理传感器数据"""
        # 这里可以添加数据处理逻辑
        logger.debug(f"接收到传感器数据: {data}")

    def connect_to_hardware(self, port: str) -> bool:
        """连接硬件设备"""
        return self.communicator.connect(port)

    def disconnect_hardware(self):
        """断开硬件连接"""
        self.communicator.disconnect()

    def start_data_collection(self):
        """开始数据采集"""
        if self.communicator.is_connected:
            self.communicator.start_listening()

    def get_latest_readings(self) -> List[SensorReading]:
        """获取最新传感器读数"""
        return self.communicator.get_sensor_data()

    def get_connection_status(self) -> Dict:
        """获取连接状态"""
        return self.communicator.connection_status
