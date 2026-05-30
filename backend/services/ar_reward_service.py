from dataclasses import dataclass
from datetime import datetime
import json
import logging
from typing import Any, Dict, List

from services.achievement_badge_system import AchievementBadge, achievement_system
from services.reward_event_bus import RewardEvent, RewardEventType, reward_event_bus

logger = logging.getLogger(__name__)


@dataclass
class ARSceneCompletionData:
    """AR场景完成数据"""

    user_id: int
    scene_id: str
    accuracy: float
    completion_time: float
    components_placed: int
    total_components: int
    bonus_points: int
    timestamp: datetime


class ARSceneRewardService:
    """AR场景奖励服务"""

    def __init__(self):
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """设置事件处理器"""
        reward_event_bus.subscribe(RewardEventType.AR_COMPONENT_PLACEMENT, self.handle_scene_completion)
        reward_event_bus.subscribe(
            RewardEventType.AR_COMPONENT_PLACEMENT, self.handle_component_validation
        )
        reward_event_bus.subscribe(
            RewardEventType.SYSTEM_NOTIFICATION, self.handle_achievement_unlock
        )

    async def handle_scene_completion(self, event: RewardEvent):
        """处理AR场景完成事件"""
        try:
            scene_data = ARSceneCompletionData(**event.data)

            # 计算基础奖励
            base_reward = self.calculate_base_reward(scene_data)

            # 检查成就解锁
            achievements = self.check_scene_achievements(scene_data)

            # 发放积分奖励
            await self.issue_integral_reward(
                user_id=scene_data.user_id,
                amount=base_reward + scene_data.bonus_points,
                reason=f"AR场景完成奖励 - 场景ID: {scene_data.scene_id}",
                metadata={
                    "scene_id": scene_data.scene_id,
                    "accuracy": scene_data.accuracy,
                    "completion_time": scene_data.completion_time,
                    "achievements_unlocked": [a.badge_id for a in achievements],
                },
            )

            # 触发成就解锁事件
            for achievement in achievements:
                await reward_event_bus.publish(
                    RewardEvent(
                        event_type="achievement_unlocked",
                        user_id=scene_data.user_id,
                        data={
                            "achievement_id": achievement.badge_id,
                            "achievement_name": achievement.name,
                            "point_value": achievement.point_value,
                            "rarity": achievement.rarity,
                        },
                        timestamp=datetime.now(),
                    )
                )

            logger.info(
                f"AR场景奖励已发放: 用户{scene_data.user_id}, 基础奖励{base_reward}, 额外奖励{scene_data.bonus_points}"
            )

        except Exception as e:
            logger.error(f"处理AR场景完成事件失败: {e}")

    async def handle_component_validation(self, event: RewardEvent):
        """处理元件验证事件"""
        try:
            user_id = event.user_id
            validation_data = event.data

            accuracy = validation_data.get("accuracy", 0)
            component_type = validation_data.get("component_type", "")

            # 高准确度奖励
            if accuracy >= 95:
                await self.issue_integral_reward(
                    user_id=user_id,
                    amount=20,
                    reason=f"高精度元件放置奖励 - {component_type}",
                    metadata={"accuracy": accuracy, "component_type": component_type},
                )

                logger.info(
                    f"高精度放置奖励已发放: 用户{user_id}, 元件{component_type}, 准确度{accuracy}%"
                )

            # 首次放置奖励
            if validation_data.get("is_first_placement", False):
                await self.issue_integral_reward(
                    user_id=user_id,
                    amount=10,
                    reason=f"首次元件放置奖励 - {component_type}",
                    metadata={"component_type": component_type},
                )

        except Exception as e:
            logger.error(f"处理元件验证事件失败: {e}")

    async def handle_achievement_unlock(self, event: RewardEvent):
        """处理成就解锁事件"""
        try:
            user_id = event.user_id
            achievement_data = event.data

            # 发放成就积分奖励
            await self.issue_integral_reward(
                user_id=user_id,
                amount=achievement_data["point_value"],
                reason=f"成就解锁奖励 - {achievement_data['achievement_name']}",
                metadata={
                    "achievement_id": achievement_data["achievement_id"],
                    "rarity": achievement_data["rarity"],
                },
            )

            # 发送成就通知
            await self.send_achievement_notification(user_id, achievement_data)

            logger.info(
                f"成就奖励已发放: 用户{user_id}, 成就{achievement_data['achievement_name']}"
            )

        except Exception as e:
            logger.error(f"处理成就解锁事件失败: {e}")

    def calculate_base_reward(self, scene_data: ARSceneCompletionData) -> int:
        """计算基础奖励积分"""
        base_points = 100  # 基础分数

        # 准确度奖励
        accuracy_bonus = 0
        if scene_data.accuracy >= 95:
            accuracy_bonus = 50
        elif scene_data.accuracy >= 90:
            accuracy_bonus = 30
        elif scene_data.accuracy >= 85:
            accuracy_bonus = 15

        # 完整性奖励
        completeness_bonus = 0
        if scene_data.components_placed >= scene_data.total_components:
            completeness_bonus = 30

        # 速度奖励
        speed_bonus = 0
        if scene_data.completion_time <= 120:  # 2分钟内
            speed_bonus = 40
        elif scene_data.completion_time <= 180:  # 3分钟内
            speed_bonus = 20

        return base_points + accuracy_bonus + completeness_bonus + speed_bonus

    def check_scene_achievements(
        self, scene_data: ARSceneCompletionData
    ) -> List[AchievementBadge]:
        """检查场景相关成就"""
        event_data = {
            "user_id": scene_data.user_id,
            "accuracy": scene_data.accuracy,
            "completion_time": scene_data.completion_time,
            "components_placed": scene_data.components_placed,
            "total_components": scene_data.total_components,
        }

        # 检查各种成就解锁条件
        unlocked_achievements = []

        # 完美准确度成就
        if scene_data.accuracy >= 95:
            perfect_accuracy_event = {"accuracy": scene_data.accuracy}
            achievements = achievement_system.check_achievement_unlock(
                scene_data.user_id, "placement_validated", perfect_accuracy_event
            )
            unlocked_achievements.extend(achievements)

        # 速度成就
        if scene_data.completion_time <= 120:
            speed_event = {"completion_time": scene_data.completion_time}
            achievements = achievement_system.check_achievement_unlock(
                scene_data.user_id, "scene_completed", speed_event
            )
            unlocked_achievements.extend(achievements)

        return unlocked_achievements

    async def issue_integral_reward(
        self, user_id: int, amount: int, reason: str, metadata: Dict[str, Any]
    ):
        """发放积分奖励"""
        try:
            # 调用区块链积分系统
            result = await self.blockchain_client.invoke_integral_chaincode(
                function="issueIntegral",
                args=[str(user_id), str(amount), reason, json.dumps(metadata)],
            )

            if result.get("success"):
                logger.info(f"积分奖励发放成功: 用户{user_id}, 数量{amount}")
            else:
                logger.error(f"积分奖励发放失败: {result.get('message')}")

        except Exception as e:
            logger.error(f"调用区块链积分系统失败: {e}")

    async def send_achievement_notification(
        self, user_id: int, achievement_data: Dict[str, Any]
    ):
        """发送成就通知"""
        try:
            notification_data = {
                "user_id": user_id,
                "type": "achievement_unlocked",
                "title": f"🎉 成就解锁 - {achievement_data['achievement_name']}",
                "message": f"恭喜您解锁了 '{achievement_data['achievement_name']}' 成就！",
                "icon": f"/badges/{achievement_data['achievement_id']}.png",
                "priority": "high",
                "metadata": {
                    "achievement_id": achievement_data["achievement_id"],
                    "rarity": achievement_data["rarity"],
                    "point_value": achievement_data["point_value"],
                },
            }

            # 发送到通知服务（需要实现）
            # await notification_service.send_notification(notification_data)

            logger.info(
                f"成就通知已发送: 用户{user_id}, 成就{achievement_data['achievement_name']}"
            )

        except Exception as e:
            logger.error(f"发送成就通知失败: {e}")

    async def get_user_ar_rewards_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户AR奖励摘要"""
        try:
            # 获取成就统计
            achievements = achievement_system.get_user_achievements(user_id)
            rarity_stats = achievement_system.get_badge_rarity_stats(user_id)
            total_points = achievement_system.get_total_points(user_id)

            # 获取最近的奖励记录（需要从区块链或数据库查询）
            recent_rewards = await self.get_recent_rewards(user_id, limit=10)

            return {
                "total_achievements": len(achievements),
                "rarity_distribution": rarity_stats,
                "total_achievement_points": total_points,
                "recent_rewards": recent_rewards,
                "unlocked_achievements": [
                    {
                        "id": badge.badge_id,
                        "name": badge.name,
                        "description": badge.description,
                        "rarity": badge.rarity,
                        "points": badge.point_value,
                        "unlocked_at": (
                            badge.unlocked_at.isoformat() if badge.unlocked_at else None
                        ),
                    }
                    for badge in achievements
                ],
            }

        except Exception as e:
            logger.error(f"获取用户AR奖励摘要失败: {e}")
            return {}

    async def get_recent_rewards(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的奖励记录"""
        # 这里需要实现从区块链或数据库查询奖励记录的逻辑
        # 暂时返回空列表
        return []


# 全局实例
ar_reward_service = ARSceneRewardService()
