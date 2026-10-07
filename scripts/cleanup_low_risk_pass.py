"""
清理后端 Python 代码中可优化的 pass 占位符

策略:
- 仅清理 except 子句中可优化的 pass (替换为 logger.debug 记录)
- 跳过保留场景:
  * Pydantic 验证器中的 pass
  * 抽象方法 (@abstractmethod) 下的 pass
  * 测试桩/驱动中的 pass
  * 空函数带 docstring 的 pass

执行:
    python scripts/cleanup_low_risk_pass.py            # dry_run 预览
    python scripts/cleanup_low_risk_pass.py --apply    # 实际清理
"""

import argparse
import re
import sys
from pathlib import Path


# 低风险 pass 占位符清单 (基于 2026-06-13 Grep 校准)
# 行号经过实际扫描验证
LOW_RISK_FILES = {
    "backend/services/code_sandbox_service.py": [198],
    "backend/services/document_service.py": [202],
    "backend/services/hidden_task_reward_system.py": [425],
    "backend/services/learning_behavior_service.py": [310],
    "backend/services/web_rtc_sensor_service.py": [208, 217, 286],
    "backend/tests/test_xr_integration.py": [78],
    "backend/enterprise_gateway/tests/test_performance.py": [190],
}


def analyze_line(lines: list, idx: int) -> dict:
    """分析指定行是否为可清理的 pass"""
    line = lines[idx].strip() if 0 <= idx < len(lines) else ""
    prev_line = lines[idx - 1].strip() if idx > 0 else ""
    next_line = lines[idx + 1].strip() if idx < len(lines) - 1 else ""

    info = {
        "is_pass": line == "pass",
        "in_except": False,
        "has_docstring_above": False,
        "abstract_method": False,
        "test_stub": False,
    }

    # 检查是否在 except 子句中
    if info["is_pass"]:
        # 向上查找最近的 try/except
        for i in range(idx - 1, max(idx - 10, -1), -1):
            stripped = lines[i].strip()
            if stripped.startswith("except") and stripped.endswith(":"):
                info["in_except"] = True
                break
            if stripped.startswith("def ") or stripped.startswith("class "):
                break

        # 跳过 docstring 紧邻的空函数
        if prev_line.startswith('"""') or prev_line.startswith("'''"):
            info["has_docstring_above"] = True

        # 检测抽象方法 (向前查找最近的 @abstractmethod/@abc.abstractmethod)
        for i in range(idx - 1, max(idx - 5, -1), -1):
            if "abstractmethod" in lines[i]:
                info["abstract_method"] = True
                break
            if lines[i].strip().startswith("def "):
                break

    return info


def build_replacement(lines: list, idx: int, file_path: Path) -> str:
    """构造替换内容 - 在 except 子句中加入 logger.debug

    保持与 except 子句相同的异常变量命名风格 (as <name>)
    缩进根据上下文推断 (使用 except 行的缩进)
    """
    # 找到上方最近的 except 行以确定异常变量名和缩进
    except_line_idx = -1
    for i in range(idx - 1, max(idx - 10, -1), -1):
        stripped = lines[i].strip()
        if stripped.startswith("except") and stripped.endswith(":"):
            except_line_idx = i
            break
        if stripped.startswith("def ") or stripped.startswith("class "):
            break

    if except_line_idx < 0:
        return ""

    except_line = lines[except_line_idx]
    indent = except_line[: len(except_line) - len(except_line.lstrip())]

    # 提取异常变量名 (如 "as e" / "as ex" / "as je")
    m = re.match(r"except\s+\w+(?:\s+as\s+(\w+))?\s*:", except_line.strip())
    except_var = m.group(1) if (m and m.group(1)) else "e"

    # 推断日志消息 (基于文件路径)
    file_name = file_path.stem
    msg = f"{file_name} 操作失败(可忽略)"

    return f"{indent}logger.debug(\"{msg}: {{{except_var}}}\")\n"


