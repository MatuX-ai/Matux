#!/usr/bin/env python3
"""
API版本兼容性测试脚本
验证v1/v2 API并行运行和路由正确性
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

class APIVersionCompatibilityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def test_api_versions(self):
        """测试不同API版本的兼容性"""
        print("🧪 开始API版本兼容性测试")
        print("="*50)
        
        # 测试用例定义
        test_cases = [
            {
                'name': '健康检查端点兼容性',
                'v1_endpoint': '/health',
                'v2_endpoint': '/health',  # 假设v2也使用相同端点
                'expected_status': 200,
                'validation_func': self.validate_health_response
            },
            {
                'name': '用户管理API兼容性',
                'v1_endpoint': '/api/v1/users',
                'v2_endpoint': '/api/v2/users',
                'expected_status': 404,  # 当前未实现，应该是404
                'validation_func': self.validate_not_found_response
            },
            {
                'name': '测试端点兼容性',
                'v1_endpoint': '/test/success',
                'v2_endpoint': '/test/success',  # 假设v2也支持
                'expected_status': 200,
                'validation_func': self.validate_success_response
            }
        ]
        
        for case in test_cases:
            self.run_version_test_case(case)
        
        return self.test_results
    
    def run_version_test_case(self, test_case: Dict[str, Any]):
        """运行单个版本测试用例"""
        print(f"\n📋 测试用例: {test_case['name']}")
        print("-" * 40)
        
        # 测试v1版本
        v1_result = self.test_single_endpoint(
            test_case['v1_endpoint'], 
            'v1', 
            test_case['expected_status'],
            test_case['validation_func']
        )
        
        # 测试v2版本
        v2_result = self.test_single_endpoint(
            test_case['v2_endpoint'], 
            'v2', 
            test_case['expected_status'],
            test_case['validation_func']
        )
        
        # 记录测试结果
        self.test_results.append({
            'test_case': test_case['name'],
            'v1_result': v1_result,
            'v2_result': v2_result,
            'compatible': v1_result['success'] == v2_result['success'],
            'timestamp': datetime.now().isoformat()
        })
        
        # 输出兼容性结果
        if v1_result['success'] == v2_result['success']:
            print(f"✅ 版本兼容性: 通过")
        else:
            print(f"❌ 版本兼容性: 失败")
            print(f"   v1状态: {v1_result['status_code']}, v2状态: {v2_result['status_code']}")
    
    def test_single_endpoint(self, endpoint: str, version: str, expected_status: int, 
                           validation_func) -> Dict[str, Any]:
        """测试单个端点"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            response_time = time.time() - start_time
            
            is_valid = (response.status_code == expected_status and 
                       validation_func(response.json()) if response.status_code == 200 else True)
            
            result = {
                'endpoint': endpoint,
                'version': version,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'success': response.status_code == expected_status and is_valid,
                'content': response.json() if response.status_code == 200 else None
            }
            
            status_icon = "✅" if result['success'] else "❌"
            print(f"  {status_icon} {version}: {endpoint} -> {response.status_code} ({response_time:.3f}s)")
            
            return result
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            result = {
                'endpoint': endpoint,
                'version': version,
                'status_code': 0,
                'response_time': round(response_time, 3),
                'success': False,
                'error': str(e)
            }
            print(f"  ❌ {version}: {endpoint} -> 连接失败 ({response_time:.3f}s)")
            return result
    
    def validate_health_response(self, data: Dict) -> bool:
        """验证健康检查响应"""
        required_fields = ['status', 'service']
        return all(field in data for field in required_fields)
    
    def validate_success_response(self, data: Dict) -> bool:
        """验证成功响应"""
        return 'message' in data and data['message'] == 'success'
    
    def validate_not_found_response(self, data: Dict) -> bool:
        """验证404响应"""
        return True  # 404响应不需要特定内容验证
    
    def test_route_prefix_isolation(self):
        """测试路由前缀隔离"""
        print(f"\n🔒 测试路由前缀隔离")
        print("-" * 40)
        
        isolation_tests = [
            {
                'name': 'API版本路由隔离',
                'endpoints': ['/api/v1/health', '/api/v2/health'],
                'expected_behavior': '不同版本应该有不同的路由处理'
            },
            {
                'name': '测试端点隔离',
                'endpoints': ['/test/success', '/api/v1/test/success'],
                'expected_behavior': '应该有不同的路由规则'
            }
        ]
        
        for test in isolation_tests:
            print(f"\n📋 {test['name']}:")
            for endpoint in test['endpoints']:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    print(f"  {endpoint} -> {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"  {endpoint} -> 连接失败: {e}")
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        print(f"\n🔄 测试向后兼容性")
        print("-" * 40)
        
        # 模拟旧客户端行为
        compatibility_tests = [
            {
                'name': 'Accept头版本协商',
                'headers': {'Accept': 'application/vnd.imato.v1+json'},
                'expected_endpoint': '/api/v1/'
            },
            {
                'name': '查询参数版本控制',
                'params': {'api_version': 'v1'},
                'expected_behavior': '应该返回v1格式数据'
            }
        ]
        
        for test in compatibility_tests:
            print(f"\n📋 {test['name']}:")
            try:
                if 'headers' in test:
                    response = requests.get(f"{self.base_url}/api/", headers=test['headers'], timeout=5)
                    print(f"  带Accept头请求 -> {response.status_code}")
                    
                if 'params' in test:
                    response = requests.get(f"{self.base_url}/api/", params=test['params'], timeout=5)
                    print(f"  带版本参数请求 -> {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  请求失败: {e}")
    
    def generate_compatibility_report(self) -> Dict[str, Any]:
        """生成兼容性测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['compatible']])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_test_cases': total_tests,
                'passed_cases': passed_tests,
                'failed_cases': failed_tests,
                'success_rate': round(success_rate, 2),
                'test_timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.test_results,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r['compatible']]
        if failed_tests:
            recommendations.append("修复版本间不兼容的API端点")
            recommendations.append("确保破坏性变更遵循语义化版本控制")
        
        # 检查是否有缺失的版本端点
        missing_endpoints = []
        for result in self.test_results:
            if result['v1_result']['status_code'] == 404:
                missing_endpoints.append(result['v1_result']['endpoint'])
        
        if missing_endpoints:
            recommendations.append(f"实现缺失的API端点: {', '.join(missing_endpoints)}")
        
        if not recommendations:
            recommendations.append("API版本兼容性良好，继续保持")
        
        return recommendations
    
    def print_report(self, report: Dict[str, Any]):
        """打印测试报告"""
        print("\n" + "="*60)
        print("📊 API版本兼容性测试报告")
        print("="*60)
        
        summary = report['summary']
        print(f"\n📈 测试概览:")
        print(f"  • 总测试用例数: {summary['total_test_cases']}")
        print(f"  • 通过用例数: {summary['passed_cases']}")
        print(f"  • 失败用例数: {summary['failed_cases']}")
        print(f"  • 成功率: {summary['success_rate']}%")
        
        print(f"\n📋 详细结果:")
        for result in report['detailed_results']:
            status_icon = "✅" if result['compatible'] else "❌"
            print(f"  {status_icon} {result['test_case']}")
            print(f"    v1: {result['v1_result']['status_code']} "
                  f"({result['v1_result']['response_time']}s)")
            print(f"    v2: {result['v2_result']['status_code']} "
                  f"({result['v2_result']['response_time']}s)")
        
        print(f"\n💡 改进建议:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print("\n" + "="*60)

def main():
    """主测试函数"""
    print("🔬 iMato API版本兼容性测试")
    print("="*50)
    
    tester = APIVersionCompatibilityTester("http://localhost:8000")
    
    # 运行兼容性测试
    tester.test_api_versions()
    
    # 测试路由隔离
    tester.test_route_prefix_isolation()
    
    # 测试向后兼容性
    tester.test_backward_compatibility()
    
    # 生成并打印报告
    report = tester.generate_compatibility_report()
    tester.print_report(report)
    
    # 保存详细报告
    with open('api_compatibility_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细测试报告已保存到 api_compatibility_test_report.json")
    
    return report

if __name__ == "__main__":
    main()