"""
难度服务层
提供难度评估、等级管理和用户档案维护功能
"""

from dataclasses import asdict
from datetime import datetime, timedelta
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# 添加项目根目录到路径
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from gamification.models.difficulty_level import (
    DebuggingSession,
    DifficultyCalculator,
    DifficultyLevel,
    HardwareOperationMetric,
    TaskPerformanceMetrics,
)
from gamification.models.task_adjustment import (
    AdjustmentReason,
    AdjustmentType,
    DifficultyAdjustment,
    UserDifficultyProfile,
    UserTaskHistory,
)

logger = logging.getLogger(__name__)


class DifficultyService:
    """难度服务类"""

    def __init__(self):
        self.user_profiles: Dict[str, UserDifficultyProfile] = {}
        self.calculator = DifficultyCalculator()
        self._initialize_default_profiles()

    def _initialize_default_profiles(self):
        """初始化默认用户档案"""
        # 这里可以从数据库加载现有用户档案
        pass

    def create_user_profile(self, user_id: str) -> UserDifficultyProfile:
        """创建用户难度档案"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]

        profile = UserDifficultyProfile(user_id=user_id)
        self.user_profiles[user_id] = profile
        logger.info(f"创建用户难度档案: {user_id}")
        return profile

    def get_user_profile(self, user_id: str) -> Optional[UserDifficultyProfile]:
        """获取用户难度档案"""
        return self.user_profiles.get(user_id)

    def update_user_performance(
        self,
        user_id: str,
        task_id: str,
        performance_metrics: TaskPerformanceMetrics,
        success: bool,
    ) -> Tuple[float, DifficultyLevel]:
        """
        更新用户表现并计算新的难度等级

        Args:
            user_id: 用户ID
            task_id: 任务ID
            performance_metrics: 表现指标
            success: 是否成功完成

        Returns:
            Tuple[新的难度分数, 新的难度等级]
        """
        # 获取或创建用户档案
        profile = self.create_user_profile(user_id)

        # 记录任务历史
        task_history = UserTaskHistory(
            user_id=user_id,
            task_id=task_id,
            difficulty_level="",  # 稍后填充
            success=success,
            completion_time=performance_metrics.average_completion_time,
            hint_used=performance_metrics.hint_usage_count > 0,
            retry_count=performance_metrics.retry_count,
        )
        profile.add_task_history(task_history)

        # 计算新的难度分数
        current_score = performance_metrics.calculate_overall_difficulty_score()
        new_score, new_level = self.calculator.calculate_adaptive_difficulty(
            base_difficulty=profile.current_difficulty_level,
            performance_metrics=performance_metrics,
            user_history=profile.task_history[:-1],  # 排除刚添加的记录
        )

        # 更新用户档案
        profile.current_difficulty_level = new_score
        task_history.difficulty_level = new_level.value

        # 记录难度调整
        adjustment = DifficultyAdjustment(
            user_id=user_id,
            task_id=task_id,
            current_difficulty=profile.current_difficulty_level,
            adjusted_difficulty=new_score,
            adjustment_reason=AdjustmentReason.SKILL_IMPROVEMENT,
            adjustment_type=self._determine_adjustment_type(
                profile.current_difficulty_level, new_score
            ),
            confidence_score=0.8,
            metadata={
                "previous_score": profile.current_difficulty_level,
                "new_score": new_score,
                "performance_score": current_score,
            },
        )
        profile.add_adjustment(adjustment)

        logger.info(
            f"用户{user_id}难度更新: {profile.current_difficulty_level:.2f} -> {new_score:.2f} ({new_level.value})"
        )

        return new_score, new_level

    def _determine_adjustment_type(
        self, old_score: float, new_score: float
    ) -> AdjustmentType:
        """确定调整类型"""
        if abs(new_score - old_score) < 0.1:
            return AdjustmentType.MAINTAIN_CURRENT
        elif new_score > old_score:
            return AdjustmentType.INCREASE_DIFFICULTY
        else:
            return AdjustmentType.DECREASE_DIFFICULTY

    def get_user_difficulty_level(self, user_id: str) -> Tuple[float, DifficultyLevel]:
        """获取用户当前难度等级"""
        profile = self.get_user_profile(user_id)
        if not profile:
            # 返回默认难度
            default_score = 5.0
            return default_score, self.calculator.score_to_level(default_score)

        level = self.calculator.score_to_level(profile.current_difficulty_level)
        return profile.current_difficulty_level, level

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计信息"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return {}

        return {
            "current_difficulty_score": profile.current_difficulty_level,
            "current_difficulty_level": self.calculator.score_to_level(
                profile.current_difficulty_level
            ).value,
            "total_tasks_completed": len(profile.task_history),
            "recent_success_rate": profile.get_recent_success_rate(),
            "average_completion_time": profile.get_average_completion_time(),
            "success_streak": profile.streak_counter.success_streak,
            "failure_streak": profile.streak_counter.failure_streak,
            "last_adjustment_time": (
                profile.last_adjustment_time.isoformat()
                if profile.last_adjustment_time
                else None
            ),
            "total_adjustments": len(profile.adjustment_history),
        }

    def get_suitable_tasks(
        self, user_id: str, available_tasks: List[Dict[str, Any]], count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        根据用户难度等级推荐合适的任务

        Args:
            user_id: 用户ID
            available_tasks: 可用任务列表
            count: 推荐数量

        Returns:
            推荐的任务列表
        """
        if not available_tasks:
            return []

        # 获取用户难度等级
        difficulty_score, difficulty_level = self.get_user_difficulty_level(user_id)

        # 按难度匹配度排序
        def task_match_score(task: Dict[str, Any]) -> float:
            task_difficulty = task.get("difficulty_score", 5.0)
            # 计算与用户难度的匹配度(差值越小越好)
            match_score = 10 - abs(task_difficulty - difficulty_score)
            # 考虑任务的其他因素
            popularity = task.get("popularity_score", 0.5)
            quality = task.get("quality_score", 0.8)
            return match_score * 0.6 + popularity * 0.2 + quality * 0.2

        sorted_tasks = sorted(available_tasks, key=task_match_score, reverse=True)
        return sorted_tasks[:count]

    def manual_adjust_difficulty(
        self, user_id: str, new_difficulty_score: float, reason: str = "manual_override"
    ) -> bool:
        """
        手动调整用户难度

        Args:
            user_id: 用户ID
            new_difficulty_score: 新的难度分数
            reason: 调整原因

        Returns:
            是否调整成功
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return False

        old_score = profile.current_difficulty_level
        profile.current_difficulty_level = max(0, min(10, new_difficulty_score))

        adjustment = DifficultyAdjustment(
            user_id=user_id,
            current_difficulty=old_score,
            adjusted_difficulty=profile.current_difficulty_level,
            adjustment_reason=AdjustmentReason.MANUAL_OVERRIDE,
            adjustment_type=self._determine_adjustment_type(
                old_score, profile.current_difficulty_level
            ),
            confidence_score=1.0,
            metadata={"manual_reason": reason},
        )
        profile.add_adjustment(adjustment)

        logger.info(
            f"手动调整用户{user_id}难度: {old_score:.2f} -> {profile.current_difficulty_level:.2f}"
        )
        return True

    def batch_update_performances(
        self, user_performances: List[Tuple[str, str, TaskPerformanceMetrics, bool]]
    ) -> List[Tuple[str, float, DifficultyLevel]]:
        """
        批量更新用户表现

        Args:
            user_performances: [(user_id, task_id, metrics, success), ...]

        Returns:
            [(user_id, new_score, new_level), ...]
        """
        results = []
        for user_id, task_id, metrics, success in user_performances:
            try:
                new_score, new_level = self.update_user_performance(
                    user_id, task_id, metrics, success
                )
                results.append((user_id, new_score, new_level))
            except Exception as e:
                logger.error(f"批量更新用户{user_id}表现失败: {e}")
                results.append((user_id, 0.0, DifficultyLevel.L1))

        return results

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取难度排行榜"""
        profiles = list(self.user_profiles.values())
        # 按难度等级排序(高级用户排前面)
        sorted_profiles = sorted(
            profiles, key=lambda p: p.current_difficulty_level, reverse=True
        )

        leaderboard = []
        for i, profile in enumerate(sorted_profiles[:limit], 1):
            leaderboard.append(
                {
                    "rank": i,
                    "user_id": profile.user_id,
                    "difficulty_score": profile.current_difficulty_level,
                    "difficulty_level": self.calculator.score_to_level(
                        profile.current_difficulty_level
                    ).value,
                    "tasks_completed": len(profile.task_history),
                    "success_rate": profile.get_recent_success_rate(),
                }
            )

        return leaderboard


