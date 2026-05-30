"""
自适应任务服务
实现动态任务推送和难度实时调整功能
"""

import asyncio
from datetime import datetime, timedelta
import logging
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

# 添加项目根目录到路径
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from gamification.models.difficulty_level import DifficultyLevel, TaskPerformanceMetrics
from gamification.models.task_adjustment import UserTaskHistory
from gamification.services.difficulty_service import DifficultyService
from gamification.services.rule_engine_service import RuleEngineService

logger = logging.getLogger(__name__)


class AdaptiveTaskService:
    """自适应任务服务类"""

    def __init__(
        self,
        difficulty_service: DifficultyService,
        rule_engine_service: RuleEngineService,
    ):
        self.difficulty_service = difficulty_service
        self.rule_engine_service = rule_engine_service
        self.task_repository = {}  # 任务存储库(模拟)
        self._initialize_sample_tasks()

    def _initialize_sample_tasks(self):
        """初始化示例任务数据"""
        sample_tasks = [
            {
                "task_id": "intro_001",
                "title": "Python基础语法练习",
                "description": "学习Python基本语法和数据类型",
                "difficulty_score": 1.5,
                "difficulty_level": "L1",
                "estimated_time": 30,  # 分钟
                "tags": ["python", "basics"],
                "prerequisites": [],
                "popularity_score": 0.9,
                "quality_score": 0.8,
            },
            {
                "task_id": "algo_001",
                "title": "冒泡排序算法实现",
                "description": "实现经典的冒泡排序算法",
                "difficulty_score": 3.2,
                "difficulty_level": "L2",
                "estimated_time": 45,
                "tags": ["algorithm", "sorting"],
                "prerequisites": ["intro_001"],
                "popularity_score": 0.8,
                "quality_score": 0.9,
            },
            {
                "task_id": "web_001",
                "title": "Flask Web应用开发",
                "description": "使用Flask框架开发简单的Web应用",
                "difficulty_score": 5.8,
                "difficulty_level": "L3",
                "estimated_time": 120,
                "tags": ["web", "flask", "backend"],
                "prerequisites": ["algo_001"],
                "popularity_score": 0.7,
                "quality_score": 0.85,
            },
            {
                "task_id": "ml_001",
                "title": "机器学习模型训练",
                "description": "使用scikit-learn训练分类模型",
                "difficulty_score": 7.5,
                "difficulty_level": "L4",
                "estimated_time": 180,
                "tags": ["machine-learning", "scikit-learn"],
                "prerequisites": ["web_001"],
                "popularity_score": 0.6,
                "quality_score": 0.9,
            },
            {
                "task_id": "distributed_001",
                "title": "分布式系统设计",
                "description": "设计高可用的分布式系统架构",
                "difficulty_score": 9.2,
                "difficulty_level": "L5",
                "estimated_time": 240,
                "tags": ["distributed-systems", "architecture"],
                "prerequisites": ["ml_001"],
                "popularity_score": 0.4,
                "quality_score": 0.95,
            },
        ]

        for task in sample_tasks:
            self.task_repository[task["task_id"]] = task

        logger.info(f"初始化了 {len(sample_tasks)} 个示例任务")

    async def get_adaptive_tasks(
        self, user_id: str, count: int = 5, include_prerequisites: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取自适应推荐的任务列表

        Args:
            user_id: 用户ID
            count: 推荐任务数量
            include_prerequisites: 是否包含前置任务

        Returns:
            推荐的任务列表
        """
        # 获取用户当前难度
        difficulty_score, difficulty_level = (
            self.difficulty_service.get_user_difficulty_level(user_id)
        )

        # 获取适合的任务
        available_tasks = list(self.task_repository.values())
        suitable_tasks = self.difficulty_service.get_suitable_tasks(
            user_id, available_tasks, count * 2  # 多取一些用于筛选
        )

        # 过滤和排序任务
        filtered_tasks = self._filter_and_sort_tasks(
            user_id, suitable_tasks, difficulty_score, include_prerequisites
        )

        # 限制返回数量
        recommended_tasks = filtered_tasks[:count]

        # 记录推荐日志
        task_ids = [task["task_id"] for task in recommended_tasks]
        logger.info(f"为用户 {user_id} 推荐任务: {task_ids}")

        return recommended_tasks

    def _filter_and_sort_tasks(
        self,
        user_id: str,
        tasks: List[Dict[str, Any]],
        user_difficulty: float,
        include_prerequisites: bool,
    ) -> List[Dict[str, Any]]:
        """过滤和排序任务"""
        # 获取用户已完成的任务
        user_profile = self.difficulty_service.get_user_profile(user_id)
        completed_task_ids = set()
        if user_profile:
            completed_task_ids = {
                history.task_id for history in user_profile.task_history
            }

        filtered_tasks = []
        for task in tasks:
            # 跳过已完成的任务
            if task["task_id"] in completed_task_ids:
                continue

            # 检查前置任务
            if not include_prerequisites:
                prerequisites_met = all(
                    prereq in completed_task_ids
                    for prereq in task.get("prerequisites", [])
                )
                if not prerequisites_met:
                    continue

            # 计算匹配度分数
            match_score = self._calculate_match_score(
                task, user_difficulty, completed_task_ids
            )
            task["match_score"] = match_score
            filtered_tasks.append(task)

        # 按匹配度排序
        return sorted(filtered_tasks, key=lambda x: x["match_score"], reverse=True)

    def _calculate_match_score(
        self, task: Dict[str, Any], user_difficulty: float, completed_tasks: Set[str]
    ) -> float:
        """计算任务匹配度分数"""
        # 难度匹配度 (最重要的因素)
        task_difficulty = task["difficulty_score"]
        difficulty_match = 10 - abs(task_difficulty - user_difficulty)

        # 前置任务完成度
        prerequisites = task.get("prerequisites", [])
        if prerequisites:
            completed_prereqs = sum(1 for p in prerequisites if p in completed_tasks)
            prereq_completion = completed_prereqs / len(prerequisites)
        else:
            prereq_completion = 1.0

        # 任务质量
        quality_score = task.get("quality_score", 0.5)

        # 任务热度
        popularity_score = task.get("popularity_score", 0.5)

        # 综合评分 (加权平均)
        total_score = (
            difficulty_match * 0.5  # 50% 权重给难度匹配
            + prereq_completion * 0.2  # 20% 权重给前置任务
            + quality_score * 0.2  # 20% 权重给质量
            + popularity_score * 0.1  # 10% 权重给热度
        )

        return total_score

    async def adjust_task_difficulty(
        self,
        user_id: str,
        task_id: str,
        performance_metrics: TaskPerformanceMetrics,
        success: bool,
    ) -> Tuple[float, str]:
        """
        调整任务难度并更新用户档案

        Args:
            user_id: 用户ID
            task_id: 任务ID
            performance_metrics: 表现指标
            success: 是否成功

        Returns:
            Tuple[新的难度分数, 调整原因]
        """
        # 更新用户表现
        new_score, new_level = self.difficulty_service.update_user_performance(
            user_id, task_id, performance_metrics, success
        )

        # 触发规则引擎处理
        event_data = {
            "success": success,
            "completion_time": performance_metrics.average_completion_time,
            "hint_used": performance_metrics.hint_usage_count > 0,
            "retry_count": performance_metrics.retry_count,
            "hardware_success_rate": performance_metrics.calculate_hardware_success_rate(),
            "debugging_efficiency": performance_metrics.calculate_debugging_efficiency(),
        }

        await self.rule_engine_service.process_user_event(
            user_id=user_id,
            event_type="task_completed",
            event_data=event_data,
            task_id=task_id,
        )

        # 确定调整原因
        adjustment_reason = "skill_improvement"
        if not success and performance_metrics.retry_count > 2:
            adjustment_reason = "difficulty_too_high"
        elif success and performance_metrics.average_completion_time < 10:
            adjustment_reason = "high_proficiency"

        return new_score, adjustment_reason

    async def get_next_recommended_task(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的下一个推荐任务

        Args:
            user_id: 用户ID

        Returns:
            推荐任务或None
        """
        recommended_tasks = await self.get_adaptive_tasks(user_id, count=1)
        return recommended_tasks[0] if recommended_tasks else None

    def get_task_progression_path(
        self, user_id: str, target_level: str = "L5"
    ) -> List[Dict[str, Any]]:
        """
        获取用户的学习路径

        Args:
            user_id: 用户ID
            target_level: 目标难度等级

        Returns:
            学习路径任务列表
        """
        # 这是一个简化的实现，实际应该使用更复杂的路径规划算法
        all_tasks = sorted(
            self.task_repository.values(), key=lambda x: x["difficulty_score"]
        )

        # 获取用户已完成的任务
        user_profile = self.difficulty_service.get_user_profile(user_id)
        completed_tasks = set()
        if user_profile:
            completed_tasks = {history.task_id for history in user_profile.task_history}

        path = []
        for task in all_tasks:
            # 只包含未完成且符合难度要求的任务
            if (
                task["task_id"] not in completed_tasks
                and task["difficulty_level"] <= target_level
            ):
                path.append(
                    {
                        "task_id": task["task_id"],
                        "title": task["title"],
                        "difficulty_level": task["difficulty_level"],
                        "estimated_time": task["estimated_time"],
                        "prerequisites_met": all(
                            prereq in completed_tasks
                            for prereq in task.get("prerequisites", [])
                        ),
                    }
                )

        return path

    async def simulate_user_session(
        self, user_id: str, session_duration: int = 120  # 分钟
    ) -> Dict[str, Any]:
        """
        模拟用户学习会话

        Args:
            user_id: 用户ID
            session_duration: 会话时长(分钟)

        Returns:
            会话统计信息
        """
        session_start = datetime.now()
        completed_tasks = []
        total_time_spent = 0

        while total_time_spent < session_duration:
            # 获取推荐任务
            next_task = await self.get_next_recommended_task(user_id)
            if not next_task:
                break

            estimated_time = next_task["estimated_time"]
            remaining_time = session_duration - total_time_spent

            # 如果剩余时间不够完成任务，结束会话
            if estimated_time > remaining_time:
                break

            # 模拟任务完成
            success_probability = 0.8  # 基础成功率
            # 根据难度调整成功率
            difficulty_factor = next_task["difficulty_score"] / 10
            success_probability *= 1 - difficulty_factor * 0.5

            success = random.random() < success_probability

            # 创建表现指标
            metrics = TaskPerformanceMetrics(
                user_id=user_id,
                task_id=next_task["task_id"],
                success_rate=1.0 if success else 0.5,
                average_completion_time=float(estimated_time),
                hint_usage_count=0 if success else random.randint(1, 3),
                retry_count=0 if success else random.randint(1, 2),
                hardware_metrics=[],
                debugging_sessions=[],
                timestamp=datetime.now(),
            )

            # 调整难度
            new_score, reason = await self.adjust_task_difficulty(
                user_id, next_task["task_id"], metrics, success
            )

            completed_tasks.append(
                {
                    "task_id": next_task["task_id"],
                    "title": next_task["title"],
                    "success": success,
                    "time_spent": estimated_time,
                    "difficulty_adjustment": new_score,
                    "reason": reason,
                }
            )

            total_time_spent += estimated_time

            # 短暂延迟模拟真实场景
            await asyncio.sleep(0.1)

        # 生成会话报告
        session_end = datetime.now()
        success_count = sum(1 for task in completed_tasks if task["success"])

        return {
            "user_id": user_id,
            "session_start": session_start.isoformat(),
            "session_end": session_end.isoformat(),
            "duration_minutes": total_time_spent,
            "tasks_completed": len(completed_tasks),
            "success_rate": (
                success_count / len(completed_tasks) if completed_tasks else 0
            ),
            "completed_tasks": completed_tasks,
            "final_difficulty_score": self.difficulty_service.get_user_difficulty_level(
                user_id
            )[0],
        }


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_adaptive_service():
        # 创建依赖服务
        difficulty_service = DifficultyService()
        rule_engine_service = RuleEngineService()

        # 创建自适应任务服务
        service = AdaptiveTaskService(difficulty_service, rule_engine_service)

        print("=== 自适应任务服务测试 ===")

        # 测试任务推荐
        user_id = "test_user_001"
        recommended_tasks = await service.get_adaptive_tasks(user_id, count=3)

        print(f"为用户 {user_id} 推荐了 {len(recommended_tasks)} 个任务:")
        for task in recommended_tasks:
            print(
                f"  - {task['title']} (难度: {task['difficulty_level']}, 匹配度: {task['match_score']:.2f})"
            )

        # 测试难度调整
        from models.difficulty_level import DebuggingSession, HardwareOperationMetric

        metrics = TaskPerformanceMetrics(
            user_id=user_id,
            task_id="test_task_001",
            success_rate=0.9,
            average_completion_time=25.0,
            hint_usage_count=0,
            retry_count=0,
            hardware_metrics=[],
            debugging_sessions=[],
            timestamp=datetime.now(),
        )

        new_score, reason = await service.adjust_task_difficulty(
            user_id, "test_task_001", metrics, True
        )
        print(f"\n难度调整: 新分数={new_score:.2f}, 原因={reason}")

        # 测试学习路径
        path = service.get_task_progression_path(user_id, "L3")
        print(f"\n学习路径 ({len(path)} 个任务):")
        for task in path:
            status = "✓" if task["prerequisites_met"] else "○"
            print(f"  {status} {task['title']} ({task['difficulty_level']})")

        # 测试模拟会话
        print("\n开始模拟学习会话...")
        session_report = await service.simulate_user_session(
            user_id, session_duration=60
        )
        print(f"会话完成:")
        print(f"  完成任务数: {session_report['tasks_completed']}")
        print(f"  成功率: {session_report['success_rate']:.2%}")
        print(f"  最终难度: {session_report['final_difficulty_score']:.2f}")

    # 运行测试
    asyncio.run(test_adaptive_service())
