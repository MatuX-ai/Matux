"""成就中心 API（桌面端 /api/v1/achievements）。

背景：
    桌面端入口只有组织级路由 /api/v1/org/{org_id}/achievements/*，
    前端成就中心调用 /gamification/achievements/badges 一律 404，
    只能退化为内置示例徽章。本模块提供扁平化成就查询（真实数据库）：
    全部成就定义 + 当前用户解锁状态 + 统计。
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from models.achievement import Achievement, UserAchievement
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils.database import get_db_session

router = APIRouter(prefix="/api/v1/achievements", tags=["成就系统"])

# 后端成就分类 → 前端 AchievementCategory 枚举值
_CATEGORY_MAP = {
    "learning": "learning",
    "coding": "experiment",
    "quiz": "challenge",
    "social": "social",
    "special": "hidden",
}

# 徽章图标：前端画廊把 icon 当 emoji 文本渲染，这里按分类给默认图标
_ICON_MAP = {
    "learning": "📚",
    "experiment": "💻",
    "challenge": "🏆",
    "social": "🤝",
    "hidden": "🌟",
}


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value)) if value is not None else ""


def _resolve_user_id(user_id: Optional[int], camel_user_id: Optional[int]) -> int:
    value = camel_user_id if camel_user_id is not None else user_id
    return int(value or 0)


def _load_unlocked(db: Session, user_id: int) -> Dict[int, UserAchievement]:
    if user_id <= 0:
        return {}
    rows = (
        db.execute(select(UserAchievement).where(UserAchievement.user_id == user_id))
        .scalars()
        .all()
    )
    return {row.achievement_id: row for row in rows}


def _load_achievements(db: Session, include_hidden: bool) -> List[Achievement]:
    stmt = select(Achievement).where(Achievement.is_active.is_(True))
    if not include_hidden:
        stmt = stmt.where(Achievement.is_hidden.is_(False))
    return db.execute(stmt.order_by(Achievement.display_order.asc())).scalars().all()


def _badge_payload(achievement: Achievement, record: Optional[UserAchievement]) -> Dict[str, Any]:
    category = _CATEGORY_MAP.get(_enum_value(achievement.category), "challenge")
    unlocked = bool(record and record.is_unlocked)
    return {
        "id": str(achievement.id),
        "name": achievement.name,
        "icon": _ICON_MAP.get(category, "🏆"),
        "description": achievement.description,
        "unlocked": unlocked,
        "unlockedDate": _iso(record.unlocked_at) if unlocked and record else None,
        "category": category,
        "rarity": (achievement.badge_rarity or "common").lower(),
        "points": achievement.points_reward or 0,
        "progress": float(record.progress or 0) if record else 0.0,
        "achievementType": _enum_value(achievement.achievement_type),
        "badgeColor": achievement.badge_color,
    }


def _streak_days(days: set) -> int:
    """从今天往前数连续天数。"""
    streak = 0
    cursor = date.today()
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _longest_streak(days: set) -> int:
    best = 0
    run = 0
    prev: Optional[date] = None
    for day in sorted(days):
        run = run + 1 if prev is not None and (day - prev).days == 1 else 1
        best = max(best, run)
        prev = day
    return best


@router.get("", summary="全部成就定义")
async def list_achievements(
    user_id: Optional[int] = Query(None, description="用户 ID（可空）"),
    userId: Optional[int] = Query(None, description="用户 ID（前端驼峰参数）"),
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db_session),
):
    """返回全部启用的成就定义，附带指定用户的解锁状态。"""
    uid = _resolve_user_id(user_id, userId)
    unlocked = _load_unlocked(db, uid)
    achievements = _load_achievements(db, include_hidden)
    items = [_badge_payload(a, unlocked.get(a.id)) for a in achievements]
    return {
        "success": True,
        "total": len(items),
        "unlocked": sum(1 for item in items if item["unlocked"]),
        "items": items,
    }


@router.get("/badges", summary="成就徽章列表")
async def list_badges(
    userId: Optional[int] = Query(None, description="用户 ID（前端驼峰参数）"),
    user_id: Optional[int] = Query(None, description="用户 ID"),
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db_session),
):
    """前端成就中心入口：返回 badges 数组 + 统计。"""
    uid = _resolve_user_id(user_id, userId)
    unlocked = _load_unlocked(db, uid)
    achievements = _load_achievements(db, include_hidden)
    badges = [_badge_payload(a, unlocked.get(a.id)) for a in achievements]
    return {
        "success": True,
        "badges": badges,
        "statistics": {
            "total": len(badges),
            "unlocked": sum(1 for badge in badges if badge["unlocked"]),
            "total_points": sum(
                badge["points"] for badge in badges if badge["unlocked"]
            ),
        },
    }


@router.get("/my", summary="我的成就（别名）")
async def list_my_achievements(
    userId: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db_session),
):
    return await list_badges(
        userId=userId,
        user_id=user_id,
        include_hidden=include_hidden,
        db=db,
    )


@router.get("/stats", summary="成就统计")
async def achievement_stats(
    userId: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """前端 AchievementStats 结构：积分 / 徽章数 / 连续天数。"""
    uid = _resolve_user_id(user_id, userId)
    unlocked = _load_unlocked(db, uid)
    achievements = _load_achievements(db, include_hidden=True)
    unlocked_records = [r for r in unlocked.values() if r.is_unlocked]

    days = {r.unlocked_at.date() for r in unlocked_records if r.unlocked_at}
    total_points = sum(
        (a.points_reward or 0)
        for a in achievements
        if a.id in unlocked and unlocked[a.id].is_unlocked
    )
    last_active = _iso(max(days)) if days else ""

    return {
        "totalPoints": total_points,
        "badgesCount": len(achievements),
        "unlockedCount": len(unlocked_records),
        "currentStreak": _streak_days(days),
        "longestStreak": _longest_streak(days),
        "lastActiveDate": last_active,
    }
