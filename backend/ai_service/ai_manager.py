"""
AI管理器 - 统一管理各种AI模型的调用
"""

from importlib import import_module
import time
from typing import Any, Dict, Optional, Tuple

from config.settings import settings
import httpx
from utils.logger import get_logger

from .models import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    ModelProvider,
    ProgrammingLanguage,
)

logger = get_logger("ai_manager")

#: 懒加载的重依赖导出（PEP 562）：导出名 -> (模块路径, 模块内属性名)
#:
#: ``langchain_openai`` 会连带拉入 transformers/torch，冷启动代价约 17s，
#: 因此改为按需解析；解析结果写入模块 globals 缓存，后续访问不再进入 __getattr__。
_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "ChatOpenAI": ("langchain_openai", "ChatOpenAI"),
    "HumanMessage": ("langchain_core.messages", "HumanMessage"),
    "SystemMessage": ("langchain_core.messages", "SystemMessage"),
}


def __getattr__(name: str):
    """按需解析重依赖导出（PEP 562）。"""
    try:
        module_path, attr = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from None

    value = getattr(import_module(module_path), attr)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


def _resolve(name: str) -> Any:
    """解析懒加载导出。

    优先取模块全局（兼容 ``mock.patch("ai_service.ai_manager.ChatOpenAI")``
    这类模块属性覆盖），未命中时再走 ``__getattr__`` 触发真实导入。
    """
    value = globals().get(name)
    if value is None:
        value = __getattr__(name)
    return value


