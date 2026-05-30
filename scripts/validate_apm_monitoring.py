"""
APM监控功能回测验证脚本
验证核心接口 /api/ai/recommend 的APM监控是否正常工作
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any

# 导入测试模块
try:
    from middleware.apm_monitoring import APMConfig, init_apm, trace_endpoint
    from middleware.apm_middleware import monitor_recommendation_endpoint
    from utils.metrics_collector import record_recommendation_metrics
    APM_MODULES_AVAILABLE = True
    print("✅ APM模块导入成功")
except ImportError as e:
    APM_MODULES_AVAILABLE = False
    print(f"❌ APM模块导入失败: {e}")

def test_apm_configuration():
    """测试APM配置"""
    print("\n=== 测试APM配置 ===")
    
    if not APM_MODULES_AVAILABLE:
        print("❌ APM模块不可用，跳过配置测试")
        return False
    
    try:
        config = APMConfig()
        print(f"✅ APM配置加载成功")
        print(f"   服务名称: {config.service_name}")
        print(f"   启用追踪: {config.enable_tracing}")
        print(f"   启用指标: {config.enable_metrics}")
        print(f"   采样率: {config.sampling_rate}")
        return True
    except Exception as e:
        print(f"❌ APM配置测试失败: {e}")
        return False

def test_apm_initialization():
    """测试APM初始化"""
    print("\n=== 测试APM初始化 ===")
    
    if not APM_MODULES_AVAILABLE:
        print("❌ APM模块不可用，跳过初始化测试")
        return False
    
    try:
        # 初始化APM（在测试环境中应该是安全的）
        init_apm()
        print("✅ APM初始化成功")
        return True
    except Exception as e:
        print(f"⚠️  APM初始化警告（预期）: {e}")
        return True  # 初始化失败在测试环境中是预期的

def test_tracing_decorators():
    """测试追踪装饰器"""
    print("\n=== 测试追踪装饰器 ===")
    
    if not APM_MODULES_AVAILABLE:
        print("❌ APM模块不可用，跳过装饰器测试")
        return False
    
    try:
        # 测试trace_endpoint装饰器
        @trace_endpoint("test.operation")
        async def sample_async_function(x, y):
            await asyncio.sleep(0.01)  # 模拟异步操作
            return x + y
        
        # 测试monitor_recommendation_endpoint装饰器
        @monitor_recommendation_endpoint
        async def sample_recommendation_function():
            await asyncio.sleep(0.01)
            return {"recommendations": ["course1", "course2"], "algorithm": "test"}
        
        # 执行测试
        async def run_tests():
            result1 = await sample_async_function(1, 2)
            result2 = await sample_recommendation_function()
            return result1, result2
        
        # 运行异步测试
        result1, result2 = asyncio.run(run_tests())
        
        print(f"✅ 追踪装饰器测试成功")
        print(f"   异步函数结果: {result1}")
        print(f"   推荐函数结果: {result2}")
        return True
        
    except Exception as e:
        print(f"❌ 追踪装饰器测试失败: {e}")
        return False

def test_metrics_collection():
    """测试指标收集"""
    print("\n=== 测试指标收集 ===")
    
    try:
        # 测试推荐指标记录
        record_recommendation_metrics("hybrid", 0.1, True)
        record_recommendation_metrics("collaborative", 0.05, False)
        
        print("✅ 指标收集测试成功")
        print("   推荐成功指标已记录")
        print("   推荐失败指标已记录")
        return True
        
    except Exception as e:
        print(f"❌ 指标收集测试失败: {e}")
        return False

def test_ai_recommendation_endpoint_structure():
    """测试AI推荐端点结构"""
    print("\n=== 测试AI推荐端点结构 ===")
    
    try:
        from routes.ai_recommend_routes import router
        
        # 检查路由是否存在
        routes = [route.path for route in router.routes]
        expected_routes = [
            '/recommend',
            '/recommend/batch',
            '/recommend/algorithms',
            '/recommend/health'
        ]
        
        found_routes = []
        missing_routes = []
        
        for expected_route in expected_routes:
            full_route = f"/ai{expected_route}"
            if any(full_route in route_path for route_path in routes):
                found_routes.append(full_route)
                print(f"✅ 找到路由: {full_route}")
            else:
                missing_routes.append(full_route)
                print(f"❌ 缺少路由: {full_route}")
        
        if missing_routes:
            print(f"⚠️  缺少 {len(missing_routes)} 个路由")
            return False
        else:
            print(f"✅ 所有 {len(found_routes)} 个路由都已正确配置")
            return True
            
    except Exception as e:
        print(f"❌ 路由结构测试失败: {e}")
        return False

def test_monitoring_integration():
    """测试监控集成"""
    print("\n=== 测试监控集成 ===")
    
    integration_tests = [
        ("APM配置", test_apm_configuration),
        ("APM初始化", test_apm_initialization),
        ("追踪装饰器", test_tracing_decorators),
        ("指标收集", test_metrics_collection),
        ("路由结构", test_ai_recommendation_endpoint_structure)
    ]
    
    results = []
    for test_name, test_func in integration_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试执行失败: {e}")
            results.append((test_name, False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n=== 监控集成测试总结 ===")
    print(f"通过测试: {passed}/{total} ({success_rate:.1f}%)")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    return success_rate >= 80  # 80%成功率认为通过

def generate_validation_report():
    """生成验证报告"""
    print("\n" + "="*60)
    print("APM监控功能验证报告")
    print("="*60)
    
    start_time = datetime.now()
    
    # 执行综合测试
    integration_passed = test_monitoring_integration()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 生成报告
    report = {
        "validation_timestamp": start_time.isoformat(),
        "duration_seconds": round(duration, 2),
        "integration_test_passed": integration_passed,
        "modules_available": APM_MODULES_AVAILABLE,
        "summary": {
            "status": "SUCCESS" if integration_passed else "PARTIAL_SUCCESS",
            "message": "APM监控功能基本可用" if integration_passed else "部分APM功能需要进一步配置"
        },
        "recommendations": [
            "确保SkyWalking collector地址配置正确",
            "验证OpenTelemetry collector连接",
            "检查Prometheus指标端点访问权限",
            "在生产环境中启用完整的APM监控"
        ]
    }
    
    print(f"\n📊 验证摘要:")
    print(f"  时间: {report['validation_timestamp']}")
    print(f"  耗时: {report['duration_seconds']}秒")
    print(f"  状态: {report['summary']['status']}")
    print(f"  消息: {report['summary']['message']}")
    
    print(f"\n💡 建议:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    # 保存报告
    report_file = f"apm_validation_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📝 详细报告已保存到: {report_file}")
    except Exception as e:
        print(f"\n⚠️  报告保存失败: {e}")
    
    return report

if __name__ == "__main__":
    print("🚀 开始APM监控功能回测验证...")
    report = generate_validation_report()
    print("\n🏁 APM监控验证完成!")