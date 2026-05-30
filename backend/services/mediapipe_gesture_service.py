from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

from .complex_gesture_recognizer import (
    GesturePoint,
    GestureType,
    RecognizedGesture,
    complex_gesture_recognizer,
)

logger = logging.getLogger(__name__)


class HandLandmark(Enum):
    """手部关键点枚举"""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


@dataclass
class HandLandmarks:
    """手部关键点数据"""

    landmarks: List[Tuple[float, float, float]]  # x, y, z coordinates
    handedness: str  # "Left" or "Right"
    confidence: float


class MediaPipeGestureRecognizer:
    """MediaPipe手势识别器"""

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
    ):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        # 初始化MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # 手势识别配置
        self.gesture_history = []
        self.max_history_length = 30
        self.recognition_threshold = 0.8

    def process_frame(self, frame: np.ndarray) -> Dict[str, any]:
        """处理视频帧，识别手势"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        hand_landmarks_list = []
        recognized_gestures = []

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                # 提取手部关键点
                landmarks = self._extract_landmarks(hand_landmarks)
                hand_data = HandLandmarks(
                    landmarks=landmarks,
                    handedness=handedness.classification[0].label,
                    confidence=handedness.classification[0].score,
                )
                hand_landmarks_list.append(hand_data)

                # 识别手势
                gesture = self._recognize_hand_gesture(hand_data)
                if gesture:
                    recognized_gestures.append(gesture)

                # 转换为手势点序列用于复杂手势识别
                gesture_points = self._convert_to_gesture_points(landmarks)
                complex_gesture_recognizer.add_gesture_points(gesture_points)

        # 检测复杂手势序列
        complex_sequences = complex_gesture_recognizer.detect_complex_sequences()

        return {
            "hand_landmarks": hand_landmarks_list,
            "recognized_gestures": recognized_gestures,
            "complex_sequences": complex_sequences,
            "frame_processed": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _extract_landmarks(self, hand_landmarks) -> List[Tuple[float, float, float]]:
        """提取手部关键点坐标"""
        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.append((landmark.x, landmark.y, landmark.z))
        return landmarks

    def _recognize_hand_gesture(
        self, hand_data: HandLandmarks
    ) -> Optional[RecognizedGesture]:
        """识别单手手势"""
        landmarks = hand_data.landmarks

        # 检查各种手势
        gestures = []

        # V字手势
        if self._is_v_shape(landmarks):
            gestures.append((GestureType.V_SHAPE, 0.9))

        # OK手势
        elif self._is_ok_sign(landmarks):
            gestures.append((GestureType.OK_SIGN, 0.85))

        # 竖大拇指
        elif self._is_thumbs_up(landmarks):
            gestures.append((GestureType.THUMBS_UP, 0.8))

        # 手掌张开
        elif self._is_palm_open(landmarks):
            gestures.append((GestureType.PALM_OPEN, 0.75))

        # 握拳
        elif self._is_fist(landmarks):
            gestures.append((GestureType.FIST, 0.8))

        # 圆形手势
        elif self._is_circle(landmarks):
            gestures.append((GestureType.CIRCLE, 0.7))

        if gestures:
            # 选择置信度最高的手势
            best_gesture, confidence = max(gestures, key=lambda x: x[1])
            return RecognizedGesture(
                gesture_type=best_gesture,
                confidence=confidence * hand_data.confidence,
                duration=0.0,  # 单帧识别，无持续时间
                points=[],  # MediaPipe手势不使用点序列
                metadata={
                    "handedness": hand_data.handedness,
                    "hand_confidence": hand_data.confidence,
                },
            )

        return None

    def _is_v_shape(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为V字手势"""
        try:
            index_tip = landmarks[HandLandmark.INDEX_FINGER_TIP.value]
            index_mcp = landmarks[HandLandmark.INDEX_FINGER_MCP.value]
            middle_tip = landmarks[HandLandmark.MIDDLE_FINGER_TIP.value]
            middle_mcp = landmarks[HandLandmark.MIDDLE_FINGER_MCP.value]
            ring_tip = landmarks[HandLandmark.RING_FINGER_TIP.value]
            pinky_tip = landmarks[HandLandmark.PINKY_TIP.value]

            # 食指和中指伸直
            index_extended = index_tip[1] < index_mcp[1] - 0.1
            middle_extended = middle_tip[1] < middle_mcp[1] - 0.1

            # 无名指和小指弯曲
            ring_curled = (
                ring_tip[1] > landmarks[HandLandmark.RING_FINGER_MCP.value][1] - 0.05
            )
            pinky_curled = (
                pinky_tip[1] > landmarks[HandLandmark.PINKY_MCP.value][1] - 0.05
            )

            return index_extended and middle_extended and ring_curled and pinky_curled
        except IndexError:
            return False

    def _is_ok_sign(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为OK手势"""
        try:
            thumb_tip = landmarks[HandLandmark.THUMB_TIP.value]
            index_tip = landmarks[HandLandmark.INDEX_FINGER_TIP.value]

            # 拇指和食指指尖接近形成圆形
            distance = np.sqrt(
                (thumb_tip[0] - index_tip[0]) ** 2
                + (thumb_tip[1] - index_tip[1]) ** 2
                + (thumb_tip[2] - index_tip[2]) ** 2
            )

            return distance < 0.1
        except IndexError:
            return False

    def _is_thumbs_up(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为竖大拇指"""
        try:
            thumb_tip = landmarks[HandLandmark.THUMB_TIP.value]
            thumb_mcp = landmarks[HandLandmark.THUMB_MCP.value]
            index_tip = landmarks[HandLandmark.INDEX_FINGER_TIP.value]
            middle_tip = landmarks[HandLandmark.MIDDLE_FINGER_TIP.value]

            # 拇指向上伸直
            thumb_up = thumb_tip[1] < thumb_mcp[1] - 0.1

            # 其他手指弯曲
            index_curled = (
                index_tip[1] > landmarks[HandLandmark.INDEX_FINGER_MCP.value][1] - 0.05
            )
            middle_curled = (
                middle_tip[1]
                > landmarks[HandLandmark.MIDDLE_FINGER_MCP.value][1] - 0.05
            )

            return thumb_up and index_curled and middle_curled
        except IndexError:
            return False

    def _is_palm_open(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为手掌张开"""
        try:
            # 检查所有手指是否伸直
            fingers_extended = []

            for finger_base, finger_tip in [
                (HandLandmark.INDEX_FINGER_MCP, HandLandmark.INDEX_FINGER_TIP),
                (HandLandmark.MIDDLE_FINGER_MCP, HandLandmark.MIDDLE_FINGER_TIP),
                (HandLandmark.RING_FINGER_MCP, HandLandmark.RING_FINGER_TIP),
                (HandLandmark.PINKY_MCP, HandLandmark.PINKY_TIP),
            ]:
                base_y = landmarks[finger_base.value][1]
                tip_y = landmarks[finger_tip.value][1]
                fingers_extended.append(tip_y < base_y - 0.1)

            return all(fingers_extended)
        except IndexError:
            return False

    def _is_fist(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为握拳"""
        try:
            # 检查手指是否弯曲
            fingers_curled = []

            for finger_base, finger_tip in [
                (HandLandmark.INDEX_FINGER_MCP, HandLandmark.INDEX_FINGER_TIP),
                (HandLandmark.MIDDLE_FINGER_MCP, HandLandmark.MIDDLE_FINGER_TIP),
                (HandLandmark.RING_FINGER_MCP, HandLandmark.RING_FINGER_TIP),
                (HandLandmark.PINKY_MCP, HandLandmark.PINKY_TIP),
            ]:
                base_y = landmarks[finger_base.value][1]
                tip_y = landmarks[finger_tip.value][1]
                fingers_curled.append(tip_y > base_y - 0.05)

            return all(fingers_curled)
        except IndexError:
            return False

    def _is_circle(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        """判断是否为圆形手势"""
        try:
            thumb_tip = landmarks[HandLandmark.THUMB_TIP.value]
            index_tip = landmarks[HandLandmark.INDEX_FINGER_TIP.value]
            middle_tip = landmarks[HandLandmark.MIDDLE_FINGER_TIP.value]

            # 拇指和食指接近
            thumb_index_dist = np.sqrt(
                (thumb_tip[0] - index_tip[0]) ** 2 + (thumb_tip[1] - index_tip[1]) ** 2
            )

            # 中指伸直作为参考
            middle_extended = (
                middle_tip[1] < landmarks[HandLandmark.MIDDLE_FINGER_MCP.value][1] - 0.1
            )

            return thumb_index_dist < 0.1 and middle_extended
        except IndexError:
            return False

    def _convert_to_gesture_points(
        self, landmarks: List[Tuple[float, float, float]]
    ) -> List[GesturePoint]:
        """将手部关键点转换为手势点序列"""
        points = []
        timestamp = datetime.now().timestamp()

        # 使用几个主要关键点作为手势轨迹点
        key_points = [
            HandLandmark.WRIST,
            HandLandmark.INDEX_FINGER_TIP,
            HandLandmark.MIDDLE_FINGER_TIP,
            HandLandmark.THUMB_TIP,
        ]

        for i, point_enum in enumerate(key_points):
            try:
                x, y, z = landmarks[point_enum.value]
                points.append(
                    GesturePoint(
                        x=float(x),
                        y=float(y),
                        z=float(z),
                        timestamp=timestamp + i * 0.01,  # 微小时间差
                        confidence=0.8,  # 假设的置信度
                    )
                )
            except IndexError:
                continue

        return points

    def draw_landmarks(self, frame: np.ndarray, results) -> np.ndarray:
        """在图像上绘制手部关键点"""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )
        return frame

    def get_gesture_statistics(self) -> Dict[str, any]:
        """获取手势识别统计信息"""
        return {
            "buffer_status": complex_gesture_recognizer.get_buffer_status(),
            "supported_gestures": [gt.value for gt in GestureType],
            "recognition_threshold": self.recognition_threshold,
        }

    def close(self):
        """释放资源"""
        if self.hands:
            self.hands.close()


# 全局实例
mediapipe_gesture_recognizer = MediaPipeGestureRecognizer()
