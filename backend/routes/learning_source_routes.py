"""
学习来源管理API路由
提供学习来源的CRUD接口
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from models.learning_source import (
    LearningSource,
    LearningSourceCreate,
    LearningSourceListResponse,
    LearningSourceResponse,
    LearningSourceStatus,
    LearningSourceType,
    LearningSourceUpdate,
)
from models.user import User
from services.learning_source_service import LearningSourceService
from utils.auth_utils import get_current_user_sync
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器实例
router = APIRouter(prefix="/api/v1", tags=["学习来源管理"])


def get_learning_source_service(db: Session = Depends(get_sync_db)) -> LearningSourceService:
    """获取学习来源服务实例"""
    return LearningSourceService(db)


# ============ 学习来源管理API ============

@router.post(
    "/learning-sources",
    response_model=LearningSourceResponse,
    summary="创建学习来源"
)
def create_learning_source(
    source_data: LearningSourceCreate = Body(..., description="学习来源创建数据"),
    current_user: User = Depends(get_current_user_sync),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """创建新的学习来源记录"""
    try:
        source = service.create_learning_source(source_data, current_user)
        return source
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建学习来源失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建学习来源失败: {str(e)}")


@router.get(
    "/learning-sources/{source_id}",
    response_model=LearningSourceResponse,
    summary="获取学习来源详情"
)
def get_learning_source(
    source_id: int = Path(..., description="学习来源ID"),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """获取指定学习来源的详细信息"""
    source = service.get_learning_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"学习来源ID {source_id} 不存在")
    return source


@router.get(
    "/learning-sources/user/{user_id}",
    response_model=LearningSourceListResponse,
    summary="获取用户的学习来源列表"
)
def get_user_learning_sources(
    user_id: int = Path(..., description="用户ID"),
    source_type: Optional[LearningSourceType] = Query(None, description="学习来源类型过滤"),
    status: Optional[LearningSourceStatus] = Query(None, description="状态过滤"),
    include_inactive: bool = Query(False, description="是否包含已停用的来源"),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """获取用户的所有学习来源"""
    sources = service.get_user_learning_sources(
        user_id=user_id,
        source_type=source_type,
        status=status,
        include_inactive=include_inactive,
    )
    return LearningSourceListResponse(total=len(sources), items=sources)


@router.put(
    "/learning-sources/{source_id}",
    response_model=LearningSourceResponse,
    summary="更新学习来源"
)
def update_learning_source(
    source_id: int = Path(..., description="学习来源ID"),
    source_data: LearningSourceUpdate = Body(..., description="更新数据"),
    current_user: User = Depends(get_current_user_sync),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """更新学习来源信息"""
    try:
        source = service.update_learning_source(source_id, source_data)
        return source
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新学习来源失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新学习来源失败: {str(e)}")


@router.delete(
    "/learning-sources/{source_id}",
    summary="删除学习来源"
)
def delete_learning_source(
    source_id: int = Path(..., description="学习来源ID"),
    soft: bool = Query(True, description="是否软删除"),
    current_user: User = Depends(get_current_user_sync),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """删除学习来源"""
    try:
        service.delete_learning_source(source_id, soft=soft)
        return {"message": "删除成功", "source_id": source_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除学习来源失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除学习来源失败: {str(e)}")


@router.get(
    "/learning-sources/user/{user_id}/stats",
    summary="获取用户学习来源统计"
)
def get_user_learning_source_stats(
    user_id: int = Path(..., description="用户ID"),
    service: LearningSourceService = Depends(get_learning_source_service),
):
    """获取用户学习来源统计信息"""
    stats = service.get_source_stats(user_id)
    return stats
