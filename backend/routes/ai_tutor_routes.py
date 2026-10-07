"""
AI 导师路由 - DeepSeek 深度集成

提供代码解释、代码优化、智能辅导等功能
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel, Field

from ..ai_service.ai_manager import AIManager
from ..ai_service.hermes_agent_service import get_hermes_service
from ..ai_service.hermes_mcp_tools import get_ai_tutor_tools
from ..middleware.permission_middleware import get_current_user
from ..models.ai_completion import (
    CodeComplexity,
    CodeElement,
    CodeGenerationRequest,
    DeepSeekExplainRequest,
    DeepSeekExplainResponse,
    DeepSeekOptimizeRequest,
    DeepSeekOptimizeResponse,
    DeepSeekTutorRequest,
    DeepSeekTutorResponse,
    ModelProvider,
    OptimizationImprovement,
    CodeExample,
    ProgrammingLanguage,
)
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-tutor", tags=["AI编程导师"])

# AI管理器单例
ai_manager = AIManager()


def _get_model_name(provider: Optional[ModelProvider], model: Optional[str]) -> str:
    """获取模型名称"""
    if model:
        return model
    if provider == ModelProvider.DEEPSEEK:
        return "deepseek-chat"
    elif provider == ModelProvider.OPENAI:
        return "gpt-4-turbo"
    elif provider == ModelProvider.LINGMA:
        return "lingma-code-pro"
    return "deepseek-chat"


def _parse_ai_response(result: dict, fallback: dict) -> dict:
    """解析AI响应，提取JSON"""
    try:
        import json
        response_text = result.get("text", "{}")
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        return json.loads(response_text.strip())
    except Exception:
        return fallback


@router.post("/explain", response_model=DeepSeekExplainResponse, summary="代码解释")
async def explain_code(
    request: DeepSeekExplainRequest,
    current_user: User = Depends(get_current_user),
):
    """
    使用 DeepSeek 解释代码

    提供：
    - 代码的详细解释
    - 代码元素分析（函数、类、变量等）
    - 代码复杂度评估
    - 改进建议
    - 相关概念
    """
    start_time = time.time()

    try:
        # 构建提示词
        detail_instruction = {
            "brief": "简要解释这段代码的功能",
            "normal": "详细解释这段代码的功能和工作原理",
            "detailed": "非常详细地解释这段代码，包括每个部分的原理和实现细节",
        }

        prompt = f"""请解释以下{request.language or 'Python'}代码：

```{request.language or 'python'}
{request.code}
```

要求：{detail_instruction.get(request.detail_level, detail_instruction['normal'])}

