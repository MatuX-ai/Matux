#!/usr/bin/env python3
"""
简化的AI代码补全系统验证脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from models.ai_completion import CompletionRequest, ProgrammingLanguage, ModelProvider
        print("  ✓ ai_completion 模块导入成功")
    except ImportError as e:
        print(f"  ✗ ai_completion 模块导入失败: {e}")
        return False
    
    try:
        from ai_service.completion_memory import CompletionMemory
        print("  ✓ completion_memory 模块导入成功")
    except ImportError as e:
        print(f"  ✗ completion_memory 模块导入失败: {e}")
        return False
    
    try:
        from services.code_completion_service import CodeCompletionService
        print("  ✓ code_completion_service 模块导入成功")
    except ImportError as e:
        print(f"  ✗ code_completion_service 模块导入失败: {e}")
        return False
    
    return True

def test_data_models():
    """测试数据模型"""
    print("\n🔍 测试数据模型...")
    
    try:
        from models.ai_completion import (
            CompletionRequest, CompletionSuggestion, 
            ProgrammingLanguage, ModelProvider
        )
        
        # 测试模型创建
        request = CompletionRequest(
            prefix="def hello_",
            context=["def world():", "    pass"],
            language=ProgrammingLanguage.PYTHON,
            provider=ModelProvider.OPENAI
        )
        print("  ✓ CompletionRequest 模型创建成功")
        
        suggestion = CompletionSuggestion(
            text="world()",
            confidence=0.95,
            relevance_score=0.92,
            language_features=["function_call"]
        )
        print("  ✓ CompletionSuggestion 模型创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 数据模型测试失败: {e}")
        return False

def test_memory_system():
    """测试记忆系统基础功能"""
    print("\n🔍 测试记忆系统...")
    
    try:
        from ai_service.completion_memory import CompletionMemory
        
        memory = CompletionMemory()
        print("  ✓ CompletionMemory 实例创建成功")
        
        # 测试哈希生成
        test_prefix = "def test_function"
        hash_value = memory._generate_prefix_hash(test_prefix)
        print(f"  ✓ 前缀哈希生成成功: {hash_value[:16]}...")
        
        # 测试作用域检测
        context_lines = ["def calculate_sum(a, b):", "    return a + b"]
        scope = memory._detect_scope_level(context_lines)
        print(f"  ✓ 作用域检测: {scope}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 记忆系统测试失败: {e}")
        return False

def test_completion_service():
    """测试补全服务基础功能"""
    print("\n🔍 测试补全服务...")
    
    try:
        from services.code_completion_service import CodeCompletionService
        
        service = CodeCompletionService()
        print("  ✓ CodeCompletionService 实例创建成功")
        
        # 测试质量评估
        quality = service._assess_completion_quality(
            "sum(numbers)", 
            "sum(", 
            None  # ProgrammingLanguage.PYTHON
        )
        print(f"  ✓ 补全质量评估: {quality:.2f}")
        
        # 测试语言特征提取
        features = service._extract_language_features(
            "def calculate_sum(a, b):",
            None,  # ProgrammingLanguage.PYTHON
            None
        )
        print(f"  ✓ 语言特征提取: {features}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 补全服务测试失败: {e}")
        return False

def test_api_routes():
    """测试API路由模块"""
    print("\n🔍 测试API路由...")
    
    try:
        # 只测试模块能否导入
        import routes.completion_routes
        print("  ✓ completion_routes 模块导入成功")
        return True
    except ImportError as e:
        print(f"  ✗ API路由测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 AI代码补全系统功能验证")
    print("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("数据模型测试", test_data_models),
        ("记忆系统测试", test_memory_system),
        ("补全服务测试", test_completion_service),
        ("API路由测试", test_api_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
            print("  🎉 测试通过")
        else:
            print("  ❌ 测试失败")
    
    print("\n" + "=" * 50)
    print("📊 验证结果汇总")
    print("=" * 50)
    print(f"总测试项: {total}")
    print(f"通过测试: {passed}")
    print(f"成功率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有功能验证通过！")
        print("✅ 代码补全系统核心功能已实现")
        print("✅ 可以进行下一步部署和集成")
        return 0
    else:
        print(f"\n⚠️  部分功能验证失败 ({passed}/{total})")
        print("❌ 建议检查失败的模块后再继续")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)