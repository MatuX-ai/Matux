#!/usr/bin/env python3
"""
Vircadia 集成防重复开发验证脚本
用途：在提交代码前检查是否有重复实现或模块冲突
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

class VircadiaDuplicationChecker:
    """Vircadia 集成防重复开发检查器"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.check_results = {
            "check_date": datetime.now().isoformat(),
            "workspace": str(self.workspace_root),
            "checks": [],
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def check_file_exists(self, file_path: str, should_exist: bool = False) -> bool:
        """检查文件是否存在"""
        full_path = self.workspace_root / file_path
        exists = full_path.exists()

        result = {
            "check_type": "file_existence",
            "file": file_path,
            "expected": should_exist,
            "actual": exists,
            "passed": exists == should_exist
        }

        self.check_results["checks"].append(result)
        return result["passed"]

    def grep_code_pattern(self, pattern: str, search_dirs: list, expected_found: bool = False) -> bool:
        """使用 grep 搜索代码模式"""
        import subprocess

        found_files = []
        for search_dir in search_dirs:
            try:
                result = subprocess.run(
                    ["grep", "-r", pattern, str(self.workspace_root / search_dir),
                     "--include=*.py", "--include=*.ts", "--include=*.js"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    found_files.extend(lines[:5])  # 最多记录 5 条结果
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        found = len(found_files) > 0
        result = {
            "check_type": "code_pattern_search",
            "pattern": pattern,
            "search_dirs": search_dirs,
            "expected_found": expected_found,
            "actual_found": found,
            "matches_found": len(found_files),
            "sample_matches": found_files,
            "passed": found == expected_found
        }

        self.check_results["checks"].append(result)
        return result["passed"]

    def check_npm_dependency(self, package_name: str) -> bool:
        """检查 NPM 依赖是否安装"""
        package_json_path = self.workspace_root / "package.json"

        if not package_json_path.exists():
            result = {
                "check_type": "npm_dependency",
                "package": package_name,
                "passed": False,
                "error": "package.json not found"
            }
            self.check_results["checks"].append(result)
            return False

        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)

        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})

        found = package_name in dependencies or package_name in dev_dependencies

        result = {
            "check_type": "npm_dependency",
            "package": package_name,
            "found": found,
            "passed": not found  # 期望未找到（防止重复）
        }

        self.check_results["checks"].append(result)
        return result["passed"]

    def check_python_dependency(self, package_name: str) -> bool:
        """检查 Python 依赖是否安装"""
        requirements_files = [
            self.workspace_root / "backend" / "requirements.txt",
            self.workspace_root / "requirements.txt"
        ]

        found = False
        for req_file in requirements_files:
            if req_file.exists():
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if package_name.lower() in content:
                        found = True
                        break

        result = {
            "check_type": "python_dependency",
            "package": package_name,
            "found": found,
            "passed": not found  # 期望未找到（防止重复）
        }

        self.check_results["checks"].append(result)
        return result["passed"]

    def run_all_checks(self) -> dict:
        """运行所有检查"""
        print("=" * 60)
        print("Vircadia 集成防重复开发验证")
        print("=" * 60)

        # 1. 检查关键文件不应存在（阶段一未开始）
        print("\n1️⃣  检查 Docker 配置文件...")
        self.check_file_exists("docker-compose.vircadia.yml", should_exist=False)
        self.check_file_exists(".env.vircadia", should_exist=False)

        print("\n2️⃣  检查前端 SDK 文件...")
        self.check_file_exists("src/app/core/services/vircadia-sdk.service.ts", should_exist=False)
        self.check_file_exists("src/app/models/vircadia.models.ts", should_exist=False)

        print("\n3️⃣  检查后端服务文件...")
        self.check_file_exists("backend/services/metaverse_gateway_service.py", should_exist=False)
        self.check_file_exists("backend/services/vircadia_sso_service.py", should_exist=False)

        print("\n4️⃣  检查代码模式...")
        self.grep_code_pattern(r"class\s+Vircadia", ["backend", "src"], expected_found=False)
        self.grep_code_pattern(r"class\s+MetaverseGateway", ["backend", "src"], expected_found=False)
        self.grep_code_pattern(r"import.*@vircadia", ["src"], expected_found=False)

        print("\n5️⃣  检查依赖...")
        self.check_npm_dependency("@vircadia/web-sdk")
        self.check_npm_dependency("@vircadia/aether-client")
        self.check_python_dependency("vircadia-sdk")

        # 计算统计
        total = len(self.check_results["checks"])
        passed = sum(1 for c in self.check_results["checks"] if c.get("passed", False))
        failed = total - passed

        self.check_results["summary"]["total_checks"] = total
        self.check_results["summary"]["passed"] = passed
        self.check_results["summary"]["failed"] = failed

        # 输出结果
        print("\n" + "=" * 60)
        print(f"验证完成：{passed}/{total} 通过")
        print("=" * 60)

        if failed == 0:
            print("\n✅ 所有检查通过，无重复开发！")
            print("\n可以安全启动阶段一实施:")
            print("   1. VIRCADIA-P1-SETUP-001: 部署 Docker 环境")
            print("   2. VIRCADIA-P1-DEV-001: Web SDK 集成")
            print("   3. VIRCADIA-P1-TEST-001: Avatar 评估")
        else:
            print(f"\n⚠️  发现 {failed} 项失败，请检查是否存在重复开发！")

        print("\n详细报告已保存至：backtest_reports/vircadia_duplication_check.json")

        return self.check_results

    def save_report(self, output_path: str):
        """保存验证报告"""
        report_path = self.workspace_root / output_path
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.check_results, f, indent=2, ensure_ascii=False)

        print(f"📄 报告已保存：{report_path}")


def main():
    """主函数"""
    workspace = os.getenv("WORKSPACE_ROOT", "g:\\iMato")

    checker = VircadiaDuplicationChecker(workspace)
    results = checker.run_all_checks()
    checker.save_report("backtest_reports/vircadia_duplication_check.json")

    # 返回退出码
    if results["summary"]["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
