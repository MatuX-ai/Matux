import asyncio
from datetime import datetime
import json
import logging
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from ..ai_service.completion_memory import completion_memory
from ..database.tenant_aware_session import get_db_session
from ..middleware.permission_middleware import get_current_user
from ..models.ai_completion import (
    CompletionConfig,
    CompletionRequest,
    CompletionResponse,
    ContextAnalysisResult,
    ProgrammingLanguage,
    UserHistoryRecord,
)
from ..models.user import User
from ..services.code_completion_service import code_completion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/completion", tags=["代码补全"])

# WebSocket连接管理
active_connections = {}


@router.post("/suggest", response_model=CompletionResponse, summary="获取代码补全建议")
async def get_code_completion(
    request: CompletionRequest, current_user: User = Depends(get_current_user)
):
    """
    根据代码前缀和上下文获取智能补全建议

    Args:
        request: 补全请求对象
        current_user: 当前认证用户

    Returns:
        代码补全响应
    """
    try:
        # 设置用户ID
        request.user_id = current_user.id

        # 调用补全服务
        response = await code_completion_service.get_completions(request)

        # 记录用户历史（异步）
        if request.prefix and len(request.prefix) > 3:
            history_record = UserHistoryRecord(
                user_id=current_user.id,
                code_snippet=request.prefix,
                context="\n".join(request.context[-5:]) if request.context else "",
                language=request.language or ProgrammingLanguage.PYTHON,
            )
            asyncio.create_task(completion_memory.add_user_history(history_record))

        return response

    except Exception as e:
        logger.error(f"代码补全API错误: {e}")
        raise HTTPException(status_code=500, detail=f"补全服务暂时不可用: {str(e)}")


