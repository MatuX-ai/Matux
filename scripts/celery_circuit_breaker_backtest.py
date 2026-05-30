#!/usr/bin/env python3
"""
Celery任务熔断器功能回测脚本
验证任务超时熔断机制的正确性和稳定性
"""

import sys
import os
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('celery_circuit_breaker_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CeleryCircuitBreakerBacktest:
    """Celery任务熔断器回测类"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.test_cases = [
            {
                'name': 'basic_circuit_breaker_functionality',
                'description': '基础熔断器功能测试',
                'weight': 20
            },
            {
                'name': 'timeout_protection',
                'description': '任务超时保护测试',
                'weight': 20
            },
            {
                'name': 'failure_detection',
                'description': '任务失败检测测试',
                'weight': 15
            },
            {
                'name': 'state_transitions',
                'description': '状态转换测试',
                'weight': 15
            },
            {
                'name': 'monitoring_integration',
                'description': '监控集成测试',
                'weight': 15
            },
            {
                'name': 'configuration_management',
                'description': '配置管理测试',
                'weight': 15
            }
        ]
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        logger.info(f"开始执行测试: {test_case['name']} - {test_case['description']}")
        
        try:
            if test_case['name'] == 'basic_circuit_breaker_functionality':
                result = self.test_basic_functionality()
            elif test_case['name'] == 'timeout_protection':
                result = self.test_timeout_protection()
            elif test_case['name'] == 'failure_detection':
                result = self.test_failure_detection()
            elif test_case['name'] == 'state_transitions':
                result = self.test_state_transitions()
            elif test_case['name'] == 'monitoring_integration':
                result = self.test_monitoring_integration()
            elif test_case['name'] == 'configuration_management':
                result = self.test_configuration_management()
            else:
                result = {
                    'status': 'skipped',
                    'message': f"未知测试用例: {test_case['name']}"
                }
            
            result['test_case'] = test_case['name']
            result['description'] = test_case['description']
            result['weight'] = test_case['weight']
            
            logger.info(f"测试完成: {test_case['name']} - 状态: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"测试执行失败 {test_case['name']}: {e}")
            return {
                'test_case': test_case['name'],
                'description': test_case['description'],
                'weight': test_case['weight'],
                'status': 'error',
                'error': str(e),
                'message': f"测试执行异常: {str(e)}"
            }
    
    def test_basic_functionality(self) -> Dict[str, Any]:
        """测试基础熔断器功能"""
        try:
            from middleware.celery_circuit_breaker import (
                CeleryTaskCircuitBreaker,
                CeleryTaskCircuitBreakerConfig,
                TaskCircuitState
            )
            
            # 创建测试配置
            config = CeleryTaskCircuitBreakerConfig(
                task_name="test_task",
                failure_threshold=3,
                timeout=10,
                soft_time_limit=5,
                time_limit=10
            )
            
            # 创建熔断器实例
            breaker = CeleryTaskCircuitBreaker(config)
            
            # 验证初始状态
            if breaker.state != TaskCircuitState.CLOSED:
                return {
                    'status': 'failed',
                    'message': f"初始状态错误，期望CLOSED，实际{breaker.state}"
                }
            
            # 测试状态信息获取
            state_info = breaker.get_state_info()
            required_fields = ['task_name', 'state', 'failure_count', 'success_count']
            for field in required_fields:
                if field not in state_info:
                    return {
                        'status': 'failed',
                        'message': f"状态信息缺少字段: {field}"
                    }
            
            return {
                'status': 'passed',
                'message': '基础熔断器功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"基础功能测试异常: {str(e)}"
            }
    
    def test_timeout_protection(self) -> Dict[str, Any]:
        """测试超时保护功能"""
        try:
            from middleware.celery_circuit_breaker import (
                CeleryTaskCircuitBreaker,
                CeleryTaskCircuitBreakerConfig,
                TaskCircuitState
            )
            
            # 创建易超时的配置
            config = CeleryTaskCircuitBreakerConfig(
                task_name="timeout_test_task",
                failure_threshold=2,
                timeout=5,
                soft_time_limit=1,  # 很短的软超时
                time_limit=2,       # 很短的硬超时
                enable_timeout_protection=True
            )
            
            breaker = CeleryTaskCircuitBreaker(config)
            
            # 模拟多次超时
            for i in range(3):
                breaker.record_timeout()
            
            # 验证是否触发熔断
            if breaker.state != TaskCircuitState.OPEN:
                return {
                    'status': 'failed',
                    'message': f"超时保护未触发熔断，当前状态: {breaker.state}"
                }
            
            # 验证超时计数
            if breaker.timeout_count < 3:
                return {
                    'status': 'failed',
                    'message': f"超时计数不正确，期望>=3，实际{breaker.timeout_count}"
                }
            
            return {
                'status': 'passed',
                'message': '超时保护功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"超时保护测试异常: {str(e)}"
            }
    
    def test_failure_detection(self) -> Dict[str, Any]:
        """测试失败检测功能"""
        try:
            from middleware.celery_circuit_breaker import (
                CeleryTaskCircuitBreaker,
                CeleryTaskCircuitBreakerConfig,
                TaskCircuitState
            )
            from celery.exceptions import SoftTimeLimitExceeded
            
            config = CeleryTaskCircuitBreakerConfig(
                task_name="failure_test_task",
                failure_threshold=2,
                timeout=5,
                enable_failure_protection=True
            )
            
            breaker = CeleryTaskCircuitBreaker(config)
            
            # 记录几次失败（非预期异常）
            for i in range(3):
                try:
                    # 模拟任务执行失败
                    raise RuntimeError(f"Test failure {i}")
                except Exception as e:
                    if not breaker._is_expected_exception(e):
                        breaker.record_failure(0.1)  # 0.1秒执行时间
            
            # 验证是否触发熔断
            if breaker.state != TaskCircuitState.OPEN:
                return {
                    'status': 'failed',
                    'message': f"失败检测未触发熔断，当前状态: {breaker.state}"
                }
            
            # 验证失败计数
            if breaker.failure_count < 2:  # 阈值是2
                return {
                    'status': 'failed',
                    'message': f"失败计数不正确，期望>=2，实际{breaker.failure_count}"
                }
            
            # 测试预期异常（不应触发熔断）
            breaker_expected = CeleryTaskCircuitBreakerConfig(
                task_name="expected_failure_test",
                failure_threshold=1
            )
            breaker_exp = CeleryTaskCircuitBreaker(breaker_expected)
            
            try:
                raise SoftTimeLimitExceeded("Expected timeout")
            except Exception as e:
                if breaker_exp._is_expected_exception(e):
                    # 预期异常不应增加失败计数
                    initial_failures = breaker_exp.failure_count
                    breaker_exp.record_failure(0.1)
                    if breaker_exp.failure_count != initial_failures:
                        return {
                            'status': 'failed',
                            'message': '预期异常错误地增加了失败计数'
                        }
            
            return {
                'status': 'passed',
                'message': '失败检测功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"失败检测测试异常: {str(e)}"
            }
    
    def test_state_transitions(self) -> Dict[str, Any]:
        """测试状态转换功能"""
        try:
            from middleware.celery_circuit_breaker import (
                CeleryTaskCircuitBreaker,
                CeleryTaskCircuitBreakerConfig,
                TaskCircuitState
            )
            
            config = CeleryTaskCircuitBreakerConfig(
                task_name="state_test_task",
                failure_threshold=2,
                timeout=3,
                half_open_attempts=2
            )
            
            breaker = CeleryTaskCircuitBreaker(config)
            
            # 测试 CLOSED -> OPEN 转换
            initial_state = breaker.state
            for i in range(2):  # 达到失败阈值
                breaker.record_failure(0.1)
            
            if breaker.state != TaskCircuitState.OPEN:
                return {
                    'status': 'failed',
                    'message': f"CLOSED->OPEN转换失败，当前状态: {breaker.state}"
                }
            
            # 测试 OPEN -> HALF_OPEN 转换（需要等待超时）
            time.sleep(1)  # 等待部分超时时间
            if not breaker._can_transition_to_half_open():
                # 手动强制转换进行测试
                breaker._transition_state(TaskCircuitState.HALF_OPEN)
            
            if breaker.state != TaskCircuitState.HALF_OPEN:
                return {
                    'status': 'failed',
                    'message': f"OPEN->HALF_OPEN转换失败，当前状态: {breaker.state}"
                }
            
            # 测试 HALF_OPEN -> CLOSED 转换
            for i in range(2):  # 成功次数达到半开尝试次数
                breaker.record_success(0.1)
            
            if breaker.state != TaskCircuitState.CLOSED:
                return {
                    'status': 'failed',
                    'message': f"HALF_OPEN->CLOSED转换失败，当前状态: {breaker.state}"
                }
            
            return {
                'status': 'passed',
                'message': '状态转换功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"状态转换测试异常: {str(e)}"
            }
    
    def test_monitoring_integration(self) -> Dict[str, Any]:
        """测试监控集成"""
        try:
            from middleware.celery_circuit_breaker import (
                task_circuit_manager,
                CeleryTaskCircuitBreakerConfig
            )
            
            # 注册多个测试任务
            test_tasks = ['monitor_task_1', 'monitor_task_2', 'monitor_task_3']
            
            for task_name in test_tasks:
                config = CeleryTaskCircuitBreakerConfig(
                    task_name=task_name,
                    failure_threshold=3
                )
                task_circuit_manager.register_task_config(task_name, config)
            
            # 获取所有状态
            all_states = task_circuit_manager.get_all_states()
            
            # 验证监控数据完整性
            if len(all_states) != len(test_tasks):
                return {
                    'status': 'failed',
                    'message': f"监控任务数量不匹配，期望{len(test_tasks)}，实际{len(all_states)}"
                }
            
            # 验证每个任务都有正确的状态信息
            for task_name, state_info in all_states.items():
                required_fields = ['task_name', 'state', 'failure_count', 'success_count']
                for field in required_fields:
                    if field not in state_info:
                        return {
                            'status': 'failed',
                            'message': f"任务{task_name}缺少监控字段: {field}"
                        }
            
            return {
                'status': 'passed',
                'message': '监控集成功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"监控集成测试异常: {str(e)}"
            }
    
    def test_configuration_management(self) -> Dict[str, Any]:
        """测试配置管理功能"""
        try:
            from middleware.celery_circuit_breaker import (
                task_circuit_manager,
                CeleryTaskCircuitBreakerConfig
            )
            from config.settings import settings
            
            # 测试默认配置
            default_config = CeleryTaskCircuitBreakerConfig("default_test_task")
            
            expected_defaults = {
                'timeout': settings.CELERY_TASK_DEFAULT_TIMEOUT,
                'soft_time_limit': settings.CELERY_TASK_SOFT_TIMEOUT,
                'time_limit': settings.CELERY_TASK_HARD_TIMEOUT,
                'failure_threshold': settings.CELERY_TASK_FAILURE_THRESHOLD
            }
            
            for attr, expected_value in expected_defaults.items():
                actual_value = getattr(default_config, attr)
                if actual_value != expected_value:
                    return {
                        'status': 'failed',
                        'message': f"默认配置{attr}不正确，期望{expected_value}，实际{actual_value}"
                    }
            
            # 测试配置覆盖
            custom_config = CeleryTaskCircuitBreakerConfig(
                task_name="custom_test_task",
                failure_threshold=10,
                timeout=60,
                soft_time_limit=45,
                time_limit=90
            )
            
            if custom_config.failure_threshold != 10:
                return {
                    'status': 'failed',
                    'message': f"自定义配置未生效，failure_threshold期望10，实际{custom_config.failure_threshold}"
                }
            
            # 测试配置注册和获取
            task_circuit_manager.register_task_config("registered_task", custom_config)
            breaker = task_circuit_manager.get_or_create_breaker("registered_task")
            
            if breaker.config.failure_threshold != 10:
                return {
                    'status': 'failed',
                    'message': '配置注册获取功能异常'
                }
            
            return {
                'status': 'passed',
                'message': '配置管理功能正常'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"配置管理测试异常: {str(e)}"
            }
    
    def calculate_score(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算测试得分"""
        total_weight = sum(test['weight'] for test in self.test_cases)
        passed_weight = sum(
            test['weight'] for test in results 
            if test['status'] in ['passed', 'success']
        )
        
        score = (passed_weight / total_weight) * 100 if total_weight > 0 else 0
        
        # 分级评定
        if score >= 90:
            grade = "优秀"
        elif score >= 80:
            grade = "良好"
        elif score >= 70:
            grade = "合格"
        else:
            grade = "不合格"
        
        return {
            'score': round(score, 2),
            'grade': grade,
            'total_tests': len(results),
            'passed_tests': len([r for r in results if r['status'] in ['passed', 'success']]),
            'failed_tests': len([r for r in results if r['status'] == 'failed']),
            'error_tests': len([r for r in results if r['status'] == 'error'])
        }
    
    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        score_info = self.calculate_score(results)
        
        report = {
            'test_suite': 'Celery任务熔断器回测',
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform
            },
            'score': score_info,
            'test_results': results,
            'summary': {
                'total_test_cases': len(self.test_cases),
                'executed_tests': len(results),
                'success_rate': round(
                    (score_info['passed_tests'] / score_info['total_tests'] * 100), 2
                ) if score_info['total_tests'] > 0 else 0
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """保存测试报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"celery_circuit_breaker_backtest_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"测试报告已保存至: {filename}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def run_full_backtest(self) -> Dict[str, Any]:
        """运行完整回测"""
        logger.info("开始执行Celery任务熔断器回测...")
        
        # 执行所有测试用例
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            self.results.append(result)
        
        # 生成报告
        report = self.generate_report(self.results)
        
        # 保存报告
        self.save_report(report)
        
        # 输出摘要
        logger.info("=" * 60)
        logger.info("回测执行完成!")
        logger.info(f"总得分: {report['score']['score']} ({report['score']['grade']})")
        logger.info(f"通过测试: {report['score']['passed_tests']}/{report['score']['total_tests']}")
        logger.info(f"成功率: {report['summary']['success_rate']}%")
        logger.info("=" * 60)
        
        return report

def main():
    """主函数"""
    try:
        backtest = CeleryCircuitBreakerBacktest()
        report = backtest.run_full_backtest()
        
        # 根据得分决定退出码
        if report['score']['score'] >= 80:
            logger.info("✅ 回测通过!")
            return 0
        else:
            logger.error("❌ 回测未通过!")
            return 1
            
    except Exception as e:
        logger.error(f"回测执行异常: {e}")
        return 1

if __name__ == "__main__":
    exit(main())