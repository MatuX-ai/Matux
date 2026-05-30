"""
表单验证器测试
"""

import unittest

from backend.utils.validation.base_validator import (
    validate_email,
    validate_password,
    validate_username,
)
from backend.utils.validation.validation_factory import (
    CommonValidators,
    FormValidator,
    ValidatorFactory,
)


class TestValidators(unittest.TestCase):

    def test_email_validation(self):
        """测试邮箱验证"""
        # 有效邮箱
        result = validate_email("test@example.com")
        self.assertTrue(result.is_valid)

        # 无效邮箱
        result = validate_email("invalid-email")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "INVALID_EMAIL")

    def test_username_validation(self):
        """测试用户名验证"""
        # 有效用户名
        result = validate_username("testuser123")
        self.assertTrue(result.is_valid)

        result = validate_username("用户_name")
        self.assertTrue(result.is_valid)

        # 无效用户名
        result = validate_username("ab")  # 太短
        self.assertFalse(result.is_valid)

        result = validate_username("a" * 51)  # 太长
        self.assertFalse(result.is_valid)

        result = validate_username("user@name")  # 包含非法字符
        self.assertFalse(result.is_valid)

    def test_password_validation(self):
        """测试密码验证"""
        # 有效密码
        result = validate_password("password123")
        self.assertTrue(result.is_valid)

        # 太短的密码
        result = validate_password("short")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_code, "PASSWORD_TOO_SHORT")

    def test_validator_factory(self):
        """测试验证器工厂"""
        # 创建邮箱验证器
        email_validator = ValidatorFactory.email("邮箱")
        result = email_validator.validate("test@example.com")
        self.assertTrue(result.is_valid)

        # 创建用户名验证器
        username_validator = ValidatorFactory.username("用户名")
        result = username_validator.validate("valid_username")
        self.assertTrue(result.is_valid)

        # 创建密码验证器
        password_validator = ValidatorFactory.password("密码")
        result = password_validator.validate("strong_password123")
        self.assertTrue(result.is_valid)

    def test_form_validator(self):
        """测试表单验证器"""
        validator = FormValidator()
        validator.add_rule("email", ValidatorFactory.email("邮箱"))
        validator.add_rule("username", ValidatorFactory.username("用户名"))
        validator.add_rule("age", ValidatorFactory.number("年龄").min(0).max(150))

        # 有效数据
        valid_data = {"email": "test@example.com", "username": "testuser", "age": 25}

        result = validator.validate(valid_data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["error_count"], 0)

        # 无效数据
        invalid_data = {
            "email": "invalid-email",
            "username": "ab",  # 太短
            "age": 200,  # 超出范围
        }

        result = validator.validate(invalid_data)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["error_count"], 3)
        self.assertIn("email", result["errors"])
        self.assertIn("username", result["errors"])
        self.assertIn("age", result["errors"])

    def test_common_validators(self):
        """测试常用验证器"""
        # 必填字符串
        validator = CommonValidators.required_string("姓名")
        result = validator.validate("")
        self.assertFalse(result.is_valid)

        result = validator.validate("张三")
        self.assertTrue(result.is_valid)

        # 手机号验证
        validator = CommonValidators.phone("手机")
        result = validator.validate("13812345678")
        self.assertTrue(result.is_valid)

        result = validator.validate("12345678901")
        self.assertFalse(result.is_valid)

        # 身份证验证
        validator = CommonValidators.id_card("身份证")
        result = validator.validate("110101199001011234")
        self.assertTrue(result.is_valid)

        result = validator.validate("invalid-id")
        self.assertFalse(result.is_valid)


if __name__ == "__main__":
    unittest.main()