请用JSON格式返回，格式如下：
{{
    "explanation": "代码解释",
    "code_elements": [
        {{"name": "元素名", "type": "function/class/variable/import/keyword", "description": "描述", "line_start": 行号, "line_end": 行号}}
    ],
    "complexity": {{"score": 0-100, "level": "low/medium/high", "factors": ["因素"]}},
    "suggestions": ["改进建议"],
    "related_concepts": ["相关概念"]
}}
"""

        # 调用AI服务
        model_name = _get_model_name(request.provider, request.model)
        provider = request.provider or ModelProvider.DEEPSEEK

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=provider,
            model=model_name,
            temperature=0.7,
            max_tokens=2000,
        )

        try:
            result = await ai_manager.generate_code(ai_request)
            ai_result = _parse_ai_response(
                {"text": result.code},
                {
                    "explanation": "无法解析代码",
                    "code_elements": [],
                    "complexity": {"score": 50, "level": "medium", "factors": []},
                    "suggestions": [],
                    "related_concepts": [],
                }
            )
        except Exception as e:
            logger.error(f"代码解释AI调用失败: {e}", exc_info=True)
            ai_result = {
                "explanation": "服务暂时不可用，请稍后重试",
                "code_elements": [],
                "complexity": {"score": 50, "level": "medium", "factors": []},
                "suggestions": [],
                "related_concepts": [],
            }

        return DeepSeekExplainResponse(
            explanation=ai_result.get("explanation", ""),
            code_elements=[
                CodeElement(**elem) for elem in ai_result.get("code_elements", [])
            ],
            complexity=CodeComplexity(**ai_result.get("complexity", {
                "score": 50,
                "level": "medium",
                "factors": []
            })),
            suggestions=ai_result.get("suggestions", []),
            related_concepts=ai_result.get("related_concepts", []),
            model_used=model_name,
            processing_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"代码解释错误: {e}")
        raise HTTPException(status_code=500, detail=f"代码解释失败: {str(e)}")


@router.post("/optimize", response_model=DeepSeekOptimizeResponse, summary="代码优化")
async def optimize_code(
    request: DeepSeekOptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    使用 DeepSeek 优化代码

    提供：
    - 优化后的代码
    - 具体的改进项
    - 改进说明和警告
    """
    start_time = time.time()

    try:
        # 构建优化目标
        goals = request.optimization_goals or ["performance", "readability", "best-practice"]
        goals_text = "、".join({
            "performance": "性能",
            "readability": "可读性",
            "security": "安全性",
            "best-practice": "最佳实践",
        }.get(g, g) for g in goals)

        prompt = f"""请优化以下{request.language or 'Python'}代码：

```{request.language or 'python'}
{request.code}
```

优化目标：{goals_text}

请用JSON格式返回，格式如下：
{{
    "optimized_code": "优化后的完整代码",
    "improvements": [
        {{
            "type": "performance/readability/security/best-practice",
            "description": "改进描述",
            "original_snippet": "原始代码片段",
            "optimized_snippet": "优化后代码片段",
            "impact": "high/medium/low"
        }}
    ],
    "explanation": "优化说明",
    "warnings": ["警告信息"]
}}
"""

        # 调用AI服务
        model_name = _get_model_name(request.provider, request.model)
        provider = request.provider or ModelProvider.DEEPSEEK

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=provider,
            model=model_name,
            temperature=0.5,
            max_tokens=3000,
        )

        try:
            result = await ai_manager.generate_code(ai_request)
            ai_result = _parse_ai_response(
                {"text": result.code},
                {
                    "optimized_code": request.code,
                    "improvements": [],
                    "explanation": "优化服务暂时不可用",
                    "warnings": [],
                }
            )
        except Exception as e:
            logger.error(f"代码优化AI调用失败: {e}", exc_info=True)
            ai_result = {
                "optimized_code": request.code,
                "improvements": [],
                "explanation": "服务暂时不可用，请稍后重试",
                "warnings": [],
            }

        return DeepSeekOptimizeResponse(
            original_code=request.code,
            optimized_code=ai_result.get("optimized_code", request.code),
            improvements=[
                OptimizationImprovement(**imp) for imp in ai_result.get("improvements", [])
            ],
            explanation=ai_result.get("explanation", ""),
            warnings=ai_result.get("warnings", []),
            model_used=model_name,
            processing_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"代码优化错误: {e}")
        raise HTTPException(status_code=500, detail=f"代码优化失败: {str(e)}")


