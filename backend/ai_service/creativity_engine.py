"""
创意激发引擎核心服务
负责创意生成、评分、图像生成等核心功能
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from ai_service.ai_manager import AIManager
from ai_service.models import ModelProvider
from models.creativity_models import (
    BusinessEvaluationRequest,
    BusinessEvaluationResponse,
    IdeaCategory,
    IdeaGenerationRequest,
    IdeaGenerationResponse,
    IdeaScoreRequest,
    IdeaScoreResponse,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageStyle,
)

logger = logging.getLogger(__name__)


class CreativityEngine:
    """创意激发引擎主类"""

    def __init__(self):
        self.ai_manager = AIManager()
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """初始化默认配置"""
        self.default_creativity_config = {
            "temperature": 0.8,
            "max_tokens": 1500,
            "provider": ModelProvider.OPENAI,
            "model": "gpt-4-turbo",
        }

        self.default_image_config = {
            "quality": "standard",
            "size": "1024x1024",
            "style": ImageStyle.REALISTIC,
        }

        self.scoring_weights = {
            "creativity": 0.4,
            "feasibility": 0.3,
            "commercial_value": 0.3,
        }

    async def generate_creative_idea(
        self, request: IdeaGenerationRequest
    ) -> IdeaGenerationResponse:
        """
        生成创意想法

        Args:
            request: 创意生成请求

        Returns:
            IdeaGenerationResponse: 创意生成响应
        """
        start_time = time.time()
        logger.info(f"开始生成创意想法: {request.category}")

        try:
            # 构建Prompt
            prompt = await self._build_creative_prompt(request)

            # 调用AI生成创意
            ai_response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=request.provider or self.default_creativity_config["provider"],
                model=request.model or self.default_creativity_config["model"],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt="你是一个专业的创意专家，请生成高质量、实用的创意想法。",
            )

            # 提取创意标题和内容
            title, content = self._extract_idea_components(ai_response.code)

            processing_time = time.time() - start_time

            response = IdeaGenerationResponse(
                idea_id=0,  # 实际使用时需要保存到数据库并获取真实ID
                title=title,
                content=content,
                category=request.category.value if request.category else None,
                processing_time=processing_time,
                tokens_used=ai_response.tokens_used,
            )

            logger.info(f"创意生成完成，耗时: {processing_time:.2f}秒")
            return response

        except Exception as e:
            logger.error(f"创意生成失败: {str(e)}")
            raise

    async def generate_creative_image(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """
        生成创意图像

        Args:
            request: 图像生成请求

        Returns:
            ImageGenerationResponse: 图像生成响应
        """
        start_time = time.time()
        logger.info(f"开始生成创意图像: {request.prompt[:50]}...")

        try:
            # 调用DALL-E 3 API
            images = await self._call_dalle_api(request)

            processing_time = time.time() - start_time
            total_cost = len(images) * 0.04  # DALL-E 3每张图片约$0.04

            response = ImageGenerationResponse(
                images=images, processing_time=processing_time, total_cost=total_cost
            )

            logger.info(
                f"图像生成完成，生成{len(images)}张图片，耗时: {processing_time:.2f}秒"
            )
            return response

        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            raise

    async def score_creative_idea(self, request: IdeaScoreRequest) -> IdeaScoreResponse:
        """
        对创意想法进行多维度评分

        Args:
            request: 创意评分请求

        Returns:
            IdeaScoreResponse: 创意评分响应
        """
        start_time = time.time()
        logger.info("开始对创意想法进行评分")

        try:
            # 并行计算各项得分
            tasks = [
                self._calculate_creativity_score(request.idea_content),
                self._calculate_feasibility_score(
                    request.idea_content, request.technical_requirements
                ),
                self._calculate_commercial_value_score(
                    request.idea_content, request.business_model, request.market_context
                ),
            ]

            creativity_score, feasibility_score, commercial_score = (
                await asyncio.gather(*tasks)
            )

            # 计算综合得分
            weights = request.scoring_criteria or self.scoring_weights
            total_score = (
                weights.get("creativity", 0.4) * creativity_score
                + weights.get("feasibility", 0.3) * feasibility_score
                + weights.get("commercial_value", 0.3) * commercial_score
            )

            # 生成详细分析
            detailed_analysis = await self._generate_detailed_analysis(
                request.idea_content,
                creativity_score,
                feasibility_score,
                commercial_score,
            )

            # 生成改进建议
            recommendations = await self._generate_recommendations(
                request.idea_content,
                creativity_score,
                feasibility_score,
                commercial_score,
            )

            processing_time = time.time() - start_time

            response = IdeaScoreResponse(
                total_score=round(total_score, 2),
                creativity=round(creativity_score, 2),
                feasibility=round(feasibility_score, 2),
                commercial_value=round(commercial_score, 2),
                detailed_analysis=detailed_analysis,
                recommendations=recommendations,
            )

            logger.info(
                f"创意评分完成，总分: {total_score:.2f}，耗时: {processing_time:.2f}秒"
            )
            return response

        except Exception as e:
            logger.error(f"创意评分失败: {str(e)}")
            raise

    async def evaluate_business_value(
        self, request: BusinessEvaluationRequest
    ) -> BusinessEvaluationResponse:
        """
        评估创意的商业价值

        Args:
            request: 商业价值评估请求

        Returns:
            BusinessEvaluationResponse: 商业价值评估响应
        """
        start_time = time.time()
        logger.info("开始商业价值评估")

        try:
            evaluation_prompt = self._build_business_evaluation_prompt(request)

            # 调用AI进行商业分析
            ai_response = await self.ai_manager.generate_code(
                prompt=evaluation_prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-4-turbo",
                temperature=0.3,  # 使用较低温度确保分析客观
                max_tokens=2000,
                system_prompt="你是一个经验丰富的商业分析师，请提供专业、客观的商业价值评估。",
            )

            # 解析AI响应
            business_analysis = self._parse_business_analysis(ai_response.code)

            processing_time = time.time() - start_time

            response = BusinessEvaluationResponse(**business_analysis)

            logger.info(f"商业价值评估完成，耗时: {processing_time:.2f}秒")
            return response

        except Exception as e:
            logger.error(f"商业价值评估失败: {str(e)}")
            raise

    async def _build_creative_prompt(self, request: IdeaGenerationRequest) -> str:
        """构建创意生成Prompt"""
        if request.custom_prompt:
            return request.custom_prompt

        # 使用模板构建Prompt
        base_prompts = {
            IdeaCategory.TECHNOLOGY: "生成一个技术创新想法，要求具有实用性和前瞻性。",
            IdeaCategory.BUSINESS: "提出一个商业模式创新想法，要有明确的盈利路径。",
            IdeaCategory.DESIGN: "设计一个产品创意，注重用户体验和美学价值。",
            IdeaCategory.EDUCATION: "构思一个教育创新方案，能够提升学习效果。",
            IdeaCategory.HEALTHCARE: "提出一个医疗健康领域的创新解决方案。",
            IdeaCategory.ENVIRONMENT: "设计一个环保可持续发展的创新项目。",
            IdeaCategory.ENTERTAINMENT: "创造一个娱乐或文化领域的创新想法。",
            IdeaCategory.OTHER: "生成一个跨领域的综合性创新想法。",
        }

        category_prompt = base_prompts.get(
            request.category, base_prompts[IdeaCategory.OTHER]
        )

        # 添加变量填充
        if request.variables:
            for key, value in request.variables.items():
                category_prompt = category_prompt.replace(f"{{{key}}}", str(value))

        return f"{category_prompt}\n\n请提供详细的创意描述，包括：\n1. 核心概念\n2. 实现方案\n3. 预期效果\n4. 潜在挑战"

    async def _call_dalle_api(
        self, request: ImageGenerationRequest
    ) -> List[Dict[str, str]]:
        """调用DALL-E API生成图像"""
        # 这里应该集成实际的DALL-E 3 API调用
        # 目前返回模拟数据
        mock_images = []
        for i in range(request.n):
            mock_images.append(
                {
                    "url": f"https://example.com/generated-image-{int(time.time())}-{i}.png",
                    "revised_prompt": request.prompt,
                    "style": request.style.value,
                }
            )

        # 模拟API延迟
        await asyncio.sleep(2)

        return mock_images

    async def _calculate_creativity_score(self, idea_content: str) -> float:
        """计算创新性得分"""
        # 使用AI评估创新性
        prompt = f"""
        请评估以下创意的创新性，评分范围0-10分：
        
        创意内容：{idea_content}
        
        评估标准：
        - 原创性 (40%)
        - 突破性 (30%)  
        - 独特性 (30%)
        
        只返回一个0-10之间的数字分数。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            # 解析分数
            score_text = response.code.strip()
            score = float("".join(filter(str.isdigit, score_text)) or "5")
            return max(0, min(10, score))
        except:
            # 如果AI评估失败，返回基础分数
            return 5.0

    async def _calculate_feasibility_score(
        self, idea_content: str, tech_requirements: Optional[str]
    ) -> float:
        """计算可行性得分"""
        # 综合评估技术可行性和实施难度
        prompt = f"""
        请评估以下创意的技术可行性和实施难度，评分范围0-10分：
        
        创意内容：{idea_content}
        技术要求：{tech_requirements or '未提供'}
        
        评估标准：
        - 技术成熟度 (40%)
        - 实施复杂度 (30%)
        - 资源需求 (30%)
        
        只返回一个0-10之间的数字分数。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            score_text = response.code.strip()
            score = float("".join(filter(str.isdigit, score_text)) or "5")
            return max(0, min(10, score))
        except:
            return 5.0

    async def _calculate_commercial_value_score(
        self,
        idea_content: str,
        business_model: Optional[str],
        market_context: Optional[str],
    ) -> float:
        """计算商业价值得分"""
        prompt = f"""
        请评估以下创意的商业价值和市场潜力，评分范围0-10分：
        
        创意内容：{idea_content}
        商业模式：{business_model or '未提供'}
        市场背景：{market_context or '未提供'}
        
        评估标准：
        - 市场需求 (40%)
        - 盈利潜力 (30%)
        - 竞争优势 (30%)
        
        只返回一个0-10之间的数字分数。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            score_text = response.code.strip()
            score = float("".join(filter(str.isdigit, score_text)) or "5")
            return max(0, min(10, score))
        except:
            return 5.0

    async def _generate_detailed_analysis(
        self,
        idea_content: str,
        creativity: float,
        feasibility: float,
        commercial: float,
    ) -> Dict[str, Any]:
        """生成详细分析"""
        prompt = f"""
        对以下创意进行全面分析：
        
        创意内容：{idea_content}
        
        当前评分：
        - 创新性：{creativity}/10
        - 可行性：{feasibility}/10  
        - 商业价值：{commercial}/10
        
        请提供：
        1. 各项评分的具体依据
        2. 创意的优势和亮点
        3. 潜在的风险和挑战
        4. 改进建议
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-4-turbo",
                temperature=0.3,
                max_tokens=1000,
            )

            return {
                "analysis_text": response.code,
                "strengths": self._extract_strengths(response.code),
                "risks": self._extract_risks(response.code),
                "improvement_areas": self._extract_improvements(response.code),
            }
        except:
            return {
                "analysis_text": "分析生成失败",
                "strengths": [],
                "risks": [],
                "improvement_areas": [],
            }

    async def _generate_recommendations(
        self,
        idea_content: str,
        creativity: float,
        feasibility: float,
        commercial: float,
    ) -> List[str]:
        """生成改进建议"""
        prompt = f"""
        基于以下创意的评分，提供3-5条具体的改进建议：
        
        创意内容：{idea_content}
        创新性：{creativity}/10
        可行性：{feasibility}/10
        商业价值：{commercial}/10
        
        建议要求：
        - 具体可行
        - 针对性强
        - 优先级明确
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider=ModelProvider.OPENAI,
                model="gpt-4-turbo",
                temperature=0.4,
                max_tokens=500,
            )

            # 解析建议列表
            suggestions = [
                line.strip("- ").strip()
                for line in response.code.split("\n")
                if line.strip().startswith("-") or line.strip().startswith("•")
            ]
            return suggestions[:5] if suggestions else [response.code.strip()]
        except:
            return [
                "建议进行更详细的市场调研",
                "考虑技术实现的可行性",
                "完善商业模式设计",
            ]

    def _extract_idea_components(self, ai_response: str) -> tuple[str, str]:
        """从AI响应中提取标题和内容"""
        lines = ai_response.strip().split("\n")
        if lines:
            title = lines[0].strip("# ") if lines[0].startswith("#") else "创新想法"
            content = "\n".join(lines[1:] if lines[0].startswith("#") else lines)
            return title, content.strip()
        return "创新想法", ai_response

    def _build_business_evaluation_prompt(
        self, request: BusinessEvaluationRequest
    ) -> str:
        """构建商业评估Prompt"""
        return f"""
        作为商业分析师，请对以下创意进行专业评估：
        
        创意描述：{request.idea_description}
        目标市场：{request.target_market}
        成本估算：{json.dumps(request.estimated_costs, ensure_ascii=False)}
        收入预测：{json.dumps(request.revenue_projections, ensure_ascii=False)}
        竞争分析：{request.competition_analysis}
        
        请提供：
        1. 成本效益比分析
        2. 市场潜力评估
        3. 风险评估
        4. 投资建议
        5. 时间规划
        6. 资源需求
        """

    def _parse_business_analysis(self, ai_response: str) -> Dict[str, Any]:
        """解析商业分析结果"""
        # 简化的解析逻辑，实际应用中需要更复杂的解析
        return {
            "cost_benefit_ratio": 1.5,
            "market_potential": 7.5,
            "risk_assessment": {
                "market_risk": "中等",
                "technical_risk": "较低",
                "financial_risk": "中等",
            },
            "investment_recommendation": "建议谨慎投资，先进行小规模试点",
            "timeline_estimate": "12-18个月",
            "resource_requirements": ["技术团队", "市场推广", "运营资金"],
        }

    def _extract_strengths(self, analysis_text: str) -> List[str]:
        """从分析文本中提取优势"""
        # 简化实现
        return ["具有创新性", "市场需求明确", "技术可行性较高"]

    def _extract_risks(self, analysis_text: str) -> List[str]:
        """从分析文本中提取风险"""
        return ["市场竞争激烈", "技术实现复杂度高", "初期投入较大"]

    def _extract_improvements(self, analysis_text: str) -> List[str]:
        """从分析文本中提取改进点"""
        return ["完善技术方案", "加强市场调研", "优化商业模式"]


# 创建全局实例
creativity_engine = CreativityEngine()
