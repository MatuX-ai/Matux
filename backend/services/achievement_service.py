"""
AI-Edu 成就系统服务层
提供成就管理、解锁判定、进度追踪等功能
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from models.achievement import (
    DEFAULT_ACHIEVEMENTS,
    Achievement,
    AchievementCategory,
    AchievementProgress,
    AchievementType,
    UserAchievement,
)
from models.user import User
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AchievementService:
    """成就服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 成就管理 ====================

    def create_achievement(self, achievement_data: Dict[str, Any]) -> Achievement:
        """创建新成就"""
        try:
            achievement = Achievement(**achievement_data)
            self.db.add(achievement)
            self.db.commit()
            self.db.refresh(achievement)

            logger.info(f"✅ 成就创建成功：{achievement.name} (ID={achievement.id})")
            return achievement

        except Exception as e:
            logger.error(f"❌ 创建成就失败：{e}")
            self.db.rollback()
            raise

    def update_achievement(
        self, achievement_id: int, updates: Dict[str, Any]
    ) -> Optional[Achievement]:
        """更新成就信息"""
        try:
            achievement = (
                self.db.query(Achievement)
                .filter(Achievement.id == achievement_id)
                .first()
            )

            if not achievement:
                return None

            for key, value in updates.items():
                if hasattr(achievement, key):
                    setattr(achievement, key, value)

            self.db.commit()
            self.db.refresh(achievement)

            logger.info(f"✅ 成就更新成功：{achievement.name}")
            return achievement

        except Exception as e:
            logger.error(f"❌ 更新成就失败：{e}")
            self.db.rollback()
            raise

    def delete_achievement(self, achievement_id: int) -> bool:
        """删除成就（软删除，设置 is_active=False）"""
        try:
            achievement = (
                self.db.query(Achievement)
                .filter(Achievement.id == achievement_id)
                .first()
            )

            if not achievement:
                return False

            achievement.is_active = False
            self.db.commit()

            logger.info(f"✅ 成就已停用：{achievement.name}")
            return True

        except Exception as e:
            logger.error(f"❌ 停用成就失败：{e}")
            self.db.rollback()
            raise

    def get_achievement(self, achievement_id: int) -> Optional[Achievement]:
        """获取单个成就详情"""
        return (
            self.db.query(Achievement).filter(Achievement.id == achievement_id).first()
        )

    def list_achievements(
        self,
        category: Optional[str] = None,
        achievement_type: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Achievement]:
        """获取成就列表（支持筛选）"""
        query = self.db.query(Achievement).filter(Achievement.is_active == is_active)

        if category:
            query = query.filter(Achievement.category == category)

        if achievement_type:
            query = query.filter(Achievement.achievement_type == achievement_type)

        query = query.order_by(Achievement.display_order, Achievement.id)

        return query.offset(offset).limit(limit).all()

    def initialize_default_achievements(self) -> int:
        """初始化预定义成就"""
        count = 0

        for achievement_data in DEFAULT_ACHIEVEMENTS:
            # 检查是否已存在
            existing = (
                self.db.query(Achievement)
                .filter(Achievement.name == achievement_data["name"])
                .first()
            )

            if not existing:
                self.create_achievement(achievement_data)
                count += 1

        logger.info(f"✅ 初始化了 {count} 个预定义成就")
        return count

    # ==================== 用户成就管理 ====================

    def get_user_achievements(
        self, user_id: int, include_locked: bool = True, include_hidden: bool = False
    ) -> List[UserAchievement]:
        """获取用户的成就列表"""
        query = (
            self.db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .join(UserAchievement.achievement)
        )

        if not include_locked:
            query = query.filter(UserAchievement.is_unlocked.is_(True))

        if not include_hidden:
            query = query.filter(
                or_(Achievement.is_hidden.is_(False), UserAchievement.is_unlocked.is_(True))
            )

        query = query.order_by(
            UserAchievement.is_unlocked.desc(), UserAchievement.unlocked_at.desc()
        )

        return query.all()

    def get_user_achievement(
        self, user_id: int, achievement_id: int
    ) -> Optional[UserAchievement]:
        """获取用户特定成就"""
        return (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement_id,
                )
            )
            .first()
        )

    def create_or_update_user_achievement(
        self, user_id: int, achievement_id: int, progress_data: Dict[str, Any]
    ) -> UserAchievement:
        """创建或更新用户成就进度"""
        user_achievement = self.get_user_achievement(user_id, achievement_id)

        if user_achievement:
            # 更新进度
            user_achievement.progress = progress_data.get(
                "progress", user_achievement.progress
            )
            user_achievement.current_value = progress_data.get(
                "current_value", user_achievement.current_value
            )
            user_achievement.updated_at = datetime.utcnow()
        else:
            # 创建新记录
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=progress_data.get("progress", 0.0),
                current_value=progress_data.get("current_value", 0),
                target_value=progress_data.get("target_value", 0),
            )
            self.db.add(user_achievement)

        self.db.commit()
        self.db.refresh(user_achievement)

        return user_achievement

    def unlock_achievement(self, user_id: int, achievement_id: int) -> UserAchievement:
        """解锁成就"""
        user_achievement = self.get_user_achievement(user_id, achievement_id)

        if not user_achievement:
            # 如果不存在，先创建
            achievement = self.get_achievement(achievement_id)
            if not achievement:
                raise ValueError(f"成就 {achievement_id} 不存在")

            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=100.0,
                current_value=achievement.unlock_condition.get("threshold", 0),
                target_value=achievement.unlock_condition.get("threshold", 0),
                is_unlocked=True,
                unlocked_at=datetime.utcnow(),
            )
            self.db.add(user_achievement)
        else:
            # 更新状态
            user_achievement.is_unlocked = True
            user_achievement.progress = 100.0
            user_achievement.unlocked_at = datetime.utcnow()

        # 更新成就的总解锁数
        achievement = self.get_achievement(achievement_id)
        if achievement:
            achievement.total_unlocked += 1
            # 计算解锁率（需要总用户数，这里简化处理）
            # achievement.unlock_rate = ...

        self.db.commit()
        self.db.refresh(user_achievement)

        # 【P3-A-1】异步重算全局统计（同步内联，但失败不影响主流程）
        try:
            self.recompute_global_stats(achievement_id)
            # 失效缓存
            from cache.achievement_stats_cache import invalidate_achievement_stats
            invalidate_achievement_stats(achievement_id)
        except Exception as e:
            logger.warning(f"⚠️  重算全局统计失败（不影响主流程）: {e}")

        # 【P3-A-2】发送解锁事件
        try:
            from services.gamification_event_bus import (
                gamification_event_bus,
                make_achievement_unlocked_payload,
            )

            gamification_event_bus.emit(
                user_id,
                "achievement_unlocked",
                make_achievement_unlocked_payload(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    name=achievement.name if achievement else f"Achievement-{achievement_id}",
                    rarity=achievement.badge_rarity if achievement else "common",
                    points=achievement.points_reward if achievement else 0,
                    icon=achievement.badge_icon if achievement else None,
                    description=achievement.description if achievement else None,
                ),
            )
        except Exception as e:
            logger.warning(f"⚠️  发送解锁事件失败（不影响主流程）: {e}")

        # 【P3-C】自动生成分享卡（仅首次解锁时）
        try:
            self._auto_create_share_card(user_id, achievement_id)
        except Exception as e:
            logger.warning(f"⚠️  自动生成分享卡失败（不影响主流程）: {e}")

        logger.info(
            f"🎉 用户 {user_id} 解锁了成就：{achievement.name if achievement else achievement_id}"
        )
        return user_achievement

    def _auto_create_share_card(self, user_id: int, achievement_id: int) -> None:
        """
        【P3-C】解锁成就后自动创建分享卡片

        策略：
        - 仅首次解锁时创建分享卡（去重）
        - 异常不影响主流程
        """
        from models.share import ShareCard, ShareCardType
        from services.share_service import ShareService

        # 检查是否已存在分享卡（同一用户同一成就只创建一次）
        existing = (
            self.db.query(ShareCard)
            .filter(
                ShareCard.card_type == ShareCardType.ACHIEVEMENT,
                ShareCard.target_id == achievement_id,
                ShareCard.creator_id == user_id,
            )
            .first()
        )
        if existing:
            logger.debug(f"用户 {user_id} 成就 {achievement_id} 已有分享卡 {existing.short_code}")
            return

        share_service = ShareService(self.db)
        card = share_service.create_card(
            card_type=ShareCardType.ACHIEVEMENT,
            target_id=achievement_id,
            creator_id=user_id,
        )
        logger.info(
            f"✅ 自动生成分享卡：用户 {user_id} 成就 {achievement_id} → {card.short_code}"
        )

    def claim_achievement_reward(
        self, user_id: int, achievement_id: int
    ) -> Dict[str, Any]:
        """领取成就奖励"""
        user_achievement = self.get_user_achievement(user_id, achievement_id)

        if not user_achievement:
            raise ValueError("成就未解锁")

        if not user_achievement.is_unlocked:
            raise ValueError("成就尚未解锁")

        if user_achievement.is_claimed:
            raise ValueError("奖励已领取")

        # 标记为已领取
        user_achievement.is_claimed = True
        self.db.commit()

        # 返回奖励信息
        achievement = self.get_achievement(achievement_id)
        reward_info = {
            "points": achievement.points_reward if achievement else 0,
            "badge": achievement.badge_icon if achievement else None,
            "message": f"恭喜获得成就：{achievement.name}" if achievement else "",
        }

        logger.info(f"✅ 用户 {user_id} 领取了成就奖励：{reward_info['points']} 积分")
        return reward_info

    # ==================== 成就进度追踪 ====================

    def update_progress(
        self,
        user_id: int,
        metric_name: str,
        metric_value: int,
        period_type: str = "all_time",
    ) -> List[Dict[str, Any]]:
        """
        更新用户指标进度，并检查是否解锁成就

        Returns:
            新解锁的成就列表
        """
        unlocked_achievements = []

        # 更新或创建进度记录
        progress_record = (
            self.db.query(AchievementProgress)
            .filter(
                and_(
                    AchievementProgress.user_id == user_id,
                    AchievementProgress.metric_name == metric_name,
                    AchievementProgress.period_type == period_type,
                )
            )
            .first()
        )

        if progress_record:
            progress_record.metric_value = metric_value
            progress_record.updated_at = datetime.utcnow()
        else:
            progress_record = AchievementProgress(
                user_id=user_id,
                metric_name=metric_name,
                metric_value=metric_value,
                period_type=period_type,
            )
            self.db.add(progress_record)

        self.db.commit()

        # 检查相关成就
        achievements_to_check = (
            self.db.query(Achievement)
            .filter(
                and_(
                    Achievement.is_active.is_(True),
                    Achievement.unlock_condition.has_key("metric"),
                    Achievement.unlock_condition["metric"].astext == metric_name,
                )
            )
            .all()
        )

        for achievement in achievements_to_check:
            condition = achievement.unlock_condition
            threshold = condition.get("threshold", 0)
            operator = condition.get("operator", ">=")

            # 判断是否满足条件
            should_unlock = False

            if operator == ">=" and metric_value >= threshold:
                should_unlock = True
            elif operator == ">" and metric_value > threshold:
                should_unlock = True
            elif operator == "==" and metric_value == threshold:
                should_unlock = True
            elif operator == "<=" and metric_value <= threshold:
                should_unlock = True
            elif operator == "<" and metric_value < threshold:
                should_unlock = True

            if should_unlock:
                # 检查用户是否已经解锁
                user_achievement = self.get_user_achievement(user_id, achievement.id)

                if not user_achievement or not user_achievement.is_unlocked:
                    # 解锁成就
                    unlocked = self.unlock_achievement(user_id, achievement.id)
                    unlocked_achievements.append(
                        {
                            "achievement": achievement.to_dict(),
                            "user_achievement": unlocked.to_dict(),
                        }
                    )

                    logger.info(
                        f"🎉 用户 {user_id} 因 {metric_name}={metric_value} 解锁了成就：{achievement.name}"
                    )

        return unlocked_achievements

    def get_progress_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户成就统计信息"""
        total_achievements = (
            self.db.query(Achievement).filter(Achievement.is_active.is_(True)).count()
        )

        unlocked_count = (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.is_unlocked.is_(True),
                )
            )
            .count()
        )

        claimed_count = (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.is_claimed.is_(True),
                )
            )
            .count()
        )

        # 按分类统计
        category_stats = {}
        for category in AchievementCategory:
            cat_total = (
                self.db.query(Achievement)
                .filter(Achievement.category == category, Achievement.is_active.is_(True))
                .count()
            )

            cat_unlocked = (
                self.db.query(UserAchievement)
                .join(UserAchievement.achievement)
                .filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.is_unlocked.is_(True),
                    Achievement.category == category,
                )
                .count()
            )

            category_stats[category.value] = {
                "total": cat_total,
                "unlocked": cat_unlocked,
                "rate": (
                    round(cat_unlocked / cat_total * 100, 2) if cat_total > 0 else 0
                ),
            }

        return {
            "total_achievements": total_achievements,
            "unlocked_count": unlocked_count,
            "claimed_count": claimed_count,
            "completion_rate": (
                round(unlocked_count / total_achievements * 100, 2)
                if total_achievements > 0
                else 0
            ),
            "category_breakdown": category_stats,
        }

    # ==================== 【P3-A-1】全局统计 ====================

    def recompute_global_stats(self, achievement_id: int) -> Dict[str, Any]:
        """
        异步重算单个成就的全局解锁率

        逻辑：
        - holders = 状态为 is_unlocked 的 UserAchievement 去重用户数
        - total_users = 平台中 is_active 用户总数
        - global_unlock_rate = holders / total_users
        """
        achievement = self.get_achievement(achievement_id)
        if not achievement:
            return {}

        try:
            total_users = (
                self.db.query(User)
                .filter(User.is_active.is_(True))  # noqa: E712
                .count()
            )
            holders = (
                self.db.query(UserAchievement.user_id)
                .filter(
                    and_(
                        UserAchievement.achievement_id == achievement_id,
                        UserAchievement.is_unlocked.is_(True),  # noqa: E712
                    )
                )
                .distinct()
                .count()
            )

            achievement.total_holders = holders
            achievement.global_unlock_rate = (
                (holders / total_users) if total_users > 0 else 0.0
            )
            achievement.stats_updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(achievement)

            logger.info(
                f"📊 成就 {achievement_id} 全局统计: holders={holders}/{total_users}, "
                f"rate={achievement.global_unlock_rate:.4f}"
            )
            return {
                "achievement_id": achievement_id,
                "global_unlock_rate": achievement.global_unlock_rate,
                "total_holders": holders,
                "total_users": total_users,
                "stats_updated_at": (
                    achievement.stats_updated_at.isoformat()
                    if achievement.stats_updated_at
                    else None
                ),
            }
        except Exception as e:
            logger.error(f"❌ recompute_global_stats 失败: {e}")
            self.db.rollback()
            return {}

    def get_badge_stats(
        self, achievement_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量获取成就的全局统计（带缓存）

        Args:
            achievement_ids: 可选，限定返回的成就 ID 列表

        Returns:
            包含 global_unlock_rate / total_holders / total_unlocked 的字典列表
        """
        from cache.achievement_stats_cache import (
            get_cached_batch_stats,
            set_cached_batch_stats,
        )

        # 尝试缓存
        cached = get_cached_batch_stats()
        if cached is not None:
            if achievement_ids is None:
                return cached
            id_set = set(achievement_ids)
            return [s for s in cached if s.get("id") in id_set]

        # 查询所有激活的成就
        query = self.db.query(Achievement).filter(Achievement.is_active.is_(True))  # noqa: E712
        if achievement_ids is not None:
            query = query.filter(Achievement.id.in_(achievement_ids))
        achievements = query.all()

        result: List[Dict[str, Any]] = []
        for ach in achievements:
            result.append(
                {
                    "id": ach.id,
                    "name": ach.name,
                    "rarity": ach.badge_rarity,
                    "total_unlocked": ach.total_unlocked or 0,
                    "unlock_rate": ach.unlock_rate or 0.0,
                    "global_unlock_rate": ach.global_unlock_rate or 0.0,
                    "total_holders": ach.total_holders or 0,
                    "stats_updated_at": (
                        ach.stats_updated_at.isoformat()
                        if ach.stats_updated_at
                        else None
                    ),
                }
            )

        # 缓存（仅完整结果）
        if achievement_ids is None:
            try:
                set_cached_batch_stats(result, ttl=60)
            except Exception as e:
                logger.warning(f"⚠️  缓存 batch stats 失败: {e}")

        return result

    def get_single_badge_stats(self, achievement_id: int) -> Optional[Dict[str, Any]]:
        """获取单个成就的统计（带缓存）"""
        from cache.achievement_stats_cache import (
            get_single_stats_cache_key,
            achievement_stats_cache,
        )

        cache_key = get_single_stats_cache_key(achievement_id)
        cached = achievement_stats_cache.get(cache_key)
        if cached is not None:
            return cached

        achievement = self.get_achievement(achievement_id)
        if not achievement:
            return None

        result = {
            "id": achievement.id,
            "name": achievement.name,
            "rarity": achievement.badge_rarity,
            "total_unlocked": achievement.total_unlocked or 0,
            "unlock_rate": achievement.unlock_rate or 0.0,
            "global_unlock_rate": achievement.global_unlock_rate or 0.0,
            "total_holders": achievement.total_holders or 0,
            "stats_updated_at": (
                achievement.stats_updated_at.isoformat()
                if achievement.stats_updated_at
                else None
            ),
        }
        try:
            achievement_stats_cache.set(cache_key, result, ttl=60)
        except Exception as e:
            logger.warning(f"⚠️  缓存 single stats 失败: {e}")
        return result


def get_achievement_service(db: Session) -> AchievementService:
    """获取成就服务实例"""
    return AchievementService(db)
