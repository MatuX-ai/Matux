"""
AI 计费功能快速验证脚本
验证 Token 计费装饰器、降级开关和 AI 服务集成
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_token_billing_decorator():
    """测试 Token 计费装饰器"""
    print("\n" + "="*60)
    print("测试 1: Token 计费装饰器")
    print("="*60)

    try:
        from utils.decorators import TokenBillingDecorator
        from services.token_service import TokenService
        from unittest.mock import Mock, MagicMock

        # 创建 Mock 数据库会话
        mock_db = Mock()
        token_service = TokenService(mock_db)
        billing_decorator = TokenBillingDecorator(token_service)

        print("✅ TokenBillingDecorator 创建成功")
        print(
            f"   - 计费状态：{'启用' if billing_decorator.billing_enabled else '禁用'}")
        print(f"   - 方法：consume_tokens, check_balance_only")

        # 测试降级开关
        billing_decorator.disable_billing()
        assert billing_decorator.billing_enabled == False
        print("✅ 降级开关测试通过 (disable)")

        billing_decorator.enable_billing()
        assert billing_decorator.billing_enabled == True
        print("✅ 降级开关测试通过 (enable)")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_config():
    """测试降级开关配置"""
    print("\n" + "="*60)
    print("测试 2: AI 降级开关配置")
    print("="*60)

    try:
        from config.ai_fallback_config import ai_fallback_config

        print("✅ AIFallbackConfig 导入成功")
        print(f"   - 全局计费开关：{ai_fallback_config.BILLING_ENABLED}")
        print(f"   - 功能开关：{list(ai_fallback_config.FEATURE_FALLBACK.keys())}")
        print(f"   - 免费额度：{ai_fallback_config.DAILY_FREE_TOKENS}")

        # 测试功能检查
        assert ai_fallback_config.is_feature_enabled("ai_teacher") == True
        print("✅ 功能检查测试通过")

        # 测试降级策略
        strategy = ai_fallback_config.get_fallback_strategy(
            "course_generation")
        assert strategy == "block"
        print(f"✅ 降级策略测试通过 (course_generation: {strategy})")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        return False


def test_llm_assistant_billing():
    """测试 LLM 助手服务 Token 计费"""
    print("\n" + "="*60)
    print("测试 3: LLM 助手服务计费集成")
    print("="*60)

    try:
        from services.llm_assistant_service import LLMAssistantService
        from unittest.mock import Mock

        # 创建 Mock 数据库会话
        mock_db = Mock()
        assistant = LLMAssistantService(mock_db)

        print("✅ LLMAssistantService 创建成功（带 Token 计费）")
        print(
            f"   - 计费装饰器：{'已初始化' if hasattr(assistant, 'billing') else '未初始化'}")

        if hasattr(assistant, 'billing'):
            print(
                f"   - 计费状态：{'启用' if assistant.billing.billing_enabled else '禁用'}")
            print("✅ Token 计费集成测试通过")
        else:
            print("⚠️  计费装饰器未正确初始化")
            return False

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_course_generator_billing():
    """测试课程生成器 Token 计费"""
    print("\n" + "="*60)
    print("测试 4: 课程生成器计费集成")
    print("="*60)

    try:
        from ai_service.dynamic_course import DynamicCourseGenerator
        from unittest.mock import Mock

        # 创建 Mock 数据库会话
        mock_db = Mock()
        generator = DynamicCourseGenerator(mock_db)

        print("✅ DynamicCourseGenerator 创建成功（带 Token 计费）")
        print(
            f"   - 计费装饰器：{'已初始化' if hasattr(generator, 'billing') else '未初始化'}")

        if hasattr(generator, 'billing'):
            print(
                f"   - 计费状态：{'启用' if generator.billing.billing_enabled else '禁用'}")
            print("✅ Token 计费集成测试通过")
        else:
            print("⚠️  计费装饰器未正确初始化")
            return False

        # 测试复杂度评估方法
        from ai_service.dynamic_course import DynamicCourseRequest, StudentProfile

        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=13,
                learning_style="visual",
                interests=["编程"],
                learning_goals=["学习 Python"]
            ),
            subject_area="计算机科学",
            learning_objectives=["理解变量"],
            difficulty_level="beginner",
            project_type="实践项目",
            time_constraint=20,
            language="zh-CN"
        )

        complexity = generator._evaluate_complexity(request)
        print(f"✅ 复杂度评估测试通过：{complexity}")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("AI 功能计费点集成验证")
    print("="*60)

    tests = [
        ("Token 计费装饰器", test_token_billing_decorator),
        ("AI 降级开关配置", test_fallback_config),
        ("LLM 助手计费", test_llm_assistant_billing),
        ("课程生成器计费", test_course_generator_billing),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计：{passed}/{total} 测试通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！AI 计费功能已成功集成。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
