"""
验证器工厂类
"""

from typing import Any, Dict, List, Optional, Tuple

from .base_validator import (
    BaseValidator,
    EmailValidator,
    NumberValidator,
    PasswordValidator,
    StringValidator,
    UsernameValidator,
    ValidationResult,
)


class ValidatorFactory:
    """验证器工厂"""

    @staticmethod
    def string(field_name: str = "字符串") -> StringValidator:
        """创建字符串验证器"""
        return StringValidator(field_name)

    @staticmethod
    def number(field_name: str = "数字") -> NumberValidator:
        """创建数字验证器"""
        return NumberValidator(field_name)

    @staticmethod
    def email(field_name: str = "邮箱") -> EmailValidator:
        """创建邮箱验证器"""
        return EmailValidator(field_name)

    @staticmethod
    def username(field_name: str = "用户名") -> UsernameValidator:
        """创建用户名验证器"""
        return UsernameValidator(field_name)

    @staticmethod
    def password(field_name: str = "密码") -> PasswordValidator:
        """创建密码验证器"""
        return PasswordValidator(field_name)

    @staticmethod
    def custom(validate_fn, field_name: str = "字段") -> BaseValidator:
        """创建自定义验证器"""

        class CustomValidator(BaseValidator):
            def validate(self, value: Any) -> ValidationResult:
                return validate_fn(value)

        validator = CustomValidator(field_name)
        return validator

    @staticmethod
    def validate_object(
        data: Dict[str, Any], rules: Dict[str, BaseValidator]
    ) -> Tuple[bool, Dict[str, str]]:
        """批量验证对象"""
        errors: Dict[str, str] = {}

        for field, validator in rules.items():
            if field in data:
                result = validator.validate(data[field])
                if not result.is_valid and result.error_message:
                    errors[field] = result.error_message

        return len(errors) == 0, errors


class ValidationRuleBuilder:
    """验证规则构建器"""

    def __init__(self):
        self.rules: Dict[str, BaseValidator] = {}

    def string(
        self, field: str, field_name: Optional[str] = None
    ) -> "ValidationRuleBuilder":
        """添加字符串验证规则"""
        self.rules[field] = ValidatorFactory.string(field_name or field)
        return self

    def number(
        self, field: str, field_name: Optional[str] = None
    ) -> "ValidationRuleBuilder":
        """添加数字验证规则"""
        self.rules[field] = ValidatorFactory.number(field_name or field)
        return self

    def email(
        self, field: str, field_name: Optional[str] = None
    ) -> "ValidationRuleBuilder":
        """添加邮箱验证规则"""
        self.rules[field] = ValidatorFactory.email(field_name or field)
        return self

    def username(
        self, field: str, field_name: Optional[str] = None
    ) -> "ValidationRuleBuilder":
        """添加用户名验证规则"""
        self.rules[field] = ValidatorFactory.username(field_name or field)
        return self

    def password(
        self, field: str, field_name: Optional[str] = None
    ) -> "ValidationRuleBuilder":
        """添加密码验证规则"""
        self.rules[field] = ValidatorFactory.password(field_name or field)
        return self

    def custom(self, field: str, validator: BaseValidator) -> "ValidationRuleBuilder":
        """添加自定义验证规则"""
        self.rules[field] = validator
        return self

    def build(self) -> Dict[str, BaseValidator]:
        """获取构建的规则"""
        return self.rules.copy()

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """直接验证对象"""
        return ValidatorFactory.validate_object(data, self.rules)


class FormValidator:
    """表单验证器"""

    def __init__(self):
        self.rules: Dict[str, BaseValidator] = {}

    def add_rule(self, field: str, validator: BaseValidator) -> "FormValidator":
        """添加验证规则"""
        self.rules[field] = validator
        return self

    def remove_rule(self, field: str) -> "FormValidator":
        """移除验证规则"""
        self.rules.pop(field, None)
        return self

    def clear_rules(self) -> "FormValidator":
        """清除所有规则"""
        self.rules.clear()
        return self

    def validate_field(self, field: str, value: Any) -> ValidationResult:
        """验证单个字段"""
        validator = self.rules.get(field)
        if not validator:
            return ValidationResult(True)
        return validator.validate(value)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证整个表单"""
        is_valid, errors = ValidatorFactory.validate_object(data, self.rules)
        return {"is_valid": is_valid, "errors": errors, "error_count": len(errors)}

    def get_rules(self) -> Dict[str, BaseValidator]:
        """获取验证规则"""
        return self.rules.copy()

    def has_rule(self, field: str) -> bool:
        """检查字段是否有验证规则"""
        return field in self.rules

    def get_validator(self, field: str) -> Optional[BaseValidator]:
        """获取字段验证器"""
        return self.rules.get(field)


# 常用验证规则常量
class CommonValidators:
    """常用验证规则常量"""

    @staticmethod
    def required_string(field_name: str) -> StringValidator:
        """必填字符串"""
        return ValidatorFactory.string(field_name).required()

    @staticmethod
    def required_email(field_name: str) -> EmailValidator:
        """必填邮箱"""
        return ValidatorFactory.email(field_name).required()

    @staticmethod
    def required_username(field_name: str) -> UsernameValidator:
        """必填用户名"""
        return ValidatorFactory.username(field_name).required()

    @staticmethod
    def required_password(field_name: str) -> PasswordValidator:
        """必填密码"""
        return ValidatorFactory.password(field_name).required()

    @staticmethod
    def short_string(field_name: str) -> StringValidator:
        """短字符串（最长100字符）"""
        return ValidatorFactory.string(field_name).max(100)

    @staticmethod
    def medium_string(field_name: str) -> StringValidator:
        """中等字符串（最长255字符）"""
        return ValidatorFactory.string(field_name).max(255)

    @staticmethod
    def long_string(field_name: str) -> StringValidator:
        """长字符串（最长1000字符）"""
        return ValidatorFactory.string(field_name).max(1000)

    @staticmethod
    def positive_number(field_name: str) -> NumberValidator:
        """正数"""
        return ValidatorFactory.number(field_name).min(0)

    @staticmethod
    def integer(field_name: str) -> NumberValidator:
        """整数"""
        return ValidatorFactory.number(field_name).integer()

    @staticmethod
    def percentage(field_name: str) -> NumberValidator:
        """百分比（0-100）"""
        return ValidatorFactory.number(field_name).min(0).max(100)

    @staticmethod
    def phone(field_name: str) -> StringValidator:
        """手机号"""
        return ValidatorFactory.string(field_name).pattern(
            r"^1[3-9]\d{9}$", "INVALID_PHONE"
        )

    @staticmethod
    def id_card(field_name: str) -> StringValidator:
        """身份证号"""
        return ValidatorFactory.string(field_name).pattern(
            r"(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)", "INVALID_ID_CARD"
        )


# 便捷函数
def validate_form(
    data: Dict[str, Any], rules: Dict[str, BaseValidator]
) -> Dict[str, Any]:
    """便捷的表单验证函数"""
    validator = FormValidator()
    for field, rule in rules.items():
        validator.add_rule(field, rule)
    return validator.validate(data)


def build_validation_rules() -> ValidationRuleBuilder:
    """创建验证规则构建器"""
    return ValidationRuleBuilder()
