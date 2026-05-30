"""
教育数据联邦学习系统单元测试
测试联邦学习组件、数据脱敏、隐私保护等功能
"""

from datetime import datetime
import unittest

import numpy as np
import pandas as pd

from backend.analytics.stem_analyzer import STEMCapabilityAnalyzer
from backend.data.edu_data_standardization import EduDataProtocol, EduDataStandardizer
from backend.models.edu_data_models import EduAcademicPerformance
from backend.security.edu_privacy_protection import (
    DataAnonymization,
    DifferentialPrivacyEngine,
    SecureAggregation,
)
from backend.utils.data_masking import DataMaskingService, DataQualityChecker


class TestDataMaskingService(unittest.TestCase):
    """数据脱敏服务测试"""

    def setUp(self):
        self.masking_service = DataMaskingService()
        self.test_df = pd.DataFrame(
            {
                "student_name": ["张三", "李四", "王五"],
                "phone": ["13800138001", "13800138002", "13800138003"],
                "email": ["zhang@example.com", "li@example.com", "wang@example.com"],
                "score": [85, 92, 78],
                "age": [15, 16, 14],
            }
        )
        self.pii_fields = ["student_name", "phone", "email"]

    def test_basic_masking(self):
        """测试基础脱敏"""
        masked_df = self.masking_service.mask_dataframe(
            self.test_df, self.pii_fields, "basic"
        )

        # 验证PII字段已被修改
        for field in self.pii_fields:
            self.assertFalse(
                masked_df[field].equals(self.test_df[field]),
                f"字段 {field} 未被正确脱敏",
            )

        # 验证非PII字段保持不变
        self.assertTrue(
            masked_df["score"].equals(self.test_df["score"]), "非PII字段被错误修改"
        )

    def test_strict_masking(self):
        """测试严格脱敏"""
        masked_df = self.masking_service.mask_dataframe(
            self.test_df, self.pii_fields, "strict"
        )

        # 验证脱敏后的值格式正确
        for field in self.pii_fields:
            for value in masked_df[field]:
                self.assertTrue(
                    value.startswith("MASKED_") or value.startswith("NUM_"),
                    f"严格脱敏格式不正确: {value}",
                )

    def test_comprehensive_masking(self):
        """测试全面脱敏"""
        masked_df = self.masking_service.mask_dataframe(
            self.test_df, self.pii_fields, "comprehensive"
        )

        # 验证全面脱敏格式
        for field in self.pii_fields:
            for value in masked_df[field]:
                self.assertTrue(
                    value.startswith("SALT_"), f"全面脱敏格式不正确: {value}"
                )

    def test_single_value_masking(self):
        """测试单值脱敏"""
        original_value = "张三"
        masked_value = self.masking_service.mask_single_value(
            original_value, "student_name", "strict"
        )

        self.assertNotEqual(original_value, masked_value)
        self.assertTrue(masked_value.startswith("MASKED_"))


class TestDataQualityChecker(unittest.TestCase):
    """数据质量检查器测试"""

    def setUp(self):
        self.quality_checker = DataQualityChecker()

        # 创建测试数据（包含质量问题）
        self.test_df = pd.DataFrame(
            {
                "student_id": ["S001", "S002", "S003", "S004", "S005"],
                "name": ["张三", "李四", None, "王五", "赵六"],  # 包含空值
                "age": [15, 16, 14, 200, 13],  # 包含异常值
                "score": [85, 92, 78, 88, -5],  # 包含负值
                "grade": [9, 10, 8, 13, 7],  # 包含不合理年级
                "duplicate_check": [1, 1, 2, 3, 3],  # 包含重复值
            }
        )

    def test_missing_values_detection(self):
        """测试缺失值检测"""
        report = self.quality_checker.check_dataframe_quality(self.test_df)

        self.assertFalse(report.is_valid)
        self.assertGreater(len(report.issues), 0)

        # 检查是否正确识别缺失值问题
        missing_issues = [
            issue for issue in report.issues if issue["type"] == "high_missing_rate"
        ]
        self.assertGreater(len(missing_issues), 0)

    def test_outlier_detection(self):
        """测试异常值检测"""
        report = self.quality_checker.check_dataframe_quality(self.test_df)

        outlier_issues = [
            issue for issue in report.issues if issue["type"] == "outliers_detected"
        ]
        self.assertGreater(len(outlier_issues), 0)

    def test_data_type_consistency(self):
        """测试数据类型一致性检查"""
        # 创建混合类型数据
        mixed_df = pd.DataFrame({"mixed_column": [1, "two", 3.0, None, True]})

        report = self.quality_checker.check_dataframe_quality(mixed_df)

        type_issues = [
            issue for issue in report.issues if issue["type"] == "mixed_data_types"
        ]
        self.assertGreater(len(type_issues), 0)

    def test_quality_score_calculation(self):
        """测试质量分数计算"""
        clean_df = pd.DataFrame({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})

        report = self.quality_checker.check_dataframe_quality(clean_df)

        self.assertTrue(report.is_valid)
        self.assertGreaterEqual(report.quality_score, 90)
        self.assertEqual(len(report.issues), 0)


