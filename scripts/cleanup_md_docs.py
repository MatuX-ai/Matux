#!/usr/bin/env python3
"""
MD文档清理和归拢脚本
功能：
1. 识别并删除过时的重复文档
2. 将分散的文档按主题归类
3. 创建统一的文档索引
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(r"g:\iMato")

# 定义需要删除的过时/重复文档
OBSOLETE_DOCS = [
    # OpenHydra/XEdu 实施状态报告（保留最新的20260304版本）
    "reports/OPENHYDRA_XEDU_IMPLEMENTATION_STATUS_20260303.md",

    # backup_course_material 中的临时文档（已集成到正式文档中）
    "backup_course_material/COURSE_DETAIL_INTEGRATION_REPORT.md",
    "backup_course_material/COURSE_DETAIL_TEST_REPORT.md",
    "backup_course_material/COURSE_DETAIL_VERIFICATION_GUIDE.md",
    "backup_course_material/MOCK_DATA_UPDATE_STEM.md",
    "backup_course_material/MULTIMEDIA_COURSEWARE_SUPPORT.md",
]

# 定义需要移动的文档及其目标位置
DOCS_TO_MOVE = [
    # backtest_reports 中的MD文件 -> documentation/tests/
    ("backtest_reports/VIRCADIA_P1_DEV_001_CHECKLIST.md",
     "documentation/tests/vircadia-p1-dev-checklist.md"),
    ("backtest_reports/VIRCADIA_P1_SETUP_001_BACKTEST_SUMMARY.md",
     "documentation/tests/vircadia-p1-setup-summary.md"),
]

def delete_obsolete_docs():
    """删除过时/重复的文档"""
    print("=" * 80)
    print("步骤 1: 删除过时/重复的文档")
    print("=" * 80)

    deleted_count = 0
    for doc_path in OBSOLETE_DOCS:
        full_path = PROJECT_ROOT / doc_path
        if full_path.exists():
            try:
                full_path.unlink()
                print(f"✅ 已删除: {doc_path}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除失败 {doc_path}: {e}")
        else:
            print(f"⚠️  文件不存在（可能已删除）: {doc_path}")

    print(f"\n总计删除: {deleted_count} 个文件\n")
    return deleted_count

def move_docs():
    """移动文档到合适的位置"""
    print("=" * 80)
    print("步骤 2: 移动文档到合适的目录")
    print("=" * 80)

    moved_count = 0
    for src_rel, dst_rel in DOCS_TO_MOVE:
        src_path = PROJECT_ROOT / src_rel
        dst_path = PROJECT_ROOT / dst_rel

        if src_path.exists():
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.move(str(src_path), str(dst_path))
                print(f"✅ 已移动: {src_rel} -> {dst_rel}")
                moved_count += 1
            except Exception as e:
                print(f"❌ 移动失败 {src_rel}: {e}")
        else:
            print(f"⚠️  源文件不存在: {src_rel}")

    print(f"\n总计移动: {moved_count} 个文件\n")
    return moved_count

def create_doc_index():
    """创建统一的文档索引"""
    print("=" * 80)
    print("步骤 3: 创建统一的文档索引")
    print("=" * 80)

    index_content = """# iMato 项目文档索引

**最后更新**: 2026-04-28
**维护者**: iMato Team

---

## 📚 文档分类

### 1. 项目概览与架构
- [README.md](../README.md) - 项目主文档
- [GLOBAL_TECHNICAL_ARCHITECTURE.md](../GLOBAL_TECHNICAL_ARCHITECTURE.md) - 全局技术架构
- [PROJECT_ROADMAP.md](../PROJECT_ROADMAP.md) - 项目路线图
- [SECURITY.md](../SECURITY.md) - 安全政策

### 2. OpenHydra + XEdu 集成文档
- [集成方案总览](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md) - 完整的集成计划
- [阶段一完成总结](./phase1-completion-summary.md) - O1.1-O1.3 任务完成报告
- [微课程与AI助手](./o2.3-o2.4-task-complete-report.md) - O2.3 & O2.4 完成报告
- [SSO技术方案](./o1.3-sso-technical-design.md) - 单点登录设计
- [快速开始指南](../../docs/OPENHYDRA_QUICKSTART.md) - 5分钟快速体验

