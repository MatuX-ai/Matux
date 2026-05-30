"""
手势处理器
处理手势识别结果，进行平滑处理和防抖动
"""

from collections import deque
import logging
import time
from typing import Dict, Optional

from .models import ARGestureConfig, GestureEvent, GestureRecognitionResult, GestureType

logger = logging.getLogger(__name__)


class GestureProcessor:
    """手势处理器类"""

    def __init__(self, config: ARGestureConfig):
        """
        初始化手势处理器

        Args:
            config: 手势识别配置
        """
        self.config = config

        # 手势历史记录（用于平滑处理）
        self.gesture_history = deque(maxlen=10)

        # 连续手势计数
        self.continuous_gesture_count = {}

        # 最后一次手势时间和类型
        self.last_gesture_time = 0
        self.last_gesture_type = GestureType.UNKNOWN

        # 冷却期管理
        self.cooldown_end_time = 0

        logger.info("GestureProcessor初始化完成")

    def process_gesture(
        self,
        gesture_result: GestureRecognitionResult,
        user_id: Optional[int] = None,
        session_id: str = "",
        device_id: str = "",
    ) -> Optional[GestureEvent]:
        """
        处理手势识别结果

        Args:
            gesture_result: 手势识别结果
            user_id: 用户ID
            session_id: 会话ID
            device_id: 设备ID

        Returns:
            Optional[GestureEvent]: 处理后手势事件，如果被过滤则返回None
        """
        try:
            current_time = time.time()

            # 1. 置信度过滤
            if gesture_result.confidence < self.config.min_detection_confidence:
                logger.debug(f"手势置信度过低: {gesture_result.confidence}")
                return None

            # 2. 冷却期检查
            if current_time < self.cooldown_end_time:
                logger.debug("手势处于冷却期")
                return None

            # 3. 相同手势去重
            if (
                gesture_result.gesture_type == self.last_gesture_type
                and current_time - self.last_gesture_time < self.config.gesture_timeout
            ):
                logger.debug("相同手势重复触发")
                return None

            # 4. 手势平滑处理
            smoothed_gesture = self._smooth_gesture(gesture_result)
            if not smoothed_gesture:
                return None

            # 5. 连续手势检测
            if self.config.enable_gesture_smoothing:
                continuous_count = self._update_continuous_gesture(
                    smoothed_gesture.gesture_type
                )
                if continuous_count < self.config.continuous_gesture_threshold:
                    logger.debug(f"连续手势次数不足: {continuous_count}")
                    return None

            # 6. 创建手势事件
            gesture_event = GestureEvent(
                event_id=f"gesture_{int(current_time * 1000)}",
                gesture_result=smoothed_gesture,
                user_id=user_id,
                session_id=session_id,
                device_id=device_id,
                created_at=smoothed_gesture.recognition_time,
            )

            # 7. 更新状态
            self._update_processor_state(smoothed_gesture, current_time)

            logger.info(
                f"手势处理成功: {smoothed_gesture.gesture_type} "
                f"(置信度: {smoothed_gesture.confidence:.2f})"
            )

            return gesture_event

        except Exception as e:
            logger.error(f"手势处理失败: {e}")
            return None

    def _smooth_gesture(
        self, gesture_result: GestureRecognitionResult
    ) -> Optional[GestureRecognitionResult]:
        """
        手势平滑处理

        Args:
            gesture_result: 原始手势识别结果

        Returns:
            Optional[GestureRecognitionResult]: 平滑后的手势结果
        """
        if not self.config.enable_gesture_smoothing:
            return gesture_result

        # 添加到历史记录
        self.gesture_history.append(gesture_result)

        if len(self.gesture_history) < 3:
            return gesture_result

        # 统计最近几次手势的类型分布
        recent_gestures = list(self.gesture_history)[-5:]  # 取最近5个
        gesture_counts = {}

        for gesture in recent_gestures:
            gesture_type = gesture.gesture_type
            if gesture_type not in gesture_counts:
                gesture_counts[gesture_type] = []
            gesture_counts[gesture_type].append(gesture.confidence)

        # 找出最一致的手势类型
        if gesture_counts:
            # 计算每个手势类型的平均置信度
            avg_confidences = {
                gesture_type: sum(confidences) / len(confidences)
                for gesture_type, confidences in gesture_counts.items()
            }

            # 选择平均置信度最高的手势类型
            best_gesture_type = max(
                avg_confidences.keys(), key=lambda x: avg_confidences[x]
            )

            # 如果最佳手势类型与当前手势不同，使用历史中最相似的结果
            if best_gesture_type != gesture_result.gesture_type:
                best_matches = [
                    g for g in recent_gestures if g.gesture_type == best_gesture_type
                ]
                if best_matches:
                    # 返回置信度最高的匹配结果
                    return max(best_matches, key=lambda x: x.confidence)

        return gesture_result

    def _update_continuous_gesture(self, gesture_type: GestureType) -> int:
        """
        更新连续手势计数

        Args:
            gesture_type: 手势类型

        Returns:
            int: 连续出现次数
        """
        current_time = time.time()

        # 清理过期的计数（超过timeout的）
        expired_keys = []
        for gesture_key, (count, last_time) in self.continuous_gesture_count.items():
            if current_time - last_time > self.config.gesture_timeout:
                expired_keys.append(gesture_key)

        for key in expired_keys:
            del self.continuous_gesture_count[key]

        # 更新当前手势计数
        gesture_key = str(gesture_type)
        if gesture_key in self.continuous_gesture_count:
            count, _ = self.continuous_gesture_count[gesture_key]
            self.continuous_gesture_count[gesture_key] = (count + 1, current_time)
        else:
            self.continuous_gesture_count[gesture_key] = (1, current_time)

        return self.continuous_gesture_count[gesture_key][0]

    def _update_processor_state(
        self, gesture_result: GestureRecognitionResult, current_time: float
    ):
        """
        更新处理器状态

        Args:
            gesture_result: 手势识别结果
            current_time: 当前时间戳
        """
        # 更新最后手势信息
        self.last_gesture_time = current_time
        self.last_gesture_type = gesture_result.gesture_type

        # 设置冷却期
        self.cooldown_end_time = current_time + self.config.gesture_cooldown

        # 清理旧的历史记录
        while (
            self.gesture_history
            and current_time - self.gesture_history[0].recognition_time.timestamp()
            > 2.0
        ):
            self.gesture_history.popleft()

    def reset(self):
        """重置处理器状态"""
        self.gesture_history.clear()
        self.continuous_gesture_count.clear()
        self.last_gesture_time = 0
        self.last_gesture_type = GestureType.UNKNOWN
        self.cooldown_end_time = 0
        logger.info("GestureProcessor状态已重置")

    def get_statistics(self) -> Dict:
        """
        获取处理器统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "history_length": len(self.gesture_history),
            "continuous_gestures": dict(self.continuous_gesture_count),
            "last_gesture_type": str(self.last_gesture_type),
            "last_gesture_time": self.last_gesture_time,
            "cooldown_remaining": max(0, self.cooldown_end_time - time.time()),
        }
