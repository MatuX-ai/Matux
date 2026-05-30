"""
创意激发引擎API路由
提供创意生成、评分、图像生成等RESTful API接口
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from ai_service.business_evaluator import business_evaluator
from ai_service.creativity_engine import creativity_engine
from ai_service.idea_scorer import idea_scorer
from ai_service.prompt_templates import prompt_template_manager
from models.creativity_models import (
    BusinessEvaluationRequest,
    BusinessEvaluationResponse,
    CreativeIdeaResponse,
    CreativeIdeaUpdate,
    IdeaGenerationRequest,
    IdeaGenerationResponse,
    IdeaScoreRequest,
    IdeaScoreResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
)
from models.user import User
from routes.auth_routes import get_current_user
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/creativity", tags=["创意引擎"])

# ==================== 创意想法相关接口 ====================


@router.post("/generate-idea", response_model=IdeaGenerationResponse)
async def generate_creative_idea(
    request: IdeaGenerationRequest, current_user: User = Depends(get_current_user)
):
    """
    生成创意想法

    此接口根据提供的Prompt模板或自定义Prompt生成创意想法。
    支持多种分类和变量填充。
    """
    try:
        logger.info(f"用户 {current_user.username} 请求生成创意想法")

        # 调用创意引擎生成创意
        response = await creativity_engine.generate_creative_idea(request)

        # 保存创意到数据库
        idea_id = await _save_generated_idea(response, request, current_user.id)
        response.idea_id = idea_id

        return response

    except Exception as e:
        logger.error(f"创意生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创意生成失败: {str(e)}")


@router.get("/my-ideas", response_model=List[CreativeIdeaResponse])
async def get_my_creative_ideas(
    category: Optional[str] = Query(None, description="创意分类筛选"),
    is_public: Optional[bool] = Query(None, description="是否公开筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
):
    """
    获取我的创意想法列表
    """
    try:
        logger.info(f"用户 {current_user.username} 查询创意想法列表")

        with get_sync_db() as db:
            query = text("""
                SELECT * FROM creative_ideas
                WHERE user_id = :user_id
                AND (:category IS NULL OR category = :category)
                AND (:is_public IS NULL OR is_public = :is_public)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = db.execute(
                query,
                {
                    "user_id": current_user.id,
                    "category": category,
                    "is_public": is_public,
                    "limit": limit,
                    "offset": offset,
                },
            )

            ideas = []
            for row in result:
                ideas.append(
                    CreativeIdeaResponse(
                        id=row.id,
                        user_id=row.user_id,
                        title=row.title,
                        description=row.description,
                        category=row.category,
                        prompt_template_id=row.prompt_template_id,
                        ai_generated_content=row.ai_generated_content,
                        images=row.images,
                        scores=row.scores,
                        tags=row.tags,
                        is_public=row.is_public,
                        view_count=row.view_count,
                        like_count=row.like_count,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )

            return ideas

    except Exception as e:
        logger.error(f"获取创意想法列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取创意想法失败: {str(e)}")


@router.get("/ideas/{idea_id}", response_model=CreativeIdeaResponse)
async def get_creative_idea(
    idea_id: int, current_user: User = Depends(get_current_user)
):
    """
    获取指定创意想法详情
    """
    try:
        logger.info(f"用户 {current_user.username} 查看创意想法 {idea_id}")

        with get_sync_db() as db:
            query = text("""
                SELECT * FROM creative_ideas
                WHERE id = :idea_id
                AND (user_id = :user_id OR is_public = TRUE)
            """)

            result = db.execute(
                query, {"idea_id": idea_id, "user_id": current_user.id}
            ).first()

            if not result:
                raise HTTPException(
                    status_code=404, detail="创意想法不存在或无权限访问"
                )

            # 增加浏览次数
            update_query = text("""
                UPDATE creative_ideas
                SET view_count = view_count + 1
                WHERE id = :idea_id
            """)
            db.execute(update_query, {"idea_id": idea_id})
            db.commit()

            return CreativeIdeaResponse(
                id=result.id,
                user_id=result.user_id,
                title=result.title,
                description=result.description,
                category=result.category,
                prompt_template_id=result.prompt_template_id,
                ai_generated_content=result.ai_generated_content,
                images=result.images,
                scores=result.scores,
                tags=result.tags,
                is_public=result.is_public,
                view_count=result.view_count,
                like_count=result.like_count,
                created_at=result.created_at,
                updated_at=result.updated_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取创意想法详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取创意想法详情失败: {str(e)}")


@router.put("/ideas/{idea_id}", response_model=CreativeIdeaResponse)
async def update_creative_idea(
    idea_id: int,
    idea_update: CreativeIdeaUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    更新创意想法
    """
    try:
        logger.info(f"用户 {current_user.username} 更新创意想法 {idea_id}")

        with get_sync_db() as db:
            # 验证权限
            check_query = text("""
                SELECT user_id FROM creative_ideas WHERE id = :idea_id
            """)
            result = db.execute(check_query, {"idea_id": idea_id}).first()

            if not result or result.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限修改此创意想法")

            # 更新记录
            update_fields = []
            update_params = {"idea_id": idea_id}

            if idea_update.title is not None:
                update_fields.append("title = :title")
                update_params["title"] = idea_update.title

            if idea_update.description is not None:
                update_fields.append("description = :description")
                update_params["description"] = idea_update.description

            if idea_update.category is not None:
                update_fields.append("category = :category")
                update_params["category"] = idea_update.category

            if idea_update.tags is not None:
                update_fields.append("tags = :tags")
                update_params["tags"] = str(idea_update.tags)

            if idea_update.is_public is not None:
                update_fields.append("is_public = :is_public")
                update_params["is_public"] = idea_update.is_public

            if not update_fields:
                raise HTTPException(status_code=400, detail="没有提供更新内容")

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_sql = f"""
                UPDATE creative_ideas
                SET {', '.join(update_fields)}
                WHERE id = :idea_id
            """

            db.execute(text(update_sql), update_params)
            db.commit()

            # 返回更新后的记录
            return await get_creative_idea(idea_id, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新创意想法失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新创意想法失败: {str(e)}")


@router.delete("/ideas/{idea_id}")
async def delete_creative_idea(
    idea_id: int, current_user: User = Depends(get_current_user)
):
    """
    删除创意想法
    """
    try:
        logger.info(f"用户 {current_user.username} 删除创意想法 {idea_id}")

        with get_sync_db() as db:
            # 验证权限
            check_query = text("""
                SELECT user_id FROM creative_ideas WHERE id = :idea_id
            """)
            result = db.execute(check_query, {"idea_id": idea_id}).first()

            if not result or result.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限删除此创意想法")

            # 删除记录
            delete_query = text("DELETE FROM creative_ideas WHERE id = :idea_id")
            db.execute(delete_query, {"idea_id": idea_id})
            db.commit()

            return {"message": "创意想法删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除创意想法失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除创意想法失败: {str(e)}")


# ==================== Prompt模板相关接口 ====================


@router.get("/templates", response_model=List[PromptTemplateResponse])
async def list_prompt_templates(
    category: Optional[str] = Query(None, description="模板分类筛选"),
    is_public: bool = Query(True, description="是否只显示公开模板"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取Prompt模板列表
    """
    try:
        logger.info("获取Prompt模板列表")
        return await prompt_template_manager.list_templates(
            category=category, is_public=is_public, limit=limit, offset=offset
        )

    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(template_id: int):
    """
    获取指定Prompt模板详情
    """
    try:
        logger.info(f"获取Prompt模板 {template_id}")
        template = await prompt_template_manager.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.post("/templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template_data: PromptTemplateCreate, current_user: User = Depends(get_current_user)
):
    """
    创建新的Prompt模板
    """
    try:
        logger.info(f"用户 {current_user.username} 创建Prompt模板")
        return await prompt_template_manager.create_template(
            template_data, current_user.id
        )

    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.get("/templates/search/{query}", response_model=List[PromptTemplateResponse])
async def search_prompt_templates(query: str, limit: int = Query(20, ge=1, le=50)):
    """
    搜索Prompt模板
    """
    try:
        logger.info(f"搜索Prompt模板: {query}")
        return await prompt_template_manager.search_templates(query, limit)

    except Exception as e:
        logger.error(f"搜索模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索模板失败: {str(e)}")


@router.get("/templates/popular", response_model=List[PromptTemplateResponse])
async def get_popular_templates(limit: int = Query(10, ge=1, le=30)):
    """
    获取热门模板
    """
    try:
        logger.info("获取热门模板")
        return await prompt_template_manager.get_popular_templates(limit)

    except Exception as e:
        logger.error(f"获取热门模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热门模板失败: {str(e)}")


# ==================== 创意评分相关接口 ====================


@router.post("/score-idea", response_model=IdeaScoreResponse)
async def score_creative_idea(
    request: IdeaScoreRequest, current_user: User = Depends(get_current_user)
):
    """
    对创意想法进行多维度评分

    评分维度包括：
    - 创新性 (40%)
    - 可行性 (30%)
    - 商业价值 (30%)
    """
    try:
        logger.info(f"用户 {current_user.username} 请求创意评分")
        return await idea_scorer.score_idea(request)

    except Exception as e:
        logger.error(f"创意评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创意评分失败: {str(e)}")


# ==================== 图像生成相关接口 ====================


@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_creative_image(
    request: ImageGenerationRequest, current_user: User = Depends(get_current_user)
):
    """
    生成创意图像

    使用DALL-E 3 API根据Prompt生成高质量图像。
    支持多种风格和尺寸选项。
    """
    try:
        logger.info(f"用户 {current_user.username} 请求生成创意图像")
        return await dalle_generator.generate_images(request)

    except Exception as e:
        logger.error(f"图像生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


# ==================== 商业价值评估接口 ====================


@router.post("/evaluate-business", response_model=BusinessEvaluationResponse)
async def evaluate_business_value(
    request: BusinessEvaluationRequest, current_user: User = Depends(get_current_user)
):
    """
    评估创意的商业价值

    提供成本效益分析、市场潜力评估、风险分析和投资建议。
    """
    try:
        logger.info(f"用户 {current_user.username} 请求商业价值评估")
        return await business_evaluator.evaluate_business_value(request)

    except Exception as e:
        logger.error(f"商业价值评估失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"商业价值评估失败: {str(e)}")


# ==================== 统计和趋势接口 ====================


@router.get("/statistics")
async def get_creativity_statistics(current_user: User = Depends(get_current_user)):
    """
    获取创意相关统计信息
    """
    try:
        logger.info(f"用户 {current_user.username} 获取创意统计")

        with get_sync_db() as db:
            # 用户创意统计
            user_ideas_query = text("""
                SELECT
                    COUNT(*) as total_ideas,
                    COUNT(CASE WHEN is_public = TRUE THEN 1 END) as public_ideas,
                    AVG(CAST(scores->>'total_score' AS FLOAT)) as avg_score
                FROM creative_ideas
                WHERE user_id = :user_id
            """)

            user_stats = db.execute(
                user_ideas_query, {"user_id": current_user.id}
            ).first()

            # 模板使用统计
            template_stats = await prompt_template_manager.get_template_statistics()

            return {
                "user_statistics": {
                    "total_ideas": user_stats.total_ideas or 0,
                    "public_ideas": user_stats.public_ideas or 0,
                    "average_score": round(user_stats.avg_score or 0, 2),
                },
                "template_statistics": template_stats,
            }

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ==================== 辅助函数 ====================


async def _save_generated_idea(
    response: IdeaGenerationResponse, request: IdeaGenerationRequest, user_id: int
) -> int:
    """保存生成的创意到数据库"""
    try:
        with get_sync_db() as db:
            insert_query = text("""
                INSERT INTO creative_ideas
                (user_id, title, description, category, prompt_template_id, ai_generated_content, created_at, updated_at)
                VALUES (:user_id, :title, :description, :category, :template_id, :content, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """)

            result = db.execute(
                insert_query,
                {
                    "user_id": user_id,
                    "title": response.title,
                    "description": getattr(request, "description", ""),
                    "category": response.category,
                    "template_id": getattr(request, "prompt_template_id", None),
                    "content": response.content,
                },
            )

            idea_id = result.first()[0]
            db.commit()

            return idea_id

    except Exception as e:
        logger.error(f"保存创意失败: {str(e)}")
        return 0  # 返回0表示保存失败但不影响主流程
