"""
STEM学科能力分析算法
实现学科能力评估、区域对比分析和趋势预测功能
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from ..config.edu_data_config import edu_config
from ..models.edu_data_models import (
    EduAcademicPerformance,
    EduRegionalData,
    EduStudentDemographics,
    EduSubject,
)

logger = logging.getLogger(__name__)


@dataclass
class SubjectAnalysis:
    """学科分析结果"""

    subject: EduSubject
    average_score: float
    median_score: float
    std_deviation: float
    score_distribution: Dict[str, int]  # 分数段分布
    improvement_rate: float  # 提升率
    ranking: int  # 排名


@dataclass
class RegionalComparison:
    """区域对比分析结果"""

    region_id: str
    region_name: str
    average_stem_score: float
    subject_scores: Dict[EduSubject, float]
    student_count: int
    schools_count: int
    performance_trend: str  # 'improving', 'declining', 'stable'
    comparison_index: float  # 与平均水平的比较指数


@dataclass
class TrendPrediction:
    """趋势预测结果"""

    subject: EduSubject
    predicted_scores: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend_direction: str  # 'upward', 'downward', 'stable'
    prediction_period: int  # 预测期数


class STEMCapabilityAnalyzer:
    """STEM能力分析器"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.subject_weights = {
            EduSubject.MATH: edu_config.get_subject_weight("math"),
            EduSubject.SCIENCE: edu_config.get_subject_weight("science"),
            EduSubject.TECHNOLOGY: edu_config.get_subject_weight("technology"),
            EduSubject.ENGINEERING: edu_config.get_subject_weight("engineering"),
        }

    def analyze_stem_capabilities(
        self,
        academic_data: List[EduAcademicPerformance],
        demographic_data: List[EduStudentDemographics] = None,
        regional_data: List[EduRegionalData] = None,
    ) -> Dict[str, Any]:
        """
        全面的STEM能力分析

        Args:
            academic_data: 学术表现数据
            demographic_data: 学生人口统计数据（可选）
            regional_data: 区域数据（可选）

        Returns:
            综合分析结果
        """
        try:
            # 转换为DataFrame便于处理
            academic_df = pd.DataFrame([vars(record) for record in academic_data])

            # 按学科分组分析
            subject_analyses = self._analyze_by_subject(academic_df)

            # 计算综合STEM得分
            stem_overall_score = self._calculate_stem_overall_score(subject_analyses)

            # 区域对比分析
            regional_analysis = (
                self._perform_regional_analysis(academic_df, regional_data)
                if regional_data
                else []
            )

            # 趋势分析
            trend_analysis = self._perform_trend_analysis(academic_df)

            # 生成能力等级
            capability_level = self._assess_capability_level(stem_overall_score)

            # 构建分析结果
            analysis_result = {
                "analysis_timestamp": datetime.now().isoformat(),
                "stem_overall_score": stem_overall_score,
                "capability_level": capability_level,
                "subject_analyses": {
                    sa.subject.value: vars(sa) for sa in subject_analyses
                },
                "regional_comparison": [vars(ra) for ra in regional_analysis],
                "trend_analysis": {ta.subject.value: vars(ta) for ta in trend_analysis},
                "recommendations": self._generate_recommendations(subject_analyses),
                "data_quality_metrics": self._calculate_data_quality_metrics(
                    academic_df
                ),
            }

            logger.info(f"STEM能力分析完成 - 综合得分: {stem_overall_score:.2f}")
            return analysis_result

        except Exception as e:
            logger.error(f"STEM能力分析失败: {e}")
            raise

    def _analyze_by_subject(self, academic_df: pd.DataFrame) -> List[SubjectAnalysis]:
        """按学科进行分析"""
        subject_analyses = []

        # 过滤STEM相关学科
        stem_subjects = [
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ]

        for subject in stem_subjects:
            subject_data = academic_df[academic_df["subject"] == subject.value]

            if len(subject_data) == 0:
                continue

            scores = subject_data["score"].values

            # 基础统计
            avg_score = float(np.mean(scores))
            median_score = float(np.median(scores))
            std_dev = float(np.std(scores))

            # 分数段分布
            score_distribution = self._calculate_score_distribution(scores)

            # 提升率计算（简化版）
            improvement_rate = self._calculate_improvement_rate(subject_data)

            analysis = SubjectAnalysis(
                subject=subject,
                average_score=avg_score,
                median_score=median_score,
                std_deviation=std_dev,
                score_distribution=score_distribution,
                improvement_rate=improvement_rate,
                ranking=0,  # 后续计算
            )

            subject_analyses.append(analysis)

        # 计算排名
        subject_analyses.sort(key=lambda x: x.average_score, reverse=True)
        for i, analysis in enumerate(subject_analyses):
            analysis.ranking = i + 1

        return subject_analyses

    def _calculate_stem_overall_score(
        self, subject_analyses: List[SubjectAnalysis]
    ) -> float:
        """计算综合STEM得分"""
        if not subject_analyses:
            return 0.0

        weighted_sum = 0.0
        weight_sum = 0.0

        for analysis in subject_analyses:
            weight = self.subject_weights.get(analysis.subject, 0.25)
            weighted_sum += analysis.average_score * weight
            weight_sum += weight

        return weighted_sum / weight_sum if weight_sum > 0 else 0.0

    def _perform_regional_analysis(
        self, academic_df: pd.DataFrame, regional_data: List[EduRegionalData]
    ) -> List[RegionalComparison]:
        """执行区域对比分析"""
        regional_comparisons = []

        # 按区域分组计算平均STEM得分
        regional_scores = {}
        for region in regional_data:
            region_academic = academic_df[academic_df["region_id"] == region.region_id]
            if len(region_academic) > 0:
                stem_score = self._calculate_regional_stem_score(region_academic)
                regional_scores[region.region_id] = {
                    "score": stem_score,
                    "student_count": len(region_academic),
                    "schools_count": region.schools_count,
                }

        # 计算整体平均分作为基准
        overall_avg = np.mean(
            list(regional_scores.values())[0]["score"] for v in regional_scores.values()
        )

        # 生成区域对比结果
        for region in regional_data:
            if region.region_id in regional_scores:
                region_info = regional_scores[region.region_id]

                # 计算各学科得分
                subject_scores = self._calculate_regional_subject_scores(
                    academic_df[academic_df["region_id"] == region.region_id]
                )

                # 确定趋势
                trend = self._determine_performance_trend(
                    academic_df[academic_df["region_id"] == region.region_id]
                )

                comparison = RegionalComparison(
                    region_id=region.region_id,
                    region_name=region.region_name,
                    average_stem_score=region_info["score"],
                    subject_scores=subject_scores,
                    student_count=region_info["student_count"],
                    schools_count=region_info["schools_count"],
                    performance_trend=trend,
                    comparison_index=(
                        region_info["score"] / overall_avg if overall_avg > 0 else 1.0
                    ),
                )

                regional_comparisons.append(comparison)

        # 按STEM得分排序
        regional_comparisons.sort(key=lambda x: x.average_stem_score, reverse=True)

        return regional_comparisons

    def _perform_trend_analysis(
        self, academic_df: pd.DataFrame
    ) -> List[TrendPrediction]:
        """执行趋势分析"""
        predictions = []

        stem_subjects = [
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ]

        for subject in stem_subjects:
            subject_data = academic_df[academic_df["subject"] == subject.value]

            if len(subject_data) < 10:  # 数据量不足时不进行预测
                continue

            # 按时间排序
            if "date_taken" in subject_data.columns:
                subject_data = subject_data.sort_values("date_taken")

            # 简单线性回归预测
            prediction = self._predict_subject_trend(subject_data, subject)
            if prediction:
                predictions.append(prediction)

        return predictions

    def _calculate_score_distribution(self, scores: np.ndarray) -> Dict[str, int]:
        """计算分数段分布"""
        distribution = {
            "优秀(90-100)": int(np.sum((scores >= 90) & (scores <= 100))),
            "良好(80-89)": int(np.sum((scores >= 80) & (scores < 90))),
            "中等(70-79)": int(np.sum((scores >= 70) & (scores < 80))),
            "及格(60-69)": int(np.sum((scores >= 60) & (scores < 70))),
            "不及格(<60)": int(np.sum(scores < 60)),
        }
        return distribution

    def _calculate_improvement_rate(self, subject_data: pd.DataFrame) -> float:
        """计算提升率"""
        try:
            if len(subject_data) < 20:
                return 0.0

            # 简化的提升率计算：最近25% vs 最早25%的平均分差异
            sorted_data = subject_data.sort_values(
                "date_taken"
                if "date_taken" in subject_data.columns
                else subject_data.index
            )

            early_quarter = sorted_data.iloc[: len(sorted_data) // 4]["score"].mean()
            recent_quarter = sorted_data.iloc[-len(sorted_data) // 4 :]["score"].mean()

            if early_quarter > 0:
                return float((recent_quarter - early_quarter) / early_quarter * 100)
            return 0.0

        except Exception as e:
            logger.warning(f"提升率计算失败: {e}")
            return 0.0

    def _calculate_regional_stem_score(self, regional_data: pd.DataFrame) -> float:
        """计算区域STEM综合得分"""
        stem_subjects = ["math", "science", "technology", "engineering"]
        stem_data = regional_data[regional_data["subject"].isin(stem_subjects)]

        if len(stem_data) == 0:
            return 0.0

        return float(stem_data["score"].mean())

    def _calculate_regional_subject_scores(
        self, regional_data: pd.DataFrame
    ) -> Dict[EduSubject, float]:
        """计算区域各学科得分"""
        subject_scores = {}

        for subject in [
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ]:
            subject_data = regional_data[regional_data["subject"] == subject.value]
            if len(subject_data) > 0:
                subject_scores[subject] = float(subject_data["score"].mean())
            else:
                subject_scores[subject] = 0.0

        return subject_scores

    def _determine_performance_trend(self, regional_data: pd.DataFrame) -> str:
        """确定表现趋势"""
        try:
            if len(regional_data) < 10:
                return "stable"

            # 按时间分组计算平均分
            if "date_taken" in regional_data.columns:
                regional_data["year"] = pd.to_datetime(
                    regional_data["date_taken"]
                ).dt.year
                yearly_scores = regional_data.groupby("year")["score"].mean()

                if len(yearly_scores) < 2:
                    return "stable"

                # 简单的趋势判断
                slope, _, _, _, _ = stats.linregress(
                    range(len(yearly_scores)), yearly_scores.values
                )

                if slope > 2:
                    return "improving"
                elif slope < -2:
                    return "declining"
                else:
                    return "stable"
            else:
                return "stable"

        except Exception as e:
            logger.warning(f"趋势判断失败: {e}")
            return "stable"

    def _predict_subject_trend(
        self, subject_data: pd.DataFrame, subject: EduSubject
    ) -> Optional[TrendPrediction]:
        """预测学科趋势"""
        try:
            # 准备时间序列数据
            if "date_taken" in subject_data.columns:
                subject_data = subject_data.sort_values("date_taken")
                time_points = pd.to_datetime(subject_data["date_taken"])
                scores = subject_data["score"].values
            else:
                # 使用索引作为时间点
                time_points = np.arange(len(subject_data))
                scores = subject_data["score"].values

            if len(time_points) < 10:
                return None

            # 线性回归预测未来6个时间点
            X = (
                time_points.values.reshape(-1, 1)
                if hasattr(time_points, "values")
                else time_points.reshape(-1, 1)
            )
            y = scores

            # 标准化
            X_scaled = self.scaler.fit_transform(X)

            # 训练模型
            model = LinearRegression()
            model.fit(X_scaled[:-6], y[:-6])  # 使用前面的数据训练

            # 预测未来6个点
            future_X = np.linspace(len(X_scaled) - 6, len(X_scaled) + 5, 6).reshape(
                -1, 1
            )
            future_X_scaled = self.scaler.transform(future_X)
            predictions = model.predict(future_X_scaled)

            # 计算置信区间（简化）
            residuals = y[:-6] - model.predict(X_scaled[:-6])
            mse = np.mean(residuals**2)
            std_error = np.sqrt(mse)

            confidence_intervals = [
                (max(0, pred - 1.96 * std_error), min(100, pred + 1.96 * std_error))
                for pred in predictions
            ]

            # 确定趋势方向
            slope = (predictions[-1] - predictions[0]) / len(predictions)
            if slope > 1:
                trend_direction = "upward"
            elif slope < -1:
                trend_direction = "downward"
            else:
                trend_direction = "stable"

            return TrendPrediction(
                subject=subject,
                predicted_scores=predictions.tolist(),
                confidence_intervals=confidence_intervals,
                trend_direction=trend_direction,
                prediction_period=6,
            )

        except Exception as e:
            logger.warning(f"趋势预测失败: {e}")
            return None

    def _assess_capability_level(self, stem_score: float) -> str:
        """评估能力等级"""
        if stem_score >= 90:
            return "excellent"  # 优秀
        elif stem_score >= 80:
            return "good"  # 良好
        elif stem_score >= 70:
            return "fair"  # 一般
        elif stem_score >= 60:
            return "poor"  # 较差
        else:
            return "very_poor"  # 很差

    def _generate_recommendations(
        self, subject_analyses: List[SubjectAnalysis]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于学科表现的建议
        weak_subjects = [sa for sa in subject_analyses if sa.average_score < 75]
        strong_subjects = [sa for sa in subject_analyses if sa.average_score >= 85]

        if weak_subjects:
            weakest = min(weak_subjects, key=lambda x: x.average_score)
            recommendations.append(f"重点关注{weakest.subject.value}学科的教学改进")

        if strong_subjects:
            strongest = max(strong_subjects, key=lambda x: x.average_score)
            recommendations.append(f"推广{strongest.subject.value}学科的成功教学经验")

        # 基于分布的建议
        for analysis in subject_analyses:
            poor_ratio = analysis.score_distribution.get("不及格(<60)", 0) / sum(
                analysis.score_distribution.values()
            )
            if poor_ratio > 0.2:
                recommendations.append(
                    f"加强{analysis.subject.value}学科的基础知识教学"
                )

        if not recommendations:
            recommendations.append("继续保持现有教学质量和水平")

        return recommendations

    def _calculate_data_quality_metrics(
        self, academic_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """计算数据质量指标"""
        metrics = {
            "total_records": len(academic_df),
            "unique_students": (
                academic_df["student_id"].nunique()
                if "student_id" in academic_df.columns
                else 0
            ),
            "completion_rate": float((academic_df.count() / len(academic_df)).mean()),
            "score_validity": float(
                len(
                    academic_df[
                        (academic_df["score"] >= 0) & (academic_df["score"] <= 100)
                    ]
                )
                / len(academic_df)
            ),
        }

        return metrics


# 全局分析器实例
stem_analyzer = STEMCapabilityAnalyzer()


if __name__ == "__main__":
    # 测试STEM分析器
    import random

    # 生成测试数据
    test_data = []
    subjects = ["math", "science", "technology", "engineering"]

    for i in range(1000):
        test_data.append(
            EduAcademicPerformance(
                student_id=f"S{i:04d}",
                subject=random.choice(subjects),
                assessment_type="standardized_test",
                score=random.uniform(60, 100),
                date_taken=datetime.now(),
                academic_year="2023-2024",
            )
        )

    # 执行分析
    analyzer = STEMCapabilityAnalyzer()
    try:
        results = analyzer.analyze_stem_capabilities(test_data)
        print("STEM分析结果:")
        print(f"综合得分: {results['stem_overall_score']:.2f}")
        print(f"能力等级: {results['capability_level']}")
        print(f"学科分析数量: {len(results['subject_analyses'])}")
        print(f"建议: {results['recommendations']}")
    except Exception as e:
        print(f"分析失败: {e}")
