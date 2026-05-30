#!/usr/bin/env python3
"""
性能基准测试脚本
用于评估重构后组件的性能表现
"""

import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any, Callable

class PerformanceBenchmark:
    """性能基准测试类"""

    def __init__(self):
        self.results = {}
        self.iterations = 10000

    def benchmark_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """基准测试单个函数"""
        times = []

        # 预热运行
        for _ in range(100):
            func(*args, **kwargs)

        # 实际测试
        for _ in range(self.iterations):
            start_time = time.perf_counter()
            func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'iterations': self.iterations
        }

    def test_string_operations(self):
        """测试字符串操作性能"""
        print("🔤 测试字符串操作性能...")

        # 测试不同的字符串操作
        def string_concatenation():
            return "hello" + " " + "world" + "!"

        def string_formatting():
            return f"Hello {'world'}!"

        def string_methods():
            s = "  Hello World  "
            return s.strip().lower().replace(" ", "_")

        results = {
            'concatenation': self.benchmark_function(string_concatenation),
            'formatting': self.benchmark_function(string_formatting),
            'methods': self.benchmark_function(string_methods)
        }

        # 显示结果
        print("  字符串连接:", f"{results['concatenation']['mean']*1000000:.2f}μs")
        print("  字符串格式化:", f"{results['formatting']['mean']*1000000:.2f}μs")
        print("  字符串方法链:", f"{results['methods']['mean']*1000000:.2f}μs")

        return results

    def test_collection_operations(self):
        """测试集合操作性能"""
        print("📦 测试集合操作性能...")

        # 测试列表操作
        def list_creation():
            return [i for i in range(100)]

        def list_filtering():
            data = list(range(1000))
            return [x for x in data if x % 2 == 0]

        def list_sorting():
            data = list(range(1000, 0, -1))
            return sorted(data)

        # 测试字典操作
        def dict_creation():
            return {f"key_{i}": i for i in range(100)}

        def dict_lookup():
            d = {f"key_{i}": i for i in range(1000)}
            return d.get("key_500", 0)

        results = {
            'list_creation': self.benchmark_function(list_creation),
            'list_filtering': self.benchmark_function(list_filtering),
            'list_sorting': self.benchmark_function(list_sorting),
            'dict_creation': self.benchmark_function(dict_creation),
            'dict_lookup': self.benchmark_function(dict_lookup)
        }

        print("  列表创建:", f"{results['list_creation']['mean']*1000000:.2f}μs")
        print("  列表过滤:", f"{results['list_filtering']['mean']*1000000:.2f}μs")
        print("  列表排序:", f"{results['list_sorting']['mean']*1000000:.2f}μs")
        print("  字典创建:", f"{results['dict_creation']['mean']*1000000:.2f}μs")
        print("  字典查找:", f"{results['dict_lookup']['mean']*1000000:.2f}μs")

        return results

    def test_validation_performance(self):
        """测试验证器性能"""
        print("✅ 测试验证器性能...")

        # 模拟验证函数
        def email_validation():
            email = "test@example.com"
            return "@" in email and "." in email.split("@")[1]

        def username_validation():
            username = "testuser123"
            return 3 <= len(username) <= 50 and username.replace("_", "").replace("-", "").isalnum()

        def password_validation():
            password = "SecurePass123!"
            return (len(password) >= 8 and
                   any(c.isupper() for c in password) and
                   any(c.islower() for c in password) and
                   any(c.isdigit() for c in password))

        results = {
            'email_validation': self.benchmark_function(email_validation),
            'username_validation': self.benchmark_function(username_validation),
            'password_validation': self.benchmark_function(password_validation)
        }

        print("  邮箱验证:", f"{results['email_validation']['mean']*1000000:.2f}μs")
        print("  用户名验证:", f"{results['username_validation']['mean']*1000000:.2f}μs")
        print("  密码验证:", f"{results['password_validation']['mean']*1000000:.2f}μs")

        return results

    def test_http_client_simulation(self):
        """测试HTTP客户端模拟性能"""
        print("🌐 测试HTTP客户端性能...")

        # 模拟HTTP操作
        def mock_http_get():
            return {
                "status": 200,
                "data": {"id": 1, "name": "test"},
                "headers": {"content-type": "application/json"}
            }

        def mock_http_post():
            return {
                "status": 201,
                "data": {"id": 1},
                "headers": {"content-type": "application/json"}
            }

        def mock_response_processing():
            response = mock_http_get()
            return {
                "success": response["status"] < 400,
                "data": response["data"],
                "processed": True
            }

        results = {
            'http_get': self.benchmark_function(mock_http_get),
            'http_post': self.benchmark_function(mock_http_post),
            'response_processing': self.benchmark_function(mock_response_processing)
        }

        print("  HTTP GET模拟:", f"{results['http_get']['mean']*1000000:.2f}μs")
        print("  HTTP POST模拟:", f"{results['http_post']['mean']*1000000:.2f}μs")
        print("  响应处理:", f"{results['response_processing']['mean']*1000000:.2f}μs")

        return results

    def test_memory_usage(self):
        """测试内存使用情况"""
        print("💾 测试内存使用...")

        import sys

        def measure_object_size():
            # 测试不同类型对象的大小
            string_obj = "Hello World" * 100
            list_obj = list(range(1000))
            dict_obj = {f"key_{i}": i for i in range(100)}

            return {
                'string_size': sys.getsizeof(string_obj),
                'list_size': sys.getsizeof(list_obj),
                'dict_size': sys.getsizeof(dict_obj)
            }

        sizes = measure_object_size()
        print(f"  字符串对象大小: {sizes['string_size']} bytes")
        print(f"  列表对象大小: {sizes['list_size']} bytes")
        print(f"  字典对象大小: {sizes['dict_size']} bytes")

        return sizes

    def run_comprehensive_benchmark(self):
        """运行综合性能基准测试"""
        print("🚀 开始综合性能基准测试...")
        print(f"测试迭代次数: {self.iterations:,}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        all_results = {
            'timestamp': datetime.now().isoformat(),
            'iterations': self.iterations,
            'tests': {}
        }

        # 运行各类测试
        test_functions = [
            ("字符串操作", self.test_string_operations),
            ("集合操作", self.test_collection_operations),
            ("验证器性能", self.test_validation_performance),
            ("HTTP客户端模拟", self.test_http_client_simulation),
            ("内存使用", self.test_memory_usage)
        ]

        for test_name, test_func in test_functions:
            print(f"\n{test_name}")
            print("-" * 30)
            try:
                result = test_func()
                all_results['tests'][test_name] = result
            except Exception as e:
                print(f"❌ {test_name} 测试失败: {e}")
                all_results['tests'][test_name] = {'error': str(e)}

        # 生成性能摘要
        self.generate_performance_summary(all_results)

        # 保存详细报告
        self.save_benchmark_report(all_results)

        return all_results

    def generate_performance_summary(self, results: Dict[str, Any]):
        """生成性能摘要"""
        print("\n" + "=" * 60)
        print("📈 性能基准测试摘要")
        print("=" * 60)

        total_mean_time = 0
        test_count = 0

        for category, tests in results['tests'].items():
            if isinstance(tests, dict) and 'error' not in tests:
                print(f"\n{category}:")
                for test_name, metrics in tests.items():
                    if isinstance(metrics, dict) and 'mean' in metrics:
                        mean_time = metrics['mean'] * 1000000  # 转换为微秒
                        print(f"  {test_name}: {mean_time:.2f}μs")
                        total_mean_time += mean_time
                        test_count += 1

        if test_count > 0:
            avg_time = total_mean_time / test_count
            print(f"\n📊 平均执行时间: {avg_time:.2f}μs")
            print(f"🎯 性能等级: {'优秀' if avg_time < 100 else '良好' if avg_time < 500 else '一般'}")

    def save_benchmark_report(self, results: Dict[str, Any]):
        """保存基准测试报告"""
        filename = f"performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"g:/iMato/{filename}"

        # 添加性能评级
        performance_rating = self.calculate_performance_rating(results)
        results['performance_rating'] = performance_rating

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 性能基准报告已保存至: {filepath}")
        return filepath

    def calculate_performance_rating(self, results: Dict[str, Any]) -> str:
        """计算整体性能评级"""
        # 简单的性能评级逻辑
        total_time = 0
        test_count = 0

        for category, tests in results['tests'].items():
            if isinstance(tests, dict) and 'error' not in tests:
                for test_name, metrics in tests.items():
                    if isinstance(metrics, dict) and 'mean' in metrics:
                        total_time += metrics['mean'] * 1000000  # 微秒
                        test_count += 1

        if test_count == 0:
            return "无法评估"

        avg_time = total_time / test_count

        if avg_time < 50:
            return "卓越"
        elif avg_time < 100:
            return "优秀"
        elif avg_time < 200:
            return "良好"
        elif avg_time < 500:
            return "一般"
        else:
            return "需要优化"

def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    try:
        results = benchmark.run_comprehensive_benchmark()
        print(f"\n🎉 性能基准测试完成！整体评级: {results.get('performance_rating', '未知')}")
        return True
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
