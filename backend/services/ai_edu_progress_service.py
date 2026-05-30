"""
AI-Edu-for-Kids 学习进度追踪服务
支持学习进度的上报、查询和统计分析
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.ai_edu_rewards import (
    AIEduLearningProgress,
    AIEduLesson,
    AIEduModule,
    AIEduPointsTransaction,
)
from models.recommendation import UserLearningProfile

logger = logging.getLogger(__name__)


class ProgressStatus:
    """学习进度状态常量"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class AIEduProgressService:
    """AI 课程学习进度服务"""

    def __init__(self, db_session: Session):
        """
        初始化进度服务

        Args:
            db_session: 数据库会话
        """
        self.db = db_session

    async def report_progress(
        self, user_id: int, lesson_id: int, progress_data: Dict[str, Any]
    ) -> AIEduLearningProgress:
        """
        上报学习进度

        Args:
            user_id: 用户 ID
            lesson_id: 课程 ID
            progress_data: 进度数据 {
                progress_percentage: int,
                time_spent_seconds: int,
                quiz_score: float,
                code_quality_score: float,
                status: str
            }

        Returns:
            更新后的进度记录
        """
        logger.info(f"用户{user_id}上报课程{lesson_id}进度")

        # 查找或创建进度记录
        progress = await self._get_or_create_progress(user_id, lesson_id)

        # 更新进度数据
        update_fields = [
            "progress_percentage",
            "time_spent_seconds",
            "quiz_score",
            "code_quality_score",
            "status",
            "attempt_count",
        ]

        for field in update_fields:
            if field in progress_data:
                setattr(progress, field, progress_data[field])

        # 更新时间戳
        if progress.status == ProgressStatus.NOT_STARTED:
            progress.start_time = datetime.utcnow()

        if progress.progress_percentage >= 100:
            progress.status = ProgressStatus.COMPLETED
            progress.completion_time = datetime.utcnow()

        progress.last_accessed_time = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(progress)
            logger.info(
                f"✅ 进度更新成功：用户{user_id}, 课程{lesson_id}, {progress.progress_percentage}%"
            )
        except Exception as e:
            logger.error(f"❌ 进度更新失败：{e}")
            self.db.rollback()
            raise

        return progress

    async def get_user_progress(
        self,
        user_id: int,
        module_id: Optional[int] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取用户学习进度

        Args:
            user_id: 用户 ID
            module_id: 模块 ID（可选，用于过滤）
            status_filter: 状态过滤（可选）

        Returns:
            进度列表
        """
        logger.info(f"查询用户{user_id}的学习进度")

        query = self.db.query(AIEduLearningProgress).filter(
            AIEduLearningProgress.user_id == user_id
        )

        if status_filter:
            query = query.filter(AIEduLearningProgress.status == status_filter)

        progress_records = query.all()

        results = []
        for progress in progress_records:
            # 获取课程信息
            lesson = (
                self.db.query(AIEduLesson)
                .filter(AIEduLesson.id == progress.lesson_id)
                .first()
            )

            if not lesson:
                continue

            # 如果指定了 module_id，进行过滤
            if module_id and lesson.module_id != module_id:
                continue

            # 获取模块信息
            module = (
                self.db.query(AIEduModule)
                .filter(AIEduModule.id == lesson.module_id)
                .first()
            )

            results.append(
                {
                    "progress_id": progress.id,
                    "lesson_id": lesson.id,
                    "lesson_code": lesson.lesson_code,
                    "lesson_title": lesson.title,
                    "module_id": module.id if module else None,
                    "module_name": module.name if module else None,
                    "progress_percentage": progress.progress_percentage,
                    "status": progress.status,
                    "time_spent_seconds": progress.time_spent_seconds,
                    "quiz_score": progress.quiz_score,
                    "code_quality_score": progress.code_quality_score,
                    "attempt_count": progress.attempt_count,
                    "points_earned": progress.points_earned,
                    "start_time": (
                        progress.start_time.isoformat() if progress.start_time else None
                    ),
                    "completion_time": (
                        progress.completion_time.isoformat()
                        if progress.completion_time
                        else None
                    ),
                    "last_accessed_time": progress.last_accessed_time.isoformat(),
                }
            )

        return results

    async def get_progress_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取进度统计信息

        Args:
            user_id: 用户 ID

        Returns:
            统计信息
        """
        logger.info(f"计算用户{user_id}的进度统计")

        # 总进度数
        total_progress = (
            self.db.query(AIEduLearningProgress)
            .filter(AIEduLearningProgress.user_id == user_id)
            .count()
        )

        # 各状态统计
        status_counts = (
            self.db.query(
                AIEduLearningProgress.status, func.count(AIEduLearningProgress.id)
            )
            .filter(AIEduLearningProgress.user_id == user_id)
            .group_by(AIEduLearningProgress.status)
            .all()
        )

        # 已完成课程数
        completed_count = (
            self.db.query(AIEduLearningProgress)
            .filter(
                and_(
                    AIEduLearningProgress.user_id == user_id,
                    AIEduLearningProgress.status == ProgressStatus.COMPLETED,
                )
            )
            .count()
        )

        # 总学习时长
        total_time = (
            self.db.query(func.sum(AIEduLearningProgress.time_spent_seconds))
            .filter(AIEduLearningProgress.user_id == user_id)
            .scalar()
            or 0
        )

        # 平均测验分数
        avg_quiz_score = (
            self.db.query(func.avg(AIEduLearningProgress.quiz_score))
            .filter(
                and_(
                    AIEduLearningProgress.user_id == user_id,
                    AIEduLearningProgress.quiz_score.isnot(None),
                )
            )
            .scalar()
            or 0
        )

        # 平均代码质量分数
        avg_code_score = (
            self.db.query(func.avg(AIEduLearningProgress.code_quality_score))
            .filter(
                and_(
                    AIEduLearningProgress.user_id == user_id,
                    AIEduLearningProgress.code_quality_score.isnot(None),
                )
            )
            .scalar()
            or 0
        )

        # 总积分
        total_points = (
            self.db.query(func.sum(AIEduLearningProgress.points_earned))
            .filter(AIEduLearningProgress.user_id == user_id)
            .scalar()
            or 0
        )

        return {
            "total_courses": total_progress,
            "completed_courses": completed_count,
            "in_progress_courses": sum(
                count
                for status, count in status_counts
                if status == ProgressStatus.IN_PROGRESS
            ),
            "not_started_courses": sum(
                count
                for status, count in status_counts
                if status == ProgressStatus.NOT_STARTED
            ),
            "total_time_seconds": total_time,
            "total_time_hours": round(total_time / 3600, 2),
            "average_quiz_score": round(avg_quiz_score, 2),
            "average_code_score": round(avg_code_score, 2),
            "total_points": total_points,
            "completion_rate": (
                round(completed_count / total_progress * 100, 2)
                if total_progress > 0
                else 0
            ),
        }

    async def complete_lesson_and_award_points(
        self, user_id: int, lesson_id: int, completion_data: Dict[str, Any]
    ) -> int:
        """
        完成课程并发放积分

        Args:
            user_id: 用户 ID
            lesson_id: 课程 ID
            completion_data: 完成数据 {
                quiz_score: float,
                code_quality_score: float,
                time_spent_seconds: int
            }

        Returns:
            获得的积分数
        """
        logger.info(f"用户{user_id}完成课程{lesson_id}，计算奖励")

        # 获取课程信息
        lesson = self.db.query(AIEduLesson).filter(AIEduLesson.id == lesson_id).first()

        if not lesson:
            raise ValueError(f"课程{lesson_id}不存在")

        # 更新进度为完成状态
        progress = await self.report_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress_data={
                "progress_percentage": 100,
                "status": ProgressStatus.COMPLETED,
                "quiz_score": completion_data.get("quiz_score"),
                "code_quality_score": completion_data.get("code_quality_score"),
                "time_spent_seconds": completion_data.get("time_spent_seconds", 0),
            },
        )

        # 计算积分奖励
        base_points = lesson.base_points

        # 获取用户年级，应用学段系数
        grade_multiplier = await self._get_grade_multiplier(user_id)

        # 质量系数
        quality_score = (
            completion_data.get("code_quality_score")
            or completion_data.get("quiz_score")
            or 0
        )
        if quality_score >= 90:
            quality_multiplier = 1.2
        elif quality_score >= 80:
            quality_multiplier = 1.1
        else:
            quality_multiplier = 1.0

        # 时间奖励（如果提前完成）
        time_bonus = 0
        if lesson.estimated_duration_minutes:
            standard_seconds = lesson.estimated_duration_minutes * 60
            actual_seconds = completion_data.get("time_spent_seconds", 0)
            if actual_seconds < standard_seconds:
                time_saved = standard_seconds - actual_seconds
                time_bonus = int(time_saved / 60 * 0.5)  # 每分钟节省奖励 0.5 积分

        # 总积分
        total_points = (
            int(base_points * grade_multiplier * quality_multiplier) + time_bonus
        )

        # 更新进度记录的积分
        progress.points_earned = total_points

        # 创建积分交易记录
        transaction = AIEduPointsTransaction(
            user_id=user_id,
            transaction_type="earn",
            points_amount=total_points,
            source_type="course_completion",
            source_id=lesson_id,
            source_description=f"完成课程：{lesson.title}",
            base_points=base_points,
            grade_multiplier=grade_multiplier,
            quality_bonus=int(base_points * (quality_multiplier - 1)),
            streak_bonus=time_bonus,
            final_points=total_points,
            status="completed",
        )

        try:
            self.db.add(transaction)
            self.db.commit()
            logger.info(f"✅ 课程完成奖励：用户{user_id}, +{total_points}积分")
        except Exception as e:
            logger.error(f"❌ 发放奖励失败：{e}")
            self.db.rollback()
            raise

        return total_points

    async def _get_or_create_progress(
        self, user_id: int, lesson_id: int
    ) -> AIEduLearningProgress:
        """获取或创建进度记录"""
        progress = (
            self.db.query(AIEduLearningProgress)
            .filter(
                and_(
                    AIEduLearningProgress.user_id == user_id,
                    AIEduLearningProgress.lesson_id == lesson_id,
                )
            )
            .first()
        )

        if not progress:
            progress = AIEduLearningProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                progress_percentage=0,
                status=ProgressStatus.NOT_STARTED,
                attempt_count=1,
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
        else:
            # 如果是重新开始，增加尝试次数
            if progress.status == ProgressStatus.NOT_STARTED:
                progress.attempt_count += 1

        return progress

    async def _get_grade_multiplier(self, user_id: int) -> float:
        """
        获取用户的学段系数

        Args:
            user_id: 用户 ID

        Returns:
            学段系数 (1.0-2.0)
        """
        try:
            # 从用户学习画像中获取年级水平
            profile = (
                self.db.query(UserLearningProfile)
                .filter(UserLearningProfile.user_id == user_id)
                .first()
            )

            if not profile or not profile.grade_level:
                # 如果没有画像或年级信息，返回默认系数 1.0
                return 1.0

            # 学段系数映射表
            grade_multipliers = {
                "G1-G2": 1.0,  # 小学 1-2 年级
                "G3-G4": 1.2,  # 小学 3-4 年级
                "G5-G6": 1.5,  # 小学 5-6 年级
                "G7-G9": 2.0,  # 初中 7-9 年级
                "G10-G12": 2.5,  # 高中 10-12 年级（预留）
            }

            # 获取对应的系数
            multiplier = grade_multipliers.get(profile.grade_level, 1.0)

            logger.info(
                f"用户{user_id}年级水平：{profile.grade_level}, 系数：{multiplier}"
            )
            return multiplier

        except Exception as e:
            logger.error(f"获取学段系数失败：{e}")
            # 出错时返回默认系数
            return 1.0


class ProgressUpdateRequest(BaseModel):
    """进度更新请求"""

    lesson_id: int = Field(..., description="课程 ID")
    progress_percentage: int = Field(0, ge=0, le=100, description="进度百分比")
    time_spent_seconds: int = Field(0, ge=0, description="花费时间 (秒)")
    quiz_score: Optional[float] = Field(None, ge=0, le=100, description="测验分数")
    code_quality_score: Optional[float] = Field(
        None, ge=0, le=100, description="代码质量分数"
    )
    status: str = Field(default="in_progress", description="状态")


class LessonCompletionRequest(BaseModel):
    """课程完成请求"""

    lesson_id: int = Field(..., description="课程 ID")
    quiz_score: Optional[float] = Field(None, ge=0, le=100, description="测验分数")
    code_quality_score: Optional[float] = Field(
        None, ge=0, le=100, description="代码质量分数"
    )
    time_spent_seconds: int = Field(0, ge=0, description="花费时间 (秒)")


class ProgressStatisticsResponse(BaseModel):
    """进度统计响应"""

    total_courses: int
    completed_courses: int
    in_progress_courses: int
    not_started_courses: int
    total_time_hours: float
    average_quiz_score: float
    average_code_score: float
    total_points: int
    completion_rate: float
