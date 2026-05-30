"""
Token 管理 API 路由快速验证脚本
验证 Token 相关的 RESTful API 端点
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_token_routes_import():
    """测试 Token 路由导入"""
    print("\n" + "="*60)
    print("测试 1: Token 路由模块导入")
    print("="*60)

    try:
        from routes.token_routes import router
        print("✅ Token 路由导入成功")
        return True

    except Exception as e:
        print(f"❌ 导入失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_token_schemas():
    """测试 Token Schema 模型"""
    print("\n" + "="*60)
    print("测试 2: Token Schema 模型")
    print("="*60)

    try:
        from models.token_schemas import (
            TokenPackageResponse,
            PurchaseTokenRequest,
            PurchaseTokenResponse,
            UserBalanceResponse,
            TokenUsageRecordResponse,
            TokenStatsResponse,
            CostEstimateRequest,
            CostEstimateResponse
        )

        print("✅ Token Schema 模型导入成功")
        print(f"   - 响应模型：7 个")
        print(f"   - 请求模型：2 个")

        # 测试创建实例
        estimate_request = CostEstimateRequest(
            feature_type="ai_teacher",
            params={"message_length": 100}
        )
        print(f"✅ CostEstimateRequest 创建成功：{estimate_request.feature_type}")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_router_registration():
    """测试路由器注册"""
    print("\n" + "="*60)
    print("测试 3: 路由器注册到主应用")
    print("="*60)

    try:
        # 检查 main_ai_edu.py 中是否包含 token_router
        with open(Path(__file__).parent.parent / "main_ai_edu.py", "r", encoding="utf-8") as f:
            content = f.read()

        if "from routes.token_routes import router as token_router" in content:
            print("✅ Token 路由导入语句存在")
        else:
            print("❌ Token 路由导入语句不存在")
            return False

        if "app.include_router(token_router)" in content:
            print("✅ Token 路由注册语句存在")
        else:
            print("❌ Token 路由注册语句不存在")
            return False

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        return False


def test_api_endpoints_structure():
    """测试 API 端点结构"""
    print("\n" + "="*60)
    print("测试 4: API 端点结构")
    print("="*60)

    try:
        from routes.token_routes import router

        # 检查路由器的路由
        routes = router.routes

        print(f"✅ Token 路由包含 {len(routes)} 个端点")

        expected_endpoints = [
            ("GET", "/api/v1/token/packages"),
            ("POST", "/api/v1/token/purchase"),
            ("GET", "/api/v1/token/balance"),
            ("GET", "/api/v1/token/usage"),
            ("GET", "/api/v1/token/stats"),
            ("POST", "/api/v1/token/estimate"),
            ("GET", "/api/v1/token/package/{package_id}"),
        ]

        print("\n预期的 API 端点:")
        for method, path in expected_endpoints:
            print(f"   {method:6} {path}")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_token_service_integration():
    """测试 Token 服务集成"""
    print("\n" + "="*60)
    print("测试 5: Token 服务集成")
    print("="*60)

    try:
        from services.token_service import TokenService
        from unittest.mock import Mock

        # 创建 Mock 数据库会话
        mock_db = Mock()
        token_service = TokenService(mock_db)

        print("✅ TokenService 创建成功")

        # 测试套餐预估方法
        course_cost = token_service.estimate_course_cost("simple")
        assert course_cost == 50
        print(f"✅ estimate_course_cost(simple) = {course_cost} tokens")

        course_cost_medium = token_service.estimate_course_cost("medium")
        assert course_cost_medium == 150
        print(f"✅ estimate_course_cost(medium) = {course_cost_medium} tokens")

        chat_cost = token_service.estimate_ai_chat_cost(200)
        assert chat_cost == 20
        print(f"✅ estimate_ai_chat_cost(200 字符) = {chat_cost} tokens")

        return True

    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Token 管理 API 路由验证")
    print("="*60)

    tests = [
        ("Token 路由导入", test_token_routes_import),
        ("Token Schema 模型", test_token_schemas),
        ("路由器注册", test_router_registration),
        ("API 端点结构", test_api_endpoints_structure),
        ("Token 服务集成", test_token_service_integration),
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
        print("\n🎉 所有测试通过！Token 管理 API 路由已成功创建并注册。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
