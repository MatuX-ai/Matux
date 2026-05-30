"""
硬件认证系统演示脚本
展示核心功能的使用方法
"""

from datetime import datetime
from models.hardware_certification import (
    CertificationRequest,
    TestResult,
    TestCategory,
    CertificationStatus,
    BadgeConfig,
    BadgeStyle
)
from services.hardware_certification_service import hardware_certification_service
from services.badge_generator import badge_generator


def demo_hardware_certification():
    """演示硬件认证流程"""
    print("🔧 硬件认证系统演示")
    print("=" * 50)
    
    # 创建示例测试结果
    test_results = [
        TestResult(
            test_id="func_boot_001",
            category=TestCategory.FUNCTIONALITY,
            name="Boot Sequence Test",
            description="验证设备启动序列正确性",
            status="pass",
            duration_ms=150,
            timestamp=datetime.utcnow()
        ),
        TestResult(
            test_id="func_com_001",
            category=TestCategory.FUNCTIONALITY,
            name="Serial Communication Test",
            description="测试串口通信功能",
            status="pass",
            duration_ms=80,
            timestamp=datetime.utcnow()
        ),
        TestResult(
            test_id="perf_speed_001",
            category=TestCategory.PERFORMANCE,
            name="Processing Speed Test",
            description="测量处理速度性能",
            status="pass",
            duration_ms=200,
            timestamp=datetime.utcnow()
        ),
        TestResult(
            test_id="perf_memory_001",
            category=TestCategory.PERFORMANCE,
            name="Memory Usage Test",
            description="测试内存使用情况",
            status="pass",
            duration_ms=120,
            timestamp=datetime.utcnow()
        ),
        TestResult(
            test_id="comp_usb_001",
            category=TestCategory.COMPATIBILITY,
            name="USB Compatibility Test",
            description="验证USB兼容性",
            status="pass",
            duration_ms=90,
            timestamp=datetime.utcnow()
        )
    ]
    
    # 创建认证请求
    request = CertificationRequest(
        hw_id="HW_DEMO_2024",
        device_info={
            "vendor": "iMato Demo",
            "model": "SmartDevice-Demo",
            "serial_number": "DEMO2024001"
        },
        test_results=test_results,
        firmware_version="2.0.1",
        hardware_version="1.1",
        submitted_by="demo_user"
    )
    
    print("📋 认证请求信息:")
    print(f"  硬件ID: {request.hw_id}")
    print(f"  设备型号: {request.device_info['model']}")
    print(f"  固件版本: {request.firmware_version}")
    print(f"  测试数量: {len(request.test_results)}")
    print()
    
    # 执行认证
    print("🚀 执行硬件认证...")
    response = hardware_certification_service.verify_certification(request)
    
    print("✅ 认证结果:")
    print(f"  状态: {response.status.value}")
    print(f"  证书ID: {response.certificate_id}")
    print(f"  徽章URL: {response.badge_url}")
    print(f"  认证时间: {response.certified_at}")
    print(f"  失败测试数: {len(response.failed_tests)}")
    print()
    
    # 生成不同样式的徽章
    print("🎨 生成认证徽章...")
    config_standard = BadgeConfig(
        style=BadgeStyle.STANDARD,
        show_timestamp=True,
        show_version=True
    )
    
    config_compact = BadgeConfig(
        style=BadgeStyle.COMPACT,
        show_timestamp=False,
        show_version=False
    )
    
    config_detailed = BadgeConfig(
        style=BadgeStyle.DETAILED,
        show_timestamp=True,
        show_version=True
    )
    
    # 生成标准样式徽章
    print("1. 标准样式徽章:")
    standard_badge = badge_generator.generate_badge_svg(
        hw_id=response.hw_id,
        status=response.status,
        config=config_standard,
        firmware_version=request.firmware_version,
        certified_at=response.certified_at
    )
    print(f"   SVG长度: {len(standard_badge)} 字符")
    print(f"   内容预览: {standard_badge[:100]}...")
    print()
    
    # 生成紧凑样式徽章
    print("2. 紧凑样式徽章:")
    compact_badge = badge_generator.generate_badge_svg(
        hw_id=response.hw_id,
        status=response.status,
        config=config_compact
    )
    print(f"   SVG长度: {len(compact_badge)} 字符")
    print(f"   内容预览: {compact_badge[:100]}...")
    print()
    
    # 生成详细样式徽章
    print("3. 详细样式徽章:")
    detailed_badge = badge_generator.generate_badge_svg(
        hw_id=response.hw_id,
        status=response.status,
        config=config_detailed,
        firmware_version=request.firmware_version,
        certified_at=response.certified_at
    )
    print(f"   SVG长度: {len(detailed_badge)} 字符")
    print(f"   内容预览: {detailed_badge[:100]}...")
    print()
    
    # 展示认证统计
    print("📊 认证统计信息:")
    stats = hardware_certification_service.get_all_certifications()
    print(f"  总认证数: {len(stats)}")
    
    # 模拟失败认证场景
    print("\n🧪 失败认证演示:")
    failed_test_results = [
        TestResult(
            test_id="func_boot_001",
            category=TestCategory.FUNCTIONALITY,
            name="Boot Sequence Test",
            description="验证设备启动序列正确性",
            status="fail",  # 故意失败
            error_message="Boot timeout",
            duration_ms=5000,
            timestamp=datetime.utcnow()
        ),
        TestResult(
            test_id="func_com_001",
            category=TestCategory.FUNCTIONALITY,
            name="Serial Communication Test",
            description="测试串口通信功能",
            status="pass",
            duration_ms=80,
            timestamp=datetime.utcnow()
        )
    ]
    
    failed_request = CertificationRequest(
        hw_id="HW_FAIL_DEMO",
        device_info={"vendor": "TestVendor", "model": "FailureTest"},
        test_results=failed_test_results,
        firmware_version="1.0.0",
        hardware_version="1.0",
        submitted_by="demo_user"
    )
    
    failed_response = hardware_certification_service.verify_certification(failed_request)
    print(f"  认证状态: {failed_response.status.value}")
    print(f"  失败原因: 通过率不足或关键测试失败")
    print(f"  失败测试数: {len(failed_response.failed_tests)}")


if __name__ == "__main__":
    demo_hardware_certification()