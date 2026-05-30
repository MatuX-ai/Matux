"""
手部追踪器
使用MediaPipe Hands进行实时手部关键点检测
"""

from datetime import datetime
import logging
from typing import List

import cv2
import mediapipe as mp
import numpy as np

from .models import HandDetectionResult, HandLandmark, HandSide

logger = logging.getLogger(__name__)


class HandTracker:
    """手部追踪器类"""

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
        static_image_mode: bool = False,
    ):
        """
        初始化手部追踪器

        Args:
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小追踪置信度
            static_image_mode: 是否静态图像模式
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.static_image_mode = static_image_mode

        # 初始化MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # 创建Hands实例
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=2,  # 最多检测两只手
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

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

        logger.info("HandTracker初始化完成")

    def detect_hands(self, image: np.ndarray) -> List[HandDetectionResult]:
        """
        检测图像中的手部

        Args:
            image: 输入图像(BGR格式)

        Returns:
            List[HandDetectionResult]: 检测到的手部结果列表
        """
        try:
            # 转换为RGB格式
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # 处理图像
            results = self.hands.process(rgb_image)

            hand_results = []

            if results.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks, results.multi_handedness
                ):
                    # 确定手部方向
                    hand_side = self._determine_hand_side(
                        handedness.classification[0].label
                    )

                    # 提取关键点
                    landmarks = self._extract_landmarks(
                        hand_landmarks, image.shape[1], image.shape[0]
                    )

                    # 计算边界框
                    bounding_box = self._calculate_bounding_box(
                        landmarks, image.shape[1], image.shape[0]
                    )

                    # 获取置信度
                    confidence = handedness.classification[0].score

                    # 创建检测结果
                    detection_result = HandDetectionResult(
                        hand_side=hand_side,
                        landmarks=landmarks,
                        confidence=confidence,
                        bounding_box=bounding_box,
                        timestamp=datetime.utcnow(),
                    )

                    hand_results.append(detection_result)

            return hand_results

        except Exception as e:
            logger.error(f"手部检测失败: {e}")
            return []

    def _determine_hand_side(self, handedness_label: str) -> HandSide:
        """
        确定手部方向

        Args:
            handedness_label: MediaPipe返回的手部标签

        Returns:
            HandSide: 手部方向枚举
        """
        # 注意：MediaPipe的左右手判断可能需要根据摄像头方向调整
        if handedness_label.lower() == "left":
            return HandSide.RIGHT  # 镜像翻转
        else:
            return HandSide.LEFT

    def _extract_landmarks(
        self, hand_landmarks, image_width: int, image_height: int
    ) -> List[HandLandmark]:
        """
        提取手部关键点坐标

        Args:
            hand_landmarks: MediaPipe手部关键点
            image_width: 图像宽度
            image_height: 图像高度

        Returns:
            List[HandLandmark]: 关键点列表
        """
        landmarks = []

        for landmark in hand_landmarks.landmark:
            # 转换为像素坐标并归一化
            x_norm = landmark.x
            y_norm = landmark.y
            z_norm = landmark.z

            landmarks.append(
                HandLandmark(
                    x=x_norm,
                    y=y_norm,
                    z=z_norm,
                    visibility=(
                        landmark.visibility if hasattr(landmark, "visibility") else 1.0
                    ),
                )
            )

        return landmarks

    def _calculate_bounding_box(
        self, landmarks: List[HandLandmark], image_width: int, image_height: int
    ) -> dict:
        """
        计算手部边界框

        Args:
            landmarks: 手部关键点列表
            image_width: 图像宽度
            image_height: 图像高度

        Returns:
            dict: 边界框信息 {'x': float, 'y': float, 'width': float, 'height': float}
        """
        if not landmarks:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        # 获取所有关键点的坐标
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]

        # 计算边界框
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # 添加一些边距
        margin = 0.05
        width = (x_max - x_min) + 2 * margin
        height = (y_max - y_min) + 2 * margin

        # 确保边界框不超出图像范围
        x_min = max(0, x_min - margin)
        y_min = max(0, y_min - margin)
        width = min(1.0 - x_min, width)
        height = min(1.0 - y_min, height)

        return {"x": x_min, "y": y_min, "width": width, "height": height}

    def draw_landmarks(
        self, image: np.ndarray, hand_results: List[HandDetectionResult]
    ) -> np.ndarray:
        """
        在图像上绘制手部关键点

        Args:
            image: 输入图像
            hand_results: 手部检测结果

        Returns:
            np.ndarray: 绘制了关键点的图像
        """
        # 转换为RGB用于MediaPipe绘制
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 创建空白图像用于绘制
        annotated_image = rgb_image.copy()

        # 重新处理以获取原始landmarks对象
        results = self.hands.process(rgb_image)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制手部连接线
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )

        # 转换回BGR
        return cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    def get_finger_states(self, landmarks: List[HandLandmark]) -> dict:
        """
        判断手指的弯曲状态

        Args:
            landmarks: 手部关键点列表

        Returns:
            dict: 各手指状态 {'thumb': bool, 'index': bool, 'middle': bool, 'ring': bool, 'pinky': bool}
                  True表示伸直，False表示弯曲
        """
        if len(landmarks) < 21:
            return {}

        finger_states = {}

        # 拇指状态（基于拇指尖和拇指基部的相对位置）
        thumb_tip = landmarks[self.HAND_LANDMARKS["THUMB_TIP"]]
        landmarks[self.HAND_LANDMARKS["THUMB_MCP"]]
        thumb_cmc = landmarks[self.HAND_LANDMARKS["THUMB_CMC"]]

        # 简单的拇指判断逻辑
        thumb_extended = (
            thumb_tip.x > thumb_cmc.x
            if thumb_tip.x > 0.5
            else thumb_tip.x < thumb_cmc.x
        )
        finger_states["thumb"] = thumb_extended

        # 其他手指状态（基于指尖和中间关节的相对位置）
        fingers = [
            ("index", "INDEX_FINGER_TIP", "INDEX_FINGER_PIP"),
            ("middle", "MIDDLE_FINGER_TIP", "MIDDLE_FINGER_PIP"),
            ("ring", "RING_FINGER_TIP", "RING_FINGER_PIP"),
            ("pinky", "PINKY_TIP", "PINKY_PIP"),
        ]

        for finger_name, tip_name, pip_name in fingers:
            tip = landmarks[self.HAND_LANDMARKS[tip_name]]
            pip = landmarks[self.HAND_LANDMARKS[pip_name]]

            # 判断手指是否伸直
            finger_states[finger_name] = tip.y < pip.y

        return finger_states

    def close(self):
        """释放资源"""
        if self.hands:
            self.hands.close()
        logger.info("HandTracker资源已释放")
