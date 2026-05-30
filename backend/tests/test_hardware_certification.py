"""
硬件认证系统测试
"""

from datetime import datetime

import pytest

from models.hardware_certification import (
    BadgeConfig,
    BadgeStyle,
    CertificationRequest,
    CertificationStatus,
    TestCategory,
    TestResult,
)
from services.badge_generator import BadgeGenerator
from services.hardware_certification_service import HardwareCertificationService


class TestHardwareCertificationService:
    """硬件认证服务测试"""

    def setup_method(self):
        """测试初始化"""
        self.service = HardwareCertificationService()

    def test_analyze_test_results_empty(self):
        """测试空测试结果分析"""
        result = self.service._analyze_test_results([])
        assert result["summary"]["total"] == 0
        assert result["summary"]["pass_rate"] == 0
        assert len(result["failed_tests"]) == 0

    def test_analyze_test_results_mixed(self):
        """测试混合测试结果分析"""
        test_results = [
            TestResult(
                test_id="test1",
                category=TestCategory.FUNCTIONALITY,
                name="Basic Function Test",
                description="Test basic functionality",
                status="pass",
                duration_ms=100,
                timestamp=datetime.utcnow(),
            ),
            TestResult(
                test_id="test2",
                category=TestCategory.PERFORMANCE,
                name="Performance Test",
                description="Test performance",
                status="fail",
                error_message="Timeout occurred",
                duration_ms=2000,
                timestamp=datetime.utcnow(),
            ),
            TestResult(
                test_id="test3",
                category=TestCategory.COMPATIBILITY,
                name="Compatibility Test",
                description="Test compatibility",
                status="pass",
                duration_ms=150,
                timestamp=datetime.utcnow(),
            ),
        ]

        result = self.service._analyze_test_results(test_results)

        assert result["summary"]["total"] == 3
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 1
        assert result["summary"]["pass_rate"] == 2 / 3
        assert len(result["failed_tests"]) == 1
        assert result["failed_tests"][0].test_id == "test2"

    def test_is_critical_test(self):
        """测试关键测试判断"""
        # 关键测试
        critical_test = TestResult(
            test_id="critical1",
            category=TestCategory.FUNCTIONALITY,
            name="Boot Sequence Test",
            description="Test boot sequence",
            status="fail",
            timestamp=datetime.utcnow(),
        )
        assert self.service._is_critical_test(critical_test) == True

        # 非关键测试
        normal_test = TestResult(
            test_id="normal1",
            category=TestCategory.PERFORMANCE,
            name="Speed Test",
            description="Test speed performance",
            status="fail",
            timestamp=datetime.utcnow(),
        )
        assert self.service._is_critical_test(normal_test) == False

    def test_verify_certification_success(self):
        """测试认证成功场景"""
        request = CertificationRequest(
            hw_id="HW123456789",
            device_info={"vendor": "TestVendor", "model": "TestModel"},
            test_results=[
                TestResult(
                    test_id="func1",
                    category=TestCategory.FUNCTIONALITY,
                    name="Basic Function Test",
                    description="Test basic functionality",
                    status="pass",
                    duration_ms=100,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="perf1",
                    category=TestCategory.PERFORMANCE,
                    name="Performance Test",
                    description="Test performance",
                    status="pass",
                    duration_ms=200,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="comp1",
                    category=TestCategory.COMPATIBILITY,
                    name="Compatibility Test",
                    description="Test compatibility",
                    status="pass",
                    duration_ms=150,
                    timestamp=datetime.utcnow(),
                ),
            ],
            firmware_version="1.0.0",
            hardware_version="1.0",
            submitted_by="test_user",
        )

        response = self.service.verify_certification(request)

        assert response.hw_id == "HW123456789"
        assert response.status == CertificationStatus.CERTIFIED
        assert response.badge_url is not None
        assert response.certificate_id is not None
        assert response.certified_at is not None
        assert len(response.failed_tests) == 0

    def test_verify_certification_failure_low_pass_rate(self):
        """测试低通过率导致认证失败"""
        request = CertificationRequest(
            hw_id="HW987654321",
            device_info={"vendor": "TestVendor", "model": "TestModel"},
            test_results=[
                TestResult(
                    test_id="func1",
                    category=TestCategory.FUNCTIONALITY,
                    name="Basic Function Test",
                    description="Test basic functionality",
                    status="pass",
                    duration_ms=100,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="func2",
                    category=TestCategory.FUNCTIONALITY,
                    name="Advanced Function Test",
                    description="Test advanced functionality",
                    status="fail",
                    error_message="Function not implemented",
                    duration_ms=200,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="func3",
                    category=TestCategory.FUNCTIONALITY,
                    name="Edge Case Test",
                    description="Test edge cases",
                    status="fail",
                    error_message="Unexpected behavior",
                    duration_ms=150,
                    timestamp=datetime.utcnow(),
                ),
            ],
            firmware_version="1.0.0",
            hardware_version="1.0",
            submitted_by="test_user",
        )

        response = self.service.verify_certification(request)

        assert response.status == CertificationStatus.FAILED
        assert response.badge_url is None
        assert response.certificate_id is None

    def test_verify_certification_failure_missing_categories(self):
        """测试缺少必要测试类别导致认证失败"""
        request = CertificationRequest(
            hw_id="HW111111111",
            device_info={"vendor": "TestVendor", "model": "TestModel"},
            test_results=[
                TestResult(
                    test_id="func1",
                    category=TestCategory.FUNCTIONALITY,
                    name="Basic Function Test",
                    description="Test basic functionality",
                    status="pass",
                    duration_ms=100,
                    timestamp=datetime.utcnow(),
                )
                # 缺少 PERFORMANCE 和 COMPATIBILITY 类别
            ],
            firmware_version="1.0.0",
            hardware_version="1.0",
            submitted_by="test_user",
        )

        response = self.service.verify_certification(request)

        assert response.status == CertificationStatus.FAILED

    def test_is_certified(self):
        """测试认证状态查询"""
        # 先进行一次成功的认证
        request = CertificationRequest(
            hw_id="HW_CERT_TEST",
            device_info={"vendor": "TestVendor", "model": "TestModel"},
            test_results=[
                TestResult(
                    test_id="func1",
                    category=TestCategory.FUNCTIONALITY,
                    name="Basic Function Test",
                    description="Test basic functionality",
                    status="pass",
                    duration_ms=100,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="perf1",
                    category=TestCategory.PERFORMANCE,
                    name="Performance Test",
                    description="Test performance",
                    status="pass",
                    duration_ms=200,
                    timestamp=datetime.utcnow(),
                ),
                TestResult(
                    test_id="comp1",
                    category=TestCategory.COMPATIBILITY,
                    name="Compatibility Test",
                    description="Test compatibility",
                    status="pass",
                    duration_ms=150,
                    timestamp=datetime.utcnow(),
                ),
            ],
            firmware_version="1.0.0",
            hardware_version="1.0",
            submitted_by="test_user",
        )

        # 认证应该成功
        response = self.service.verify_certification(request)
        assert response.status == CertificationStatus.CERTIFIED

        # 查询认证状态应该返回True
        assert self.service.is_certified("HW_CERT_TEST") == True

        # 查询不存在的硬件应该返回False
        assert self.service.is_certified("NON_EXISTENT_HW") == False


