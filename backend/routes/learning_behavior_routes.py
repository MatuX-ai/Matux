"""
学习行为特征API路由
提供学习行为数据的RESTful API接口
"""

from datetime import datetime, timedelta
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.learning_behavior import (
    BehaviorAnalyticsRequest,
    BehaviorAnalyticsResponse,
    BehaviorCategory,
    LearningBehaviorCreate,
    LearningBehaviorResponse,
    LearningBehaviorSummaryResponse,
    LearningBehaviorUpdate,
)
from models.user import User
from services.learning_behavior_service import get_learning_behavior_service
from utils.auth_utils import get_current_user as get_current_active_user
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/learning-behavior", tags=["学习行为特征"])


@router.post("/", response_model=LearningBehaviorResponse, summary="创建学习行为记录")
async def create_behavior_record(
    behavior_data: LearningBehaviorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    创建新的学习行为记录

    - **student_id**: 学生ID
    - **category**: 行为类别 (code_debugging/hardware_operation/learning_activity/assessment/collaboration)
    - **event_type**: 事件类型
    - **event_timestamp**: 事件时间戳
    """
    try:
        service = get_learning_behavior_service(db)
        record = service.create_behavior_record(behavior_data, current_user.org_id)
        return record
    except Exception as e:
        logger.error(f"创建行为记录失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{record_id}", response_model=LearningBehaviorResponse, summary="获取行为记录详情"
)
async def get_behavior_record(
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    根据ID获取特定的行为记录详情
    """
    try:
        service = get_learning_behavior_service(db)
        record = (
            service.db.query(service.model_class)
            .filter(
                service.model_class.id == record_id,
                service.model_class.org_id == current_user.org_id,
            )
            .first()
        )

        if not record:
            raise HTTPException(status_code=404, detail="行为记录不存在")

        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取行为记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{record_id}", response_model=LearningBehaviorResponse, summary="更新行为记录"
)
async def update_behavior_record(
    record_id: int,
    update_data: LearningBehaviorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    更新指定的行为记录
    """
    try:
        service = get_learning_behavior_service(db)
        record = service.update_behavior_record(record_id, update_data)
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新行为记录失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/", response_model=List[LearningBehaviorResponse], summary="查询行为记录列表"
)
async def list_behavior_records(
    student_id: Optional[int] = Query(None, description="学生ID"),
    category: Optional[BehaviorCategory] = Query(None, description="行为类别"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    查询学习行为记录列表

    支持按学生、类别、时间范围等条件筛选
    """
    try:
        service = get_learning_behavior_service(db)

        # 设置默认时间范围（最近30天）
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        records = service.get_behavior_records(
            student_id=student_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return records
    except Exception as e:
        logger.error(f"查询行为记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/debug-metrics", summary="获取学生调试指标")
async def get_student_debug_metrics(
    student_id: int,
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取指定学生的代码调试相关指标
    """
    try:
        service = get_learning_behavior_service(db)

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        metrics = service.calculate_debug_metrics(student_id, start_date, end_date)
        return {
            "student_id": student_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"获取调试指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}/hardware-metrics", summary="获取学生硬件指标")
async def get_student_hardware_metrics(
    student_id: int,
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取指定学生的硬件操作相关指标
    """
    try:
        service = get_learning_behavior_service(db)

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        metrics = service.calculate_hardware_metrics(student_id, start_date, end_date)
        return {
            "student_id": student_id,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"获取硬件指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/student/{student_id}/summary",
    response_model=LearningBehaviorSummaryResponse,
    summary="生成学生行为汇总",
)
async def generate_student_summary(
    student_id: int,
    period_start: datetime = Body(..., description="统计周期开始时间"),
    period_end: datetime = Body(..., description="统计周期结束时间"),
    period_type: str = Body("daily", description="统计周期类型"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    为指定学生生成指定时间段的行为汇总数据
    """
    try:
        service = get_learning_behavior_service(db)
        summary = service.generate_behavior_summary(
            student_id, period_start, period_end, period_type
        )
        return summary
    except Exception as e:
        logger.error(f"生成行为汇总失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/student/{student_id}/summaries",
    response_model=List[LearningBehaviorSummaryResponse],
    summary="获取学生行为汇总列表",
)
async def list_student_summaries(
    student_id: int,
    period_type: Optional[str] = Query(None, description="统计周期类型"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(50, ge=1, le=500, description="每页记录数"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取指定学生的行为汇总记录列表
    """
    try:
        service = get_learning_behavior_service(db)
        query = service.db.query(service.summary_model_class).filter(
            service.summary_model_class.student_id == student_id,
            service.summary_model_class.org_id == current_user.org_id,
        )

        if period_type:
            query = query.filter(service.summary_model_class.period_type == period_type)

        if start_date:
            query = query.filter(service.summary_model_class.period_start >= start_date)

        if end_date:
            query = query.filter(service.summary_model_class.period_end <= end_date)

        summaries = (
            query.order_by(service.summary_model_class.period_start.desc())
            .limit(limit)
            .all()
        )

        return summaries
    except Exception as e:
        logger.error(f"获取行为汇总列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analytics", response_model=BehaviorAnalyticsResponse, summary="获取行为分析数据"
)
async def get_behavior_analytics(
    analytics_request: BehaviorAnalyticsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取综合行为分析数据，包括统计、趋势和效果评估
    """
    try:
        service = get_learning_behavior_service(db)
        analytics_data = service.get_behavior_analytics(analytics_request)
        return analytics_data
    except Exception as e:
        logger.error(f"获取行为分析数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/student/{student_id}/batch-process", summary="批量处理学生行为数据")
async def batch_process_student_data(
    student_id: int,
    days_back: int = Body(30, ge=1, le=365, description="回溯天数"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    批量处理指定学生的近期行为数据，生成各种周期的汇总
    """
    try:
        service = get_learning_behavior_service(db)
        results = service.batch_process_behavior_data(student_id, days_back)
        return {
            "student_id": student_id,
            "days_back": days_back,
            "processing_results": results,
            "message": "批量处理完成",
        }
    except Exception as e:
        logger.error(f"批量处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics/overview", summary="获取行为统计概览")
async def get_behavior_statistics_overview(
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取组织级别的学习行为统计概览
    """
    try:
        service = get_learning_behavior_service(db)

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # 获取统计信息
        total_records = (
            service.db.query(service.model_class)
            .filter(
                service.model_class.org_id == current_user.org_id,
                service.model_class.event_timestamp.between(start_date, end_date),
            )
            .count()
        )

        # 按类别统计
        category_stats = {}
        for category in BehaviorCategory:
            count = (
                service.db.query(service.model_class)
                .filter(
                    service.model_class.org_id == current_user.org_id,
                    service.model_class.category == category.value,
                    service.model_class.event_timestamp.between(start_date, end_date),
                )
                .count()
            )
            category_stats[category.value] = count

        # 活跃学生数
        active_students = (
            service.db.query(service.model_class.student_id)
            .filter(
                service.model_class.org_id == current_user.org_id,
                service.model_class.event_timestamp.between(start_date, end_date),
            )
            .distinct()
            .count()
        )

        return {
            "organization_id": current_user.org_id,
            "period": {"start_date": start_date, "end_date": end_date},
            "total_records": total_records,
            "active_students": active_students,
            "category_distribution": category_stats,
            "average_daily_records": total_records
            / max((end_date - start_date).days, 1),
        }
    except Exception as e:
        logger.error(f"获取统计概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
