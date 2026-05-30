"""
AI创意激发引擎测试用例
"""

from unittest.mock import AsyncMock, patch

import pytest

from ai_service.business_evaluator import BusinessEvaluator
from ai_service.creativity_engine import CreativityEngine
from ai_service.idea_scorer import IdeaScorer
from ai_service.image_generator import DalleImageGenerator
from ai_service.prompt_templates import PromptTemplateManager
from models.creativity_models import (
    BusinessEvaluationRequest,
    BusinessEvaluationResponse,
    IdeaGenerationRequest,
    IdeaGenerationResponse,
    IdeaScoreRequest,
    IdeaScoreResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    PromptTemplateCreate,
)


class TestCreativityEngine:
    """创意引擎核心功能测试"""

    @pytest.fixture
    def creativity_engine(self):
        """创建创意引擎实例"""
        return CreativityEngine()

    @pytest.mark.asyncio
    async def test_generate_creative_idea_success(self, creativity_engine):
        """测试成功生成创意想法"""
        # 模拟AI管理器响应
        mock_ai_response = AsyncMock()
        mock_ai_response.code = (
            "# 创新智能家居控制系统\n\n这是一个基于物联网的智能家居控制系统..."
        )
        mock_ai_response.tokens_used = 150
        mock_ai_response.processing_time = 2.5

        with patch.object(
            creativity_engine.ai_manager, "generate_code", return_value=mock_ai_response
        ):
            request = IdeaGenerationRequest(
                category="technology", temperature=0.8, max_tokens=1500
            )

            response = await creativity_engine.generate_creative_idea(request)

            assert isinstance(response, IdeaGenerationResponse)
            assert response.title == "创新智能家居控制系统"
            assert "智能家居控制系统" in response.content
            assert response.processing_time > 0
            assert response.tokens_used == 150

    @pytest.mark.asyncio
    async def test_generate_creative_image_mock(self, creativity_engine):
        """测试图像生成（使用模拟数据）"""
        request = ImageGenerationRequest(
            prompt="一个现代智能家居控制面板的界面设计", style="realistic", n=2
        )

        # 由于DALL-E API需要实际密钥，这里测试核心逻辑
        with patch.object(creativity_engine, "_call_dalle_api") as mock_dalle:
            mock_dalle.return_value = {
                "data": [
                    {
                        "url": "https://example.com/image1.png",
                        "revised_prompt": request.prompt,
                    },
                    {
                        "url": "https://example.com/image2.png",
                        "revised_prompt": request.prompt,
                    },
                ]
            }

            response = await creativity_engine.generate_creative_image(request)

            assert isinstance(response, ImageGenerationResponse)
            assert len(response.images) == 2
            assert response.total_cost > 0
            assert response.processing_time > 0


class TestPromptTemplateManager:
    """Prompt模板管理器测试"""

    @pytest.fixture
    def template_manager(self):
        """创建模板管理器实例"""
        return PromptTemplateManager()

    def test_validate_template_variables_valid(self, template_manager):
        """测试有效的模板变量验证"""
        variables = {
            "场景": {"type": "string", "description": "应用场景"},
            "预算": {"type": "number", "description": "预算金额"},
        }

        # 不应该抛出异常
        template_manager._validate_template_variables(variables)

    def test_validate_template_variables_invalid_type(self, template_manager):
        """测试无效的模板变量类型"""
        variables = {"场景": "invalid_type"}  # 应该是字典

        with pytest.raises(ValueError, match="变量 必须是字典格式"):
            template_manager._validate_template_variables(variables)

    def test_validate_template_variables_missing_type(self, template_manager):
        """测试缺少类型的模板变量"""
        variables = {"场景": {"description": "应用场景"}}  # 缺少type字段

        with pytest.raises(ValueError, match="变量 必须包含 type 字段"):
            template_manager._validate_template_variables(variables)


