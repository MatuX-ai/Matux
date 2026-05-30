"""
AI服务路由
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service import (
    AvailableModelsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    ModelInfo,
    ModelProvider,
    ProgrammingLanguage,
    ai_manager,
)
from models.ai_request import AIRequest
from models.user import User
from utils.database import get_db

# 延迟导入get_current_user避免循环依赖

router = APIRouter()


@router.post("/generate-code", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest, db: AsyncSession = Depends(get_db)
):
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    生成代码
    
    此端点支持多种AI模型提供商：
    - OpenAI (GPT-4系列)
    - Lingma (代码专用模型)
    - DeepSeek (代码专用模型)
    - Anthropic (Claude系列)
    - Google (Gemini系列)
    """
    start_time = time.time()

    try:
        # 调用AI管理器生成代码
        response = await ai_manager.generate_code(request)

        # 记录请求到数据库
        ai_request = AIRequest(
            user_id=current_user.id,
            prompt=request.prompt,
            response=response.code,
            model_provider=request.provider.value,
            model_name=response.model,
            tokens_used=response.tokens_used,
            processing_time=response.processing_time,
            success=True,
        )

        db.add(ai_request)
        await db.commit()

        return response

    except Exception as e:
        # 记录失败的请求
        processing_time = time.time() - start_time
        ai_request = AIRequest(
            user_id=current_user.id,
            prompt=request.prompt,
            response=None,
            model_provider=request.provider.value,
            model_name=request.model or "",
            tokens_used=0,
            processing_time=processing_time,
            success=False,
            error_message=str(e),
        )

        db.add(ai_request)
        await db.commit()

        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models():
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    获取可用的AI模型列表
    """
    models = [
        ModelInfo(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4-turbo",
            description="OpenAI最新的GPT-4 Turbo模型，适合复杂代码生成",
            max_tokens=4096,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.TYPESCRIPT,
                ProgrammingLanguage.JAVA,
                ProgrammingLanguage.CSHARP,
                ProgrammingLanguage.GO,
                ProgrammingLanguage.RUST,
                ProgrammingLanguage.CPP,
            ],
        ),
        ModelInfo(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            description="标准GPT-4模型",
            max_tokens=8192,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.TYPESCRIPT,
                ProgrammingLanguage.JAVA,
                ProgrammingLanguage.CSHARP,
                ProgrammingLanguage.GO,
            ],
        ),
        ModelInfo(
            provider=ModelProvider.LINGMA,
            model_name="lingma-code-pro",
            description="Lingma专业代码生成模型",
            max_tokens=4096,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.TYPESCRIPT,
                ProgrammingLanguage.GO,
            ],
        ),
        ModelInfo(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-coder",
            description="DeepSeek代码专用模型",
            max_tokens=4096,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.GO,
                ProgrammingLanguage.CPP,
            ],
        ),
        ModelInfo(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus-20240229",
            description="Anthropic Claude 3 Opus，最强大的模型",
            max_tokens=4096,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.TYPESCRIPT,
                ProgrammingLanguage.JAVA,
                ProgrammingLanguage.CSHARP,
            ],
        ),
        ModelInfo(
            provider=ModelProvider.GOOGLE,
            model_name="gemini-pro",
            description="Google Gemini Pro模型",
            max_tokens=2048,
            supported_languages=[
                ProgrammingLanguage.PYTHON,
                ProgrammingLanguage.JAVASCRIPT,
                ProgrammingLanguage.JAVA,
                ProgrammingLanguage.GO,
            ],
        ),
    ]

    return AvailableModelsResponse(models=models)


@router.get("/usage-stats")
async def get_usage_stats(db: AsyncSession = Depends(get_db)):
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    获取用户的AI使用统计
    """
    # 查询用户的所有AI请求记录
    from sqlalchemy import func, select

    # 统计总请求数
    stmt = select(func.count(AIRequest.id)).where(AIRequest.user_id == current_user.id)
    result = await db.execute(stmt)
    total_requests = result.scalar()

    # 统计成功请求数
    stmt = select(func.count(AIRequest.id)).where(
        AIRequest.user_id == current_user.id, AIRequest.success == True
    )
    result = await db.execute(stmt)
    successful_requests = result.scalar()

    # 按提供商统计
    stmt = (
        select(
            AIRequest.model_provider,
            func.count(AIRequest.id).label("count"),
            func.avg(AIRequest.processing_time).label("avg_time"),
        )
        .where(AIRequest.user_id == current_user.id)
        .group_by(AIRequest.model_provider)
    )

    result = await db.execute(stmt)
    provider_stats = result.fetchall()

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "success_rate": (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0
        ),
        "provider_stats": [
            {
                "provider": stat.model_provider,
                "request_count": stat.count,
                "average_processing_time": (
                    round(stat.avg_time, 2) if stat.avg_time else 0
                ),
            }
            for stat in provider_stats
        ],
    }


@router.get("/recent-requests")
async def get_recent_requests(limit: int = 10, db: AsyncSession = Depends(get_db)):
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    获取用户最近的AI请求记录
    """
    from sqlalchemy import select

    stmt = (
        select(AIRequest)
        .where(AIRequest.user_id == current_user.id)
        .order_by(AIRequest.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    requests = result.scalars().all()

    return [
        {
            "id": req.id,
            "prompt": req.prompt[:100] + "..." if len(req.prompt) > 100 else req.prompt,
            "model_provider": req.model_provider,
            "model_name": req.model_name,
            "tokens_used": req.tokens_used,
            "processing_time": round(req.processing_time, 2),
            "success": req.success,
            "created_at": req.created_at.isoformat(),
        }
        for req in requests
    ]
