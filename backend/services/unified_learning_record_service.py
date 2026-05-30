"""
统一学习记录管理服务
处理跨来源学习记录的创建、查询、统计等业务逻辑
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.course import Course
from models.learning_source import LearningSource
from models.unified_learning_record import (
    LearningRecordStatus,
    UnifiedLearningRecord,
    UnifiedLearningRecordCreate,
    UnifiedLearningRecordResponse,
    UnifiedLearningRecordUpdate,
)
from models.user import User

logger = logging.getLogger(__name__)


class UnifiedLearningRecordService:
    """统一学习记录管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_record(
        self, data: UnifiedLearningRecordCreate, current_user: Optional[User] = None
    ) -> UnifiedLearningRecord:
        """
        创建统一学习记录

        Args:
            data: 记录创建数据
            current_user: 当前用户

        Returns:
            UnifiedLearningRecord: 创建的记录

        Raises:
            ValueError: 数据验证失败
        """
        try:
            # 验证用户存在
            user = self.db.query(User).filter(User.id == data.user_id).first()
            if not user:
                raise ValueError(f"用户ID {data.user_id} 不存在")

            # 验证学习来源存在
            source = (
                self.db.query(LearningSource)
                .filter(LearningSource.id == data.learning_source_id)
                .first()
            )
            if not source:
                raise ValueError(f"学习来源ID {data.learning_source_id} 不存在")

            # 验证课程存在（如果提供了course_id）
            if data.course_id:
                course = (
                    self.db.query(Course).filter(Course.id == data.course_id).first()
                )
                if not course:
                    raise ValueError(f"课程ID {data.course_id} 不存在")

            # 创建记录
            record = UnifiedLearningRecord(**data.dict())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

            logger.info(
                f"用户 {data.user_id} 创建学习记录: course_id={data.course_id}, source_id={data.learning_source_id}"
            )
            return record

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建学习记录失败: {str(e)}")
            raise

    def get_record(self, record_id: int) -> Optional[UnifiedLearningRecord]:
        """获取学习记录详情"""
        return (
            self.db.query(UnifiedLearningRecord)
            .options(
                joinedload(UnifiedLearningRecord.learning_source),
                joinedload(UnifiedLearningRecord.course),
            )
            .filter(UnifiedLearningRecord.id == record_id)
            .first()
        )

    def get_user_records(
        self,
        user_id: int,
        learning_source_id: Optional[int] = None,
        course_id: Optional[int] = None,
        status: Optional[LearningRecordStatus] = None,
    ) -> List[UnifiedLearningRecord]:
        """
        获取用户的学习记录列表

        Args:
            user_id: 用户ID
            learning_source_id: 学习来源过滤
            course_id: 课程过滤
            status: 状态过滤

        Returns:
            List[UnifiedLearningRecord]: 记录列表
        """
        query = (
            self.db.query(UnifiedLearningRecord)
            .options(
                joinedload(UnifiedLearningRecord.learning_source),
                joinedload(UnifiedLearningRecord.course),
            )
            .filter(UnifiedLearningRecord.user_id == user_id)
        )

        if learning_source_id:
            query = query.filter(
                UnifiedLearningRecord.learning_source_id == learning_source_id
            )

        if course_id:
            query = query.filter(UnifiedLearningRecord.course_id == course_id)

        if status:
            query = query.filter(UnifiedLearningRecord.status == status)

        return query.order_by(UnifiedLearningRecord.created_at.desc()).all()

    def update_record(
        self, record_id: int, data: UnifiedLearningRecordUpdate
    ) -> UnifiedLearningRecord:
        """
        更新学习记录

        Args:
            record_id: 记录ID
            data: 更新数据

        Returns:
            UnifiedLearningRecord: 更新后的记录
        """
        record = self.get_record(record_id)
        if not record:
            raise ValueError(f"学习记录ID {record_id} 不存在")

        # 如果完成，更新完成日期
        if data.status == LearningRecordStatus.COMPLETED and not record.completion_date:
            data.completion_date = datetime.utcnow()

        # 更新字段
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"更新学习记录: {record_id}")
        return record

    def delete_record(self, record_id: int, soft: bool = True) -> bool:
        """
        删除学习记录

        Args:
            record_id: 记录ID
            soft: 是否软删除

        Returns:
            bool: 是否删除成功
        """
        record = self.get_record(record_id)
        if not record:
            raise ValueError(f"学习记录ID {record_id} 不存在")

        if soft:
            record.is_active = False
            self.db.commit()
        else:
            self.db.delete(record)
            self.db.commit()

        logger.info(f"删除学习记录: {record_id}, 软删除: {soft}")
        return True

    def get_user_progress_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户跨来源学习进度统计

        Args:
            user_id: 用户ID

        Returns:
            Dict: 进度统计信息
        """
        records = self.get_user_records(user_id)

        total_courses = len(records)
        completed_courses = len(
            [r for r in records if r.status == LearningRecordStatus.COMPLETED]
        )
        in_progress_courses = len(
            [r for r in records if r.status == LearningRecordStatus.IN_PROGRESS]
        )
        total_time = sum(r.total_time_minutes for r in records)

        # 计算平均成绩
        scored_records = [r for r in records if r.score is not None]
        average_score = None
        if scored_records:
            average_score = sum(r.score for r in scored_records) / len(scored_records)

        # 按来源统计
        source_stats = {}
        for record in records:
            source_id = record.learning_source_id
            if source_id not in source_stats:
                source = record.learning_source
                source_stats[source_id] = {
                    "source_id": source_id,
                    "source_name": source.name if source else "未知",
                    "source_type": source.source_type.value if source else None,
                    "courses": 0,
                    "completed": 0,
                    "total_time": 0,
                    "scores": [],
                }

            stats = source_stats[source_id]
            stats["courses"] += 1
            stats["total_time"] += record.total_time_minutes

            if record.status == LearningRecordStatus.COMPLETED:
                stats["completed"] += 1

            if record.score is not None:
                stats["scores"].append(record.score)

        # 整理来源统计数据
        source_breakdown = []
        for source_id, stats in source_stats.items():
            avg_score = None
            if stats["scores"]:
                avg_score = sum(stats["scores"]) / len(stats["scores"])

            source_breakdown.append(
                {
                    "source_type": stats["source_type"],
                    "source_name": stats["source_name"],
                    "courses": stats["courses"],
                    "completed": stats["completed"],
                    "avg_score": avg_score,
                    "total_time": stats["total_time"],
                }
            )

        return {
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "in_progress_courses": in_progress_courses,
            "total_time_minutes": total_time,
            "average_score": average_score,
            "source_breakdown": source_breakdown,
        }

    def sync_from_enrollment(
        self, enrollment_id: int, user_id: int, learning_source_id: int
    ) -> UnifiedLearningRecord:
        """
        从选课记录同步到统一学习记录

        Args:
            enrollment_id: 选课记录ID
            user_id: 用户ID
            learning_source_id: 学习来源ID

        Returns:
            UnifiedLearningRecord: 创建/更新的记录
        """
        from models.course import CourseEnrollment

        # 获取选课记录
        enrollment = (
            self.db.query(CourseEnrollment)
            .filter(CourseEnrollment.id == enrollment_id)
            .first()
        )
        if not enrollment:
            raise ValueError(f"选课记录ID {enrollment_id} 不存在")

        # 检查是否已存在记录
        existing = (
            self.db.query(UnifiedLearningRecord)
            .filter(
                UnifiedLearningRecord.user_id == user_id,
                UnifiedLearningRecord.course_id == enrollment.course_id,
                UnifiedLearningRecord.enrollment_id == enrollment_id,
            )
            .first()
        )

        if existing:
            # 更新现有记录
            existing.learning_source_id = learning_source_id
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # 创建新记录
        record_data = UnifiedLearningRecordCreate(
            user_id=user_id,
            course_id=enrollment.course_id,
            learning_source_id=learning_source_id,
            enrollment_id=enrollment_id,
            status=LearningRecordStatus.NOT_STARTED
            if enrollment.status.value == "pending"
            else LearningRecordStatus.IN_PROGRESS,
        )

        return self.create_record(record_data)
