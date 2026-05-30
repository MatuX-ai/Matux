from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.ai_service.completion_memory import CompletionMemory
from backend.models.ai_completion import (
    CompletionRequest,
    CompletionSuggestion,
    ModelProvider,
    ProgrammingLanguage,
)
from backend.services.code_completion_service import CodeCompletionService


class TestCodeCompletionService:
    """代码补全服务测试"""

    @pytest.fixture
    def completion_service(self):
        """创建补全服务实例"""
        return CodeCompletionService()

    @pytest.fixture
    def mock_completion_request(self):
        """创建模拟补全请求"""
        return CompletionRequest(
            prefix="def calculate_",
            context=["def add(a, b):", "    return a + b", ""],
            language=ProgrammingLanguage.PYTHON,
            provider=ModelProvider.OPENAI,
            max_suggestions=5,
            temperature=0.7,
        )

    @pytest.mark.asyncio
    async def test_get_completions_success(
        self, completion_service, mock_completion_request
    ):
        """测试成功获取补全建议"""
        with patch.object(completion_service, "_generate_completions") as mock_generate:
            mock_suggestions = [
                CompletionSuggestion(
                    text="sum(numbers)",
                    confidence=0.95,
                    relevance_score=0.92,
                    language_features=["function_call"],
                    metadata={},
                )
            ]
            mock_generate.return_value = mock_suggestions

            response = await completion_service.get_completions(mock_completion_request)

            assert response.suggestions == mock_suggestions
            assert response.processing_time >= 0
            assert response.model_used == "openai"
            assert response.cache_hit is False

    @pytest.mark.asyncio
    async def test_get_completions_with_cache(
        self, completion_service, mock_completion_request
    ):
        """测试缓存命中情况"""
        with patch(
            "backend.ai_service.completion_memory.completion_memory"
        ) as mock_memory:
            mock_memory.get_cached_completion.return_value = (
                [
                    {
                        "text": "sum(numbers)",
                        "confidence": 0.95,
                        "relevance_score": 0.92,
                        "language_features": ["function_call"],
                        "metadata": {},
                    }
                ],
                [0.95],
            )

            response = await completion_service.get_completions(mock_completion_request)

            assert len(response.suggestions) == 1
            assert response.cache_hit is True
            assert response.suggestions[0].text == "sum(numbers)"

    @pytest.mark.asyncio
    async def test_get_completions_short_prefix(self, completion_service):
        """测试前缀过短的情况"""
        request = CompletionRequest(
            prefix="de", context=[], language=ProgrammingLanguage.PYTHON  # 小于最小长度
        )

        response = await completion_service.get_completions(request)

        assert response.suggestions == []
        assert response.processing_time >= 0

    @pytest.mark.asyncio
    async def test_generate_completions_multiple_models(
        self, completion_service, mock_completion_request
    ):
        """测试多模型生成补全"""
        with patch.object(completion_service, "_call_multiple_models") as mock_call:
            mock_call.return_value = [
                ("sum(numbers)", 0.95, "gpt-4-turbo"),
                ("total(values)", 0.85, "lingma-code-pro"),
                ("sum_values(data)", 0.90, "deepseek-coder"),
            ]

            suggestions = await completion_service._generate_completions(
                mock_completion_request, None
            )

            assert len(suggestions) == 3
            # 验证去重和排序逻辑
            assert suggestions[0].text in ["sum(numbers)", "sum_values(data)"]

    @pytest.mark.asyncio
    async def test_assess_completion_quality(self, completion_service):
        """测试补全质量评估"""
        # 测试高质量补全
        quality1 = completion_service._assess_completion_quality(
            "sum(numbers)", "sum(", ProgrammingLanguage.PYTHON
        )
        assert quality1 > 0.7

        # 测试低质量补全
        quality2 = completion_service._assess_completion_quality(
            "", "sum(", ProgrammingLanguage.PYTHON
        )
        assert quality2 <= 0.2

        # 测试语法无效的补全
        quality3 = completion_service._assess_completion_quality(
            "sum(numbers", "sum(", ProgrammingLanguage.PYTHON
        )
        assert quality3 < 1.0  # 语法不完整应该得分较低

    @pytest.mark.asyncio
    async def test_merge_and_rank_completions(self, completion_service):
        """测试合并和排序补全结果"""
        ai_responses = [
            ("sum(numbers)", 0.95, "gpt-4-turbo"),
            ("sum(values)", 0.90, "gpt-4-turbo"),  # 重复项
            ("total(data)", 0.85, "lingma-code-pro"),
            ("sum(numbers)", 0.92, "deepseek-coder"),  # 与第一个重复
        ]

        suggestions = completion_service._merge_and_rank_completions(
            ai_responses, ProgrammingLanguage.PYTHON, None
        )

        # 验证去重效果
        texts = [s.text for s in suggestions]
        assert len(set(texts)) == len(texts)  # 无重复

        # 验证排序（高置信度在前）
        assert suggestions[0].confidence >= suggestions[-1].confidence

    def test_extract_language_features(self, completion_service):
        """测试语言特征提取"""
        # Python特征提取
        features1 = completion_service._extract_language_features(
            "def calculate_sum(a, b):", ProgrammingLanguage.PYTHON, None
        )
        assert "function_definition" in features1

        # JavaScript特征提取
        features2 = completion_service._extract_language_features(
            "function calculateSum(a, b) {", ProgrammingLanguage.JAVASCRIPT, None
        )
        assert "function_definition" in features2

        # 导入语句特征
        features3 = completion_service._extract_language_features(
            "import numpy as np", ProgrammingLanguage.PYTHON, None
        )
        assert "import_statement" in features3