class TestDifferentialPrivacyEngine(unittest.IsolatedAsyncioTestCase):
    """差分隐私引擎测试"""

    def setUp(self):
        self.dp_engine = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)

    async def test_noise_addition(self):
        """测试噪声添加"""
        # 创建测试梯度
        import torch

        test_gradients = {
            "weight1": torch.tensor([1.0, 2.0, 3.0]),
            "weight2": torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        }

        # 添加噪声
        noisy_gradients = self.dp_engine.add_noise_to_gradients(test_gradients)

        # 验证噪声已添加
        for key in test_gradients:
            self.assertIn(key, noisy_gradients)
            self.assertFalse(
                torch.equal(test_gradients[key], noisy_gradients[key]),
                f"梯度 {key} 未添加噪声",
            )

    def test_privacy_budget_consumption(self):
        """测试隐私预算消耗"""
        initial_budget = self.dp_engine.budget.remaining()

        # 消耗一些预算
        self.dp_engine.budget.consume(0.1)

        remaining_budget = self.dp_engine.budget.remaining()
        self.assertLess(remaining_budget, initial_budget)
        self.assertAlmostEqual(remaining_budget, initial_budget - 0.1)

    def test_privacy_loss_tracking(self):
        """测试隐私损失跟踪"""
        privacy_loss = self.dp_engine.get_privacy_loss()

        self.assertIn("epsilon", privacy_loss)
        self.assertIn("delta", privacy_loss)
        self.assertIn("consumed_budget", privacy_loss)
        self.assertIn("remaining_budget", privacy_loss)

        self.assertEqual(privacy_loss["epsilon"], 1.0)
        self.assertEqual(privacy_loss["delta"], 1e-5)


class TestSecureAggregation(unittest.TestCase):
    """安全聚合测试"""

    def setUp(self):
        dp_engine = DifferentialPrivacyEngine(epsilon=1.0)
        self.aggregator = SecureAggregation(dp_engine)

    def test_weighted_aggregation(self):
        """测试加权聚合"""
        # 创建测试模型更新
        model_updates = [
            {"param1": 1.0, "param2": 2.0},
            {"param1": 1.5, "param2": 2.5},
            {"param1": 0.8, "param2": 1.8},
        ]

        weights = [0.4, 0.3, 0.3]

        aggregated = self.aggregator.aggregate_with_dp(model_updates, weights)

        # 验证聚合结果
        expected_param1 = 1.0 * 0.4 + 1.5 * 0.3 + 0.8 * 0.3
        expected_param2 = 2.0 * 0.4 + 2.5 * 0.3 + 1.8 * 0.3

        self.assertAlmostEqual(aggregated["param1"], expected_param1, places=6)
        self.assertAlmostEqual(aggregated["param2"], expected_param2, places=6)

    def test_uniform_aggregation(self):
        """测试均匀聚合"""
        model_updates = [{"param1": 1.0, "param2": 2.0}, {"param1": 1.5, "param2": 2.5}]

        aggregated = self.aggregator.aggregate_with_dp(model_updates)

        # 均匀权重应该是 0.5
        expected_param1 = (1.0 + 1.5) / 2
        expected_param2 = (2.0 + 2.5) / 2

        self.assertAlmostEqual(aggregated["param1"], expected_param1, places=6)
        self.assertAlmostEqual(aggregated["param2"], expected_param2, places=6)


class TestDataAnonymization(unittest.TestCase):
    """数据匿名化测试"""

    def setUp(self):
        self.test_data = [
            {"name": "张三", "age": 25, "city": "北京", "salary": 8000},
            {"name": "李四", "age": 26, "city": "北京", "salary": 8500},
            {"name": "王五", "age": 24, "city": "上海", "salary": 7500},
            {"name": "赵六", "age": 27, "city": "广州", "salary": 9000},
        ]

    def test_k_anonymity(self):
        """测试K-匿名化"""
        anonymized_data = DataAnonymization.k_anonymize(
            self.test_data, quasi_identifiers=["age", "city"], k=2
        )

        # 验证数据数量保持一致
        self.assertEqual(len(anonymized_data), len(self.test_data))

        # 验证准标识符已被适当处理
        for record in anonymized_data:
            self.assertIn("age", record)
            self.assertIn("city", record)