### 3. 测试与回测报告
- [Vircadia P1 开发检查清单](./vircadia-p1-dev-checklist.md)
- [Vircadia P1 设置总结](./vircadia-p1-setup-summary.md)

### 4. 其他技术文档
详见 [documentation/README.md](../README.md)

---

## 🔍 快速查找

### 我是...
- **新开发者** → 查看 [README.md](../README.md) 和 [快速开始](../../docs/QUICK_START_GUIDE.md)
- **AI工程师** → 查看 [OpenHydra集成方案](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md)
- **测试工程师** → 查看本目录下的测试报告
- **架构师** → 查看 [全局技术架构](../GLOBAL_TECHNICAL_ARCHITECTURE.md)

---

## 📊 文档统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 核心架构文档 | 3 | README, 架构, 路线图 |
| OpenHydra/XEdu | 5 | 集成方案、报告、设计 |
| 测试报告 | 2 | Vircadia相关 |
| 其他技术文档 | 见documentation/ | 详细技术实现 |

---

*本文档由自动化脚本生成，最后更新于 2026-04-28*
"""

    index_path = PROJECT_ROOT / "reports" / "DOCUMENT_INDEX.md"
    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"✅ 已创建文档索引: {index_path}")
        return True
    except Exception as e:
        print(f"❌ 创建索引失败: {e}")
        return False

def update_readme_references():
    """更新README中的文档引用"""
    print("\n" + "=" * 80)
    print("步骤 4: 检查README文档引用")
    print("=" * 80)

    readme_path = PROJECT_ROOT / "README.md"
    if not readme_path.exists():
        print("⚠️  README.md 不存在")
        return False

    print("✅ README.md 存在，建议手动检查以下引用:")
    print("   - OPENHYDRA_XEDU_INTEGRATION_PLAN.md (保留在根目录)")
    print("   - GLOBAL_TECHNICAL_ARCHITECTURE.md (保留在根目录)")
    print("   - PROJECT_ROADMAP.md (保留在根目录)")
    print("   - SECURITY.md (保留在根目录)")
    print("\n   这些核心文档保持在根目录便于访问，无需移动。")
    return True

def generate_cleanup_report(deleted, moved):
    """生成清理报告"""
    print("\n" + "=" * 80)
    print("清理完成报告")
    print("=" * 80)

    report = f"""
## MD文档清理报告

**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 操作统计
- 删除过时文档: {deleted} 个
- 移动文档: {moved} 个
- 创建索引: 1 个

### 保留的核心文档（根目录）
- README.md - 项目主文档
- GLOBAL_TECHNICAL_ARCHITECTURE.md - 全局技术架构
- PROJECT_ROADMAP.md - 项目路线图
- SECURITY.md - 安全政策
- OPENHYDRA_XEDU_INTEGRATION_PLAN.md - OpenHydra集成方案

### 新增文档
- reports/DOCUMENT_INDEX.md - 统一文档索引

### 下一步建议
1. 检查 application/logs/ 等目录中的临时MD文件
2. 审查 docs/ 目录，合并重复的技术文档
3. 更新项目Wiki或在线文档中心
4. 定期运行此脚本保持文档整洁

---
*报告由 cleanup_md_docs.py 自动生成*
"""

    report_path = PROJECT_ROOT / "reports" / "CLEANUP_REPORT_20260428.md"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 清理报告已保存: {report_path}")
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("iMato 项目 MD 文档清理工具")
    print("=" * 80 + "\n")

    # 确认操作
    print("⚠️  警告: 此操作将删除和移动文件，请确认继续？")
    print("   按 Enter 继续，或按 Ctrl+C 取消...\n")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        return

    # 执行清理步骤
    deleted = delete_obsolete_docs()
    moved = move_docs()
    create_doc_index()
    update_readme_references()
    generate_cleanup_report(deleted, moved)

    print("\n" + "=" * 80)
    print("✅ 文档清理完成！")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

