"""
通用表单验证器基类
"""

from abc import ABC, abstractmethod
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        is_valid: bool,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.error_message = error_message
        self.error_code = error_code

    def __bool__(self) -> bool:
        return self.is_valid


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        field_name: Optional[str] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.field_name = field_name


class BaseValidator(ABC):
    """验证器基类"""

    def __init__(self, field_name: str = ""):
        self.field_name = field_name

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """验证值"""
        pass

    def validate_or_throw(self, value: Any) -> Any:
        """验证值并抛出异常（如果无效）"""
        result = self.validate(value)
        if not result.is_valid:
            raise ValidationError(
                result.error_message or "验证失败", result.error_code, self.field_name
            )
        return value


class StringValidator(BaseValidator):
    """字符串验证器"""

    def __init__(self, field_name: str = "字符串"):
        super().__init__(field_name)
        self.min_length: Optional[int] = None
        self.max_length: Optional[int] = None
        self.pattern: Optional[re.Pattern] = None
        self.pattern_error_code: Optional[str] = None
        self.required: bool = False
        self.trim: bool = True

    def required(self) -> "StringValidator":
        """设置必填"""
        self.required = True
        return self

    def min(self, length: int) -> "StringValidator":
        """设置最小长度"""
        self.min_length = length
        return self

    def max(self, length: int) -> "StringValidator":
        """设置最大长度"""
        self.max_length = length
        return self

    def pattern(
        self, regex: str, error_code: Optional[str] = None
    ) -> "StringValidator":
        """设置正则表达式模式"""
        self.pattern = re.compile(regex)
        self.pattern_error_code = error_code
        return self

    def trim_spaces(self, trim: bool = True) -> "StringValidator":
        """设置是否去除首尾空格"""
        self.trim = trim
        return self

    def validate(self, value: Any) -> ValidationResult:
        # 处理空值
        if value is None:
            value = ""

        str_value = str(value)

        # 去除首尾空格
        if self.trim:
            str_value = str_value.strip()

        # 必填验证
        if self.required and len(str_value) == 0:
            return ValidationResult(False, f"{self.field_name}不能为空", "REQUIRED")

        # 空值且非必填，验证通过
        if not self.required and len(str_value) == 0:
            return ValidationResult(True)

        # 最小长度验证
        if self.min_length is not None and len(str_value) < self.min_length:
            return ValidationResult(
                False,
                f"{self.field_name}长度不能少于{self.min_length}个字符",
                "MIN_LENGTH",
            )

        # 最大长度验证
        if self.max_length is not None and len(str_value) > self.max_length:
            return ValidationResult(
                False,
                f"{self.field_name}长度不能超过{self.max_length}个字符",
                "MAX_LENGTH",
            )

        # 正则表达式验证
        if self.pattern and not self.pattern.match(str_value):
            return ValidationResult(
                False,
                f"{self.field_name}格式不正确",
                self.pattern_error_code or "PATTERN_MISMATCH",
            )

        return ValidationResult(True)


class NumberValidator(BaseValidator):
    """数字验证器"""

    def __init__(self, field_name: str = "数字"):
        super().__init__(field_name)
        self.min_value: Optional[float] = None
        self.max_value: Optional[float] = None
        self.integer_only: bool = False
        self.required: bool = False

    def required(self) -> "NumberValidator":
        """设置必填"""
        self.required = True
        return self

    def min(self, value: float) -> "NumberValidator":
        """设置最小值"""
        self.min_value = value
        return self

    def max(self, value: float) -> "NumberValidator":
        """设置最大值"""
        self.max_value = value
        return self

    def integer(self) -> "NumberValidator":
        """设置只能是整数"""
        self.integer_only = True
        return self

    def validate(self, value: Any) -> ValidationResult:
        # 处理空值
        if value is None:
            if self.required:
                return ValidationResult(False, f"{self.field_name}不能为空", "REQUIRED")
            return ValidationResult(True)

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult(
                False, f"{self.field_name}必须是有效数字", "INVALID_NUMBER"
            )

        # 整数验证
        if self.integer_only and not num_value.is_integer():
            return ValidationResult(
                False, f"{self.field_name}必须是整数", "NOT_INTEGER"
            )

        # 最小值验证
        if self.min_value is not None and num_value < self.min_value:
            return ValidationResult(
                False, f"{self.field_name}不能小于{self.min_value}", "MIN_VALUE"
            )

        # 最大值验证
        if self.max_value is not None and num_value > self.max_value:
            return ValidationResult(
                False, f"{self.field_name}不能大于{self.max_value}", "MAX_VALUE"
            )

        return ValidationResult(True)


