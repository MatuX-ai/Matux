"""
单元测试质量验证工具

功能:
1. 检测脆弱测试 (过度 Mock)
2. 识别测试实现而非功能
3. 统计测试覆盖率分布
4. 提供测试改进建议
5. 生成质量评估报告

使用方法:
    python scripts/validate_test_quality.py
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class TestQuality(Enum):
    """测试质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class TestFileAnalysis:
    """测试文件分析结果"""
    file_path: str
    test_count: int
    mock_count: int
    assertion_count: int
    has_setup: bool
    has_teardown: bool
    avg_test_length: float
    quality_score: float
    quality_level: TestQuality
    issues: List[str]


class TestQualityValidator:
    """测试质量验证器"""

    def __init__(self, test_dirs: List[str]):
        self.test_dirs = [Path(d) for d in test_dirs]
        self.results: List[TestFileAnalysis] = []

    def find_test_files(self) -> List[Path]:
        """查找所有测试文件"""
        test_files = []
        for test_dir in self.test_dirs:
            if not test_dir.exists():
                print(f"⚠️  目录不存在：{test_dir}")
                continue
            test_files.extend(test_dir.rglob("test_*.py"))
        return test_files

    def analyze_test_file(self, file_path: Path) -> TestFileAnalysis:
        """分析单个测试文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return TestFileAnalysis(
                file_path=str(file_path),
                test_count=0,
                mock_count=0,
                assertion_count=0,
                has_setup=False,
                has_teardown=False,
                avg_test_length=0,
                quality_score=0,
                quality_level=TestQuality.POOR,
                issues=[f"语法错误：{str(e)}"]
            )

        # 统计测试函数
        test_functions = []
        mock_count = 0
        assertion_count = 0
        has_setup = False
        has_teardown = False

        for node in ast.walk(tree):
            # 检测测试函数
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    test_functions.append(node)
                    # 计算函数长度
                    func_lines = node.end_lineno - node.lineno

                    # 统计 Mock 使用
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                if 'Mock' in child.func.id or 'mock' in child.func.id.lower():
                                    mock_count += 1
                            elif isinstance(child.func, ast.Attribute):
                                if 'Mock' in child.func.attr or 'mock' in child.func.attr.lower():
                                    mock_count += 1

                        # 统计断言
                        if isinstance(child, ast.Assert):
                            assertion_count += 1
                        elif isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Attribute):
                                if child.func.attr.startswith('assert'):
                                    assertion_count += 1

                elif node.name == 'setUp':
                    has_setup = True
                elif node.name == 'tearDown':
                    has_teardown = True

        test_count = len(test_functions)
        avg_test_length = sum(func.end_lineno - func.lineno for func in test_functions) / max(test_count, 1)

        # 计算质量分数
        quality_score = self._calculate_quality_score(
            test_count=test_count,
            mock_count=mock_count,
            assertion_count=assertion_count,
            avg_test_length=avg_test_length,
            has_setup=has_setup,
            has_teardown=has_teardown
        )

        # 识别问题
        issues = self._identify_issues(
            test_count=test_count,
            mock_count=mock_count,
            assertion_count=assertion_count,
            avg_test_length=avg_test_length,
            quality_score=quality_score
        )

        # 确定质量等级
        quality_level = self._get_quality_level(quality_score)

        return TestFileAnalysis(
            file_path=str(file_path),
            test_count=test_count,
            mock_count=mock_count,
            assertion_count=assertion_count,
            has_setup=has_setup,
            has_teardown=has_teardown,
            avg_test_length=avg_test_length,
            quality_score=quality_score,
            quality_level=quality_level,
            issues=issues
        )

    def _calculate_quality_score(
        self,
        test_count: int,
        mock_count: int,
        assertion_count: int,
        avg_test_length: float,
        has_setup: bool,
        has_teardown: bool
    ) -> float:
        """计算质量分数 (0-100)"""
        score = 0

        # 测试数量 (20 分)
        if test_count >= 10:
            score += 20
        elif test_count >= 5:
            score += 15
        elif test_count >= 3:
            score += 10
        else:
            score += 5

        # Mock 使用合理性 (25 分) - 越少越好
        mock_ratio = mock_count / max(test_count, 1)
        if mock_ratio <= 2:
            score += 25
        elif mock_ratio <= 4:
            score += 20
        elif mock_ratio <= 6:
            score += 15
        else:
            score += 5  # 过度 Mock

        # 断言充分性 (25 分)
        assertion_ratio = assertion_count / max(test_count, 1)
        if assertion_ratio >= 3:
            score += 25
        elif assertion_ratio >= 2:
            score += 20
        elif assertion_ratio >= 1:
            score += 15
        else:
            score += 5

        # 测试结构 (15 分)
        if has_setup and has_teardown:
            score += 15
        elif has_setup or has_teardown:
            score += 10

        # 测试长度合理性 (15 分)
        if 5 <= avg_test_length <= 30:
            score += 15
        elif 3 <= avg_test_length <= 50:
            score += 10
        else:
            score += 5

        return min(100, score)

    def _identify_issues(
        self,
        test_count: int,
        mock_count: int,
        assertion_count: int,
        avg_test_length: float,
        quality_score: float
    ) -> List[str]:
        """识别测试问题"""
        issues = []

        # 过度 Mock
        mock_ratio = mock_count / max(test_count, 1)
        if mock_ratio > 6:
            issues.append(f"⚠️  过度使用 Mock (平均每个测试 {mock_ratio:.1f} 个 Mock)")
        elif mock_ratio > 4:
            issues.append(f"⚠️  Mock 使用较多 (平均每个测试 {mock_ratio:.1f} 个)")

        # 断言不足
        assertion_ratio = assertion_count / max(test_count, 1)
        if assertion_ratio < 1:
            issues.append("❌ 断言不足 (平均每个测试少于 1 个断言)")
        elif assertion_ratio < 2:
            issues.append("⚠️  断言较少 (平均每个测试 {:.1f} 个)".format(assertion_ratio))

        # 测试过长
        if avg_test_length > 50:
            issues.append(f"⚠️  测试函数过长 (平均 {avg_test_length:.0f} 行)")

        # 测试过短
        if avg_test_length < 3:
            issues.append(f"⚠️  测试函数过短 (平均 {avg_test_length:.0f} 行)，可能测试不充分")

        # 缺少 fixture
        # 需要读取完整文件内容来检测
        # 简化处理

        # 质量评分低
        if quality_score < 40:
            issues.append("❌ 整体质量较差，需要重构")
        elif quality_score < 60:
            issues.append("⚠️  整体质量一般，建议改进")

        return issues

    def _get_quality_level(self, quality_score: float) -> TestQuality:
        """获取质量等级"""
        if quality_score >= 80:
            return TestQuality.EXCELLENT
        elif quality_score >= 60:
            return TestQuality.GOOD
        elif quality_score >= 40:
            return TestQuality.NEEDS_IMPROVEMENT
        else:
            return TestQuality.POOR

    def validate_all(self) -> List[TestFileAnalysis]:
        """验证所有测试文件"""
        test_files = self.find_test_files()
        print(f"🔍 找到 {len(test_files)} 个测试文件\n")

        for file_path in test_files:
            print(f"分析中：{file_path.name}")
            analysis = self.analyze_test_file(file_path)
            self.results.append(analysis)

        return self.results

    def generate_report(self) -> str:
        """生成质量报告"""
        report_lines = []

        report_lines.append("=" * 70)
        report_lines.append("📋 单元测试质量验证报告")
        report_lines.append("=" * 70)
        report_lines.append("")

        # 总体统计
        total_tests = sum(r.test_count for r in self.results)
        total_mocks = sum(r.mock_count for r in self.results)
        total_assertions = sum(r.assertion_count for r in self.results)
        avg_quality = sum(r.quality_score for r in self.results) / max(len(self.results), 1)

        report_lines.append("【总体统计】")
        report_lines.append(f"测试文件数：{len(self.results)}")
        report_lines.append(f"测试函数总数：{total_tests}")
        report_lines.append(f"Mock 使用总数：{total_mocks}")
        report_lines.append(f"断言使用总数：{total_assertions}")
        report_lines.append(f"平均质量分数：{avg_quality:.1f}/100")
        report_lines.append("")

        # 质量分布
        excellent = sum(1 for r in self.results if r.quality_level == TestQuality.EXCELLENT)
        good = sum(1 for r in self.results if r.quality_level == TestQuality.GOOD)
        needs_improvement = sum(1 for r in self.results if r.quality_level == TestQuality.NEEDS_IMPROVEMENT)
        poor = sum(1 for r in self.results if r.quality_level == TestQuality.POOR)

        report_lines.append("【质量分布】")
        report_lines.append(f"✅ 优秀：{excellent} 个文件")
        report_lines.append(f"✔️  良好：{good} 个文件")
        report_lines.append(f"⚠️  需改进：{needs_improvement} 个文件")
        report_lines.append(f"❌ 较差：{poor} 个文件")
        report_lines.append("")

        # 问题汇总
        all_issues = []
        for result in self.results:
            for issue in result.issues:
                all_issues.append((result.file_path, issue))

        if all_issues:
            report_lines.append("【问题汇总】")
            report_lines.append("-" * 70)
            for file_path, issue in all_issues[:20]:  # 显示前 20 个
                report_lines.append(f"{Path(file_path).name}: {issue}")
            if len(all_issues) > 20:
                report_lines.append(f"... 还有 {len(all_issues) - 20} 个问题")
            report_lines.append("")

        # 改进建议
        report_lines.append("【改进建议】")
        report_lines.append("-" * 70)

        if poor > 0:
            report_lines.append(f"❌ {poor} 个文件质量较差，建议优先重构")
        if needs_improvement > 0:
            report_lines.append(f"⚠️  {needs_improvement} 个文件需要改进，关注以下方面:")

        if total_mocks / max(total_tests, 1) > 4:
            report_lines.append("  • 减少 Mock 使用，增加真实对象测试")
        if total_assertions / max(total_tests, 1) < 2:
            report_lines.append("  • 增加断言数量，确保测试充分性")
        if avg_quality < 60:
            report_lines.append("  • 学习 pytest 最佳实践，提升测试质量")

        report_lines.append("")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)


def main():
    """主函数"""
    print(f"\n{'='*70}")
    print(f"🔍 开始测试质量验证")
    print(f"{'='*70}\n")

    # 测试目录
    test_dirs = [
        "backend/tests",
        "backend/enterprise_gateway/tests",
        "backend/gamification/tests"
    ]

    validator = TestQualityValidator(test_dirs)
    results = validator.validate_all()

    # 生成报告
    report = validator.generate_report()
    print("\n" + report)

    # 保存报告
    reports_dir = Path("backend/reports")
    reports_dir.mkdir(exist_ok=True)

    report_path = reports_dir / f"test_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📄 报告已保存：{report_path}")

    # 返回退出码
    avg_quality = sum(r.quality_score for r in results) / max(len(results), 1)
    sys.exit(0 if avg_quality >= 60 else 1)


if __name__ == "__main__":
    from datetime import datetime
    import sys
    main()
