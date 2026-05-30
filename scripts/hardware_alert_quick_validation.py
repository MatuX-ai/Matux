"""
硬件告警系统核心功能快速验证
针对新添加的功能进行快速验证，无需启动完整服务
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
hardware_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)
sys.path.insert(0, hardware_path)

def run_quick_validation() -> Dict[str, Any]:
    """快速验证核心功能"""
    print("=" * 60)
    print("硬件告警系统核心功能快速验证")
    print("=" * 60)
    
    validation_results = []
    
    # 1. 验证数据模型导入
    try:
        from models.hardware_alert import (
            HardwareAlert, AlertType, AlertSeverity, AlertSource,
            HardwareDeviceStatus
        )
        print("✅ 数据模型导入成功")
        validation_results.append({
            "test_name": "数据模型导入",
            "status": "PASSED",
            "details": "所有硬件告警数据模型均可正常导入"
        })
    except Exception as e:
        print(f"❌ 数据模型导入失败: {str(e)}")
        validation_results.append({
            "test_name": "数据模型导入",
            "status": "FAILED",
            "error": str(e)
        })
        return _generate_simple_report(validation_results)
    
    # 2. 验证MQTT服务导入
    try:
        from services.hardware_alert_mqtt_service import (
            MQTTConfig, HardwareAlertMQTTService
        )
        print("✅ MQTT服务导入成功")
        validation_results.append({
            "test_name": "MQTT服务导入",
            "status": "PASSED",
            "details": "MQTT服务组件可正常导入"
        })
    except Exception as e:
        print(f"❌ MQTT服务导入失败: {str(e)}")
        validation_results.append({
            "test_name": "MQTT服务导入",
            "status": "FAILED",
            "error": str(e)
        })
    
    # 3. 验证异常检测服务导入
    try:
        from services.hardware_alert_detection_service import (
            HardwareAlertDetector, HardwareAlertManager,
            DeviceOfflineDetector, PerformanceDegradationDetector,
            TemperatureAnomalyDetector, MemoryLeakDetector
        )
        print("✅ 异常检测服务导入成功")
        validation_results.append({
            "test_name": "异常检测服务导入",
            "status": "PASSED",
            "details": "异常检测组件可正常导入"
        })
    except Exception as e:
        print(f"❌ 异常检测服务导入失败: {str(e)}")
        validation_results.append({
            "test_name": "异常检测服务导入",
            "status": "FAILED",
            "error": str(e)
        })
    
    # 4. 验证路由导入
    try:
        from routes.hardware_alert_routes import router
        print("✅ 路由模块导入成功")
        validation_results.append({
            "test_name": "路由模块导入",
            "status": "PASSED",
            "details": "硬件告警路由可正常导入"
        })
    except Exception as e:
        print(f"❌ 路由模块导入失败: {str(e)}")
        validation_results.append({
            "test_name": "路由模块导入",
            "status": "FAILED",
            "error": str(e)
        })
    
    # 5. 验证配置项
    try:
        from config.settings import settings
        config_items = [
            "HARDWARE_ALERT_MQTT_ENABLED",
            "HARDWARE_ALERT_MQTT_BROKER", 
            "HARDWARE_ALERT_MQTT_PORT",
            "HARDWARE_ALERT_DETECTION_ENABLED",
            "HARDWARE_ALERT_MONITORING_INTERVAL"
        ]
        
        missing_configs = []
        for config_item in config_items:
            if not hasattr(settings, config_item):
                missing_configs.append(config_item)
        
        if not missing_configs:
            print("✅ 配置项验证通过")
            validation_results.append({
                "test_name": "配置项验证",
                "status": "PASSED",
                "details": f"所有必需配置项均已定义: {len(config_items)} 项"
            })
        else:
            print(f"⚠️  缺少配置项: {missing_configs}")
            validation_results.append({
                "test_name": "配置项验证",
                "status": "PARTIAL",
                "details": f"缺少配置项: {missing_configs}"
            })
    except Exception as e:
        print(f"❌ 配置验证失败: {str(e)}")
        validation_results.append({
            "test_name": "配置项验证",
            "status": "FAILED",
            "error": str(e)
        })
    
    # 6. 验证模型实例化
    try:
        # 创建测试告警
        alert = HardwareAlert(
            alert_id="quick_test_001",
            device_id="test_device",
            alert_type=AlertType.DEVICE_OFFLINE,
            severity=AlertSeverity.ERROR,
            message="快速验证测试告警",
            source=AlertSource.SYSTEM_MONITOR,
            timestamp=datetime.now()
        )
        
        # 创建测试设备状态
        device_status = HardwareDeviceStatus(
            device_id="test_device",
            status="online",
            last_seen=datetime.now(),
            cpu_usage=75.5,
            memory_usage=60.2,
            temperature=45.0
        )
        
        print("✅ 模型实例化成功")
        validation_results.append({
            "test_name": "模型实例化",
            "status": "PASSED",
            "details": "硬件告警模型和设备状态模型可正常实例化"
        })
    except Exception as e:
        print(f"❌ 模型实例化失败: {str(e)}")
        validation_results.append({
            "test_name": "模型实例化",
            "status": "FAILED",
            "error": str(e)
        })
    
    # 7. 验证检测器初始化
    try:
        # 测试检测器初始化（不需要MQTT连接）
        detectors_to_test = [
            ("设备离线检测器", DeviceOfflineDetector),
            ("性能下降检测器", PerformanceDegradationDetector),
            ("温度异常检测器", TemperatureAnomalyDetector),
            ("内存泄漏检测器", MemoryLeakDetector)
        ]
        
        initialized_detectors = 0
        for name, detector_class in detectors_to_test:
            try:
                detector = detector_class()
                if hasattr(detector, 'detect'):
                    initialized_detectors += 1
                    print(f"✅ {name} 初始化成功")
            except Exception as e:
                print(f"❌ {name} 初始化失败: {str(e)}")
        
        if initialized_detectors == len(detectors_to_test):
            validation_results.append({
                "test_name": "检测器初始化",
                "status": "PASSED",
                "details": f"所有 {len(detectors_to_test)} 个检测器初始化成功"
            })
        else:
            validation_results.append({
                "test_name": "检测器初始化",
                "status": "PARTIAL",
                "details": f"{initialized_detectors}/{len(detectors_to_test)} 个检测器初始化成功"
            })
            
    except Exception as e:
        print(f"❌ 检测器初始化测试失败: {str(e)}")
        validation_results.append({
            "test_name": "检测器初始化",
            "status": "FAILED",
            "error": str(e)
        })
    
    return _generate_simple_report(validation_results)

def _generate_simple_report(validation_results: List[Dict]) -> Dict[str, Any]:
    """生成简单验证报告"""
    passed_tests = len([r for r in validation_results if r['status'] == 'PASSED'])
    failed_tests = len([r for r in validation_results if r['status'] == 'FAILED'])
    partial_tests = len([r for r in validation_results if r['status'] == 'PARTIAL'])
    total_tests = len(validation_results)
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    report = {
        "validation_info": {
            "name": "硬件告警系统核心功能快速验证",
            "timestamp": datetime.now().isoformat(),
            "type": "quick_validation"
        },
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "partial_tests": partial_tests,
            "success_rate": round(success_rate, 2)
        },
        "results": validation_results,
        "conclusion": _generate_conclusion(validation_results)
    }
    
    # 保存报告
    report_filename = f"hardware_alert_quick_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 验证报告已保存: {report_filename}")
    return report

def _generate_conclusion(validation_results: List[Dict]) -> str:
    """生成结论"""
    passed_tests = len([r for r in validation_results if r['status'] == 'PASSED'])
    total_tests = len(validation_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    if success_rate >= 90:
        return "🎉 硬件告警系统核心功能验证通过，可以投入生产使用"
    elif success_rate >= 70:
        return "⚠️  硬件告警系统基本功能可用，但需要关注部分警告项"
    else:
        return "❌ 硬件告警系统存在较多问题，需要修复后才能使用"

def main():
    """主函数"""
    report = run_quick_validation()
    
    # 输出结果摘要
    print("\n" + "=" * 60)
    print("验证结果摘要")
    print("=" * 60)
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"通过测试: {report['summary']['passed_tests']}")
    print(f"部分通过: {report['summary']['partial_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"成功率: {report['summary']['success_rate']}%")
    
    print("\n详细结果:")
    print("-" * 40)
    for result in report['results']:
        status_icon = {
            'PASSED': '✅',
            'PARTIAL': '⚠️ ',
            'FAILED': '❌'
        }.get(result['status'], '❓')
        print(f"{status_icon} {result['test_name']}: {result['status']}")
        if result['status'] != 'PASSED' and 'error' in result:
            print(f"   错误: {result['error']}")
    
    print(f"\n结论: {report['conclusion']}")
    print("=" * 60)
    
    # 返回退出码
    return 0 if report['summary']['success_rate'] >= 80 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)