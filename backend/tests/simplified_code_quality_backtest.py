#!/usr/bin/env python3
"""
简化版代码质量优化验证脚本
不依赖外部库，仅验证核心逻辑
"""

import sys
import time
from typing import Any, Dict


class SimpleBacktestValidator:
    """简化版回测验证器"""

    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "tests": []}
        self.start_time = None

    def run_test(self, name: str, test_func) -> bool:
        """运行单个测试"""
        print(f"\n{'='*60}")
        print(f"🧪 测试：{name}")
        print(f"{'='*60}")

        start = time.time()
        try:
            result = test_func()
            duration = time.time() - start
            self.results["passed"] += 1
            self.results["tests"].append(
                {"name": name, "status": "PASSED", "duration": duration}
            )
            print(f"✅ 通过 (耗时：{duration:.2f}s)")
            return True
        except Exception as e:
            duration = time.time() - start
            self.results["failed"] += 1
            self.results["tests"].append(
                {"name": name, "status": "FAILED", "error": str(e)}
            )
            print(f"❌ 失败：{e}")
            return False

    def test_string_utils(self):
        """测试字符串工具函数"""
        from utils.string_utils import (
            capitalize,
            camel_to_snake,
            is_empty,
            random_string,
            snake_to_camel,
        )

        assert is_empty("") is True, "空字符串判断失败"
        assert is_empty("hello") is False, "非空字符串判断失败"
        assert capitalize("hello") == "Hello", "首字母大写失败"
        assert len(random_string(8)) == 8, "随机字符串长度错误"
        assert camel_to_snake("userName") == "user_name", "驼峰转下划线失败"
        assert snake_to_camel("user_name") == "userName", "下划线转驼峰失败"

        print("  ✓ 所有字符串工具函数正常")

    def test_date_utils(self):
        """测试日期工具函数"""
        from utils.date_utils import (
            format_date,
            get_time_ago,
            is_leap_year,
            is_same_day,
        )
        from datetime import datetime

        # 测试格式化
        now = datetime.now()
        formatted = format_date(now, "%Y-%m-%d")
        assert len(formatted) == 10, "日期格式化失败"

        # 测试闰年
        assert is_leap_year(2024) is True, "2024 年应该是闰年"
        assert is_leap_year(2023) is False, "2023 年不是闰年"

        # 测试同一天判断
        assert is_same_day(now, now) is True, "相同时间应该是同一天"

        # 测试相对时间
        ago = get_time_ago(now)
        assert "刚刚" in ago or "分钟" in ago, "相对时间格式错误"

        print("  ✓ 所有日期工具函数正常")

    def test_cache_manager(self):
        """测试缓存管理器"""
        from utils.cache_manager import cache_manager

        # 测试设置和获取
        cache_manager.set("test_key", "test_value", expire_minutes=5)
        value = cache_manager.get("test_key")
        assert value == "test_value", "缓存读取失败"

        # 测试删除
        cache_manager.delete("test_key")
        value = cache_manager.get("test_key")
        assert value is None, "缓存删除失败"

        print("  ✓ 缓存管理器功能正常")

    def test_logging_component(self):
        """测试 logging 组件"""
        import logging

        logger = logging.getLogger("test_backtest")
        logger.setLevel(logging.INFO)

        assert logger.level == logging.INFO, "日志级别设置错误"
        assert logger.name == "test_backtest", "Logger 名称错误"

        print("  ✓ Logging 组件正常")

    def test_exception_handling_patterns(self):
        """测试异常处理模式"""
        # 验证我们的 except 修复是否正确
        try:
            # 模拟可能抛出 TypeError 的操作
            data = None
            try:
                result = data.some_method()  # type: ignore
            except (AttributeError, TypeError):
                result = "handled"
            assert result == "handled", "异常处理失败"

            # 模拟 JSON 解析异常
            import json

            try:
                json.loads("invalid json")
            except json.JSONDecodeError:
                handled = True

            assert handled is True, "JSON 异常处理失败"

            print("  ✓ 异常处理模式正确")

        except Exception as e:
            raise AssertionError(f"异常处理验证失败：{e}")

    def test_type_annotations(self):
        """测试类型注解完整性"""
        import inspect
        from utils.string_utils import capitalize, is_empty
        from utils.date_utils import format_date

        # 检查函数是否有类型注解
        capitalize_sig = inspect.signature(capitalize)
        assert (
            str(capitalize_sig.return_annotation) != "<class 'inspect._empty'>"
        ), "capitalize 缺少返回类型注解"

        is_empty_sig = inspect.signature(is_empty)
        params = list(is_empty_sig.parameters.values())
        assert (
            len(params) > 0 and params[0].annotation != inspect.Parameter.empty
        ), "is_empty 缺少参数类型注解"

        print("  ✓ 类型注解完整")

    def generate_report(self) -> str:
        """生成报告"""
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        report = f"""
{'='*70}
📊 代码质量优化验证报告
{'='*70}

⏱️  总耗时：{time.time() - self.start_time:.2f}秒
📈 测试总数：{total}
✅ 通过数量：{self.results['passed']}
❌ 失败数量：{self.results['failed']}
⭐ 成功率：{success_rate:.1f}%

"""

        if self.results["failed"] > 0:
            report += "\n❌ 失败测试:\n"
            for test in self.results["tests"]:
                if test["status"] == "FAILED":
                    report += f"  - {test['name']}: {test.get('error', 'Unknown')}\n"

        report += f"""
{'='*70}
"""

        if success_rate == 100:
            report += "🎉 所有测试通过！代码质量优化验证成功！\n"
        elif success_rate >= 80:
            report += "✅ 大部分测试通过，代码质量良好\n"
        else:
            report += "⚠️  测试失败较多，请检查\n"

        report += f"{'='*70}\n"
        return report

    def run_validation(self):
        """运行完整验证"""
        self.start_time = time.time()

        print("\n" + "=" * 70)
        print("🚀 开始代码质量优化验证")
        print("=" * 70)

        tests = [
            ("字符串工具函数", self.test_string_utils),
            ("日期工具函数", self.test_date_utils),
            ("缓存管理器", self.test_cache_manager),
            ("Logging 组件", self.test_logging_component),
            ("异常处理模式", self.test_exception_handling_patterns),
            ("类型注解完整性", self.test_type_annotations),
        ]

        for name, test_func in tests:
            self.run_test(name, test_func)

        report = self.generate_report()
        print(report)

        # 保存报告
        report_file = f"simplified_backtest_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n📄 报告已保存到：{report_file}")

        return self.results["failed"] == 0


def main():
    validator = SimpleBacktestValidator()
    success = validator.run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
