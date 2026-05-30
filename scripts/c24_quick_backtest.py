"""
C2.4 单元测试覆盖率与质量 - 快速回测脚本

功能:
1. 运行关键测试套件
2. 生成覆盖率基线报告
3. 识别重复开发风险
4. 提供改进优先级建议

使用方法:
    python scripts/c24_quick_backtest.py
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


def print_header(text: str):
    """打印标题"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def run_command(cmd: list, cwd: str = None) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)


def check_pytest_cov_installed() -> bool:
    """检查是否安装了 pytest-cov"""
    try:
        import pytest_cov
        return True
    except ImportError:
        return False


def install_dependencies():
    """安装必要依赖"""
    print("📦 检查依赖...")

    if not check_pytest_cov_installed():
        print("⚠️  未安装 pytest-cov，正在安装...")
        success, stdout, stderr = run_command([
            sys.executable, "-m", "pip", "install", "pytest-cov"
        ])
        if success:
            print("✅ pytest-cov 安装成功")
        else:
            print(f"❌ 安装失败：{stderr}")
            return False
    else:
        print("✅ 依赖已安装")

    return True


def run_smoke_tests() -> dict:
    """运行冒烟测试"""
    print_header("🧪 运行冒烟测试")

    test_files = [
        "backend/tests/test_payment_service.py",
        "backend/tests/test_permission_system.py",
        "backend/tests/test_ai_service.py",
        "backend/enterprise_gateway/tests/test_unit.py",
        "backend/gamification/tests/test_gamification_suite.py"
    ]

    results = {}
    for test_file in test_files[:3]:  # 只测试前 3 个节省时间
        if not Path(test_file).exists():
            print(f"⚠️  文件不存在：{test_file}")
            continue

        print(f"测试中：{Path(test_file).name} ...", end=" ")
        success, stdout, stderr = run_command([
            sys.executable, "-m", "pytest",
            test_file,
            "-v", "--tb=short",
            "-p", "no:warnings"
        ], cwd="backend")

        status = "✅" if success else "❌"
        print(f"{status}")

        results[Path(test_file).stem] = {
            "passed": success,
            "output_lines": len(stdout.split('\n'))
        }

    return results


def generate_coverage_baseline() -> bool:
    """生成覆盖率基线"""
    print_header("📊 生成覆盖率基线")

    # 确保报告目录存在
    reports_dir = Path("backend/reports")
    reports_dir.mkdir(exist_ok=True)

    print("运行 pytest 收集覆盖率数据...")
    success, stdout, stderr = run_command([
        sys.executable, "-m", "pytest",
        "backend/tests",
        "--cov=backend",
        "--cov-report=term-missing",
        "--cov-fail-under=50",
        "-q",
        "-p", "no:warnings"
    ], cwd="backend")

    if success or "FAILED" in stdout:
        # 即使部分测试失败也要显示覆盖率
        print("\n覆盖率统计完成")
        # 提取覆盖率信息
        for line in stdout.split('\n'):
            if 'TOTAL' in line and '%' in line:
                print(f"📊 {line.strip()}")
        return True
    else:
        print(f"❌ 覆盖率统计失败：{stderr}")
        return False


def analyze_existing_tests() -> dict:
    """分析现有测试"""
    print_header("🔍 分析现有测试资产")

    backend_tests = Path("backend/tests")
    enterprise_tests = Path("backend/enterprise_gateway/tests")
    gamification_tests = Path("backend/gamification/tests")

    analysis = {
        "backend_tests": {
            "count": len(list(backend_tests.glob("test_*.py"))) if backend_tests.exists() else 0,
            "path": str(backend_tests)
        },
        "enterprise_tests": {
            "count": len(list(enterprise_tests.glob("test_*.py"))) if enterprise_tests.exists() else 0,
            "path": str(enterprise_tests)
        },
        "gamification_tests": {
            "count": len(list(gamification_tests.glob("test_*.py"))) if gamification_tests.exists() else 0,
            "path": str(gamification_tests)
        }
    }

    total = sum(v["count"] for v in analysis.values())
    print(f"测试文件总数：{total}")
    print(f"  • backend/tests: {analysis['backend_tests']['count']} 个")
    print(f"  • enterprise_gateway/tests: {analysis['enterprise_tests']['count']} 个")
    print(f"  • gamification/tests: {analysis['gamification_tests']['count']} 个")

    return analysis


def identify_redundancy_risk() -> list:
    """识别重复开发风险"""
    print_header("⚠️  识别重复开发风险")

    risks = []

    # 检查是否有重复的测试文件
    test_files = set()
    duplicates = []

    for test_dir in ["backend/tests", "backend/enterprise_gateway/tests", "backend/gamification/tests"]:
        test_path = Path(test_dir)
        if not test_path.exists():
            continue

        for test_file in test_path.rglob("test_*.py"):
            filename = test_file.name
            if filename in test_files:
                duplicates.append(filename)
            test_files.add(filename)

    if duplicates:
        risks.append({
            "type": "duplicate_filenames",
            "severity": "medium",
            "files": duplicates,
            "suggestion": "检查是否存在重复测试，考虑合并或重命名"
        })
        print(f"⚠️  发现 {len(duplicates)} 个重复的测试文件名:")
        for dup in duplicates[:5]:
            print(f"   - {dup}")
    else:
        print("✅ 未发现重复的测试文件名")

    # 检查是否有过于相似的测试内容
    # (简化处理，实际应该用 AST 分析)

    return risks


