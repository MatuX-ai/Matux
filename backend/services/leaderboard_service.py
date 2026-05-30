"""
AI-Edu 积分排行榜服务
提供积分统计、排行榜查询等功能
"""

from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from models.leaderboard import (
    LeaderboardPeriod,
    LeaderboardRecord,
    LeaderboardType,
    PointsTransaction,
    UserPoints,
    UserStatistics,
)
from models.user import User

logger = logging.getLogger(__name__)


class LeaderboardService:
    """排行榜服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 积分管理 ====================

    def get_user_points(self, user_id: int) -> UserPoints:
        """获取用户积分信息"""
        points = self.db.query(UserPoints).filter(UserPoints.user_id == user_id).first()

        if not points:
            # 创建默认积分记录
            points = UserPoints(user_id=user_id)
            self.db.add(points)
            self.db.commit()
            self.db.refresh(points)

        return points

    def add_points(
        self,
        user_id: int,
        amount: int,
        reason: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> UserPoints:
        """添加积分"""
        try:
            points = self.get_user_points(user_id)

            # 更新积分
            points.total_points += amount
            points.available_points += amount

            # 更新明细
            if reason not in points.points_breakdown:
                points.points_breakdown[reason] = 0
            points.points_breakdown[reason] += amount

            # 创建交易记录
            transaction = PointsTransaction(
                user_id=user_id,
                transaction_type="earn",
                points_amount=amount,
                balance_after=points.available_points,
                reason=reason,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
            )
            self.db.add(transaction)

            self.db.commit()
            self.db.refresh(points)

            logger.info(f"✅ 用户 {user_id} 获得 {amount} 积分，原因：{reason}")
            return points

        except Exception as e:
            logger.error(f"❌ 添加积分失败：{e}")
            self.db.rollback()
            raise

    def spend_points(
        self, user_id: int, amount: int, reason: str, description: Optional[str] = None
    ) -> UserPoints:
        """消费积分"""
        try:
            points = self.get_user_points(user_id)

            if points.available_points < amount:
                raise ValueError(
                    f"积分不足：当前可用 {points.available_points}，需要 {amount}"
                )

            # 更新积分
            points.total_points -= amount
            points.available_points -= amount
            points.consumed_points += amount

            # 创建交易记录
            transaction = PointsTransaction(
                user_id=user_id,
                transaction_type="spend",
                points_amount=amount,
                balance_after=points.available_points,
                reason=reason,
                description=description,
            )
            self.db.add(transaction)

            self.db.commit()
            self.db.refresh(points)

            logger.info(f"✅ 用户 {user_id} 消费 {amount} 积分，原因：{reason}")
            return points

        except Exception as e:
            logger.error(f"❌ 消费积分失败：{e}")
            self.db.rollback()
            raise

    def get_points_history(
        self, user_id: int, limit: int = 50, transaction_type: Optional[str] = None
    ) -> List[PointsTransaction]:
        """获取积分流水"""
        query = self.db.query(PointsTransaction).filter(
            PointsTransaction.user_id == user_id
        )

        if transaction_type:
            query = query.filter(PointsTransaction.transaction_type == transaction_type)

        query = query.order_by(desc(PointsTransaction.created_at))

        return query.limit(limit).all()

    # ==================== 用户统计 ====================

    def get_user_statistics(self, user_id: int) -> UserStatistics:
        """获取用户统计信息"""
        stats = (
            self.db.query(UserStatistics)
            .filter(UserStatistics.user_id == user_id)
            .first()
        )

        if not stats:
            # 创建默认统计记录
            stats = UserStatistics(user_id=user_id)
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)

        return stats

    def update_user_statistics(self, user_id: int) -> UserStatistics:
        """更新用户统计信息（从其他表聚合）"""
        from models.ai_edu_rewards import AIEduLearningProgress

        stats = self.get_user_statistics(user_id)

        # 从学习进度表聚合
        progress_query = (
            self.db.query(
                func.sum(AIEduLearningProgress.time_spent_seconds).label("total_time"),
                func.count(AIEduLearningProgress.id).label("total_courses"),
                func.sum(
                    func.case((AIEduLearningProgress.status == "completed", 1), else_=0)
                ).label("completed_courses"),
                func.avg(AIEduLearningProgress.quiz_score).label("avg_score"),
            )
            .filter(AIEduLearningProgress.user_id == user_id)
            .first()
        )

        if progress_query:
            stats.total_study_time_minutes = (progress_query.total_time or 0) // 60
            stats.courses_completed = progress_query.completed_courses or 0
            stats.average_quiz_score = round(progress_query.avg_score or 0, 2)

        # 从成就表聚合
        from models.achievement import UserAchievement

        stats.achievements_unlocked = (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.is_unlocked == True,
                )
            )
            .count()
        )

        # 更新活跃统计（简化实现）
        stats.last_active_date = datetime.utcnow()

        self.db.commit()
        self.db.refresh(stats)

        return stats

    # ==================== 排行榜查询 ====================

    def _get_previous_period_records(self, period: LeaderboardPeriod) -> Dict[int, int]:
        """
        获取上一期的排名记录

        Args:
            period: 当前周期

        Returns:
            用户 ID 到排名的映射字典 {user_id: rank}
        """
        from models.leaderboard import LeaderboardRecord as LeaderboardRecordModel

        # 计算上一期的时间范围
        now = datetime.now()

        if period == LeaderboardPeriod.DAILY:
            # 上一天
            prev_day = now - timedelta(days=1)
            period_start = prev_day.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = prev_day.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        elif period == LeaderboardPeriod.WEEKLY:
            # 上上周
            days_since_monday = now.weekday()
            last_monday = now - timedelta(days=days_since_monday + 7)
            period_start = last_monday.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(days=7, microseconds=-1)
        elif period == LeaderboardPeriod.MONTHLY:
            # 上个月
            if now.month == 1:
                prev_year = now.year - 1
                prev_month = 12
            else:
                prev_year = now.year
                prev_month = now.month - 1

            period_start = datetime(prev_year, prev_month, 1, 0, 0, 0, 0)
            if prev_month == 12:
                next_month = datetime(prev_year + 1, 1, 1, 0, 0, 0, 0)
            else:
                next_month = datetime(prev_year, prev_month + 1, 1, 0, 0, 0, 0)
            period_end = next_month - timedelta(microseconds=1)
        else:
            # ALL_TIME 没有"上一期"的概念
            return {}

        # 查询上一期排行榜记录
        query = self.db.query(LeaderboardRecordModel).filter(
            LeaderboardRecordModel.period == period.value,
            LeaderboardRecordModel.period_start >= period_start,
            LeaderboardRecordModel.period_start <= period_end,
        )

        # 构建 {user_id: rank} 映射
        previous_records = {}
        for record in query.all():
            previous_records[record.user_id] = record.rank

        return previous_records

    def get_leaderboard(
        self,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME,
        limit: int = 100,
        org_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取排行榜

        Args:
            leaderboard_type: 排行榜类型
            period: 周期
            limit: 返回数量
            org_id: 组织 ID（可选，用于过滤）

        Returns:
            排行榜列表
        """
        # 查询上一期排名记录（用于计算 rank_change）
        previous_records = self._get_previous_period_records(period)

        # 根据类型选择不同的数据源
        if leaderboard_type == LeaderboardType.TOTAL_POINTS:
            return self._get_points_leaderboard(period, limit, org_id, previous_records)
        elif leaderboard_type == LeaderboardType.STUDY_TIME:
            return self._get_study_time_leaderboard(
                period, limit, org_id, previous_records
            )
        elif leaderboard_type == LeaderboardType.COURSES_COMPLETED:
            return self._get_courses_leaderboard(
                period, limit, org_id, previous_records
            )
        elif leaderboard_type == LeaderboardType.QUIZ_SCORE:
            return self._get_quiz_score_leaderboard(
                period, limit, org_id, previous_records
            )
        elif leaderboard_type == LeaderboardType.ACHIEVEMENTS:
            return self._get_achievements_leaderboard(
                period, limit, org_id, previous_records
            )
        elif leaderboard_type == LeaderboardType.CODE_EXECUTIONS:
            return self._get_code_executions_leaderboard(
                period, limit, org_id, previous_records
            )
        else:
            return []

    def _get_points_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """积分排行榜"""
        query = self.db.query(
            UserPoints.user_id, UserPoints.total_points.label("score"), User
        ).join(User, User.id == UserPoints.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        query = query.order_by(desc(UserPoints.total_points))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(
            results, "total_points", previous_records
        )

    def _get_study_time_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """学习时长排行榜"""
        query = self.db.query(
            UserStatistics.user_id,
            UserStatistics.total_study_time_minutes.label("score"),
            User,
        ).join(User, User.id == UserStatistics.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        query = query.order_by(desc(UserStatistics.total_study_time_minutes))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(results, "study_time", previous_records)

    def _get_courses_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """完成课程数排行榜"""
        query = self.db.query(
            UserStatistics.user_id,
            UserStatistics.courses_completed.label("score"),
            User,
        ).join(User, User.id == UserStatistics.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        query = query.order_by(desc(UserStatistics.courses_completed))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(
            results, "courses_completed", previous_records
        )

    def _get_quiz_score_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """测验平均分排行榜"""
        query = self.db.query(
            UserStatistics.user_id,
            UserStatistics.average_quiz_score.label("score"),
            User,
        ).join(User, User.id == UserStatistics.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        # 只显示至少参加过 1 次测验的用户
        query = query.filter(UserStatistics.average_quiz_score > 0)
        query = query.order_by(desc(UserStatistics.average_quiz_score))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(results, "quiz_score", previous_records)

    def _get_achievements_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """成就数量排行榜"""
        query = self.db.query(
            UserStatistics.user_id,
            UserStatistics.achievements_unlocked.label("score"),
            User,
        ).join(User, User.id == UserStatistics.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        query = query.order_by(desc(UserStatistics.achievements_unlocked))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(
            results, "achievements", previous_records
        )

    def _get_code_executions_leaderboard(
        self,
        period: LeaderboardPeriod,
        limit: int,
        org_id: Optional[int],
        previous_records: Optional[Dict[int, int]] = None,
    ) -> List[Dict[str, Any]]:
        """代码执行次数排行榜"""
        query = self.db.query(
            UserStatistics.user_id, UserStatistics.code_executions.label("score"), User
        ).join(User, User.id == UserStatistics.user_id)

        if org_id:
            query = query.filter(User.org_id == org_id)

        query = query.order_by(desc(UserStatistics.code_executions))

        results = query.limit(limit).all()

        return self._format_leaderboard_results(
            results, "code_executions", previous_records
        )

    def _format_leaderboard_results(
        self,
        results: List[Tuple],
        score_type: str,
        previous_records: Optional[
            Dict[int, int]
        ] = None,  # 新增：上期排名 {user_id: rank}
    ) -> List[Dict[str, Any]]:
        """格式化排行榜结果

        Args:
            results: 查询结果元组列表
            score_type: 分数类型标识
            previous_records: 上一期排名记录，用于计算排名变化

        Returns:
            格式化的排行榜列表
        """
        leaderboard = []

        for rank, row in enumerate(results, 1):
            user_points, user = row[0], row[2]
            user_id = user_points.user_id

            # 计算排名变化
            if previous_records is None:
                rank_change = 0  # 无上期数据
            else:
                previous_rank = previous_records.get(user_id)
                if previous_rank is None:
                    rank_change = 0  # 新用户
                else:
                    rank_change = previous_rank - rank  # 正数表示排名上升

            leaderboard.append(
                {
                    "rank": rank,
                    "user_id": user_id,
                    "username": (
                        user.username if hasattr(user, "username") else f"User{user_id}"
                    ),
                    "score": (
                        user_points.score
                        if hasattr(user_points, "score")
                        else user_points.total_points
                    ),
                    "score_type": score_type,
                    "rank_change": rank_change,  # ✅ 已计算排名变化
                }
            )

        return leaderboard

    def get_user_rank(
        self,
        user_id: int,
        leaderboard_type: LeaderboardType,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME,
    ) -> Dict[str, Any]:
        """获取用户在排行榜中的排名"""
        # 获取完整排行榜
        leaderboard = self.get_leaderboard(leaderboard_type, period, limit=1000)

        # 找到自己的排名
        user_rank = None
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                user_rank = entry
                break

        if not user_rank:
            # 如果不在前 1000 名，单独计算
            return {"user_id": user_id, "rank": ">1000", "score": 0}

        return user_rank

    # ==================== 定时任务 ====================

    def refresh_daily_leaderboard(self):
        """刷新日榜（每天凌晨执行）"""
        self._refresh_periodic_leaderboard(LeaderboardPeriod.DAILY)

    def refresh_weekly_leaderboard(self):
        """刷新周榜（每周一凌晨执行）"""
        self._refresh_periodic_leaderboard(LeaderboardPeriod.WEEKLY)

    def refresh_monthly_leaderboard(self):
        """刷新月榜（每月 1 号凌晨执行）"""
        self._refresh_periodic_leaderboard(LeaderboardPeriod.MONTHLY)

    def _calculate_period_start_end(
        self, period: LeaderboardPeriod
    ) -> Tuple[datetime, datetime]:
        """
        计算周期的开始和结束时间

        Args:
            period: 排行榜周期类型

        Returns:
            (period_start, period_end) 元组
        """
        now = datetime.utcnow()

        if period == LeaderboardPeriod.DAILY:
            # 日榜：当天 00:00:00 到 23:59:59
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        elif period == LeaderboardPeriod.WEEKLY:
            # 周榜：本周一 00:00:00 到 周日 23:59:59
            days_since_monday = now.weekday()  # Monday = 0, Sunday = 6
            monday = now - timedelta(days=days_since_monday)
            period_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            sunday = monday + timedelta(days=6)
            period_end = sunday.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

        elif period == LeaderboardPeriod.MONTHLY:
            # 月榜：本月 1 号 00:00:00 到 月末 23:59:59
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 下个月 1 号的前一秒
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            period_end = next_month - timedelta(microseconds=1)

        else:  # ALL_TIME
            # 总榜：从系统启动到现在
            period_start = datetime(2024, 1, 1)  # 系统启动时间
            period_end = now

        return period_start, period_end

    def _refresh_periodic_leaderboard(self, period: LeaderboardPeriod):
        """刷新周期性排行榜"""
        try:
            # 计算正确的周期时间范围
            period_start, period_end = self._calculate_period_start_end(period)

            logger.info(
                f"📊 刷新 {period.value} 排行榜，时间范围：{period_start} - {period_end}"
            )

            # 为每种类型生成排行榜快照
            for lb_type in LeaderboardType:
                leaderboard = self.get_leaderboard(lb_type.value, period, limit=100)

                # 获取上一期的排名用于计算变化
                previous_records = {}
                if period == LeaderboardPeriod.DAILY:
                    # 昨天的记录
                    prev_start = period_start - timedelta(days=1)
                    prev_end = period_start - timedelta(seconds=1)
                    prev_query = self.db.query(LeaderboardRecord).filter(
                        LeaderboardRecord.leaderboard_type == lb_type.value,
                        LeaderboardRecord.period == LeaderboardPeriod.DAILY.value,
                        LeaderboardRecord.period_start >= prev_start,
                        LeaderboardRecord.period_start <= prev_end,
                    )
                    for record in prev_query:
                        previous_records[record.user_id] = record.rank

                elif period == LeaderboardPeriod.WEEKLY:
                    # 上周的记录
                    prev_start = period_start - timedelta(weeks=1)
                    prev_end = period_start - timedelta(seconds=1)
                    prev_query = self.db.query(LeaderboardRecord).filter(
                        LeaderboardRecord.leaderboard_type == lb_type.value,
                        LeaderboardRecord.period == LeaderboardPeriod.WEEKLY.value,
                        LeaderboardRecord.period_start >= prev_start,
                        LeaderboardRecord.period_start <= prev_end,
                    )
                    for record in prev_query:
                        previous_records[record.user_id] = record.rank

                elif period == LeaderboardPeriod.MONTHLY:
                    # 上月的记录
                    if period_start.month == 1:
                        prev_year = period_start.year - 1
                        prev_month = 12
                    else:
                        prev_year = period_start.year
                        prev_month = period_start.month - 1

                    prev_start = period_start.replace(year=prev_year, month=prev_month)
                    prev_end = period_start - timedelta(seconds=1)
                    prev_query = self.db.query(LeaderboardRecord).filter(
                        LeaderboardRecord.leaderboard_type == lb_type.value,
                        LeaderboardRecord.period == LeaderboardPeriod.MONTHLY.value,
                        LeaderboardRecord.period_start >= prev_start,
                        LeaderboardRecord.period_start <= prev_end,
                    )
                    for record in prev_query:
                        previous_records[record.user_id] = record.rank

                # 保存到 LeaderboardRecord
                for entry in leaderboard:
                    user_id = entry["user_id"]
                    current_rank = entry["rank"]
                    previous_rank = previous_records.get(user_id)

                    # 计算排名变化
                    if previous_rank is None:
                        rank_change = 0  # 新用户，无变化
                    else:
                        rank_change = previous_rank - current_rank  # 正数表示排名上升

                    record = LeaderboardRecord(
                        user_id=user_id,
                        leaderboard_type=lb_type.value,
                        period=period.value,
                        period_start=period_start,
                        period_end=period_end,
                        rank=current_rank,
                        score=entry["score"],
                        rank_change=rank_change,
                    )
                    self.db.add(record)

                self.db.commit()
                logger.info(
                    f"✅ {period.value} {lb_type.value} 排行榜已刷新 ({len(leaderboard)} 条记录)"
                )

        except Exception as e:
            logger.error(f"❌ 刷新排行榜失败：{e}", exc_info=True)
            self.db.rollback()


def get_leaderboard_service(db: Session) -> LeaderboardService:
    """获取排行榜服务实例"""
    return LeaderboardService(db)
