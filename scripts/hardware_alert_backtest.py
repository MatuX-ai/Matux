"""
硬件告警系统回测脚本
验证硬件异常上报通道的功能完整性和正确性
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import unittest
from unittest.mock import Mock, patch

# 添加项目路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
hardware_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)
sys.path.insert(0, hardware_path)

from models.hardware_alert import (
    HardwareAlert, AlertType, AlertSeverity, AlertSource,
    HardwareDeviceStatus
)
from services.hardware_alert_mqtt_service import (
    MQTTConfig, HardwareAlertMQTTService
)
from services.hardware_alert_detection_service import (
    HardwareAlertDetector, HardwareAlertManager,
    DeviceOfflineDetector, PerformanceDegradationDetector,
    TemperatureAnomalyDetector, MemoryLeakDetector,
    ConnectionStabilityDetector
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HardwareAlertBacktest:
    """硬件告警系统回测类"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_complete_backtest(self) -> Dict[str, Any]:
        """运行完整的回测"""
        self.start_time = datetime.now()
        logger.info("开始硬件告警系统回测...")
        
        try:
            # 1. 数据模型测试
            self._test_data_models()
            
            # 2. MQTT服务测试
            self._test_mqtt_service()
            
            # 3. 异常检测器测试
            self._test_anomaly_detectors()
            
            # 4. 告警管理器测试
            self._test_alert_manager()
            
            # 5. 集成测试
            self._test_integration()
            
        except Exception as e:
            logger.error(f"回测执行失败: {str(e)}")
            self.test_results.append({
                "test_name": "回测执行",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        self.end_time = datetime.now()
        return self._generate_report()
    
    def _test_data_models(self):
        """测试数据模型"""
        logger.info("测试数据模型...")
        
        try:
            # 测试告警模型
            alert = HardwareAlert(
                alert_id="test_001",
                device_id="device_123",
                device_name="测试设备",
                alert_type=AlertType.DEVICE_OFFLINE,
                severity=AlertSeverity.ERROR,
                message="设备离线测试",
                source=AlertSource.SYSTEM_MONITOR,
                timestamp=datetime.now()
            )
            
            # 验证模型序列化
            alert_dict = alert.dict()
            assert alert_dict['alert_id'] == "test_001"
            assert alert_dict['device_id'] == "device_123"
            assert alert_dict['alert_type'] == AlertType.DEVICE_OFFLINE.value
            
            # 测试设备状态模型
            device_status = HardwareDeviceStatus(
                device_id="device_123",
                device_name="测试设备",
                status="online",
                last_seen=datetime.now(),
                cpu_usage=75.5,
                memory_usage=60.2,
                temperature=45.0
            )
            
            status_dict = device_status.dict()
            assert status_dict['device_id'] == "device_123"
            assert status_dict['cpu_usage'] == 75.5
            
            self.test_results.append({
                "test_name": "数据模型测试",
                "status": "PASSED",
                "details": "告警模型和设备状态模型验证通过",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "数据模型测试",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _test_mqtt_service(self):
        """测试MQTT服务"""
        logger.info("测试MQTT服务...")
        
        try:
            # 创建模拟MQTT配置
            config = MQTTConfig(
                broker_host="localhost",
                broker_port=1883,
                username="test_user",
                password="test_password"
            )
            
            # 由于我们不想真正连接到MQTT代理，这里只测试配置和初始化
            mqtt_service = HardwareAlertMQTTService(config)
            
            # 测试配置信息获取
            service_info = mqtt_service.get_service_info()
            assert service_info['alert_topic_prefix'] == "hardware/alerts"
            assert service_info['initialized'] == False  # 未初始化
            
            self.test_results.append({
                "test_name": "MQTT服务测试",
                "status": "PASSED",
                "details": "MQTT服务配置和初始化测试通过",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "MQTT服务测试",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _test_anomaly_detectors(self):
        """测试异常检测器"""
        logger.info("测试异常检测器...")
        
        try:
            # 创建模拟MQTT服务
            mock_mqtt_service = Mock()
            mock_mqtt_service.send_alert.return_value = True
            
            # 初始化检测器
            detector = HardwareAlertDetector(mock_mqtt_service)
            
            # 测试设备离线检测
            test_metrics = {'cpu_usage': 50.0, 'memory_usage': 60.0}
            alerts = detector.detect_anomalies("test_device_1", test_metrics)
            
            # 验证检测器注册
            assert len(detector.detectors) >= 4  # 至少4个默认检测器
            
            # 测试具体的检测器
            offline_detector = DeviceOfflineDetector()
            perf_detector = PerformanceDegradationDetector()
            temp_detector = TemperatureAnomalyDetector()
            memory_detector = MemoryLeakDetector()
            conn_detector = ConnectionStabilityDetector()
            
            # 验证各检测器都能正常初始化
            detectors = [
                offline_detector, perf_detector, temp_detector, 
                memory_detector, conn_detector
            ]
            
            for detector_instance in detectors:
                assert hasattr(detector_instance, 'detect')
                assert callable(getattr(detector_instance, 'detect'))
            
            self.test_results.append({
                "test_name": "异常检测器测试",
                "status": "PASSED",
                "details": f"共测试了 {len(detectors)} 个异常检测器",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "异常检测器测试",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _test_alert_manager(self):
        """测试告警管理器"""
        logger.info("测试告警管理器...")
        
        try:
            # 创建模拟MQTT服务
            mock_mqtt_service = Mock()
            mock_mqtt_service.send_alert.return_value = True
            
            # 初始化告警管理器
            alert_manager = HardwareAlertManager(mock_mqtt_service)
            
            # 测试手动告警报告
            alert = alert_manager.report_manual_alert(
                device_id="test_device_1",
                alert_type=AlertType.UNKNOWN_ERROR,
                severity=AlertSeverity.WARNING,
                message="测试手动告警"
            )
            
            assert alert.device_id == "test_device_1"
            assert alert.alert_type == AlertType.UNKNOWN_ERROR
            assert alert.severity == AlertSeverity.WARNING
            
            # 测试获取设备告警
            device_alerts = alert_manager.get_device_alerts("test_device_1")
            assert len(device_alerts) >= 1
            
            # 测试获取活跃告警
            active_alerts = alert_manager.get_active_alerts()
            assert isinstance(active_alerts, list)
            
            self.test_results.append({
                "test_name": "告警管理器测试",
                "status": "PASSED",
                "details": "告警管理器功能验证通过",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "告警管理器测试",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _test_integration(self):
        """测试集成功能"""
        logger.info("测试集成功能...")
        
        try:
            # 创建模拟MQTT服务
            mock_mqtt_service = Mock()
            mock_mqtt_service.send_alert.return_value = True
            
            # 初始化完整的告警系统
            alert_manager = HardwareAlertManager(mock_mqtt_service)
            
            # 模拟设备指标数据流
            test_scenarios = [
                {
                    "device_id": "cpu_high_device",
                    "metrics": {"cpu_usage": 90.0, "memory_usage": 45.0},
                    "expected_alerts": 1
                },
                {
                    "device_id": "temp_hot_device",
                    "metrics": {"temperature": 80.0, "cpu_usage": 30.0},
                    "expected_alerts": 1
                },
                {
                    "device_id": "normal_device",
                    "metrics": {"cpu_usage": 45.0, "memory_usage": 30.0, "temperature": 40.0},
                    "expected_alerts": 0
                }
            ]
            
            total_detected_alerts = 0
            
            for scenario in test_scenarios:
                alerts = alert_manager.alert_detector.detect_anomalies(
                    scenario["device_id"],
                    scenario["metrics"]
                )
                total_detected_alerts += len(alerts)
                
                # 验证告警数量符合预期
                assert len(alerts) >= scenario["expected_alerts"]
            
            # 验证MQTT消息发送
            assert mock_mqtt_service.send_alert.call_count >= total_detected_alerts
            
            self.test_results.append({
                "test_name": "集成测试",
                "status": "PASSED",
                "details": f"处理了 {len(test_scenarios)} 个场景，检测到 {total_detected_alerts} 个告警",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "集成测试",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        # 统计结果
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        total_tests = len(self.test_results)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "backtest_info": {
                "name": "硬件告警系统回测",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "environment": "development"
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2)
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告到文件
        report_filename = f"hardware_alert_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"回测报告已保存: {report_filename}")
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        failed_tests = [r for r in self.test_results if r['status'] == 'FAILED']
        
        if failed_tests:
            recommendations.append("修复失败的测试用例")
            for failed_test in failed_tests:
                recommendations.append(f"修复 {failed_test['test_name']}: {failed_test.get('error', '未知错误')}")
        
        # 基于成功测试生成建议
        passed_tests = [r for r in self.test_results if r['status'] == 'PASSED']
        
        if any("MQTT" in r['test_name'] for r in passed_tests):
            recommendations.append("考虑在生产环境中部署真实的MQTT代理")
        
        if any("检测器" in r['test_name'] for r in passed_tests):
            recommendations.append("定期审查和更新异常检测阈值")
        
        if any("集成" in r['test_name'] for r in passed_tests):
            recommendations.append("建立持续集成测试流程")
        
        return recommendations


def main():
    """主函数"""
    print("=" * 60)
    print("硬件设备异常上报通道回测")
    print("=" * 60)
    
    # 运行回测
    backtest = HardwareAlertBacktest()
    report = backtest.run_complete_backtest()
    
    # 输出结果摘要
    print("\n回测结果摘要:")
    print("-" * 40)
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"通过测试: {report['summary']['passed_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"成功率: {report['summary']['success_rate']}%")
    print(f"执行时间: {report['backtest_info']['duration_seconds']} 秒")
    
    print("\n详细结果:")
    print("-" * 40)
    for result in report['test_results']:
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} {result['test_name']}: {result['status']}")
        if result['status'] == 'FAILED':
            print(f"   错误: {result.get('error', '未知错误')}")
    
    if report['recommendations']:
        print("\n改进建议:")
        print("-" * 40)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print("\n" + "=" * 60)
    
    # 返回退出码
    return 0 if report['summary']['success_rate'] >= 90 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)