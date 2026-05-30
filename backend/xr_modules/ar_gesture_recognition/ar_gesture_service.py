"""
AR手势识别服务
整合所有组件提供完整的手势识别功能
"""

from datetime import datetime
import logging
from typing import Callable, Dict, List, Optional
import uuid

import cv2
import numpy as np

from .gesture_detector import GestureDetector
from .gesture_mapper import GestureMapper
from .gesture_processor import GestureProcessor
from .hand_tracker import HandTracker
from .models import ARGestureConfig, GestureEvent, GestureSessionInfo

logger = logging.getLogger(__name__)


class ARGestureService:
    """AR手势识别服务主类"""

    def __init__(self, config: Optional[ARGestureConfig] = None):
        """
        初始化AR手势识别服务

        Args:
            config: 手势识别配置，如果为None则使用默认配置
        """
        self.config = config or ARGestureConfig()

        # 初始化各个组件
        self.hand_tracker = HandTracker(
            min_detection_confidence=self.config.min_detection_confidence,
            min_tracking_confidence=self.config.min_tracking_confidence,
        )

        self.gesture_detector = GestureDetector()
        self.gesture_processor = GestureProcessor(self.config)
        self.gesture_mapper = GestureMapper(self.config)

        # 会话管理
        self.current_session: Optional[GestureSessionInfo] = None
        self.is_running = False
        self.frame_count = 0

        # 回调函数
        self.gesture_callback: Optional[Callable[[GestureEvent, str], None]] = None
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None

        logger.info("ARGestureService初始化完成")

    def start_session(
        self, user_id: Optional[int] = None, device_id: str = "default_device"
    ) -> str:
        """
        开始新的手势识别会话

        Args:
            user_id: 用户ID
            device_id: 设备ID

        Returns:
            str: 会话ID
        """
        if self.current_session and self.current_session.is_active:
            self.stop_session()

        session_id = str(uuid.uuid4())
        self.current_session = GestureSessionInfo(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            start_time=datetime.utcnow(),
            config=self.config,
        )

        self.is_running = True
        self.frame_count = 0

        logger.info(f"手势识别会话开始: {session_id}")
        return session_id

    def stop_session(self):
        """停止当前会话"""
        if self.current_session:
            self.current_session.is_active = False
            self.current_session.end_time = datetime.utcnow()
            self.current_session.statistics.end_time = datetime.utcnow()
            self.current_session.statistics.session_duration = (
                self.current_session.end_time - self.current_session.start_time
            ).total_seconds()

            logger.info(f"手势识别会话结束: {self.current_session.session_id}")

        self.is_running = False
        self.current_session = None

    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        处理视频帧进行手势识别

        Args:
            frame: 输入视频帧(BGR格式)

        Returns:
            Optional[np.ndarray]: 处理后的帧（如果启用了绘制），否则返回None
        """
        if not self.is_running or not self.current_session:
            return frame

        try:
            self.frame_count += 1

            # 图像预处理
            processed_frame = self._preprocess_frame(frame)

            # 手部检测
            hand_detections = self.hand_tracker.detect_hands(processed_frame)

            # 处理每个检测到的手
            for hand_detection in hand_detections:
                # 手势识别
                gesture_result = self.gesture_detector.recognize_gesture(
                    hand_detection, self.frame_count
                )

                # 手势处理
                gesture_event = self.gesture_processor.process_gesture(
                    gesture_result,
                    self.current_session.user_id,
                    self.current_session.session_id,
                    self.current_session.device_id,
                )

                if gesture_event:
                    # 手势映射
                    command = self.gesture_mapper.map_gesture_to_command(gesture_event)
                    gesture_event.mapped_command = command

                    # 更新统计信息
                    self._update_statistics(gesture_event)

                    # 触发回调
                    if self.gesture_callback:
                        try:
                            self.gesture_callback(gesture_event, command)
                        except Exception as e:
                            logger.error(f"手势回调执行失败: {e}")

                    logger.info(f"手势识别: {gesture_result.gesture_type} -> {command}")

            # 绘制关键点（如果启用）
            if self.config.enable_gesture_smoothing:
                annotated_frame = self.hand_tracker.draw_landmarks(
                    processed_frame, hand_detections
                )

                # 触发帧回调
                if self.frame_callback:
                    try:
                        self.frame_callback(annotated_frame)
                    except Exception as e:
                        logger.error(f"帧回调执行失败: {e}")

                return annotated_frame

            return processed_frame

        except Exception as e:
            logger.error(f"帧处理失败: {e}")
            return frame

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        图像预处理

        Args:
            frame: 输入帧

        Returns:
            np.ndarray: 预处理后的帧
        """
        # 调整图像大小
        if (
            frame.shape[1] != self.config.image_width
            or frame.shape[0] != self.config.image_height
        ):
            frame = cv2.resize(
                frame, (self.config.image_width, self.config.image_height)
            )

        # 水平翻转（镜像效果）
        if self.config.flip_horizontal:
            frame = cv2.flip(frame, 1)

        # 垂直翻转
        if self.config.flip_vertical:
            frame = cv2.flip(frame, 0)

        return frame

    def _update_statistics(self, gesture_event: GestureEvent):
        """更新会话统计信息"""
        if not self.current_session:
            return

        stats = self.current_session.statistics

        # 更新总计数
        stats.total_gestures += 1

        # 更新手势计数
        gesture_type = gesture_event.gesture_result.gesture_type
        if gesture_type not in stats.gesture_counts:
            stats.gesture_counts[gesture_type] = 0
        stats.gesture_counts[gesture_type] += 1

        # 更新置信度统计
        confidence = gesture_event.gesture_result.confidence
        stats.average_confidence = (
            stats.average_confidence * (stats.total_gestures - 1) + confidence
        ) / stats.total_gestures

        # 更新最常用手势
        if stats.gesture_counts:
            stats.most_used_gesture = max(
                stats.gesture_counts.keys(), key=lambda x: stats.gesture_counts[x]
            )

    def set_gesture_callback(self, callback: Callable[[GestureEvent, str], None]):
        """
        设置手势识别回调函数

        Args:
            callback: 回调函数，接收(GestureEvent, command)参数
        """
        self.gesture_callback = callback
        logger.info("手势回调函数已设置")

    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """
        设置帧处理回调函数

        Args:
            callback: 回调函数，接收处理后的帧
        """
        self.frame_callback = callback
        logger.info("帧回调函数已设置")

    def get_session_info(self) -> Optional[GestureSessionInfo]:
        """获取当前会话信息"""
        return self.current_session

    def get_available_commands(self) -> List[Dict]:
        """获取可用命令列表"""
        return self.gesture_mapper.get_available_commands()

    def update_gesture_mapping(self, gesture_type: str, **kwargs) -> bool:
        """
        更新手势映射

        Args:
            gesture_type: 手势类型字符串
            **kwargs: 映射参数

        Returns:
            bool: 更新是否成功
        """
        from .models import GestureType

        try:
            gesture_enum = GestureType(gesture_type)
            return self.gesture_mapper.update_mapping(gesture_enum, **kwargs)
        except ValueError:
            logger.error(f"无效的手势类型: {gesture_type}")
            return False

    def get_service_status(self) -> Dict:
        """
        获取服务状态信息

        Returns:
            Dict: 状态信息
        """
        return {
            "is_running": self.is_running,
            "session_id": (
                self.current_session.session_id if self.current_session else None
            ),
            "frame_count": self.frame_count,
            "config": self.config.dict(),
            "processor_stats": self.gesture_processor.get_statistics(),
            "mapper_stats": self.gesture_mapper.get_mapping_stats(),
        }

    def close(self):
        """关闭服务并释放资源"""
        self.stop_session()
        self.hand_tracker.close()
        logger.info("ARGestureService已关闭")


# 便捷函数
def create_default_gesture_service() -> ARGestureService:
    """创建默认配置的手势识别服务"""
    config = ARGestureConfig(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
        gesture_timeout=2.0,
        gesture_cooldown=0.5,
        continuous_gesture_threshold=3,
        enable_multi_hand=True,
        enable_gesture_smoothing=True,
    )

    return ARGestureService(config)
