import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from utils.dependencies import get_current_user_sync
from models.user import User
from services.ar_reward_service import ARSceneCompletionData, ar_reward_service
from services.reward_event_bus import RewardEvent, reward_event_bus

router = APIRouter(prefix="/ar", tags=["AR Rewards"])
logger = logging.getLogger(__name__)


class ARSceneCompletionRequest(BaseModel):
    """AR场景完成请求模型"""

    event_type: str
    accuracy: float
    components_placed: int
    total_time: float
    bonus_points: int
    scene_id: str
    timestamp: str
    user_id: Optional[int] = None


class ARElementValidationRequest(BaseModel):
    """AR元件验证请求模型"""

    event_type: str
    component_type: str
    accuracy: float
    is_first_placement: bool = False
    user_id: Optional[int] = None


@router.post("/rewards/scene-completed")
async def handle_scene_completion(
    request: ARSceneCompletionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sync),
):
    """处理AR场景完成奖励"""
    try:
        # 构造场景完成数据
        scene_data = ARSceneCompletionData(
            user_id=current_user.id,
            scene_id=request.scene_id,
            accuracy=request.accuracy,
            completion_time=request.total_time,
            components_placed=request.components_placed,
            total_components=4,  # 假设有4个必需组件
            bonus_points=request.bonus_points,
            timestamp=datetime.fromisoformat(request.timestamp.replace("Z", "+00:00")),
        )

        # 发布奖励事件到事件总线
        event = RewardEvent(
            event_type="ar_scene_completed",
            user_id=current_user.id,
            data={
                "accuracy": scene_data.accuracy,
                "completion_time": scene_data.completion_time,
                "components_placed": scene_data.components_placed,
                "total_components": scene_data.total_components,
                "bonus_points": scene_data.bonus_points,
                "scene_id": scene_data.scene_id,
            },
            timestamp=scene_data.timestamp,
        )

        background_tasks.add_task(reward_event_bus.publish, event)

        logger.info(
            f"AR场景完成事件已接收: 用户{current_user.id}, 场景{request.scene_id}"
        )

        return {
            "success": True,
            "message": "场景完成事件已处理",
            "data": {
                "user_id": current_user.id,
                "scene_id": request.scene_id,
                "estimated_reward": 100 + request.bonus_points,  # 估算奖励
            },
        }

    except Exception as e:
        logger.error(f"处理AR场景完成事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/rewards/component-validated")
async def handle_component_validation(
    request: ARElementValidationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_sync),
):
    """处理AR元件验证奖励"""
    try:
        # 发布元件验证事件
        event = RewardEvent(
            event_type="ar_component_validated",
            user_id=current_user.id,
            data={
                "component_type": request.component_type,
                "accuracy": request.accuracy,
                "is_first_placement": request.is_first_placement,
            },
            timestamp=datetime.now(),
        )

        background_tasks.add_task(reward_event_bus.publish, event)

        logger.info(
            f"AR元件验证事件已接收: 用户{current_user.id}, 元件{request.component_type}"
        )

        return {
            "success": True,
            "message": "元件验证事件已处理",
            "data": {
                "user_id": current_user.id,
                "component_type": request.component_type,
                "accuracy": request.accuracy,
            },
        }

    except Exception as e:
        logger.error(f"处理AR元件验证事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/rewards/summary")
async def get_ar_rewards_summary(current_user: User = Depends(get_current_user_sync)):
    """获取用户AR奖励摘要"""
    try:
        summary = await ar_reward_service.get_user_ar_rewards_summary(current_user.id)

        return {"success": True, "data": summary}

    except Exception as e:
        logger.error(f"获取AR奖励摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/achievements/unlocked")
async def get_unlocked_achievements(current_user: User = Depends(get_current_user_sync)):
    """获取用户已解锁的成就"""
    try:
        from ..services.achievement_badge_system import achievement_system

        achievements = achievement_system.get_user_achievements(current_user.id)
        rarity_stats = achievement_system.get_badge_rarity_stats(current_user.id)
        total_points = achievement_system.get_total_points(current_user.id)

        return {
            "success": True,
            "data": {
                "achievements": [
                    {
                        "id": badge.badge_id,
                        "name": badge.name,
                        "description": badge.description,
                        "icon_url": badge.icon_url,
                        "rarity": badge.rarity,
                        "point_value": badge.point_value,
                        "unlocked_at": (
                            badge.unlocked_at.isoformat() if badge.unlocked_at else None
                        ),
                    }
                    for badge in achievements
                ],
                "statistics": {
                    "total_achievements": len(achievements),
                    "rarity_distribution": rarity_stats,
                    "total_points": total_points,
                },
            },
        }

    except Exception as e:
        logger.error(f"获取成就信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/events/test-scene-completion")
async def test_scene_completion(
    background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user_sync)
):
    """测试场景完成事件（开发用）"""
    try:
        # 模拟一个完美的场景完成事件
        test_data = ARSceneCompletionData(
            user_id=current_user.id,
            scene_id="test_scene_001",
            accuracy=96.5,
            completion_time=95.0,
            components_placed=4,
            total_components=4,
            bonus_points=120,
            timestamp=datetime.now(),
        )

        event = RewardEvent(
            event_type="ar_scene_completed",
            user_id=current_user.id,
            data={
                "accuracy": test_data.accuracy,
                "completion_time": test_data.completion_time,
                "components_placed": test_data.components_placed,
                "total_components": test_data.total_components,
                "bonus_points": test_data.bonus_points,
                "scene_id": test_data.scene_id,
            },
            timestamp=test_data.timestamp,
        )

        background_tasks.add_task(reward_event_bus.publish, event)

        return {
            "success": True,
            "message": "测试事件已发布",
            "test_data": {
                "user_id": current_user.id,
                "accuracy": test_data.accuracy,
                "completion_time": test_data.completion_time,
                "estimated_total_reward": 220,  # 100基础 + 120奖励
            },
        }

    except Exception as e:
        logger.error(f"测试场景完成事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")
