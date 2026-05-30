"""
创意引擎业务逻辑服务层
封装创意生成、评分、图像生成等核心业务逻辑
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from ai_service.business_evaluator import business_evaluator
from ai_service.creativity_engine import creativity_engine
from ai_service.idea_scorer import idea_scorer
from ai_service.image_generator import dalle_generator
from ai_service.prompt_templates import prompt_template_manager
from models.creativity_models import (
    BusinessEvaluationRequest,
    CreativeIdeaCreate,
    IdeaGenerationRequest,
    IdeaScoreRequest,
    ImageGenerationRequest,
)
from utils.database import get_sync_db

logger = logging.getLogger(__name__)


class CreativityService:
    """创意引擎业务服务类"""

    def __init__(self):
        self.creativity_engine = creativity_engine
        self.prompt_manager = prompt_template_manager
        self.idea_scorer = idea_scorer
        self.image_generator = dalle_generator
        self.business_evaluator = business_evaluator

    async def create_creative_idea(
        self, idea_data: CreativeIdeaCreate, user_id: int
    ) -> Dict[str, Any]:
        """
        创建创意想法

        Args:
            idea_data: 创意想法创建数据
            user_id: 用户ID

        Returns:
            Dict: 创建结果
        """
        try:
            logger.info(f"用户 {user_id} 创建创意想法: {idea_data.title}")

            with get_sync_db() as db:
                # 插入创意想法记录
                insert_query = text("""
                    INSERT INTO creative_ideas 
                    (user_id, title, description, category, tags, is_public, created_at, updated_at)
                    VALUES (:user_id, :title, :description, :category, :tags, :is_public, :created_at, :updated_at)
                    RETURNING id
                """)

                result = db.execute(
                    insert_query,
                    {
                        "user_id": user_id,
                        "title": idea_data.title,
                        "description": idea_data.description,
                        "category": idea_data.category,
                        "tags": str(idea_data.tags) if idea_data.tags else None,
                        "is_public": idea_data.is_public,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )

                idea_id = result.first()[0]
                db.commit()

                logger.info(f"创意想法创建成功，ID: {idea_id}")

                return {
                    "success": True,
                    "idea_id": idea_id,
                    "message": "创意想法创建成功",
                }

        except Exception as e:
            logger.error(f"创建创意想法失败: {str(e)}")
            return {"success": False, "error": str(e), "message": "创意想法创建失败"}

    async def generate_and_save_idea(
        self, request: IdeaGenerationRequest, user_id: int
    ) -> Dict[str, Any]:
        """
        生成并保存创意想法

        Args:
            request: 创意生成请求
            user_id: 用户ID

        Returns:
            Dict: 生成和保存结果
        """
        try:
            logger.info(f"用户 {user_id} 请求生成并保存创意想法")

            # 1. 生成创意
            generation_response = await self.creativity_engine.generate_creative_idea(
                request
            )

            # 2. 保存到数据库
            with get_sync_db() as db:
                insert_query = text("""
                    INSERT INTO creative_ideas 
                    (user_id, title, description, category, prompt_template_id, ai_generated_content, is_public, created_at, updated_at)
                    VALUES (:user_id, :title, :description, :category, :template_id, :content, FALSE, :created_at, :updated_at)
                    RETURNING id
                """)

                result = db.execute(
                    insert_query,
                    {
                        "user_id": user_id,
                        "title": generation_response.title,
                        "description": getattr(request, "description", ""),
                        "category": generation_response.category,
                        "template_id": getattr(request, "prompt_template_id", None),
                        "content": generation_response.content,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )

                idea_id = result.first()[0]
                db.commit()

                # 如果使用了模板，增加模板使用次数
                if request.prompt_template_id:
                    await self.prompt_manager.increment_usage_count(
                        request.prompt_template_id
                    )

                logger.info(f"创意想法生成并保存成功，ID: {idea_id}")

                return {
                    "success": True,
                    "idea_id": idea_id,
                    "title": generation_response.title,
                    "content": generation_response.content,
                    "category": generation_response.category,
                    "processing_time": generation_response.processing_time,
                    "tokens_used": generation_response.tokens_used,
                    "message": "创意想法生成并保存成功",
                }

        except Exception as e:
            logger.error(f"生成并保存创意想法失败: {str(e)}")
            return {"success": False, "error": str(e), "message": "创意想法生成失败"}

    async def batch_score_ideas(
        self,
        idea_contents: List[str],
        scoring_criteria: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        批量评分创意想法

        Args:
            idea_contents: 创意内容列表
            scoring_criteria: 评分标准

        Returns:
            List[Dict]: 批量评分结果
        """
        try:
            logger.info(f"开始批量评分 {len(idea_contents)} 个创意想法")

            # 并发执行评分任务
            scoring_tasks = [
                self.score_single_idea(content, scoring_criteria)
                for content in idea_contents
            ]

            results = await asyncio.gather(*scoring_tasks, return_exceptions=True)

            # 处理结果
            batch_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    batch_results.append(
                        {
                            "index": i,
                            "success": False,
                            "error": str(result),
                            "content": (
                                idea_contents[i][:50] + "..."
                                if len(idea_contents[i]) > 50
                                else idea_contents[i]
                            ),
                        }
                    )
                else:
                    batch_results.append(
                        {
                            "index": i,
                            "success": True,
                            "content": (
                                idea_contents[i][:50] + "..."
                                if len(idea_contents[i]) > 50
                                else idea_contents[i]
                            ),
                            **result,
                        }
                    )

            logger.info(
                f"批量评分完成，成功: {sum(1 for r in batch_results if r['success'])}/{len(batch_results)}"
            )
            return batch_results

        except Exception as e:
            logger.error(f"批量评分失败: {str(e)}")
            raise

    async def score_single_idea(
        self, idea_content: str, scoring_criteria: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        评分单个创意想法

        Args:
            idea_content: 创意内容
            scoring_criteria: 评分标准

        Returns:
            Dict: 评分结果
        """
        try:
            score_request = IdeaScoreRequest(
                idea_content=idea_content, scoring_criteria=scoring_criteria
            )

            score_response = await self.idea_scorer.score_idea(score_request)

            return {
                "total_score": score_response.total_score,
                "creativity": score_response.creativity,
                "feasibility": score_response.feasibility,
                "commercial_value": score_response.commercial_value,
                "recommendations": score_response.recommendations,
            }

        except Exception as e:
            logger.error(f"单个创意评分失败: {str(e)}")
            raise

    async def generate_idea_with_images(
        self,
        idea_request: IdeaGenerationRequest,
        image_request: ImageGenerationRequest,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        生成创意想法并配套图像

        Args:
            idea_request: 创意生成请求
            image_request: 图像生成请求
            user_id: 用户ID

        Returns:
            Dict: 创意和图像生成结果
        """
        try:
            logger.info(f"用户 {user_id} 请求生成创意想法及配套图像")

            # 并发执行创意生成和图像生成
            idea_task = self.generate_and_save_idea(idea_request, user_id)
            image_task = self.image_generator.generate_images(image_request)

            idea_result, image_result = await asyncio.gather(idea_task, image_task)

            if not idea_result["success"]:
                return {
                    "success": False,
                    "error": "创意生成失败",
                    "details": idea_result,
                }

            # 更新创意记录，添加图像信息
            if idea_result["success"] and image_result.images:
                with get_sync_db() as db:
                    update_query = text("""
                        UPDATE creative_ideas 
                        SET images = :images, updated_at = :updated_at
                        WHERE id = :idea_id
                    """)

                    db.execute(
                        update_query,
                        {
                            "images": str(image_result.images),
                            "updated_at": datetime.utcnow(),
                            "idea_id": idea_result["idea_id"],
                        },
                    )
                    db.commit()

            return {
                "success": True,
                "idea": idea_result,
                "images": image_result.images,
                "total_processing_time": idea_result.get("processing_time", 0)
                + image_result.processing_time,
                "total_cost": image_result.total_cost,
                "message": "创意想法和图像生成成功",
            }

        except Exception as e:
            logger.error(f"创意想法和图像生成失败: {str(e)}")
            return {"success": False, "error": str(e), "message": "生成失败"}

    async def comprehensive_idea_analysis(
        self, idea_content: str, business_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        综合创意分析（评分+商业评估）

        Args:
            idea_content: 创意内容
            business_context: 商业背景信息

        Returns:
            Dict: 综合分析结果
        """
        try:
            logger.info("开始综合创意分析")

            # 并发执行评分和商业评估
            scoring_task = self.score_single_idea(idea_content)

            if business_context:
                business_request = BusinessEvaluationRequest(
                    idea_description=idea_content,
                    target_market=business_context.get("target_market", ""),
                    estimated_costs=business_context.get("estimated_costs", {}),
                    revenue_projections=business_context.get("revenue_projections", {}),
                    competition_analysis=business_context.get(
                        "competition_analysis", ""
                    ),
                )
                business_task = self.business_evaluator.evaluate_business_value(
                    business_request
                )
                scoring_result, business_result = await asyncio.gather(
                    scoring_task, business_task
                )
            else:
                scoring_result = await scoring_task
                business_result = None

            analysis_result = {
                "scoring": scoring_result,
                "business_evaluation": (
                    business_result.dict() if business_result else None
                ),
                "overall_assessment": self._generate_overall_assessment(
                    scoring_result, business_result
                ),
            }

            logger.info("综合创意分析完成")
            return analysis_result

        except Exception as e:
            logger.error(f"综合创意分析失败: {str(e)}")
            raise

    def _generate_overall_assessment(
        self, scoring_result: Dict[str, Any], business_result: Optional[Any]
    ) -> Dict[str, Any]:
        """生成总体评估"""
        assessment = {
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "investment_outlook": "待评估",
        }

        # 基于评分结果的评估
        if scoring_result["total_score"] >= 8.0:
            assessment["strengths"].append("整体评分优秀，具有较高的创新价值")
            assessment["investment_outlook"] = "积极推荐"
        elif scoring_result["total_score"] >= 6.0:
            assessment["strengths"].append("评分良好，具备一定创新性")
            assessment["investment_outlook"] = "建议关注"
        else:
            assessment["weaknesses"].append("整体评分偏低，需要进一步优化")
            assessment["investment_outlook"] = "谨慎考虑"

        # 添加具体维度建议
        if scoring_result["creativity"] < 6.0:
            assessment["recommendations"].append("提升创新性和独特性")
        if scoring_result["feasibility"] < 6.0:
            assessment["recommendations"].append("改善技术可行性和实施路径")
        if scoring_result["commercial_value"] < 6.0:
            assessment["recommendations"].append("完善商业模式和市场定位")

        return assessment

    async def get_user_creativity_dashboard(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户创意仪表板数据

        Args:
            user_id: 用户ID

        Returns:
            Dict: 仪表板数据
        """
        try:
            logger.info(f"获取用户 {user_id} 的创意仪表板数据")

            with get_sync_db() as db:
                # 统计用户创意数据
                stats_query = text("""
                    SELECT 
                        COUNT(*) as total_ideas,
                        COUNT(CASE WHEN is_public = TRUE THEN 1 END) as public_ideas,
                        COUNT(CASE WHEN category = 'technology' THEN 1 END) as tech_ideas,
                        COUNT(CASE WHEN category = 'business' THEN 1 END) as business_ideas,
                        AVG(CAST(scores->>'total_score' AS FLOAT)) as avg_score,
                        SUM(view_count) as total_views,
                        SUM(like_count) as total_likes
                    FROM creative_ideas 
                    WHERE user_id = :user_id
                """)

                stats_result = db.execute(stats_query, {"user_id": user_id}).first()

                # 获取最近的创意想法
                recent_ideas_query = text("""
                    SELECT id, title, category, created_at, view_count, like_count
                    FROM creative_ideas 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 5
                """)

                recent_ideas = db.execute(
                    recent_ideas_query, {"user_id": user_id}
                ).fetchall()

                # 获取热门模板使用情况
                template_usage_query = text("""
                    SELECT pt.name, pt.category, COUNT(ci.id) as usage_count
                    FROM prompt_templates pt
                    LEFT JOIN creative_ideas ci ON pt.id = ci.prompt_template_id 
                    WHERE ci.user_id = :user_id
                    GROUP BY pt.id, pt.name, pt.category
                    ORDER BY usage_count DESC
                    LIMIT 5
                """)

                template_usage = db.execute(
                    template_usage_query, {"user_id": user_id}
                ).fetchall()

                dashboard_data = {
                    "statistics": {
                        "total_ideas": stats_result.total_ideas or 0,
                        "public_ideas": stats_result.public_ideas or 0,
                        "tech_ideas": stats_result.tech_ideas or 0,
                        "business_ideas": stats_result.business_ideas or 0,
                        "average_score": round(stats_result.avg_score or 0, 2),
                        "total_views": stats_result.total_views or 0,
                        "total_likes": stats_result.total_likes or 0,
                    },
                    "recent_ideas": [
                        {
                            "id": idea.id,
                            "title": idea.title,
                            "category": idea.category,
                            "created_at": (
                                idea.created_at.isoformat() if idea.created_at else None
                            ),
                            "view_count": idea.view_count,
                            "like_count": idea.like_count,
                        }
                        for idea in recent_ideas
                    ],
                    "template_usage": [
                        {
                            "template_name": usage.name,
                            "category": usage.category,
                            "usage_count": usage.usage_count,
                        }
                        for usage in template_usage
                    ],
                }

                logger.info(f"用户 {user_id} 仪表板数据获取成功")
                return dashboard_data

        except Exception as e:
            logger.error(f"获取用户仪表板数据失败: {str(e)}")
            raise


# 创建全局实例
creativity_service = CreativityService()
