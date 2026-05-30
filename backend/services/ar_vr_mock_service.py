"""
AR/VR模块Mock接口服务
为AR/VR功能提供完整的模拟实现，确保主线开发不受硬件依赖影响
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
import math
import random
import time
from typing import Any, Dict, List
import uuid

from services.ar_vr_content_service import ARVRContentService

logger = logging.getLogger(__name__)


class MockScenario(Enum):
    """Mock场景类型"""

    SUCCESSFUL_INTERACTION = "successful_interaction"
    SENSOR_ERROR = "sensor_error"
    NETWORK_DELAY = "network_delay"
    PARTIAL_FAILURE = "partial_failure"
    HIGH_LATENCY = "high_latency"


class ARVRMockService:
    """AR/VR Mock服务主类"""

    def __init__(self, db_session):
        self.db = db_session
        self.content_service = ARVRContentService(db_session)
        self.active_sessions = {}
        self.mock_data_generators = {}
        self.scenario_configs = self._load_scenario_configs()

    def _load_scenario_configs(self) -> Dict[str, Any]:
        """加载Mock场景配置"""
        return {
            MockScenario.SUCCESSFUL_INTERACTION: {
                "success_rate": 0.95,
                "latency_ms": (10, 50),
                "error_rate": 0.01,
            },
            MockScenario.SENSOR_ERROR: {
                "success_rate": 0.3,
                "latency_ms": (50, 200),
                "error_rate": 0.4,
            },
            MockScenario.NETWORK_DELAY: {
                "success_rate": 0.8,
                "latency_ms": (200, 1000),
                "error_rate": 0.05,
            },
            MockScenario.PARTIAL_FAILURE: {
                "success_rate": 0.7,
                "latency_ms": (30, 150),
                "error_rate": 0.2,
            },
            MockScenario.HIGH_LATENCY: {
                "success_rate": 0.9,
                "latency_ms": (500, 2000),
                "error_rate": 0.02,
            },
        }


class SensorMockGenerator:
    """传感器数据Mock生成器"""

    def __init__(self, scenario: MockScenario = MockScenario.SUCCESSFUL_INTERACTION):
        self.scenario = scenario
        self.base_time = time.time()
        self.noise_level = 0.1

    def generate_accelerometer_data(self) -> Dict[str, Any]:
        """生成加速度计模拟数据"""
        t = time.time() - self.base_time

        # 基础运动模式：轻微晃动 + 周期性运动
        base_motion = {
            "x": math.sin(t * 0.5) * 2.0 + random.uniform(-0.5, 0.5),
            "y": 9.81 + math.cos(t * 0.3) * 1.0 + random.uniform(-0.3, 0.3),
            "z": math.sin(t * 0.7) * 1.5 + random.uniform(-0.4, 0.4),
        }

        # 根据场景调整数据质量
        if self.scenario == MockScenario.SENSOR_ERROR:
            # 模拟传感器故障
            if random.random() < 0.3:
                base_motion["x"] = random.choice([0, float("inf"), float("-inf")])
            if random.random() < 0.2:
                base_motion["y"] = 0

        elif self.scenario == MockScenario.HIGH_LATENCY:
            # 模拟数据滞后
            lag_factor = 0.5 + random.random() * 0.5
            for key in base_motion:
                base_motion[key] *= lag_factor

        return {
            "sensor_type": "accelerometer",
            "payload": base_motion,
            "timestamp": datetime.utcnow().isoformat(),
            "quality": self._calculate_data_quality(base_motion),
        }

    def generate_gyroscope_data(self) -> Dict[str, Any]:
        """生成陀螺仪模拟数据"""
        t = time.time() - self.base_time

        rotation_data = {
            "alpha": (t * 30) % 360,  # 绕Z轴旋转
            "beta": math.sin(t * 0.2) * 15,  # 绕X轴倾斜
            "gamma": math.cos(t * 0.15) * 10,  # 绕Y轴倾斜
        }

        # 添加噪声
        for key in rotation_data:
            noise = random.uniform(-self.noise_level * 10, self.noise_level * 10)
            rotation_data[key] += noise

        return {
            "sensor_type": "gyroscope",
            "payload": rotation_data,
            "timestamp": datetime.utcnow().isoformat(),
            "quality": self._calculate_data_quality(rotation_data),
        }

    def generate_gps_data(self) -> Dict[str, Any]:
        """生成GPS模拟数据"""
        # 模拟在北京附近的移动
        base_lat = 39.9042  # 北京纬度
        base_lng = 116.4074  # 北京经度

        t = time.time() - self.base_time

        # 模拟圆形轨迹移动
        radius = 0.001  # 约111米半径
        lat_offset = radius * math.cos(t * 0.1)
        lng_offset = radius * math.sin(t * 0.1) * 0.8  # 经度变化较小

        gps_data = {
            "latitude": base_lat + lat_offset,
            "longitude": base_lng + lng_offset,
            "altitude": 43.5 + math.sin(t * 0.05) * 2,  # 高度轻微变化
            "accuracy": 5.0 + random.uniform(0, 3),  # 精度5-8米
            "speed": abs(math.cos(t * 0.1) * 2),  # 速度0-2 m/s
        }

        return {
            "sensor_type": "gps",
            "payload": gps_data,
            "timestamp": datetime.utcnow().isoformat(),
            "quality": "high" if gps_data["accuracy"] < 10 else "medium",
        }

    def generate_camera_data(self) -> Dict[str, Any]:
        """生成摄像头模拟数据（Base64占位符）"""
        # 生成模拟的图像数据（实际项目中可能是真实的图像处理）
        placeholder_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        return {
            "sensor_type": "camera",
            "payload": {
                "image": placeholder_image,
                "width": 640,
                "height": 480,
                "timestamp": datetime.utcnow().isoformat(),
                "detection_objects": self._generate_mock_detections(),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "quality": "medium",
        }

    def _generate_mock_detections(self) -> List[Dict[str, Any]]:
        """生成模拟的目标检测结果"""
        objects = ["cube", "sphere", "cylinder", "plane"]
        detections = []

        # 随机生成1-3个检测对象
        for _ in range(random.randint(1, 3)):
            obj_type = random.choice(objects)
            confidence = 0.7 + random.random() * 0.3  # 70%-100%置信度

            detections.append(
                {
                    "type": obj_type,
                    "confidence": round(confidence, 2),
                    "bounding_box": {
                        "x": random.randint(0, 600),
                        "y": random.randint(0, 440),
                        "width": random.randint(20, 100),
                        "height": random.randint(20, 100),
                    },
                    "distance": round(random.uniform(0.5, 5.0), 2),
                }
            )

        return detections

    def _calculate_data_quality(self, data: Dict[str, float]) -> str:
        """计算数据质量等级"""
        # 检查是否有异常值
        has_invalid = any(
            val == float("inf") or val == float("-inf") or val != val  # NaN检查
            for val in data.values()
        )

        if has_invalid:
            return "invalid"
        elif self.scenario == MockScenario.SENSOR_ERROR:
            return "low"
        elif self.scenario == MockScenario.HIGH_LATENCY:
            return "medium"
        else:
            return "high"


class InteractionMockHandler:
    """交互Mock处理器"""

    def __init__(self, scenario: MockScenario = MockScenario.SUCCESSFUL_INTERACTION):
        self.scenario = scenario
        self.interaction_history = []

    def handle_gesture(self, gesture_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理手势交互Mock"""
        gesture_type = gesture_data.get("type", "unknown")

        # 根据场景决定成功率
        success_threshold = self._get_success_threshold()
        success = random.random() < success_threshold

        response_time = self._calculate_response_time()

        result = {
            "success": success,
            "gesture_type": gesture_type,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat(),
            "simulated_effects": [],
        }

        if success:
            result["message"] = f"{gesture_type}手势处理成功"
            result["simulated_effects"] = self._generate_gesture_effects(
                gesture_type, gesture_data
            )
        else:
            result["message"] = f"{gesture_type}手势处理失败"
            result["error_code"] = self._generate_error_code()

        self.interaction_history.append(result)
        return result

    def handle_voice_command(self, command: str) -> Dict[str, Any]:
        """处理语音命令Mock"""
        # 语音命令映射
        command_responses = {
            "开始实验": "实验已开始，物理引擎已激活",
            "停止实验": "实验已停止",
            "重置": "所有对象已重置到初始位置",
            "增加重力": "重力已增加到14.7 m/s²",
            "减少重力": "重力已减少到6.9 m/s²",
            "播放": "仿真动画已开始播放",
            "暂停": "仿真动画已暂停",
        }

        success_threshold = self._get_success_threshold()
        success = random.random() < success_threshold

        response_time = self._calculate_response_time()

        # 匹配命令
        response_message = "未识别的命令"
        for keyword, response in command_responses.items():
            if keyword in command:
                response_message = response
                break

        result = {
            "success": success,
            "command": command,
            "response": response_message,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if not success:
            result["error_code"] = self._generate_error_code()

        self.interaction_history.append(result)
        return result

    def _get_success_threshold(self) -> float:
        """获取当前场景的成功阈值"""
        configs = {
            MockScenario.SUCCESSFUL_INTERACTION: 0.95,
            MockScenario.SENSOR_ERROR: 0.3,
            MockScenario.NETWORK_DELAY: 0.8,
            MockScenario.PARTIAL_FAILURE: 0.7,
            MockScenario.HIGH_LATENCY: 0.9,
        }
        return configs.get(self.scenario, 0.8)

    def _calculate_response_time(self) -> float:
        """计算响应时间"""
        base_times = {
            MockScenario.SUCCESSFUL_INTERACTION: (0.05, 0.2),
            MockScenario.SENSOR_ERROR: (0.1, 0.5),
            MockScenario.NETWORK_DELAY: (0.5, 2.0),
            MockScenario.PARTIAL_FAILURE: (0.1, 0.4),
            MockScenario.HIGH_LATENCY: (1.0, 3.0),
        }

        min_time, max_time = base_times.get(self.scenario, (0.1, 0.5))
        return round(random.uniform(min_time, max_time), 3)

    def _generate_gesture_effects(
        self, gesture_type: str, gesture_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成手势效果模拟"""
        effects = []

        if gesture_type == "tap":
            effects.append(
                {
                    "type": "force_application",
                    "magnitude": random.uniform(10, 50),
                    "direction": [0, 1, 0],
                    "target_objects": ["object_1", "object_2"],
                }
            )
        elif gesture_type == "swipe":
            effects.append(
                {
                    "type": "velocity_change",
                    "delta_velocity": [random.uniform(-5, 5) for _ in range(3)],
                    "affected_objects": ["all_dynamic"],
                }
            )
        elif gesture_type == "pinch":
            effects.append(
                {
                    "type": "scale_change",
                    "scale_factor": gesture_data.get("scale_factor", 1.0),
                    "center_point": gesture_data.get("center", [0, 0, 0]),
                }
            )

        return effects

    def _generate_error_code(self) -> str:
        """生成错误码"""
        error_codes = ["E001", "E002", "E003", "E004", "E005"]
        return random.choice(error_codes)


class PhysicsMockEngine:
    """物理引擎Mock"""

    def __init__(self, scenario: MockScenario = MockScenario.SUCCESSFUL_INTERACTION):
        self.scenario = scenario
        self.objects = {}
        self.gravity = 9.81
        self.time_step = 1 / 60.0
        self.simulation_time = 0

    def initialize_objects(self, content_type: str):
        """根据内容类型初始化模拟对象"""
        if content_type == "virtual_lab":
            self.objects = {
                "ground": {
                    "mass": 0,
                    "position": [0, 0, 0],
                    "velocity": [0, 0, 0],
                    "static": True,
                },
                "ball_1": {
                    "mass": 1.0,
                    "position": [0, 5, 0],
                    "velocity": [0, 0, 0],
                    "static": False,
                },
                "ball_2": {
                    "mass": 2.0,
                    "position": [2, 3, 1],
                    "velocity": [0, 0, 0],
                    "static": False,
                },
            }
        elif content_type == "model_viewer":
            self.objects = {
                "model_base": {
                    "mass": 0,
                    "position": [0, 0, 0],
                    "velocity": [0, 0, 0],
                    "static": True,
                },
                "rotating_part": {
                    "mass": 0.5,
                    "position": [0, 1, 0],
                    "velocity": [0, 0, 0],
                    "static": False,
                },
            }

    def update_physics(self, external_forces: List[Dict] = None):
        """更新物理模拟"""
        self.simulation_time += self.time_step

        for obj_id, obj in self.objects.items():
            if not obj["static"]:
                # 应用重力
                obj["velocity"][1] -= self.gravity * self.time_step

                # 应用外力
                if external_forces:
                    for force in external_forces:
                        if (
                            force.get("target") == obj_id
                            or force.get("target") == "all"
                        ):
                            f_mag = force.get("magnitude", [0, 0, 0])
                            for i in range(3):
                                obj["velocity"][i] += (
                                    f_mag[i] * self.time_step / obj["mass"]
                                )

                # 更新位置
                for i in range(3):
                    obj["position"][i] += obj["velocity"][i] * self.time_step

                # 简单的地面碰撞检测
                if obj["position"][1] < 0:
                    obj["position"][1] = 0
                    obj["velocity"][1] = -obj["velocity"][1] * 0.8  # 弹性碰撞

    def get_state(self) -> Dict[str, Any]:
        """获取物理状态"""
        return {
            "objects": self.objects,
            "gravity": self.gravity,
            "simulation_time": self.simulation_time,
            "scenario": self.scenario.value,
        }


class ARVRMockOrchestrator:
    """AR/VR Mock服务编排器"""

    def __init__(self, db_session):
        self.mock_service = ARVRMockService(db_session)
        self.active_sessions = {}

    async def start_mock_session(
        self,
        content_id: int,
        user_id: int,
        scenario: MockScenario = MockScenario.SUCCESSFUL_INTERACTION,
    ) -> str:
        """启动Mock会话"""
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "content_id": content_id,
            "user_id": user_id,
            "scenario": scenario,
            "started_at": datetime.utcnow(),
            "sensor_generator": SensorMockGenerator(scenario),
            "interaction_handler": InteractionMockHandler(scenario),
            "physics_engine": PhysicsMockEngine(scenario),
            "last_activity": datetime.utcnow(),
        }

        # 初始化物理引擎
        try:
            content = self.mock_service.content_service.get_arvr_content(content_id, 1)
            session_data["physics_engine"].initialize_objects(
                content.content_type.value
            )
        except Exception as e:
            logger.warning(f"初始化物理引擎失败: {e}")

        self.active_sessions[session_id] = session_data
        logger.info(f"Mock会话已启动: {session_id} (场景: {scenario.value})")

        return session_id

    async def stop_mock_session(self, session_id: str) -> bool:
        """停止Mock会话"""
        if session_id in self.active_sessions:
            self.active_sessions.pop(session_id)
            logger.info(f"Mock会话已停止: {session_id}")
            return True
        return False

    async def get_sensor_data_stream(
        self, session_id: str, sensor_types: List[str]
    ) -> List[Dict[str, Any]]:
        """获取传感器数据流"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")

        session = self.active_sessions[session_id]
        generator = session["sensor_generator"]

        data_stream = []
        for sensor_type in sensor_types:
            if sensor_type == "accelerometer":
                data_stream.append(generator.generate_accelerometer_data())
            elif sensor_type == "gyroscope":
                data_stream.append(generator.generate_gyroscope_data())
            elif sensor_type == "gps":
                data_stream.append(generator.generate_gps_data())
            elif sensor_type == "camera":
                data_stream.append(generator.generate_camera_data())

        session["last_activity"] = datetime.utcnow()
        return data_stream

    async def handle_interaction(
        self, session_id: str, interaction_type: str, interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理交互请求"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")

        session = self.active_sessions[session_id]
        handler = session["interaction_handler"]

        if interaction_type == "gesture":
            result = handler.handle_gesture(interaction_data)
        elif interaction_type == "voice":
            result = handler.handle_voice_command(interaction_data.get("command", ""))
        else:
            result = {"success": False, "message": "不支持的交互类型"}

        # 更新物理引擎
        if result["success"] and "simulated_effects" in result:
            external_forces = [
                effect
                for effect in result["simulated_effects"]
                if effect["type"] == "force_application"
            ]
            session["physics_engine"].update_physics(external_forces)

        session["last_activity"] = datetime.utcnow()
        return result

    async def get_physics_state(self, session_id: str) -> Dict[str, Any]:
        """获取物理状态"""
        if session_id not in self.active_sessions:
            raise ValueError("会话不存在")

        session = self.active_sessions[session_id]
        physics_state = session["physics_engine"].get_state()
        session["last_activity"] = datetime.utcnow()

        return physics_state

    async def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """清理超时的会话"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        expired_sessions = [
            sid
            for sid, session in self.active_sessions.items()
            if session["last_activity"] < cutoff_time
        ]

        for session_id in expired_sessions:
            await self.stop_mock_session(session_id)

        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个超时会话")


# Mock服务工厂
def create_mock_service(
    db_session, scenario: MockScenario = MockScenario.SUCCESSFUL_INTERACTION
):
    """创建Mock服务实例"""
    return ARVRMockService(db_session)


def get_mock_orchestrator(db_session):
    """获取Mock服务编排器"""
    return ARVRMockOrchestrator(db_session)


# 预定义的Mock场景配置
MOCK_SCENARIOS = {
    "ideal_conditions": MockScenario.SUCCESSFUL_INTERACTION,
    "hardware_failure": MockScenario.SENSOR_ERROR,
    "network_issues": MockScenario.NETWORK_DELAY,
    "partial_degradation": MockScenario.PARTIAL_FAILURE,
    "high_latency_env": MockScenario.HIGH_LATENCY,
}
