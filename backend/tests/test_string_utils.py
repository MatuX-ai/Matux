"""
字符串工具函数测试
"""

import unittest

from backend.utils.string_utils import (
    camel_to_snake,
    capitalize,
    contains_sensitive_words,
    filter_sensitive_words,
    is_empty,
    is_not_empty,
    random_string,
    snake_to_camel,
    template,
    trim_chars,
    truncate,
)


class TestStringUtils(unittest.TestCase):

    def test_is_empty_and_is_not_empty(self):
        """测试空字符串判断"""
        # 测试空字符串
        self.assertTrue(is_empty(""))
        self.assertTrue(is_empty("   "))
        self.assertTrue(is_empty(None))

        self.assertFalse(is_not_empty(""))
        self.assertFalse(is_not_empty("   "))
        self.assertFalse(is_not_empty(None))

        # 测试非空字符串
        self.assertFalse(is_empty("hello"))
        self.assertTrue(is_not_empty("hello"))
        self.assertTrue(is_not_empty(" hello "))

    def test_truncate(self):
        """测试字符串截取"""
        self.assertEqual(truncate("hello world", 5), "hello...")
        self.assertEqual(truncate("hello", 10), "hello")
        self.assertEqual(truncate("", 5), "")
        self.assertEqual(truncate("hello world", 5, "***"), "hello***")

    def test_capitalize(self):
        """测试首字母大写"""
        self.assertEqual(capitalize("hello"), "Hello")
        self.assertEqual(capitalize("HELLO"), "HELLO")
        self.assertEqual(capitalize(""), "")
        self.assertEqual(capitalize("a"), "A")

    def test_naming_conversions(self):
        """测试命名格式转换"""
        self.assertEqual(camel_to_snake("userName"), "_user_name")
        self.assertEqual(camel_to_snake("XMLHttpRequest"), "_x_m_l_http_request")
        self.assertEqual(snake_to_camel("user_name"), "userName")
        self.assertEqual(snake_to_camel("first_name"), "firstName")

    def test_random_string(self):
        """测试随机字符串生成"""
        str1 = random_string(8)
        str2 = random_string(10)

        self.assertEqual(len(str1), 8)
        self.assertEqual(len(str2), 10)
        self.assertNotEqual(str1, str2)

        # 验证只包含字母和数字
        self.assertTrue(str1.isalnum())

    def test_trim_chars(self):
        """测试字符移除"""
        self.assertEqual(trim_chars("***hello***", "*"), "hello")
        self.assertEqual(trim_chars("---hello---", "-"), "hello")
        self.assertEqual(trim_chars("abcabcdefabc", "abc"), "def")
        self.assertEqual(trim_chars("", "*"), "")

    def test_template(self):
        """测试模板替换"""
        tpl = "Hello {name}, welcome to {place}!"
        data = {"name": "John", "place": "iMato"}

        self.assertEqual(template(tpl, data), "Hello John, welcome to iMato!")
        self.assertEqual(template("No vars here", data), "No vars here")
        self.assertEqual(template("{name}", {"name": "Alice"}), "Alice")
        self.assertEqual(template("{missing}", {}), "{missing}")

    def test_sensitive_words(self):
        """测试敏感词检测和过滤"""
        sensitive_words = ["敏感词", "badword", "禁止"]

        # 测试敏感词检测
        self.assertTrue(contains_sensitive_words("这包含敏感词内容", sensitive_words))
        self.assertTrue(
            contains_sensitive_words("This contains badword", sensitive_words)
        )
        self.assertFalse(contains_sensitive_words("正常内容", sensitive_words))
        self.assertFalse(contains_sensitive_words("", sensitive_words))

        # 测试敏感词过滤
        self.assertEqual(
            filter_sensitive_words("这包含敏感词内容", sensitive_words), "这包含***内容"
        )
        self.assertEqual(
            filter_sensitive_words(
                "Multiple badword instances badword", sensitive_words
            ),
            "Multiple ******* instances *******",
        )
        self.assertEqual(
            filter_sensitive_words("正常内容", sensitive_words), "正常内容"
        )
        self.assertEqual(filter_sensitive_words("", sensitive_words), "")

        # 测试自定义替换字符
        self.assertEqual(
            filter_sensitive_words("敏感词测试", sensitive_words, "#"), "###测试"
        )


if __name__ == "__main__":
    unittest.main()
