"""
难度等级模型定义
实现L1-L5五级难度标准和评估算法
"""

from dataclasses import dataclass
from datetime import datetime
import enum
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DifficultyLevel(str, enum.Enum):
    """任务难度等级枚举 (L1-L5)"""

    L1 = "L1"  # 入门级 - 非常简单
    L2 = "L2"  # 初级 - 简单
    L3 = "L3"  # 中级 - 中等
    L4 = "L4"  # 高级 - 困难
    L5 = "L5"  # 专家级 - 非常困难


# 难度等级标准映射
DIFFICULTY_LEVELS = {
    DifficultyLevel.L1: {
        "score_range": (0.0, 2.0),
        "description": "入门级",
        "characteristics": ["基础知识掌握", "简单操作任务", "明确指导步骤"],
        "target_users": "初学者",
    },
    DifficultyLevel.L2: {
        "score_range": (2.0, 4.0),
        "description": "初级",
        "characteristics": ["基本技能应用", "常规问题解决", "少量独立思考"],
        "target_users": "有一定基础的学习者",
    },
    DifficultyLevel.L3: {
        "score_range": (4.0, 6.0),
        "description": "中级",
        "characteristics": ["综合技能运用", "复杂问题分析", "创新思维要求"],
        "target_users": "熟练学习者",
    },
    DifficultyLevel.L4: {
        "score_range": (6.0, 8.0),
        "description": "高级",
        "characteristics": ["专业知识深度", "系统性解决方案", "批判性思维"],
        "target_users": "高级学习者",
    },
    DifficultyLevel.L5: {
        "score_range": (8.0, 10.0),
        "description": "专家级",
        "characteristics": ["前沿技术掌握", "原创性研究", "行业领先水平"],
        "target_users": "专家级用户",
    },
}


@dataclass
class HardwareOperationMetric:
    """硬件操作指标"""

    operation_type: str  # 操作类型
    success_count: int  # 成功次数
    total_count: int  # 总次数
    average_response_time: float  # 平均响应时间(ms)
    error_rate: float  # 错误率

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


@dataclass
class DebuggingSession:
    """调试会话记录"""

    session_id: str
    duration: float  # 调试时长(分钟)
    breakpoint_count: int  # 断点数量
    step_count: int  # 步进次数
    variable_inspection_count: int  # 变量检查次数
    completion_status: str  # 完成状态


@dataclass
class TaskPerformanceMetrics:
    """任务表现指标"""

    user_id: str
    task_id: str
    success_rate: float  # 任务成功率
    average_completion_time: float  # 平均完成时间(分钟)
    hint_usage_count: int  # 提示使用次数
    retry_count: int  # 重试次数
    hardware_metrics: List[HardwareOperationMetric]  # 硬件操作指标
    debugging_sessions: List[DebuggingSession]  # 调试会话记录
    timestamp: datetime

    def calculate_hardware_success_rate(self) -> float:
        """计算硬件操作综合成功率"""
        if not self.hardware_metrics:
            return 1.0  # 无硬件操作时默认满分

        total_success = sum(metric.success_count for metric in self.hardware_metrics)
        total_operations = sum(metric.total_count for metric in self.hardware_metrics)

        if total_operations == 0:
            return 1.0

        return total_success / total_operations

    def calculate_debugging_efficiency(self) -> float:
        """计算调试效率分数 (0-10分，分数越高效率越高)"""
        if not self.debugging_sessions:
            return 10.0  # 无调试记录时默认高效率

        total_duration = sum(session.duration for session in self.debugging_sessions)
        avg_duration = total_duration / len(self.debugging_sessions)

        # 调试时间越短，效率分数越高
        # 假设30分钟为基准时间，超过则扣分
        efficiency_score = max(0, 10 - (avg_duration / 3))  # 每3分钟扣1分
        return min(10.0, efficiency_score)

    def calculate_overall_difficulty_score(self) -> float:
        """计算综合难度分数 (0-10)"""
        # 各指标权重
        weights = {
            "success_rate": 0.4,  # 成功率权重40%
            "time_efficiency": 0.3,  # 时间效率权重30%
            "hint_usage": 0.2,  # 提示使用权重20%
            "retry_count": 0.1,  # 重试次数权重10%
        }

        # 成功率反向指标 (成功率越低难度越高)
        success_component = (1 - self.success_rate) * 10 * weights["success_rate"]

        # 时间效率指标
        time_component = (
            min(10, self.average_completion_time / 5) * weights["time_efficiency"]
        )

        # 提示使用惩罚 (提示越多说明难度越大)
        hint_penalty = min(3, self.hint_usage_count) * weights["hint_usage"]

        # 重试惩罚 (重试越多说明难度越大)
        retry_penalty = min(2, self.retry_count) * weights["retry_count"]

        # 硬件操作和调试效率加成
        hardware_bonus = (1 - self.calculate_hardware_success_rate()) * 2  # 最多加2分
        debugging_bonus = (10 - self.calculate_debugging_efficiency()) / 5  # 最多加2分

        total_score = (
            success_component
            + time_component
            + hint_penalty
            + retry_penalty
            + hardware_bonus
            + debugging_bonus
        )

        return min(10.0, max(0.0, total_score))


