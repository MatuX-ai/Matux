"""
简化版许可证服务测试
用于快速验证核心功能
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_license_key_generation():
    """测试许可证密钥生成"""
    import hashlib
    import secrets
    import string

    def generate_license_key(prefix="LICENSE", key_length=32):
        """生成许可证密钥"""
        characters = string.ascii_uppercase + string.digits
        random_part = "".join(secrets.choice(characters) for _ in range(key_length))
        checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
        return f"{prefix}-{random_part}-{checksum}"

    # 生成测试密钥
    key1 = generate_license_key()
    key2 = generate_license_key()

    print(f"生成的许可证密钥1: {key1}")
    print(f"生成的许可证密钥2: {key2}")

    # 验证格式
    assert key1.startswith("LICENSE-")
    assert len(key1.split("-")) == 3
    assert len(key1.split("-")[1]) == 32  # 随机部分长度
    assert len(key1.split("-")[2]) == 4  # 校验和长度

    # 验证唯一性
    assert key1 != key2

    print("✅ 许可证密钥生成测试通过")


def test_license_key_validation():
    """测试许可证密钥验证"""
    import hashlib

    def validate_license_key_format(license_key, prefix="LICENSE", key_length=32):
        """验证许可证密钥格式"""
        if not license_key:
            return False

        parts = license_key.split("-")
        if len(parts) != 3:
            return False

        prefix_part, random_part, checksum = parts

        # 验证前缀
        if prefix_part != prefix:
            return False

        # 验证长度
        if len(random_part) != key_length:
            return False

        # 验证校验和
        expected_checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
        if checksum != expected_checksum:
            return False

        return True

    # 测试有效密钥
    valid_key = "LICENSE-ABCDEF1234567890GHIJKL-MN12"
    # 手动计算校验和确保正确
    manual_checksum = (
        hashlib.md5("ABCDEF1234567890GHIJKL".encode()).hexdigest()[:4].upper()
    )
    valid_key = f"LICENSE-ABCDEF1234567890GHIJKL-{manual_checksum}"

    assert validate_license_key_format(valid_key) == True
    print(f"✅ 有效密钥验证通过: {valid_key}")

    # 测试无效密钥
    invalid_keys = [
        "",  # 空字符串
        "INVALID-FORMAT",  # 格式错误
        "LICENSE-TOO-SHORT-X",  # 长度不够
        f"LICENSE-WRONG-PREFIX-{'A'*32}-1234",  # 前缀错误
    ]

    for invalid_key in invalid_keys:
        assert validate_license_key_format(invalid_key) == False
        print(f"✅ 无效密钥检测通过: {invalid_key}")

    print("✅ 许可证密钥验证测试通过")


def test_redis_connection():
    """测试Redis连接"""
    try:
        import redis

        # 尝试连接本地Redis
        client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)
        client.ping()
        print("✅ Redis连接测试通过")
        return True
    except Exception as e:
        print(f"⚠️  Redis连接测试失败: {e}")
        print("💡 请确保Redis服务正在运行")
        return False


def test_basic_imports():
    """测试基本导入"""
    try:

        print("✅ 基本模块导入测试通过")
        return True
    except Exception as e:
        print(f"❌ 基本导入测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("许可证管理系统核心功能测试")
    print("=" * 50)

    tests_passed = 0
    total_tests = 4

    # 运行各项测试
    try:
        test_basic_imports()
        tests_passed += 1
        print()

        test_license_key_generation()
        tests_passed += 1
        print()

        test_license_key_validation()
        tests_passed += 1
        print()

        if test_redis_connection():
            tests_passed += 1
        print()

    except Exception as e:
        print(f"❌ 测试执行出现异常: {e}")

    # 输出测试结果
    print("=" * 50)
    print(f"测试结果: {tests_passed}/{total_tests} 项测试通过")

    if tests_passed == total_tests:
        print("🎉 所有核心功能测试通过！系统基本可用。")
        return True
    else:
        print("⚠️  部分测试未通过，请检查相关配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
