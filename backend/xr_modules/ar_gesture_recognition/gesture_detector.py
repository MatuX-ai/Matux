"""
手势检测器
基于手部关键点识别各种手势
"""

from datetime import datetime
import logging
import math
from typing import List

from .models import (
    GestureRecognitionResult,
    GestureType,
    HandDetectionResult,
    HandLandmark,
)

logger = logging.getLogger(__name__)


class GestureDetector:
    """手势检测器类"""

    def __init__(self):
        """初始化手势检测器"""
        # 手部关键点索引映射
        self.HAND_LANDMARKS = {
            "WRIST": 0,
            "THUMB_CMC": 1,
            "THUMB_MCP": 2,
            "THUMB_IP": 3,
            "THUMB_TIP": 4,
            "INDEX_FINGER_MCP": 5,
            "INDEX_FINGER_PIP": 6,
            "INDEX_FINGER_DIP": 7,
            "INDEX_FINGER_TIP": 8,
            "MIDDLE_FINGER_MCP": 9,
            "MIDDLE_FINGER_PIP": 10,
            "MIDDLE_FINGER_DIP": 11,
            "MIDDLE_FINGER_TIP": 12,
            "RING_FINGER_MCP": 13,
            "RING_FINGER_PIP": 14,
            "RING_FINGER_DIP": 15,
            "RING_FINGER_TIP": 16,
            "PINKY_MCP": 17,
            "PINKY_PIP": 18,
            "PINKY_DIP": 19,
            "PINKY_TIP": 20,
        }

        logger.info("GestureDetector初始化完成")

    def recognize_gesture(
        self, hand_detection: HandDetectionResult, frame_number: int
    ) -> GestureRecognitionResult:
        """
        识别手势

        Args:
            hand_detection: 手部检测结果
            frame_number: 帧编号

        Returns:
            GestureRecognitionResult: 手势识别结果
        """
        try:
            landmarks = hand_detection.landmarks
            if len(landmarks) < 21:
                # 关键点不足，无法识别
                return GestureRecognitionResult(
                    gesture_type=GestureType.UNKNOWN,
                    confidence=0.0,
                    hand_side=hand_detection.hand_side,
                    hand_detection=hand_detection,
                    recognition_time=datetime.utcnow(),
                    frame_number=frame_number,
                )

            # 识别具体手势
            gesture_type, confidence = self._identify_gesture(landmarks)

            return GestureRecognitionResult(
                gesture_type=gesture_type,
                confidence=confidence,
                hand_side=hand_detection.hand_side,
                hand_detection=hand_detection,
                recognition_time=datetime.utcnow(),
                frame_number=frame_number,
            )

        except Exception as e:
            logger.error(f"手势识别失败: {e}")
            return GestureRecognitionResult(
                gesture_type=GestureType.UNKNOWN,
                confidence=0.0,
                hand_side=hand_detection.hand_side,
                hand_detection=hand_detection,
                recognition_time=datetime.utcnow(),
                frame_number=frame_number,
            )

    def _identify_gesture(self, landmarks: List[HandLandmark]) -> tuple:
        """
        识别具体的手势类型

        Args:
            landmarks: 手部关键点列表

        Returns:
            tuple: (GestureType, confidence)
        """
        # 获取手指状态
        finger_states = self._get_finger_states(landmarks)

        # 计算手部几何特征
        features = self._calculate_hand_features(landmarks)

        # 识别各种手势
        gestures = [
            self._recognize_circle(landmarks, features),
            self._recognize_swipe(landmarks, features),
            self._recognize_pinch(landmarks, features),
            self._recognize_fist(finger_states),
            self._recognize_palm(finger_states),
            self._recognize_thumb_up(landmarks, finger_states),
            self._recognize_thumb_down(landmarks, finger_states),
            self._recognize_victory(finger_states),
            self._recognize_point(landmarks, finger_states),
            self._recognize_ok_sign(landmarks),
            self._recognize_rock_on(finger_states),
            self._recognize_spiderman(finger_states),
        ]

        # 返回置信度最高的手势
        best_gesture = max(gestures, key=lambda x: x[1])
        return best_gesture

    def _get_finger_states(self, landmarks: List[HandLandmark]) -> dict:
        """获取手指弯曲状态"""
        if len(landmarks) < 21:
            return {}

        finger_states = {}

        # 拇指状态
        thumb_tip = landmarks[self.HAND_LANDMARKS["THUMB_TIP"]]
        landmarks[self.HAND_LANDMARKS["THUMB_MCP"]]
        thumb_cmc = landmarks[self.HAND_LANDMARKS["THUMB_CMC"]]

        # 拇指是否伸直（简化判断）
        thumb_extended = abs(thumb_tip.x - thumb_cmc.x) > 0.1
        finger_states["thumb"] = thumb_extended

        # 其他手指
        fingers = [
            ("index", "INDEX_FINGER_TIP", "INDEX_FINGER_MCP"),
            ("middle", "MIDDLE_FINGER_TIP", "MIDDLE_FINGER_MCP"),
            ("ring", "RING_FINGER_TIP", "RING_FINGER_MCP"),
            ("pinky", "PINKY_TIP", "PINKY_MCP"),
        ]

        for finger_name, tip_name, mcp_name in fingers:
            tip = landmarks[self.HAND_LANDMARKS[tip_name]]
            mcp = landmarks[self.HAND_LANDMARKS[mcp_name]]

            # 手指是否伸直（指尖在MCP关节上方）
            finger_states[finger_name] = tip.y < mcp.y - 0.05

        return finger_states

    def _calculate_hand_features(self, landmarks: List[HandLandmark]) -> dict:
        """计算手部几何特征"""
        features = {}

        if len(landmarks) < 21:
            return features

        # 计算关键距离
        landmarks[self.HAND_LANDMARKS["WRIST"]]
        index_tip = landmarks[self.HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        thumb_tip = landmarks[self.HAND_LANDMARKS["THUMB_TIP"]]
        middle_tip = landmarks[self.HAND_LANDMARKS["MIDDLE_FINGER_TIP"]]

        # 指尖距离
        features["index_thumb_distance"] = self._calculate_distance(
            index_tip, thumb_tip
        )
        features["index_middle_distance"] = self._calculate_distance(
            index_tip, middle_tip
        )

        # 手掌大小（拇指到小指根部的距离）
        pinky_mcp = landmarks[self.HAND_LANDMARKS["PINKY_MCP"]]
        features["palm_size"] = self._calculate_distance(thumb_tip, pinky_mcp)

        # 手部角度
        features["hand_angle"] = self._calculate_hand_angle(landmarks)

        return features

    def _calculate_distance(self, point1: HandLandmark, point2: HandLandmark) -> float:
        """计算两点间欧几里得距离"""
        return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

    def _calculate_hand_angle(self, landmarks: List[HandLandmark]) -> float:
        """计算手部倾斜角度"""
        wrist = landmarks[self.HAND_LANDMARKS["WRIST"]]
        middle_mcp = landmarks[self.HAND_LANDMARKS["MIDDLE_FINGER_MCP"]]

        # 计算相对于垂直方向的角度
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y

        if dy != 0:
            angle = math.atan2(dx, dy) * 180 / math.pi
        else:
            angle = 90 if dx > 0 else -90

        return angle

    def _recognize_circle(self, landmarks: List[HandLandmark], features: dict) -> tuple:
        """识别画圆手势"""
        # 检查是否形成近似圆形轨迹（简化实现）
        # 这里需要更复杂的时间序列分析来真正检测画圆动作
        # 当前实现基于静态姿态的近似判断

        finger_states = self._get_finger_states(landmarks)

        # 食指伸直，其他手指弯曲，拇指与其他指尖接近
        if (
            finger_states.get("index", False)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
            and features.get("index_thumb_distance", 0) < 0.15
        ):

            return (GestureType.CIRCLE, 0.7)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_swipe(self, landmarks: List[HandLandmark], features: dict) -> tuple:
        """识别滑动手势"""
        # 基于手部角度判断滑动方向
        angle = features.get("hand_angle", 0)

        # 简化判断：主要基于手部倾斜角度
        if abs(angle) > 45:  # 足够倾斜
            if angle > 0:
                return (GestureType.SWIPE_RIGHT, 0.6)
            else:
                return (GestureType.SWIPE_LEFT, 0.6)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_pinch(self, landmarks: List[HandLandmark], features: dict) -> tuple:
        """识别捏合手势"""
        distance = features.get("index_thumb_distance", float("inf"))
        palm_size = features.get("palm_size", 1.0)

        # 归一化距离
        normalized_distance = distance / palm_size if palm_size > 0 else float("inf")

        if normalized_distance < 0.3:  # 捏合
            return (GestureType.PINCH_IN, 0.8)
        elif normalized_distance > 0.6:  # 展开
            return (GestureType.PINCH_OUT, 0.8)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_fist(self, finger_states: dict) -> tuple:
        """识别握拳手势"""
        # 所有手指弯曲
        if (
            not finger_states.get("thumb", True)  # 拇指可以稍微伸出
            and not finger_states.get("index", False)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
        ):

            return (GestureType.FIST, 0.9)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_palm(self, finger_states: dict) -> tuple:
        """识别手掌手势"""
        # 所有手指伸直
        if (
            finger_states.get("thumb", True)
            and finger_states.get("index", True)
            and finger_states.get("middle", True)
            and finger_states.get("ring", True)
            and finger_states.get("pinky", True)
        ):

            return (GestureType.PALM, 0.8)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_thumb_up(
        self, landmarks: List[HandLandmark], finger_states: dict
    ) -> tuple:
        """识别竖拇指手势"""
        # 拇指伸直且向上，其他手指弯曲
        thumb_extended = finger_states.get("thumb", False)
        thumb_tip = landmarks[self.HAND_LANDMARKS["THUMB_TIP"]]
        wrist = landmarks[self.HAND_LANDMARKS["WRIST"]]

        # 拇指在手腕上方
        thumb_up = thumb_tip.y < wrist.y - 0.1

        if (
            thumb_extended
            and thumb_up
            and not finger_states.get("index", False)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
        ):

            return (GestureType.THUMB_UP, 0.85)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_thumb_down(
        self, landmarks: List[HandLandmark], finger_states: dict
    ) -> tuple:
        """识别竖食指手势"""
        # 食指伸直且向下，其他手指弯曲
        index_extended = finger_states.get("index", False)
        index_tip = landmarks[self.HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        wrist = landmarks[self.HAND_LANDMARKS["WRIST"]]

        # 食指在手腕下方
        index_down = index_tip.y > wrist.y + 0.1

        if (
            index_extended
            and index_down
            and not finger_states.get("thumb", False)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
        ):

            return (GestureType.THUMB_DOWN, 0.8)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_victory(self, finger_states: dict) -> tuple:
        """识别胜利手势"""
        # 食指和中指伸直，其他手指弯曲
        if (
            finger_states.get("index", True)
            and finger_states.get("middle", True)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
            and not finger_states.get("thumb", False)
        ):

            return (GestureType.VICTORY, 0.85)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_point(
        self, landmarks: List[HandLandmark], finger_states: dict
    ) -> tuple:
        """识别指向手势"""
        # 食指伸直，其他手指弯曲
        if (
            finger_states.get("index", True)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
            and not finger_states.get("pinky", False)
            and not finger_states.get("thumb", False)
        ):

            return (GestureType.POINT, 0.75)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_ok_sign(self, landmarks: List[HandLandmark]) -> tuple:
        """识别OK手势"""
        if len(landmarks) < 21:
            return (GestureType.UNKNOWN, 0.0)

        # 拇指和食指形成圆形
        thumb_tip = landmarks[self.HAND_LANDMARKS["THUMB_TIP"]]
        index_tip = landmarks[self.HAND_LANDMARKS["INDEX_FINGER_TIP"]]
        distance = self._calculate_distance(thumb_tip, index_tip)

        if distance < 0.1:  # 拇指和食指很接近
            return (GestureType.OK_SIGN, 0.7)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_rock_on(self, finger_states: dict) -> tuple:
        """识别摇滚手势"""
        # 食指和小指伸直，拇指伸出，中指和无名指弯曲
        if (
            finger_states.get("index", True)
            and finger_states.get("pinky", True)
            and finger_states.get("thumb", True)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
        ):

            return (GestureType.ROCK_ON, 0.8)

        return (GestureType.UNKNOWN, 0.0)

    def _recognize_spiderman(self, finger_states: dict) -> tuple:
        """识别蜘蛛侠手势"""
        # 拇指和小指伸直，其他手指弯曲
        if (
            finger_states.get("thumb", True)
            and finger_states.get("pinky", True)
            and not finger_states.get("index", False)
            and not finger_states.get("middle", False)
            and not finger_states.get("ring", False)
        ):

            return (GestureType.SPIDERMAN, 0.8)

        return (GestureType.UNKNOWN, 0.0)
