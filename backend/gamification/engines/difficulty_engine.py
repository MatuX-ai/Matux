"""
难度计算引擎
实现核心的难度评估和计算逻辑
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..models.difficulty_level import (
    DIFFICULTY_LEVELS,
    DifficultyLevel,
    TaskPerformanceMetrics,
)

logger = logging.getLogger(__name__)


class DifficultyEngine:
    """难度计算引擎"""

    def __init__(self):
        self.calculation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.user_performance_cache: Dict[str, List[TaskPerformanceMetrics]] = {}

    def calculate_task_difficulty(
        self,
        task_metrics: TaskPerformanceMetrics,
        user_history: Optional[List[TaskPerformanceMetrics]] = None,
    ) -> Tuple[float, DifficultyLevel]:
        """
        计算任务难度分数和等级

        Args:
            task_metrics: 任务表现指标
            user_history: 用户历史表现记录

        Returns:
            Tuple[难度分数(0-10), 难度等级]
        """
        try:
            # 计算基础难度分数
            base_score = self._calculate_base_difficulty(task_metrics)

            # 如果有用户历史，计算自适应难度
            if user_history and len(user_history) >= 3:
                adaptive_score = self._calculate_adaptive_difficulty(
                    base_score, task_metrics, user_history
                )
                final_score = adaptive_score
            else:
                final_score = base_score

            # 确保分数在合理范围内
            final_score = max(0.0, min(10.0, final_score))

            # 转换为难度等级
            difficulty_level = self._score_to_level(final_score)

            # 记录计算历史
            self._record_calculation(
                task_metrics.user_id,
                task_metrics.task_id,
                final_score,
                difficulty_level,
            )

            logger.debug(
                f"难度计算完成: 用户={task_metrics.user_id}, "
                f"任务={task_metrics.task_id}, 分数={final_score:.2f}, "
                f"等级={difficulty_level.value}"
            )

            return final_score, difficulty_level

        except Exception as e:
            logger.error(f"难度计算失败: {e}")
            # 返回默认值
            return 5.0, DifficultyLevel.L3

    def _calculate_base_difficulty(self, metrics: TaskPerformanceMetrics) -> float:
        """计算基础难度分数"""
        # 各指标权重
        weights = {
            "success_rate": 0.35,  # 成功率权重
            "time_efficiency": 0.25,  # 时间效率权重
            "hint_penalty": 0.20,  # 提示惩罚权重
            "retry_penalty": 0.15,  # 重试惩罚权重
            "hardware_bonus": 0.05,  # 硬件操作加成权重
        }

        # 成功率组件 (成功率越低，难度越高)
        success_component = (1 - metrics.success_rate) * 10 * weights["success_rate"]

        # 时间效率组件
        # 假设标准时间为30分钟，超过则增加难度分数
        time_factor = min(2.0, metrics.average_completion_time / 30)
        time_component = time_factor * weights["time_efficiency"]

        # 提示使用惩罚
        hint_penalty = min(2, metrics.hint_usage_count) * weights["hint_penalty"]

        # 重试惩罚
        retry_penalty = min(1.5, metrics.retry_count) * weights["retry_penalty"]

        # 硬件操作加成 (硬件操作越复杂，难度可能越高)
        hardware_bonus = 0
        if metrics.hardware_metrics:
            hardware_complexity = len(metrics.hardware_metrics)
            hardware_bonus = (
                min(1.0, hardware_complexity * 0.2) * weights["hardware_bonus"]
            )

        # 综合计算
        base_score = (
            success_component
            + time_component
            + hint_penalty
            + retry_penalty
            - hardware_bonus  # 减去bonus因为是加分项
        )

        return max(0.0, min(10.0, base_score))

    def _calculate_adaptive_difficulty(
        self,
        base_score: float,
        current_metrics: TaskPerformanceMetrics,
        user_history: List[TaskPerformanceMetrics],
    ) -> float:
        """计算自适应难度分数"""
        # 获取最近几次的表现
        recent_metrics = user_history[-3:] if len(user_history) >= 3 else user_history

        # 计算趋势
        recent_scores = [
            self._calculate_base_difficulty(metrics) for metrics in recent_metrics
        ]

        if len(recent_scores) >= 2:
            # 计算表现趋势
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]

            # 根据趋势调整难度
            if trend > 0.5:  # 表现持续改善
                adjustment = -0.3  # 降低难度
            elif trend < -0.5:  # 表现持续下降
                adjustment = 0.3  # 增加难度
            else:
                adjustment = 0.0  # 保持不变

        else:
            adjustment = 0.0

        # 应用调整
        adaptive_score = base_score + adjustment

        # 考虑当前表现的特殊情况
        if (
            current_metrics.success_rate > 0.9
            and current_metrics.average_completion_time < 15
        ):
            # 表现优秀，适度降低难度
            adaptive_score = max(0, adaptive_score - 0.2)
        elif current_metrics.success_rate < 0.3:
            # 表现较差，适度降低难度帮助用户
            adaptive_score = max(0, adaptive_score - 0.5)

        return adaptive_score

    def _score_to_level(self, score: float) -> DifficultyLevel:
        """将分数转换为难度等级"""
        for level, config in DIFFICULTY_LEVELS.items():
            min_score, max_score = config["score_range"]
            if min_score <= score <= max_score:
                return level

        # 边界情况处理
        if score < 0:
            return DifficultyLevel.L1
        else:
            return DifficultyLevel.L5

    def _record_calculation(
        self, user_id: str, task_id: str, score: float, level: DifficultyLevel
    ):
        """记录计算历史"""
        if user_id not in self.calculation_history:
            self.calculation_history[user_id] = []

        record = {
            "task_id": task_id,
            "difficulty_score": score,
            "difficulty_level": level.value,
            "timestamp": datetime.now().isoformat(),
        }

        self.calculation_history[user_id].append(record)

        # 限制历史记录数量
        if len(self.calculation_history[user_id]) > 100:
            self.calculation_history[user_id] = self.calculation_history[user_id][-100:]

    def get_user_difficulty_trend(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户难度趋势"""
        return self.calculation_history.get(user_id, [])

    def calculate_user_competency_score(self, user_id: str) -> float:
        """计算用户综合能力分数"""
        history = self.calculation_history.get(user_id, [])
        if not history:
            return 5.0  # 默认中等水平

        # 基于完成的任务难度和成功率计算
        total_weighted_score = 0
        total_weight = 0

        for record in history[-10:]:  # 最近10次记录
            # 权重基于任务难度
            weight = record["difficulty_score"] / 10
            weighted_score = record["difficulty_score"] * weight
            total_weighted_score += weighted_score
            total_weight += weight

        if total_weight > 0:
            competency_score = total_weighted_score / total_weight
        else:
            competency_score = 5.0

        return min(10.0, max(0.0, competency_score))


# 测试代码
if __name__ == "__main__":
    # 创建引擎实例
    engine = DifficultyEngine()

    # 创建测试数据
    from ..models.difficulty_level import DebuggingSession, HardwareOperationMetric

    test_metrics = TaskPerformanceMetrics(
        user_id="test_user_001",
        task_id="test_task_001",
        success_rate=0.8,
        average_completion_time=25.0,
        hint_usage_count=1,
        retry_count=0,
        hardware_metrics=[HardwareOperationMetric("gpio_read", 5, 5, 100.0, 0.0)],
        debugging_sessions=[DebuggingSession("debug_001", 15.0, 2, 10, 3, "completed")],
        timestamp=datetime.now(),
    )

    print("=== 难度引擎测试 ===")

    # 测试难度计算
    score, level = engine.calculate_task_difficulty(test_metrics)
    print(f"基础难度计算: 分数={score:.2f}, 等级={level.value}")

    # 测试用户能力分数
    competency = engine.calculate_user_competency_score("test_user_001")
    print(f"用户能力分数: {competency:.2f}")

    # 测试趋势分析
    trend = engine.get_user_difficulty_trend("test_user_001")
    print(f"计算历史记录数: {len(trend)}")
