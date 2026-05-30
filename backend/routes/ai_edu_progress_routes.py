"""
AI-Edu-for-Kids 学习进度 API 路由
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database.db import Base
from models.user import User
from utils.auth_utils import get_current_user_sync
from services.ai_edu_progress_service import (
    AIEduProgressService,
    LessonCompletionRequest,
    ProgressStatisticsResponse,
    ProgressUpdateRequest,
)
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/org/{org_id}/ai-edu", tags=["AI 教育学习进度"])


@router.post("/progress")
async def update_learning_progress(
    org_id: int,
    request: ProgressUpdateRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    更新学习进度

    Args:
        org_id: 组织 ID
        request: 进度更新请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的进度记录
    """
    try:
        service = AIEduProgressService(db)

        progress_data = {
            "progress_percentage": request.progress_percentage,
            "time_spent_seconds": request.time_spent_seconds,
            "quiz_score": request.quiz_score,
            "code_quality_score": request.code_quality_score,
            "status": request.status,
        }

        progress = await service.report_progress(
            user_id=current_user.id,
            lesson_id=request.lesson_id,
            progress_data=progress_data,
        )

        return {
            "success": True,
            "data": {
                "progress_id": progress.id,
                "lesson_id": progress.lesson_id,
                "progress_percentage": progress.progress_percentage,
                "status": progress.status,
                "time_spent_seconds": progress.time_spent_seconds,
                "last_accessed_time": progress.last_accessed_time.isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"更新学习进度失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress")
async def get_user_progress(
    org_id: int,
    module_id: Optional[int] = Query(None, description="模块 ID"),
    status_filter: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
) -> dict:
    """
    获取用户学习进度

    Args:
        org_id: 组织 ID
        module_id: 模块 ID（可选）
        status_filter: 状态过滤（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        进度列表
    """
    try:
        service = AIEduProgressService(db)

        progress_list = await service.get_user_progress(
            user_id=current_user.id, module_id=module_id, status_filter=status_filter
        )

        return {"success": True, "count": len(progress_list), "data": progress_list}

    except Exception as e:
        logger.error(f"获取学习进度失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/complete")
async def complete_lesson(
    org_id: int,
    request: LessonCompletionRequest,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    完成课程并发放积分

    Args:
        org_id: 组织 ID
        request: 课程完成请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        获得的积分和进度更新
    """
    try:
        service = AIEduProgressService(db)

        completion_data = {
            "quiz_score": request.quiz_score,
            "code_quality_score": request.code_quality_score,
            "time_spent_seconds": request.time_spent_seconds,
        }

        points_earned = await service.complete_lesson_and_award_points(
            user_id=current_user.id,
            lesson_id=request.lesson_id,
            completion_data=completion_data,
        )

        return {
            "success": True,
            "points_earned": points_earned,
            "message": f"恭喜完成课程！获得{points_earned}积分奖励",
            "data": {
                "lesson_id": request.lesson_id,
                "status": "completed",
                "points": points_earned,
            },
        }

    except Exception as e:
        logger.error(f"完成课程并发放积分失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/statistics")
async def get_progress_statistics(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
) -> ProgressStatisticsResponse:
    """
    获取学习进度统计信息

    Args:
        org_id: 组织 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计信息
    """
    try:
        service = AIEduProgressService(db)

        stats = await service.get_progress_statistics(user_id=current_user.id)

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"获取进度统计失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/progress/{lesson_id}")
async def reset_progress(
    org_id: int,
    lesson_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    重置学习进度（重新开始课程）

    Args:
        org_id: 组织 ID
        lesson_id: 课程 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        操作结果
    """
    from sqlalchemy import delete

    from models.ai_edu_rewards import AIEduLearningProgress

    try:
        # 删除进度记录
        stmt = delete(AIEduLearningProgress).where(
            and_(
                AIEduLearningProgress.user_id == current_user.id,
                AIEduLearningProgress.lesson_id == lesson_id,
            )
        )

        db.execute(stmt)
        db.commit()

        return {"success": True, "message": "进度已重置，可以重新开始学习"}

    except Exception as e:
        logger.error(f"重置学习进度失败：{e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