# 测试代码
if __name__ == "__main__":
    # 创建服务实例
    service = DifficultyService()

    # 创建测试数据
    hardware_metric = HardwareOperationMetric(
        operation_type="sensor_reading",
        success_count=9,
        total_count=10,
        average_response_time=120.0,
        error_rate=0.1,
    )

    debugging_session = DebuggingSession(
        session_id="debug_001",
        duration=12.0,
        breakpoint_count=2,
        step_count=15,
        variable_inspection_count=3,
        completion_status="completed",
    )

    # 测试用户表现更新
    metrics = TaskPerformanceMetrics(
        user_id="test_user_001",
        task_id="task_001",
        success_rate=0.8,
        average_completion_time=20.0,
        hint_usage_count=1,
        retry_count=0,
        hardware_metrics=[hardware_metric],
        debugging_sessions=[debugging_session],
        timestamp=datetime.now(),
    )

    print("=== 难度服务测试 ===")

    # 更新用户表现
    new_score, new_level = service.update_user_performance(
        user_id="test_user_001",
        task_id="task_001",
        performance_metrics=metrics,
        success=True,
    )

    print(f"用户难度更新: {new_score:.2f} ({new_level.value})")

    # 获取用户统计
    stats = service.get_user_statistics("test_user_001")
    print(f"用户统计: {stats}")

    # 测试任务推荐
    available_tasks = [
        {
            "id": "task_001",
            "difficulty_score": 4.5,
            "popularity_score": 0.8,
            "quality_score": 0.9,
        },
        {
            "id": "task_002",
            "difficulty_score": 6.2,
            "popularity_score": 0.7,
            "quality_score": 0.8,
        },
        {
            "id": "task_003",
            "difficulty_score": 3.8,
            "popularity_score": 0.9,
            "quality_score": 0.7,
        },
    ]

    recommended_tasks = service.get_suitable_tasks("test_user_001", available_tasks, 2)
    print(f"推荐任务: {[task['id'] for task in recommended_tasks]}")

    # 测试排行榜
    leaderboard = service.get_leaderboard(3)
    print(f"排行榜: {leaderboard}")
