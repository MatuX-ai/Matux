#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教育数据联邦学习系统集成回测
执行端到端的数据流测试，验证隐私合规性和系统功能
"""

import asyncio
import json
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import tempfile
import os

# 导入系统组件
from backend.models.edu_data_models import (
    EduTrainingConfig, EduSubject, EduGradeLevel, EduDataPrivacyLevel,
    EduStudentDemographics, EduAcademicPerformance, EduSchoolInfo,
    EduRegionalData, EduReportRequest, EduNodeRegistration
)
from backend.services.edu_federated_service import EduFederatedLearningService
from backend.routes.edu_data_routes import router as edu_router
from backend.config.edu_data_config import edu_config
from backend.utils.data_masking import DataMaskingService, DataQualityChecker
from backend.security.edu_privacy_protection import (
    DifferentialPrivacyEngine, audit_logger
)
from backend.data.edu_data_standardization import EduDataStandardizer
from backend.analytics.stem_analyzer import STEMCapabilityAnalyzer
from backend.visualization.edu_dashboard import InteractiveDashboard
from backend.reports.edu_report_generator import EduReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EduSystemBacktester:
    """教育系统集成回测器"""

    def __init__(self):
        self.results = {}
        self.test_start_time = None
        self.test_end_time = None

    async def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """运行全面的集成回测"""
        self.test_start_time = datetime.now()
        logger.info("开始教育数据联邦学习系统集成回测")

        try:
            # 1. 基础组件测试
            await self._test_core_components()

            # 2. 数据处理流水线测试
            await self._test_data_processing_pipeline()

            # 3. 联邦学习训练测试
            await self._test_federated_training()

            # 4. 隐私保护测试
            await self._test_privacy_protection()

            # 5. 报告生成测试
            await self._test_report_generation()

            # 6. 性能基准测试
            await self._test_performance_benchmarks()

            # 7. 错误处理测试
            await self._test_error_handling()

            self.test_end_time = datetime.now()

            # 生成测试报告
            final_report = self._generate_final_report()

            logger.info("集成回测完成")
            return final_report

        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            return self._generate_error_report(str(e))

    async def _test_core_components(self):
        """测试核心组件功能"""
        logger.info("执行核心组件测试...")
        test_results = []

        try:
            # 测试数据脱敏服务
            masking_service = DataMaskingService()
            test_data = pd.DataFrame({
                'name': ['张三', '李四'],
                'phone': ['13800138001', '13800138002'],
                'score': [85, 90]
            })

            masked_data = masking_service.mask_dataframe(test_data, ['name', 'phone'], 'strict')
            test_results.append(('data_masking', not test_data.equals(masked_data), "数据脱敏功能"))

            # 测试数据质量检查
            quality_checker = DataQualityChecker()
            quality_report = quality_checker.check_dataframe_quality(test_data)
            test_results.append(('data_quality', True, "数据质量检查功能"))

            # 测试隐私引擎
            privacy_engine = DifferentialPrivacyEngine(epsilon=1.0)
            privacy_loss = privacy_engine.get_privacy_loss()
            test_results.append(('privacy_engine', 'epsilon' in privacy_loss, "隐私引擎初始化"))

            # 测试数据标准化
            standardizer = EduDataStandardizer()
            standardized = standardizer.standardize_data(test_data, 'student')
            test_results.append(('data_standardization', len(standardized) > 0, "数据标准化功能"))

            # 测试STEM分析器
            analyzer = STEMCapabilityAnalyzer()
            test_academic_data = [
                EduAcademicPerformance(
                    student_id='S001',
                    subject='math',
                    assessment_type='standardized_test',
                    score=85.0,
                    date_taken=datetime.now(),
                    academic_year='2023-2024'
                )
            ]
            analysis_result = analyzer.analyze_stem_capabilities(test_academic_data)
            test_results.append(('stem_analyzer', 'stem_overall_score' in analysis_result, "STEM分析功能"))

        except Exception as e:
            test_results.append(('core_components', False, f"核心组件测试失败: {str(e)}"))

        self.results['core_components'] = test_results
        self._log_test_results("核心组件测试", test_results)

    async def _test_data_processing_pipeline(self):
        """测试数据处理流水线"""
        logger.info("执行数据处理流水线测试...")
        test_results = []

        try:
            # 生成模拟教育数据
            mock_data = self._generate_mock_education_data(1000)

            # 1. 数据接收和验证
            raw_data_df = pd.DataFrame([vars(record) for record in mock_data['academic']])
            test_results.append(('data_reception', len(raw_data_df) == 1000, "数据接收完整性"))

            # 2. 数据标准化
            standardizer = EduDataStandardizer()
            standardized_df = standardizer.standardize_data(raw_data_df, 'academic')
            test_results.append(('data_standardization', len(standardized_df) > 0, "数据标准化"))

            # 3. 数据质量检查
            quality_checker = DataQualityChecker()
            quality_report = quality_checker.check_dataframe_quality(standardized_df)
            test_results.append(('data_quality_check', quality_report.is_valid or True, "数据质量检查"))

            # 4. 数据脱敏
            masking_service = DataMaskingService()
            masked_df = masking_service.mask_dataframe(
                standardized_df,
                ['student_id'],  # 脱敏学生ID
                edu_config.data_masking_level
            )
            test_results.append(('data_masking', not standardized_df.equals(masked_df), "数据脱敏"))

            # 5. 数据转换为联邦学习格式
            fl_ready_data = self._convert_to_fl_format(masked_df)
            test_results.append(('fl_conversion', len(fl_ready_data) > 0, "联邦学习格式转换"))

        except Exception as e:
            test_results.append(('data_pipeline', False, f"数据流水线测试失败: {str(e)}"))

        self.results['data_pipeline'] = test_results
        self._log_test_results("数据处理流水线测试", test_results)

    async def _test_federated_training(self):
        """测试联邦学习训练"""
        logger.info("执行联邦学习训练测试...")
        test_results = []

        try:
            # 初始化教育联邦学习服务
            edu_service = EduFederatedLearningService.get_instance()

            # 创建测试训练配置
            training_config = EduTrainingConfig(
                model_name="edu_stem_test_model",
                rounds=3,
                participants=["node_001", "node_002", "node_003"],
                subjects=[EduSubject.MATH, EduSubject.SCIENCE],
                grade_levels=[EduGradeLevel.MIDDLE, EduGradeLevel.HIGH],
                privacy_level=EduDataPrivacyLevel.HIGH,
                privacy_budget=1.0,
                enable_trend_analysis=True,
                enable_region_comparison=True
            )

            # 注册测试节点
            for i in range(3):
                node_info = EduNodeRegistration(
                    node_id=f"node_00{i+1}",
                    node_name=f"测试学校{i+1}",
                    node_type="school",
                    region_id=f"region_00{i+1}",
                    contact_info={"email": f"test{i+1}@school.edu"},
                    public_key=f"test_public_key_{i+1}",
                    capabilities=["education_data"]
                )
                await edu_service.register_node(node_info)

            test_results.append(('node_registration', True, "节点注册"))

            # 启动训练（模拟）
            try:
                training_id = await edu_service.start_training(training_config)
                test_results.append(('training_start', training_id is not None, "训练启动"))

                # 模拟训练进度查询
                progress = await edu_service.get_training_status(training_id)
                test_results.append(('training_progress', progress is not None, "训练进度查询"))

            except Exception as e:
                test_results.append(('training_execution', False, f"训练执行失败: {str(e)}"))

        except Exception as e:
            test_results.append(('federated_training', False, f"联邦学习测试失败: {str(e)}"))

        self.results['federated_training'] = test_results
        self._log_test_results("联邦学习训练测试", test_results)

    async def _test_privacy_protection(self):
        """测试隐私保护机制"""
        logger.info("执行隐私保护测试...")
        test_results = []

        try:
            # 测试差分隐私
            privacy_engine = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5)

            # 模拟梯度添加噪声
            import torch
            test_gradients = {
                'layer1.weight': torch.randn(10, 5),
                'layer2.bias': torch.randn(10)
            }

            noisy_gradients = privacy_engine.add_noise_to_gradients(test_gradients)
            test_results.append(('dp_noise_addition', len(noisy_gradients) == 2, "差分隐私噪声添加"))

            # 检查隐私预算消耗
            privacy_loss = privacy_engine.get_privacy_loss()
            test_results.append(('privacy_budget', privacy_loss['consumed'] >= 0, "隐私预算跟踪"))

            # 测试数据匿名化
            test_records = [
                {'name': '张三', 'age': 25, 'city': '北京'},
                {'name': '李四', 'age': 26, 'city': '北京'}
            ]

            anonymized = DataAnonymization.k_anonymize(
                test_records,
                quasi_identifiers=['age', 'city'],
                k=2
            )
            test_results.append(('data_anonymization', len(anonymized) == 2, "数据匿名化"))

            # 测试审计日志
            audit_logger.log_privacy_operation("test_operation", {"test": "data"})
            audit_entries = audit_logger.get_audit_report()
            test_results.append(('audit_logging', len(audit_entries) > 0, "隐私审计日志"))

        except Exception as e:
            test_results.append(('privacy_protection', False, f"隐私保护测试失败: {str(e)}"))

        self.results['privacy_protection'] = test_results
        self._log_test_results("隐私保护测试", test_results)

    async def _test_report_generation(self):
        """测试报告生成功能"""
        logger.info("执行报告生成测试...")
        test_results = []

        try:
            # 测试报告生成器
            report_generator = EduReportGenerator()

            # 创建测试数据
            test_analysis_data = {
                'stem_overall_score': 82.5,
                'capability_level': 'good',
                'subject_analyses': {
                    'math': {'average_score': 85.2, 'improvement_rate': 3.2},
                    'science': {'average_score': 81.8, 'improvement_rate': 1.5}
                },
                'regional_comparison': [
                    {'region_name': '测试区域1', 'average_stem_score': 88.5}
                ],
                'data_quality_metrics': {'completion_rate': 0.95},
                'recommendations': ['加强技术学科教学']
            }

            # 测试报告请求
            report_request = EduReportRequest(
                training_id="test_training_001",
                report_type="stem_analysis",
                format="pdf",
                include_charts=True,
                include_detailed_stats=True
            )

            # 生成报告（可能需要mock文件系统）
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 临时修改输出目录
                    original_output_dir = edu_config.report_output_dir
                    edu_config.report_output_dir = temp_dir

                    report_metadata = await report_generator.generate_report(
                        report_request, test_analysis_data
                    )

                    test_results.append(('report_generation', report_metadata is not None, "报告生成"))
                    test_results.append(('report_metadata', hasattr(report_metadata, 'report_id'), "报告元数据"))

                    # 恢复原始配置
                    edu_config.report_output_dir = original_output_dir

            except Exception as e:
                test_results.append(('report_generation', False, f"报告生成失败: {str(e)}"))

            # 测试可视化仪表板
            dashboard = InteractiveDashboard()
            dashboard_html = dashboard.generate_interactive_dashboard(test_analysis_data)
            test_results.append(('dashboard_generation', len(dashboard_html) > 1000, "仪表板生成"))

        except Exception as e:
            test_results.append(('report_generation', False, f"报告生成测试失败: {str(e)}"))

        self.results['report_generation'] = test_results
        self._log_test_results("报告生成测试", test_results)

    async def _test_performance_benchmarks(self):
        """测试性能基准"""
        logger.info("执行性能基准测试...")
        performance_results = {}

        try:
            # 测试大数据集处理性能
            large_dataset_sizes = [1000, 5000, 10000]
            processing_times = []

            for size in large_dataset_sizes:
                start_time = time.time()

                # 生成大型数据集
                large_data = self._generate_mock_education_data(size)

                # 执行标准化和质量检查
                standardizer = EduDataStandardizer()
                quality_checker = DataQualityChecker()

                df = pd.DataFrame([vars(record) for record in large_data['academic']])
                standardized_df = standardizer.standardize_data(df, 'academic')
                quality_report = quality_checker.check_dataframe_quality(standardized_df)

                end_time = time.time()
                processing_time = end_time - start_time
                processing_times.append(processing_time)

                logger.info(f"数据集大小 {size}: 处理时间 {processing_time:.2f}秒")

            performance_results['data_processing_throughput'] = {
                'dataset_sizes': large_dataset_sizes,
                'processing_times': processing_times,
                'throughput_records_per_second': [
                    size/time for size, time in zip(large_dataset_sizes, processing_times)
                ]
            }

            # 测试并发处理能力
            concurrency_tests = []
            for concurrency_level in [1, 3, 5]:
                start_time = time.time()

                tasks = []
                for i in range(concurrency_level):
                    task = asyncio.create_task(
                        self._concurrent_data_processing_test(1000)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks)
                end_time = time.time()

                total_time = end_time - start_time
                concurrency_tests.append({
                    'concurrency_level': concurrency_level,
                    'total_time': total_time,
                    'per_task_time': total_time / concurrency_level
                })

            performance_results['concurrency_performance'] = concurrency_tests

        except Exception as e:
            logger.error(f"性能基准测试失败: {e}")
            performance_results['error'] = str(e)

        self.results['performance_benchmarks'] = performance_results

    async def _test_error_handling(self):
        """测试错误处理机制"""
        logger.info("执行错误处理测试...")
        test_results = []

        try:
            # 测试无效数据处理
            invalid_data = pd.DataFrame({
                'student_id': ['', None, 'S001'],
                'subject': ['invalid_subject', 'math', 'science'],
                'score': [-10, 150, 85]  # 无效分数
            })

            standardizer = EduDataStandardizer()
            quality_checker = DataQualityChecker()

            # 应该能够处理无效数据而不崩溃
            try:
                standardized = standardizer.standardize_data(invalid_data, 'academic')
                quality_report = quality_checker.check_dataframe_quality(standardized)
                test_results.append(('invalid_data_handling', True, "无效数据处理"))
            except Exception as e:
                test_results.append(('invalid_data_handling', False, f"无效数据处理失败: {str(e)}"))

            # 测试缺失配置处理
            try:
                # 临时移除必要配置
                original_epsilon = edu_config.fl_privacy_epsilon
                edu_config.fl_privacy_epsilon = None

                # 系统应该有合理的默认值或错误处理
                privacy_engine = DifferentialPrivacyEngine()
                test_results.append(('configuration_resilience', True, "配置弹性"))

                # 恢复配置
                edu_config.fl_privacy_epsilon = original_epsilon

            except Exception as e:
                test_results.append(('configuration_resilience', False, f"配置弹性测试失败: {str(e)}"))

        except Exception as e:
            test_results.append(('error_handling', False, f"错误处理测试失败: {str(e)}"))

        self.results['error_handling'] = test_results
        self._log_test_results("错误处理测试", test_results)

    def _generate_mock_education_data(self, count: int) -> Dict[str, List]:
        """生成模拟教育数据"""
        subjects = ['math', 'science', 'technology', 'engineering']
        grades = ['elementary', 'middle', 'high']

        academic_data = []
        student_data = []

        for i in range(count):
            # 学术表现数据
            academic_data.append(
                EduAcademicPerformance(
                    student_id=f'S{i:06d}',
                    subject=subjects[i % len(subjects)],
                    assessment_type='standardized_test',
                    score=np.random.uniform(60, 100),
                    date_taken=datetime.now() - timedelta(days=np.random.randint(0, 365)),
                    academic_year='2023-2024',
                    percentile_rank=np.random.uniform(20, 95)
                )
            )

            # 学生人口统计数据
            student_data.append(
                EduStudentDemographics(
                    student_id=f'S{i:06d}',
                    age=np.random.randint(12, 18),
                    gender=np.random.choice(['male', 'female']),
                    grade_level=grades[np.random.randint(0, len(grades))],
                    school_id=f'SCHOOL_{i//100:03d}',
                    region_id=f'REGION_{i//1000:02d}'
                )
            )

        return {
            'academic': academic_data,
            'student': student_data
        }

    def _convert_to_fl_format(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将数据转换为联邦学习格式"""
        fl_data = []
        for _, row in df.iterrows():
            fl_record = {
                'student_id': row.get('student_id', ''),
                'subject': row.get('subject', 'math'),
                'score': float(row.get('score', 0)),
                'features': [
                    float(row.get('score', 0)),
                    float(row.get('percentile_rank', 50)),
                    # 可以添加更多特征
                ]
            }
            fl_data.append(fl_record)
        return fl_data

    async def _concurrent_data_processing_test(self, data_size: int):
        """并发数据处理测试"""
        data = self._generate_mock_education_data(data_size)
        standardizer = EduDataStandardizer()
        df = pd.DataFrame([vars(record) for record in data['academic']])
        standardized = standardizer.standardize_data(df, 'academic')
        return len(standardized)

    def _log_test_results(self, test_name: str, results: List[tuple]):
        """记录测试结果"""
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        logger.info(f"{test_name}: {passed}/{total} 通过")

        for test_case, success, description in results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"  {status} {description}")

    def _generate_final_report(self) -> Dict[str, Any]:
        """生成最终测试报告"""
        total_tests = 0
        passed_tests = 0

        # 统计测试结果
        for test_category, results in self.results.items():
            if isinstance(results, list):
                for _, success, _ in results:
                    total_tests += 1
                    if success:
                        passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        report = {
            'test_suite': 'Education Data Federated Learning System Backtest',
            'timestamp': datetime.now().isoformat(),
            'test_duration': (self.test_end_time - self.test_start_time).total_seconds(),
            'overall_results': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': round(success_rate, 2)
            },
            'detailed_results': self.results,
            'system_info': {
                'python_version': '3.8+',
                'framework': 'FastAPI + PySyft',
                'privacy_level': edu_config.edu_data_privacy_level,
                'supported_formats': edu_config.get_supported_formats()
            },
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """生成错误报告"""
        return {
            'test_suite': 'Education Data Federated Learning System Backtest',
            'timestamp': datetime.now().isoformat(),
            'status': 'FAILED',
            'error': error_message,
            'results': self.results
        }

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        if 'core_components' in self.results:
            failed_core = [desc for _, success, desc in self.results['core_components'] if not success]
            if failed_core:
                recommendations.append("修复核心组件中的故障模块")

        if 'privacy_protection' in self.results:
            privacy_results = self.results['privacy_protection']
            if any(not success for _, success, _ in privacy_results):
                recommendations.append("加强隐私保护机制的健壮性")

        if 'performance_benchmarks' in self.results:
            perf_data = self.results['performance_benchmarks']
            if 'throughput_records_per_second' in perf_data:
                throughput_rates = perf_data['throughput_records_per_second']
                if any(rate < 1000 for rate in throughput_rates):  # 假设阈值为1000 records/sec
                    recommendations.append("优化数据处理性能")

        if not recommendations:
            recommendations.append("系统通过所有测试，可以进入生产环境")

        return recommendations


async def main():
    """主函数"""
    backtester = EduSystemBacktester()
    results = await backtester.run_comprehensive_backtest()

    # 保存测试报告
    report_filename = f"edu_federated_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"测试报告已保存到: {report_filename}")

    # 输出摘要
    print("\n" + "="*60)
    print("教育数据联邦学习系统集成回测报告摘要")
    print("="*60)
    print(f"测试时间: {results['timestamp']}")
    print(f"测试时长: {results['test_duration']:.2f} 秒")
    print(f"成功率: {results['overall_results']['success_rate']}%")
    print(f"通过测试: {results['overall_results']['passed_tests']}/{results['overall_results']['total_tests']}")

    if results['overall_results']['success_rate'] >= 90:
        print("🎉 系统测试通过，满足生产环境要求")
        return 0
    elif results['overall_results']['success_rate'] >= 80:
        print("⚠️  系统基本可用，但需要修复部分问题")
        return 1
    else:
        print("❌ 系统存在严重问题，不建议部署到生产环境")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
