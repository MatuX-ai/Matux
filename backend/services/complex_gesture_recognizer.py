from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging
import time
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class GestureType(Enum):
    """手势类型枚举"""

    UNKNOWN = "unknown"
    TAP = "tap"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PINCH_IN = "pinch_in"
    PINCH_OUT = "pinch_out"
    ROTATE_CLOCKWISE = "rotate_clockwise"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    CIRCLE = "circle"
    V_SHAPE = "v_shape"
    OK_SIGN = "ok_sign"
    THUMBS_UP = "thumbs_up"
    PALM_OPEN = "palm_open"
    FIST = "fist"
    # 特殊组合手势
    SECRET_GESTURE_1 = "secret_gesture_1"  # 隐藏任务手势1
    SECRET_GESTURE_2 = "secret_gesture_2"  # 隐藏任务手势2


@dataclass
class GesturePoint:
    """手势点数据"""

    x: float
    y: float
    z: float
    timestamp: float
    confidence: float


@dataclass
class RecognizedGesture:
    """识别的手势结果"""

    gesture_type: GestureType
    confidence: float
    duration: float
    points: List[GesturePoint]
    metadata: Dict[str, any]


class GestureRecognizer:
    """基础手势识别器"""

    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
        self.recognizers: Dict[GestureType, Callable] = {}
        self._register_basic_recognizers()

    def _register_basic_recognizers(self):
        """注册基础手势识别器"""
        self.recognizers[GestureType.TAP] = self._recognize_tap
        self.recognizers[GestureType.SWIPE_LEFT] = self._recognize_swipe_left
        self.recognizers[GestureType.SWIPE_RIGHT] = self._recognize_swipe_right
        self.recognizers[GestureType.SWIPE_UP] = self._recognize_swipe_up
        self.recognizers[GestureType.SWIPE_DOWN] = self._recognize_swipe_down
        self.recognizers[GestureType.PINCH_IN] = self._recognize_pinch_in
        self.recognizers[GestureType.PINCH_OUT] = self._recognize_pinch_out

    def recognize(self, points: List[GesturePoint]) -> Optional[RecognizedGesture]:
        """识别手势"""
        if len(points) < 2:
            return None

        best_match = None
        best_confidence = 0.0

        for gesture_type, recognizer_func in self.recognizers.items():
            try:
                confidence = recognizer_func(points)
                if confidence > best_confidence and confidence >= self.min_confidence:
                    best_confidence = confidence
                    best_match = RecognizedGesture(
                        gesture_type=gesture_type,
                        confidence=confidence,
                        duration=self._calculate_duration(points),
                        points=points,
                        metadata={},
                    )
            except Exception as e:
                logger.warning(f"手势识别失败 {gesture_type}: {e}")

        return best_match

    def _recognize_tap(self, points: List[GesturePoint]) -> float:
        """识别点击手势"""
        if len(points) > 5:  # 点击应该是短促的动作
            return 0.0

        # 检查点的移动距离是否很小
        total_distance = self._calculate_total_distance(points)
        if total_distance < 0.05:  # 5cm以内认为是点击
            return 0.9
        return 0.0

    def _recognize_swipe_left(self, points: List[GesturePoint]) -> float:
        """识别左滑手势"""
        if len(points) < 3:
            return 0.0

        start_x = points[0].x
        end_x = points[-1].x
        delta_x = start_x - end_x

        # 检查主要是水平移动且向左
        if delta_x > 0.1:  # 至少移动10cm
            vertical_movement = abs(points[-1].y - points[0].y)
            if vertical_movement < delta_x * 0.3:  # 垂直移动不超过水平移动的30%
                return min(0.95, delta_x / 0.2)  # 最大信心度0.95
        return 0.0

    def _recognize_swipe_right(self, points: List[GesturePoint]) -> float:
        """识别右滑手势"""
        if len(points) < 3:
            return 0.0

        start_x = points[0].x
        end_x = points[-1].x
        delta_x = end_x - start_x

        if delta_x > 0.1:
            vertical_movement = abs(points[-1].y - points[0].y)
            if vertical_movement < delta_x * 0.3:
                return min(0.95, delta_x / 0.2)
        return 0.0

    def _recognize_swipe_up(self, points: List[GesturePoint]) -> float:
        """识别上滑手势"""
        if len(points) < 3:
            return 0.0

        start_y = points[0].y
        end_y = points[-1].y
        delta_y = end_y - start_y

        if delta_y > 0.1:
            horizontal_movement = abs(points[-1].x - points[0].x)
            if horizontal_movement < delta_y * 0.3:
                return min(0.95, delta_y / 0.2)
        return 0.0

    def _recognize_swipe_down(self, points: List[GesturePoint]) -> float:
        """识别下滑手势"""
        if len(points) < 3:
            return 0.0

        start_y = points[0].y
        end_y = points[-1].y
        delta_y = start_y - end_y

        if delta_y > 0.1:
            horizontal_movement = abs(points[-1].x - points[0].x)
            if horizontal_movement < delta_y * 0.3:
                return min(0.95, delta_y / 0.2)
        return 0.0

    def _recognize_pinch_in(self, points: List[GesturePoint]) -> float:
        """识别捏合手势"""
        # 需要至少两个点序列来检测距离变化
        return 0.0  # 简化实现

    def _recognize_pinch_out(self, points: List[GesturePoint]) -> float:
        """识别展开手势"""
        return 0.0  # 简化实现

    def _calculate_total_distance(self, points: List[GesturePoint]) -> float:
        """计算总移动距离"""
        if len(points) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            dz = points[i].z - points[i - 1].z
            total_distance += np.sqrt(dx * dx + dy * dy + dz * dz)

        return total_distance

    def _calculate_duration(self, points: List[GesturePoint]) -> float:
        """计算手势持续时间"""
        if len(points) < 2:
            return 0.0
        return points[-1].timestamp - points[0].timestamp


