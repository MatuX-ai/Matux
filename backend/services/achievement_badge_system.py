from dataclasses import asdict, dataclass
from datetime import datetime
import json
from typing import Any, Dict, List, Optional


@dataclass
class AchievementBadge:
    """成就徽章数据类"""

    badge_id: str
    name: str
    description: str
    icon_url: str
    rarity: str  # common, rare, epic, legendary
    point_value: int
    unlock_conditions: Dict[str, Any]
    created_at: datetime
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None


@dataclass
class UserAchievementProgress:
    """用户成就进度"""

    user_id: int
    badge_id: str
    progress: float  # 0.0 - 1.0
    last_updated: datetime
    unlock_data: Optional[Dict[str, Any]] = None


class AchievementBadgeSystem:
    """成就徽章管理系统"""

    def __init__(self):
        self.badges: Dict[str, AchievementBadge] = {}
        self.user_progress: Dict[int, Dict[str, UserAchievementProgress]] = {}
        self._initialize_default_badges()

    def _initialize_default_badges(self):
        """初始化默认成就徽章"""
        default_badges = [
            AchievementBadge(
                badge_id="first_placement",
                name="首次放置",
                description="成功放置第一个虚拟元件",
                icon_url="/badges/first_placement.png",
                rarity="common",
                point_value=10,
                unlock_conditions={"event_type": "component_placed", "count": 1},
                created_at=datetime.now(),
            ),
            AchievementBadge(
                badge_id="perfect_accuracy",
                name="精准大师",
                description="元件放置准确度达到95%以上",
                icon_url="/badges/perfect_accuracy.png",
                rarity="rare",
                point_value=50,
                unlock_conditions={
                    "event_type": "placement_validated",
                    "accuracy_threshold": 95.0,
                },
                created_at=datetime.now(),
            ),
            AchievementBadge(
                badge_id="speed_master",
                name="速度之王",
                description="在2分钟内完成AR场景",
                icon_url="/badges/speed_master.png",
                rarity="epic",
                point_value=100,
                unlock_conditions={
                    "event_type": "scene_completed",
                    "time_limit": 120,  # 秒
                },
                created_at=datetime.now(),
            ),
            AchievementBadge(
                badge_id="completion_master",
                name="完成大师",
                description="完成所有AR场景挑战",
                icon_url="/badges/completion_master.png",
                rarity="legendary",
                point_value=200,
                unlock_conditions={"event_type": "scenes_completed", "count": 10},
                created_at=datetime.now(),
            ),
            AchievementBadge(
                badge_id="voice_corrector",
                name="语音纠错专家",
                description="通过语音指令纠正5次硬件连接错误",
                icon_url="/badges/voice_corrector.png",
                rarity="rare",
                point_value=75,
                unlock_conditions={"event_type": "voice_corrections", "count": 5},
                created_at=datetime.now(),
            ),
        ]

        for badge in default_badges:
            self.badges[badge.badge_id] = badge

    def check_achievement_unlock(
        self, user_id: int, event_type: str, event_data: Dict[str, Any]
    ) -> List[AchievementBadge]:
        """检查成就解锁"""
        unlocked_badges = []

        for badge_id, badge in self.badges.items():
            if badge.is_unlocked:
                continue

            if self._check_unlock_conditions(badge, event_type, event_data):
                unlocked_badge = self._unlock_badge(user_id, badge_id, event_data)
                if unlocked_badge:
                    unlocked_badges.append(unlocked_badge)

        return unlocked_badges

    def _check_unlock_conditions(
        self, badge: AchievementBadge, event_type: str, event_data: Dict[str, Any]
    ) -> bool:
        """检查解锁条件"""
        conditions = badge.unlock_conditions

        if conditions.get("event_type") != event_type:
            return False

        # 根据不同事件类型检查条件
        if event_type == "component_placed":
            required_count = conditions.get("count", 1)
            current_count = self._get_user_component_count(event_data.get("user_id", 0))
            return current_count >= required_count

        elif event_type == "placement_validated":
            threshold = conditions.get("accuracy_threshold", 90.0)
            accuracy = event_data.get("accuracy", 0.0)
            return accuracy >= threshold

        elif event_type == "scene_completed":
            time_limit = conditions.get("time_limit", 300)
            completion_time = event_data.get("completion_time", 999)
            return completion_time <= time_limit

        elif event_type == "scenes_completed":
            required_count = conditions.get("count", 1)
            completed_count = event_data.get("completed_count", 0)
            return completed_count >= required_count

        elif event_type == "voice_corrections":
            required_count = conditions.get("count", 1)
            correction_count = event_data.get("correction_count", 0)
            return correction_count >= required_count

        return False

    def _unlock_badge(
        self, user_id: int, badge_id: str, unlock_data: Dict[str, Any]
    ) -> Optional[AchievementBadge]:
        """解锁成就徽章"""
        if badge_id not in self.badges:
            return None

        badge = self.badges[badge_id]
        if badge.is_unlocked:
            return None

        # 更新徽章状态
        badge.is_unlocked = True
        badge.unlocked_at = datetime.now()

        # 记录用户进度
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}

        self.user_progress[user_id][badge_id] = UserAchievementProgress(
            user_id=user_id,
            badge_id=badge_id,
            progress=1.0,
            last_updated=datetime.now(),
            unlock_data=unlock_data,
        )

        print(f"🎉 用户 {user_id} 解锁成就: {badge.name}")
        return badge

    def _get_user_component_count(self, user_id: int) -> int:
        """获取用户放置的组件数量（模拟实现）"""
        # 实际实现应该查询数据库
        return len(self.user_progress.get(user_id, {}))

    def get_user_achievements(self, user_id: int) -> List[AchievementBadge]:
        """获取用户已解锁的成就"""
        if user_id not in self.user_progress:
            return []

        unlocked_badges = []
        for badge_id in self.user_progress[user_id]:
            if badge_id in self.badges and self.badges[badge_id].is_unlocked:
                unlocked_badges.append(self.badges[badge_id])

        return unlocked_badges

    def get_user_progress(self, user_id: int) -> Dict[str, UserAchievementProgress]:
        """获取用户成就进度"""
        return self.user_progress.get(user_id, {})

    def get_badge_rarity_stats(self, user_id: int) -> Dict[str, int]:
        """获取用户徽章稀有度统计"""
        achievements = self.get_user_achievements(user_id)
        stats = {"common": 0, "rare": 0, "epic": 0, "legendary": 0}

        for badge in achievements:
            if badge.rarity in stats:
                stats[badge.rarity] += 1

        return stats

    def get_total_points(self, user_id: int) -> int:
        """获取用户总成就点数"""
        achievements = self.get_user_achievements(user_id)
        return sum(badge.point_value for badge in achievements)

    def add_custom_badge(self, badge: AchievementBadge) -> bool:
        """添加自定义成就徽章"""
        if badge.badge_id in self.badges:
            return False

        self.badges[badge.badge_id] = badge
        return True

    def serialize_state(self) -> str:
        """序列化系统状态"""
        state = {
            "badges": {k: asdict(v) for k, v in self.badges.items()},
            "user_progress": {},
        }

        # 序列化用户进度
        for user_id, progress_dict in self.user_progress.items():
            state["user_progress"][str(user_id)] = {
                badge_id: asdict(progress)
                for badge_id, progress in progress_dict.items()
            }

        return json.dumps(state, default=str, indent=2)

    def deserialize_state(self, state_json: str):
        """反序列化系统状态"""
        state = json.loads(state_json)

        # 恢复徽章
        for badge_id, badge_data in state["badges"].items():
            badge_data["created_at"] = datetime.fromisoformat(badge_data["created_at"])
            if badge_data["unlocked_at"]:
                badge_data["unlocked_at"] = datetime.fromisoformat(
                    badge_data["unlocked_at"]
                )
            self.badges[badge_id] = AchievementBadge(**badge_data)

        # 恢复用户进度
        for user_id_str, progress_dict in state["user_progress"].items():
            user_id = int(user_id_str)
            self.user_progress[user_id] = {}
            for badge_id, progress_data in progress_dict.items():
                progress_data["last_updated"] = datetime.fromisoformat(
                    progress_data["last_updated"]
                )
                self.user_progress[user_id][badge_id] = UserAchievementProgress(
                    **progress_data
                )


# 全局实例
achievement_system = AchievementBadgeSystem()
