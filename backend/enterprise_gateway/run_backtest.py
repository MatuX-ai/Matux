"""
企业API网关回测执行脚本
运行完整的测试套件并生成测试报告
"""

from datetime import datetime
import json
import os
import subprocess
import sys


def run_tests():
    """运行所有测试并收集结果"""
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "summary": {},
        "unit_tests": {},
        "integration_tests": {},
        "performance_tests": {},
        "coverage": {},
    }

    print("🚀 开始执行企业API网关回测...")

    # 运行单元测试
    print("\n🔬 运行单元测试...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_unit.py",
                "-v",
                "--tb=short",
                "--junit-xml=reports/unit_test_results.xml",
            ],
            cwd="backend/enterprise_gateway",
            capture_output=True,
            text=True,
        )

        test_results["unit_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": "FAILED" not in result.stdout,
            "duration": "N/A",  # 可以从XML报告中解析
        }
        print(f"单元测试结果: {'✅ 通过' if result.returncode == 0 else '❌ 失败'}")

    except Exception as e:
        test_results["unit_tests"] = {"exit_code": 1, "error": str(e), "passed": False}
        print(f"单元测试执行失败: {e}")

    # 运行集成测试
    print("\n🔗 运行集成测试...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_integration.py",
                "-v",
                "--tb=short",
                "--junit-xml=reports/integration_test_results.xml",
            ],
            cwd="backend/enterprise_gateway",
            capture_output=True,
            text=True,
        )

        test_results["integration_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": "FAILED" not in result.stdout,
        }
        print(f"集成测试结果: {'✅ 通过' if result.returncode == 0 else '❌ 失败'}")

    except Exception as e:
        test_results["integration_tests"] = {
            "exit_code": 1,
            "error": str(e),
            "passed": False,
        }
        print(f"集成测试执行失败: {e}")

    # 运行性能测试
    print("\n⚡ 运行性能测试...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_performance.py",
                "-v",
                "--tb=short",
                "-k",
                "not slow",  # 跳过标记为slow的测试
                "--junit-xml=reports/performance_test_results.xml",
            ],
            cwd="backend/enterprise_gateway",
            capture_output=True,
            text=True,
        )

        test_results["performance_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": "FAILED" not in result.stdout,
        }
        print(f"性能测试结果: {'✅ 通过' if result.returncode == 0 else '❌ 失败'}")

    except Exception as e:
        test_results["performance_tests"] = {
            "exit_code": 1,
            "error": str(e),
            "passed": False,
        }
        print(f"性能测试执行失败: {e}")

    # 计算总体统计
    passed_tests = sum(
        [
            test_results["unit_tests"].get("passed", False),
            test_results["integration_tests"].get("passed", False),
            test_results["performance_tests"].get("passed", False),
        ]
    )

    total_tests = 3
    success_rate = (passed_tests / total_tests) * 100

    test_results["summary"] = {
        "total_test_suites": total_tests,
        "passed_test_suites": passed_tests,
        "failed_test_suites": total_tests - passed_tests,
        "success_rate": round(success_rate, 2),
        "overall_status": "PASS" if success_rate >= 80 else "FAIL",
    }

    return test_results