class ComplexGestureSequenceRecognizer:
    """复杂手势序列识别器"""

    def __init__(self, buffer_size: int = 50):
        self.gesture_buffer = deque(maxlen=buffer_size)
        self.basic_recognizer = GestureRecognizer()
        self.sequence_patterns: Dict[str, List[GestureType]] = {}
        self._initialize_secret_gestures()
        self.min_sequence_confidence = 0.8

    def _initialize_secret_gestures(self):
        """初始化隐藏任务手势序列"""
        # 隐藏任务1: 圆形 + V字形 + 点击
        self.sequence_patterns["secret_task_1"] = [
            GestureType.CIRCLE,
            GestureType.V_SHAPE,
            GestureType.TAP,
        ]

        # 隐藏任务2: 左滑 + 右滑 + 上滑 + 下滑
        self.sequence_patterns["secret_task_2"] = [
            GestureType.SWIPE_LEFT,
            GestureType.SWIPE_RIGHT,
            GestureType.SWIPE_UP,
            GestureType.SWIPE_DOWN,
        ]

        # 隐藏任务3: 捏合 + 展开 + 旋转
        self.sequence_patterns["secret_task_3"] = [
            GestureType.PINCH_IN,
            GestureType.PINCH_OUT,
            GestureType.ROTATE_CLOCKWISE,
        ]

    def add_gesture_points(self, points: List[GesturePoint]):
        """添加手势点到缓冲区"""
        recognized = self.basic_recognizer.recognize(points)
        if recognized:
            self.gesture_buffer.append(recognized)
            logger.debug(
                f"识别到手势: {recognized.gesture_type.value}, 置信度: {recognized.confidence:.2f}"
            )

    def detect_complex_sequences(self) -> List[Tuple[str, float]]:
        """检测复杂手势序列"""
        detected_sequences = []

        if len(self.gesture_buffer) < 3:  # 至少需要3个手势
            return detected_sequences

        # 检查每个预定义的序列模式
        for sequence_name, pattern in self.sequence_patterns.items():
            confidence = self._match_sequence_pattern(pattern)
            if confidence >= self.min_sequence_confidence:
                detected_sequences.append((sequence_name, confidence))
                logger.info(
                    f"检测到复杂手势序列: {sequence_name}, 置信度: {confidence:.2f}"
                )

        return detected_sequences

    def _match_sequence_pattern(self, pattern: List[GestureType]) -> float:
        """匹配手势序列模式"""
        if len(self.gesture_buffer) < len(pattern):
            return 0.0

        # 在缓冲区中寻找匹配的连续手势序列
        best_match_score = 0.0

        # 滑动窗口匹配
        for start_idx in range(len(self.gesture_buffer) - len(pattern) + 1):
            window_score = self._score_window_match(start_idx, pattern)
            best_match_score = max(best_match_score, window_score)

        return best_match_score

    def _score_window_match(self, start_idx: int, pattern: List[GestureType]) -> float:
        """评分窗口匹配度"""
        total_score = 0.0
        matched_count = 0

        for i, gesture_type in enumerate(pattern):
            buffer_index = start_idx + i
            if buffer_index >= len(self.gesture_buffer):
                break

            recognized_gesture = self.gesture_buffer[buffer_index]
            if recognized_gesture.gesture_type == gesture_type:
                # 时间连续性加分
                time_penalty = 0.0
                if i > 0 and buffer_index > 0:
                    time_gap = (
                        self.gesture_buffer[buffer_index].points[0].timestamp
                        - self.gesture_buffer[buffer_index - 1].points[-1].timestamp
                    )
                    time_penalty = max(0.0, (time_gap - 2.0) / 5.0)  # 超过2秒开始扣分

                gesture_score = recognized_gesture.confidence * (1.0 - time_penalty)
                total_score += gesture_score
                matched_count += 1

        if matched_count == 0:
            return 0.0

        # 计算平均分数并考虑完整性
        average_score = total_score / len(pattern)
        completeness_bonus = matched_count / len(pattern)

        return average_score * completeness_bonus

    def clear_buffer(self):
        """清空手势缓冲区"""
        self.gesture_buffer.clear()

    def get_buffer_status(self) -> Dict[str, any]:
        """获取缓冲区状态"""
        return {
            "buffer_size": len(self.gesture_buffer),
            "buffer_capacity": self.gesture_buffer.maxlen,
            "recent_gestures": [
                {
                    "type": g.gesture_type.value,
                    "confidence": g.confidence,
                    "duration": g.duration,
                }
                for g in list(self.gesture_buffer)[-5:]  # 最近5个手势
            ],
        }


# 全局实例
complex_gesture_recognizer = ComplexGestureSequenceRecognizer()
