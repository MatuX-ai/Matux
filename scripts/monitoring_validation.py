#!/usr/bin/env python3
"""
监控体系验证脚本
确认Prometheus指标和Grafana仪表板正常工作
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime
import subprocess
import sys

class MonitoringValidator:
    def __init__(self, 
                 app_url: str = "http://localhost:8000",
                 prometheus_url: str = "http://localhost:9090",
                 grafana_url: str = "http://localhost:3001"):
        self.app_url = app_url
        self.prometheus_url = prometheus_url
        self.grafana_url = grafana_url
        self.validation_results = []
        
    def validate_prometheus_metrics(self) -> Dict[str, Any]:
        """验证Prometheus指标"""
        print("📈 验证Prometheus指标...")
        
        try:
            # 测试应用指标端点
            metrics_response = requests.get(f"{self.app_url}/metrics", timeout=10)
            metrics_available = metrics_response.status_code == 200
            
            if metrics_available:
                metrics_content = metrics_response.text
                circuit_breaker_metrics = self.extract_circuit_breaker_metrics(metrics_content)
                http_metrics = self.extract_http_metrics(metrics_content)
                
                result = {
                    'status': 'success',
                    'metrics_endpoint_accessible': True,
                    'circuit_breaker_metrics': circuit_breaker_metrics,
                    'http_metrics': http_metrics,
                    'total_metrics_count': len(metrics_content.split('\n')),
                    'sample_metrics': metrics_content.split('\n')[:10]  # 前10行作为样本
                }
            else:
                result = {
                    'status': 'failed',
                    'metrics_endpoint_accessible': False,
                    'error': f'指标端点返回状态码: {metrics_response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            result = {
                'status': 'failed',
                'metrics_endpoint_accessible': False,
                'error': str(e)
            }
        
        self.validation_results.append({
            'component': 'prometheus_metrics',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def extract_circuit_breaker_metrics(self, metrics_content: str) -> Dict[str, Any]:
        """提取熔断器相关指标"""
        circuit_metrics = {}
        lines = metrics_content.split('\n')
        
        for line in lines:
            if line.startswith('circuit_breaker_'):
                # 解析指标行，格式: metric_name{labels} value
                if ' ' in line:
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        try:
                            metric_value = float(parts[-1])
                            circuit_metrics[metric_name] = metric_value
                        except ValueError:
                            # 非数值指标（如枚举）
                            circuit_metrics[metric_name] = parts[-1]
        
        return circuit_metrics
    
    def extract_http_metrics(self, metrics_content: str) -> Dict[str, Any]:
        """提取HTTP相关指标"""
        http_metrics = {}
        lines = metrics_content.split('\n')
        
        for line in lines:
            if line.startswith('http_') or line.startswith('fastapi_'):
                if ' ' in line:
                    parts = line.split(' ')
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        try:
                            metric_value = float(parts[-1])
                            http_metrics[metric_name] = metric_value
                        except ValueError:
                            http_metrics[metric_name] = parts[-1]
        
        return http_metrics
    
    def validate_prometheus_server(self) -> Dict[str, Any]:
        """验证Prometheus服务器"""
        print("🔍 验证Prometheus服务器...")
        
        try:
            # 测试Prometheus API
            response = requests.get(f"{self.prometheus_url}/api/v1/status/runtimeinfo", timeout=10)
            prometheus_accessible = response.status_code == 200
            
            if prometheus_accessible:
                runtime_info = response.json()
                result = {
                    'status': 'success',
                    'prometheus_accessible': True,
                    'version': runtime_info.get('data', {}).get('version', 'unknown'),
                    'storage_retention': runtime_info.get('data', {}).get('storageRetention', 'unknown')
                }
            else:
                result = {
                    'status': 'failed',
                    'prometheus_accessible': False,
                    'error': f'Prometheus API返回状态码: {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            result = {
                'status': 'failed',
                'prometheus_accessible': False,
                'error': str(e)
            }
        
        self.validation_results.append({
            'component': 'prometheus_server',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def validate_grafana_dashboard(self) -> Dict[str, Any]:
        """验证Grafana仪表板"""
        print("📊 验证Grafana仪表板...")
        
        try:
            # 测试Grafana登录页面
            response = requests.get(f"{self.grafana_url}/login", timeout=10)
            grafana_accessible = response.status_code in [200, 401]  # 200或401都表示可达
            
            if grafana_accessible:
                # 尝试获取仪表板信息（需要认证）
                auth = ('admin', 'admin123')  # 默认凭据
                dashboards_response = requests.get(
                    f"{self.grafana_url}/api/search", 
                    auth=auth, 
                    timeout=10
                )
                
                if dashboards_response.status_code == 200:
                    dashboards = dashboards_response.json()
                    result = {
                        'status': 'success',
                        'grafana_accessible': True,
                        'dashboards_count': len(dashboards),
                        'dashboards_list': [d.get('title', 'Unknown') for d in dashboards[:5]]
                    }
                else:
                    result = {
                        'status': 'partial',
                        'grafana_accessible': True,
                        'dashboards_count': 0,
                        'error': '无法获取仪表板列表（可能需要配置认证）'
                    }
            else:
                result = {
                    'status': 'failed',
                    'grafana_accessible': False,
                    'error': f'Grafana返回状态码: {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            result = {
                'status': 'failed',
                'grafana_accessible': False,
                'error': str(e)
            }
        
        self.validation_results.append({
            'component': 'grafana_dashboard',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def test_metric_queries(self) -> Dict[str, Any]:
        """测试Prometheus查询"""
        print("🔍 测试Prometheus查询...")
        
        test_queries = [
            {
                'name': 'HTTP请求总数',
                'query': 'sum(http_requests_total)',
                'description': '统计总的HTTP请求数'
            },
            {
                'name': '熔断器状态',
                'query': 'circuit_breaker_state',
                'description': '当前熔断器状态'
            },
            {
                'name': '失败率',
                'query': 'circuit_breaker_failure_rate',
                'description': '当前失败率'
            }
        ]
        
        query_results = []
        
        for test_query in test_queries:
            try:
                # 构造查询URL
                encoded_query = requests.utils.quote(test_query['query'])
                query_url = f"{self.prometheus_url}/api/v1/query?query={encoded_query}"
                
                response = requests.get(query_url, timeout=10)
                
                if response.status_code == 200:
                    query_data = response.json()
                    if query_data.get('status') == 'success':
                        result_data = query_data.get('data', {})
                        query_results.append({
                            'name': test_query['name'],
                            'query': test_query['query'],
                            'status': 'success',
                            'result': result_data.get('result', []),
                            'result_type': result_data.get('resultType', 'unknown')
                        })
                    else:
                        query_results.append({
                            'name': test_query['name'],
                            'query': test_query['query'],
                            'status': 'failed',
                            'error': query_data.get('error', 'Unknown error')
                        })
                else:
                    query_results.append({
                        'name': test_query['name'],
                        'query': test_query['query'],
                        'status': 'failed',
                        'error': f'HTTP {response.status_code}'
                    })
                    
            except requests.exceptions.RequestException as e:
                query_results.append({
                    'name': test_query['name'],
                    'query': test_query['query'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        result = {
            'status': 'completed',
            'queries_tested': len(test_queries),
            'successful_queries': len([q for q in query_results if q['status'] == 'success']),
            'query_results': query_results
        }
        
        self.validation_results.append({
            'component': 'metric_queries',
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        # 统计结果
        total_components = len(self.validation_results)
        successful_components = len([r for r in self.validation_results if r['result']['status'] == 'success'])
        partial_components = len([r for r in self.validation_results if r['result']['status'] == 'partial'])
        failed_components = total_components - successful_components - partial_components
        
        success_rate = (successful_components / total_components * 100) if total_components > 0 else 0
        
        report = {
            'summary': {
                'total_components': total_components,
                'successful_components': successful_components,
                'partial_components': partial_components,
                'failed_components': failed_components,
                'success_rate': round(success_rate, 2),
                'validation_timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.validation_results,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 检查各个组件的结果
        for result in self.validation_results:
            component = result['component']
            status = result['result']['status']
            
            if status == 'failed':
                if component == 'prometheus_metrics':
                    recommendations.append("检查应用的指标端点配置")
                elif component == 'prometheus_server':
                    recommendations.append("检查Prometheus服务器是否正常运行")
                elif component == 'grafana_dashboard':
                    recommendations.append("检查Grafana服务器连接和认证配置")
                elif component == 'metric_queries':
                    recommendations.append("检查Prometheus查询语句是否正确")
            elif status == 'partial':
                recommendations.append(f"{component}功能部分可用，建议进一步排查")
        
        if not recommendations:
            recommendations.append("监控体系验证通过，所有组件工作正常")
        
        return recommendations
    
    def print_report(self, report: Dict[str, Any]):
        """打印验证报告"""
        print("\n" + "="*70)
        print("📊 监控体系验证报告")
        print("="*70)
        
        summary = report['summary']
        print(f"\n📈 验证概览:")
        print(f"  • 验证组件总数: {summary['total_components']}")
        print(f"  • 完全成功组件: {summary['successful_components']}")
        print(f"  • 部分成功组件: {summary['partial_components']}")
        print(f"  • 失败组件: {summary['failed_components']}")
        print(f"  • 总体成功率: {summary['success_rate']}%")
        
        print(f"\n📋 详细结果:")
        for result in report['detailed_results']:
            component = result['component']
            status = result['result']['status']
            
            status_icons = {
                'success': '✅',
                'partial': '⚠️ ',
                'failed': '❌'
            }
            
            print(f"  {status_icons.get(status, '❓')} {component}: {status}")
            
            # 显示额外信息
            if component == 'prometheus_metrics' and status == 'success':
                metrics_result = result['result']
                print(f"    - 指标端点可访问: {metrics_result['metrics_endpoint_accessible']}")
                print(f"    - 熔断器指标数: {len(metrics_result['circuit_breaker_metrics'])}")
                print(f"    - HTTP指标数: {len(metrics_result['http_metrics'])}")
            
            elif component == 'prometheus_server' and status == 'success':
                server_result = result['result']
                print(f"    - Prometheus版本: {server_result['version']}")
            
            elif component == 'grafana_dashboard' and status == 'success':
                grafana_result = result['result']
                print(f"    - 仪表板数量: {grafana_result['dashboards_count']}")
            
            elif component == 'metric_queries':
                queries_result = result['result']
                print(f"    - 成功查询: {queries_result['successful_queries']}/{queries_result['queries_tested']}")
        
        print(f"\n💡 改进建议:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print("\n" + "="*70)

def main():
    """主验证函数"""
    print("🔬 iMato监控体系验证")
    print("="*50)
    
    validator = MonitoringValidator()
    
    # 执行各项验证
    validator.validate_prometheus_metrics()
    validator.validate_prometheus_server()
    validator.validate_grafana_dashboard()
    validator.test_metric_queries()
    
    # 生成并打印报告
    report = validator.generate_validation_report()
    validator.print_report(report)
    
    # 保存详细报告
    with open('monitoring_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细验证报告已保存到 monitoring_validation_report.json")
    
    return report

if __name__ == "__main__":
    main()