class EmailValidator(StringValidator):
    """邮箱验证器"""

    def __init__(self, field_name: str = "邮箱"):
        super().__init__(field_name)
        self.email_pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
        self.pattern(self.email_pattern.pattern, "INVALID_EMAIL")

    def validate(self, value: Any) -> ValidationResult:
        # 先执行父类验证
        parent_result = super().validate(value)
        if not parent_result.is_valid:
            return parent_result

        # 空值且非必填，验证通过
        str_value = str(value).strip() if value is not None else ""
        if not self.required and len(str_value) == 0:
            return ValidationResult(True)

        # 邮箱格式验证
        if not self.email_pattern.match(str_value):
            return ValidationResult(
                False, f"{self.field_name}格式不正确", "INVALID_EMAIL"
            )

        return ValidationResult(True)


class UsernameValidator(StringValidator):
    """用户名验证器"""

    def __init__(self, field_name: str = "用户名"):
        super().__init__(field_name)
        self.min(3).max(50).pattern(r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$", "INVALID_USERNAME")

    def validate(self, value: Any) -> ValidationResult:
        parent_result = super().validate(value)
        if not parent_result.is_valid:
            return parent_result

        str_value = str(value).strip() if value is not None else ""
        if not self.required and len(str_value) == 0:
            return ValidationResult(True)

        # 额外的用户名规则验证
        if len(str_value) > 0 and not re.match(
            r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$", str_value
        ):
            return ValidationResult(
                False,
                f"{self.field_name}只能包含字母、数字、下划线和中文字符",
                "INVALID_USERNAME",
            )

        return ValidationResult(True)


class PasswordValidator(StringValidator):
    """密码验证器"""

    def __init__(self, field_name: str = "密码"):
        super().__init__(field_name)
        self.min_length = 8
        self.require_uppercase: bool = False
        self.require_lowercase: bool = False
        self.require_numbers: bool = False
        self.require_special_chars: bool = False
        self.min(self.min_length)

    def uppercase(self) -> "PasswordValidator":
        """要求包含大写字母"""
        self.require_uppercase = True
        return self

    def lowercase(self) -> "PasswordValidator":
        """要求包含小写字母"""
        self.require_lowercase = True
        return self

    def numbers(self) -> "PasswordValidator":
        """要求包含数字"""
        self.require_numbers = True
        return self

    def special_chars(self) -> "PasswordValidator":
        """要求包含特殊字符"""
        self.require_special_chars = True
        return self

    def validate(self, value: Any) -> ValidationResult:
        parent_result = super().validate(value)
        if not parent_result.is_valid:
            return parent_result

        str_value = str(value) if value is not None else ""
        if not self.required and len(str_value) == 0:
            return ValidationResult(True)

        errors: List[str] = []

        # 大写字母验证
        if self.require_uppercase and not re.search(r"[A-Z]", str_value):
            errors.append("必须包含大写字母")

        # 小写字母验证
        if self.require_lowercase and not re.search(r"[a-z]", str_value):
            errors.append("必须包含小写字母")

        # 数字验证
        if self.require_numbers and not re.search(r"\d", str_value):
            errors.append("必须包含数字")

        # 特殊字符验证
        if self.require_special_chars and not re.search(
            r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', str_value
        ):
            errors.append("必须包含特殊字符")

        if errors:
            return ValidationResult(
                False, f'{self.field_name}{"".join(errors)}', "WEAK_PASSWORD"
            )

        return ValidationResult(True)


# 便捷函数
def validate_email(email: str, field_name: str = "邮箱") -> ValidationResult:
    """验证邮箱"""
    return EmailValidator(field_name).validate(email)


def validate_username(username: str, field_name: str = "用户名") -> ValidationResult:
    """验证用户名"""
    return UsernameValidator(field_name).validate(username)


def validate_password(password: str, field_name: str = "密码") -> ValidationResult:
    """验证密码"""
    return PasswordValidator(field_name).validate(password)
