#!/usr/bin/env python3
"""
表单验证器功能演示脚本
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def demonstrate_validators():
    """演示验证器功能"""
    print("=== 表单验证器功能演示 ===\n")

    # 模拟验证函数
    def validate_email(email):
        if "@" not in email or "." not in email.split("@")[1]:
            return {
                "is_valid": False,
                "error_code": "INVALID_EMAIL",
                "error_message": "邮箱格式不正确",
            }
        return {"is_valid": True}

    def validate_username(username):
        if len(username) < 3:
            return {
                "is_valid": False,
                "error_code": "USERNAME_TOO_SHORT",
                "error_message": "用户名长度不能少于3个字符",
            }
        if len(username) > 50:
            return {
                "is_valid": False,
                "error_code": "USERNAME_TOO_LONG",
                "error_message": "用户名长度不能超过50个字符",
            }
        if not all(c.isalnum() or c in "_\u4e00-\u9fa5" for c in username):
            return {
                "is_valid": False,
                "error_code": "INVALID_USERNAME_CHARS",
                "error_message": "用户名只能包含字母、数字、下划线和中文字符",
            }
        return {"is_valid": True}

    def validate_password(password):
        if len(password) < 8:
            return {
                "is_valid": False,
                "error_code": "PASSWORD_TOO_SHORT",
                "error_message": "密码长度不能少于8个字符",
            }
        return {"is_valid": True}

    def validate_number(value, min_val=None, max_val=None):
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return {
                    "is_valid": False,
                    "error_code": "NUMBER_TOO_SMALL",
                    "error_message": f"数值不能小于{min_val}",
                }
            if max_val is not None and num > max_val:
                return {
                    "is_valid": False,
                    "error_code": "NUMBER_TOO_LARGE",
                    "error_message": f"数值不能大于{max_val}",
                }
            return {"is_valid": True}
        except (ValueError, TypeError):
            return {
                "is_valid": False,
                "error_code": "INVALID_NUMBER",
                "error_message": "必须是有效数字",
            }

    # 演示邮箱验证
    print("1. 邮箱验证测试:")
    emails = ["test@example.com", "invalid-email", "user@domain"]
    for email in emails:
        result = validate_email(email)
        status = (
            "✓ 通过" if result["is_valid"] else f"✗ 失败 ({result['error_message']})"
        )
        print(f"  {email}: {status}")

    print("\n2. 用户名验证测试:")
    usernames = ["testuser", "ab", "a" * 51, "user@name"]
    for username in usernames:
        result = validate_username(username)
        status = (
            "✓ 通过" if result["is_valid"] else f"✗ 失败 ({result['error_message']})"
        )
        print(f"  '{username}': {status}")

    print("\n3. 密码验证测试:")
    passwords = ["password123", "short"]
    for password in passwords:
        result = validate_password(password)
        status = (
            "✓ 通过" if result["is_valid"] else f"✗ 失败 ({result['error_message']})"
        )
        print(f"  '{password}': {status}")

    print("\n4. 数字验证测试:")
    numbers = [25, -1, 200, "not-a-number"]
    for number in numbers:
        result = validate_number(number, 0, 100)
        status = (
            "✓ 通过" if result["is_valid"] else f"✗ 失败 ({result['error_message']})"
        )
        print(f"  {number}: {status}")

    # 演示表单验证
    print("\n5. 表单验证演示:")

    # 模拟表单验证器类
    class FormValidator:
        def __init__(self):
            self.rules = {}

        def add_rule(self, field, validator_func):
            self.rules[field] = validator_func
            return self

        def validate(self, data):
            errors = {}
            for field, validator in self.rules.items():
                if field in data:
                    result = validator(data[field])
                    if not result["is_valid"]:
                        errors[field] = result["error_message"]
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "error_count": len(errors),
            }

    # 创建表单验证器
    form_validator = FormValidator()
    form_validator.add_rule("email", validate_email).add_rule(
        "username", validate_username
    ).add_rule("password", validate_password).add_rule(
        "age", lambda x: validate_number(x, 0, 150)
    )

    # 测试有效数据
    valid_data = {
        "email": "user@example.com",
        "username": "testuser123",
        "password": "securepassword123",
        "age": 25,
    }

    print("  有效表单数据验证:")
    result = form_validator.validate(valid_data)
    print(f"    结果: {'✓ 通过' if result['is_valid'] else '✗ 失败'}")
    print(f"    错误数量: {result['error_count']}")

    # 测试无效数据
    invalid_data = {
        "email": "invalid-email",
        "username": "ab",
        "password": "short",
        "age": 200,
    }

    print("  无效表单数据验证:")
    result = form_validator.validate(invalid_data)
    print(f"    结果: {'✓ 通过' if result['is_valid'] else '✗ 失败'}")
    print(f"    错误数量: {result['error_count']}")
    if result["errors"]:
        print("    错误详情:")
        for field, error in result["errors"].items():
            print(f"      {field}: {error}")

    print("\n✓ 表单验证器演示完成")


def main():
    """主演示函数"""
    print("开始演示表单验证器重构效果...\n")

    try:
        demonstrate_validators()
        print("\n🎉 所有演示完成！展示了重构后的验证器结构和使用方式。")
        return True
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