def generate_improvement_priorities(analysis: dict) -> list:
    """生成改进优先级列表"""
    print_header("🎯 改进优先级建议")

    priorities = []

    # 高优先级 - 核心模块无测试
    critical_services_without_tests = [
        "ar_physics_service.py",
        "creativity_service.py",
        "document_service.py",
        "model_manager.py",
        "order_manager.py"
    ]

    for service in critical_services_without_tests:
        service_path = Path(f"backend/services/{service}")
        if service_path.exists():
            test_name = f"test_{service.replace('.py', '')}.py"
            test_path = Path(f"backend/tests/{test_name}")
            if not test_path.exists():
                priorities.append({
                    "level": "HIGH",
                    "module": service,
                    "action": f"创建 {test_name}",
                    "reason": "核心服务缺少单元测试"
                })

    # 中优先级 - 工具函数测试不足
    utils_without_tests = [
        "decorators.py",
        "circuit_breaker.py",
        "database.py"
    ]

    for util in utils_without_tests:
        util_path = Path(f"backend/utils/{util}")
        if util_path.exists():
            test_name = f"test_{util}"
            test_path = Path(f"backend/tests/{test_name}")
            if not test_path.exists():
                priorities.append({
                    "level": "MEDIUM",
                    "module": util,
                    "action": f"创建 {test_name}",
                    "reason": "工具函数缺少独立测试"
                })

    # 显示优先级
    high_priority = [p for p in priorities if p["level"] == "HIGH"]
    medium_priority = [p for p in priorities if p["level"] == "MEDIUM"]

    print(f"高优先级任务 ({len(high_priority)} 个):")
    for task in high_priority[:5]:
        print(f"  🔴 {task['module']}: {task['action']}")

    print(f"\n中优先级任务 ({len(medium_priority)} 个):")
    for task in medium_priority[:5]:
        print(f"  🟡 {task['module']}: {task['action']}")

    return priorities


def generate_backtest_report(
    smoke_results: dict,
    analysis: dict,
    risks: list,
    priorities: list
) -> dict:
    """生成回测报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_test_files": sum(v["count"] for v in analysis.values()),
            "smoke_tests_passed": sum(1 for v in smoke_results.values() if v["passed"]),
            "total_smoke_tests": len(smoke_results),
            "redundancy_risks": len(risks),
            "improvement_tasks": len(priorities)
        },
        "smoke_tests": smoke_results,
        "test_assets": analysis,
        "risks": risks,
        "priorities": priorities,
        "recommendations": []
    }

    # 生成建议
    if report["summary"]["smoke_tests_passed"] < report["summary"]["total_smoke_tests"]:
        report["recommendations"].append({
            "priority": "CRITICAL",
            "suggestion": "部分现有测试失败，需立即修复"
        })

    if report["summary"]["redundancy_risks"] > 0:
        report["recommendations"].append({
            "priority": "HIGH",
            "suggestion": "存在重复开发风险，建议先清理再新增"
        })

    if len(priorities) > 10:
        report["recommendations"].append({
            "priority": "MEDIUM",
            "suggestion": "待补充测试较多，建议分批次实施"
        })

    return report


def main():
    """主函数"""
    print_header("C2.4 单元测试覆盖率与质量 - 快速回测")

    # 1. 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，无法继续")
        sys.exit(1)

    # 2. 分析现有测试
    analysis = analyze_existing_tests()

    # 3. 运行冒烟测试
    smoke_results = run_smoke_tests()

    # 4. 生成覆盖率基线
    coverage_success = generate_coverage_baseline()

    # 5. 识别重复开发风险
    risks = identify_redundancy_risk()

    # 6. 生成改进优先级
    priorities = generate_improvement_priorities(analysis)

    # 7. 生成回测报告
    report = generate_backtest_report(smoke_results, analysis, risks, priorities)

    # 8. 保存报告
    reports_dir = Path("backend/reports")
    reports_dir.mkdir(exist_ok=True)

    report_path = reports_dir / f"c24_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print_header("📋 回测总结")
    print(f"✅ 测试文件总数：{report['summary']['total_test_files']}")
    print(f"{'✅' if report['summary']['smoke_tests_passed'] == report['summary']['total_smoke_tests'] else '⚠️'}  冒烟测试：{report['summary']['smoke_tests_passed']}/{report['summary']['total_smoke_tests']}")
    print(f"{'✅' if coverage_success else '⚠️'}  覆盖率基线：{'生成成功' if coverage_success else '生成失败'}")
    print(f"⚠️  重复开发风险：{report['summary']['redundancy_risks']} 个")
    print(f"🎯 改进任务：{report['summary']['improvement_tasks']} 个")
    print(f"\n📄 详细报告：{report_path}")

    # 返回退出码
    has_critical_issues = (
        report['summary']['smoke_tests_passed'] < report['summary']['total_smoke_tests'] or
        report['summary']['redundancy_risks'] > 3
    )

    sys.exit(1 if has_critical_issues else 0)


if __name__ == "__main__":
    main()
