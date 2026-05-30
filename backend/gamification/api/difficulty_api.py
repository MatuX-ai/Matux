"""
难度相关API接口
提供难度等级查询、用户统计、任务推荐等接口
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models.difficulty_level import (
    DebuggingSession,
    HardwareOperationMetric,
    TaskPerformanceMetrics,
)
from ..services.difficulty_service import DifficultyService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/difficulty", tags=["难度管理"])


# 请求/响应模型
class PerformanceMetricsRequest(BaseModel):
    success_rate: float
    average_completion_time: float
    hint_usage_count: int
    retry_count: int
    hardware_metrics: List[Dict[str, Any]] = []
    debugging_sessions: List[Dict[str, Any]] = []


class DifficultyResponse(BaseModel):
    user_id: str
    difficulty_score: float
    difficulty_level: str
    level_description: str
    confidence: float


class TaskRecommendationResponse(BaseModel):
    task_id: str
    title: str
    description: str
    difficulty_score: float
    difficulty_level: str
    estimated_time: int
    match_score: float
    tags: List[str]


class UserStatisticsResponse(BaseModel):
    user_id: str
    current_difficulty_score: float
    current_difficulty_level: str
    total_tasks_completed: int
    recent_success_rate: float
    average_completion_time: float
    success_streak: int
    failure_streak: int
    last_adjustment_time: Optional[str]
    total_adjustments: int


# 依赖注入
def get_difficulty_service() -> DifficultyService:
    """获取难度服务实例"""
    return DifficultyService()


@router.get("/user/{user_id}/level", response_model=DifficultyResponse)
async def get_user_difficulty_level(
    user_id: str, service: DifficultyService = Depends(get_difficulty_service)
):
    """
    获取用户当前难度等级

    Args:
        user_id: 用户ID
        service: 难度服务依赖

    Returns:
        用户难度等级信息
    """
    try:
        score, level = service.get_user_difficulty_level(user_id)

        # 计算置信度(基于任务完成数量)
        profile = service.get_user_profile(user_id)
        task_count = len(profile.task_history) if profile else 0
        confidence = min(1.0, task_count / 10.0)  # 10个任务后达到最高置信度

        return DifficultyResponse(
            user_id=user_id,
            difficulty_score=score,
            difficulty_level=level.value,
            level_description=level.name.lower().replace("_", " "),
            confidence=confidence,
        )
    except Exception as e:
        logger.error(f"获取用户难度等级失败: {e}")
        raise HTTPException(status_code=500, detail="获取难度等级失败")


@router.post("/user/{user_id}/update")
async def update_user_performance(
    user_id: str,
    task_id: str,
    success: bool,
    metrics: PerformanceMetricsRequest,
    service: DifficultyService = Depends(get_difficulty_service),
):
    """
    更新用户表现并调整难度

    Args:
        user_id: 用户ID
        task_id: 任务ID
        success: 是否成功完成
        metrics: 表现指标
        service: 难度服务依赖

    Returns:
        更新结果
    """
    try:
        # 转换硬件指标
        hardware_metrics = [
            HardwareOperationMetric(
                operation_type=m.get("operation_type", ""),
                success_count=m.get("success_count", 0),
                total_count=m.get("total_count", 0),
                average_response_time=m.get("average_response_time", 0.0),
                error_rate=m.get("error_rate", 0.0),
            )
            for m in metrics.hardware_metrics
        ]

        # 转换调试会话
        debugging_sessions = [
            DebuggingSession(
                session_id=s.get("session_id", ""),
                duration=float(s.get("duration", 0)),
                breakpoint_count=s.get("breakpoint_count", 0),
                step_count=s.get("step_count", 0),
                variable_inspection_count=s.get("variable_inspection_count", 0),
                completion_status=s.get("completion_status", "unknown"),
            )
            for s in metrics.debugging_sessions
        ]

        # 创建表现指标对象
        performance_metrics = TaskPerformanceMetrics(
            user_id=user_id,
            task_id=task_id,
            success_rate=metrics.success_rate,
            average_completion_time=metrics.average_completion_time,
            hint_usage_count=metrics.hint_usage_count,
            retry_count=metrics.retry_count,
            hardware_metrics=hardware_metrics,
            debugging_sessions=debugging_sessions,
            timestamp=None,  # 服务层会自动设置
        )

        # 更新用户表现
        new_score, new_level = service.update_user_performance(
            user_id, task_id, performance_metrics, success
        )

        return {
            "status": "success",
            "message": "用户表现更新成功",
            "user_id": user_id,
            "new_difficulty_score": new_score,
            "new_difficulty_level": new_level.value,
            "success": success,
        }
    except Exception as e:
        logger.error(f"更新用户表现失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户表现失败")


@router.get("/user/{user_id}/statistics", response_model=UserStatisticsResponse)
async def get_user_statistics(
    user_id: str, service: DifficultyService = Depends(get_difficulty_service)
):
    """
    获取用户详细统计信息

    Args:
        user_id: 用户ID
        service: 难度服务依赖

    Returns:
        用户统计信息
    """
    try:
        stats = service.get_user_statistics(user_id)
        if not stats:
            raise HTTPException(status_code=404, detail="用户不存在")

        return UserStatisticsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户统计失败")


@router.get(
    "/user/{user_id}/recommended-tasks", response_model=List[TaskRecommendationResponse]
)
async def get_recommended_tasks(
    user_id: str,
    count: int = Query(5, ge=1, le=20, description="推荐任务数量"),
    service: DifficultyService = Depends(get_difficulty_service),
):
    """
    获取推荐任务列表

    Args:
        user_id: 用户ID
        count: 推荐任务数量
        service: 难度服务依赖

    Returns:
        推荐任务列表
    """
    try:
        # 模拟可用任务数据(实际应该从任务服务获取)
        available_tasks = [
            {
                "task_id": "task_001",
                "title": "Python基础语法练习",
                "description": "学习Python基本语法和数据类型",
                "difficulty_score": 1.5,
                "estimated_time": 30,
                "tags": ["python", "basics"],
                "popularity_score": 0.9,
                "quality_score": 0.8,
            },
            {
                "task_id": "task_002",
                "title": "冒泡排序算法实现",
                "description": "实现经典的冒泡排序算法",
                "difficulty_score": 3.2,
                "estimated_time": 45,
                "tags": ["algorithm", "sorting"],
                "popularity_score": 0.8,
                "quality_score": 0.9,
            },
            {
                "task_id": "task_003",
                "title": "Flask Web应用开发",
                "description": "使用Flask框架开发简单的Web应用",
                "difficulty_score": 5.8,
                "estimated_time": 120,
                "tags": ["web", "flask", "backend"],
                "popularity_score": 0.7,
                "quality_score": 0.85,
            },
        ]

        recommended_tasks = service.get_suitable_tasks(user_id, available_tasks, count)

        response_tasks = []
        for task in recommended_tasks:
            response_tasks.append(
                TaskRecommendationResponse(
                    task_id=task["task_id"],
                    title=task["title"],
                    description=task["description"],
                    difficulty_score=task["difficulty_score"],
                    difficulty_level=service.calculator.score_to_level(
                        task["difficulty_score"]
                    ).value,
                    estimated_time=task["estimated_time"],
                    match_score=task.get("match_score", 0.0),
                    tags=task["tags"],
                )
            )

        return response_tasks
    except Exception as e:
        logger.error(f"获取推荐任务失败: {e}")
        raise HTTPException(status_code=500, detail="获取推荐任务失败")


@router.post("/user/{user_id}/manual-adjust")
async def manual_adjust_difficulty(
    user_id: str,
    new_difficulty_score: float,
    reason: str = "manual_override",
    service: DifficultyService = Depends(get_difficulty_service),
):
    """
    手动调整用户难度

    Args:
        user_id: 用户ID
        new_difficulty_score: 新的难度分数
        reason: 调整原因
        service: 难度服务依赖

    Returns:
        调整结果
    """
    try:
        success = service.manual_adjust_difficulty(
            user_id, new_difficulty_score, reason
        )

        if success:
            return {
                "status": "success",
                "message": "难度调整成功",
                "user_id": user_id,
                "new_difficulty_score": new_difficulty_score,
            }
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动调整难度失败: {e}")
        raise HTTPException(status_code=500, detail="手动调整难度失败")


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_difficulty_leaderboard(
    limit: int = Query(10, ge=1, le=100, description="排行榜数量"),
    service: DifficultyService = Depends(get_difficulty_service),
):
    """
    获取难度排行榜

    Args:
        limit: 排行榜数量
        service: 难度服务依赖

    Returns:
        难度排行榜
    """
    try:
        leaderboard = service.get_leaderboard(limit)
        return leaderboard
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail="获取排行榜失败")


@router.get("/levels/info")
async def get_difficulty_levels_info():
    """
    获取难度等级信息

    Returns:
        所有难度等级的详细信息
    """
    try:
        from ..models.difficulty_level import DIFFICULTY_LEVELS, DifficultyLevel

        levels_info = {}
        for level in DifficultyLevel:
            level_info = DIFFICULTY_LEVELS[level]
            levels_info[level.value] = {
                "description": level_info["description"],
                "score_range": level_info["score_range"],
                "characteristics": level_info["characteristics"],
                "target_users": level_info["target_users"],
            }

        return {"levels": levels_info, "total_levels": len(DIFFICULTY_LEVELS)}
    except Exception as e:
        logger.error(f"获取难度等级信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取难度等级信息失败")
