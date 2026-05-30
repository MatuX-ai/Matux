#!/usr/bin/env python3
"""
高并发熔断测试脚本
模拟1000+ QPS场景验证熔断机制
"""

import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import json
from datetime import datetime

class HighConcurrencyTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.start_time = None
        self.end_time = None
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """发送单个请求并记录结果"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                result = {
                    'endpoint': endpoint,
                    'status_code': response.status,
                    'response_time': response_time,
                    'success': 200 <= response.status < 300,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 读取响应内容
                try:
                    content = await response.text()
                    result['content'] = content[:200]  # 限制内容长度
                except:
                    result['content'] = 'Failed to read content'
                    
                return result
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'response_time': response_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_concurrent_requests(self, endpoint: str, concurrency: int, duration: int = 30):
        """运行并发请求测试"""
        print(f"🚀 开始高并发测试: {concurrency} 并发, 持续 {duration} 秒")
        print(f"🎯 目标端点: {endpoint}")
        
        tasks = []
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # 创建持续发送请求的任务
            async def continuous_requests():
                while time.time() - self.start_time < duration:
                    task = asyncio.create_task(self.make_request(session, endpoint))
                    tasks.append(task)
                    # 控制并发数量
                    if len(tasks) >= concurrency:
                        # 等待部分任务完成
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        for task in done:
                            try:
                                result = await task
                                self.results.append(result)
                            except Exception as e:
                                print(f"❌ 任务执行异常: {e}")
                        tasks[:] = list(pending)  # 保留未完成的任务
                    
                    # 小延迟避免过于激进
                    await asyncio.sleep(0.001)
            
            await continuous_requests()
            
            # 等待剩余任务完成
            if tasks:
                done, _ = await asyncio.wait(tasks)
                for task in done:
                    try:
                        result = await task
                        self.results.append(result)
                    except Exception as e:
                        print(f"❌ 任务执行异常: {e}")
        
        self.end_time = time.time()
        print(f"✅ 测试完成，共执行 {len(self.results)} 个请求")
    
    def analyze_results(self) -> Dict[str, Any]:
        """分析测试结果"""
        if not self.results:
            return {"error": "没有测试结果"}
        
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r['success']])
        failed_requests = total_requests - successful_requests
        
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # 响应时间统计
        response_times = [r['response_time'] for r in self.results if r['success']]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = max_response_time = 0
        
        # 状态码统计
        status_codes = {}
        for result in self.results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # 错误统计
        errors = {}
        for result in self.results:
            if not result['success'] and 'error' in result:
                error_type = type(result['error']).__name__
                errors[error_type] = errors.get(error_type, 0) + 1
        
        analysis = {
            'test_summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': round(success_rate, 2),
                'test_duration': round(self.end_time - self.start_time, 2) if self.end_time else 0,
                'requests_per_second': round(total_requests / (self.end_time - self.start_time), 2) if self.end_time and self.start_time else 0
            },
            'response_time_stats': {
                'average': round(avg_response_time, 3),
                'median': round(median_response_time, 3),
                'p95': round(p95_response_time, 3),
                'max': round(max_response_time, 3)
            },
            'status_code_distribution': status_codes,
            'error_distribution': errors
        }
        
        return analysis
    
    def print_report(self, analysis: Dict[str, Any]):
        """打印测试报告"""
        print("\n" + "="*60)
        print("📊 高并发熔断测试报告")
        print("="*60)
        
        summary = analysis['test_summary']
        print(f"\n📈 测试概览:")
        print(f"  • 总请求数: {summary['total_requests']}")
        print(f"  • 成功请求数: {summary['successful_requests']}")
        print(f"  • 失败请求数: {summary['failed_requests']}")
        print(f"  • 成功率: {summary['success_rate']}%")
        print(f"  • 测试时长: {summary['test_duration']} 秒")
        print(f"  • QPS: {summary['requests_per_second']}")
        
        rt_stats = analysis['response_time_stats']
        print(f"\n⏱️  响应时间统计:")
        print(f"  • 平均响应时间: {rt_stats['average']}s")
        print(f"  • 中位数响应时间: {rt_stats['median']}s")
        print(f"  • 95th百分位响应时间: {rt_stats['p95']}s")
        print(f"  • 最大响应时间: {rt_stats['max']}s")
        
        print(f"\n🔢 状态码分布:")
        for code, count in analysis['status_code_distribution'].items():
            print(f"  • {code}: {count} 次")
        
        if analysis['error_distribution']:
            print(f"\n💥 错误分布:")
            for error_type, count in analysis['error_distribution'].items():
                print(f"  • {error_type}: {count} 次")
        
        print("\n" + "="*60)
    
    async def monitor_circuit_breaker_state(self):
        """监控熔断器状态"""
        print("🔍 开始监控熔断器状态...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 获取指标数据
                async with session.get(f"{self.base_url}/metrics") as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # 解析关键指标
                        metrics = {}
                        for line in content.split('\n'):
                            if line.startswith('circuit_breaker_'):
                                parts = line.split(' ')
                                if len(parts) == 2:
                                    metric_name = parts[0]
                                    metric_value = float(parts[1])
                                    metrics[metric_name] = metric_value
                        
                        print("📋 熔断器指标:")
                        for name, value in metrics.items():
                            print(f"  • {name}: {value}")
                            
                        # 检查熔断器状态
                        if 'circuit_breaker_state' in metrics:
                            state_value = int(metrics['circuit_breaker_state'])
                            states = {0: 'CLOSED', 1: 'OPEN', 2: 'HALF_OPEN'}
                            current_state = states.get(state_value, 'UNKNOWN')
                            print(f"  🔄 当前熔断器状态: {current_state}")
                            
                            # 检查失败率
                            if 'circuit_breaker_failure_rate' in metrics:
                                failure_rate = metrics['circuit_breaker_failure_rate']
                                print(f"  ⚠️  当前失败率: {failure_rate}%")
                                
                                if failure_rate > 50:
                                    print("  🚨 警告: 失败率过高，可能触发熔断!")
                                    
                    else:
                        print(f"❌ 无法获取指标数据 (状态码: {response.status})")
                        
            except Exception as e:
                print(f"❌ 监控过程中出现异常: {e}")

async def main():
    """主测试函数"""
    print("🔬 iMato高并发熔断测试")
    print("="*50)
    
    # 测试配置
    tester = HighConcurrencyTester("http://localhost:8000")
    
    # 测试场景1: 正常高并发测试
    print("\n📋 场景1: 正常高并发测试 (/test/success)")
    await tester.run_concurrent_requests("/test/success", concurrency=50, duration=30)
    analysis1 = tester.analyze_results()
    tester.print_report(analysis1)
    await tester.monitor_circuit_breaker_state()
    
    # 清空结果准备下一场景
    tester.results.clear()
    
    # 测试场景2: 故障注入高并发测试
    print("\n📋 场景2: 故障注入高并发测试 (/test/faulty)")
    await tester.run_concurrent_requests("/test/faulty", concurrency=30, duration=20)
    analysis2 = tester.analyze_results()
    tester.print_report(analysis2)
    await tester.monitor_circuit_breaker_state()
    
    # 保存详细结果
    detailed_results = {
        'normal_test': analysis1,
        'faulty_test': analysis2,
        'test_timestamp': datetime.now().isoformat()
    }
    
    with open('high_concurrency_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细测试结果已保存到 high_concurrency_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())