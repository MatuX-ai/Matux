"""
字符串处理工具函数集合
"""

import random
import re
import string
from typing import List, Optional


def is_empty(s: Optional[str]) -> bool:
    """
    判断字符串是否为空或仅包含空白字符

    Args:
        s: 待检查的字符串

    Returns:
        bool: 是否为空
    """
    return s is None or not isinstance(s, str) or s.strip() == ""


def is_not_empty(s: Optional[str]) -> bool:
    """
    判断字符串是否非空

    Args:
        s: 待检查的字符串

    Returns:
        bool: 是否非空
    """
    return not is_empty(s)


def truncate(s: str, max_length: int, suffix: str = "...") -> str:
    """
    截取字符串并添加省略号

    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 后缀，默认为'...'

    Returns:
        str: 处理后的字符串
    """
    if not s or len(s) <= max_length:
        return s
    return s[:max_length] + suffix


def capitalize(s: str) -> str:
    """
    首字母大写

    Args:
        s: 输入字符串

    Returns:
        str: 首字母大写的字符串
    """
    if not s:
        return s
    return s[0].upper() + s[1:] if len(s) > 1 else s.upper()


def camel_to_snake(s: str) -> str:
    """
    驼峰命名转换为下划线命名

    Args:
        s: 驼峰命名字符串

    Returns:
        str: 下划线命名字符串
    """
    return re.sub("([A-Z])", r"_\1", s).lower()


def snake_to_camel(s: str) -> str:
    """
    下划线命名转换为驼峰命名

    Args:
        s: 下划线命名字符串

    Returns:
        str: 驼峰命名字符串
    """
    return re.sub("_([a-z])", lambda m: m.group(1).upper(), s)


def random_string(length: int = 8) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        str: 随机字符串
    """
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def trim_chars(s: str, chars: str) -> str:
    """
    移除字符串两端的指定字符

    Args:
        s: 原始字符串
        chars: 要移除的字符

    Returns:
        str: 处理后的字符串
    """
    if not s or not chars:
        return s
    return s.strip(chars)


def template(template_str: str, data: dict) -> str:
    """
    字符串模板替换

    Args:
        template_str: 模板字符串，如 "Hello {name}"
        data: 替换数据对象

    Returns:
        str: 替换后的字符串
    """
    if not template_str or not isinstance(data, dict):
        return template_str

    result = template_str
    for key, value in data.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            result = result.replace(
                placeholder, str(value) if value is not None else ""
            )

    return result


def contains_sensitive_words(s: str, sensitive_words: List[str]) -> bool:
    """
    检查字符串是否包含敏感词

    Args:
        s: 待检查字符串
        sensitive_words: 敏感词数组

    Returns:
        bool: 是否包含敏感词
    """
    if not s or not sensitive_words:
        return False

    lower_s = s.lower()
    return any(word.lower() in lower_s for word in sensitive_words)


def filter_sensitive_words(
    s: str, sensitive_words: List[str], replacement: str = "*"
) -> str:
    """
    过滤敏感词

    Args:
        s: 待过滤字符串
        sensitive_words: 敏感词数组
        replacement: 替换字符，默认为'*'

    Returns:
        str: 过滤后的字符串
    """
    if not s or not sensitive_words:
        return s

    result = s
    for word in sensitive_words:
        # 转义特殊字符
        escaped_word = re.escape(word)
        pattern = re.compile(escaped_word, re.IGNORECASE)
        result = pattern.sub(replacement * len(word), result)

    return result


# 便捷函数别名
isempty = is_empty
isnotempty = is_not_empty
randomstring = random_string
trimchars = trim_chars
contains_sensitive = contains_sensitive_words
filter_sensitive = filter_sensitive_words
