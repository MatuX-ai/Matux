"""
课程聚合路由
提供课程同步回调和学生课程聚合查询API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.learning.aggregation_service import course_aggregation_service
from modules.learning.models import (
    CourseSyncRequest,
    CourseSyncResponse,
    AggregatedCourseListResponse,
)
from utils.database import get_db

router = APIRouter(prefix="/api/v1/courses", tags=["课程聚合"])


@router.post("/sync", response_model=CourseSyncResponse, summary="子项目推送课程数据")
async def sync_course(
    req: CourseSyncRequest, db: AsyncSession = Depends(get_db)
):
    """子项目（OpenMTEduInst / OpenMTSciEd）回调此接口推送课程数据

    当机构为学生报名课程，或学生在课件平台开始学习时调用。
    通过 student_phone 匹配 iMato 统一用户。
    """
    try:
        aggregation = await course_aggregation_service.sync_course(db, req)
        return CourseSyncResponse(
            id=aggregation.id,
            student_id=aggregation.student_id,
            course_id=aggregation.course_id,
            course_name=aggregation.course_name,
            source=aggregation.source.value if aggregation.source else "unknown",
            status=aggregation.status.value if aggregation.status else "enrolled",
            message="同步成功",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}",
        )


@router.get(
    "/students/{student_id}/courses",
    response_model=AggregatedCourseListResponse,
    summary="查询学生聚合课程列表",
)
async def get_student_courses(
    student_id: int, db: AsyncSession = Depends(get_db)
):
    """获取指定学生的所有聚合课程（按来源分组）"""
    try:
        return await course_aggregation_service.get_student_courses(db, student_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}",
        )


@router.put("/progress", summary="更新学习进度")
async def update_course_progress(
    student_id: int,
    course_id: str,
    source: str,
    progress: float,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """更新学生在某课程的学习进度"""
    result = await course_aggregation_service.update_progress(
        db=db,
        student_id=student_id,
        course_id=course_id,
        source=source,
        progress=progress,
        status=status,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到对应的课程记录",
        )
    return {"message": "进度更新成功", "student_id": student_id, "course_id": course_id}
