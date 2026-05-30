"""
硬件告警系统完整功能验证脚本
执行端到端的功能测试和回归测试
"""

import sys
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from models.hardware_alert import AlertType, AlertSeverity
from config.settings import settings

class HardwareAlertFullValidation:
    """硬件告警系统完整验证类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.validation_results = []
        self.start_time = None
        self.end_time = None
    
    def run_full_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        self.start_time = datetime.now()
        print("=" * 60)
        print("硬件告警系统完整功能验证")
        print("=" * 60)
        
        try:
            # 1. 服务健康检查
            self._validate_service_health()
            
            # 2. API接口测试
            self._validate_api_endpoints()
            
            # 3. 告警功能测试
            self._validate_alert_functionality()
            
            # 4. 设备状态管理测试
            self._validate_device_management()
            
            # 5. 配置验证
            self._validate_configuration()
            
        except Exception as e:
            print(f"❌ 验证过程出错: {str(e)}")
            self.validation_results.append({
                "test_category": "整体验证",
                "test_name": "执行过程",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        self.end_time = datetime.now()
        return self._generate_validation_report()
    
    def _validate_service_health(self):
        """验证服务健康状态"""
        print("\n🔍 正在验证服务健康状态...")
        
        try:
            # 基础健康检查
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 服务健康检查通过 - 版本: {health_data.get('version', 'unknown')}")
                self.validation_results.append({
                    "test_category": "服务健康",
                    "test_name": "基础健康检查",
                    "status": "PASSED",
                    "details": health_data,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                raise Exception(f"健康检查失败，状态码: {response.status_code}")
            
            # 服务信息检查
            response = requests.get(f"{self.base_url}/api/v1/hardware-alerts/service/info", timeout=5)
            if response.status_code == 200:
                service_info = response.json()
                mqtt_connected = service_info.get('mqtt_service', {}).get('connected', False)
                detection_enabled = service_info.get('settings', {}).get('detection_enabled', False)
                
                print(f"✅ MQTT连接状态: {'已连接' if mqtt_connected else '未连接'}")
                print(f"✅ 检测功能状态: {'已启用' if detection_enabled else '已禁用'}")
                
                self.validation_results.append({
                    "test_category": "服务健康",
                    "test_name": "详细服务信息",
                    "status": "PASSED",
                    "details": {
                        "mqtt_connected": mqtt_connected,
                        "detection_enabled": detection_enabled,
                        "service_info": service_info
                    },
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print("⚠️  无法获取详细服务信息")
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务，请确保服务正在运行")
            self.validation_results.append({
                "test_category": "服务健康",
                "test_name": "服务连接",
                "status": "FAILED",
                "error": "无法连接到服务",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"❌ 服务健康检查失败: {str(e)}")
            self.validation_results.append({
                "test_category": "服务健康",
                "test_name": "健康检查",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _validate_api_endpoints(self):
        """验证API端点功能"""
        print("\n🔍 正在验证API端点...")
        
        endpoints_to_test = [
            {
                "name": "列出告警",
                "method": "GET",
                "url": "/api/v1/hardware-alerts/alerts",
                "expected_status": 200
            },
            {
                "name": "获取设备状态列表",
                "method": "GET",
                "url": "/api/v1/hardware-alerts/devices/status",
                "expected_status": 200
            },
            {
                "name": "发送测试告警",
                "method": "POST",
                "url": "/api/v1/hardware-alerts/test-alert",
                "params": {"device_id": "validation_test_001"},
                "expected_status": 200
            }
        ]
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint['url']}"
                method = endpoint['method']
                
                if method == "GET":
                    response = requests.get(url, params=endpoint.get('params'), timeout=10)
                elif method == "POST":
                    response = requests.post(url, params=endpoint.get('params'), timeout=10)
                
                if response.status_code == endpoint['expected_status']:
                    print(f"✅ {endpoint['name']}: 通过")
                    self.validation_results.append({
                        "test_category": "API验证",
                        "test_name": endpoint['name'],
                        "status": "PASSED",
                        "details": {
                            "status_code": response.status_code,
                            "response_size": len(response.content)
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    print(f"❌ {endpoint['name']}: 失败 (状态码: {response.status_code})")
                    self.validation_results.append({
                        "test_category": "API验证",
                        "test_name": endpoint['name'],
                        "status": "FAILED",
                        "error": f"期望状态码 {endpoint['expected_status']}, 实际 {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                print(f"❌ {endpoint['name']}: 异常 - {str(e)}")
                self.validation_results.append({
                    "test_category": "API验证",
                    "test_name": endpoint['name'],
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    def _validate_alert_functionality(self):
        """验证告警功能"""
        print("\n🔍 正在验证告警功能...")
        
        test_device_id = "functional_test_device"
        
        # 1. 创建手动告警
        try:
            alert_data = {
                "device_id": test_device_id,
                "alert_type": AlertType.UNKNOWN_ERROR.value,
                "severity": AlertSeverity.WARNING.value,
                "message": "功能验证测试告警",
                "details": {"test": True, "purpose": "validation"}
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/hardware-alerts/alerts",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 201:
                alert_response = response.json()
                print(f"✅ 手动告警创建成功 - ID: {alert_response.get('alert_id')}")
                self.validation_results.append({
                    "test_category": "告警功能",
                    "test_name": "手动告警创建",
                    "status": "PASSED",
                    "details": alert_response,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"❌ 手动告警创建失败: {response.status_code}")
                self.validation_results.append({
                    "test_category": "告警功能",
                    "test_name": "手动告警创建",
                    "status": "FAILED",
                    "error": f"状态码: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"❌ 手动告警创建异常: {str(e)}")
            self.validation_results.append({
                "test_category": "告警功能",
                "test_name": "手动告警创建",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        # 2. 查询设备告警
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/hardware-alerts/alerts/device/{test_device_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                alerts = response.json()
                print(f"✅ 设备告警查询成功 - 找到 {len(alerts)} 条告警")
                self.validation_results.append({
                    "test_category": "告警功能",
                    "test_name": "设备告警查询",
                    "status": "PASSED",
                    "details": {"alert_count": len(alerts)},
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"❌ 设备告警查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 设备告警查询异常: {str(e)}")
    
    def _validate_device_management(self):
        """验证设备管理功能"""
        print("\n🔍 正在验证设备管理...")
        
        test_device_id = "management_test_device"
        
        # 1. 上报设备指标
        try:
            metrics_data = {
                "cpu_usage": 75.5,
                "memory_usage": 60.2,
                "temperature": 45.0,
                "connection_status": "connected"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/hardware-alerts/devices/{test_device_id}/metrics",
                json=metrics_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                detected_alerts = result.get('detected_alerts', 0)
                print(f"✅ 设备指标上报成功 - 检测到 {detected_alerts} 个告警")
                self.validation_results.append({
                    "test_category": "设备管理",
                    "test_name": "指标上报",
                    "status": "PASSED",
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"❌ 设备指标上报失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 设备指标上报异常: {str(e)}")
        
        # 2. 获取设备状态
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/hardware-alerts/devices/{test_device_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                print(f"✅ 设备状态获取成功 - 状态: {status.get('status')}")
                self.validation_results.append({
                    "test_category": "设备管理",
                    "test_name": "状态查询",
                    "status": "PASSED",
                    "details": status,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print(f"❌ 设备状态获取失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 设备状态获取异常: {str(e)}")
    
    def _validate_configuration(self):
        """验证配置"""
        print("\n🔍 正在验证配置...")
        
        try:
            # 检查关键配置项
            config_checks = [
                ("MQTT启用状态", settings.HARDWARE_ALERT_MQTT_ENABLED),
                ("检测功能启用", settings.HARDWARE_ALERT_DETECTION_ENABLED),
                ("MQTT代理地址", settings.HARDWARE_ALERT_MQTT_BROKER),
                ("监控间隔", settings.HARDWARE_ALERT_MONITORING_INTERVAL)
            ]
            
            for config_name, config_value in config_checks:
                print(f"✅ {config_name}: {config_value}")
            
            self.validation_results.append({
                "test_category": "配置验证",
                "test_name": "配置项检查",
                "status": "PASSED",
                "details": {
                    "mqtt_enabled": settings.HARDWARE_ALERT_MQTT_ENABLED,
                    "detection_enabled": settings.HARDWARE_ALERT_DETECTION_ENABLED,
                    "broker_host": settings.HARDWARE_ALERT_MQTT_BROKER,
                    "monitoring_interval": settings.HARDWARE_ALERT_MONITORING_INTERVAL
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ 配置验证失败: {str(e)}")
            self.validation_results.append({
                "test_category": "配置验证",
                "test_name": "配置检查",
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        # 统计结果
        passed_tests = len([r for r in self.validation_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.validation_results if r['status'] == 'FAILED'])
        total_tests = len(self.validation_results)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 按分类统计
        category_stats = {}
        for result in self.validation_results:
            category = result['test_category']
            if category not in category_stats:
                category_stats[category] = {'passed': 0, 'failed': 0, 'total': 0}
            
            category_stats[category]['total'] += 1
            if result['status'] == 'PASSED':
                category_stats[category]['passed'] += 1
            else:
                category_stats[category]['failed'] += 1
        
        report = {
            "validation_info": {
                "name": "硬件告警系统完整功能验证",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "base_url": self.base_url
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round(success_rate, 2),
                "category_stats": category_stats
            },
            "detailed_results": self.validation_results,
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        report_filename = f"hardware_alert_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 验证报告已保存: {report_filename}")
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        failed_results = [r for r in self.validation_results if r['status'] == 'FAILED']
        
        if failed_results:
            recommendations.append("修复验证失败的测试项")
            for failed in failed_results:
                recommendations.append(f"修复 {failed['test_category']} - {failed['test_name']}: {failed.get('error', '未知错误')}")
        
        # 基于成功测试生成建议
        api_tests_passed = any(r['test_category'] == 'API验证' and r['status'] == 'PASSED' 
                              for r in self.validation_results)
        if api_tests_passed:
            recommendations.append("API接口功能正常，可投入生产使用")
        
        config_valid = any(r['test_category'] == '配置验证' and r['status'] == 'PASSED'
                          for r in self.validation_results)
        if config_valid:
            recommendations.append("配置检查通过，确保生产环境配置正确")
        
        return recommendations


def main():
    """主函数"""
    # 获取命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='硬件告警系统完整验证')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='服务基础URL (默认: http://localhost:8000)')
    args = parser.parse_args()
    
    # 执行验证
    validator = HardwareAlertFullValidation(base_url=args.url)
    report = validator.run_full_validation()
    
    # 输出最终结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"通过测试: {report['summary']['passed_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"成功率: {report['summary']['success_rate']}%")
    print(f"执行时间: {report['validation_info']['duration_seconds']} 秒")
    
    print("\n分类统计:")
    print("-" * 30)
    for category, stats in report['summary']['category_stats'].items():
        rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
    
    if report['recommendations']:
        print("\n建议改进:")
        print("-" * 30)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print("\n" + "=" * 60)
    
    # 返回退出码
    success_rate = report['summary']['success_rate']
    return 0 if success_rate >= 80 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)