@router.post(
    "/analyze-context", response_model=ContextAnalysisResult, summary="分析代码上下文"
)
async def analyze_code_context(
    code_lines: List[str] = Query(..., description="代码行列表"),
    cursor_position: int = Query(0, description="光标位置"),
    language: ProgrammingLanguage = Query(
        ProgrammingLanguage.PYTHON, description="编程语言"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    分析代码上下文以提供更精准的补全建议

    Args:
        code_lines: 代码行列表
        cursor_position: 光标位置
        language: 编程语言
        current_user: 当前认证用户

    Returns:
        上下文分析结果
    """
    try:
        analysis_result = await completion_memory.analyze_context_patterns(
            code_lines, language
        )
        return analysis_result

    except Exception as e:
        logger.error(f"上下文分析错误: {e}")
        raise HTTPException(status_code=500, detail=f"上下文分析失败: {str(e)}")


@router.get("/user-patterns", summary="获取用户代码模式")
async def get_user_patterns(
    language: ProgrammingLanguage = Query(ProgrammingLanguage.PYTHON),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户的代码使用模式和偏好

    Args:
        language: 编程语言
        limit: 返回记录数限制
        current_user: 当前认证用户

    Returns:
        用户代码模式列表
    """
    try:
        patterns = await completion_memory.get_user_patterns(
            current_user.id, language, limit
        )
        return {"patterns": patterns}

    except Exception as e:
        logger.error(f"获取用户模式错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户模式失败: {str(e)}")


@router.get("/config", response_model=CompletionConfig, summary="获取补全服务配置")
async def get_completion_config(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的补全服务配置

    Args:
        current_user: 当前认证用户

    Returns:
        补全服务配置
    """
    try:
        # 这里可以从用户设置或系统配置中获取
        from ..config.settings import get_settings

        settings = get_settings()

        config = CompletionConfig(
            enable_caching=settings.COMPLETION_ENABLE_CACHING,
            cache_ttl_hours=settings.COMPLETION_CACHE_TTL_HOURS,
            max_context_lines=settings.COMPLETION_MAX_CONTEXT_LINES,
            min_prefix_length=settings.COMPLETION_MIN_PREFIX_LENGTH,
            enable_syntax_analysis=settings.COMPLETION_ENABLE_SYNTAX_ANALYSIS,
            default_provider=settings.COMPLETION_DEFAULT_PROVIDER,
        )

        return config

    except Exception as e:
        logger.error(f"获取配置错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/cache/cleanup", summary="清理过期缓存")
async def cleanup_expired_cache(current_user: User = Depends(get_current_user)):
    """
    手动清理过期的补全缓存

    Args:
        current_user: 当前认证用户（需要管理员权限）

    Returns:
        清理结果
    """
    try:
        # 检查管理员权限
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        deleted_count = await completion_memory.cleanup_expired_cache()

        return {
            "message": f"成功清理 {deleted_count} 个过期缓存条目",
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"清理缓存错误: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket连接端点，用于实时代码补全

    支持的消息类型:
    - completion_request: 请求补全建议
    - context_update: 更新上下文信息
    - disconnect: 客户端断开连接
    """
    await websocket.accept()

    client_id = f"{websocket.client.host}:{websocket.client.port}"
    active_connections[client_id] = websocket

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "completion_request":
                await handle_completion_request(websocket, message)
            elif message_type == "context_update":
                await handle_context_update(websocket, message)
            elif message_type == "disconnect":
                break
            else:
                await websocket.send_text(
                    json.dumps(
                        {"type": "error", "message": f"未知消息类型: {message_type}"}
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
        await websocket.send_text(
            json.dumps({"type": "error", "message": f"服务器错误: {str(e)}"})
        )
    finally:
        if client_id in active_connections:
            del active_connections[client_id]


async def handle_completion_request(websocket: WebSocket, message: dict):
    """处理补全请求"""
    try:
        # 解析请求数据
        request_data = message.get("data", {})

        # 构建CompletionRequest对象
        request = CompletionRequest(
            prefix=request_data.get("prefix", ""),
            context=request_data.get("context", []),
            language=ProgrammingLanguage(request_data.get("language", "python")),
            provider=request_data.get("provider"),
            max_suggestions=request_data.get("max_suggestions", 5),
            temperature=request_data.get("temperature", 0.7),
        )

        # 调用补全服务
        response = await code_completion_service.get_completions(request)

        # 发送响应
        await websocket.send_text(
            json.dumps({"type": "completion_response", "data": response.dict()})
        )

    except Exception as e:
        logger.error(f"处理补全请求错误: {e}")
        await websocket.send_text(
            json.dumps({"type": "error", "message": f"处理补全请求失败: {str(e)}"})
        )


async def handle_context_update(websocket: WebSocket, message: dict):
    """处理上下文更新"""
    try:
        context_data = message.get("data", {})
        code_lines = context_data.get("code_lines", [])
        language = ProgrammingLanguage(context_data.get("language", "python"))

        # 分析上下文
        analysis_result = await completion_memory.analyze_context_patterns(
            code_lines, language
        )

        # 发送分析结果
        await websocket.send_text(
            json.dumps({"type": "context_analysis", "data": analysis_result.dict()})
        )

    except Exception as e:
        logger.error(f"处理上下文更新错误: {e}")
        await websocket.send_text(
            json.dumps({"type": "error", "message": f"上下文分析失败: {str(e)}"})
        )


@router.get("/health", summary="健康检查")
async def health_check():
    """
    检查补全服务的健康状态

    Returns:
        服务状态信息
    """
    try:
        # 检查各组件状态
        status = {
            "service": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "ai_manager": "unknown",
                "memory_system": "unknown",
                "database": "unknown",
            },
        }

        # 检查AI管理器
        try:
            # 简单的连通性检查
            status["components"]["ai_manager"] = "healthy"
        except Exception:
            status["components"]["ai_manager"] = "unhealthy"

        # 检查记忆系统
        try:
            await completion_memory.get_user_patterns(1, ProgrammingLanguage.PYTHON, 1)
            status["components"]["memory_system"] = "healthy"
        except Exception:
            status["components"]["memory_system"] = "unhealthy"

        # 检查数据库连接
        try:
            async with get_db_session() as db:
                await db.execute("SELECT 1")
                status["components"]["database"] = "healthy"
        except Exception:
            status["components"]["database"] = "unhealthy"

        # 整体状态判断
        if all(comp == "healthy" for comp in status["components"].values()):
            status["overall"] = "healthy"
        else:
            status["overall"] = "degraded"
            status["service"] = "degraded"

        return status

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
