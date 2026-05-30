"""
创意想法多维度评分系统
实现创新性、可行性和商业价值的量化评估
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional

from ai_service.ai_manager import AIManager
from models.creativity_models import IdeaScoreRequest, IdeaScoreResponse

logger = logging.getLogger(__name__)


class ScoreDimension(Enum):
    """评分维度枚举"""

    CREATIVITY = "creativity"
    FEASIBILITY = "feasibility"
    COMMERCIAL_VALUE = "commercial_value"


@dataclass
class ScoringCriteria:
    """评分标准"""

    weight: float
    min_threshold: float
    max_threshold: float
    evaluation_factors: List[str]


class IdeaScorer:
    """创意想法评分器"""

    def __init__(self):
        self.ai_manager = AIManager()
        self._initialize_scoring_criteria()
        self._initialize_keyword_dictionaries()

    def _initialize_scoring_criteria(self):
        """初始化评分标准"""
        self.criteria = {
            ScoreDimension.CREATIVITY: ScoringCriteria(
                weight=0.4,
                min_threshold=0.0,
                max_threshold=10.0,
                evaluation_factors=[
                    "originality",  # 原创性
                    "novelty",  # 新颖性
                    "uniqueness",  # 独特性
                    "breakthrough",  # 突破性
                    "innovation",  # 创新程度
                ],
            ),
            ScoreDimension.FEASIBILITY: ScoringCriteria(
                weight=0.3,
                min_threshold=0.0,
                max_threshold=10.0,
                evaluation_factors=[
                    "technical_complexity",  # 技术复杂度
                    "implementation_cost",  # 实施成本
                    "resource_requirements",  # 资源需求
                    "timeline",  # 时间要求
                    "risk_level",  # 风险等级
                ],
            ),
            ScoreDimension.COMMERCIAL_VALUE: ScoringCriteria(
                weight=0.3,
                min_threshold=0.0,
                max_threshold=10.0,
                evaluation_factors=[
                    "market_demand",  # 市场需求
                    "profit_potential",  # 盈利潜力
                    "competitive_advantage",  # 竞争优势
                    "scalability",  # 可扩展性
                    "roi_projection",  # ROI预期
                ],
            ),
        }

    def _initialize_keyword_dictionaries(self):
        """初始化关键词词典"""
        self.keyword_dictionaries = {
            "creativity_indicators": {
                "high": [
                    "革命性",
                    "突破性",
                    "颠覆性",
                    "创新性",
                    "独特",
                    "原创",
                    "新颖",
                    "前所未有",
                    "开创性",
                    "变革性",
                    "前瞻性",
                    "先锋性",
                ],
                "medium": ["改进", "优化", "升级", "增强", "改良", "完善", "提升"],
                "low": ["复制", "模仿", "跟随", "传统", "常规", "普通", "一般"],
            },
            "feasibility_indicators": {
                "high": [
                    "成熟技术",
                    "现成方案",
                    "标准化",
                    "易实现",
                    "低成本",
                    "快速部署",
                    "资源充足",
                    "风险可控",
                ],
                "medium": [
                    "需要研发",
                    "适度投入",
                    "中等复杂度",
                    "合理周期",
                    "可控风险",
                    "分阶段实施",
                ],
                "low": [
                    "技术不成熟",
                    "高风险",
                    "巨额投入",
                    "长期研发",
                    "资源不足",
                    "不确定性高",
                    "实施困难",
                ],
            },
            "commercial_indicators": {
                "high": [
                    "巨大市场",
                    "强烈需求",
                    "高额利润",
                    "竞争优势明显",
                    "快速增长",
                    "可规模化",
                    "变现能力强",
                ],
                "medium": [
                    "有一定市场",
                    "稳定收益",
                    "适度竞争",
                    "合理回报",
                    "增长潜力",
                    "商业模式清晰",
                ],
                "low": [
                    "市场狭小",
                    "需求不明确",
                    "竞争激烈",
                    "盈利困难",
                    "增长缓慢",
                    "商业模式模糊",
                ],
            },
        }

    async def score_idea(self, request: IdeaScoreRequest) -> IdeaScoreResponse:
        """
        对创意想法进行多维度评分

        Args:
            request: 创意评分请求

        Returns:
            IdeaScoreResponse: 评分结果响应
        """
        logger.info("开始多维度创意评分")

        try:
            # 并行计算各维度得分
            dimension_scores = await self._calculate_dimension_scores(request)

            # 计算综合得分
            total_score = self._calculate_weighted_score(
                dimension_scores, request.scoring_criteria
            )

            # 生成详细分析
            detailed_analysis = await self._generate_detailed_analysis(
                request.idea_content, dimension_scores
            )

            # 生成改进建议
            recommendations = await self._generate_recommendations(
                dimension_scores, request.idea_content
            )

            response = IdeaScoreResponse(
                total_score=round(total_score, 2),
                creativity=round(dimension_scores[ScoreDimension.CREATIVITY], 2),
                feasibility=round(dimension_scores[ScoreDimension.FEASIBILITY], 2),
                commercial_value=round(
                    dimension_scores[ScoreDimension.COMMERCIAL_VALUE], 2
                ),
                detailed_analysis=detailed_analysis,
                recommendations=recommendations,
            )

            logger.info(f"评分完成 - 总分: {total_score:.2f}")
            return response

        except Exception as e:
            logger.error(f"创意评分失败: {str(e)}")
            raise

    async def _calculate_dimension_scores(
        self, request: IdeaScoreRequest
    ) -> Dict[ScoreDimension, float]:
        """计算各维度得分"""
        tasks = [
            self._assess_creativity(request.idea_content),
            self._assess_feasibility(
                request.idea_content, request.technical_requirements
            ),
            self._assess_commercial_value(
                request.idea_content, request.business_model, request.market_context
            ),
        ]

        creativity_score, feasibility_score, commercial_score = await asyncio.gather(
            *tasks
        )

        return {
            ScoreDimension.CREATIVITY: creativity_score,
            ScoreDimension.FEASIBILITY: feasibility_score,
            ScoreDimension.COMMERCIAL_VALUE: commercial_score,
        }

    async def _assess_creativity(self, idea_content: str) -> float:
        """评估创新性得分"""
        # 1. 关键词分析
        keyword_score = self._analyze_keywords(idea_content, "creativity_indicators")

        # 2. 语言特征分析
        linguistic_score = self._analyze_linguistic_features(idea_content)

        # 3. AI智能评估
        ai_score = await self._ai_evaluate_creativity(idea_content)

        # 综合得分（加权平均）
        final_score = 0.3 * keyword_score + 0.2 * linguistic_score + 0.5 * ai_score
        return max(0, min(10, final_score))

    async def _assess_feasibility(
        self, idea_content: str, tech_requirements: Optional[str]
    ) -> float:
        """评估可行性得分"""
        # 1. 技术关键词分析
        tech_keyword_score = self._analyze_keywords(
            idea_content, "feasibility_indicators"
        )

        # 2. 复杂度分析
        complexity_score = self._analyze_technical_complexity(
            idea_content, tech_requirements
        )

        # 3. AI可行性评估
        ai_score = await self._ai_evaluate_feasibility(idea_content, tech_requirements)

        # 综合得分
        final_score = 0.4 * tech_keyword_score + 0.3 * complexity_score + 0.3 * ai_score
        return max(0, min(10, final_score))

    async def _assess_commercial_value(
        self,
        idea_content: str,
        business_model: Optional[str],
        market_context: Optional[str],
    ) -> float:
        """评估商业价值得分"""
        # 1. 商业关键词分析
        commercial_keyword_score = self._analyze_keywords(
            idea_content, "commercial_indicators"
        )

        # 2. 市场潜力分析
        market_score = self._analyze_market_potential(idea_content, market_context)

        # 3. AI商业价值评估
        ai_score = await self._ai_evaluate_commercial_value(
            idea_content, business_model, market_context
        )

        # 综合得分
        final_score = (
            0.4 * commercial_keyword_score + 0.3 * market_score + 0.3 * ai_score
        )
        return max(0, min(10, final_score))

    def _analyze_keywords(self, content: str, indicator_type: str) -> float:
        """基于关键词的评分分析"""
        content_lower = content.lower()
        indicators = self.keyword_dictionaries[indicator_type]

        high_matches = sum(
            content_lower.count(keyword) for keyword in indicators["high"]
        )
        medium_matches = sum(
            content_lower.count(keyword) for keyword in indicators["medium"]
        )
        low_matches = sum(content_lower.count(keyword) for keyword in indicators["low"])

        total_matches = high_matches + medium_matches + low_matches

        if total_matches == 0:
            return 5.0  # 默认中等分数

        # 计算加权得分
        weighted_score = (
            high_matches * 9.0  # 高级别关键词得9分
            + medium_matches * 6.0  # 中级别关键词得6分
            + low_matches * 3.0  # 低级别关键词得3分
        ) / total_matches

        return weighted_score

    def _analyze_linguistic_features(self, content: str) -> float:
        """分析语言特征评估创新性"""
        # 词汇丰富度
        words = re.findall(r"\b\w+\b", content.lower())
        unique_words = len(set(words))
        vocabulary_richness = min(10, unique_words / max(len(words), 1) * 20)

        # 句子复杂度
        sentences = re.split(r"[.!?]+", content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        sentence_complexity = min(10, avg_sentence_length / 2)

        # 创新词汇密度
        innovation_words = ["创新", "新", "首创", "独创", "突破", "革命", "变革"]
        innovation_density = (
            sum(content.count(word) for word in innovation_words) / len(words) * 100
        )
        innovation_score = min(10, innovation_density * 0.5)

        return (vocabulary_richness + sentence_complexity + innovation_score) / 3

    def _analyze_technical_complexity(
        self, content: str, tech_requirements: Optional[str]
    ) -> float:
        """分析技术复杂度"""
        complexity_indicators = [
            "复杂",
            "高级",
            "专业",
            "精密",
            "高端",
            "先进",
            "需要大量",
            "高度依赖",
            "专业技术",
            "深度集成",
        ]

        simplicity_indicators = [
            "简单",
            "基础",
            "通用",
            "标准",
            "现成",
            "容易",
            "无需特殊",
            "基本技能",
            "快速上手",
            "门槛低",
        ]

        content_lower = content.lower()
        if tech_requirements:
            content_lower += " " + tech_requirements.lower()

        complex_matches = sum(
            content_lower.count(indicator) for indicator in complexity_indicators
        )
        simple_matches = sum(
            content_lower.count(indicator) for indicator in simplicity_indicators
        )

        total_indicators = complex_matches + simple_matches

        if total_indicators == 0:
            return 7.0  # 默认较可行

        # 复杂度越高，可行性越低
        complexity_ratio = complex_matches / total_indicators
        feasibility_score = 10 - (complexity_ratio * 7)  # 映射到0-10分

        return max(0, min(10, feasibility_score))

    def _analyze_market_potential(
        self, content: str, market_context: Optional[str]
    ) -> float:
        """分析市场潜力"""
        market_indicators = [
            "大规模",
            "广泛",
            "巨大",
            "庞大",
            "全球",
            "全国",
            "数十亿",
            "数百万",
            "高速增长",
            "爆发式",
            "刚需",
        ]

        niche_indicators = [
            "小众",
            "特定",
            "垂直",
            "细分",
            "专业化",
            "定制化",
            "有限",
            "局部",
            "少数",
            "特定人群",
        ]

        content_lower = content.lower()
        if market_context:
            content_lower += " " + market_context.lower()

        mass_market_matches = sum(
            content_lower.count(indicator) for indicator in market_indicators
        )
        niche_matches = sum(
            content_lower.count(indicator) for indicator in niche_indicators
        )

        total_indicators = mass_market_matches + niche_matches

        if total_indicators == 0:
            return 6.0  # 默认中等市场潜力

        # 大众市场得分更高
        mass_market_ratio = mass_market_matches / total_indicators
        market_score = 5 + (mass_market_ratio * 5)  # 5-10分范围

        return market_score

    async def _ai_evaluate_creativity(self, idea_content: str) -> float:
        """使用AI评估创新性"""
        prompt = f"""
        作为一个创新评估专家，请评估以下创意的创新性，给出0-10分的评分：
        
        创意内容：{idea_content}
        
        评估要点：
        - 解决方案的独特性和原创性
        - 与现有方案的差异化程度
        - 技术或方法上的创新点
        - 对行业或领域的潜在影响
        
        只返回一个数字分数，精确到小数点后一位。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            # 提取分数
            score_match = re.search(r"(\d+(?:\.\d+)?)", response.code)
            if score_match:
                return float(score_match.group(1))
            return 5.0
        except:
            return 5.0  # AI评估失败时返回默认分数

    async def _ai_evaluate_feasibility(
        self, idea_content: str, tech_requirements: Optional[str]
    ) -> float:
        """使用AI评估可行性"""
        prompt = f"""
        作为一个技术评估专家，请评估以下创意的技术可行性，给出0-10分的评分：
        
        创意内容：{idea_content}
        技术要求：{tech_requirements or '未明确说明'}
        
        评估要点：
        - 技术实现的现实可能性
        - 所需资源和成本的合理性
        - 实施周期的可行性
        - 技术风险的可控性
        
        只返回一个数字分数，精确到小数点后一位。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            score_match = re.search(r"(\d+(?:\.\d+)?)", response.code)
            if score_match:
                return float(score_match.group(1))
            return 5.0
        except:
            return 5.0

    async def _ai_evaluate_commercial_value(
        self,
        idea_content: str,
        business_model: Optional[str],
        market_context: Optional[str],
    ) -> float:
        """使用AI评估商业价值"""
        prompt = f"""
        作为一个商业分析师，请评估以下创意的商业价值，给出0-10分的评分：
        
        创意内容：{idea_content}
        商业模式：{business_model or '未明确说明'}
        市场背景：{market_context or '未明确说明'}
        
        评估要点：
        - 市场需求的迫切程度
        - 盈利模式的清晰度和可持续性
        - 竞争优势和进入壁垒
        - 规模化和增长潜力
        
        只返回一个数字分数，精确到小数点后一位。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100,
            )

            score_match = re.search(r"(\d+(?:\.\d+)?)", response.code)
            if score_match:
                return float(score_match.group(1))
            return 5.0
        except:
            return 5.0

    def _calculate_weighted_score(
        self,
        dimension_scores: Dict[ScoreDimension, float],
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """计算加权综合得分"""
        if custom_weights:
            weights = {
                ScoreDimension.CREATIVITY: custom_weights.get("creativity", 0.4),
                ScoreDimension.FEASIBILITY: custom_weights.get("feasibility", 0.3),
                ScoreDimension.COMMERCIAL_VALUE: custom_weights.get(
                    "commercial_value", 0.3
                ),
            }
        else:
            weights = {dim: criteria.weight for dim, criteria in self.criteria.items()}

        total_score = sum(
            dimension_scores[dim] * weights[dim] for dim in ScoreDimension
        )

        return total_score

    async def _generate_detailed_analysis(
        self, idea_content: str, dimension_scores: Dict[ScoreDimension, float]
    ) -> Dict[str, Any]:
        """生成详细分析报告"""
        analysis_prompt = f"""
        对以下创意进行全面分析：
        
        创意内容：{idea_content}
        
        各项评分：
        - 创新性：{dimension_scores[ScoreDimension.CREATIVITY]:.1f}/10
        - 可行性：{dimension_scores[ScoreDimension.FEASIBILITY]:.1f}/10
        - 商业价值：{dimension_scores[ScoreDimension.COMMERCIAL_VALUE]:.1f}/10
        
        请提供：
        1. 各项评分的具体依据和分析
        2. 创意的核心优势和亮点
        3. 潜在的风险和挑战
        4. 改进和优化建议
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=analysis_prompt,
                provider="openai",
                model="gpt-4-turbo",
                temperature=0.3,
                max_tokens=1500,
            )

            return {
                "analysis_summary": response.code,
                "strengths": self._extract_analysis_points(response.code, "优势"),
                "weaknesses": self._extract_analysis_points(response.code, "风险"),
                "opportunities": self._extract_analysis_points(response.code, "机会"),
            }
        except:
            return {
                "analysis_summary": "AI分析生成失败",
                "strengths": ["内容完整", "逻辑清晰"],
                "weaknesses": ["缺乏具体数据支撑", "实施细节不够明确"],
                "opportunities": ["进一步市场调研", "技术方案细化"],
            }

    async def _generate_recommendations(
        self, dimension_scores: Dict[ScoreDimension, float], idea_content: str
    ) -> List[str]:
        """生成针对性建议"""
        weak_dimensions = [
            dim
            for dim, score in dimension_scores.items()
            if score < 6.0  # 低于6分认为需要改进
        ]

        if not weak_dimensions:
            return ["整体表现优秀，建议推进实施", "保持现有优势，关注市场反馈"]

        recommendation_prompt = f"""
        基于以下创意的评分结果，为较低分的维度提供改进建议：
        
        创意内容：{idea_content}
        评分情况：{', '.join([f'{dim.value}:{score:.1f}' for dim, score in dimension_scores.items()])}
        
        需要重点关注的维度：{[dim.value for dim in weak_dimensions]}
        
        请提供3-5条具体、可操作的改进建议。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=recommendation_prompt,
                provider="openai",
                model="gpt-4-turbo",
                temperature=0.4,
                max_tokens=800,
            )

            # 解析建议列表
            suggestions = [
                line.strip("- •").strip()
                for line in response.code.split("\n")
                if line.strip().startswith(("-", "•"))
            ]
            return suggestions[:5] if suggestions else [response.code.strip()]
        except:
            # 默认建议
            default_suggestions = []
            if ScoreDimension.CREATIVITY in weak_dimensions:
                default_suggestions.extend(
                    [
                        "深入研究相关领域的最新发展趋势",
                        "借鉴跨行业的成功案例和创新思路",
                        "增加用户调研，从实际需求出发思考创新点",
                    ]
                )
            if ScoreDimension.FEASIBILITY in weak_dimensions:
                default_suggestions.extend(
                    [
                        "细化技术实施方案和里程碑规划",
                        "评估所需资源和预算的合理性",
                        "考虑分阶段实施降低风险",
                    ]
                )
            if ScoreDimension.COMMERCIAL_VALUE in weak_dimensions:
                default_suggestions.extend(
                    [
                        "开展详细的市场调研和竞品分析",
                        "完善商业模式和盈利路径设计",
                        "制定清晰的用户获取和留存策略",
                    ]
                )

            return default_suggestions[:5]

    def _extract_analysis_points(self, text: str, category: str) -> List[str]:
        """从分析文本中提取特定类别的要点"""
        # 简化的提取逻辑
        patterns = {
            "优势": [r"优势[:：]?\s*(.+?)(?=\n|$)", r"亮点[:：]?\s*(.+?)(?=\n|$)"],
            "风险": [r"风险[:：]?\s*(.+?)(?=\n|$)", r"挑战[:：]?\s*(.+?)(?=\n|$)"],
            "机会": [r"机会[:：]?\s*(.+?)(?=\n|$)", r"建议[:：]?\s*(.+?)(?=\n|$)"],
        }

        points = []
        for pattern in patterns.get(category, []):
            matches = re.findall(pattern, text, re.MULTILINE)
            points.extend(matches)

        return points[:3] if points else [f"暂无明确的{category}分析"]


# 创建全局实例
idea_scorer = IdeaScorer()
