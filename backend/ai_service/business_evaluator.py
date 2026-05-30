"""
商业价值评估系统
对创意想法进行成本效益分析、市场可行性评估和投资建议
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
import json
import logging
from typing import Any, Dict, List

from ai_service.ai_manager import AIManager
from models.creativity_models import (
    BusinessEvaluationRequest,
    BusinessEvaluationResponse,
)

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级枚举"""

    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"


class InvestmentRecommendation(Enum):
    """投资建议枚举"""

    STRONG_BUY = "强烈推荐投资"
    BUY = "推荐投资"
    HOLD = "建议观望"
    SELL = "不建议投资"


@dataclass
class FinancialMetrics:
    """财务指标"""

    npv: float  # 净现值
    irr: float  # 内部收益率
    payback_period: float  # 投资回收期
    roi: float  # 投资回报率
    break_even_point: int  # 盈亏平衡点


class BusinessEvaluator:
    """商业价值评估器"""

    def __init__(self):
        self.ai_manager = AIManager()
        self._initialize_evaluation_parameters()

    def _initialize_evaluation_parameters(self):
        """初始化评估参数"""
        # 行业基准数据（简化版）
        self.industry_benchmarks = {
            "technology": {
                "avg_roi": 25.0,
                "avg_payback_period": 2.5,
                "market_growth_rate": 15.0,
                "competition_intensity": "高",
            },
            "business": {
                "avg_roi": 18.0,
                "avg_payback_period": 3.0,
                "market_growth_rate": 8.0,
                "competition_intensity": "中等",
            },
            "design": {
                "avg_roi": 20.0,
                "avg_payback_period": 2.0,
                "market_growth_rate": 12.0,
                "competition_intensity": "中等",
            },
            "education": {
                "avg_roi": 15.0,
                "avg_payback_period": 4.0,
                "market_growth_rate": 10.0,
                "competition_intensity": "低",
            },
        }

        # 风险评估权重
        self.risk_weights = {
            "market_risk": 0.3,
            "technical_risk": 0.25,
            "financial_risk": 0.25,
            "operational_risk": 0.2,
        }

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
        logger.info("开始商业价值评估")

        try:
            # 并行执行各项评估
            tasks = [
                self._calculate_cost_benefit_ratio(request),
                self._assess_market_potential(request),
                self._evaluate_risks(request),
                self._generate_investment_recommendation(request),
                self._estimate_timeline(request),
                self._identify_resource_requirements(request),
            ]

            results = await asyncio.gather(*tasks)

            cost_benefit_ratio = results[0]
            market_potential = results[1]
            risk_assessment = results[2]
            investment_recommendation = results[3]
            timeline_estimate = results[4]
            resource_requirements = results[5]

            response = BusinessEvaluationResponse(
                cost_benefit_ratio=cost_benefit_ratio,
                market_potential=market_potential,
                risk_assessment=risk_assessment,
                investment_recommendation=investment_recommendation,
                timeline_estimate=timeline_estimate,
                resource_requirements=resource_requirements,
            )

            logger.info("商业价值评估完成")
            return response

        except Exception as e:
            logger.error(f"商业价值评估失败: {str(e)}")
            raise

    async def _calculate_cost_benefit_ratio(
        self, request: BusinessEvaluationRequest
    ) -> float:
        """计算成本效益比"""
        try:
            # 计算总成本
            total_costs = sum(request.estimated_costs.values())

            # 计算总收益（3年预测）
            total_revenue = sum(request.revenue_projections.values())

            if total_costs == 0:
                return 0.0

            cost_benefit_ratio = total_revenue / total_costs

            # AI辅助分析
            ai_analysis = await self._ai_analyze_cost_benefit(
                request.estimated_costs, request.revenue_projections, cost_benefit_ratio
            )

            # 结合AI分析调整比率
            adjusted_ratio = cost_benefit_ratio * ai_analysis.get(
                "adjustment_factor", 1.0
            )

            return round(adjusted_ratio, 2)

        except Exception as e:
            logger.warning(f"成本效益计算失败: {str(e)}")
            return 1.0  # 默认1:1比率

    async def _assess_market_potential(
        self, request: BusinessEvaluationRequest
    ) -> float:
        """评估市场潜力"""
        try:
            # 基于目标市场和竞争分析
            market_size_score = self._analyze_market_size(request.target_market)
            growth_rate_score = self._analyze_growth_rate(request.target_market)
            competitive_position_score = self._analyze_competition(
                request.competition_analysis
            )

            # 加权计算市场潜力得分
            market_potential = (
                0.4 * market_size_score
                + 0.3 * growth_rate_score
                + 0.3 * competitive_position_score
            )

            # AI辅助评估
            ai_score = await self._ai_assess_market_potential(
                request.idea_description,
                request.target_market,
                request.competition_analysis,
            )

            # 综合得分
            final_score = 0.7 * market_potential + 0.3 * ai_score
            return round(final_score, 1)

        except Exception as e:
            logger.warning(f"市场潜力评估失败: {str(e)}")
            return 5.0

    async def _evaluate_risks(
        self, request: BusinessEvaluationRequest
    ) -> Dict[str, Any]:
        """评估各类风险"""
        try:
            # 市场风险
            market_risk = await self._assess_market_risk(
                request.target_market, request.competition_analysis
            )

            # 技术风险
            technical_risk = await self._assess_technical_risk(request.idea_description)

            # 财务风险
            financial_risk = await self._assess_financial_risk(
                request.estimated_costs, request.revenue_projections
            )

            # 运营风险
            operational_risk = await self._assess_operational_risk(
                request.idea_description
            )

            # 计算总体风险等级
            overall_risk_score = (
                self.risk_weights["market_risk"]
                * self._risk_level_to_score(market_risk)
                + self.risk_weights["technical_risk"]
                * self._risk_level_to_score(technical_risk)
                + self.risk_weights["financial_risk"]
                * self._risk_level_to_score(financial_risk)
                + self.risk_weights["operational_risk"]
                * self._risk_level_to_score(operational_risk)
            )

            overall_risk_level = self._score_to_risk_level(overall_risk_score)

            return {
                "overall_risk": overall_risk_level.value,
                "market_risk": market_risk.value,
                "technical_risk": technical_risk.value,
                "financial_risk": financial_risk.value,
                "operational_risk": operational_risk.value,
                "risk_factors": await self._identify_risk_factors(request),
            }

        except Exception as e:
            logger.warning(f"风险评估失败: {str(e)}")
            return {
                "overall_risk": RiskLevel.MEDIUM.value,
                "market_risk": RiskLevel.MEDIUM.value,
                "technical_risk": RiskLevel.MEDIUM.value,
                "financial_risk": RiskLevel.MEDIUM.value,
                "operational_risk": RiskLevel.MEDIUM.value,
                "risk_factors": ["评估过程中出现异常"],
            }

    async def _generate_investment_recommendation(
        self, request: BusinessEvaluationRequest
    ) -> str:
        """生成投资建议"""
        try:
            # 收集评估指标
            cost_benefit = await self._calculate_cost_benefit_ratio(request)
            market_potential = await self._assess_market_potential(request)

            risk_assessment = await self._evaluate_risks(request)
            overall_risk = risk_assessment["overall_risk"]

            # 基于规则的推荐逻辑
            recommendation = self._rule_based_recommendation(
                cost_benefit, market_potential, overall_risk
            )

            # AI辅助优化
            ai_recommendation = await self._ai_optimize_recommendation(
                request, cost_benefit, market_potential, overall_risk, recommendation
            )

            return ai_recommendation

        except Exception as e:
            logger.warning(f"投资建议生成失败: {str(e)}")
            return InvestmentRecommendation.HOLD.value

    async def _estimate_timeline(self, request: BusinessEvaluationRequest) -> str:
        """估算项目时间线"""
        try:
            # AI分析项目复杂度和时间需求
            timeline_analysis = await self._ai_analyze_timeline(
                request.idea_description, request.estimated_costs
            )

            return timeline_analysis.get("timeline_estimate", "12-18个月")

        except Exception as e:
            logger.warning(f"时间线估算失败: {str(e)}")
            return "12-18个月"

    async def _identify_resource_requirements(
        self, request: BusinessEvaluationRequest
    ) -> List[str]:
        """识别资源需求"""
        try:
            # AI分析资源需求
            resource_analysis = await self._ai_analyze_resources(
                request.idea_description, request.estimated_costs
            )

            return resource_analysis.get(
                "resources", ["技术团队", "市场推广资金", "运营管理"]
            )

        except Exception as e:
            logger.warning(f"资源需求识别失败: {str(e)}")
            return ["技术开发", "市场运营", "资金投入"]

    def _analyze_market_size(self, target_market: str) -> float:
        """分析市场规模"""
        market_keywords = {
            "巨大": 9.0,
            "大规模": 8.5,
            "庞大": 8.0,
            "较大": 7.0,
            "中等": 6.0,
            "一般": 5.0,
            "较小": 4.0,
            "有限": 3.0,
            "狭窄": 2.0,
        }

        target_market_lower = target_market.lower()
        for keyword, score in market_keywords.items():
            if keyword in target_market_lower:
                return score
        return 5.0

    def _analyze_growth_rate(self, target_market: str) -> float:
        """分析增长率"""
        growth_keywords = {
            "高速增长": 9.0,
            "快速增长": 8.5,
            "稳步增长": 7.5,
            "稳定增长": 7.0,
            "缓慢增长": 5.0,
            "停滞": 3.0,
            "下降": 2.0,
        }

        target_market_lower = target_market.lower()
        for keyword, score in growth_keywords.items():
            if keyword in target_market_lower:
                return score
        return 6.0

    def _analyze_competition(self, competition_analysis: str) -> float:
        """分析竞争态势"""
        competition_keywords = {
            "垄断": 9.0,
            "寡头": 8.0,
            "竞争较少": 7.5,
            "适度竞争": 6.5,
            "竞争激烈": 4.5,
            "红海": 3.0,
            "完全竞争": 2.0,
        }

        analysis_lower = competition_analysis.lower()
        for keyword, score in competition_keywords.items():
            if keyword in analysis_lower:
                return score
        return 5.0

    async def _assess_market_risk(
        self, target_market: str, competition: str
    ) -> RiskLevel:
        """评估市场风险"""
        market_score = self._analyze_market_size(target_market)
        competition_score = self._analyze_competition(competition)

        combined_score = (market_score + competition_score) / 2

        if combined_score >= 7.5:
            return RiskLevel.LOW
        elif combined_score >= 5.5:
            return RiskLevel.MEDIUM
        elif combined_score >= 3.5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    async def _assess_technical_risk(self, idea_description: str) -> RiskLevel:
        """评估技术风险"""
        tech_keywords = {
            "成熟技术": RiskLevel.LOW,
            "现有技术": RiskLevel.LOW,
            "需要研发": RiskLevel.MEDIUM,
            "技术不成熟": RiskLevel.HIGH,
            "前沿技术": RiskLevel.HIGH,
        }

        description_lower = idea_description.lower()
        for keyword, risk_level in tech_keywords.items():
            if keyword in description_lower:
                return risk_level

        return RiskLevel.MEDIUM

    async def _assess_financial_risk(
        self, costs: Dict[str, float], revenues: Dict[str, float]
    ) -> RiskLevel:
        """评估财务风险"""
        total_costs = sum(costs.values())
        total_revenues = sum(revenues.values())

        if total_costs == 0:
            return RiskLevel.HIGH

        cost_revenue_ratio = total_revenues / total_costs

        if cost_revenue_ratio >= 3.0:
            return RiskLevel.LOW
        elif cost_revenue_ratio >= 1.5:
            return RiskLevel.MEDIUM
        elif cost_revenue_ratio >= 1.0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    async def _assess_operational_risk(self, idea_description: str) -> RiskLevel:
        """评估运营风险"""
        # 简化评估逻辑
        if "复杂" in idea_description.lower() or "多环节" in idea_description.lower():
            return RiskLevel.HIGH
        elif "简单" in idea_description.lower() or "直接" in idea_description.lower():
            return RiskLevel.LOW
        else:
            return RiskLevel.MEDIUM

    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """风险等级转分数"""
        risk_scores = {
            RiskLevel.LOW: 2.0,
            RiskLevel.MEDIUM: 5.0,
            RiskLevel.HIGH: 8.0,
            RiskLevel.VERY_HIGH: 9.5,
        }
        return risk_scores.get(risk_level, 5.0)

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """分数转风险等级"""
        if score <= 3.0:
            return RiskLevel.LOW
        elif score <= 6.0:
            return RiskLevel.MEDIUM
        elif score <= 8.0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    async def _identify_risk_factors(
        self, request: BusinessEvaluationRequest
    ) -> List[str]:
        """识别具体风险因素"""
        prompt = f"""
        基于以下项目信息，识别3-5个主要风险因素：
        
        创意描述：{request.idea_description}
        目标市场：{request.target_market}
        成本估算：{json.dumps(request.estimated_costs, ensure_ascii=False)}
        竞争分析：{request.competition_analysis}
        
        每个风险因素请简明扼要地描述。
        """

        try:
            response = await self.ai_manager.generate_code(
                prompt=prompt,
                provider="openai",
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=500,
            )

            risk_factors = [
                line.strip("- •").strip()
                for line in response.code.split("\n")
                if line.strip().startswith(("-", "•"))
            ]
            return (
                risk_factors[:5]
                if risk_factors
                else ["市场接受度不确定", "技术实现风险"]
            )
        except:
            return ["市场风险", "技术风险", "财务风险"]

    def _rule_based_recommendation(
        self, cost_benefit: float, market_potential: float, overall_risk: str
    ) -> str:
        """基于规则的投资建议"""
        # 简化的决策树逻辑
        if (
            cost_benefit >= 2.0
            and market_potential >= 7.0
            and overall_risk == RiskLevel.LOW.value
        ):
            return InvestmentRecommendation.STRONG_BUY.value
        elif (
            cost_benefit >= 1.5
            and market_potential >= 6.0
            and overall_risk in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value]
        ):
            return InvestmentRecommendation.BUY.value
        elif cost_benefit >= 1.0 and market_potential >= 5.0:
            return InvestmentRecommendation.HOLD.value
        else:
            return InvestmentRecommendation.SELL.value

    # AI辅助分析方法（简化实现）
    async def _ai_analyze_cost_benefit(
        self, costs: Dict[str, float], revenues: Dict[str, float], ratio: float
    ) -> Dict[str, Any]:
        return {"adjustment_factor": 1.0}

    async def _ai_assess_market_potential(
        self, idea: str, market: str, competition: str
    ) -> float:
        return 6.5

    async def _ai_optimize_recommendation(
        self,
        request: BusinessEvaluationRequest,
        cb: float,
        mp: float,
        risk: str,
        rec: str,
    ) -> str:
        return rec

    async def _ai_analyze_timeline(
        self, idea: str, costs: Dict[str, float]
    ) -> Dict[str, str]:
        return {"timeline_estimate": "12-18个月"}

    async def _ai_analyze_resources(
        self, idea: str, costs: Dict[str, float]
    ) -> Dict[str, Any]:
        return {"resources": ["技术团队", "市场推广", "运营管理"]}


# 创建全局实例
business_evaluator = BusinessEvaluator()