class TestBadgeGenerator:
    """徽章生成器测试"""

    def setup_method(self):
        """测试初始化"""
        self.generator = BadgeGenerator()

    def test_generate_standard_badge(self):
        """测试标准徽章生成"""
        config = BadgeConfig(
            style=BadgeStyle.STANDARD, show_timestamp=True, show_version=True
        )

        svg_content = self.generator.generate_badge_svg(
            hw_id="HW123456789",
            status=CertificationStatus.CERTIFIED,
            config=config,
            firmware_version="1.0.0",
            certified_at=datetime(2024, 1, 15),
        )

        assert "<svg" in svg_content
        assert "CERTIFIED" in svg_content
        assert "HW:HW12345678" in svg_content
        assert "2024-01-15" in svg_content

    def test_generate_compact_badge(self):
        """测试紧凑徽章生成"""
        config = BadgeConfig(
            style=BadgeStyle.COMPACT, show_timestamp=False, show_version=False
        )

        svg_content = self.generator.generate_badge_svg(
            hw_id="HW123456789", status=CertificationStatus.FAILED, config=config
        )

        assert "<svg" in svg_content
        assert "FAILED" in svg_content
        assert "HW:HW12345678" not in svg_content  # 紧凑模式不应该显示硬件ID

    def test_generate_detailed_badge(self):
        """测试详细徽章生成"""
        config = BadgeConfig(
            style=BadgeStyle.DETAILED, show_timestamp=True, show_version=True
        )

        svg_content = self.generator.generate_badge_svg(
            hw_id="HW123456789ABCDEF",
            status=CertificationStatus.PENDING,
            config=config,
            firmware_version="2.1.3",
            certified_at=datetime(2024, 3, 20),
        )

        assert "<svg" in svg_content
        assert "Hardware: HW123456789A" in svg_content  # 截断显示
        assert "Firmware: v2.1.3" in svg_content
        assert "Status: PENDING" in svg_content
        assert "Date: 2024-03-20" in svg_content

    def test_generate_error_badge(self):
        """测试错误徽章生成"""
        svg_content = self.generator._generate_error_badge("Test Error")

        assert "<svg" in svg_content
        assert "ERROR" in svg_content
        assert "#F44336" in svg_content  # 错误颜色

    def test_calculate_text_width(self):
        """测试文本宽度计算"""
        width1 = self.generator._calculate_text_width("Hello")
        width2 = self.generator._calculate_text_width("你好世界")
        width3 = self.generator._calculate_text_width("HW123456789")

        assert isinstance(width1, int)
        assert isinstance(width2, int)
        assert isinstance(width3, int)
        assert width2 > width1  # 中文字符应该比英文宽
        assert width3 > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