def generate_html_report(test_results):
    """生成HTML格式的测试报告"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企业API网关回测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #ecf0f1; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric.pass {{ background: #d5f4e6; }}
        .metric.fail {{ background: #fadbd8; }}
        .test-section {{ margin-bottom: 30px; }}
        .test-header {{ background: #3498db; color: white; padding: 10px 15px; border-radius: 5px; margin-bottom: 15px; }}
        .test-result {{ padding: 15px; border-left: 4px solid; }}
        .test-result.pass {{ border-color: #27ae60; background: #d5f4e6; }}
        .test-result.fail {{ border-color: #e74c3c; background: #fadbd8; }}
        .details {{ margin-top: 10px; font-size: 0.9em; }}
        .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 企业API网关回测报告</h1>
            <p>测试时间: {test_results['timestamp']}</p>
        </div>

        <div class="summary">
            <div class="metric {'pass' if test_results['summary']['overall_status'] == 'PASS' else 'fail'}">
                <h3>总体状态</h3>
                <p style="font-size: 24px; font-weight: bold;">{test_results['summary']['overall_status']}</p>
            </div>
            <div class="metric">
                <h3>测试套件总数</h3>
                <p style="font-size: 24px; font-weight: bold;">{test_results['summary']['total_test_suites']}</p>
            </div>
            <div class="metric pass">
                <h3>通过套件</h3>
                <p style="font-size: 24px; font-weight: bold;">{test_results['summary']['passed_test_suites']}</p>
            </div>
            <div class="metric fail">
                <h3>失败套件</h3>
                <p style="font-size: 24px; font-weight: bold;">{test_results['summary']['failed_test_suites']}</p>
            </div>
            <div class="metric">
                <h3>成功率</h3>
                <p style="font-size: 24px; font-weight: bold;">{test_results['summary']['success_rate']}%</p>
            </div>
        </div>

        <div class="test-section">
            <div class="test-header">
                <h2>🔬 单元测试</h2>
            </div>
            <div class="test-result {'pass' if test_results['unit_tests'].get('passed', False) else 'fail'}">
                <strong>状态:</strong> {'✅ 通过' if test_results['unit_tests'].get('passed', False) else '❌ 失败'}
                <div class="details">
                    <strong>退出码:</strong> {test_results['unit_tests'].get('exit_code', 'N/A')}<br>
                    <strong>执行详情:</strong><br>
                    <pre>{test_results['unit_tests'].get('stdout', '无输出')}</pre>
                </div>
            </div>
        </div>

        <div class="test-section">
            <div class="test-header">
                <h2>🔗 集成测试</h2>
            </div>
            <div class="test-result {'pass' if test_results['integration_tests'].get('passed', False) else 'fail'}">
                <strong>状态:</strong> {'✅ 通过' if test_results['integration_tests'].get('passed', False) else '❌ 失败'}
                <div class="details">
                    <strong>退出码:</strong> {test_results['integration_tests'].get('exit_code', 'N/A')}<br>
                    <strong>执行详情:</strong><br>
                    <pre>{test_results['integration_tests'].get('stdout', '无输出')}</pre>
                </div>
            </div>
        </div>

        <div class="test-section">
            <div class="test-header">
                <h2>⚡ 性能测试</h2>
            </div>
            <div class="test-result {'pass' if test_results['performance_tests'].get('passed', False) else 'fail'}">
                <strong>状态:</strong> {'✅ 通过' if test_results['performance_tests'].get('passed', False) else '❌ 失败'}
                <div class="details">
                    <strong>退出码:</strong> {test_results['performance_tests'].get('exit_code', 'N/A')}<br>
                    <strong>执行详情:</strong><br>
                    <pre>{test_results['performance_tests'].get('stdout', '无输出')}</pre>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by iMato Enterprise API Gateway Test Suite</p>
        </div>
    </div>
</body>
</html>
"""

    return html_content


def main():
    """主函数"""
    # 创建报告目录
    os.makedirs("backend/enterprise_gateway/reports", exist_ok=True)

    # 运行测试
    test_results = run_tests()

    # 生成JSON报告
    json_report_path = (
        "backend/enterprise_gateway/reports/enterprise_backtest_report.json"
    )
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    # 生成HTML报告
    html_content = generate_html_report(test_results)
    html_report_path = (
        "backend/enterprise_gateway/reports/enterprise_backtest_report.html"
    )
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 输出摘要
    print(f"\n{'='*60}")
    print("📋 回测执行完成!")
    print(f"{'='*60}")
    print(f"总体状态: {test_results['summary']['overall_status']}")
    print(f"成功率: {test_results['summary']['success_rate']}%")
    print(
        f"通过套件: {test_results['summary']['passed_test_suites']}/{test_results['summary']['total_test_suites']}"
    )
    print(f"{'='*60}")
    print(f"详细报告已生成:")
    print(f"  - JSON格式: {json_report_path}")
    print(f"  - HTML格式: {html_report_path}")

    # 返回退出码
    sys.exit(0 if test_results["summary"]["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