class TestIdeaScorer:
    """创意评分器测试"""

    @pytest.fixture
    def idea_scorer(self):
        """创建创意评分器实例"""
        return IdeaScorer()

    @pytest.mark.asyncio
    async def test_score_idea_success(self, idea_scorer):
        """测试创意评分成功"""
        request = IdeaScoreRequest(
            idea_content="基于AI的个性化学习平台，通过分析学生行为数据提供定制化学习路径",
            technical_requirements="需要机器学习算法和大数据处理能力",
            business_model="SaaS订阅模式，按学生数量收费",
            market_context="在线教育市场快速增长，个性化需求强烈",
        )

        # 模拟AI评分响应
        with patch.multiple(
            idea_scorer,
            _ai_evaluate_creativity=AsyncMock(return_value=8.5),
            _ai_evaluate_feasibility=AsyncMock(return_value=7.0),
            _ai_evaluate_commercial_value=AsyncMock(return_value=8.0),
        ):

            response = await idea_scorer.score_idea(request)

            assert isinstance(response, IdeaScoreResponse)
            assert 0 <= response.total_score <= 10
            assert 0 <= response.creativity <= 10
            assert 0 <= response.feasibility <= 10
            assert 0 <= response.commercial_value <= 10
            assert len(response.recommendations) > 0


class TestDalleImageGenerator:
    """DALL-E图像生成器测试"""

    @pytest.fixture
    def dalle_generator(self):
        """创建DALL-E生成器实例"""
        generator = DalleImageGenerator()
        # 使用测试API密钥
        generator.api_key = "test-api-key"
        return generator

    def test_validate_request_valid(self, dalle_generator):
        """测试有效的请求验证"""
        request = ImageGenerationRequest(
            prompt="现代科技产品的界面设计", size="1024x1024", n=1
        )

        # 不应该抛出异常
        dalle_generator._validate_request(request)

    def test_validate_request_invalid_prompt_length(self, dalle_generator):
        """测试无效的Prompt长度"""
        request = ImageGenerationRequest(prompt="短", size="1024x1024")  # 太短

        with pytest.raises(ValueError, match="Prompt长度不能少于10个字符"):
            dalle_generator._validate_request(request)

    def test_is_valid_size(self, dalle_generator):
        """测试图像尺寸验证"""
        assert dalle_generator._is_valid_size("1024x1024") == True
        assert dalle_generator._is_valid_size("1024x1792") == True
        assert dalle_generator._is_valid_size("invalid") == False


class TestBusinessEvaluator:
    """商业价值评估器测试"""

    @pytest.fixture
    def business_evaluator(self):
        """创建商业评估器实例"""
        return BusinessEvaluator()

    @pytest.mark.asyncio
    async def test_evaluate_business_value_success(self, business_evaluator):
        """测试商业价值评估成功"""
        request = BusinessEvaluationRequest(
            idea_description="AI驱动的个性化健康管理应用",
            target_market="健康意识强的年轻人和中年人群",
            estimated_costs={
                "开发成本": 500000,
                "运营成本": 100000,
                "营销成本": 200000,
            },
            revenue_projections={"第一年": 100000, "第二年": 500000, "第三年": 1500000},
            competition_analysis="市场上有类似产品，但我们的AI算法更具优势",
        )

        response = await business_evaluator.evaluate_business_value(request)

        assert isinstance(response, BusinessEvaluationResponse)
        assert response.cost_benefit_ratio >= 0
        assert 0 <= response.market_potential <= 10
        assert "risk" in response.risk_assessment


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_creativity_workflow(self):
        """测试完整的创意工作流程"""
        # 1. 初始化各个组件
        engine = CreativityEngine()
        scorer = IdeaScorer()
        PromptTemplateManager()

        # 2. 创建测试模板
        template_data = PromptTemplateCreate(
            name="测试模板",
            category="technology",
            template="为{领域}设计一个创新的{产品类型}解决方案",
            variables={
                "领域": {"type": "string", "description": "技术领域"},
                "产品类型": {"type": "string", "description": "产品类别"},
            },
            description="用于测试的模板",
        )

        # 3. 模拟完整流程
        with patch.object(engine.ai_manager, "generate_code") as mock_generate:
            mock_generate.return_value = AsyncMock(
                code="# 智能家居控制系统\n\n基于物联网的智能家居管理方案...",
                tokens_used=200,
                processing_time=3.0,
            )

            # 生成创意
            gen_request = IdeaGenerationRequest(
                custom_prompt="生成一个智能家居创新方案", temperature=0.8
            )

            idea_response = await engine.generate_creative_idea(gen_request)
            assert idea_response.title == "智能家居控制系统"

            # 评分创意
            score_request = IdeaScoreRequest(idea_content=idea_response.content)

            with patch.multiple(
                scorer,
                _ai_evaluate_creativity=AsyncMock(return_value=8.0),
                _ai_evaluate_feasibility=AsyncMock(return_value=7.5),
                _ai_evaluate_commercial_value=AsyncMock(return_value=7.0),
            ):

                score_response = await scorer.score_idea(score_request)
                assert score_response.total_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
