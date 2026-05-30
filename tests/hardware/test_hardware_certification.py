"""
硬件认证系统综合测试

整合了原有多个硬件认证测试文件的功能，提供完整的测试覆盖：
- 硬件认证核心逻辑测试
- 认证流程完整性测试
- 边界条件和异常处理测试
- 性能基准测试

测试范围:
- 认证请求处理
- 测试结果分析
- 证书生成和验证
- 徽章系统集成
- 异常情况处理
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

# 导入数据模型
from models.hardware_certification import (
    CertificationRequest,
    TestResult,
    TestCategory,
    CertificationStatus,
    BadgeConfig,
    BadgeStyle,
)

# 导入服务类
from services.hardware_certification_service import HardwareCertificationService
from services.badge_generator import BadgeGenerator

class TestHardwareCertificationService:
    """硬件认证服务测试类"""
    
    def setup_method(self):
        """测试前置条件"""
        self.service = HardwareCertificationService()
        self.badge_generator = BadgeGenerator()
        
    def teardown_method(self):
        """测试后置清理"""
        pass
    
    def test_analyze_test_results_empty(self):
        """测试空测试结果分析"""
        result = self.service._analyze_test_results([])
        assert result["summary"]["total"] == 0
        assert result["summary"]["passed"] == 0
        assert result["summary"]["failed"] == 0
        assert len(result["by_category"]) == 0
    
    def test_analyze_test_results_single_category(self):
        """测试单类别测试结果分析"""
        test_results = [
            TestResult(
                test_id="test_001",
                category=TestCategory.FUNCTIONALITY,
                name="Basic Function Test",
                passed=True,
                score=95.0,
                execution_time=2.5
            )
        ]
        
        result = self.service._analyze_test_results(test_results)
        
        assert result["summary"]["total"] == 1
        assert result["summary"]["passed"] == 1
        assert result["summary"]["failed"] == 0
        assert len(result["by_category"]) == 1
        assert result["by_category"][TestCategory.FUNCTIONALITY]["count"] == 1
    
    def test_analyze_test_results_multiple_categories(self):
        """测试多类别测试结果分析"""
        test_results = [
            TestResult(
                test_id="test_001",
                category=TestCategory.FUNCTIONALITY,
                name="Function Test 1",
                passed=True,
                score=90.0
            ),
            TestResult(
                test_id="test_002",
                category=TestCategory.PERFORMANCE,
                name="Perf Test 1",
                passed=False,
                score=45.0
            ),
            TestResult(
                test_id="test_003",
                category=TestCategory.SECURITY,
                name="Security Test 1",
                passed=True,
                score=98.0
            )
        ]
        
        result = self.service._analyze_test_results(test_results)
        
        assert result["summary"]["total"] == 3
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 1
        assert len(result["by_category"]) == 3
        
        # 验证各类别统计
        assert result["by_category"][TestCategory.FUNCTIONALITY]["count"] == 1
        assert result["by_category"][TestCategory.PERFORMANCE]["count"] == 1
        assert result["by_category"][TestCategory.SECURITY]["count"] == 1
    
    def test_determine_certification_result_all_passed(self):
        """测试全部通过的认证结果判定"""
        analysis_result = {
            "summary": {
                "total": 5,
                "passed": 5,
                "failed": 0,
                "pass_rate": 100.0
            },
            "by_category": {
                TestCategory.FUNCTIONALITY: {"passed": 2, "total": 2},
                TestCategory.PERFORMANCE: {"passed": 2, "total": 2},
                TestCategory.SECURITY: {"passed": 1, "total": 1}
            }
        }
        
        result = self.service._determine_certification_result(analysis_result)
        
        assert result.status == CertificationStatus.CERTIFIED
        assert result.score == 100.0
        assert result.passed_all_required == True
    
    def test_determine_certification_result_partial_failure(self):
        """测试部分失败的认证结果判定"""
        analysis_result = {
            "summary": {
                "total": 5,
                "passed": 3,
                "failed": 2,
                "pass_rate": 60.0
            },
            "by_category": {
                TestCategory.FUNCTIONALITY: {"passed": 2, "total": 2},
                TestCategory.PERFORMANCE: {"passed": 1, "total": 2},
                TestCategory.SECURITY: {"passed": 0, "total": 1}
            }
        }
        
        result = self.service._determine_certification_result(analysis_result)
        
        assert result.status == CertificationStatus.FAILED
        assert result.score == 60.0
        assert result.passed_all_required == False
    
    def test_determine_certification_result_boundary_condition(self):
        """测试边界条件的认证结果判定"""
        # 测试刚好达到合格线的情况 (80%)
        analysis_result = {
            "summary": {
                "total": 10,
                "passed": 8,
                "failed": 2,
                "pass_rate": 80.0
            },
            "by_category": {}
        }
        
        result = self.service._determine_certification_result(analysis_result)
        assert result.status == CertificationStatus.CERTIFIED
        assert result.score == 80.0
    
    def test_generate_badge_config_success(self):
        """测试成功认证的徽章配置生成"""
        certification_result = Mock()
        certification_result.status = CertificationStatus.CERTIFIED
        certification_result.score = 95.0
        certification_result.device_name = "Test Device Pro"
        certification_result.certification_date = datetime.now()
        
        badge_config = self.service._generate_badge_config(certification_result)
        
        assert isinstance(badge_config, BadgeConfig)
        assert badge_config.style == BadgeStyle.GOLD
        assert badge_config.title == "Test Device Pro"
        assert badge_config.subtitle == "Hardware Certified"
        assert badge_config.score == 95.0
        assert badge_config.show_qr_code == True
    
    def test_generate_badge_config_failure(self):
        """测试失败认证的徽章配置生成"""
        certification_result = Mock()
        certification_result.status = CertificationStatus.FAILED
        certification_result.score = 45.0
        certification_result.device_name = "Test Device Basic"
        certification_result.certification_date = datetime.now()
        
        badge_config = self.service._generate_badge_config(certification_result)
        
        assert isinstance(badge_config, BadgeConfig)
        assert badge_config.style == BadgeStyle.GRAY
        assert badge_config.title == "Test Device Basic"
        assert badge_config.subtitle == "Certification Failed"
        assert badge_config.score == 45.0
        assert badge_config.show_qr_code == False
    
    def test_process_certification_request_complete_flow(self):
        """测试完整的认证请求处理流程"""
        # 准备测试数据
        request = CertificationRequest(
            device_id="device_123",
            device_name="IoT Sensor Model X",
            manufacturer="TestCorp",
            firmware_version="1.0.0",
            test_suite="comprehensive"
        )
        
        # Mock测试执行服务
        with patch('services.hardware_certification_service.TestExecutionService') as mock_test_service:
            mock_test_service_instance = Mock()
            mock_test_service_instance.run_test_suite.return_value = [
                TestResult(
                    test_id="func_001",
                    category=TestCategory.FUNCTIONALITY,
                    name="Sensor Read Test",
                    passed=True,
                    score=92.0,
                    execution_time=1.2
                ),
                TestResult(
                    test_id="perf_001",
                    category=TestCategory.PERFORMANCE,
                    name="Response Time Test",
                    passed=True,
                    score=88.0,
                    execution_time=0.8
                )
            ]
            mock_test_service.return_value = mock_test_service_instance
            
            # 执行认证流程
            result = self.service.process_certification_request(request)
            
            # 验证结果
            assert result.request_id is not None
            assert result.status == CertificationStatus.CERTIFIED
            assert result.score >= 80.0  # 应该通过认证
            assert result.badge_config is not None
            assert result.completion_time is not None
    
    def test_process_certification_request_with_failure(self):
        """测试包含失败测试的认证请求"""
        request = CertificationRequest(
            device_id="device_456",
            device_name="IoT Actuator Model Y",
            manufacturer="ActuateInc",
            firmware_version="2.1.0",
            test_suite="standard"
        )
        
        with patch('services.hardware_certification_service.TestExecutionService') as mock_test_service:
            mock_test_service_instance = Mock()
            mock_test_service_instance.run_test_suite.return_value = [
                TestResult(
                    test_id="func_001",
                    category=TestCategory.FUNCTIONALITY,
                    name="Motor Control Test",
                    passed=True,
                    score=95.0
                ),
                TestResult(
                    test_id="sec_001",
                    category=TestCategory.SECURITY,
                    name="Encryption Test",
                    passed=False,
                    score=30.0
                )
            ]
            mock_test_service.return_value = mock_test_service_instance
            
            result = self.service.process_certification_request(request)
            
            assert result.status == CertificationStatus.FAILED
            assert result.score < 80.0
            assert result.badge_config.style == BadgeStyle.GRAY

class TestBadgeGenerator:
    """徽章生成器测试类"""
    
    def setup_method(self):
        """测试前置条件"""
        self.generator = BadgeGenerator()
    
    def test_generate_svg_badge_gold_style(self):
        """测试金色徽章SVG生成"""
        config = BadgeConfig(
            style=BadgeStyle.GOLD,
            title="Premium Device",
            subtitle="Hardware Certified",
            score=95.0,
            show_qr_code=True
        )
        
        svg_content = self.generator.generate_svg(config)
        
        assert isinstance(svg_content, str)
        assert "<svg" in svg_content
        assert "Premium Device" in svg_content
        assert "95%" in svg_content
        assert "#FFD700" in svg_content  # 金色代码
    
    def test_generate_svg_badge_gray_style(self):
        """测试灰色徽章SVG生成"""
        config = BadgeConfig(
            style=BadgeStyle.GRAY,
            title="Standard Device",
            subtitle="Certification Failed",
            score=45.0,
            show_qr_code=False
        )
        
        svg_content = self.generator.generate_svg(config)
        
        assert isinstance(svg_content, str)
        assert "<svg" in svg_content
        assert "Standard Device" in svg_content
        assert "45%" in svg_content
        assert "#808080" in svg_content  # 灰色代码
    
    def test_validate_badge_config_valid(self):
        """测试有效的徽章配置验证"""
        config = BadgeConfig(
            style=BadgeStyle.SILVER,
            title="Valid Device",
            subtitle="Certified",
            score=85.0
        )
        
        is_valid, errors = self.generator.validate_config(config)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_badge_config_invalid_score(self):
        """测试无效分数的徽章配置验证"""
        config = BadgeConfig(
            style=BadgeStyle.BRONZE,
            title="Invalid Device",
            subtitle="Testing",
            score=150.0  # 无效分数
        )
        
        is_valid, errors = self.generator.validate_config(config)
        assert is_valid == False
        assert len(errors) > 0
        assert any("score" in error.lower() for error in errors)

# 性能测试
class TestHardwareCertificationPerformance:
    """硬件认证性能测试类"""
    
    def setup_method(self):
        """性能测试前置条件"""
        self.service = HardwareCertificationService()
    
    def test_analysis_performance_large_dataset(self):
        """测试大数据集分析性能"""
        import time
        
        # 生成大量测试结果
        large_test_results = []
        for i in range(1000):
            large_test_results.append(
                TestResult(
                    test_id=f"test_{i:04d}",
                    category=TestCategory.FUNCTIONALITY if i % 2 == 0 else TestCategory.PERFORMANCE,
                    name=f"Test {i}",
                    passed=i % 10 != 0,  # 90%通过率
                    score=80.0 + (i % 20),
                    execution_time=0.1 + (i % 5) * 0.1
                )
            )
        
        start_time = time.time()
        result = self.service._analyze_test_results(large_test_results)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证结果正确性
        assert result["summary"]["total"] == 1000
        assert result["summary"]["passed"] == 900
        assert result["summary"]["failed"] == 100
        # 性能要求：处理1000个结果应在1秒内完成
        assert execution_time < 1.0, f"性能测试失败：执行时间 {execution_time:.3f}s 超过阈值"

# 异常处理测试
class TestHardwareCertificationExceptions:
    """硬件认证异常处理测试"""
    
    def setup_method(self):
        """异常测试前置条件"""
        self.service = HardwareCertificationService()
    
    def test_handle_invalid_test_results(self):
        """测试处理无效测试结果"""
        invalid_results = [
            None,  # None值
            "invalid_object",  # 字符串
            TestResult(  # 缺少必需字段
                test_id="",
                category=None,
                name="",
                passed=True,
                score=-1.0  # 无效分数
            )
        ]
        
        # 应该能够处理无效数据而不崩溃
        try:
            result = self.service._analyze_test_results(invalid_results)
            # 即使有无效数据也应该返回合理的分析结果
            assert isinstance(result, dict)
            assert "summary" in result
        except Exception as e:
            # 如果抛出异常，应该是指明的业务异常
            assert "invalid" in str(e).lower() or "validation" in str(e).lower()

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])