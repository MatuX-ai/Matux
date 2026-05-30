import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from ..config.settings import get_settings
from ..models.ai_completion import (
    CompletionRequest,
    CompletionResponse,
    CompletionSuggestion,
    ContextAnalysisResult,
    ModelProvider,
    ProgrammingLanguage,
)
from .ai_manager import AIManager
from .completion_memory import completion_memory

logger = logging.getLogger(__name__)


class CodeCompletionService:
    """核心代码补全服务"""

    def __init__(self):
        self.ai_manager = AIManager()
        self.settings = get_settings()
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def get_completions(self, request: CompletionRequest) -> CompletionResponse:
        """
        获取代码补全建议

        Args:
            request: 补全请求对象

        Returns:
            补全响应对象
        """
        start_time = time.time()

        try:
            # 输入验证
            if len(request.prefix) < self.settings.COMPLETION_MIN_PREFIX_LENGTH:
                return CompletionResponse(
                    suggestions=[],
                    processing_time=time.time() - start_time,
                    model_used="validation",
                    cache_hit=False,
                    context_analyzed=False,
                )

            # 限制上下文行数
            context_lines = request.context[
                -self.settings.COMPLETION_MAX_CONTEXT_LINES :
            ]

            # 尝试从缓存获取
            cache_result = None
            if self.settings.COMPLETION_ENABLE_CACHING:
                cache_result = await completion_memory.get_cached_completion(
                    request.prefix
                )

            if cache_result:
                # 从缓存返回结果
                completions_data, confidence_scores = cache_result
                suggestions = [
                    CompletionSuggestion(**data) for data in completions_data
                ]

                return CompletionResponse(
                    suggestions=suggestions,
                    processing_time=time.time() - start_time,
                    model_used="cache",
                    cache_hit=True,
                    context_analyzed=False,
                )

            # 进行上下文分析
            context_analysis = None
            if self.settings.COMPLETION_ENABLE_SYNTAX_ANALYSIS:
                context_analysis = await completion_memory.analyze_context_patterns(
                    context_lines, request.language or ProgrammingLanguage.PYTHON
                )

            # 生成补全建议
            suggestions = await self._generate_completions(request, context_analysis)

            # 缓存结果
            if self.settings.COMPLETION_ENABLE_CACHING and suggestions:
                await self._cache_completions(request.prefix, suggestions)

            processing_time = time.time() - start_time

            return CompletionResponse(
                suggestions=suggestions,
                processing_time=processing_time,
                model_used=request.provider.value if request.provider else "default",
                cache_hit=False,
                context_analyzed=bool(context_analysis),
            )

        except Exception as e:
            logger.error(f"代码补全服务错误: {e}")
            return CompletionResponse(
                suggestions=[],
                processing_time=time.time() - start_time,
                model_used="error",
                cache_hit=False,
                context_analyzed=False,
            )

    async def _generate_completions(
        self,
        request: CompletionRequest,
        context_analysis: Optional[ContextAnalysisResult],
    ) -> List[CompletionSuggestion]:
        """
        生成补全建议

        Args:
            request: 补全请求
            context_analysis: 上下文分析结果

        Returns:
            补全建议列表
        """
        # 获取用户历史模式
        user_patterns = []
        if request.user_id:
            user_patterns = await completion_memory.get_user_patterns(
                request.user_id, request.language or ProgrammingLanguage.PYTHON, limit=5
            )

        # 构建AI提示
        prompt = self._build_completion_prompt(request, context_analysis, user_patterns)

        # 调用AI模型
        ai_responses = await self._call_multiple_models(request, prompt)

        # 合并和排序结果
        suggestions = self._merge_and_rank_completions(
            ai_responses, request.language, context_analysis
        )

        # 限制建议数量
        return suggestions[: request.max_suggestions]

    def _build_completion_prompt(
        self,
        request: CompletionRequest,
        context_analysis: Optional[ContextAnalysisResult],
        user_patterns: List[Dict[str, Any]],
    ) -> str:
        """
        构建AI补全提示

        Args:
            request: 补全请求
            context_analysis: 上下文分析结果
            user_patterns: 用户历史模式

        Returns:
            构建的提示文本
        """
        prompt_parts = []

        # 基础指令
        prompt_parts.append(
            "你是一个专业的代码补全助手。请根据提供的代码前缀和上下文，生成合适的代码补全建议。"
        )

        # 编程语言指示
        if request.language:
            prompt_parts.append(f"请使用 {request.language.value} 编程语言。")

        # 上下文信息
        if context_analysis:
            prompt_parts.append(f"当前作用域: {context_analysis.scope_level}")
            prompt_parts.append(f"语法上下文: {context_analysis.syntax_context}")

            if context_analysis.variable_declarations:
                vars_list = ", ".join(context_analysis.variable_declarations[:5])
                prompt_parts.append(f"已声明变量: {vars_list}")

            if context_analysis.imported_modules:
                modules_list = ", ".join(context_analysis.imported_modules[:3])
                prompt_parts.append(f"已导入模块: {modules_list}")

        # 用户历史模式
        if user_patterns:
            prompt_parts.append("\n用户的常用代码模式:")
            for i, pattern in enumerate(user_patterns[:3]):
                snippet = (
                    pattern["code_snippet"][:100] + "..."
                    if len(pattern["code_snippet"]) > 100
                    else pattern["code_snippet"]
                )
                prompt_parts.append(f"{i+1}. {snippet}")

        # 上下文代码
        if request.context:
            context_text = "\n".join(request.context[-10:])  # 最近10行
            prompt_parts.append(f"\n上下文代码:\n{context_text}")

        # 待补全的前缀
        prompt_parts.append(f"\n请补全以下代码:\n{request.prefix}")
        prompt_parts.append("请只返回补全的部分，不要包含原有前缀。")

        return "\n".join(prompt_parts)

    async def _call_multiple_models(
        self, request: CompletionRequest, prompt: str
    ) -> List[Tuple[str, float, str]]:
        """
        调用多个AI模型获取补全结果

        Args:
            request: 补全请求
            prompt: 构建的提示

        Returns:
            [(补全文本, 置信度, 模型名)] 列表
        """
        providers = (
            [request.provider]
            if request.provider
            else [self.settings.COMPLETION_DEFAULT_PROVIDER]
        )
        providers.extend(self.settings.COMPLETION_FALLBACK_PROVIDERS)

        tasks = []
        for provider in providers[:3]:  # 限制最多3个提供商
            task = self._call_single_model(provider, prompt, request)
            tasks.append(task)

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"模型 {providers[i]} 调用失败: {result}")
                continue
            if result:
                valid_results.append(result)

        return valid_results

    async def _call_single_model(
        self, provider: ModelProvider, prompt: str, request: CompletionRequest
    ) -> Optional[Tuple[str, float, str]]:
        """
        调用单个AI模型

        Args:
            provider: AI提供商
            prompt: 提示文本
            request: 请求对象

        Returns:
            (补全文本, 置信度, 模型名) 或 None
        """
        try:
            # 根据提供商选择模型
            model_mapping = {
                ModelProvider.OPENAI: "gpt-4-turbo",
                ModelProvider.LINGMA: "lingma-code-pro",
                ModelProvider.DEEPSEEK: "deepseek-coder",
            }

            model_name = model_mapping.get(provider, "gpt-4-turbo")

            # 调用AI管理器
            ai_request = type(
                "AIRequest",
                (),
                {
                    "prompt": prompt,
                    "temperature": request.temperature,
                    "max_tokens": 200,
                },
            )()

            if provider == ModelProvider.OPENAI:
                result = await self.ai_manager._call_openai(ai_request, model_name)
            elif provider == ModelProvider.LINGMA:
                result = await self.ai_manager._call_lingma(ai_request, model_name)
            elif provider == ModelProvider.DEEPSEEK:
                result = await self.ai_manager._call_deepseek(ai_request, model_name)
            else:
                return None

            completion_text = result.get("code", "").strip()
            if completion_text:
                # 计算基础置信度（基于提供商可靠性）
                base_confidence = {
                    ModelProvider.OPENAI: 0.95,
                    ModelProvider.LINGMA: 0.85,
                    ModelProvider.DEEPSEEK: 0.80,
                }.get(provider, 0.7)

                # 根据补全质量调整置信度
                quality_score = self._assess_completion_quality(
                    completion_text, request.prefix, request.language
                )

                final_confidence = base_confidence * quality_score

                return (completion_text, final_confidence, model_name)

        except Exception as e:
            logger.error(f"调用 {provider} 模型失败: {e}")
            return None

    def _assess_completion_quality(
        self, completion: str, prefix: str, language: Optional[ProgrammingLanguage]
    ) -> float:
        """
        评估补全质量

        Args:
            completion: 补全文本
            prefix: 前缀文本
            language: 编程语言

        Returns:
            质量评分 (0.0-1.0)
        """
        score = 1.0

        # 检查是否为空或过短
        if not completion or len(completion) < 2:
            return 0.1

        # 检查语法完整性
        if language:
            syntax_valid = self._check_syntax_validity(completion, language)
            if not syntax_valid:
                score *= 0.7

        # 检查重复性（避免简单重复前缀）
        if completion.lower().startswith(prefix.lower()):
            score *= 0.8

        # 检查合理性长度
        if len(completion) > 200:  # 过长可能不是好的补全
            score *= 0.8
        elif len(completion) < 5:  # 过短可能不完整
            score *= 0.9

        return max(0.1, min(1.0, score))

    def _check_syntax_validity(
        self, completion: str, language: ProgrammingLanguage
    ) -> bool:
        """
        检查补全的语法有效性

        Args:
            completion: 补全文本
            language: 编程语言

        Returns:
            是否语法有效
        """
        try:
            if language == ProgrammingLanguage.PYTHON:
                # 简单的Python语法检查
                if ":" in completion and not completion.strip().endswith(":"):
                    # 可能是不完整的语句
                    return False
                if completion.count("(") != completion.count(")"):
                    return False

            elif language == ProgrammingLanguage.JAVASCRIPT:
                # JavaScript语法检查
                if completion.count("{") != completion.count("}"):
                    return False
                if ";" not in completion and not completion.strip().endswith("{"):
                    # 可能需要分号结尾
                    return False

            return True

        except Exception:
            return True  # 如果无法确定，假设有效

    def _merge_and_rank_completions(
        self,
        ai_responses: List[Tuple[str, float, str]],
        language: Optional[ProgrammingLanguage],
        context_analysis: Optional[ContextAnalysisResult],
    ) -> List[CompletionSuggestion]:
        """
        合并和排序来自不同模型的补全结果

        Args:
            ai_responses: AI响应列表
            language: 编程语言
            context_analysis: 上下文分析结果

        Returns:
            排序后的补全建议列表
        """
        if not ai_responses:
            return []

        # 去重和合并
        unique_completions = {}
        for text, confidence, model in ai_responses:
            # 标准化文本用于去重
            normalized_text = text.strip().lower()

            if normalized_text not in unique_completions:
                unique_completions[normalized_text] = {
                    "text": text,
                    "confidences": [confidence],
                    "models": [model],
                    "count": 1,
                }
            else:
                unique_completions[normalized_text]["confidences"].append(confidence)
                unique_completions[normalized_text]["models"].append(model)
                unique_completions[normalized_text]["count"] += 1

        # 创建建议对象并计算最终分数
        suggestions = []
        for item in unique_completions.values():
            # 计算平均置信度
            avg_confidence = sum(item["confidences"]) / len(item["confidences"])

            # 计算共识分数（多个模型同意的程度）
            consensus_score = item["count"] / len(ai_responses)

            # 计算最终相关性分数
            relevance_score = avg_confidence * 0.7 + consensus_score * 0.3

            # 提取语言特征
            language_features = self._extract_language_features(
                item["text"], language, context_analysis
            )

            suggestion = CompletionSuggestion(
                text=item["text"],
                confidence=avg_confidence,
                relevance_score=relevance_score,
                language_features=language_features,
                metadata={"models": item["models"], "consensus_score": consensus_score},
            )

            suggestions.append(suggestion)

        # 按相关性分数排序
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)

        return suggestions

    def _extract_language_features(
        self,
        text: str,
        language: Optional[ProgrammingLanguage],
        context_analysis: Optional[ContextAnalysisResult],
    ) -> List[str]:
        """
        提取语言特征

        Args:
            text: 文本内容
            language: 编程语言
            context_analysis: 上下文分析结果

        Returns:
            特征标签列表
        """
        features = []

        if not language:
            return features

        text_lower = text.lower()

        # 基于语言的关键字特征
        if language == ProgrammingLanguage.PYTHON:
            if "def " in text_lower:
                features.append("function_definition")
            if "class " in text_lower:
                features.append("class_definition")
            if "import " in text_lower:
                features.append("import_statement")
            if any(op in text for op in ["+", "-", "*", "/", "="]):
                features.append("expression")

        elif language == ProgrammingLanguage.JAVASCRIPT:
            if "function " in text_lower or "=>" in text:
                features.append("function_definition")
            if "class " in text_lower:
                features.append("class_definition")
            if "import " in text_lower or "require(" in text_lower:
                features.append("import_statement")
            if "console." in text_lower:
                features.append("debug_statement")

        # 基于上下文的特征
        if context_analysis:
            if (
                context_analysis.scope_level == "function"
                and "(" in text
                and ")" in text
            ):
                features.append("function_call")
            if context_analysis.syntax_context == "import" and "." in text:
                features.append("module_access")

        return list(set(features))  # 去重

    async def _cache_completions(
        self, prefix: str, suggestions: List[CompletionSuggestion]
    ):
        """
        缓存补全结果

        Args:
            prefix: 前缀
            suggestions: 补全建议列表
        """
        try:
            completions_data = [
                {
                    "text": s.text,
                    "confidence": s.confidence,
                    "relevance_score": s.relevance_score,
                    "language_features": s.language_features,
                    "metadata": s.metadata,
                }
                for s in suggestions
            ]

            confidence_scores = [s.confidence for s in suggestions]

            await completion_memory.cache_completion(
                prefix, completions_data, confidence_scores
            )

        except Exception as e:
            logger.error(f"缓存补全结果失败: {e}")


# 全局实例
code_completion_service = CodeCompletionService()
