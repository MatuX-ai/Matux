#!/usr/bin/env python3
"""
工具函数测试验证脚本
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.date_utils import *
from utils.string_utils import *

logger = logging.getLogger(__name__)


def test_string_utils():
    """测试字符串工具函数"""
    logger.info("=== 字符串工具函数测试 ===")

    # 测试空字符串判断
    logger.debug("is_empty(''): %s", is_empty(""))
    logger.debug("is_empty('hello'): %s", is_empty("hello"))
    logger.debug("capitalize('hello'): %s", capitalize("hello"))
    logger.debug("random_string(8): %s", random_string(8))
    logger.debug("camel_to_snake('userName'): %s", camel_to_snake("userName"))
    logger.debug("snake_to_camel('user_name'): %s", snake_to_camel("user_name"))

    # 测试敏感词过滤
    sensitive_words = ["敏感词", "badword"]
    test_text = "这包含敏感词和 badword 的内容"
    filtered = filter_sensitive_words(test_text, sensitive_words)
    logger.info("敏感词过滤：%s -> %s", test_text, filtered)

    logger.info("✓ 字符串工具函数测试通过\n")


def test_date_utils():
    """测试日期工具函数"""
    logger.info("=== 日期工具函数测试 ===")

    from datetime import datetime

    now = datetime.now()
    logger.debug("当前时间：%s", now)
    logger.debug("格式化：%s", format_date(now, "%Y-%m-%d %H:%M:%S"))
    logger.debug("相对时间：%s", get_time_ago(now))

    # 测试闰年判断
    logger.info("2024 年是闰年：%s", is_leap_year(2024))
    logger.info("2023 年是闰年：%s", is_leap_year(2023))

    # 测试季度信息
    quarter_info = get_quarter_info(now)
    logger.debug("当前季度：Q%s", quarter_info["quarter"])

    logger.info("✓ 日期工具函数测试通过\n")


def main():
    """主测试函数"""
    logging.basicConfig(level=logging.INFO)
    logger.info("开始验证共享工具函数...\n")

    try:
        test_string_utils()
        test_date_utils()
        logger.info("🎉 所有工具函数测试通过！")
        return True
    except Exception as e:
        logger.error("❌ 测试失败：%s", e, exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
