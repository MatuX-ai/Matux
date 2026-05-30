"""
联邦学习API路由
提供联邦学习系统的RESTful API接口
"""

from datetime import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ai_service.fl_models import FLParticipantInfo, FLTrainingConfig, FLTrainingProgress
from utils.dependencies import get_current_user_sync
from models.user import User
from services.federated_service import FederatedLearningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/federated", tags=["联邦学习"])


# 依赖注入
async def get_fl_service() -> FederatedLearningService:
    """获取联邦学习服务实例"""
    return FederatedLearningService.get_instance()


@router.post("/trainings/", response_model=dict)
async def start_federated_training(
    config: FLTrainingConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    启动联邦学习训练
    """
    try:
        logger.info(f"用户 {current_user.username} 请求启动联邦学习训练")

        # 权限检查
        if not current_user.has_permission("ai") and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")

        # 启动训练
        training_id = await fl_service.start_training(config)

        # 在后台启动监控任务
        background_tasks.add_task(fl_service.monitor_training_progress, training_id)

        return {
            "training_id": training_id,
            "message": "联邦学习训练已启动",
            "created_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"启动训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trainings/{training_id}", response_model=FLTrainingProgress)
async def get_training_status(
    training_id: str,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    获取训练状态
    """
    try:
        progress = await fl_service.get_training_status(training_id)
        if not progress:
            raise HTTPException(status_code=404, detail="训练不存在")
        return progress
    except Exception as e:
        logger.error(f"获取训练状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trainings/", response_model=List[FLTrainingProgress])
async def list_trainings(
    status: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    列出训练任务
    """
    try:
        trainings = await fl_service.list_trainings(status, limit)
        return trainings
    except Exception as e:
        logger.error(f"列出训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trainings/{training_id}/pause")
async def pause_training(
    training_id: str,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    暂停训练
    """
    try:
        if not current_user.has_permission("ai") and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")

        success = await fl_service.pause_training(training_id)
        if not success:
            raise HTTPException(status_code=400, detail="暂停训练失败")

        return {"message": "训练已暂停", "training_id": training_id}
    except Exception as e:
        logger.error(f"暂停训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trainings/{training_id}/resume")
async def resume_training(
    training_id: str,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    恢复训练
    """
    try:
        if not current_user.has_permission("ai") and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")

        success = await fl_service.resume_training(training_id)
        if not success:
            raise HTTPException(status_code=400, detail="恢复训练失败")

        return {"message": "训练已恢复", "training_id": training_id}
    except Exception as e:
        logger.error(f"恢复训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trainings/{training_id}")
async def stop_training(
    training_id: str,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    停止训练
    """
    try:
        if not current_user.has_permission("ai") and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")

        success = await fl_service.stop_training(training_id)
        if not success:
            raise HTTPException(status_code=400, detail="停止训练失败")

        return {"message": "训练已停止", "training_id": training_id}
    except Exception as e:
        logger.error(f"停止训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/participants/", response_model=List[FLParticipantInfo])
async def list_participants(
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    列出所有参与者
    """
    try:
        participants = await fl_service.list_participants()
        return participants
    except Exception as e:
        logger.error(f"列出参与者失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/participants/{participant_id}", response_model=FLParticipantInfo)
async def get_participant_info(
    participant_id: str,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    获取参与者详细信息
    """
    try:
        participant = await fl_service.get_participant_info(participant_id)
        if not participant:
            raise HTTPException(status_code=404, detail="参与者不存在")
        return participant
    except Exception as e:
        logger.error(f"获取参与者信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/status", response_model=dict)
async def get_cluster_status(
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    获取集群状态
    """
    try:
        status = await fl_service.get_cluster_status()
        return status
    except Exception as e:
        logger.error(f"获取集群状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/metrics", response_model=dict)
async def get_monitoring_metrics(
    training_id: Optional[str] = None,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    获取监控指标
    """
    try:
        metrics = await fl_service.get_monitoring_metrics(training_id, hours)
        return metrics
    except Exception as e:
        logger.error(f"获取监控指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts", response_model=dict)
async def get_active_alerts(
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    获取活跃告警
    """
    try:
        alerts = await fl_service.get_active_alerts()
        return alerts
    except Exception as e:
        logger.error(f"获取告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/participants/register", response_model=dict)
async def register_participant(
    participant_info: FLParticipantInfo,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    注册新的参与者
    """
    try:
        if not current_user.has_permission("ai") and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足")

        success = await fl_service.register_participant(participant_info)
        if not success:
            raise HTTPException(status_code=400, detail="参与者注册失败")

        return {
            "message": "参与者注册成功",
            "participant_id": participant_info.participant_id,
        }
    except Exception as e:
        logger.error(f"注册参与者失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configurations/validate", response_model=dict)
async def validate_training_config(
    config: FLTrainingConfig,
    current_user: User = Depends(get_current_active_user),
    fl_service: FederatedLearningService = Depends(get_fl_service),
):
    """
    验证训练配置
    """
    try:
        validation_result = await fl_service.validate_training_config(config)
        return validation_result
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict)
async def health_check(fl_service: FederatedLearningService = Depends(get_fl_service)):
    """
    健康检查
    """
    try:
        health_status = await fl_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
