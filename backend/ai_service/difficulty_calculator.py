"""
动态难度系数计算器
实现 difficulty = 1/(success_rate)^2 公式及相关的难度调整机制
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """难度等级枚举"""

    VERY_EASY = "very_easy"  # 非常简单
    EASY = "easy"  # 简单
    MODERATE = "moderate"  # 中等
    DIFFICULT = "difficult"  # 困难
    VERY_DIFFICULT = "very_difficult"  # 非常困难


@dataclass
class PerformanceMetrics:
    """用户表现指标"""

    user_id: str
    content_id: str
    success_rate: float  # 成功率 (0-1)
    attempt_count: int  # 尝试次数
    average_time_spent: float  # 平均耗时(分钟)
    error_rate: float  # 错误率
    hint_usage: int  # 提示使用次数
    last_attempt_date: datetime
    confidence_interval: Tuple[float, float]  # 置信区间


@dataclass
class DifficultyAdjustment:
    """难度调整结果"""

    content_id: str
    current_difficulty: float
    adjusted_difficulty: float
    adjustment_reason: str
    confidence_score: float
    recommended_next_level: Optional[str]


class DifficultyCalculator:
    """动态难度系数计算器"""

    # 难度等级映射
    DIFFICULTY_LEVELS = {
        DifficultyLevel.VERY_EASY: 0.2,
        DifficultyLevel.EASY: 0.4,
        DifficultyLevel.MODERATE: 0.6,
        DifficultyLevel.DIFFICULT: 0.8,
        DifficultyLevel.VERY_DIFFICULT: 1.0,
    }

    # 逆向映射
    DIFFICULTY_VALUES = {v: k for k, v in DIFFICULTY_LEVELS.items()}

    def __init__(self, smoothing_factor: float = 0.3, min_samples: int = 5):
        """
        初始化难度计算器

        Args:
            smoothing_factor: 平滑因子，用于EMA计算 (0-1)
            min_samples: 最小样本数量阈值
        """
        self.smoothing_factor = smoothing_factor
        self.min_samples = min_samples
        self.performance_history = {}  # user_id -> content_id -> deque of metrics
        self.difficulty_cache = {}  # content_id -> current_difficulty

    @staticmethod
    def calculate_dynamic_difficulty(success_rate: float) -> float:
        """
        核心难度计算公式: difficulty = 1/(success_rate)^2

        Args:
            success_rate: 成功率 (0-1)

        Returns:
            float: 难度系数
        """
        # 边界处理
        if success_rate <= 0:
            return float("inf")  # 无限难度
        if success_rate >= 1:
            return 0.1  # 最小难度

        # 核心公式实现
        difficulty = 1 / (success_rate**2)

        # 限制合理范围
        return max(0.1, min(10.0, difficulty))

    def calculate_difficulty_level(self, difficulty_score: float) -> DifficultyLevel:
        """
        将难度分数转换为难度等级

        Args:
            difficulty_score: 难度分数

        Returns:
            DifficultyLevel: 难度等级
        """
        if difficulty_score <= 0.3:
            return DifficultyLevel.VERY_EASY
        elif difficulty_score <= 0.5:
            return DifficultyLevel.EASY
        elif difficulty_score <= 0.7:
            return DifficultyLevel.MODERATE
        elif difficulty_score <= 0.9:
            return DifficultyLevel.DIFFICULT
        else:
            return DifficultyLevel.VERY_DIFFICULT

    def add_performance_metric(self, metric: PerformanceMetrics) -> bool:
        """
        添加用户表现指标

        Args:
            metric: 表现指标对象

        Returns:
            bool: 添加是否成功
        """
        try:
            # 初始化用户历史记录
            if metric.user_id not in self.performance_history:
                self.performance_history[metric.user_id] = {}

            # 初始化内容历史记录
            if metric.content_id not in self.performance_history[metric.user_id]:
                self.performance_history[metric.user_id][metric.content_id] = deque(
                    maxlen=20
                )

            # 添加到历史记录
            self.performance_history[metric.user_id][metric.content_id].append(metric)

            # 更新难度缓存
            self._update_difficulty_cache(metric.content_id)

            logger.debug(
                f"添加用户 {metric.user_id} 在内容 {metric.content_id} 的表现数据"
            )
            return True

        except Exception as e:
            logger.error(f"添加表现指标失败: {e}")
            return False

    def _update_difficulty_cache(self, content_id: str):
        """更新难度缓存"""
        all_metrics = []

        # 收集所有用户对该内容的表现数据
        for user_history in self.performance_history.values():
            if content_id in user_history:
                all_metrics.extend(user_history[content_id])

        if len(all_metrics) >= self.min_samples:
            # 计算综合成功率
            avg_success_rate = np.mean(
                [m.success_rate for m in all_metrics[-self.min_samples :]]
            )

            # 使用EMA平滑
            current_difficulty = self.difficulty_cache.get(content_id, 0.5)
            new_difficulty = (
                self.smoothing_factor
                * self.calculate_dynamic_difficulty(avg_success_rate)
                + (1 - self.smoothing_factor) * current_difficulty
            )

            self.difficulty_cache[content_id] = new_difficulty

    def get_content_difficulty(self, content_id: str) -> float:
        """
        获取内容的当前难度系数

        Args:
            content_id: 内容ID

        Returns:
            float: 难度系数
        """
        return self.difficulty_cache.get(content_id, 0.5)  # 默认中等难度

    def adjust_difficulty_for_user(
        self, user_id: str, content_id: str, target_success_rate: float = 0.7
    ) -> DifficultyAdjustment:
        """
        为特定用户调整内容难度

        Args:
            user_id: 用户ID
            content_id: 内容ID
            target_success_rate: 目标成功率

        Returns:
            DifficultyAdjustment: 难度调整结果
        """
        # 获取用户历史表现
        user_metrics = self._get_user_metrics(user_id, content_id)
        if not user_metrics:
            return DifficultyAdjustment(
                content_id=content_id,
                current_difficulty=self.get_content_difficulty(content_id),
                adjusted_difficulty=self.get_content_difficulty(content_id),
                adjustment_reason="无历史数据，使用默认难度",
                confidence_score=0.1,
                recommended_next_level=None,
            )

        # 计算用户当前成功率
        current_success_rate = np.mean([m.success_rate for m in user_metrics])
        current_difficulty = self.get_content_difficulty(content_id)

        # 计算需要的目标难度
        target_difficulty = self.calculate_dynamic_difficulty(target_success_rate)

        # 计算调整幅度
        adjustment_ratio = (
            target_difficulty / current_difficulty if current_difficulty > 0 else 1.0
        )
        adjusted_difficulty = current_difficulty * adjustment_ratio

        # 限制调整范围
        adjusted_difficulty = max(0.1, min(10.0, adjusted_difficulty))

        # 确定调整原因
        if current_success_rate < 0.5:
            reason = "用户成功率过低，需要降低难度"
        elif current_success_rate > 0.9:
            reason = "用户成功率过高，可以适当增加难度"
        else:
            reason = "用户表现适中，维持当前难度"

        # 计算置信度
        confidence = min(1.0, len(user_metrics) / self.min_samples)

        # 推荐下一个难度等级
        next_level = self._recommend_next_difficulty_level(
            current_difficulty, adjusted_difficulty, current_success_rate
        )

        return DifficultyAdjustment(
            content_id=content_id,
            current_difficulty=current_difficulty,
            adjusted_difficulty=adjusted_difficulty,
            adjustment_reason=reason,
            confidence_score=confidence,
            recommended_next_level=next_level,
        )

    def _get_user_metrics(
        self, user_id: str, content_id: str
    ) -> Optional[List[PerformanceMetrics]]:
        """获取用户在特定内容上的表现指标"""
        if (
            user_id in self.performance_history
            and content_id in self.performance_history[user_id]
        ):
            return list(self.performance_history[user_id][content_id])
        return None

    def _recommend_next_difficulty_level(
        self, current_diff: float, adjusted_diff: float, success_rate: float
    ) -> Optional[str]:
        """推荐下一个难度等级"""
        if abs(adjusted_diff - current_diff) < 0.1:  # 变化很小
            return None

        if adjusted_diff > current_diff:  # 难度增加
            if success_rate > 0.8:
                return "increase_difficulty"
            else:
                return "maintain_current"
        else:  # 难度降低
            if success_rate < 0.3:
                return "decrease_difficulty"
            else:
                return "maintain_current"

    def get_personalized_difficulty(self, user_id: str, content_id: str) -> float:
        """
        获取针对用户的个性化难度系数

        Args:
            user_id: 用户ID
            content_id: 内容ID

        Returns:
            float: 个性化难度系数
        """
        # 基础难度
        base_difficulty = self.get_content_difficulty(content_id)

        # 用户历史调整
        user_metrics = self._get_user_metrics(user_id, content_id)
        if user_metrics and len(user_metrics) >= 3:
            recent_success = np.mean([m.success_rate for m in user_metrics[-3:]])
            # 根据用户近期表现微调难度
            personalization_factor = 1.0 + (0.7 - recent_success) * 0.3
            return base_difficulty * personalization_factor

        return base_difficulty

    def batch_adjust_difficulties(
        self, user_id: str, content_list: List[str]
    ) -> Dict[str, DifficultyAdjustment]:
        """
        批量调整用户对多个内容的难度

        Args:
            user_id: 用户ID
            content_list: 内容ID列表

        Returns:
            Dict: 内容ID到难度调整结果的映射
        """
        adjustments = {}

        for content_id in content_list:
            adjustment = self.adjust_difficulty_for_user(user_id, content_id)
            adjustments[content_id] = adjustment

        return adjustments

    def get_difficulty_insights(self, content_id: str) -> Dict[str, Any]:
        """
        获取内容难度洞察

        Args:
            content_id: 内容ID

        Returns:
            Dict: 难度洞察信息
        """
        current_difficulty = self.get_content_difficulty(content_id)
        difficulty_level = self.calculate_difficulty_level(current_difficulty)

        # 收集相关统计数据
        all_user_metrics = []
        for user_history in self.performance_history.values():
            if content_id in user_history:
                all_user_metrics.extend(user_history[content_id])

        if all_user_metrics:
            success_rates = [m.success_rate for m in all_user_metrics]
            avg_success_rate = np.mean(success_rates)
            std_success_rate = np.std(success_rates)

            return {
                "content_id": content_id,
                "current_difficulty": current_difficulty,
                "difficulty_level": difficulty_level.value,
                "average_success_rate": avg_success_rate,
                "success_rate_std": std_success_rate,
                "total_attempts": len(all_user_metrics),
                "difficulty_trend": self._analyze_difficulty_trend(content_id),
            }

        return {
            "content_id": content_id,
            "current_difficulty": current_difficulty,
            "difficulty_level": difficulty_level.value,
            "average_success_rate": 0.0,
            "success_rate_std": 0.0,
            "total_attempts": 0,
            "difficulty_trend": "stable",
        }

    def _analyze_difficulty_trend(self, content_id: str) -> str:
        """分析难度趋势"""
        difficulties = []

        for user_history in self.performance_history.values():
            if content_id in user_history:
                for metric in user_history[content_id]:
                    diff = self.calculate_dynamic_difficulty(metric.success_rate)
                    difficulties.append(diff)

        if len(difficulties) < 5:
            return "insufficient_data"

        # 简单的趋势分析
        recent_avg = np.mean(difficulties[-5:])
        overall_avg = np.mean(difficulties)

        if recent_avg > overall_avg * 1.1:
            return "increasing"
        elif recent_avg < overall_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def reset_user_history(self, user_id: str):
        """重置用户历史记录"""
        if user_id in self.performance_history:
            del self.performance_history[user_id]
            logger.info(f"用户 {user_id} 的历史记录已重置")


# 便捷函数
def create_performance_metric(
    user_id: str, content_id: str, success_rate: float, **kwargs
) -> PerformanceMetrics:
    """创建表现指标的便捷函数"""
    return PerformanceMetrics(
        user_id=user_id,
        content_id=content_id,
        success_rate=success_rate,
        attempt_count=kwargs.get("attempt_count", 1),
        average_time_spent=kwargs.get("time_spent", 0.0),
        error_rate=kwargs.get("error_rate", 1 - success_rate),
        hint_usage=kwargs.get("hint_usage", 0),
        last_attempt_date=kwargs.get("attempt_date", datetime.now()),
        confidence_interval=kwargs.get(
            "confidence_interval", (success_rate - 0.1, success_rate + 0.1)
        ),
    )


def test_difficulty_calculation():
    """测试难度计算功能"""
    calculator = DifficultyCalculator()

    # 测试核心公式
    test_cases = [
        (1.0, 0.1),  # 100%成功率 -> 最低难度
        (0.9, 1.23),  # 90%成功率 -> 低难度
        (0.7, 2.04),  # 70%成功率 -> 中等难度
        (0.5, 4.0),  # 50%成功率 -> 高难度
        (0.3, 11.11),  # 30%成功率 -> 很高难度
        (0.1, 100.0),  # 10%成功率 -> 最高难度
        (0.0, float("inf")),  # 0%成功率 -> 无限难度
    ]

    print("难度计算公式测试:")
    for success_rate, expected_difficulty in test_cases:
        calculated_difficulty = calculator.calculate_dynamic_difficulty(success_rate)
        print(
            f"成功率: {success_rate:.1f} -> 难度: {calculated_difficulty:.2f} (期望: {expected_difficulty})"
        )

    # 测试难度等级转换
    print("\n难度等级转换测试:")
    difficulty_scores = [0.2, 0.4, 0.6, 0.8, 1.0]
    for score in difficulty_scores:
        level = calculator.calculate_difficulty_level(score)
        print(f"难度分数: {score} -> 等级: {level.value}")


if __name__ == "__main__":
    test_difficulty_calculation()
