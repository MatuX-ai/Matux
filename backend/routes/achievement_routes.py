"""
AI-Edu 成就系统 API 路由
提供成就管理、用户成就展示、进度追踪等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.achievement import Achievement, AchievementCategory, AchievementType
from models.user import User
from utils.dependencies import get_current_user_sync
from services.achievement_service import AchievementService, get_achievement_service

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/org/{org_id}/achievements", tags=["成就系统"])


# ==================== 成就管理（管理员） ====================


@router.post("/admin/create")
async def create_achievement(
    org_id: int,
    achievement_data: Dict[str, Any] = Body(..., description="成就配置数据"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    创建新成就（需要管理员权限）

    Args:
        org_id: 组织 ID
        achievement_data: 成就配置
        {
            "name": "成就名称",
            "description": "成就描述",
            "category": "learning|coding|quiz|social|special",
            "achievement_type": "cumulative|single|sequence|hidden",
            "badge_icon": "/badges/icon.png",
            "badge_color": "#FFD700",
            "badge_rarity": "common|rare|epic|legendary",
            "unlock_condition": {...},
            "points_reward": 100,
            "is_hidden": false
        }
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的成就详情
    """
    # TODO: 添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    try:
        service = get_achievement_service(db)
        achievement = service.create_achievement(achievement_data)

        return {"success": True, "data": achievement.to_dict()}

    except Exception as e:
        logger.error(f"创建成就失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/{achievement_id}")
