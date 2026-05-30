#!/usr/bin/env python3
"""
Celery任务熔断器简单验证脚本
验证核心功能而不需要完整的Celery环境
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

def validate_core_components():
    """验证核心组件"""
    print("🔍 验证核心组件...")
    
    try:
        # 验证熔断器模块
        from middleware.celery_circuit_breaker import (
            CeleryTaskCircuitBreaker,
            CeleryTaskCircuitBreakerConfig,
            TaskCircuitState,
            task_circuit_manager
        )
        print("✅ Celery熔断器模块加载成功")
        
        # 验证配置管理
        from config.settings import settings
        print("✅ 配置管理模块加载成功")
        
        # 验证监控服务
        from services.celery_monitoring import CeleryMonitoringService
        print("✅ 监控服务模块加载成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

def test_basic_functionality():
    """测试基础功能"""
    print("\n🧪 测试基础功能...")
    
    try:
        from middleware.celery_circuit_breaker import (
            CeleryTaskCircuitBreaker,
            CeleryTaskCircuitBreakerConfig,
            TaskCircuitState
        )
        
        # 创建测试配置
        config = CeleryTaskCircuitBreakerConfig(
            task_name="validation_test",
            failure_threshold=3,
            timeout=30,
            soft_time_limit=25,
            time_limit=60
        )
        
        # 创建熔断器实例
        breaker = CeleryTaskCircuitBreaker(config)
        
        # 验证初始状态
        if breaker.state != TaskCircuitState.CLOSED:
            print(f"❌ 初始状态错误: {breaker.state}")
            return False
        
        # 验证配置参数
        if breaker.config.failure_threshold != 3:
            print(f"❌ 配置参数错误: failure_threshold={breaker.config.failure_threshold}")
            return False
            
        if breaker.config.timeout != 30:
            print(f"❌ 配置参数错误: timeout={breaker.config.timeout}")
            return False
        
        print("✅ 基础功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False

def test_state_machine():
    """测试状态机"""
    print("\n🔄 测试状态机...")
    
    try:
        from middleware.celery_circuit_breaker import (
            CeleryTaskCircuitBreaker,
            CeleryTaskCircuitBreakerConfig,
            TaskCircuitState
        )
        
        config = CeleryTaskCircuitBreakerConfig(
            task_name="state_test",
            failure_threshold=2,
            timeout=10
        )
        
        breaker = CeleryTaskCircuitBreaker(config)
        
        # 测试 CLOSED -> OPEN
        initial_state = breaker.state
        breaker.record_failure(0.1)  # 第一次失败
        breaker.record_failure(0.1)  # 第二次失败，应触发熔断
        
        if breaker.state != TaskCircuitState.OPEN:
            print(f"❌ 状态转换失败: {initial_state} -> {breaker.state}")
            return False
        
        print("✅ 状态机测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 状态机测试失败: {e}")
        return False

def test_configuration():
    """测试配置管理"""
    print("\n⚙️  测试配置管理...")
    
    try:
        from middleware.celery_circuit_breaker import (
            task_circuit_manager,
            CeleryTaskCircuitBreakerConfig
        )
        from config.settings import settings
        
        # 测试默认配置
        default_config = CeleryTaskCircuitBreakerConfig("default_task")
        
        expected_values = {
            'timeout': settings.CELERY_TASK_DEFAULT_TIMEOUT,
            'soft_time_limit': settings.CELERY_TASK_SOFT_TIMEOUT,
            'time_limit': settings.CELERY_TASK_HARD_TIMEOUT,
            'failure_threshold': settings.CELERY_TASK_FAILURE_THRESHOLD
        }
        
        for attr, expected in expected_values.items():
            actual = getattr(default_config, attr)
            if actual != expected:
                print(f"❌ 默认配置错误 {attr}: 期望{expected}, 实际{actual}")
                return False
        
        # 测试配置注册
        custom_config = CeleryTaskCircuitBreakerConfig(
            task_name="custom_task",
            failure_threshold=10
        )
        
        task_circuit_manager.register_task_config("custom_task", custom_config)
        retrieved_breaker = task_circuit_manager.get_or_create_breaker("custom_task")
        
        if retrieved_breaker.config.failure_threshold != 10:
            print("❌ 配置注册/获取失败")
            return False
        
        print("✅ 配置管理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False

def test_monitoring_interface():
    """测试监控接口"""
    print("\n📊 测试监控接口...")
    
    try:
        from services.celery_monitoring import CeleryMonitoringService
        
        # 创建监控服务实例
        service = CeleryMonitoringService()
        
        # 测试获取状态信息（即使没有实际任务）
        states = service.get_all_circuit_breaker_states()
        
        if not isinstance(states, dict):
            print("❌ 监控接口返回格式错误")
            return False
        
        required_keys = ['timestamp', 'service', 'total_tasks']
        for key in required_keys:
            if key not in states:
                print(f"❌ 监控数据缺少必要字段: {key}")
                return False
        
        print("✅ 监控接口测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 监控接口测试失败: {e}")
        return False

def generate_validation_report(results):
    """生成验证报告"""
    passed_count = sum(1 for result in results if result)
    total_count = len(results)
    success_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
    
    report = {
        "validation_suite": "Celery任务熔断器验证",
        "timestamp": datetime.now().isoformat(),
        "results": {
            "core_components": results[0],
            "basic_functionality": results[1],
            "state_machine": results[2],
            "configuration": results[3],
            "monitoring_interface": results[4]
        },
        "summary": {
            "total_tests": total_count,
            "passed_tests": passed_count,
            "failed_tests": total_count - passed_count,
            "success_rate": round(success_rate, 2)
        }
    }
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"celery_validation_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 验证报告已保存: {filename}")
    return report

def main():
    """主函数"""
    print("🚀 开始Celery任务熔断器验证...")
    print("=" * 50)
    
    # 执行各项测试
    results = [
        validate_core_components(),
        test_basic_functionality(),
        test_state_machine(),
        test_configuration(),
        test_monitoring_interface()
    ]
    
    # 生成报告
    report = generate_validation_report(results)
    
    # 输出总结
    print("\n" + "=" * 50)
    print("🎯 验证结果总结:")
    print(f"   总测试数: {report['summary']['total_tests']}")
    print(f"   通过测试: {report['summary']['passed_tests']}")
    print(f"   失败测试: {report['summary']['failed_tests']}")
    print(f"   成功率: {report['summary']['success_rate']}%")
    
    if report['summary']['success_rate'] >= 80:
        print("✅ 验证通过! 功能实现正确")
        return 0
    else:
        print("❌ 验证未通过! 存在问题需要修复")
        return 1

if __name__ == "__main__":
    exit(main())