class TestEduDataStandardizer(unittest.TestCase):
    """教育数据标准化测试"""

    def setUp(self):
        self.standardizer = EduDataStandardizer()

    def test_student_data_standardization(self):
        """测试学生数据标准化"""
        raw_data = pd.DataFrame(
            {
                "学号": ["S001", "S002"],
                "姓名": ["张三", "李四"],
                "年级": ["小学", "初中"],
                "性别": ["男", "女"],
            }
        )

        standardized = self.standardizer.standardize_data(raw_data, "student")

        # 验证关键字段存在
        self.assertIn("student_id", standardized.columns)
        self.assertIn("name", standardized.columns)
        self.assertIn("grade_level", standardized.columns)

        # 验证年级标准化
        self.assertIn("elementary", standardized["grade_level"].values)
        self.assertIn("middle", standardized["grade_level"].values)

    def test_academic_data_standardization(self):
        """测试学术数据标准化"""
        raw_data = pd.DataFrame(
            {"学号": ["S001", "S002"], "学科": ["数学", "语文"], "分数": [85, 90]}
        )

        standardized = self.standardizer.standardize_data(raw_data, "academic")

        # 验证字段标准化
        self.assertIn("student_id", standardized.columns)
        self.assertIn("subject", standardized.columns)
        self.assertIn("score", standardized.columns)

        # 验证学科标准化
        self.assertIn("math", standardized["subject"].values)


class TestEduDataProtocol(unittest.TestCase):
    """教育数据协议测试"""

    def test_student_data_validation(self):
        """测试学生数据验证"""
        valid_data = {
            "student_id": "S001",
            "name": "张三",
            "age": 15,
            "grade_level": "middle",
        }

        invalid_data = {
            "student_id": "",  # 必填字段为空
            "name": "李四",
            "age": 150,  # 年龄超出范围
        }

        # 验证有效数据
        self.assertTrue(EduDataProtocol.validate_data_structure(valid_data, "student"))

        # 验证无效数据
        self.assertFalse(
            EduDataProtocol.validate_data_structure(invalid_data, "student")
        )

    def test_academic_data_validation(self):
        """测试学术数据验证"""
        valid_data = {"student_id": "S001", "subject": "math", "score": 85}

        invalid_data = {
            "student_id": "S001",
            "subject": "invalid_subject",  # 无效学科
            "score": 150,  # 分数超出范围
        }

        self.assertTrue(EduDataProtocol.validate_data_structure(valid_data, "academic"))
        self.assertFalse(
            EduDataProtocol.validate_data_structure(invalid_data, "academic")
        )


class TestSTEMCapabilityAnalyzer(unittest.IsolatedAsyncioTestCase):
    """STEM能力分析器测试"""

    def setUp(self):
        self.analyzer = STEMCapabilityAnalyzer()

        # 创建测试学术数据
        self.test_academic_data = []
        subjects = ["math", "science", "technology", "engineering"]

        for i in range(200):  # 200条测试记录
            self.test_academic_data.append(
                EduAcademicPerformance(
                    student_id=f"S{i:03d}",
                    subject=subjects[i % 4],
                    assessment_type="standardized_test",
                    score=np.random.uniform(60, 100),
                    date_taken=datetime.now(),
                    academic_year="2023-2024",
                )
            )

    async def test_stem_analysis(self):
        """测试STEM综合分析"""
        results = self.analyzer.analyze_stem_capabilities(self.test_academic_data)

        # 验证基本结构
        self.assertIn("stem_overall_score", results)
        self.assertIn("subject_analyses", results)
        self.assertIn("capability_level", results)
        self.assertIn("recommendations", results)

        # 验证得分范围
        self.assertGreaterEqual(results["stem_overall_score"], 0)
        self.assertLessEqual(results["stem_overall_score"], 100)

        # 验证学科分析结果
        self.assertEqual(len(results["subject_analyses"]), 4)  # 4个STEM学科

        # 验证能力等级
        capability_levels = ["excellent", "good", "fair", "poor", "very_poor"]
        self.assertIn(results["capability_level"], capability_levels)


class TestIntegrationScenarios(unittest.IsolatedAsyncioTestCase):
    """集成场景测试"""

    async def test_complete_data_pipeline(self):
        """测试完整数据处理流水线"""
        # 1. 创建原始数据
        raw_data = pd.DataFrame(
            {
                "学号": [f"S{i:03d}" for i in range(50)],
                "姓名": [f"学生{i}" for i in range(50)],
                "年级": ["小学"] * 25 + ["初中"] * 25,
                "数学": np.random.uniform(60, 100, 50),
                "科学": np.random.uniform(60, 100, 50),
            }
        )

        # 2. 数据标准化
        standardizer = EduDataStandardizer()
        standardized_data = standardizer.standardize_data(raw_data, "student")

        # 3. 数据质量检查
        quality_checker = DataQualityChecker()
        quality_report = quality_checker.check_dataframe_quality(standardized_data)

        # 4. 数据脱敏
        masking_service = DataMaskingService()
        masked_data = masking_service.mask_dataframe(
            standardized_data, ["name"], "strict"  # 脱敏姓名字段
        )

        # 5. 验证整个流程
        self.assertTrue(len(standardized_data) > 0)
        self.assertTrue(quality_report.is_valid or len(quality_report.issues) > 0)
        self.assertNotEqual(list(standardized_data["name"]), list(masked_data["name"]))


if __name__ == "__main__":
    # 运行所有测试
    unittest.main(verbosity=2)
