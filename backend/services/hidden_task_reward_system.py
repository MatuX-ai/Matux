import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import random
from typing import Any, Dict, List, Optional

from ..utils.blockchain_client import BlockchainClient
from .achievement_badge_system import AchievementBadge, achievement_system
from .reward_event_bus import RewardEvent, reward_event_bus

logger = logging.getLogger(__name__)


class HiddenTaskType(Enum):
    """隐藏任务类型"""

    GESTURE_SEQUENCE = "gesture_sequence"
    TIME_BASED = "time_based"
    COMBO_CHALLENGE = "combo_challenge"
    SPEED_RUN = "speed_run"
    PERFECTIONIST = "perfectionist"
    COLLECTOR = "collector"


@dataclass
class HiddenTask:
    """隐藏任务数据类"""

    task_id: str
    name: str
    description: str
    task_type: HiddenTaskType
    trigger_conditions: Dict[str, Any]
    reward_structure: Dict[str, Any]
    difficulty_level: int  # 1-5级
    is_active: bool
    activation_time: Optional[datetime]
    expiration_time: Optional[datetime]
    unlock_requirements: List[str]  # 需要先解锁的任务ID


@dataclass
class UserHiddenTaskProgress:
    """用户隐藏任务进度"""

    user_id: int
    task_id: str
    progress: float  # 0.0 - 1.0
    attempts: int
    best_score: float
    unlocked_at: Optional[datetime]
    completed_at: Optional[datetime]
    rewards_claimed: bool


