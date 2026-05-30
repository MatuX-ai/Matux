"""
动态课程生成回测验证框架
用于验证AI生成课程与手工课程的效果对比
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dynamic_course import BacktestResult, GeneratedCourse

logger = logging.getLogger(__name__)


@dataclass
class CourseComparison:
    """课程对比数据"""

    course_id: int
    course_type: str  # "generated" 或 "manual"
    completion_rate: float
    student_count: int
    average_score: Optional[float]
    engagement_metrics: Dict[str, Any]


class BacktestManager:
    """回测管理器"""

    def __init__(self):
        """初始化回测管理器"""
        self.significance_level = 0.05  # 显著性水平
        self.minimum_sample_size = 30  # 最小样本量
        self.target_completion_rate = 85.0  # 目标完成率(%)

        logger.info("回测管理器初始化完成")

    async def compare_completion_rates(
        self,
        db: AsyncSession,
        test_period: str = "30d",
        subject_area: Optional[str] = None,
    ) -> BacktestResult:
        """
        对比生成课程与手工课程的完成率

        Args:
            db: 数据库会话
            test_period: 测试周期 (如: "7d", "30d")
            subject_area: 学科领域筛选

        Returns:
            BacktestResult: 回测结果
        """
        try:
            # 计算时间范围
            days = int(test_period.replace("d", ""))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 获取生成课程数据
            generated_stats = await self._get_course_statistics(
                db, "generated", start_date, end_date, subject_area
            )

            # 获取手工课程数据（这里需要根据实际情况调整）
            manual_stats = await self._get_manual_course_statistics(
                db, start_date, end_date, subject_area
            )

            # 计算改进百分比
            if manual_stats.completion_rate > 0:
                improvement = (
                    (generated_stats.completion_rate - manual_stats.completion_rate)
                    / manual_stats.completion_rate
                    * 100
                )
            else:
                improvement = 0.0

            # 统计显著性检验
            statistical_significance = await self._perform_statistical_test(
                generated_stats.completion_rates, manual_stats.completion_rates
            )

            # 构造回测结果
            result = BacktestResult(
                test_name=f"动态课程生成效果测试_{test_period}",
                generated_courses_count=generated_stats.course_count,
                manual_courses_count=manual_stats.course_count,
                generated_completion_rate=generated_stats.completion_rate,
                manual_completion_rate=manual_stats.completion_rate,
                improvement_percentage=improvement,
                statistical_significance=statistical_significance,
                test_period=test_period,
                created_at=datetime.utcnow(),
            )

            logger.info(
                f"回测完成: 生成课程{generated_stats.course_count}个, "
                f"手工课程{manual_stats.course_count}个, "
                f"改进{improvement:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(f"回测对比失败: {str(e)}")
            raise

    async def _get_course_statistics(
        self,
        db: AsyncSession,
        course_type: str,
        start_date: datetime,
        end_date: datetime,
        subject_area: Optional[str] = None,
    ) -> "CourseStatistics":
        """获取课程统计数据"""
        try:
            # 构建查询条件
            conditions = [
                GeneratedCourse.created_at >= start_date,
                GeneratedCourse.created_at <= end_date,
            ]

            if subject_area:
                conditions.append(GeneratedCourse.subject_area == subject_area)

            # 获取符合条件的课程
            query = select(GeneratedCourse).where(and_(*conditions))
            result = await db.execute(query)
            courses = result.scalars().all()

            if not courses:
                return CourseStatistics(
                    course_count=0,
                    completion_rate=0.0,
                    completion_rates=[],
                    average_score=0.0,
                    total_students=0,
                )

            # 计算统计数据
            completion_rates = [
                course.completion_rate
                for course in courses
                if course.completion_rate is not None
            ]
            np.mean(completion_rates) if completion_rates else 0.0

            total_students = sum(course.current_students or 0 for course in courses)
            total_completions = sum(
                int(
                    (course.completion_rate or 0) * (course.current_students or 0) / 100
                )
                for course in courses
            )

            overall_completion_rate = (
                (total_completions / total_students * 100)
                if total_students > 0
                else 0.0
            )

            return CourseStatistics(
                course_count=len(courses),
                completion_rate=overall_completion_rate,
                completion_rates=completion_rates,
                average_score=np.mean(
                    [course.average_score or 0 for course in courses]
                ),
                total_students=total_students,
            )

        except Exception as e:
            logger.error(f"获取课程统计数据失败: {str(e)}")
            raise

    async def _get_manual_course_statistics(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        subject_area: Optional[str] = None,
    ) -> "CourseStatistics":
        """
        获取手工课程统计数据
        注意：这需要根据实际的手工课程数据结构调整
        """
        # 这里应该查询传统手工创建的课程数据
        # 目前返回模拟数据用于演示
        return CourseStatistics(
            course_count=120,
            completion_rate=72.3,
            completion_rates=[70.0, 75.0, 68.0, 73.0, 71.0] * 24,  # 模拟120个数据点
            average_score=82.5,
            total_students=1200,
        )

    async def _perform_statistical_test(
        self, generated_rates: List[float], manual_rates: List[float]
    ) -> bool:
        """
        执行统计显著性检验

        Args:
            generated_rates: 生成课程完成率列表
            manual_rates: 手工课程完成率列表

        Returns:
            bool: 是否具有统计显著性
        """
        try:
            if (
                len(generated_rates) < self.minimum_sample_size
                or len(manual_rates) < self.minimum_sample_size
            ):
                logger.warning("样本量不足，无法进行统计检验")
                return False

            # 使用双样本t检验
            t_statistic, p_value = stats.ttest_ind(
                generated_rates, manual_rates, equal_var=False
            )

            # 判断是否显著
            is_significant = p_value < self.significance_level

            logger.info(
                f"统计检验结果: t={t_statistic:.4f}, p={p_value:.4f}, "
                f"显著性={is_significant}"
            )

            return is_significant

        except Exception as e:
            logger.error(f"统计检验失败: {str(e)}")
            return False

    async def test_prompt_templates(
        self, db: AsyncSession, test_period: str = "30d"
    ) -> List[Dict[str, Any]]:
        """
        测试不同提示词模板的质量

        Args:
            db: 数据库会话
            test_period: 测试周期

        Returns:
            List[Dict]: 模板测试结果列表
        """
        try:
            days = int(test_period.replace("d", ""))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 按模板分组统计
            query = (
                select(
                    func.substring(GeneratedCourse.prompt_template, 1, 50).label(
                        "template_snippet"
                    ),
                    func.count(GeneratedCourse.id).label("usage_count"),
                    func.avg(GeneratedCourse.completion_rate).label(
                        "avg_completion_rate"
                    ),
                    func.avg(GeneratedCourse.average_score).label("avg_score"),
                )
                .where(
                    and_(
                        GeneratedCourse.created_at >= start_date,
                        GeneratedCourse.created_at <= end_date,
                        GeneratedCourse.prompt_template.isnot(None),
                    )
                )
                .group_by(func.substring(GeneratedCourse.prompt_template, 1, 50))
                .order_by(desc("avg_completion_rate"))
            )

            result = await db.execute(query)
            template_stats = result.fetchall()

            template_results = []
            for stat in template_stats:
                template_results.append(
                    {
                        "template_preview": stat[0],
                        "usage_count": stat[1],
                        "average_completion_rate": float(stat[2]) if stat[2] else 0.0,
                        "average_score": float(stat[3]) if stat[3] else 0.0,
                    }
                )

            logger.info(f"模板测试完成，共分析{len(template_results)}个模板变体")

            return template_results

        except Exception as e:
            logger.error(f"模板测试失败: {str(e)}")
            raise

    async def analyze_user_feedback(
        self, db: AsyncSession, test_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        分析用户反馈数据

        Args:
            db: 数据库会话
            test_period: 测试周期

        Returns:
            Dict: 用户反馈分析结果
        """
        # 这里应该实现用户反馈数据的分析逻辑
        # 包括满意度调查、使用频率、改进建议等
        return {
            "feedback_collected": 0,
            "satisfaction_score": 0.0,
            "common_suggestions": [],
            "usage_frequency": {},
        }

    async def generate_performance_report(
        self, db: AsyncSession, test_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        生成完整的性能报告

        Args:
            db: 数据库会话
            test_period: 测试周期

        Returns:
            Dict: 完整的性能报告
        """
        try:
            # 执行各项分析
            completion_comparison = await self.compare_completion_rates(db, test_period)
            template_analysis = await self.test_prompt_templates(db, test_period)
            feedback_analysis = await self.analyze_user_feedback(db, test_period)

            report = {
                "report_date": datetime.utcnow().isoformat(),
                "test_period": test_period,
                "completion_analysis": {
                    "generated_courses": completion_comparison.generated_courses_count,
                    "manual_courses": completion_comparison.manual_courses_count,
                    "generated_completion_rate": completion_comparison.generated_completion_rate,
                    "manual_completion_rate": completion_comparison.manual_completion_rate,
                    "improvement_percentage": completion_comparison.improvement_percentage,
                    "statistically_significant": completion_comparison.statistical_significance,
                },
                "template_analysis": template_analysis,
                "feedback_analysis": feedback_analysis,
                "recommendations": self._generate_recommendations(
                    completion_comparison, template_analysis
                ),
            }

            logger.info("性能报告生成完成")

            return report

        except Exception as e:
            logger.error(f"生成性能报告失败: {str(e)}")
            raise

    def _generate_recommendations(
        self, completion_result: BacktestResult, template_analysis: List[Dict[str, Any]]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于完成率的建议
        if completion_result.generated_completion_rate >= self.target_completion_rate:
            recommendations.append("✅ 生成课程完成率已达到目标水平")
        else:
            gap = (
                self.target_completion_rate
                - completion_result.generated_completion_rate
            )
            recommendations.append(f"⚠️ 生成课程完成率还需提升{gap:.1f}%")

        # 基于统计显著性的建议
        if completion_result.statistical_significance:
            recommendations.append("✅ 生成课程效果显著优于手工课程")
        else:
            recommendations.append("ℹ️ 建议扩大样本量以获得更可靠的统计结果")

        # 基于模板分析的建议
        if template_analysis:
            best_template = template_analysis[0]
            if best_template["average_completion_rate"] > 80:
                recommendations.append("✅ 最佳模板表现良好")
            else:
                recommendations.append("⚠️ 建议优化提示词模板设计")

        return recommendations


@dataclass
class CourseStatistics:
    """课程统计数据"""

    course_count: int
    completion_rate: float
    completion_rates: List[float]
    average_score: float
    total_students: int


# 全局实例
backtest_manager = BacktestManager()


# 便捷函数
async def run_completion_backtest(
    db: AsyncSession, test_period: str = "30d", subject_area: Optional[str] = None
) -> BacktestResult:
    """运行完成率回测"""
    return await backtest_manager.compare_completion_rates(
        db, test_period, subject_area
    )


async def run_template_analysis(
    db: AsyncSession, test_period: str = "30d"
) -> List[Dict[str, Any]]:
    """运行模板分析"""
    return await backtest_manager.test_prompt_templates(db, test_period)


async def generate_full_report(
    db: AsyncSession, test_period: str = "30d"
) -> Dict[str, Any]:
    """生成完整报告"""
    return await backtest_manager.generate_performance_report(db, test_period)
