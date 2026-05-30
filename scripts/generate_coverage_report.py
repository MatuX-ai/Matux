"""
单元测试覆盖率统计与分析报告生成器

功能:
1. 运行 pytest 收集覆盖率数据
2. 生成 HTML/XML 格式报告
3. 识别覆盖率最低的模块
4. 提供测试改进建议
5. 生成执行回测报告

使用方法:
    python scripts/generate_coverage_report.py
    python scripts/generate_coverage_report.py --target-coverage 80
    python scripts/generate_coverage_report.py --module services.payment_service
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


class CoverageAnalyzer:
    """覆盖率分析器"""

    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir)
        self.reports_dir = self.backend_dir / "reports"
        self.coverage_xml = self.reports_dir / "coverage.xml"
        self.test_results_xml = self.reports_dir / "test-results.xml"

    def ensure_reports_dir(self):
        """确保报告目录存在"""
        self.reports_dir.mkdir(exist_ok=True)

    def run_pytest(self, target: str = None, verbose: bool = True):
        """运行 pytest 收集覆盖率"""
        self.ensure_reports_dir()

        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=backend",
            "--cov-report=html:reports/coverage_html",
            "--cov-report=xml:reports/coverage.xml",
            "--cov-report=term-missing",
            "--junit-xml=reports/test-results.xml",
            "-v",
            "--tb=short",
            "-p", "no:warnings"
        ]

        if target:
            cmd.append(target)
        else:
            cmd.extend([
                "backend/tests",
                "backend/enterprise_gateway/tests",
                "backend/gamification/tests"
            ])

        print(f"\n{'='*60}")
        print(f"🧪 运行测试套件...")
        print(f"{'='*60}")
        print(f"命令：{' '.join(cmd)}\n")

        result = subprocess.run(cmd, cwd=self.backend_dir.parent)

        if result.returncode != 0:
            print(f"\n⚠️  部分测试失败，但仍会生成覆盖率报告")

        return result.returncode == 0

    def parse_coverage_xml(self):
        """解析 coverage.xml 文件"""
        if not self.coverage_xml.exists():
            print("❌ 覆盖率 XML 文件不存在，请先运行 pytest")
            return None

        tree = ET.parse(self.coverage_xml)
        root = tree.getroot()

        packages = {}
        classes = []

        # 解析包和类
        for package in root.findall('.//package'):
            pkg_name = package.get('name')
            pkg_data = {
                'name': pkg_name,
                'line-rate': float(package.get('line-rate', 0)),
                'branch-rate': float(package.get('branch-rate', 0)),
                'classes': []
            }

            for cls in package.findall('.//class'):
                cls_data = {
                    'name': cls.get('name'),
                    'filename': cls.get('filename'),
                    'line-rate': float(cls.get('line-rate', 0)),
                    'complexity': float(cls.get('complexity', 0))
                }
                pkg_data['classes'].append(cls_data)
                classes.append(cls_data)

            packages[pkg_name] = pkg_data

        return {
            'packages': packages,
            'classes': classes,
            'total_line_rate': float(root.get('line-rate', 0)),
            'total_branch_rate': float(root.get('branch-rate', 0))
        }

    def get_low_coverage_modules(self, threshold: float = 0.6, limit: int = 20):
        """获取覆盖率低于阈值的模块"""
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            return []

        low_coverage = []
        for cls in coverage_data['classes']:
            if cls['line-rate'] < threshold:
                low_coverage.append({
                    'name': cls['name'],
                    'filename': cls['filename'],
                    'coverage': cls['line-rate'] * 100
                })

        # 按覆盖率排序
        low_coverage.sort(key=lambda x: x['coverage'])
        return low_coverage[:limit]

    def generate_text_report(self, coverage_data: dict):
        """生成文本格式报告"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("📊 单元测试覆盖率报告")
        report_lines.append("=" * 70)
        report_lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # 总体统计
        report_lines.append("【总体覆盖率】")
        total_line = coverage_data['total_line_rate'] * 100
        total_branch = coverage_data['total_branch_rate'] * 100

        status_line = "✅" if total_line >= 80 else "⚠️" if total_line >= 60 else "❌"
        report_lines.append(f"{status_line} 行覆盖率：{total_line:.1f}%")

        status_branch = "✅" if total_branch >= 80 else "⚠️" if total_branch >= 60 else "❌"
        report_lines.append(f"{status_branch} 分支覆盖率：{total_branch:.1f}%")
        report_lines.append("")

        # 包级别统计
        report_lines.append("【包级别覆盖率】")
        report_lines.append("-" * 70)
        report_lines.append(f"{'包名':<50} {'行覆盖':<10} {'分支覆盖':<10}")
        report_lines.append("-" * 70)

        for pkg_name, pkg_data in sorted(coverage_data['packages'].items()):
            line_rate = pkg_data['line-rate'] * 100
            branch_rate = pkg_data['branch-rate'] * 100

            status = "✅" if line_rate >= 80 else "⚠️" if line_rate >= 60 else "❌"
            report_lines.append(
                f"{pkg_name:<50} {line_rate:>6.1f}% {status:<4} {branch_rate:>6.1f}%"
            )
        report_lines.append("")

        # 低覆盖率模块 Top 20
        low_coverage = self.get_low_coverage_modules(threshold=0.6, limit=20)
        if low_coverage:
            report_lines.append("【待改进模块 - 覆盖率最低 Top 20】")
            report_lines.append("-" * 70)
            report_lines.append(f"{'排名':<5} {'模块名':<40} {'文件':<30} {'覆盖率':<10}")
            report_lines.append("-" * 70)

            for idx, module in enumerate(low_coverage, 1):
                report_lines.append(
                    f"{idx:<5} {module['name']:<40} {module['filename']:<30} {module['coverage']:.1f}%"
                )
        report_lines.append("")

        # 改进建议
        report_lines.append("【改进建议】")
        report_lines.append("-" * 70)

        if total_line < 60:
            report_lines.append("❌ 覆盖率低于 60%，需要大量补充测试用例")
        elif total_line < 80:
            report_lines.append("⚠️  覆盖率中等，建议优先补充核心业务逻辑测试")
        else:
            report_lines.append("✅ 覆盖率良好，继续保持并关注边界场景测试")

        if low_coverage:
            report_lines.append(f"\n重点关注以下 {len(low_coverage)} 个低覆盖率模块:")
            for module in low_coverage[:5]:
                report_lines.append(f"  • {module['name']} ({module['coverage']:.1f}%)")

        report_lines.append("")
        report_lines.append("=" * 70)

        return "\n".join(report_lines)

    def generate_json_report(self, coverage_data: dict, all_tests_passed: bool):
        """生成 JSON 格式报告"""
        low_coverage = self.get_low_coverage_modules(threshold=0.6, limit=20)

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_line_rate": coverage_data['total_line_rate'],
                "total_branch_rate": coverage_data['total_branch_rate'],
                "all_tests_passed": all_tests_passed,
                "status": "PASS" if (
                    coverage_data['total_line_rate'] >= 0.6 and all_tests_passed
                ) else "NEEDS_IMPROVEMENT"
            },
            "packages": {
                name: {
                    'line_rate': data['line-rate'],
                    'branch_rate': data['branch-rate'],
                    'class_count': len(data['classes'])
                }
                for name, data in coverage_data['packages'].items()
            },
            "low_coverage_modules": low_coverage,
            "recommendations": self._generate_recommendations(coverage_data, low_coverage)
        }

        return report

    def _generate_recommendations(self, coverage_data: dict, low_coverage: list):
        """生成改进建议"""
        recommendations = []

        total_line = coverage_data['total_line_rate']

        if total_line < 0.6:
            recommendations.append({
                "priority": "HIGH",
                "category": "Coverage",
                "suggestion": "总体覆盖率低于 60%，需要系统性补充测试用例",
                "action_items": [
                    "为核心服务类添加单元测试",
                    "为工具函数添加单元测试",
                    "为 API 路由添加集成测试"
                ]
            })
        elif total_line < 0.8:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Coverage",
                "suggestion": "总体覆盖率中等，优先补充核心模块测试",
                "action_items": [
                    f"针对覆盖率最低的 {len(low_coverage)} 个模块补充测试",
                    "添加边界场景和异常处理测试"
                ]
            })

        if low_coverage:
            top_3 = low_coverage[:3]
            recommendations.append({
                "priority": "HIGH",
                "category": "Critical Modules",
                "suggestion": "以下模块覆盖率极低，需立即补充测试",
                "affected_modules": [m['name'] for m in top_3],
                "action_items": [
                    f"为 {m['name']} 编写至少 3 个测试用例"
                    for m in top_3
                ]
            })

        return recommendations

    def save_reports(self, coverage_data: dict, all_tests_passed: bool):
        """保存各种格式的报告"""
        # 文本报告
        text_report = self.generate_text_report(coverage_data)
        text_report_path = self.reports_dir / f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        print(f"\n📄 文本报告已保存：{text_report_path}")

        # JSON 报告
        json_report = self.generate_json_report(coverage_data, all_tests_passed)
        json_report_path = self.reports_dir / f"coverage_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON 报告已保存：{json_report_path}")

        # HTML 报告 (由 pytest-cov 自动生成)
        html_report_path = self.reports_dir / "coverage_html" / "index.html"
        if html_report_path.exists():
            print(f"📄 HTML 报告已生成：{html_report_path}")

        return text_report_path, json_report_path, html_report_path

    def analyze(self, target: str = None, target_coverage: float = 0.8):
        """执行完整分析流程"""
        print(f"\n{'='*70}")
        print(f"🚀 开始单元测试覆盖率分析")
        print(f"{'='*70}\n")

        # 运行测试
        all_passed = self.run_pytest(target=target)

        # 解析覆盖率
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            print("❌ 无法解析覆盖率数据")
            return False

        # 生成报告
        self.save_reports(coverage_data, all_passed)

        # 输出摘要
        print(f"\n{'='*70}")
        print(f"📊 覆盖率摘要")
        print(f"{'='*70}")
        print(f"总行覆盖率：{coverage_data['total_line_rate']*100:.1f}%")
        print(f"目标覆盖率：{target_coverage*100:.1f}%")

        if coverage_data['total_line_rate'] >= target_coverage:
            print(f"✅ 已达到目标覆盖率!")
        else:
            gap = (target_coverage - coverage_data['total_line_rate']) * 100
            print(f"⚠️  距离目标还差 {gap:.1f}%")

        print(f"{'='*70}\n")

        return coverage_data['total_line_rate'] >= target_coverage


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='单元测试覆盖率分析工具')
    parser.add_argument('--target', type=str, help='指定测试目标 (文件或模块)')
    parser.add_argument('--target-coverage', type=float, default=0.8,
                       help='目标覆盖率 (默认 0.8)')
    parser.add_argument('--skip-test', action='store_true',
                       help='跳过测试执行，仅分析现有报告')

    args = parser.parse_args()

    analyzer = CoverageAnalyzer()

    if args.skip_test:
        # 仅分析现有报告
        coverage_data = analyzer.parse_coverage_xml()
        if coverage_data:
            analyzer.save_reports(coverage_data, True)
            print(f"\n总覆盖率：{coverage_data['total_line_rate']*100:.1f}%")
        else:
            print("❌ 未找到覆盖率报告，请先运行 pytest")
            sys.exit(1)
    else:
        # 完整分析流程
        success = analyzer.analyze(target=args.target, target_coverage=args.target_coverage)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
