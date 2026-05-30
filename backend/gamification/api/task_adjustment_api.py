"""
任务调整API接口
提供任务难度实时调整、用户事件处理等功能
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models.difficulty_level import TaskPerformanceMetrics
from ..services.adaptive_task_service import AdaptiveTaskService
from ..services.difficulty_service import DifficultyService
from ..services.rule_engine_service import RuleEngineService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/tasks", tags=["任务调整"])


# 请求/响应模型
class TaskCompletionEvent(BaseModel):
    user_id: str
    task_id: str
    success: bool
    completion_time: float
    hint_used: bool = False
    retry_count: int = 0
    hardware_metrics: List[Dict[str, Any]] = []
    debugging_sessions: List[Dict[str, Any]] = []


class EventProcessingResult(BaseModel):
    event_id: str
    user_id: str
    task_id: str
    rules_triggered: List[str]
    adjustments_made: List[Dict[str, Any]]
    processing_time_ms: float


class AdaptiveTaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    difficulty_score: float
    difficulty_level: str
    estimated_time: int
    match_score: float
    prerequisites: List[str]


class LearningPathResponse(BaseModel):
    user_id: str
    target_level: str
    path_length: int
    tasks: List[Dict[str, Any]]


class SessionSimulationRequest(BaseModel):
    user_id: str
    session_duration: int = 120  # 分钟


class SessionReportResponse(BaseModel):
    user_id: str
    session_start: str
    session_end: str
    duration_minutes: float
    tasks_completed: int
    success_rate: float
    completed_tasks: List[Dict[str, Any]]
    final_difficulty_score: float


# 依赖注入
def get_adaptive_task_service() -> AdaptiveTaskService:
    """获取自适应任务服务实例"""
    difficulty_service = DifficultyService()
    rule_engine_service = RuleEngineService()
    return AdaptiveTaskService(difficulty_service, rule_engine_service)


@router.post("/complete", response_model=EventProcessingResult)
async def process_task_completion(
    event: TaskCompletionEvent,
    service: AdaptiveTaskService = Depends(get_adaptive_task_service),
):
    """
    处理任务完成事件并调整难度

    Args:
        event: 任务完成事件
        service: 自适应任务服务依赖

    Returns:
        事件处理结果
    """
    start_time = datetime.now()

    try:
        # 创建表现指标
        from ..models.difficulty_level import DebuggingSession, HardwareOperationMetric

        hardware_metrics = [
            HardwareOperationMetric(
                operation_type=m.get("operation_type", ""),
                success_count=m.get("success_count", 0),
                total_count=m.get("total_count", 0),
                average_response_time=m.get("average_response_time", 0.0),
                error_rate=m.get("error_rate", 0.0),
            )
            for m in event.hardware_metrics
        ]

        debugging_sessions = [
            DebuggingSession(
                session_id=s.get("session_id", ""),
                duration=float(s.get("duration", 0)),
                breakpoint_count=s.get("breakpoint_count", 0),
                step_count=s.get("step_count", 0),
                variable_inspection_count=s.get("variable_inspection_count", 0),
                completion_status=s.get("completion_status", "unknown"),
            )
            for s in event.debugging_sessions
        ]

        performance_metrics = TaskPerformanceMetrics(
            user_id=event.user_id,
            task_id=event.task_id,
            success_rate=1.0 if event.success else 0.5,
            average_completion_time=event.completion_time,
            hint_usage_count=1 if event.hint_used else 0,
            retry_count=event.retry_count,
            hardware_metrics=hardware_metrics,
            debugging_sessions=debugging_sessions,
            timestamp=datetime.now(),
        )

        # 调整任务难度
        new_score, adjustment_reason = await service.adjust_task_difficulty(
            event.user_id, event.task_id, performance_metrics, event.success
        )

        # 计算处理时间
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        return EventProcessingResult(
            event_id=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            user_id=event.user_id,
            task_id=event.task_id,
            rules_triggered=[],  # 实际应该从规则引擎获取
            adjustments_made=[
                {
                    "type": "difficulty_adjustment",
                    "new_score": new_score,
                    "reason": adjustment_reason,
                }
            ],
            processing_time_ms=processing_time,
        )
    except Exception as e:
        logger.error(f"处理任务完成事件失败: {e}")
        raise HTTPException(status_code=500, detail="处理任务完成事件失败")


@router.get("/user/{user_id}/next", response_model=AdaptiveTaskResponse)
async def get_next_recommended_task(
    user_id: str, service: AdaptiveTaskService = Depends(get_adaptive_task_service)
):
    """
    获取用户的下一个推荐任务

    Args:
        user_id: 用户ID
        service: 自适应任务服务依赖

    Returns:
        推荐任务
    """
    try:
        recommended_task = await service.get_next_recommended_task(user_id)

        if not recommended_task:
            raise HTTPException(status_code=404, detail="暂无推荐任务")

        # 获取难度等级
        from ..services.difficulty_service import DifficultyService

        difficulty_service = DifficultyService()
        _, difficulty_level = difficulty_service.get_user_difficulty_level(user_id)

        return AdaptiveTaskResponse(
            task_id=recommended_task["task_id"],
            title=recommended_task["title"],
            description=recommended_task["description"],
            difficulty_score=recommended_task["difficulty_score"],
            difficulty_level=difficulty_level.value,
            estimated_time=recommended_task["estimated_time"],
            match_score=recommended_task.get("match_score", 0.0),
            prerequisites=recommended_task.get("prerequisites", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推荐任务失败: {e}")
        raise HTTPException(status_code=500, detail="获取推荐任务失败")


@router.get("/user/{user_id}/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    user_id: str,
    target_level: str = Query("L5", description="目标难度等级"),
    service: AdaptiveTaskService = Depends(get_adaptive_task_service),
):
    """
    获取用户学习路径

    Args:
        user_id: 用户ID
        target_level: 目标难度等级
        service: 自适应任务服务依赖

    Returns:
        学习路径
    """
    try:
        path = service.get_task_progression_path(user_id, target_level)

        return LearningPathResponse(
            user_id=user_id,
            target_level=target_level,
            path_length=len(path),
            tasks=path,
        )
    except Exception as e:
        logger.error(f"获取学习路径失败: {e}")
        raise HTTPException(status_code=500, detail="获取学习路径失败")


@router.post("/simulate-session", response_model=SessionReportResponse)
async def simulate_learning_session(
    request: SessionSimulationRequest,
    service: AdaptiveTaskService = Depends(get_adaptive_task_service),
):
    """
    模拟学习会话

    Args:
        request: 会话模拟请求
        service: 自适应任务服务依赖

    Returns:
        会话报告
    """
    try:
        session_report = await service.simulate_user_session(
            request.user_id, request.session_duration
        )

        return SessionReportResponse(**session_report)
    except Exception as e:
        logger.error(f"模拟学习会话失败: {e}")
        raise HTTPException(status_code=500, detail="模拟学习会话失败")


@router.get("/user/{user_id}/streak")
async def get_user_streak_info(
    user_id: str, service: AdaptiveTaskService = Depends(get_adaptive_task_service)
):
    """
    获取用户连胜信息

    Args:
        user_id: 用户ID
        service: 自适应任务服务依赖

    Returns:
        连胜信息
    """
    try:
        # 从规则引擎获取连胜信息
        streak_info = service.rule_engine_service.get_user_streak_info(user_id)
        return {
            "user_id": user_id,
            "success_streak": streak_info["success_streak"],
            "failure_streak": streak_info["failure_streak"],
            "last_activity_time": streak_info["last_activity_time"],
        }
    except Exception as e:
        logger.error(f"获取连胜信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取连胜信息失败")


@router.post("/user/{user_id}/streak/reset")
async def reset_user_streak(
    user_id: str, service: AdaptiveTaskService = Depends(get_adaptive_task_service)
):
    """
    重置用户连胜计数

    Args:
        user_id: 用户ID
        service: 自适应任务服务依赖

    Returns:
        重置结果
    """
    try:
        service.rule_engine_service.reset_user_streak(user_id)
        return {"status": "success", "message": "连胜计数已重置", "user_id": user_id}
    except Exception as e:
        logger.error(f"重置连胜计数失败: {e}")
        raise HTTPException(status_code=500, detail="重置连胜计数失败")


@router.get("/health")
async def health_check():
    """
    健康检查接口

    Returns:
        服务健康状态
    """
    return {
        "status": "healthy",
        "service": "gamification-task-adjustment",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics")
async def get_service_metrics(
    service: AdaptiveTaskService = Depends(get_adaptive_task_service),
):
    """
    获取服务性能指标

    Args:
        service: 自适应任务服务依赖

    Returns:
        性能指标
    """
    try:
        # 获取规则引擎统计
        rule_stats = service.rule_engine_service.get_rule_statistics()

        # 获取难度服务统计
        difficulty_stats = {
            "user_profiles_count": len(service.difficulty_service.user_profiles)
        }

        return {
            "rule_engine": rule_stats,
            "difficulty_service": difficulty_stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"获取服务指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取服务指标失败")