class AIManager:
    """AI模型管理器"""

    def __init__(self):
        self.providers = {
            ModelProvider.OPENAI: self._setup_openai(),
            ModelProvider.LINGMA: self._setup_lingma(),
            ModelProvider.DEEPSEEK: self._setup_deepseek(),
            ModelProvider.ANTHROPIC: self._setup_anthropic(),
            ModelProvider.GOOGLE: self._setup_google(),
        }

        # 默认模型映射
        self.default_models = {
            ModelProvider.OPENAI: settings.OPENAI_MODEL,
            ModelProvider.LINGMA: settings.LINGMA_MODEL,
            ModelProvider.DEEPSEEK: settings.DEEPSEEK_MODEL,
            ModelProvider.ANTHROPIC: settings.ANTHROPIC_MODEL,
            ModelProvider.GOOGLE: settings.GOOGLE_MODEL,
        }

    def _setup_openai(self):
        """设置OpenAI客户端"""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            return None

        chat_openai = _resolve("ChatOpenAI")
        return chat_openai(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

    def _setup_lingma(self):
        """设置Lingma客户端"""
        if not settings.LINGMA_API_KEY:
            logger.warning("Lingma API key not configured")
            return None

        # Lingma使用自定义HTTP客户端
        return httpx.AsyncClient(
            base_url="https://api.lingma.com/v1",
            headers={
                "Authorization": f"Bearer {settings.LINGMA_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    def _setup_deepseek(self):
        """设置DeepSeek客户端"""
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API key not configured")
            return None

        return httpx.AsyncClient(
            base_url="https://api.deepseek.com/v1",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    def _setup_anthropic(self):
        """设置Anthropic客户端"""
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("Anthropic API key not configured")
            return None

        return httpx.AsyncClient(
            base_url="https://api.anthropic.com/v1",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )

    def _setup_google(self):
        """设置Google客户端"""
        if not settings.GOOGLE_API_KEY:
            logger.warning("Google API key not configured")
            return None

        return httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            headers={"Content-Type": "application/json"},
        )

    async def generate_code(
        self, request: CodeGenerationRequest
    ) -> CodeGenerationResponse:
        """生成代码的主要方法"""
        start_time = time.time()

        try:
            # 验证提供商是否可用
            if (
                request.provider not in self.providers
                or self.providers[request.provider] is None
            ):
                raise ValueError(
                    f"Provider {request.provider.value} is not configured or unavailable"
                )

            # 获取模型名称
            model_name = request.model or self.default_models.get(request.provider)
            if not model_name:
                raise ValueError(
                    f"No model configured for provider {request.provider.value}"
                )

            # 根据提供商调用相应的方法
            if request.provider == ModelProvider.OPENAI:
                result = await self._call_openai(request, model_name)
            elif request.provider == ModelProvider.LINGMA:
                result = await self._call_lingma(request, model_name)
            elif request.provider == ModelProvider.DEEPSEEK:
                result = await self._call_deepseek(request, model_name)
            elif request.provider == ModelProvider.ANTHROPIC:
                result = await self._call_anthropic(request, model_name)
            elif request.provider == ModelProvider.GOOGLE:
                result = await self._call_google(request, model_name)
            else:
                raise ValueError(f"Unsupported provider: {request.provider}")

            processing_time = time.time() - start_time

            return CodeGenerationResponse(
                code=result["code"],
                provider=request.provider,
                model=model_name,
                tokens_used=result.get("tokens_used", 0),
                processing_time=processing_time,
                language_detected=self._detect_language(result["code"]),
            )

        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    def _detect_language(self, code: str) -> Optional[ProgrammingLanguage]:
        """简单检测代码语言"""
        code_lower = code.lower()

        # 基于关键字的简单检测
        if "def " in code_lower or "import " in code_lower or "print(" in code_lower:
            return ProgrammingLanguage.PYTHON
        elif (
            "function " in code_lower or "const " in code_lower or "let " in code_lower
        ):
            return ProgrammingLanguage.JAVASCRIPT
        elif "interface " in code_lower or "type " in code_lower:
            return ProgrammingLanguage.TYPESCRIPT
        elif "public class " in code_lower or "private " in code_lower:
            return ProgrammingLanguage.JAVA
        elif "using " in code_lower or "namespace " in code_lower:
            return ProgrammingLanguage.CSHARP
        elif "func " in code_lower or "package " in code_lower:
            return ProgrammingLanguage.GO

        return None

    async def _call_openai(
        self, request: CodeGenerationRequest, model_name: str
    ) -> Dict[str, Any]:
        """调用OpenAI API"""
        client = self.providers[ModelProvider.OPENAI]

        # 构建消息
        system_message_cls = _resolve("SystemMessage")
        human_message_cls = _resolve("HumanMessage")

        messages = []
        if request.system_prompt:
            messages.append(system_message_cls(content=request.system_prompt))

        # 添加代码生成专用提示
        code_prompt = f"请根据以下需求生成代码：\n\n{request.prompt}"
        if request.language:
            code_prompt += f"\n\n请使用 {request.language.value} 编程语言。"

        messages.append(human_message_cls(content=code_prompt))

        # 调用模型
        response = await client.agenerate([messages])

        return {
            "code": response.generations[0][0].text,
            "tokens_used": response.llm_output.get("token_usage", {}).get(
                "total_tokens", 0
            ),
        }

    async def _call_lingma(
        self, request: CodeGenerationRequest, model_name: str
    ) -> Dict[str, Any]:
        """调用Lingma API"""
        client = self.providers[ModelProvider.LINGMA]

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": f"生成代码：{request.prompt}"}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.system_prompt:
            payload["messages"].insert(
                0, {"role": "system", "content": request.system_prompt}
            )

        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        return {
            "code": data["choices"][0]["message"]["content"],
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
        }

    async def _call_deepseek(
        self, request: CodeGenerationRequest, model_name: str
    ) -> Dict[str, Any]:
        """调用DeepSeek API"""
        client = self.providers[ModelProvider.DEEPSEEK]

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": f"生成代码：{request.prompt}"}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()
        return {
            "code": data["choices"][0]["message"]["content"],
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
        }

    async def _call_anthropic(
        self, request: CodeGenerationRequest, model_name: str
    ) -> Dict[str, Any]:
        """调用Anthropic API"""
        client = self.providers[ModelProvider.ANTHROPIC]

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": f"生成代码：{request.prompt}"}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt

        response = await client.post("/messages", json=payload)
        response.raise_for_status()

        data = response.json()
        return {
            "code": data["content"][0]["text"],
            "tokens_used": data.get("usage", {}).get("input_tokens", 0)
            + data.get("usage", {}).get("output_tokens", 0),
        }

    async def _call_google(
        self, request: CodeGenerationRequest, model_name: str
    ) -> Dict[str, Any]:
        """调用Google API"""
        client = self.providers[ModelProvider.GOOGLE]

        payload = {
            "contents": [{"parts": [{"text": f"生成代码：{request.prompt}"}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        response = await client.post(
            f"/models/{model_name}:generateContent?key={settings.GOOGLE_API_KEY}",
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return {
            "code": data["candidates"][0]["content"]["parts"][0]["text"],
            "tokens_used": 0,  # Google API不直接返回token统计
        }


# 创建全局实例
ai_manager = AIManager()
