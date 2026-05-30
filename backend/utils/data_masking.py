"""
数据脱敏服务
提供教育数据的隐私保护和脱敏处理功能
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataMaskingService:
    """数据脱敏服务类"""

    def __init__(self):
        self.masking_algorithms = {
            "basic": self._basic_masking,
            "strict": self._strict_masking,
            "comprehensive": self._comprehensive_masking,
        }

    def mask_dataframe(
        self, df: pd.DataFrame, pii_fields: List[str], masking_level: str = "strict"
    ) -> pd.DataFrame:
        """
        对DataFrame进行数据脱敏

        Args:
            df: 原始数据框
            pii_fields: 需要脱敏的字段列表
            masking_level: 脱敏级别 (basic/strict/comprehensive)

        Returns:
            脱敏后的数据框
        """
        try:
            masked_df = df.copy()

            # 获取脱敏算法
            masking_func = self.masking_algorithms.get(
                masking_level, self._strict_masking
            )

            # 对每个PII字段进行脱敏
            for field in pii_fields:
                if field in masked_df.columns:
                    masked_df[field] = masked_df[field].apply(
                        lambda x: masking_func(x, field) if pd.notna(x) else x
                    )

            logger.info(
                f"数据脱敏完成 - 级别: {masking_level}, 字段数: {len(pii_fields)}"
            )
            return masked_df

        except Exception as e:
            logger.error(f"数据脱敏失败: {e}")
            raise

    def _basic_masking(self, value: Any, field_name: str) -> str:
        """基础脱敏 - 简单替换"""
        if isinstance(value, str):
            if len(value) <= 3:
                return "***"
            else:
                return value[:1] + "*" * (len(value) - 2) + value[-1:]
        elif isinstance(value, (int, float)):
            return str(int(value))[:2] + "**"
        else:
            return str(value)[:3] + "***"

    def _strict_masking(self, value: Any, field_name: str) -> str:
        """严格脱敏 - 哈希处理"""
        if isinstance(value, str):
            # 使用哈希函数进行脱敏
            hash_value = hashlib.sha256(str(value).encode()).hexdigest()[:10]
            return f"MASKED_{hash_value}"
        elif isinstance(value, (int, float)):
            # 数值类型也进行哈希处理
            hash_value = hashlib.sha256(str(value).encode()).hexdigest()[:8]
            return f"NUM_{hash_value}"
        else:
            return f"MASKED_{type(value).__name__}"

    def _comprehensive_masking(self, value: Any, field_name: str) -> str:
        """全面脱敏 - 加盐哈希"""
        salt = "edu_data_salt_2026"  # 固定盐值
        if isinstance(value, str):
            salted_value = f"{salt}{value}{field_name}"
            hash_value = hashlib.sha256(salted_value.encode()).hexdigest()[:12]
            return f"SALT_{hash_value}"
        elif isinstance(value, (int, float)):
            salted_value = f"{salt}{value}{field_name}"
            hash_value = hashlib.sha256(salted_value.encode()).hexdigest()[:10]
            return f"SALT_NUM_{hash_value}"
        else:
            return f"SALT_{type(value).__name__}_{field_name}"

    def mask_single_value(
        self, value: Any, field_name: str, masking_level: str = "strict"
    ) -> str:
        """对单个值进行脱敏"""
        try:
            masking_func = self.masking_algorithms.get(
                masking_level, self._strict_masking
            )
            return masking_func(value, field_name)
        except Exception as e:
            logger.error(f"单值脱敏失败: {e}")
            return str(value)  # 失败时返回原值的字符串表示


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self):
        self.quality_rules = {
            "missing_values": self._check_missing_values,
            "outliers": self._check_outliers,
            "data_types": self._check_data_types,
            "ranges": self._check_value_ranges,
            "consistency": self._check_consistency,
        }

    def check_dataframe_quality(
        self, df: pd.DataFrame, rules: Optional[List[str]] = None
    ) -> "QualityReport":
        """
        检查DataFrame数据质量

        Args:
            df: 待检查的数据框
            rules: 要应用的检查规则列表

        Returns:
            质量检查报告
        """
        try:
            if rules is None:
                rules = list(self.quality_rules.keys())

            issues = []
            metrics = {}

            # 应用各项检查规则
            for rule_name in rules:
                if rule_name in self.quality_rules:
                    rule_issues, rule_metrics = self.quality_rules[rule_name](df)
                    issues.extend(rule_issues)
                    metrics.update(rule_metrics)

            # 计算总体质量分数
            quality_score = self._calculate_quality_score(len(issues), len(df))

            is_valid = (
                quality_score >= 80  # 质量分数>=80
                and metrics.get("missing_ratio", 0) <= 0.1  # 缺失值比例<=10%
                and len(issues) <= max(5, len(df) * 0.01)  # 问题数不超过5个或1%
            )

            report = QualityReport(
                is_valid=is_valid,
                quality_score=quality_score,
                issues=issues,
                metrics=metrics,
                checked_at=pd.Timestamp.now(),
            )

            logger.info(
                f"数据质量检查完成 - 分数: {quality_score:.1f}, 问题数: {len(issues)}"
            )
            return report

        except Exception as e:
            logger.error(f"数据质量检查失败: {e}")
            return QualityReport(
                is_valid=False,
                quality_score=0,
                issues=[f"检查过程出错: {str(e)}"],
                metrics={},
                checked_at=pd.Timestamp.now(),
            )

    def _check_missing_values(self, df: pd.DataFrame) -> tuple:
        """检查缺失值"""
        issues = []
        metrics = {}

        missing_counts = df.isnull().sum()
        missing_ratios = df.isnull().mean()

        metrics["missing_counts"] = missing_counts.to_dict()
        metrics["missing_ratio"] = missing_ratios.mean()

        # 报告高缺失率的列
        high_missing_cols = missing_ratios[missing_ratios > 0.1].index.tolist()
        for col in high_missing_cols:
            issues.append(
                {
                    "type": "high_missing_rate",
                    "column": col,
                    "ratio": missing_ratios[col],
                    "message": f"列 '{col}' 缺失值比例过高: {missing_ratios[col]:.2%}",
                }
            )

        return issues, metrics

    def _check_outliers(self, df: pd.DataFrame) -> tuple:
        """检查异常值"""
        issues = []
        metrics = {}

        numeric_columns = df.select_dtypes(include=[np.number]).columns
        outlier_counts = {}

        for col in numeric_columns:
            if len(df[col].dropna()) > 10:  # 至少需要10个非空值
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                outlier_counts[col] = len(outliers)

                if len(outliers) > 0:
                    issues.append(
                        {
                            "type": "outliers_detected",
                            "column": col,
                            "count": len(outliers),
                            "percentage": len(outliers) / len(df) * 100,
                            "bounds": {"lower": lower_bound, "upper": upper_bound},
                            "message": f"列 '{col}' 发现 {len(outliers)} 个异常值",
                        }
                    )

        metrics["outlier_counts"] = outlier_counts
        return issues, metrics

    def _check_data_types(self, df: pd.DataFrame) -> tuple:
        """检查数据类型一致性"""
        issues = []
        metrics = {}

        type_consistency = {}

        for col in df.columns:
            # 检查列中数据类型的多样性
            type_counts = df[col].apply(lambda x: type(x).__name__).value_counts()
            type_consistency[col] = len(type_counts)

            if len(type_counts) > 1:
                issues.append(
                    {
                        "type": "mixed_data_types",
                        "column": col,
                        "types": type_counts.to_dict(),
                        "message": f"列 '{col}' 包含多种数据类型: {list(type_counts.index)}",
                    }
                )

        metrics["type_consistency"] = type_consistency
        return issues, metrics

    def _check_value_ranges(self, df: pd.DataFrame) -> tuple:
        """检查数值范围合理性"""
        issues = []
        metrics = {}

        # 定义合理的数值范围
        reasonable_ranges = {
            "age": (0, 100),
            "score": (0, 100),
            "grade": (1, 12),
            "year": (1900, 2030),
        }

        for col in df.columns:
            col_lower = col.lower()
            for range_key, (min_val, max_val) in reasonable_ranges.items():
                if range_key in col_lower and df[col].dtype in ["int64", "float64"]:
                    out_of_range = df[(df[col] < min_val) | (df[col] > max_val)][col]
                    if len(out_of_range) > 0:
                        issues.append(
                            {
                                "type": "value_out_of_range",
                                "column": col,
                                "count": len(out_of_range),
                                "range": (min_val, max_val),
                                "message": f"列 '{col}' 有 {len(out_of_range)} 个值超出合理范围 [{min_val}, {max_val}]",
                            }
                        )

        return issues, metrics

    def _check_consistency(self, df: pd.DataFrame) -> tuple:
        """检查数据一致性"""
        issues = []
        metrics = {}

        # 检查重复行
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            issues.append(
                {
                    "type": "duplicate_rows",
                    "count": duplicate_rows,
                    "percentage": duplicate_rows / len(df) * 100,
                    "message": f"发现 {duplicate_rows} 行重复数据",
                }
            )

        # 检查逻辑一致性（例如年龄和年级的关系）
        if "age" in df.columns and "grade" in df.columns:
            # 简单的年龄-年级关系检查
            inconsistent_age_grade = df[
                (df["age"].between(6, 18))
                & (df["grade"].between(1, 12))
                & (abs(df["age"] - df["grade"] - 5) > 3)  # 年龄应该大约等于年级+5-6岁
            ]

            if len(inconsistent_age_grade) > 0:
                issues.append(
                    {
                        "type": "logical_inconsistency",
                        "columns": ["age", "grade"],
                        "count": len(inconsistent_age_grade),
                        "message": f"发现 {len(inconsistent_age_grade)} 条年龄和年级不一致的记录",
                    }
                )

        metrics["duplicate_rows"] = duplicate_rows
        return issues, metrics

    def _calculate_quality_score(self, issue_count: int, total_rows: int) -> float:
        """计算数据质量分数"""
        if total_rows == 0:
            return 0.0

        # 基础分数：100分
        base_score = 100.0

        # 根据问题数量扣分
        issues_per_thousand = (issue_count / total_rows) * 1000
        penalty = min(issues_per_thousand * 2, 50)  # 最多扣50分

        return max(0, base_score - penalty)


class QualityReport:
    """数据质量检查报告"""

    def __init__(
        self,
        is_valid: bool,
        quality_score: float,
        issues: List[Dict],
        metrics: Dict,
        checked_at,
    ):
        self.is_valid = is_valid
        self.quality_score = quality_score
        self.issues = issues
        self.metrics = metrics
        self.checked_at = checked_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "is_valid": self.is_valid,
            "quality_score": self.quality_score,
            "issue_count": len(self.issues),
            "issues": self.issues,
            "metrics": self.metrics,
            "checked_at": self.checked_at.isoformat(),
        }

    def __str__(self) -> str:
        return f"QualityReport(valid={self.is_valid}, score={self.quality_score:.1f}, issues={len(self.issues)})"


if __name__ == "__main__":
    # 测试数据脱敏和质量检查
    test_data = pd.DataFrame(
        {
            "student_name": ["张三", "李四", "王五"],
            "phone": ["13800138001", "13800138002", "13800138003"],
            "score": [85, 92, 78],
            "age": [15, 16, 14],
        }
    )

    # 测试数据脱敏
    masking_service = DataMaskingService()
    masked_data = masking_service.mask_dataframe(
        test_data, pii_fields=["student_name", "phone"], masking_level="strict"
    )
    print("脱敏后数据:")
    print(masked_data)

    # 测试数据质量检查
    quality_checker = DataQualityChecker()
    quality_report = quality_checker.check_dataframe_quality(test_data)
    print("\n质量检查报告:")
    print(quality_report.to_dict())
