#!/usr/bin/env python3
"""
HTTP客户端功能演示脚本
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def demonstrate_http_client_concept():
    """演示HTTP客户端概念（Python模拟）"""
    print("=== HTTP客户端概念演示 ===\n")

    # 模拟统一的HTTP客户端接口概念
    class MockHttpClient:
        def __init__(self, base_url=""):
            self.base_url = base_url

        def get(self, url, **kwargs):
            print(f"GET {self.base_url}{url}")
            print(f"Headers: {kwargs.get('headers', {})}")
            return {"status": 200, "data": {"message": "Success"}}

        def post(self, url, data=None, **kwargs):
            print(f"POST {self.base_url}{url}")
            print(f"Data: {data}")
            print(f"Headers: {kwargs.get('headers', {})}")
            return {"status": 201, "data": {"id": 1, "created": True}}

        def put(self, url, data=None, **kwargs):
            print(f"PUT {self.base_url}{url}")
            print(f"Data: {data}")
            return {"status": 200, "data": {"updated": True}}

        def delete(self, url, **kwargs):
            print(f"DELETE {self.base_url}{url}")
            return {"status": 204, "data": None}

    # 演示使用
    print("1. 创建HTTP客户端实例:")
    client = MockHttpClient("https://api.imatu.com")

    print("\n2. 执行GET请求:")
    response = client.get("/users", headers={"Authorization": "Bearer token123"})
    print(f"响应: {response}")

    print("\n3. 执行POST请求:")
    user_data = {"name": "张三", "email": "zhangsan@example.com"}
    response = client.post("/users", data=user_data)
    print(f"响应: {response}")

    print("\n4. 执行PUT请求:")
    update_data = {"name": "李四"}
    response = client.put("/users/1", data=update_data)
    print(f"响应: {response}")

    print("\n5. 执行DELETE请求:")
    response = client.delete("/users/1")
    print(f"响应: {response}")

    print("\n✓ HTTP客户端概念演示完成")


def demonstrate_validation_refactor():
    """演示验证器重构概念"""
    print("\n=== 表单验证器重构演示 ===\n")

    # 模拟统一的验证器
    class EmailValidator:
        @staticmethod
        def validate(email):
            if not email or "@" not in email:
                return False, "邮箱格式不正确"
            if len(email) > 100:
                return False, "邮箱长度不能超过100个字符"
            return True, ""

    class UsernameValidator:
        @staticmethod
        def validate(username):
            if not username or len(username.strip()) < 3:
                return False, "用户名长度不能少于3个字符"
            if len(username) > 50:
                return False, "用户名长度不能超过50个字符"
            return True, ""

    # 统一验证器工厂
    class ValidatorFactory:
        @staticmethod
        def create_validator(validator_type):
            validators = {"email": EmailValidator(), "username": UsernameValidator()}
            return validators.get(validator_type)

        @staticmethod
        def validate_all(data, rules):
            errors = []
            for field, validator_type in rules.items():
                if field in data:
                    validator = ValidatorFactory.create_validator(validator_type)
                    if validator:
                        is_valid, error_msg = validator.validate(data[field])
                        if not is_valid:
                            errors.append(f"{field}: {error_msg}")
            return len(errors) == 0, errors

    # 演示使用
    print("1. 单独验证器使用:")
    email_validator = EmailValidator()
    is_valid, msg = email_validator.validate("test@example.com")
    print(f"邮箱验证: {is_valid}, {msg}")

    username_validator = UsernameValidator()
    is_valid, msg = username_validator.validate("abc")
    print(f"用户名验证: {is_valid}, {msg}")

    print("\n2. 统一验证器工厂使用:")
    user_data = {"email": "test@example.com", "username": "testuser123"}

    validation_rules = {"email": "email", "username": "username"}

    is_valid, errors = ValidatorFactory.validate_all(user_data, validation_rules)
    print(f"批量验证结果: {is_valid}")
    if errors:
        print("错误信息:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("  ✓ 所有验证通过")

    print("\n✓ 验证器重构演示完成")


def main():
    """主演示函数"""
    print("开始演示代码重构效果...\n")

    try:
        demonstrate_http_client_concept()
        demonstrate_validation_refactor()
        print("\n🎉 所有演示完成！展示了重构后的代码结构和使用方式。")
        return True
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