class HiddenTaskRewardSystem:
    """隐藏任务奖励系统"""

    def __init__(self):
        self.tasks: Dict[str, HiddenTask] = {}
        self.user_progress: Dict[int, Dict[str, UserHiddenTaskProgress]] = {}
        self.blockchain_client = BlockchainClient()
        self._initialize_hidden_tasks()
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """设置事件处理器"""
        reward_event_bus.subscribe(
            "complex_gesture_sequence", self.handle_gesture_sequence
        )
        reward_event_bus.subscribe(
            "hidden_task_completed", self.handle_hidden_task_completion
        )
        reward_event_bus.subscribe(
            "ar_scene_completed", self.handle_ar_completion_for_tasks
        )

    def _initialize_hidden_tasks(self):
        """初始化隐藏任务"""
        hidden_tasks = [
            HiddenTask(
                task_id="ht_gesture_master",
                name="手势大师",
                description="连续完成3个不同的复杂手势序列",
                task_type=HiddenTaskType.GESTURE_SEQUENCE,
                trigger_conditions={
                    "sequences_required": 3,
                    "time_window": 300,  # 5分钟内
                    "different_sequences": True,
                },
                reward_structure={
                    "base_points": 200,
                    "bonus_multiplier": 1.5,
                    "achievements": ["gesture_master"],
                    "special_items": ["golden_cursor"],
                },
                difficulty_level=3,
                is_active=True,
                activation_time=datetime.now(),
                expiration_time=datetime.now() + timedelta(days=30),
                unlock_requirements=[],
            ),
            HiddenTask(
                task_id="ht_speed_demon",
                name="速度恶魔",
                description="在60秒内完成AR场景构建",
                task_type=HiddenTaskType.SPEED_RUN,
                trigger_conditions={"max_time": 60, "accuracy_threshold": 85.0},  # 秒
                reward_structure={
                    "base_points": 300,
                    "time_bonus": 50,  # 每提前10秒加50分
                    "achievements": ["speed_demon"],
                    "special_items": ["time_crystal"],
                },
                difficulty_level=4,
                is_active=True,
                activation_time=datetime.now(),
                expiration_time=None,  # 永久任务
                unlock_requirements=["ht_gesture_master"],
            ),
            HiddenTask(
                task_id="ht_perfectionist",
                name="完美主义者",
                description="连续5次AR场景完成准确率达到95%以上",
                task_type=HiddenTaskType.PERFECTIONIST,
                trigger_conditions={
                    "consecutive_completions": 5,
                    "accuracy_threshold": 95.0,
                },
                reward_structure={
                    "base_points": 500,
                    "accuracy_bonus": 100,
                    "achievements": ["perfectionist"],
                    "special_items": ["diamond_toolkit"],
                },
                difficulty_level=5,
                is_active=True,
                activation_time=datetime.now(),
                expiration_time=None,
                unlock_requirements=["ht_speed_demon"],
            ),
            HiddenTask(
                task_id="ht_secret_combo",
                name="秘密连击",
                description="在一次会话中完成特定的手势组合：V字→OK→竖拇指→手掌",
                task_type=HiddenTaskType.COMBO_CHALLENGE,
                trigger_conditions={
                    "gesture_sequence": [
                        "v_shape",
                        "ok_sign",
                        "thumbs_up",
                        "palm_open",
                    ],
                    "max_interval": 10,  # 手势间最大间隔10秒
                },
                reward_structure={
                    "base_points": 150,
                    "combo_bonus": 75,
                    "achievements": ["combo_master"],
                    "special_items": ["combo_amulet"],
                },
                difficulty_level=2,
                is_active=True,
                activation_time=datetime.now(),
                expiration_time=datetime.now() + timedelta(days=7),
                unlock_requirements=[],
            ),
        ]

        for task in hidden_tasks:
            self.tasks[task.task_id] = task

    async def handle_gesture_sequence(self, event: RewardEvent):
        """处理复杂手势序列事件"""
        try:
            user_id = event.user_id
            sequence_name = event.data.get("sequence_name")
            confidence = event.data.get("confidence", 0)

            # 检查相关隐藏任务
            triggered_tasks = self._check_gesture_related_tasks(
                user_id, sequence_name, confidence
            )

            for task_id in triggered_tasks:
                await self._process_task_progress(user_id, task_id, event.data)

        except Exception as e:
            logger.error(f"处理手势序列事件失败: {e}")

    async def handle_hidden_task_completion(self, event: RewardEvent):
        """处理隐藏任务完成事件"""
        try:
            user_id = event.user_id
            task_name = event.data.get("task_name")

            # 查找对应的任务ID
            task_id = self._find_task_id_by_name(task_name)
            if not task_id:
                return

            # 发放奖励
            await self._award_hidden_task_rewards(user_id, task_id, event.data)

        except Exception as e:
            logger.error(f"处理隐藏任务完成事件失败: {e}")

    async def handle_ar_completion_for_tasks(self, event: RewardEvent):
        """处理AR完成事件对隐藏任务的影响"""
        try:
            user_id = event.user_id
            completion_data = event.data

            # 检查时间挑战任务
            await self._check_speed_run_tasks(user_id, completion_data)

            # 检查完美主义任务
            await self._check_perfectionist_tasks(user_id, completion_data)

        except Exception as e:
            logger.error(f"处理AR完成事件失败: {e}")

    def _check_gesture_related_tasks(
        self, user_id: int, sequence_name: str, confidence: float
    ) -> List[str]:
        """检查与手势相关的隐藏任务"""
        triggered_tasks = []

        for task_id, task in self.tasks.items():
            if task.task_type != HiddenTaskType.GESTURE_SEQUENCE:
                continue

            if not self._is_task_available(user_id, task_id):
                continue

            # 检查触发条件
            if self._meets_trigger_conditions(
                task, {"sequence_name": sequence_name, "confidence": confidence}
            ):
                triggered_tasks.append(task_id)

        return triggered_tasks

    async def _check_speed_run_tasks(
        self, user_id: int, completion_data: Dict[str, Any]
    ):
        """检查速度挑战任务"""
        completion_time = completion_data.get("completion_time", 999)

        for task_id, task in self.tasks.items():
            if task.task_type != HiddenTaskType.SPEED_RUN:
                continue

            if not self._is_task_available(user_id, task_id):
                continue

            if completion_time <= task.trigger_conditions.get("max_time", 999):
                accuracy = completion_data.get("accuracy", 0)
                if accuracy >= task.trigger_conditions.get("accuracy_threshold", 0):
                    await self._process_task_progress(user_id, task_id, completion_data)

    async def _check_perfectionist_tasks(
        self, user_id: int, completion_data: Dict[str, Any]
    ):
        """检查完美主义任务"""
        accuracy = completion_data.get("accuracy", 0)

        for task_id, task in self.tasks.items():
            if task.task_type != HiddenTaskType.PERFECTIONIST:
                continue

            if not self._is_task_available(user_id, task_id):
                continue

            if accuracy >= task.trigger_conditions.get("accuracy_threshold", 0):
                await self._process_task_progress(user_id, task_id, completion_data)

    def _is_task_available(self, user_id: int, task_id: str) -> bool:
        """检查任务是否可用"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # 检查任务激活状态
        if not task.is_active:
            return False

        # 检查时间限制
        now = datetime.now()
        if task.activation_time and now < task.activation_time:
            return False
        if task.expiration_time and now > task.expiration_time:
            return False

        # 检查前置任务要求
        for req_task_id in task.unlock_requirements:
            if not self._is_task_completed(user_id, req_task_id):
                return False

        return True

    def _is_task_completed(self, user_id: int, task_id: str) -> bool:
        """检查任务是否已完成"""
        if user_id not in self.user_progress:
            return False
        if task_id not in self.user_progress[user_id]:
            return False

        progress = self.user_progress[user_id][task_id]
        return progress.completed_at is not None

    def _meets_trigger_conditions(
        self, task: HiddenTask, event_data: Dict[str, Any]
    ) -> bool:
        """检查是否满足触发条件"""
        conditions = task.trigger_conditions

        if task.task_type == HiddenTaskType.GESTURE_SEQUENCE:
            sequence_name = event_data.get("sequence_name")
            required_sequences = conditions.get("sequences_required", 1)
            # 这里应该检查序列历史，简化实现
            return True

        elif task.task_type == HiddenTaskType.COMBO_CHALLENGE:
            # 检查手势组合序列
            return self._check_gesture_combo(event_data)

        return False

    def _check_gesture_combo(self, event_data: Dict[str, Any]) -> bool:
        """检查手势组合"""
        # 简化实现，实际应该维护手势序列历史
        return True

    async def _process_task_progress(
        self, user_id: int, task_id: str, event_data: Dict[str, Any]
    ):
        """处理任务进度"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}

        if task_id not in self.user_progress[user_id]:
            self.user_progress[user_id][task_id] = UserHiddenTaskProgress(
                user_id=user_id,
                task_id=task_id,
                progress=0.0,
                attempts=0,
                best_score=0.0,
                unlocked_at=datetime.now(),
                completed_at=None,
                rewards_claimed=False,
            )

        progress = self.user_progress[user_id][task_id]
        progress.attempts += 1

        # 更新进度
        new_progress = self._calculate_progress(task_id, event_data)
        progress.progress = max(progress.progress, new_progress)

        # 检查是否完成
        if progress.progress >= 1.0 and progress.completed_at is None:
            progress.completed_at = datetime.now()
            await self._on_task_completed(user_id, task_id)

    def _calculate_progress(self, task_id: str, event_data: Dict[str, Any]) -> float:
        """计算任务进度"""
        task = self.tasks[task_id]

        if task.task_type == HiddenTaskType.GESTURE_SEQUENCE:
            return min(
                1.0,
                event_data.get("sequence_count", 1)
                / task.trigger_conditions.get("sequences_required", 1),
            )

        elif task.task_type == HiddenTaskType.SPEED_RUN:
            max_time = task.trigger_conditions.get("max_time", 60)
            actual_time = event_data.get("completion_time", max_time)
            return max(0.0, 1.0 - (actual_time / max_time))

        return 0.0

    async def _on_task_completed(self, user_id: int, task_id: str):
        """任务完成回调"""
        logger.info(f"隐藏任务完成: 用户{user_id}, 任务{task_id}")

        # 发布任务完成事件
        event = RewardEvent(
            event_type="hidden_task_completed",
            user_id=user_id,
            data={"task_id": task_id, "completion_time": datetime.now().isoformat()},
            timestamp=datetime.now(),
        )

        await reward_event_bus.publish(event)

    async def _award_hidden_task_rewards(
        self, user_id: int, task_id: str, completion_data: Dict[str, Any]
    ):
        """发放隐藏任务奖励"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        reward_struct = task.reward_structure

        # 计算奖励积分
        base_points = reward_struct.get("base_points", 100)
        bonus_points = self._calculate_bonus_points(task_id, completion_data)
        total_points = base_points + bonus_points

        # 发放积分奖励
        await self._issue_integral_reward(
            user_id=user_id, amount=total_points, reason=f"隐藏任务奖励 - {task.name}"
        )

        # 解锁成就
        achievements = reward_struct.get("achievements", [])
        for achievement_id in achievements:
            # 这里应该调用成就系统
            pass

        # 发放特殊物品（如果有的话）
        special_items = reward_struct.get("special_items", [])
        for item in special_items:
            await self._grant_special_item(user_id, item)

        logger.info(
            f"隐藏任务奖励已发放: 用户{user_id}, 任务{task.name}, 总计{total_points}积分"
        )

    def _calculate_bonus_points(
        self, task_id: str, completion_data: Dict[str, Any]
    ) -> int:
        """计算奖励积分"""
        task = self.tasks[task_id]
        bonus_points = 0

        if task.task_type == HiddenTaskType.SPEED_RUN:
            completion_time = completion_data.get("completion_time", 999)
            max_time = task.trigger_conditions.get("max_time", 60)
            time_saved = max_time - completion_time
            bonus_points = int(time_saved / 10) * task.reward_structure.get(
                "time_bonus", 50
            )

        elif task.task_type == HiddenTaskType.PERFECTIONIST:
            bonus_points = task.reward_structure.get("accuracy_bonus", 100)

        elif task.task_type == HiddenTaskType.COMBO_CHALLENGE:
            bonus_points = task.reward_structure.get("combo_bonus", 75)

        return bonus_points

    async def _issue_integral_reward(self, user_id: int, amount: int, reason: str):
        """发放积分奖励"""
        try:
            result = await self.blockchain_client.invoke_integral_chaincode(
                function="issueIntegral", args=[str(user_id), str(amount), reason, "{}"]
            )

            if not result.get("success"):
                logger.error(f"积分奖励发放失败: {result.get('message')}")

        except Exception as e:
            logger.error(f"调用区块链积分系统失败: {e}")

    async def _grant_special_item(self, user_id: int, item_id: str):
        """发放特殊物品"""
        # 这里应该调用物品系统
        logger.info(f"特殊物品已发放: 用户{user_id}, 物品{item_id}")

    def _find_task_id_by_name(self, task_name: str) -> Optional[str]:
        """根据任务名称查找任务ID"""
        for task_id, task in self.tasks.items():
            if task.name.lower().replace(" ", "_") == task_name.lower():
                return task_id
        return None

    async def get_user_hidden_tasks(self, user_id: int) -> Dict[str, Any]:
        """获取用户隐藏任务状态"""
        available_tasks = []
        completed_tasks = []
        in_progress_tasks = []

        for task_id, task in self.tasks.items():
            if not self._is_task_available(user_id, task_id):
                continue

            task_status = {
                "task_id": task_id,
                "name": task.name,
                "description": task.description,
                "difficulty": task.difficulty_level,
                "reward_points": task.reward_structure.get("base_points", 100),
            }

            # 添加用户进度信息
            if user_id in self.user_progress and task_id in self.user_progress[user_id]:
                progress = self.user_progress[user_id][task_id]
                task_status.update(
                    {
                        "progress": progress.progress,
                        "attempts": progress.attempts,
                        "completed": progress.completed_at is not None,
                        "completion_time": (
                            progress.completed_at.isoformat()
                            if progress.completed_at
                            else None
                        ),
                    }
                )

                if progress.completed_at:
                    completed_tasks.append(task_status)
                else:
                    in_progress_tasks.append(task_status)
            else:
                available_tasks.append(task_status)

        return {
            "available_tasks": available_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "total_tasks": len(self.tasks),
            "unlocked_tasks": len(available_tasks)
            + len(in_progress_tasks)
            + len(completed_tasks),
        }


# 全局实例
hidden_task_system = HiddenTaskRewardSystem()
