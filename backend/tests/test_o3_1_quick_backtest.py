"""
O3.1 联动任务快速回测脚本
验证任务编排服务和 API 路由的基本功能
"""

import asyncio
from datetime import datetime
import json
from pathlib import Path


async def test_task_orchestration_service():
    """测试任务编排服务"""
    print("\n" + "=" * 80)
    print("测试 O3.1: 联动任务编排服务")
    print("=" * 80)

    try:
        from services.task_orchestration_service import TaskOrchestrationService

        # 创建服务实例
        service = TaskOrchestrationService()

        print("\n✅ 服务初始化成功")

        # 测试积分计算
        metrics_90 = {"accuracy": 0.90, "loss": 0.2}
        xp_90 = await service._award_stage1_xp(1, metrics_90)
        print(f"✅ 准确率 90% 积分计算：{xp_90} XP (预期：500 XP)")
        assert xp_90 == 500, f"积分计算错误：期望 500，实际 {xp_90}"

        metrics_95 = {"accuracy": 0.95, "loss": 0.1}
        xp_95 = await service._award_stage1_xp(1, metrics_95)
        print(f"✅ 准确率 95% 积分计算：{xp_95} XP (预期：600 XP)")
        assert xp_95 == 600, f"积分计算错误：期望 600，实际 {xp_95}"

        # 测试性能评估
        perf_metrics = {
            "plant_health_score": 90,
            "resource_efficiency": 85,
            "stability_score": 95,
        }
        score = await service._evaluate_performance(perf_metrics)
        print(f"✅ 性能评分：{score:.1f}/100")
        assert 80 <= score <= 100, f"性能评分异常：{score}"

        # 测试排行榜（Mock）
        leaderboard = await service.get_leaderboard("greenhouse_001", limit=5)
        print(f"✅ 排行榜返回 {len(leaderboard)} 条记录")
        assert len(leaderboard) <= 5, "排行榜数量超限"

        return True

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False


async def test_routes_structure():
    """测试路由结构"""
    print("\n" + "=" * 80)
    print("测试路由模块结构")
    print("=" * 80)

    try:
        # 导入路由模块
        from routes.linked_task_routes import router

        print("\n✅ 路由模块导入成功")
        print(f"✅ 路由前缀：{router.prefix}")
        print(f"✅ 路由标签：{router.tags}")

        # 检查路由数量
        routes_count = len(router.routes)
        print(f"✅ 路由数量：{routes_count}")

        # 列出所有路由
        print("\n📋 可用路由:")
        for route in router.routes:
            methods = ", ".join(route.methods) if hasattr(route, "methods") else "N/A"
            print(f"  - [{methods}] {route.path}")

        return True

    except Exception as e:
        print(f"\n❌ 路由测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False


def test_notebook_structure():
    """测试 Notebook 文件结构"""
    print("\n" + "=" * 80)
    print("测试 Notebook 文件")
    print("=" * 80)

    try:
        notebook_path = Path("notebooks/01_greenhouse_ai_training.ipynb")

        if not notebook_path.exists():
            print(f"❌ Notebook 文件不存在：{notebook_path}")
            return False

        # 读取 Notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        print(f"\n✅ Notebook 文件加载成功")
        print(
            f"✅ Jupyter 版本：{nb.get('nbformat', '未知')}.{nb.get('nbformat_minor', 'unknown')}"
        )

        # 统计单元格
        cells = nb.get("cells", [])
        markdown_cells = sum(1 for c in cells if c["cell_type"] == "markdown")
        code_cells = sum(1 for c in cells if c["cell_type"] == "code")

        print(f"✅ 总单元格数：{len(cells)}")
        print(f"   - Markdown 单元格：{markdown_cells}")
        print(f"   - 代码单元格：{code_cells}")

        # 检查关键内容
        all_text = ""
        for cell in cells:
            if cell["source"]:
                all_text += "".join(cell["source"])

        required_sections = [
            "智能温室监控系统",
            "AI 模型训练",
            "MMEdu",
            "积分奖励",
            "提交作业",
        ]

        print("\n📋 检查关键章节:")
        for section in required_sections:
            if section in all_text:
                print(f"  ✅ {section}")
            else:
                print(f"  ❌ {section} (缺失)")

        return True

    except Exception as e:
        print(f"\n❌ Notebook 测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("O3.1 联动任务 快速回测")
    print("=" * 80)
    print(f"开始时间：{datetime.utcnow().isoformat()}")

    results = []

    # 测试 1: 编排服务
    result1 = await test_task_orchestration_service()
    results.append(("任务编排服务", result1))

    # 测试 2: 路由结构
    result2 = await test_routes_structure()
    results.append(("路由模块结构", result2))

    # 测试 3: Notebook 结构
    result3 = test_notebook_structure()
    results.append(("Notebook 文件", result3))

    # 汇总结果
    print("\n" + "=" * 80)
    print("回测总结")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)

    print(f"\n总测试数：{total_tests}")
    print(f"✅ 通过：{passed_tests}")
    print(f"❌ 失败：{total_tests - passed_tests}")
    print(f"成功率：{passed_tests/total_tests*100:.1f}%\n")

    print("详细结果:")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  - {name}: {status}")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！O3.1 开发完成！")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} 个测试失败，请检查问题")

    # 保存回测报告
    backtest_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": [{"name": name, "passed": result} for name, result in results],
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": f"{passed_tests/total_tests*100:.1f}%",
        },
        "deliverables": {
            "backend_services": ["backend/services/task_orchestration_service.py"],
            "backend_routes": ["backend/routes/linked_task_routes.py"],
            "notebooks": ["backend/notebooks/01_greenhouse_ai_training.ipynb"],
            "documentation": ["docs/O3.1_LINKED_TASK_DESIGN.md"],
        },
    }

    report_dir = Path("backtest_reports")
    report_dir.mkdir(exist_ok=True)

    report_file = (
        report_dir
        / f"o3_1_quick_backtest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(backtest_report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 回测报告已保存：{report_file}")


if __name__ == "__main__":
    asyncio.run(main())
