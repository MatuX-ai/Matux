"""
课程聚合服务
接收子项目回调、查询学生聚合课程列表
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from modules.learning.models import (
    StudentCourseAggregation,
    CourseSource,
    CourseStatus,
    CourseSyncRequest,
    AggregatedCourseItem,
    AggregatedCourseListResponse,
)


class CourseAggregationService:
    """课程聚合服务"""

    async def sync_course(
        self, db: AsyncSession, req: CourseSyncRequest
    ) -> StudentCourseAggregation:
        """接收子项目回调，写入或更新课程聚合记录"""

        # 通过手机号匹配学生
        stmt = select(User).filter(User.phone == req.student_phone)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"未找到手机号为 {req.student_phone} 的学生")

        # 解析来源类型
        try:
            source = CourseSource(req.source)
        except ValueError:
            source = CourseSource.IMATO

        # 查找是否已有记录（同一学生+同一来源+同一课程ID）
        stmt = select(StudentCourseAggregation).filter(
            and_(
                StudentCourseAggregation.student_id == student.id,
                StudentCourseAggregation.source == source,
                StudentCourseAggregation.course_id == req.course_id,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # 更新已有记录
            existing.org_id = req.org_id or existing.org_id
            existing.org_name = req.org_name or existing.org_name
            existing.course_name = req.course_name
            if req.status:
                try:
                    existing.status = CourseStatus(req.status)
                except ValueError:
                    pass
            if req.progress is not None:
                existing.progress = req.progress
            if req.extra_data:
                existing.extra_data = json.dumps(req.extra_data)
            existing.synced_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # 新建记录
            try:
                status = CourseStatus(req.status) if req.status else CourseStatus.ENROLLED
            except ValueError:
                status = CourseStatus.ENROLLED

            aggregation = StudentCourseAggregation(
                student_id=student.id,
                org_id=req.org_id,
                org_name=req.org_name,
                course_id=req.course_id,
                course_name=req.course_name,
                source=source,
                status=status,
                progress=req.progress or 0.0,
                extra_data=json.dumps(req.extra_data) if req.extra_data else None,
            )
            db.add(aggregation)
            await db.commit()
            await db.refresh(aggregation)
            return aggregation

    async def get_student_courses(
        self, db: AsyncSession, student_id: int
    ) -> AggregatedCourseListResponse:
        """获取学生的所有聚合课程"""
        stmt = (
            select(StudentCourseAggregation)
            .filter(StudentCourseAggregation.student_id == student_id)
            .order_by(StudentCourseAggregation.synced_at.desc())
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        courses = []
        by_source: Dict[str, int] = {}

        for record in records:
            source_key = record.source.value if record.source else "unknown"
            by_source[source_key] = by_source.get(source_key, 0) + 1

            courses.append(
                AggregatedCourseItem(
                    id=record.id,
                    org_id=record.org_id,
                    org_name=record.org_name,
                    course_id=record.course_id,
                    course_name=record.course_name,
                    source=source_key,
                    status=record.status.value if record.status else "enrolled",
                    progress=record.progress,
                    synced_at=record.synced_at.isoformat() if record.synced_at else None,
                )
            )

        return AggregatedCourseListResponse(
            student_id=student_id,
            total=len(courses),
            by_source=by_source,
            courses=courses,
        )

    async def update_progress(
        self,
        db: AsyncSession,
        student_id: int,
        course_id: str,
        source: str,
        progress: float,
        status: Optional[str] = None,
    ) -> bool:
        """更新学习进度"""
        try:
            src = CourseSource(source)
        except ValueError:
            return False

        stmt = (
            update(StudentCourseAggregation)
            .where(
                and_(
                    StudentCourseAggregation.student_id == student_id,
                    StudentCourseAggregation.course_id == course_id,
                    StudentCourseAggregation.source == src,
                )
            )
            .values(progress=progress, synced_at=datetime.utcnow())
        )

        if status:
            try:
                stmt = stmt.values(status=CourseStatus(status))
            except ValueError:
                pass

        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0


# 全局服务实例
course_aggregation_service = CourseAggregationService()
