"""
AI推荐服务API路由
提供统一的AI推荐接口 /api/ai/recommend
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.recommendation_service import RecommendationEngine as RecEngine

# 导入APM监控装饰器
from middleware.apm_middleware import (
    monitor_ai_operation,
    monitor_recommendation_endpoint,
)
from middleware.apm_monitoring import trace_endpoint
from models.user import User
from routes.auth_routes import get_current_user
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI推荐服务"])

# 全局推荐引擎实例
ai_recommendation_engine = RecEngine()


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化AI推荐引擎"""
    try:
        logger.info("AI推荐服务已启动")
    except Exception as e:
        logger.error(f"AI推荐服务启动失败: {e}")


@router.get("/recommend")
@trace_endpoint("ai.recommend")
@monitor_recommendation_endpoint
async def get_ai_recommendations(
    num_recommendations: int = Query(5, ge=1, le=20, description="推荐数量"),
    algorithm: str = Query(
        "hybrid", description="推荐算法类型: hybrid, collaborative, content, adaptive"
    ),
    include_metadata: bool = Query(True, description="是否包含详细元数据"),
    user_context: Optional[str] = Query(None, description="用户上下文信息"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI智能推荐接口
    统一的推荐服务入口，支持多种推荐算法

    Args:
        num_recommendations: 推荐数量 (1-20)
        algorithm: 推荐算法类型
            - hybrid: 混合推荐（默认）
            - collaborative: 协同过滤
            - content: 内容推荐
            - adaptive: 自适应推荐
        include_metadata: 是否包含详细的课程元数据
        user_context: 用户上下文信息（JSON字符串）
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        统一的推荐结果格式
    """
    try:
        # 根据算法类型选择推荐方法
        if algorithm == "adaptive":
            recommendations = (
                await ai_recommendation_engine.get_adaptive_recommendations(
                    current_user.id, db, num_recommendations
                )
            )
        elif algorithm == "hybrid":
            recommendations = await ai_recommendation_engine.get_recommendations(
                current_user.id, db, num_recommendations
            )
        else:
            # 对于其他算法类型，使用基础推荐
            recommendations = await ai_recommendation_engine.get_recommendations(
                current_user.id, db, num_recommendations
            )

        # 格式化响应
        response_data = {
            "user_id": current_user.id,
            "recommendations": recommendations,
            "algorithm_used": algorithm,
            "total_recommendations": len(recommendations),
            "include_metadata": include_metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 如果需要包含元数据，丰富推荐信息
        if include_metadata and recommendations:
            enriched_recommendations = []
            for rec in recommendations:
                # 这里可以根据需要添加更多的元数据处理逻辑
                enriched_rec = {
                    **rec,
                    "metadata": {
                        "generated_by": "ai_recommendation_engine",
                        "confidence_score": rec.get("score", 0.0),
                        "recommendation_reason": rec.get("type", "unknown"),
                    },
                }
                enriched_recommendations.append(enriched_rec)

            response_data["recommendations"] = enriched_recommendations

        logger.info(
            f"AI推荐成功: 用户 {current_user.id}, 算法 {algorithm}, 数量 {len(recommendations)}"
        )
        return response_data

    except Exception as e:
        logger.error(f"AI推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI推荐服务暂时不可用: {str(e)}")


@router.post("/recommend/batch")
@trace_endpoint("ai.recommend.batch")
@monitor_ai_operation("batch_recommendation")
async def batch_ai_recommendations(
    requests: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    批量AI推荐接口

    Args:
        requests: 推荐请求列表，每个请求包含推荐参数
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        批量推荐结果
    """
    try:
        batch_results = []

        for i, request_params in enumerate(requests):
            try:
                # 解析单个请求参数
                num_recs = request_params.get("num_recommendations", 3)
                algorithm = request_params.get("algorithm", "hybrid")
                request_params.get("context", {})

                # 执行推荐
                if algorithm == "adaptive":
                    recommendations = (
                        await ai_recommendation_engine.get_adaptive_recommendations(
                            current_user.id, db, num_recs
                        )
                    )
                else:
                    recommendations = (
                        await ai_recommendation_engine.get_recommendations(
                            current_user.id, db, num_recs
                        )
                    )

                batch_results.append(
                    {
                        "request_id": i,
                        "status": "success",
                        "recommendations": recommendations,
                        "algorithm_used": algorithm,
                        "total_recommendations": len(recommendations),
                    }
                )

            except Exception as req_error:
                batch_results.append(
                    {"request_id": i, "status": "error", "error": str(req_error)}
                )

        return {
            "user_id": current_user.id,
            "batch_results": batch_results,
            "total_requests": len(requests),
            "successful_requests": len(
                [r for r in batch_results if r["status"] == "success"]
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"批量AI推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量推荐服务失败: {str(e)}")


@router.get("/recommend/algorithms")
async def get_available_algorithms():
    """
    获取可用的推荐算法列表

    Returns:
        支持的算法信息
    """
    algorithms = [
        {
            "name": "hybrid",
            "description": "混合推荐算法，结合协同过滤和内容推荐",
            "default": True,
            "performance": "high",
        },
        {
            "name": "collaborative",
            "description": "基于用户行为的协同过滤推荐",
            "default": False,
            "performance": "medium",
        },
        {
            "name": "content",
            "description": "基于内容相似度的内容推荐",
            "default": False,
            "performance": "medium",
        },
        {
            "name": "adaptive",
            "description": "自适应学习路径推荐，结合行为分析和知识图谱",
            "default": False,
            "performance": "high",
        },
    ]

    return {
        "available_algorithms": algorithms,
        "default_algorithm": "hybrid",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/recommend/health")
async def health_check():
    """
    AI推荐服务健康检查

    Returns:
        服务健康状态
    """
    try:
        # 检查推荐引擎状态
        engine_status = (
            "ready"
            if hasattr(ai_recommendation_engine, "is_trained")
            else "initializing"
        )

        return {
            "status": "healthy",
            "service": "AI Recommendation Service",
            "engine_status": engine_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "AI Recommendation Service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