async def update_achievement(
    org_id: int,
    achievement_id: int,
    updates: Dict[str, Any] = Body(..., description="更新字段"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    更新成就信息（需要管理员权限）
    """
    # TODO: 添加管理员权限检查

    try:
        service = get_achievement_service(db)
        achievement = service.update_achievement(achievement_id, updates)

        if not achievement:
            raise HTTPException(status_code=404, detail="成就不存在")

        return {"success": True, "data": achievement.to_dict()}

    except Exception as e:
        logger.error(f"更新成就失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/{achievement_id}")
async def delete_achievement(
    org_id: int,
    achievement_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    停用成就（软删除，需要管理员权限）
    """
    # TODO: 添加管理员权限检查

    try:
        service = get_achievement_service(db)
        success = service.delete_achievement(achievement_id)

        if not success:
            raise HTTPException(status_code=404, detail="成就不存在")

        return {"success": True, "message": f"成就已停用"}

    except Exception as e:
        logger.error(f"停用成就失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/list")
async def list_all_achievements(
    org_id: int,
    category: Optional[str] = Query(None, description="成就分类"),
    achievement_type: Optional[str] = Query(None, description="成就类型"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取所有成就列表（管理员视图，包含隐藏成就）
    """
    # TODO: 添加管理员权限检查

    try:
        service = get_achievement_service(db)
        achievements = service.list_achievements(
            category=category,
            achievement_type=achievement_type,
            is_active=True,
            limit=limit,
            offset=offset,
        )

        total = (
            service.db.query(Achievement).filter(Achievement.is_active == True).count()
        )

        return {
            "success": True,
            "count": len(achievements),
            "total": total,
            "data": [ach.to_dict() for ach in achievements],
        }

    except Exception as e:
        logger.error(f"获取成就列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 用户成就（普通用户） ====================


@router.get("/my/list")
async def get_my_achievements(
    org_id: int,
    include_locked: bool = Query(False, description="是否包含未解锁成就"),
    include_hidden: bool = Query(False, description="是否包含隐藏成就（仅已解锁）"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的成就列表

    Args:
        org_id: 组织 ID
        include_locked: 是否显示未解锁的成就
        include_hidden: 是否显示隐藏成就（只有已解锁的才会显示）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        成就列表
    """
    try:
        service = get_achievement_service(db)
        user_achievements = service.get_user_achievements(
            user_id=current_user.id,  # type: ignore[arg-type]
            include_locked=include_locked,
            include_hidden=include_hidden,
        )

        return {
            "success": True,
            "count": len(user_achievements),
            "data": [ua.to_dict() for ua in user_achievements],
        }

    except Exception as e:
        logger.error(f"获取用户成就失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my/statistics")
async def get_my_achievement_statistics(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的成就统计信息

    Returns:
        统计数据，包含：
        - 总成就数
        - 已解锁数
        - 完成率
        - 各分类详情
    """
    try:
        service = get_achievement_service(db)
        stats = service.get_progress_statistics(user_id=current_user.id)  # type: ignore[arg-type]

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"获取成就统计失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/my/{achievement_id}/claim")
async def claim_achievement_reward(
    org_id: int,
    achievement_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    领取成就奖励

    Args:
        org_id: 组织 ID
        achievement_id: 成就 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        奖励信息
    """
    try:
        service = get_achievement_service(db)
        reward = service.claim_achievement_reward(
            user_id=current_user.id, achievement_id=achievement_id  # type: ignore[arg-type]
        )

        return {"success": True, "data": reward, "message": "奖励领取成功！"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"领取成就奖励失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 成就进度追踪 ====================


@router.post("/progress/update")
async def update_achievement_progress(
    org_id: int,
    metric_name: str = Body(..., description="指标名称"),
    metric_value: int = Body(..., description="指标值"),
    period_type: str = Body("all_time", description="周期类型"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    更新成就进度指标

    使用场景：
    - 学习完成后更新学习时长
    - 代码执行后更新执行次数
    - 测验完成后更新分数

    Args:
        org_id: 组织 ID
        metric_name: 指标名称（如 study_time_minutes, code_executions）
        metric_value: 指标值
        period_type: 周期类型（daily, weekly, monthly, all_time）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        新解锁的成就列表
    """
    try:
        service = get_achievement_service(db)
        unlocked = service.update_progress(
            user_id=current_user.id,  # type: ignore[arg-type]
            metric_name=metric_name,
            metric_value=metric_value,
            period_type=period_type,
        )

        response = {
            "success": True,
            "updated_metric": {
                "name": metric_name,
                "value": metric_value,
                "period": period_type,
            },
            "newly_unlocked": [],
        }

        # 如果有新解锁的成就
        if unlocked:
            response["newly_unlocked"] = [
                {
                    "achievement_id": u["achievement"]["id"],
                    "achievement_name": u["achievement"]["name"],
                    "badge_icon": u["achievement"]["badge_icon"],
                    "points_reward": u["achievement"]["points_reward"],
                }
                for u in unlocked
            ]

            # TODO: 触发 WebSocket 通知推送
            # await broadcast_achievement_unlocked(current_user.id, unlocked)

        return response

    except Exception as e:
        logger.error(f"更新成就进度失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/current")
async def get_current_progress(
    org_id: int,
    metric_name: Optional[str] = Query(None, description="指标名称"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取当前成就进度

    Args:
        org_id: 组织 ID
        metric_name: 可选，查询特定指标
        db: 数据库会话
        current_user: 当前用户

    Returns:
        进度数据
    """
    from sqlalchemy import and_

    from models.achievement import AchievementProgress

    try:
        query = db.query(AchievementProgress).filter(
            AchievementProgress.user_id == current_user.id
        )

        if metric_name:
            query = query.filter(AchievementProgress.metric_name == metric_name)

        progress_records = query.all()

        return {
            "success": True,
            "count": len(progress_records),
            "data": [pr.to_dict() for pr in progress_records],
        }

    except Exception as e:
        logger.error(f"获取进度数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 初始化与工具 ====================


@router.post("/admin/initialize")
async def initialize_achievements(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    初始化预定义成就（管理员操作）

    一次性导入系统预定义的成就模板
    """
    # TODO: 添加管理员权限检查

    try:
        service = get_achievement_service(db)
        count = service.initialize_default_achievements()

        return {
            "success": True,
            "initialized_count": count,
            "message": f"成功初始化 {count} 个成就",
        }

    except Exception as e:
        logger.error(f"初始化成就失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{achievement_id}")
async def get_achievement_detail(
    org_id: int,
    achievement_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取成就详情
    """
    try:
        service = get_achievement_service(db)
        achievement = service.get_achievement(achievement_id)

        if not achievement:
            raise HTTPException(status_code=404, detail="成就不存在")

        # 检查是否应该对用户可见
        ih: bool = achievement.is_hidden  # type: ignore[assignment]
        if ih:
            user_achievement = service.get_user_achievement(
                current_user.id, achievement_id  # type: ignore[arg-type]
            )
            if user_achievement is None:
                # 隐藏成就且未解锁，返回模糊信息
                return {
                    "success": True,
                    "data": {
                        "id": achievement.id,
                        "name": "???",
                        "description": "???",
                        "is_hidden": True,
                        "is_unlocked": False,
                    },
                }
            iu: bool = user_achievement.is_unlocked  # type: ignore[assignment]
            if not iu:
                # 隐藏成就且未解锁，返回模糊信息
                return {
                    "success": True,
                    "data": {
                        "id": achievement.id,
                        "name": "???",
                        "description": "???",
                        "is_hidden": True,
                        "is_unlocked": False,
                    },
                }

        return {"success": True, "data": achievement.to_dict()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成就详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
