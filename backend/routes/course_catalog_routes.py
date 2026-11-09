"""课程目录 API（桌面端 /api/v1/courses）。

背景：
    桌面端入口 main_ai_edu 原先没有通用课程查询路由，前端请求
    /api/v1/courses 一律 404，课程列表只能显示前端 mock 数据。
    本模块基于真实数据库提供：课程列表 / 课程详情 / 我的选课。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from models.course import Course, CourseEnrollment, CourseLesson
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from utils.database import get_sync_session

router = APIRouter(prefix="/api/v1/courses", tags=["课程"])


class EnrollmentCreate(BaseModel):
    """报名请求体（前端 CourseEnrollmentService.enrollInCourse）。"""

    course_id: int = Field(..., description="课程 ID")
    user_id: int = Field(..., description="用户 ID")
    org_id: Optional[int] = Field(None, description="组织 ID")


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _course_payload(course: Course, teacher_name: Optional[str] = None) -> Dict[str, Any]:
    """把 Course ORM 对象转成前端 UnifiedCourse 需要的结构。"""
    return {
        "id": course.id,
        "org_id": course.org_id,
        "title": course.title,
        "description": course.description or "",
        "cover_image_url": course.cover_image_url,
        "category": course.category or "general",
        "difficulty": course.difficulty or "intermediate",
        "duration_minutes": course.duration_minutes or 0,
        "status": course.status or "published",
        "source_type": "school_curriculum",
        "teacher_name": teacher_name,
        "tags": course.tags or [],
        "created_at": _iso(course.created_at),
        "updated_at": _iso(course.updated_at),
    }


def _enrollment_payload(enrollment: CourseEnrollment) -> Dict[str, Any]:
    """把 CourseEnrollment ORM 对象转成前端 CourseEnrollment 结构。"""
    return {
        "id": enrollment.id,
        "user_id": enrollment.user_id,
        "course_id": enrollment.course_id,
        "org_id": enrollment.org_id,
        "learning_source_id": enrollment.learning_source_id,
        "progress_percentage": enrollment.progress_percentage or 0,
        "score": enrollment.score,
        "status": enrollment.status or "active",
        "enrolled_at": _iso(enrollment.enrolled_at),
        "completed_at": _iso(enrollment.completed_at),
    }


def _teacher_names(db: Session, courses: List[Course]) -> Dict[int, str]:
    """批量取教师用户名，避免 N+1 查询。"""
    teacher_ids = {c.teacher_id for c in courses if c.teacher_id}
    if not teacher_ids:
        return {}
    rows = db.execute(
        select(User.id, User.username).where(User.id.in_(teacher_ids))
    ).all()
    return {row[0]: row[1] for row in rows}


def _course_filters(stmt, status: Optional[str], category: Optional[str], keyword: Optional[str]):
    stmt = stmt.where(Course.is_active.is_(True))
    if status:
        stmt = stmt.where(Course.status == status)
    if category:
        stmt = stmt.where(Course.category == category)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Course.title.like(like) | Course.description.like(like))
    return stmt


@router.post("/enrollments", summary="报名课程")
async def create_enrollment(payload: EnrollmentCreate, db: Session = Depends(get_sync_session)):
    """报名课程；已存在有效选课记录时幂等返回原记录。"""
    course = db.get(Course, payload.course_id)
    if course is None or not course.is_active:
        raise HTTPException(status_code=404, detail="课程不存在")

    existing = (
        db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.user_id == payload.user_id,
                CourseEnrollment.course_id == payload.course_id,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return _enrollment_payload(existing)

    enrollment = CourseEnrollment(
        user_id=payload.user_id,
        course_id=payload.course_id,
        org_id=payload.org_id if payload.org_id is not None else course.org_id,
        progress_percentage=0.0,
        status="active",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return _enrollment_payload(enrollment)


@router.get("/enrollments", summary="我的选课列表")
async def list_my_enrollments(
    user_id: int = Query(..., description="用户 ID"),
    status: Optional[str] = Query(None, description="active/completed/suspended"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_sync_session),
):
    """返回指定用户的选课记录（供「我的课程」页使用）。"""
    base = select(CourseEnrollment).where(CourseEnrollment.user_id == user_id)
    if status:
        base = base.where(CourseEnrollment.status == status)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = int(db.execute(count_stmt).scalar() or 0)

    rows = (
        db.execute(
            base.order_by(CourseEnrollment.enrolled_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    items = [_enrollment_payload(e) for e in rows]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("", summary="课程列表")
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="published/draft"),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    ids: Optional[str] = Query(None, description="逗号分隔的课程 ID，批量查询"),
    db: Session = Depends(get_sync_session),
):
    """分页返回课程列表；ids 参数用于「按选课记录批量取课程」。"""
    id_list: Optional[List[int]] = None
    if ids:
        try:
            id_list = [int(part) for part in ids.split(",") if part.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="ids 必须是逗号分隔的整数")

    base = _course_filters(select(Course), status, category, keyword)
    if id_list is not None:
        base = base.where(Course.id.in_(id_list))

    count_stmt = select(func.count()).select_from(base.subquery())
    total = int(db.execute(count_stmt).scalar() or 0)

    courses = (
        db.execute(
            base.order_by(Course.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    teachers = _teacher_names(db, courses)
    items = [_course_payload(c, teachers.get(c.teacher_id)) for c in courses]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{course_id}", summary="课程详情")
async def get_course(course_id: int, db: Session = Depends(get_sync_session)):
    """返回单门课程详情（含课时列表）。"""
    course = db.get(Course, course_id)
    if course is None or not course.is_active:
        raise HTTPException(status_code=404, detail="课程不存在")

    teachers = _teacher_names(db, [course])
    payload = _course_payload(course, teachers.get(course.teacher_id))
    lessons = (
        db.execute(
            select(CourseLesson)
            .where(CourseLesson.course_id == course_id, CourseLesson.is_active.is_(True))
            .order_by(CourseLesson.order_index.asc())
        )
        .scalars()
        .all()
    )
    payload["lessons"] = [
        {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description or "",
            "order_index": lesson.order_index,
            "duration_minutes": lesson.duration_minutes or 0,
            "content_type": lesson.content_type or "video",
            "content_url": lesson.content_url,
        }
        for lesson in lessons
    ]
    return payload
