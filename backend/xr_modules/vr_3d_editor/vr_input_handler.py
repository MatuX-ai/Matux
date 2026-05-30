"""
VR输入处理器
处理VR环境中的各种输入方式
"""

from datetime import datetime
from enum import Enum
import logging
from typing import Callable, Dict, Optional, Tuple

from .models import VRInteractionMode

logger = logging.getLogger(__name__)


class VRInputType(Enum):
    """VR输入类型"""

    CONTROLLER_BUTTON = "controller_button"
    CONTROLLER_AXIS = "controller_axis"
    HAND_GESTURE = "hand_gesture"
    GAZE = "gaze"
    VOICE = "voice"


class VRControllerButton(Enum):
    """控制器按钮"""

    TRIGGER = "trigger"
    GRIP = "grip"
    THUMBSTICK = "thumbstick"
    MENU = "menu"
    A = "a"
    B = "b"
    X = "x"
    Y = "y"


class VRInputHandler:
    """VR输入处理器"""

    def __init__(
        self, interaction_mode: VRInteractionMode = VRInteractionMode.CONTROLLER
    ):
        """
        初始化输入处理器

        Args:
            interaction_mode: 交互模式
        """
        self.interaction_mode = interaction_mode
        self.active_inputs = {}
        self.input_callbacks = {}
        self.gesture_thresholds = {
            "swipe_distance": 0.1,
            "pinch_threshold": 0.05,
            "hold_duration": 0.5,
        }

        logger.info("VRInputHandler初始化完成")

    def register_input_callback(
        self, input_type: VRInputType, callback: Callable[[Dict], None]
    ):
        """注册输入回调"""
        if input_type not in self.input_callbacks:
            self.input_callbacks[input_type] = []
        self.input_callbacks[input_type].append(callback)
        logger.debug(f"已注册输入回调: {input_type}")

    def process_controller_input(
        self,
        controller_id: str,
        button: VRControllerButton,
        pressed: bool,
        axis_values: Optional[Dict[str, float]] = None,
    ):
        """处理控制器输入"""
        input_data = {
            "type": VRInputType.CONTROLLER_BUTTON,
            "controller_id": controller_id,
            "button": button.value,
            "pressed": pressed,
            "axis_values": axis_values or {},
            "timestamp": datetime.utcnow(),
        }

        self._handle_input(input_data)

    def process_hand_gesture(
        self,
        hand_id: str,
        gesture_type: str,
        hand_position: Tuple[float, float, float],
        confidence: float,
    ):
        """处理手势输入"""
        input_data = {
            "type": VRInputType.HAND_GESTURE,
            "hand_id": hand_id,
            "gesture_type": gesture_type,
            "position": hand_position,
            "confidence": confidence,
            "timestamp": datetime.utcnow(),
        }

        self._handle_input(input_data)

    def process_gaze_input(
        self, gaze_target: str, hit_point: Tuple[float, float, float], duration: float
    ):
        """处理注视输入"""
        input_data = {
            "type": VRInputType.GAZE,
            "target": gaze_target,
            "hit_point": hit_point,
            "duration": duration,
            "timestamp": datetime.utcnow(),
        }

        self._handle_input(input_data)

    def process_voice_input(self, text: str, confidence: float):
        """处理语音输入"""
        input_data = {
            "type": VRInputType.VOICE,
            "text": text,
            "confidence": confidence,
            "timestamp": datetime.utcnow(),
        }

        self._handle_input(input_data)

    def _handle_input(self, input_data: Dict):
        """处理输入数据"""
        input_type = input_data["type"]

        # 触发对应类型的回调
        if input_type in self.input_callbacks:
            for callback in self.input_callbacks[input_type]:
                try:
                    callback(input_data)
                except Exception as e:
                    logger.error(f"输入回调执行失败: {e}")

        # 根据交互模式处理特定逻辑
        self._process_interaction_mode(input_data)

    def _process_interaction_mode(self, input_data: Dict):
        """根据交互模式处理输入"""
        if self.interaction_mode == VRInteractionMode.CONTROLLER:
            self._handle_controller_mode(input_data)
        elif self.interaction_mode == VRInteractionMode.HAND_TRACKING:
            self._handle_hand_tracking_mode(input_data)
        elif self.interaction_mode == VRInteractionMode.GAZE_SELECTION:
            self._handle_gaze_mode(input_data)
        elif self.interaction_mode == VRInteractionMode.VOICE_COMMAND:
            self._handle_voice_mode(input_data)

    def _handle_controller_mode(self, input_data: Dict):
        """处理控制器模式输入"""
        if input_data["type"] == VRInputType.CONTROLLER_BUTTON:
            button = input_data["button"]
            pressed = input_data["pressed"]

            # 映射按钮到编辑器操作
            action_map = {
                "trigger": "select_element" if pressed else "release_element",
                "grip": "grab_object" if pressed else "release_object",
                "thumbstick": "move_cursor",
                "a": "confirm_action" if pressed else None,
                "b": "cancel_action" if pressed else None,
            }

            if button in action_map and action_map[button]:
                logger.debug(f"控制器操作: {action_map[button]}")

    def _handle_hand_tracking_mode(self, input_data: Dict):
        """处理手势追踪模式输入"""
        if input_data["type"] == VRInputType.HAND_GESTURE:
            gesture = input_data["gesture_type"]
            confidence = input_data["confidence"]

            # 手势到编辑器操作的映射
            gesture_actions = {
                "point": "select_element",
                "pinch": "grab_element",
                "swipe_right": "next_page",
                "swipe_left": "prev_page",
                "fist": "execute_action",
                "open_palm": "cancel_action",
            }

            if gesture in gesture_actions and confidence > 0.7:
                action = gesture_actions[gesture]
                logger.debug(f"手势操作: {action} (置信度: {confidence})")

    def _handle_gaze_mode(self, input_data: Dict):
        """处理注视选择模式输入"""
        if input_data["type"] == VRInputType.GAZE:
            duration = input_data["duration"]
            target = input_data["target"]

            # 长时间注视触发选择
            if duration > self.gesture_thresholds["hold_duration"]:
                logger.debug(f"注视选择: {target}")

    def _handle_voice_mode(self, input_data: Dict):
        """处理语音命令模式输入"""
        if input_data["type"] == VRInputType.VOICE:
            text = input_data["text"].lower()
            confidence = input_data["confidence"]

            # 语音命令映射
            voice_commands = {
                "save": "save_file",
                "undo": "undo_action",
                "redo": "redo_action",
                "next line": "move_cursor_down",
                "previous line": "move_cursor_up",
                "delete line": "delete_line",
            }

            # 匹配命令
            matched_command = None
            for command_phrase, action in voice_commands.items():
                if command_phrase in text and confidence > 0.6:
                    matched_command = action
                    break

            if matched_command:
                logger.debug(f"语音命令: {matched_command}")

    def set_interaction_mode(self, mode: VRInteractionMode):
        """设置交互模式"""
        self.interaction_mode = mode
        logger.info(f"交互模式已设置为: {mode}")

    def get_active_inputs(self) -> Dict:
        """获取当前活跃输入"""
        return self.active_inputs.copy()

    def update_gesture_thresholds(self, thresholds: Dict):
        """更新手势阈值"""
        self.gesture_thresholds.update(thresholds)
        logger.debug(f"手势阈值已更新: {thresholds}")
