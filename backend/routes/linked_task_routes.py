"""
AI-Edu 联动任务 API 路由
提供跨平台任务的提交、评测和排行榜功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync
from services.task_orchestration_service import (
    TaskOrchestrationService,
    get_task_orchestration_service,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/v1/org/{org_id}/ai-edu/linked-tasks", tags=["联动任务管理"]
)


@router.post("/{task_id}/stage/1/submit")
async def submit_stage_1(
    org_id: int,
    task_id: str,
    model_file: UploadFile = File(..., description="AI 模型文件"),
    training_report: str = Form(..., description="训练报告 JSON"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    提交第一阶段 AI 模型训练结果

    Args:
        org_id: 组织 ID
        task_id: 任务 ID（如 'greenhouse_001'）
        model_file: AI 模型文件（.pth 或 .onnx）
        training_report: 训练报告（JSON 格式）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        评测结果和积分奖励

    Examples:
        POST /api/v1/org/1/ai-edu/linked-tasks/greenhouse_001/stage/1/submit
        Content-Type: multipart/form-data

        model_file: <plant_health_classifier.pth>
        training_report: '{"accuracy": 0.92, "loss": 0.15, "training_time_minutes": 25}'
    """
    try:
        import json

        report_data = json.loads(training_report)

        service = get_task_orchestration_service(db)

        result = await service.submit_stage1_result(
            user_id=current_user.id,  # type: ignore[arg-type]
            task_id=task_id,
            model_file=model_file,
            training_report=report_data,
        )

        if result["success"]:
            return {"success": True, "data": result, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "提交失败"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段 1 提交失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")


@router.post("/{task_id}/stage/2/submit")
async def submit_stage_2(
    org_id: int,
    task_id: str,
    hardware_control_code: str = Form(..., description="硬件控制代码"),
    system_logs: str = Form(None, description="系统日志 JSON 数组"),
    performance_metrics: str = Form(..., description="性能指标 JSON"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    提交第二阶段硬件模拟集成结果

    Args:
        org_id: 组织 ID
        task_id: 任务 ID
        hardware_control_code: 硬件控制代码（Python）
        system_logs: 系统运行日志（JSON 数组）
        performance_metrics: 性能指标（JSON）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        评测结果和积分奖励
    """
    try:
        import json

        # 解析日志和指标
        logs = json.loads(system_logs) if system_logs else []
        metrics = json.loads(performance_metrics)

        service = get_task_orchestration_service(db)

        result = await service.submit_stage2_result(
            user_id=current_user.id,  # type: ignore[arg-type]
            task_id=task_id,
            hardware_control_code=hardware_control_code,
            system_logs=logs,
            performance_metrics=metrics,
        )

        if result["success"]:
            return {"success": True, "data": result, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "提交失败"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"阶段 2 提交失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")


@router.get("/{task_id}/leaderboard")
async def get_leaderboard(
    org_id: int,
    task_id: str,
    stage: Optional[int] = Query(None, ge=1, le=3, description="阶段编号"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取任务排行榜

    Args:
        org_id: 组织 ID
        task_id: 任务 ID
        stage: 阶段编号（1/2/3，None 表示总分）
        limit: 返回数量限制
        db: 数据库会话
        current_user: 当前用户

    Returns:
        排行榜列表

    Examples:
        GET /api/v1/org/1/ai-edu/linked-tasks/greenhouse_001/leaderboard?limit=10
    """
    try:
        service = get_task_orchestration_service(db)

        leaderboard = await service.get_leaderboard(
            task_id=task_id, stage=stage, limit=limit
        )

        return {
            "success": True,
            "count": len(leaderboard),
            "data": leaderboard,
            "task_id": task_id,
            "stage": stage,
        }

    except Exception as e:
        logger.error(f"获取排行榜失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/my-submissions")
async def get_my_submissions(
    org_id: int,
    task_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的提交记录

    Args:
        org_id: 组织 ID
        task_id: 任务 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        提交记录列表
    """
    try:
        # ✅ 从数据库查询用户的提交记录
        from sqlalchemy import desc

        from models.ai_edu_rewards import AIEduLearningProgress

        # 构建查询
        query = db.query(AIEduLearningProgress).filter(
            AIEduLearningProgress.user_id == current_user.id
        )

        # 如果指定了 task_id，进行过滤
        if task_id:
            query = query.filter(AIEduLearningProgress.lesson_id.like(f"%{task_id}%"))

        # 按时间倒序排序
        query = query.order_by(desc(AIEduLearningProgress.updated_at))

        # 获取最近的 50 条记录
        submissions = query.limit(50).all()

        # 转换为提交记录格式
        submission_list = [
            {
                "submission_id": f"sub_{sub.id}",
                "lesson_id": sub.lesson_id,
                "stage": 1,  # 默认阶段 1
                "status": (
                    sub.status.value if hasattr(sub.status, "value") else sub.status
                ),
                "score": sub.quiz_score,
                "xp_earned": sub.points_earned,
                "submitted_at": sub.updated_at.isoformat() if sub.updated_at is not None else None,
            }
            for sub in submissions
        ]

        return {
            "success": True,
            "count": len(submission_list),
            "data": submission_list,
        }

    except Exception as e:
        logger.error(f"获取提交记录失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/details")
async def get_task_details(
    org_id: int,
    task_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取任务详情

    Args:
        org_id: 组织 ID
        task_id: 任务 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        任务详细信息
    """
    try:
        # TODO: 从数据库查询任务详情
        mock_task = {
            "task_id": task_id,
            "title": "智能温室监控系统",
            "description": "设计一套智能温室监控系统，实时监测植物生长环境并自动调节",
            "stages": [
                {
                    "stage": 1,
                    "name": "AI 模型训练",
                    "status": "available",
                    "xp_reward": 1000,
                    "deadline": "2026-03-20T23:59:59",
                },
                {
                    "stage": 2,
                    "name": "硬件模拟集成",
                    "status": "locked",
                    "xp_reward": 1500,
                    "deadline": "2026-03-25T23:59:59",
                },
                {
                    "stage": 3,
                    "name": "成果展示与竞赛",
                    "status": "locked",
                    "xp_reward": 2500,
                    "deadline": "2026-03-30T23:59:59",
                },
            ],
            "total_participants": 156,
            "your_progress": {
                "current_stage": 1,
                "completed_stages": 0,
                "total_xp": 0,
                "best_rank": None,
            },
        }

        return {"success": True, "data": mock_task}

    except Exception as e:
        logger.error(f"获取任务详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/register")
async def register_for_task(
    org_id: int,
    task_id: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    报名参加任务

    Args:
        org_id: 组织 ID
        task_id: 任务 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        报名结果
    """
    try:
        # TODO: 实现报名逻辑
        logger.info(f"用户{current_user.id}报名任务{task_id}")

        return {
            "success": True,
            "message": "报名成功！现在开始你的挑战吧！",
            "data": {
                "task_id": task_id,
                "registered_at": datetime.utcnow().isoformat(),
                "user_id": current_user.id,
            },
        }

    except Exception as e:
        logger.error(f"报名失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# 导入 datetime
from datetime import datetime
