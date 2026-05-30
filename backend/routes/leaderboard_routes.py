"""
AI-Edu 积分排行榜 API 路由
提供个人积分统计、多维度排行榜等功能
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.leaderboard import LeaderboardPeriod, LeaderboardType
from models.user import User
from utils.dependencies import get_current_user_sync
from services.leaderboard_service import LeaderboardService, get_leaderboard_service

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/org/{org_id}/leaderboard", tags=["积分排行榜"])


# ==================== 个人积分 ====================


@router.get("/my/points")
async def get_my_points(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的积分信息

    Returns:
        积分详情，包括总积分、可用积分、消费积分和来源明细

    示例:
        GET /api/v1/org/1/leaderboard/my/points

        Response:
        {
            "success": true,
            "data": {
                "total_points": 1500,
                "available_points": 1200,
                "consumed_points": 300,
                "points_breakdown": {
                    "course_completion": 500,
                    "achievement_unlock": 300,
                    "quiz_perfect_score": 150
                }
            }
        }
    """
    try:
        service = get_leaderboard_service(db)
        points = service.get_user_points(current_user.id)  # type: ignore[arg-type]

        return {"success": True, "data": points.to_dict()}

    except Exception as e:
        logger.error(f"获取积分信息失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my/points/history")
async def get_my_points_history(
    org_id: int,
    limit: int = Query(50, ge=1, le=200, description="记录数量"),
    transaction_type: Optional[str] = Query(None, description="交易类型（earn/spend）"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的积分流水

    Args:
        limit: 返回记录数量（1-200）
        transaction_type: 交易类型过滤（可选）

    Returns:
        积分流水列表
    """
    try:
        service = get_leaderboard_service(db)
        history = service.get_points_history(
            user_id=current_user.id,  # type: ignore[arg-type]
            limit=limit,
            transaction_type=transaction_type,
        )

        return {
            "success": True,
            "count": len(history),
            "data": [tx.to_dict() for tx in history],
        }

    except Exception as e:
        logger.error(f"获取积分流水失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my/statistics")
async def get_my_statistics(
    org_id: int,
    refresh: bool = Query(False, description="是否刷新统计数据"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我的学习统计信息

    Args:
        refresh: 是否刷新统计数据

    Returns:
        统计数据，包括学习时长、完成课程数、平均分等
    """
    try:
        service = get_leaderboard_service(db)

        if refresh:
            stats = service.update_user_statistics(current_user.id)  # type: ignore[arg-type]
        else:
            stats = service.get_user_statistics(current_user.id)  # type: ignore[arg-type]

        return {"success": True, "data": stats.to_dict()}

    except Exception as e:
        logger.error(f"获取统计数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 排行榜查询 ====================


@router.get("/{leaderboard_type}")
async def get_leaderboard(
    org_id: int,
    leaderboard_type: str,
    period: str = Query(
        "all_time", description="周期类型（daily/weekly/monthly/all_time）"
    ),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取排行榜

    Args:
        leaderboard_type: 排行榜类型
            - total_points: 总积分榜
            - study_time: 学习时长榜
            - courses_completed: 完成课程数榜
            - quiz_score: 测验平均分榜
            - achievements: 成就数量榜
            - code_executions: 代码执行次数榜
        period: 周期类型
            - daily: 日榜
            - weekly: 周榜
            - monthly: 月榜
            - all_time: 总榜
        limit: 返回数量（1-500）

    Returns:
        排行榜列表，包含排名、用户信息、分数

    示例:
        GET /api/v1/org/1/leaderboard/total_points?period=all_time&limit=10

        Response:
        {
            "success": true,
            "count": 10,
            "leaderboard_type": "total_points",
            "period": "all_time",
            "data": [
                {
                    "rank": 1,
                    "user_id": 123,
                    "username": "学霸小明",
                    "score": 5000,
                    "score_type": "total_points",
                    "rank_change": 0
                },
                ...
            ]
        }
    """
    try:
        service = get_leaderboard_service(db)

        # 验证参数
        try:
            lb_type = LeaderboardType(leaderboard_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的排行榜类型：{leaderboard_type}。有效值：{[t.value for t in LeaderboardType]}",
            )

        try:
            lb_period = LeaderboardPeriod(period)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的周期类型：{period}。有效值：{[p.value for p in LeaderboardPeriod]}",
            )

        # 获取排行榜
        leaderboard = service.get_leaderboard(
            leaderboard_type=lb_type, period=lb_period, limit=limit, org_id=org_id
        )

        return {
            "success": True,
            "count": len(leaderboard),
            "leaderboard_type": leaderboard_type,
            "period": period,
            "data": leaderboard,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排行榜失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my/rank/{leaderboard_type}")
async def get_my_rank(
    org_id: int,
    leaderboard_type: str,
    period: str = Query("all_time", description="周期类型"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取我在排行榜中的排名

    Args:
        leaderboard_type: 排行榜类型（同上）
        period: 周期类型

    Returns:
        用户的排名信息
    """
    try:
        service = get_leaderboard_service(db)

        try:
            lb_type = LeaderboardType(leaderboard_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"无效的排行榜类型：{leaderboard_type}"
            )

        try:
            lb_period = LeaderboardPeriod(period)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的周期类型：{period}")

        # 获取排名
        rank_info = service.get_user_rank(
            user_id=current_user.id,  # type: ignore[arg-type]
            leaderboard_type=lb_type,
            period=lb_period,
        )

        return {"success": True, "data": rank_info}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排名失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 积分操作（演示用） ====================


@router.post("/my/points/earn")
async def earn_points_demo(
    org_id: int,
    amount: int = Query(..., ge=1, le=1000, description="积分金额"),
    reason: str = Query(..., description="获得积分原因"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获得积分（演示接口，实际应通过成就、学习等行为自动获得）

    Args:
        amount: 积分金额（1-1000）
        reason: 获得积分的原因

    Returns:
        更新后的积分信息
    """
    try:
        service = get_leaderboard_service(db)
        points = service.add_points(
            user_id=current_user.id, amount=amount, reason=reason  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "data": points.to_dict(),
            "message": f"获得 {amount} 积分！",
        }

    except Exception as e:
        logger.error(f"获得积分失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/my/points/spend")
async def spend_points_demo(
    org_id: int,
    amount: int = Query(..., ge=1, le=1000, description="积分金额"),
    reason: str = Query(..., description="消费积分原因"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    消费积分（演示接口）

    Args:
        amount: 积分金额（1-1000）
        reason: 消费积分的原因

    Returns:
        更新后的积分信息
    """
    try:
        service = get_leaderboard_service(db)
        points = service.spend_points(
            user_id=current_user.id, amount=amount, reason=reason  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "data": points.to_dict(),
            "message": f"消费 {amount} 积分！",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"消费积分失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计信息 ====================


@router.get("/stats/overview")
async def get_leaderboard_stats_overview(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取排行榜统计概览

    Returns:
        各类型排行榜的参与人数统计
    """
    from models.leaderboard import UserStatistics

    try:
        # 统计参与人数
        total_users = db.query(UserStatistics).count()

        # 各维度有数据的用户数
        active_learners = (
            db.query(UserStatistics)
            .filter(UserStatistics.total_study_time_minutes > 0)
            .count()
        )

        course_completers = (
            db.query(UserStatistics)
            .filter(UserStatistics.courses_completed > 0)
            .count()
        )

        quiz_takers = (
            db.query(UserStatistics).filter(UserStatistics.quizzes_taken > 0).count()
        )

        return {
            "success": True,
            "data": {
                "total_users": total_users,
                "active_learners": active_learners,
                "course_completers": course_completers,
                "quiz_takers": quiz_takers,
            },
        }

    except Exception as e:
        logger.error(f"获取统计概览失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
