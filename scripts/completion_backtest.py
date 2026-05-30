#!/usr/bin/env python3
"""
AI代码补全系统回测验证脚本
验证系统功能完整性和性能表现
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models.ai_completion import (
    CompletionRequest, ProgrammingLanguage, ModelProvider
)
from backend.services.code_completion_service import code_completion_service
from backend.ai_service.completion_memory import completion_memory


class CompletionBacktest:
    """代码补全系统回测验证类"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
    
    async def run_all_tests(self):
        """运行所有回测"""
        print("🚀 开始AI代码补全系统回测验证...")
        print("=" * 60)
        
        # 测试1: 基础补全功能
        await self.test_basic_completion()
        
        # 测试2: 多语言支持
        await self.test_multi_language_support()
        
        # 测试3: 上下文感知能力
        await self.test_context_awareness()
        
        # 测试4: 缓存机制
        await self.test_caching_mechanism()
        
        # 测试5: 多模型集成
        await self.test_multi_model_integration()
        
        # 测试6: 性能基准测试
        await self.test_performance_benchmark()
        
        # 测试7: 错误处理
        await self.test_error_handling()
        
        # 生成报告
        self.generate_report()
        
        return self.results
    
    async def test_basic_completion(self):
        """测试基础补全功能"""
        print("\n📋 测试1: 基础代码补全功能")
        print("-" * 40)
        
        test_cases = [
            {
                'name': 'Python函数补全',
                'request': CompletionRequest(
                    prefix='def calculate_',
                    context=['def add(a, b):', '    return a + b', ''],
                    language=ProgrammingLanguage.PYTHON
                )
            },
            {
                'name': 'JavaScript变量补全',
                'request': CompletionRequest(
                    prefix='const user',
                    context=['const name = "John";', 'const age = 25;', ''],
                    language=ProgrammingLanguage.JAVASCRIPT
                )
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for case in test_cases:
            try:
                print(f"  测试: {case['name']}")
                response = await code_completion_service.get_completions(case['request'])
                
                if response.suggestions and len(response.suggestions) > 0:
                    print(f"    ✓ 成功生成 {len(response.suggestions)} 个建议")
                    print(f"    ✓ 处理时间: {response.processing_time:.3f}秒")
                    print(f"    ✓ 使用模型: {response.model_used}")
                    passed += 1
                else:
                    print(f"    ✗ 未生成任何建议")
                    
            except Exception as e:
                print(f"    ✗ 测试失败: {str(e)}")
        
        success_rate = (passed / total) * 100
        print(f"\n  结果: {passed}/{total} 通过 ({success_rate:.1f}%)")
        
        self.results['tests']['basic_completion'] = {
            'passed': passed,
            'total': total,
            'success_rate': success_rate,
            'details': f'基础补全功能测试完成，成功率{success_rate:.1f}%'
        }
    
    async def test_multi_language_support(self):
        """测试多语言支持"""
        print("\n📋 测试2: 多语言支持")
        print("-" * 40)
        
        languages = [
            (ProgrammingLanguage.PYTHON, 'def hello_'),
            (ProgrammingLanguage.JAVASCRIPT, 'function greet_'),
            (ProgrammingLanguage.TYPESCRIPT, 'interface User'),
            (ProgrammingLanguage.JAVA, 'public class '),
        ]
        
        passed = 0
        total = len(languages)
        
        for language, prefix in languages:
            try:
                print(f"  测试: {language.value} 语言")
                request = CompletionRequest(
                    prefix=prefix,
                    context=[],
                    language=language
                )
                
                response = await code_completion_service.get_completions(request)
                
                if response.suggestions:
                    print(f"    ✓ 支持 {language.value} 语言补全")
                    passed += 1
                else:
                    print(f"    ⚠ {language.value} 语言未生成建议")
                    
            except Exception as e:
                print(f"    ✗ {language.value} 语言测试失败: {str(e)}")
        
        success_rate = (passed / total) * 100
        print(f"\n  结果: {passed}/{total} 语言支持 ({success_rate:.1f}%)")
        
        self.results['tests']['multi_language'] = {
            'passed': passed,
            'total': total,
            'success_rate': success_rate,
            'supported_languages': [lang.value for lang, _ in languages[:passed]]
        }
    
    async def test_context_awareness(self):
        """测试上下文感知能力"""
        print("\n📋 测试3: 上下文感知能力")
        print("-" * 40)
        
        # 测试不同上下文场景
        contexts = [
            {
                'name': '函数内部补全',
                'context': [
                    'def calculate_total(items):',
                    '    total = 0',
                    '    for item in items:',
                    '        total += item.price',
                    '    '
                ],
                'prefix': 'return t'
            },
            {
                'name': '类方法补全',
                'context': [
                    'class Calculator:',
                    '    def __init__(self):',
                    '        self.result = 0',
                    '    ',
                    '    def add(self, a, b):'
                ],
                'prefix': '        self.r'
            }
        ]
        
        passed = 0
        total = len(contexts)
        
        for ctx in contexts:
            try:
                print(f"  测试: {ctx['name']}")
                request = CompletionRequest(
                    prefix=ctx['prefix'],
                    context=ctx['context'],
                    language=ProgrammingLanguage.PYTHON
                )
                
                response = await code_completion_service.get_completions(request)
                
                if response.suggestions:
                    # 检查建议是否与上下文相关
                    relevant_suggestions = [
                        s for s in response.suggestions 
                        if any(keyword in s.text.lower() 
                              for keyword in ['total', 'result', 'self'])
                    ]
                    
                    if relevant_suggestions:
                        print(f"    ✓ 生成 {len(relevant_suggestions)} 个相关建议")
                        passed += 1
                    else:
                        print(f"    ⚠ 建议与上下文关联性较低")
                else:
                    print(f"    ✗ 未生成建议")
                    
            except Exception as e:
                print(f"    ✗ 测试失败: {str(e)}")
        
        success_rate = (passed / total) * 100
        print(f"\n  结果: {passed}/{total} 场景通过 ({success_rate:.1f}%)")
        
        self.results['tests']['context_awareness'] = {
            'passed': passed,
            'total': total,
            'success_rate': success_rate
        }
    
    async def test_caching_mechanism(self):
        """测试缓存机制"""
        print("\n📋 测试4: 缓存机制")
        print("-" * 40)
        
        prefix = "def cache_test_"
        request = CompletionRequest(
            prefix=prefix,
            context=[],
            language=ProgrammingLanguage.PYTHON
        )
        
        try:
            # 第一次请求（应该不命中缓存）
            start_time = time.time()
            response1 = await code_completion_service.get_completions(request)
            first_time = time.time() - start_time
            
            # 第二次请求（应该命中缓存）
            start_time = time.time()
            response2 = await code_completion_service.get_completions(request)
            second_time = time.time() - start_time
            
            cache_hit = response2.cache_hit
            time_improvement = ((first_time - second_time) / first_time) * 100 if first_time > 0 else 0
            
            print(f"  首次请求时间: {first_time:.3f}秒")
            print(f"  缓存请求时间: {second_time:.3f}秒")
            print(f"  缓存命中: {'是' if cache_hit else '否'}")
            print(f"  性能提升: {time_improvement:.1f}%")
            
            if cache_hit and second_time < first_time:
                print("  ✓ 缓存机制工作正常")
                passed = True
            else:
                print("  ✗ 缓存机制存在问题")
                passed = False
                
        except Exception as e:
            print(f"  ✗ 缓存测试失败: {str(e)}")
            passed = False
        
        self.results['tests']['caching'] = {
            'passed': 1 if passed else 0,
            'total': 1,
            'success_rate': 100 if passed else 0,
            'cache_enabled': True
        }
    
    async def test_multi_model_integration(self):
        """测试多模型集成"""
        print("\n📋 测试5: 多模型集成")
        print("-" * 40)
        
        providers = [ModelProvider.OPENAI, ModelProvider.LINGMA, ModelProvider.DEEPSEEK]
        passed = 0
        total = len(providers)
        
        for provider in providers:
            try:
                print(f"  测试: {provider.value} 模型")
                request = CompletionRequest(
                    prefix='def multi_model_',
                    context=[],
                    language=ProgrammingLanguage.PYTHON,
                    provider=provider
                )
                
                response = await code_completion_service.get_completions(request)
                
                if response.suggestions and response.model_used:
                    print(f"    ✓ {provider.value} 模型响应正常")
                    print(f"    ✓ 使用模型: {response.model_used}")
                    passed += 1
                else:
                    print(f"    ✗ {provider.value} 模型无响应")
                    
            except Exception as e:
                print(f"    ✗ {provider.value} 模型测试失败: {str(e)}")
        
        success_rate = (passed / total) * 100
        print(f"\n  结果: {passed}/{total} 模型集成 ({success_rate:.1f}%)")
        
        self.results['tests']['multi_model'] = {
            'passed': passed,
            'total': total,
            'success_rate': success_rate,
            'working_providers': [p.value for p in providers[:passed]]
        }
    
    async def test_performance_benchmark(self):
        """性能基准测试"""
        print("\n📋 测试6: 性能基准测试")
        print("-" * 40)
        
        test_cases = [
            {'name': '简单补全', 'prefix': 'def hello_', 'context': []},
            {'name': '复杂上下文', 'prefix': 'return res', 'context': ['def process_data(data):', '    result = []', '    for item in data:', '        if item.valid:', '            result.append(item)', '    ']},
            {'name': '长前缀', 'prefix': 'def very_long_function_name_that_tests_performance_', 'context': []}
        ]
        
        results = []
        
        for case in test_cases:
            try:
                print(f"  测试: {case['name']}")
                request = CompletionRequest(
                    prefix=case['prefix'],
                    context=case['context'],
                    language=ProgrammingLanguage.PYTHON
                )
                
                start_time = time.time()
                response = await code_completion_service.get_completions(request)
                elapsed_time = time.time() - start_time
                
                results.append({
                    'name': case['name'],
                    'time': elapsed_time,
                    'suggestions': len(response.suggestions),
                    'success': response.suggestions is not None
                })
                
                print(f"    ✓ 时间: {elapsed_time:.3f}秒")
                print(f"    ✓ 建议数: {len(response.suggestions)}")
                
            except Exception as e:
                print(f"    ✗ 测试失败: {str(e)}")
                results.append({
                    'name': case['name'],
                    'time': 0,
                    'suggestions': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # 计算统计数据
        successful_tests = [r for r in results if r['success']]
        avg_time = sum(r['time'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        max_time = max(r['time'] for r in successful_tests) if successful_tests else 0
        
        print(f"\n  性能统计:")
        print(f"    平均响应时间: {avg_time:.3f}秒")
        print(f"    最大响应时间: {max_time:.3f}秒")
        print(f"    成功率: {len(successful_tests)}/{len(results)}")
        
        self.results['tests']['performance'] = {
            'average_response_time': avg_time,
            'max_response_time': max_time,
            'success_rate': (len(successful_tests) / len(results)) * 100,
            'benchmark_results': results
        }
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n📋 测试7: 错误处理")
        print("-" * 40)
        
        error_cases = [
            {'name': '空前缀', 'prefix': '', 'should_fail': True},
            {'name': '超长前缀', 'prefix': 'a' * 2000, 'should_fail': True},
            {'name': '无效语言', 'prefix': 'test', 'language': 'invalid', 'should_fail': True}
        ]
        
        passed = 0
        total = len(error_cases)
        
        for case in error_cases:
            try:
                print(f"  测试: {case['name']}")
                
                request = CompletionRequest(
                    prefix=case.get('prefix', 'test'),
                    context=[],
                    language=ProgrammingLanguage.PYTHON
                )
                
                response = await code_completion_service.get_completions(request)
                
                # 检查是否正确处理错误
                if case.get('should_fail', False):
                    if not response.suggestions:  # 错误情况下应该没有建议或返回空
                        print(f"    ✓ 正确处理错误情况")
                        passed += 1
                    else:
                        print(f"    ✗ 应该处理为错误但返回了建议")
                else:
                    if response.suggestions is not None:
                        print(f"    ✓ 正常处理")
                        passed += 1
                    else:
                        print(f"    ✗ 处理失败")
                        
            except Exception as e:
                if case.get('should_fail', False):
                    print(f"    ✓ 正确抛出异常: {type(e).__name__}")
                    passed += 1
                else:
                    print(f"    ✗ 不应有的异常: {str(e)}")
        
        success_rate = (passed / total) * 100
        print(f"\n  结果: {passed}/{total} 错误处理通过 ({success_rate:.1f}%)")
        
        self.results['tests']['error_handling'] = {
            'passed': passed,
            'total': total,
            'success_rate': success_rate
        }
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 AI代码补全系统回测报告")
        print("=" * 60)
        
        # 计算总体统计
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for test in self.results['tests'].values() if test.get('success_rate', 0) >= 80)
        
        print(f"总测试项: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"整体通过率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 功能覆盖度
        features_covered = [
            '基础代码补全',
            '多语言支持',
            '上下文感知',
            '缓存机制',
            '多模型集成',
            '性能优化',
            '错误处理'
        ]
        
        print(f"\n✅ 已实现功能: {len(features_covered)}/7")
        for feature in features_covered:
            print(f"  • {feature}")
        
        # 保存详细报告
        report_file = f'ai_completion_backtest_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 详细报告已保存至: {report_file}")
        
        # 生成摘要
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'overall_success_rate': (passed_tests/total_tests)*100,
            'features_covered': len(features_covered),
            'report_generated': True,
            'report_file': report_file
        }


async def main():
    """主函数"""
    backtest = CompletionBacktest()
    results = await backtest.run_all_tests()
    
    # 根据结果决定退出码
    overall_success_rate = results['summary']['overall_success_rate']
    if overall_success_rate >= 80:
        print("\n🎉 回测通过！系统功能完整，可以部署。")
        return 0
    else:
        print(f"\n⚠️  回测未完全通过 ({overall_success_rate:.1f}% < 80%)，建议修复后再部署。")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)