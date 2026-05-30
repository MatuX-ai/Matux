"""
AI-Edu 智能推荐 API 路由
提供个性化课程推荐、学习路径规划等功能
"""

import logging
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync
from services.recommendation_service import (
    RecommendationService,
    get_recommendation_service,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/org/{org_id}/recommendations", tags=["AI 智能推荐"])


# ==================== 课程推荐 ====================


@router.get("/courses")
async def recommend_courses(
    org_id: int,
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    difficulty_min: Optional[int] = Query(None, ge=1, le=5, description="最低难度"),
    difficulty_max: Optional[int] = Query(None, ge=1, le=5, description="最高难度"),
    skill_category: Optional[str] = Query(None, description="技能分类"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    为用户推荐个性化课程列表

    Args:
        org_id: 组织 ID
        limit: 推荐数量（1-50）
        difficulty_min: 最低难度等级
        difficulty_max: 最高难度等级
        skill_category: 技能分类过滤
        db: 数据库会话
        current_user: 当前用户

    Returns:
        推荐课程列表，包含推荐理由和匹配分数

    示例:
        GET /api/v1/org/1/recommendations/courses?limit=10&difficulty_max=3

        Response:
        {
            "success": true,
            "count": 10,
            "data": [
                {
                    "course_id": 123,
                    "course_name": "Python 函数入门",
                    "difficulty_level": 2,
                    "score": 0.92,
                    "reasons": [
                        {
                            "type": "difficulty_perfect",
                            "description": "难度非常适合你当前的水平"
                        },
                        {
                            "type": "interest_match",
                            "description": "这门课程符合你的兴趣：programming"
                        }
                    ],
                    "algorithm": "hybrid"
                }
            ]
        }
    """
    try:
        service = get_recommendation_service(db)

        # 构建过滤条件
        filters = {}
        if difficulty_min is not None:
            filters["difficulty_min"] = difficulty_min
        if difficulty_max is not None:
            filters["difficulty_max"] = difficulty_max
        if skill_category:
            filters["skill_category"] = skill_category

        # 获取推荐
        recommendations = service.recommend_courses(
            user_id=cast(int, current_user.id), limit=limit, filters=filters
        )

        return {"success": True, "count": len(recommendations), "data": recommendations}

    except Exception as e:
        logger.error(f"推荐课程失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学习路径规划 ====================


@router.post("/learning-path")
async def generate_learning_path(
    org_id: int,
    request: Dict[str, Any] = Body(..., description="学习路径生成请求"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    生成个性化学习路径

    Args:
        org_id: 组织 ID
        request: 请求体
            {
                "target_skills": ["python_basics", "functions"],  # 目标技能
                "time_commitment_minutes": 120  # 可用时间（分钟）
            }
        db: 数据库会话
        current_user: 当前用户

    Returns:
        学习路径规划

    示例:
        POST /api/v1/org/1/recommendations/learning-path
        {
            "target_skills": ["python_basics"],
            "time_commitment_minutes": 60
        }

        Response:
        {
            "success": true,
            "data": {
                "user_id": 123,
                "target_skills": ["python_basics"],
                "time_commitment": 60,
                "recommended_sequence": [
                    {
                        "course_id": 1,
                        "estimated_duration": 30,
                        "difficulty": 1,
                        "skills_covered": ["python_basics", "variables"]
                    },
                    {
                        "course_id": 2,
                        "estimated_duration": 25,
                        "difficulty": 2,
                        "skills_covered": ["functions", "parameters"]
                    }
                ],
                "total_estimated_time": 55,
                "difficulty_progression": "循序渐进"
            }
        }
    """
    try:
        service = get_recommendation_service(db)

        target_skills = request.get("target_skills", [])
        time_commitment = request.get("time_commitment_minutes", 60)

        if not target_skills:
            raise HTTPException(status_code=400, detail="请指定目标技能列表")

        learning_path = service.generate_learning_path(
            user_id=cast(int, current_user.id),
            target_skills=target_skills,
            time_commitment_minutes=time_commitment,
        )

        return {"success": True, "data": learning_path}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成学习路径失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 用户画像管理 ====================


@router.get("/user-profile")
async def get_user_profile(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取用户学习画像

    Returns:
        用户学习画像详情，包括：
        - 学习风格
        - 兴趣偏好
        - 能力维度
        - 知识掌握程度
        - 学习统计

    示例:
        GET /api/v1/org/1/recommendations/user-profile

        Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "user_id": 123,
                "learning_style": "visual",
                "preferred_content_type": "video",
                "ability_dimensions": {
                    "logical_reasoning": {"score": 75, "level": "intermediate"}
                },
                "interest_preferences": [
                    {"category": "game_development", "interest_score": 90}
                ],
                "knowledge_mastery": {
                    "python_basics": 0.8
                },
                "total_study_time_minutes": 600,
                "completed_courses_count": 5,
                "average_quiz_score": 85.5
            }
        }
    """
    try:
        service = get_recommendation_service(db)
        profile = service.get_or_create_user_profile(cast(int, current_user.id))

        return {"success": True, "data": profile.to_dict()}

    except Exception as e:
        logger.error(f"获取用户画像失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/user-profile/preferences")
async def update_learning_preferences(
    org_id: int,
    preferences: Dict[str, Any] = Body(..., description="学习偏好配置"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    更新学习偏好

    Args:
        org_id: 组织 ID
        preferences: 偏好配置
            {
                "learning_style": "visual",           # 学习风格
                "preferred_content_type": "video",    # 内容类型偏好
                "interest_preferences": [...],         # 兴趣偏好
                "recommendation_weights": {...}       # 推荐权重
            }
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的用户画像
    """
    try:
        service = get_recommendation_service(db)
        profile = service.update_user_profile(cast(int, current_user.id), preferences)

        return {"success": True, "data": profile.to_dict(), "message": "学习偏好已更新"}

    except Exception as e:
        logger.error(f"更新学习偏好失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 反馈收集 ====================


@router.post("/feedback/{recommendation_id}")
async def submit_feedback(
    org_id: int,
    recommendation_id: int,
    feedback: Dict[str, Any] = Body(..., description="反馈信息"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    提交对推荐的反馈

    Args:
        org_id: 组织 ID
        recommendation_id: 推荐记录 ID
        feedback: 反馈信息
            {
                "clicked": true,          # 是否点击
                "completed": false,       # 是否完成（可选）
                "rating": 5,              # 评分（可选）
                "feedback_text": "很好"   # 文字反馈（可选）
            }

    Returns:
        操作结果
    """
    try:
        service = get_recommendation_service(db)

        user_clicked = feedback.get("clicked", False)
        user_completed = feedback.get("completed", False)
        user_rating = feedback.get("rating")
        feedback_text = feedback.get("feedback_text")

        service.submit_feedback(
            recommendation_id=recommendation_id,
            user_clicked=user_clicked,
            user_completed=user_completed,
            user_rating=user_rating,
            feedback_text=feedback_text,
        )

        return {"success": True, "message": "反馈已提交，感谢！"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"提交反馈失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 推荐统计 ====================


@router.get("/stats")
async def get_recommendation_statistics(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取推荐统计信息

    Returns:
        统计数据
    """
    from sqlalchemy import func

    from models.recommendation import RecommendationRecord

    try:
        # 总推荐数
        total_recommendations = (
            db.query(RecommendationRecord)
            .filter(RecommendationRecord.user_id == current_user.id)
            .count()
        )

        # 点击数
        clicked_count = (
            db.query(RecommendationRecord)
            .filter(
                and_(
                    RecommendationRecord.user_id == current_user.id,
                    RecommendationRecord.user_clicked == True,
                )
            )
            .count()
        )

        # 完成数
        completed_count = (
            db.query(RecommendationRecord)
            .filter(
                and_(
                    RecommendationRecord.user_id == current_user.id,
                    RecommendationRecord.user_completed == True,
                )
            )
            .count()
        )

        # 计算点击率和完成率
        click_rate = (
            (clicked_count / total_recommendations * 100)
            if total_recommendations > 0
            else 0
        )
        completion_rate = (
            (completed_count / total_recommendations * 100)
            if total_recommendations > 0
            else 0
        )

        return {
            "success": True,
            "data": {
                "total_recommendations": total_recommendations,
                "clicked_count": clicked_count,
                "completed_count": completed_count,
                "click_rate": round(click_rate, 2),
                "completion_rate": round(completion_rate, 2),
            },
        }

    except Exception as e:
        logger.error(f"获取推荐统计失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