@router.post("/tutor", response_model=DeepSeekTutorResponse, summary="智能编程辅导")
async def ask_tutor(
    request: DeepSeekTutorRequest,
    current_user: User = Depends(get_current_user),
):
    """
    使用 DeepSeek 进行智能编程辅导

    回答用户的编程问题，提供：
    - 详细的答案解释
    - 代码示例
    - 相关主题
    - 后续学习建议
    """
    start_time = time.time()

    try:
        # 构建上下文
        context_text = ""
        if request.context:
            context_text = f"\n\n上下文代码：\n{chr(10).join(request.context[-5:])}"
        if request.code:
            context_text += f"\n\n相关代码：\n```{request.language or 'python'}\n{request.code}\n```"

        prompt = f"""你是一位专业的编程导师。请回答用户的问题：

问题：{request.question}
{context_text}

编程语言：{request.language or 'Python'}

请用JSON格式返回，格式如下：
{{
    "answer": "详细回答",
    "code_examples": [
        {{
            "title": "示例标题",
            "code": "示例代码",
            "language": "python",
            "explanation": "代码解释"
        }}
    ],
    "related_topics": ["相关主题"],
    "next_steps": ["后续学习建议"]
}}
"""

        # 调用AI服务
        model_name = _get_model_name(request.provider, request.model)
        provider = request.provider or ModelProvider.DEEPSEEK

        ai_request = CodeGenerationRequest(
            prompt=prompt,
            provider=provider,
            model=model_name,
            temperature=0.8,
            max_tokens=2000,
        )

        try:
            result = await ai_manager.generate_code(ai_request)
            ai_result = _parse_ai_response(
                {"text": result.code},
                {
                    "answer": "抱歉，我暂时无法回答这个问题",
                    "code_examples": [],
                    "related_topics": [],
                    "next_steps": [],
                }
            )
        except Exception as e:
            logger.error(f"智能辅导AI调用失败: {e}", exc_info=True)
            ai_result = {
                "answer": "服务暂时不可用，请稍后重试",
                "code_examples": [],
                "related_topics": [],
                "next_steps": [],
            }

        return DeepSeekTutorResponse(
            answer=ai_result.get("answer", ""),
            code_examples=[
                CodeExample(**example) for example in ai_result.get("code_examples", [])
            ],
            related_topics=ai_result.get("related_topics", []),
            next_steps=ai_result.get("next_steps", []),
            model_used=model_name,
            processing_time=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"智能辅导错误: {e}")
        raise HTTPException(status_code=500, detail=f"智能辅导失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check():
    """检查AI导师服务的健康状态"""
    return {
        "service": "healthy",
        "deepseek_available": True,
        "features": ["code_explain", "code_optimize", "ai_tutor"],
    }


# ========================================================================
# Hermes Agent 请求模型
# ========================================================================


class HermesChatRequest(BaseModel):
    """Hermes对话请求模型"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    use_tools: bool = Field(default=True, description="是否启用工具调用")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")


class HermesExecuteToolRequest(BaseModel):
    """Hermes工具执行请求模型"""
    tool_name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


# ========================================================================
# Hermes Agent 集成路由
# ========================================================================

@router.get("/hermes/health", summary="Hermes Agent 健康检查")
async def hermes_health_check():
    """检查Hermes Agent服务的健康状态"""
    try:
        hermes_service = get_hermes_service()
        health = await hermes_service.health_check()

        return {
            "service": "hermes_agent",
            "status": health.get("status", "unknown"),
            "enabled": hermes_service.enabled,
            "details": health
        }
    except Exception as e:
        logger.error(f"Hermes健康检查失败: {str(e)}", exc_info=True)
        return {
            "service": "hermes_agent",
            "status": "error",
            "enabled": False,
            "error": "服务暂时不可用"
        }


@router.get("/hermes/tools", summary="获取可用工具列表")
async def get_hermes_tools(
    current_user: User = Depends(get_current_user)
):
    """获取Hermes Agent可用的AI导师工具列表"""
    tools = get_ai_tutor_tools()
    tool_definitions = tools.get_tool_definitions()

    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            }
            for t in tool_definitions
        ]
    }


@router.post("/hermes/chat", summary="Hermes Agent 对话")
async def hermes_chat(
    request: HermesChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    使用Hermes Agent进行智能对话

    通过Hermes Agent的自改进AI能力提供更智能的编程辅导
    """
    hermes_service = get_hermes_service()

    if not hermes_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Hermes Agent 未启用。请配置HERMES_API_KEY或确保本地Hermes服务运行在localhost:8080"
        )

    result = await hermes_service.chat(
        request.message,
        context=request.context,
        use_tools=request.use_tools
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Hermes Agent 调用失败")
        )

    return {
        "success": True,
        "message": result.get("message", ""),
        "tool_calls": result.get("tool_calls", []),
        "usage": result.get("usage", {})
    }


@router.post("/hermes/execute", summary="执行Hermes工具")
async def hermes_execute_tool(
    request: HermesExecuteToolRequest,
    current_user: User = Depends(get_current_user)
):
    """
    直接执行MCP工具

    通过Hermes Agent的工具调用能力执行AI导师功能
    """
    try:
        tools = get_ai_tutor_tools()
        result = await tools.execute_tool(request.tool_name, request.arguments)
        return result
    except Exception as e:
        logger.error(f"工具执行失败: {request.tool_name}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="工具执行失败，请稍后重试"
        )