class DifficultyCalculator:
    """难度等级计算器"""

    @staticmethod
    def score_to_level(score: float) -> DifficultyLevel:
        """将难度分数转换为等级"""
        for level, config in DIFFICULTY_LEVELS.items():
            min_score, max_score = config["score_range"]
            if min_score <= score <= max_score:
                return level
        # 边界情况处理
        if score < 0:
            return DifficultyLevel.L1
        else:
            return DifficultyLevel.L5

    @staticmethod
    def level_to_score_range(level: DifficultyLevel) -> Tuple[float, float]:
        """获取等级对应的分数范围"""
        return DIFFICULTY_LEVELS[level]["score_range"]

    @staticmethod
    def get_level_description(level: DifficultyLevel) -> str:
        """获取等级描述"""
        return DIFFICULTY_LEVELS[level]["description"]

    @staticmethod
    def calculate_adaptive_difficulty(
        base_difficulty: float,
        performance_metrics: TaskPerformanceMetrics,
        user_history: List[TaskPerformanceMetrics] = None,
    ) -> Tuple[float, DifficultyLevel]:
        """
        计算自适应难度分数和等级

        Args:
            base_difficulty: 基础难度分数
            performance_metrics: 当前表现指标
            user_history: 用户历史表现记录

        Returns:
            Tuple[难度分数, 难度等级]
        """
        # 当前任务难度分数
        current_score = performance_metrics.calculate_overall_difficulty_score()

        # 如果有历史记录，计算趋势调整
        if user_history and len(user_history) >= 3:
            # 注意：user_history包含的是UserTaskHistory对象，不是TaskPerformanceMetrics
            # 我们需要从这些历史记录中推断趋势
            recent_success_rates = [
                1.0 if record.success else 0.0 for record in user_history[-3:]
            ]
            avg_success_rate = sum(recent_success_rates) / len(recent_success_rates)

            # 根据近期成功率调整
            if avg_success_rate > 0.8:  # 近期表现优秀
                current_score = max(0, current_score - 0.3)
            elif avg_success_rate < 0.4:  # 近期表现较差
                current_score = min(10, current_score + 0.3)

        # 结合基础难度和实际表现
        final_score = (base_difficulty + current_score) / 2
        final_level = DifficultyCalculator.score_to_level(final_score)

        logger.info(
            f"难度计算: 基础={base_difficulty:.2f}, 实际={current_score:.2f}, "
            f"最终={final_score:.2f}, 等级={final_level.value}"
        )

        return final_score, final_level


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    hardware_metric = HardwareOperationMetric(
        operation_type="gpio_control",
        success_count=8,
        total_count=10,
        average_response_time=150.0,
        error_rate=0.2,
    )

    debugging_session = DebuggingSession(
        session_id="debug_001",
        duration=15.5,
        breakpoint_count=3,
        step_count=20,
        variable_inspection_count=5,
        completion_status="completed",
    )

    # 测试表现指标
    metrics = TaskPerformanceMetrics(
        user_id="test_user_001",
        task_id="task_001",
        success_rate=0.7,
        average_completion_time=25.0,
        hint_usage_count=2,
        retry_count=1,
        hardware_metrics=[hardware_metric],
        debugging_sessions=[debugging_session],
        timestamp=datetime.now(),
    )

    print("=== 难度等级测试 ===")
    print(f"硬件成功率: {metrics.calculate_hardware_success_rate():.2f}")
    print(f"调试效率: {metrics.calculate_debugging_efficiency():.2f}")
    print(f"综合难度分数: {metrics.calculate_overall_difficulty_score():.2f}")

    # 测试等级转换
    score = metrics.calculate_overall_difficulty_score()
    level = DifficultyCalculator.score_to_level(score)
    print(
        f"难度等级: {level.value} ({DifficultyCalculator.get_level_description(level)})"
    )

    # 测试自适应难度计算
    final_score, final_level = DifficultyCalculator.calculate_adaptive_difficulty(
        base_difficulty=5.0, performance_metrics=metrics
    )
    print(f"自适应难度: {final_score:.2f} -> {final_level.value}")
