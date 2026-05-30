"""
统一学习记录管理API路由
提供跨来源学习记录的CRUD接口和统计功能
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from models.user import User
from models.unified_learning_record import (
    LearningRecordStatus,
    UnifiedLearningRecord,
    UnifiedLearningRecordCreate,
    UnifiedLearningRecordListResponse,
    UnifiedLearningRecordResponse,
    UnifiedLearningRecordUpdate,
    UnifiedProgressStats,
)
from services.unified_learning_record_service import UnifiedLearningRecordService
from utils.auth_utils import get_current_user_sync
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器实例
router = APIRouter(prefix="/api/v1", tags=["统一学习记录"])


def get_service(db: Session = Depends(get_sync_db)) -> UnifiedLearningRecordService:
    """获取服务实例"""
    return UnifiedLearningRecordService(db)


# ============ 统一学习记录管理API ============

@router.post(
    "/unified-learning-records",
    response_model=UnifiedLearningRecordResponse,
    summary="创建学习记录"
)
def create_record(
    data: UnifiedLearningRecordCreate = Body(..., description="记录创建数据"),
    current_user: User = Depends(get_current_user_sync),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """创建新的统一学习记录"""
    try:
        record = service.create_record(data, current_user)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建学习记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get(
    "/unified-learning-records/{record_id}",
    response_model=UnifiedLearningRecordResponse,
    summary="获取学习记录详情"
)
def get_record(
    record_id: int = Path(..., description="记录ID"),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """获取指定学习记录的详细信息"""
    record = service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"记录ID {record_id} 不存在")
    return record


@router.get(
    "/unified-learning-records/user/{user_id}",
    response_model=UnifiedLearningRecordListResponse,
    summary="获取用户的学习记录列表"
)
def get_user_records(
    user_id: int = Path(..., description="用户ID"),
    learning_source_id: Optional[int] = Query(None, description="学习来源ID过滤"),
    course_id: Optional[int] = Query(None, description="课程ID过滤"),
    status: Optional[LearningRecordStatus] = Query(None, description="状态过滤"),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """获取用户的所有学习记录"""
    records = service.get_user_records(
        user_id=user_id,
        learning_source_id=learning_source_id,
        course_id=course_id,
        status=status,
    )
    return UnifiedLearningRecordListResponse(total=len(records), items=records)


@router.put(
    "/unified-learning-records/{record_id}",
    response_model=UnifiedLearningRecordResponse,
    summary="更新学习记录"
)
def update_record(
    record_id: int = Path(..., description="记录ID"),
    data: UnifiedLearningRecordUpdate = Body(..., description="更新数据"),
    current_user: User = Depends(get_current_user_sync),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """更新学习记录信息"""
    try:
        record = service.update_record(record_id, data)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新学习记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/unified-learning-records/{record_id}",
    summary="删除学习记录"
)
def delete_record(
    record_id: int = Path(..., description="记录ID"),
    soft: bool = Query(True, description="是否软删除"),
    current_user: User = Depends(get_current_user_sync),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """删除学习记录"""
    try:
        service.delete_record(record_id, soft=soft)
        return {"message": "删除成功", "record_id": record_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除学习记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get(
    "/unified-learning/progress/{user_id}",
    summary="获取用户跨来源学习进度统计"
)
def get_user_progress(
    user_id: int = Path(..., description="用户ID"),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """获取用户跨所有学习来源的学习进度统计"""
    stats = service.get_user_progress_stats(user_id)
    return stats


@router.post(
    "/unified-learning-records/sync-from-enrollment",
    response_model=UnifiedLearningRecordResponse,
    summary="从选课记录同步学习记录"
)
def sync_from_enrollment(
    enrollment_id: int = Body(..., description="选课记录ID"),
    user_id: int = Body(..., description="用户ID"),
    learning_source_id: int = Body(..., description="学习来源ID"),
    current_user: User = Depends(get_current_user_sync),
    service: UnifiedLearningRecordService = Depends(get_service),
):
    """从已有的选课记录创建统一学习记录"""
    try:
        record = service.sync_from_enrollment(enrollment_id, user_id, learning_source_id)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"同步学习记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