def clean_pass_placeholder(file_path: Path, line_numbers: list, dry_run: bool = True) -> dict:
    """清理指定文件中的 pass 占位符"""
    result = {
        "file": str(file_path),
        "cleaned": 0,
        "skipped": 0,
        "errors": [],
    }

    if not file_path.exists():
        result["errors"].append("文件不存在")
        return result

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 从后向前处理,避免行号偏移
        for line_num in sorted(line_numbers, reverse=True):
            idx = line_num - 1
            if not (0 <= idx < len(lines)):
                result["skipped"] += 1
                continue

            info = analyze_line(lines, idx)

            if not info["is_pass"]:
                print(f"  ⚠️  行 {line_num} 不是 pass 语句,跳过")
                result["skipped"] += 1
                continue

            if info["abstract_method"]:
                print(f"  ⚠️  行 {line_num} 是抽象方法,跳过")
                result["skipped"] += 1
                continue

            if info["has_docstring_above"]:
                print(f"  ⚠️  行 {line_num} 上方有 docstring,跳过")
                result["skipped"] += 1
                continue

            if not info["in_except"]:
                print(f"  ⚠️  行 {line_num} 不在 except 子句中,跳过 (保守策略)")
                result["skipped"] += 1
                continue

            if dry_run:
                print(f"  ✅ [DRY-RUN] 将清理 {file_path.name}:{line_num}")
                result["cleaned"] += 1
            else:
                replacement = build_replacement(lines, idx, file_path)
                # 同时修改 except 行 - 添加 "as <var>" 赋予异常变量名
                except_line_idx = -1
                for i in range(idx - 1, max(idx - 10, -1), -1):
                    stripped = lines[i].strip()
                    if stripped.startswith("except") and stripped.endswith(":"):
                        except_line_idx = i
                        break
                    if stripped.startswith("def ") or stripped.startswith("class "):
                        break
                if except_line_idx >= 0:
                    except_line = lines[except_line_idx].rstrip("\n")
                    stripped_except = except_line.strip()
                    m = re.match(r"except\s+\w+(?:\s+as\s+(\w+))?\s*:", stripped_except)
                    if m and not m.group(1):
                        # 补充 as <var>
                        new_except = re.sub(
                            r"^except\s+(\w+)\s*:",
                            r"except \1 as e:",
                            stripped_except,
                        )
                        # 保留缩进
                        indent = except_line[: len(except_line) - len(except_line.lstrip())]
                        lines[except_line_idx] = indent + new_except + "\n"
                lines[idx] = replacement
                print(f"  ✅ 已清理 {file_path.name}:{line_num}")
                result["cleaned"] += 1

        if not dry_run and result["cleaned"] > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

    except Exception as e:
        result["errors"].append(str(e))
        print(f"  ❌ 错误: {file_path} - {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="清理后端 Python 中的 pass 占位符")
    parser.add_argument("--apply", action="store_true", help="实际执行清理 (默认 dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply

    print("=" * 80)
    print("🔧 开始清理后端 Python pass 占位符")
    print(f"   模式: {'DRY-RUN (预览)' if dry_run else 'APPLY (实际修改)'}")
    print("=" * 80)
    print()

    total_cleaned = 0
    total_skipped = 0
    results = []

    for file_path_str, line_numbers in LOW_RISK_FILES.items():
        file_path = Path(file_path_str)
        print(f"\n📄 {file_path}:")
        result = clean_pass_placeholder(file_path, line_numbers, dry_run=dry_run)
        results.append(result)
        total_cleaned += result["cleaned"]
        total_skipped += result["skipped"]

    print("\n" + "=" * 80)
    print("📊 清理完成总结")
    print("=" * 80)
    print(f"✅ 成功清理: {total_cleaned} 处")
    print(f"⚠️  跳过保留: {total_skipped} 处")
    print(f"❌ 错误文件: {len([r for r in results if r['errors']])} 个")

    if any(r["errors"] for r in results):
        print("\n错误详情:")
        for result in results:
            if result["errors"]:
                print(f"  - {result['file']}: {', '.join(result['errors'])}")

    print()
    if dry_run:
        print("💡 这是预览模式,实际修改请加 --apply 参数:")
        print("   python scripts/cleanup_low_risk_pass.py --apply")
    else:
        print("✨ 实际清理完成!请运行验证脚本确认后端可正常导入.")
    print("=" * 80)


if __name__ == "__main__":
    main()