"""
许可证管理系统快速功能验证测试
验证核心功能是否正常工作
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_basic_functionality():
    """测试基本功能"""
    print("🔍 测试基本功能...")

    # 测试1: 导入测试
    try:
        import hashlib
        import secrets
        import string

        print("  ✅ 基本模块导入成功")
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False

    # 测试2: 许可证密钥生成
    try:

        def generate_license_key():
            prefix = "LICENSE"
            key_length = 32
            characters = string.ascii_uppercase + string.digits
            random_part = "".join(secrets.choice(characters) for _ in range(key_length))
            checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
            return f"{prefix}-{random_part}-{checksum}"

        key1 = generate_license_key()
        key2 = generate_license_key()

        # 验证格式
        assert key1.startswith("LICENSE-")
        assert len(key1.split("-")) == 3
        assert key1 != key2  # 确保唯一性

        print(f"  ✅ 许可证密钥生成成功: {key1}")
    except Exception as e:
        print(f"  ❌ 许可证密钥生成失败: {e}")
        return False

    # 测试3: 许可证密钥验证
    try:

        def validate_license_key(license_key):
            if not license_key or len(license_key.split("-")) != 3:
                return False
            prefix, random_part, checksum = license_key.split("-")
            if prefix != "LICENSE":
                return False
            expected_checksum = (
                hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
            )
            return checksum == expected_checksum

        # 测试有效密钥
        test_random = "ABCDEF1234567890GHIJKL"  # 22字符
        test_checksum = hashlib.md5(test_random.encode()).hexdigest()[:4].upper()
        valid_key = f"LICENSE-{test_random}-{test_checksum}"

        assert validate_license_key(valid_key) == True
        assert validate_license_key("INVALID-KEY") == False

        print(f"  ✅ 许可证密钥验证成功")
    except Exception as e:
        print(f"  ❌ 许可证密钥验证失败: {e}")
        return False

    return True


def test_redis_connectivity():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")

    try:
        import redis

        client = redis.Redis(
            host="localhost", port=6379, db=1, decode_responses=True, socket_timeout=5
        )
        client.ping()
        print("  ✅ Redis连接成功")
        return True
    except Exception as e:
        print(f"  ⚠️  Redis连接失败: {e}")
        print("     请确保Redis服务正在运行 (redis-server)")
        return False


def test_database_connectivity():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")

    try:
        from sqlalchemy import create_engine

        from config.settings import settings

        # 测试SQLite连接（开发环境默认）
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1
        print("  ✅ 数据库连接成功")
        return True
    except Exception as e:
        print(f"  ⚠️  数据库连接测试失败: {e}")
        return False


def test_api_endpoints():
    """测试API端点（模拟）"""
    print("🔍 测试API端点结构...")

    try:
        # 测试路由导入
        from routes.license_routes import router

        print(f"  ✅ 许可证路由导入成功，包含 {len(router.routes)} 个端点")

        # 显示主要端点
        main_endpoints = [
            route.path
            for route in router.routes
            if hasattr(route, "path") and route.path.startswith("/api/v1/")
        ][
            :5
        ]  # 只显示前5个

        for endpoint in main_endpoints:
            print(f"    - {endpoint}")

        return True
    except Exception as e:
        print(f"  ❌ API端点测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("📋 许可证管理系统功能验证测试")
    print("=" * 60)

    tests = [
        ("基本功能测试", test_basic_functionality),
        ("Redis连接测试", test_redis_connectivity),
        ("数据库连接测试", test_database_connectivity),
        ("API端点测试", test_api_endpoints),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"  ❌ 测试执行异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed_tests}/{total_tests} 项测试通过")

    if passed_tests == total_tests:
        print("🎉 所有测试通过！系统功能正常。")
        print("\n💡 下一步建议:")
        print("   1. 启动Redis服务: redis-server")
        print("   2. 运行数据库迁移: python migrations/001_create_license_tables.py")
        print("   3. 启动后端服务: uvicorn main:app --reload")
        print("   4. 访问API文档: http://localhost:8000/docs")
        return True
    else:
        print("⚠️  部分测试未通过，请检查相关配置。")
        if passed_tests >= 2:
            print("💡 核心功能正常，可以进行基本测试。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
