#!/usr/bin/env python3
"""
预提交代码预览检查工具
在本地提前发现 CI 问题，避免提交后才知道失败
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    passed: bool
    message: str
    suggestions: List[str]


class PreCommitChecker:
    """预提交检查器"""

    def __init__(self):
        self.project_root = Path("g:/iMato")
        self.results: List[CheckResult] = []

    def run_command(self, cmd: str, cwd: Path = None) -> Tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root,
                timeout=120
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, f"执行出错：{str(e)}"

    def check_git_status(self) -> CheckResult:
        """检查 Git 状态"""
        success, output = self.run_command("git status --porcelain")

        if not success:
            return CheckResult(
                name="Git 状态检查",
                passed=False,
                message="无法获取 Git 状态",
                suggestions=["确保当前目录是 Git 仓库"]
            )

        changed_files = [line for line in output.strip().split('\n') if line]

        if not changed_files:
            return CheckResult(
                name="Git 状态检查",
                passed=False,
                message="没有检测到变更的文件",
                suggestions=["先添加要提交的文件：git add <file>"]
            )

        return CheckResult(
            name="Git 状态检查",
            passed=True,
            message=f"检测到 {len(changed_files)} 个变更文件",
            suggestions=[]
        )

    def check_frontend_lint(self) -> CheckResult:
        """检查前端代码质量"""
        print("\n🔍 检查前端代码质量...")

        # ESLint 检查
        print("   ├─ 运行 ESLint...")
        eslint_ok, eslint_output = self.run_command("npm run lint:ts-check")

        # Stylelint 检查
        print("   ├─ 运行 Stylelint...")
        stylelint_ok, stylelint_output = self.run_command("npm run lint:scss-check")

        # Prettier 检查
        print("   └─ 运行 Prettier...")
        prettier_ok, prettier_output = self.run_command("npm run format:check")

        all_passed = eslint_ok and stylelint_ok and prettier_ok

        suggestions = []
        if not eslint_ok:
            suggestions.append("运行 'npm run lint:ts -- --fix' 自动修复 ESLint 问题")
        if not stylelint_ok:
            suggestions.append("运行 'npm run lint:scss -- --fix' 自动修复 Stylelint 问题")
        if not prettier_ok:
            suggestions.append("运行 'npm run format' 自动格式化代码")

        return CheckResult(
            name="前端质量检查",
            passed=all_passed,
            message=f"ESLint: {'✅' if eslint_ok else '❌'} | "
                   f"Stylelint: {'✅' if stylelint_ok else '❌'} | "
                   f"Prettier: {'✅' if prettier_ok else '❌'}",
            suggestions=suggestions
        )

    def check_backend_lint(self) -> CheckResult:
        """检查后端代码质量"""
        print("\n🔍 检查后端代码质量...")

        backend_dir = self.project_root / "backend"
        if not backend_dir.exists():
            return CheckResult(
                name="后端质量检查",
                passed=False,
                message="后端目录不存在",
                suggestions=[]
            )

        # Black 格式检查
        print("   ├─ 运行 Black 格式检查...")
        black_ok, black_output = self.run_command("black --check backend/", backend_dir.parent)

        # isort 导入检查
        print("   ├─ 运行 isort 导入检查...")
        isort_ok, isort_output = self.run_command("isort --check-only backend/", backend_dir.parent)

        # Flake8 代码检查
        print("   └─ 运行 Flake8 代码检查...")
        flake8_ok, flake8_output = self.run_command("flake8 backend/", backend_dir.parent)

        all_passed = black_ok and isort_ok and flake8_ok

        suggestions = []
        if not black_ok:
            suggestions.append("运行 'black backend/' 自动格式化 Python 代码")
        if not isort_ok:
            suggestions.append("运行 'isort backend/' 自动排序导入语句")
        if not flake8_ok:
            suggestions.append("手动修复 Flake8 报告的代码问题")

        return CheckResult(
            name="后端质量检查",
            passed=all_passed,
            message=f"Black: {'✅' if black_ok else '❌'} | "
                   f"isort: {'✅' if isort_ok else '❌'} | "
                   f"Flake8: {'✅' if flake8_ok else '❌'}",
            suggestions=suggestions
        )

    def check_type_checking(self) -> CheckResult:
        """检查类型检查"""
        print("\n🔍 检查 TypeScript 类型...")

        type_ok, output = self.run_command("npx tsc --noEmit")

        if type_ok:
            return CheckResult(
                name="类型检查",
                passed=True,
                message="TypeScript 类型检查通过 ✅",
                suggestions=[]
            )
        else:
            # 统计错误数量
            error_count = output.lower().count("error")
            return CheckResult(
                name="类型检查",
                passed=False,
                message=f"发现约 {error_count} 个类型错误",
                suggestions=[
                    "查看详细错误信息：npx tsc --noEmit",
                    "根据错误提示修复类型问题"
                ]
            )

    def check_test_coverage(self) -> CheckResult:
        """检查测试覆盖率"""
        print("\n🔍 检查测试覆盖率...")

        # 运行测试（如果有的话）
        test_ok, test_output = self.run_command("npm test")

        if test_ok:
            return CheckResult(
                name="测试检查",
                passed=True,
                message="单元测试通过 ✅",
                suggestions=[]
            )
        else:
            return CheckResult(
                name="测试检查",
                passed=False,
                message="单元测试失败或无测试用例",
                suggestions=[
                    "确保新增代码包含对应的单元测试",
                    "运行 'npm test' 查看详细信息"
                ]
            )

    def check_changed_files(self) -> CheckResult:
        """检查变更文件列表"""
        success, output = self.run_command("git diff --cached --name-only")

        if not success:
            return CheckResult(
                name="变更文件检查",
                passed=False,
                message="无法获取已暂存的变更文件",
                suggestions=["使用 'git add <file>' 添加要提交的文件"]
            )

        changed_files = [f for f in output.strip().split('\n') if f]

        if not changed_files:
            return CheckResult(
                name="变更文件检查",
                passed=False,
                message="没有已暂存的变更文件",
                suggestions=["使用 'git add <file>' 添加要提交的文件"]
            )

        # 分析文件类型
        ts_files = [f for f in changed_files if f.endswith(('.ts', '.tsx'))]
        py_files = [f for f in changed_files if f.endswith('.py')]
        scss_files = [f for f in changed_files if f.endswith(('.scss', '.css'))]

        message_parts = []
        if ts_files:
            message_parts.append(f"{len(ts_files)} 个 TypeScript 文件")
        if py_files:
            message_parts.append(f"{len(py_files)} 个 Python 文件")
        if scss_files:
            message_parts.append(f"{len(scss_files)} 个样式文件")

        return CheckResult(
            name="变更文件检查",
            passed=True,
            message=f"准备提交：{', '.join(message_parts)}",
            suggestions=[]
        )

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print("=" * 60)
        print("🔍 开始预提交代码质量检查")
        print("=" * 60)

        # 基础检查
        self.results.append(self.check_git_status())
        self.results.append(self.check_changed_files())

        # 前端检查
        self.results.append(self.check_frontend_lint())

        # 后端检查
        self.results.append(self.check_backend_lint())

        # 类型检查
        self.results.append(self.check_type_checking())

        # 测试检查（可选）
        # self.results.append(self.check_test_coverage())

        # 打印结果
        print("\n" + "=" * 60)
        print("📊 检查结果汇总")
        print("=" * 60)

        all_passed = True
        for result in self.results:
            status = "✅" if result.passed else "❌"
            print(f"{status} {result.name}: {result.message}")

            if not result.passed and result.suggestions:
                for suggestion in result.suggestions:
                    print(f"   💡 {suggestion}")

        # 总结
        print("\n" + "=" * 60)
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)

        if all_passed:
            print(f"✅ 所有检查通过 ({passed_count}/{total_count})")
            print("💡 代码符合 CI/CD 质量标准，可以安全提交")
            return True
        else:
            failed_count = total_count - passed_count
            print(f"❌ {failed_count} 项检查未通过 ({passed_count}/{total_count})")
            print("💡 建议先修复问题再提交，避免 CI/CD 失败")
            return False

    def generate_report(self) -> str:
        """生成检查报告"""
        report_lines = [
            "# 预提交代码质量检查报告",
            f"\n检查时间：{subprocess.getoutput('date')}",
            f"\n检查项目数：{len(self.results)}",
            "\n## 检查结果\n",
        ]

        for result in self.results:
            status = "✅" if result.passed else "❌"
            report_lines.append(f"### {status} {result.name}")
            report_lines.append(f"\n{result.message}\n")

            if result.suggestions:
                report_lines.append("**改进建议:**\n")
                for i, suggestion in enumerate(result.suggestions, 1):
                    report_lines.append(f"{i}. {suggestion}\n")

        return "\n".join(report_lines)


def main():
    """主函数"""
    checker = PreCommitChecker()

    try:
        all_passed = checker.run_all_checks()

        # 保存报告
        report = checker.generate_report()
        report_path = checker.project_root / "precommit_check_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📄 详细报告已保存至：{report_path}")

        # 返回退出码
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程出错：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