class TestCompletionMemory:
    """记忆链系统测试"""

    @pytest.fixture
    def completion_memory(self):
        """创建记忆系统实例"""
        return CompletionMemory()

    @pytest.mark.asyncio
    async def test_add_user_history(self, completion_memory):
        """测试添加用户历史记录"""
        from backend.models.ai_completion import UserHistoryRecord

        record = UserHistoryRecord(
            user_id=1,
            code_snippet="def hello():\n    print('Hello')",
            context="",
            language=ProgrammingLanguage.PYTHON,
        )

        with patch(
            "backend.database.tenant_aware_session.get_db_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.fetchone.return_value = None

            result = await completion_memory.add_user_history(record)

            assert result is True
            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_user_patterns(self, completion_memory):
        """测试获取用户模式"""
        with patch(
            "backend.database.tenant_aware_session.get_db_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # 模拟数据库返回
            mock_row = MagicMock()
            mock_row.code_snippet = "def test_func():\n    pass"
            mock_row.context = ""
            mock_row.usage_count = 5
            mock_row.last_used = datetime.utcnow()

            mock_db.execute.return_value.fetchall.return_value = [mock_row]

            patterns = await completion_memory.get_user_patterns(
                1, ProgrammingLanguage.PYTHON, 5
            )

            assert len(patterns) == 1
            assert patterns[0]["code_snippet"] == "def test_func():\n    pass"

    @pytest.mark.asyncio
    async def test_cache_completion(self, completion_memory):
        """测试缓存补全结果"""
        suggestions = [{"text": "sum(numbers)", "confidence": 0.95}]
        confidence_scores = [0.95]

        with patch(
            "backend.database.tenant_aware_session.get_db_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.fetchone.return_value = None

            result = await completion_memory.cache_completion(
                "sum(", suggestions, confidence_scores, ProgrammingLanguage.PYTHON
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_get_cached_completion(self, completion_memory):
        """测试获取缓存的补全结果"""
        with patch(
            "backend.database.tenant_aware_session.get_db_session"
        ) as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # 模拟缓存数据
            mock_row = MagicMock()
            mock_row.completions_json = '[{"text": "sum(numbers)", "confidence": 0.95}]'
            mock_row.confidence_scores_json = "[0.95]"
            mock_row.hit_count = 2

            mock_db.execute.return_value.fetchone.return_value = mock_row

            result = await completion_memory.get_cached_completion("sum(")

            assert result is not None
            completions, scores = result
            assert len(completions) == 1
            assert completions[0]["text"] == "sum(numbers)"

    def test_generate_prefix_hash(self, completion_memory):
        """测试前缀哈希生成"""
        prefix = "def calculate_"
        hash1 = completion_memory._generate_prefix_hash(prefix)
        hash2 = completion_memory._generate_prefix_hash(prefix)

        # 相同前缀应该产生相同哈希
        assert hash1 == hash2

        # 不同前缀应该产生不同哈希
        hash3 = completion_memory._generate_prefix_hash("def compute_")
        assert hash1 != hash3

    def test_detect_scope_level(self, completion_memory):
        """测试作用域级别检测"""
        # 类定义
        context1 = ["class Calculator:", "    def __init__(self):", "        pass"]
        assert completion_memory._detect_scope_level(context1) == "class"

        # 函数定义
        context2 = ["def calculate_sum(a, b):", "    "]
        assert completion_memory._detect_scope_level(context2) == "function"

        # 块级作用域
        context3 = ["if condition:", "    "]
        assert completion_memory._detect_scope_level(context3) == "block"

        # 全局作用域
        context4 = ["x = 10", ""]
        assert completion_memory._detect_scope_level(context4) == "global"


@pytest.mark.integration
class TestCompletionIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_completion_flow(self):
        """测试完整的补全流程"""
        # 这个测试需要实际的AI服务运行
        service = CodeCompletionService()

        request = CompletionRequest(
            prefix="def fibonacci(",
            context=[
                "def factorial(n):",
                "    if n <= 1:",
                "        return 1",
                "    return n * factorial(n-1)",
                "",
            ],
            language=ProgrammingLanguage.PYTHON,
            max_suggestions=3,
        )

        response = await service.get_completions(request)

        # 验证响应结构
        assert hasattr(response, "suggestions")
        assert hasattr(response, "processing_time")
        assert hasattr(response, "model_used")

        # 验证处理时间合理
        assert 0 <= response.processing_time <= 10  # 10秒内应该完成

        # 如果有建议，验证建议格式
        if response.suggestions:
            for suggestion in response.suggestions:
                assert hasattr(suggestion, "text")
                assert hasattr(suggestion, "confidence")
                assert 0 <= suggestion.confidence <= 1
