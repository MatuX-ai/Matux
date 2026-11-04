#!/usr/bin/env python
"""flake8 baseline 闸门。

把仓库既有的 lint 债务冻结在 baseline 文件里，只对「新增」的 lint 错误失败。
这样既能摘掉 CI 里的 `|| true`，又不会要求一次性清零全部历史问题。

用法：
    python scripts/flake8_baseline.py            # 校验模式：有新增 lint 则退出码 1
    python scripts/flake8_baseline.py --update   # 按当前工作区重新生成 baseline

baseline 文件：config/lint-baseline.txt
格式：每行 `<相对路径>:<错误码>:<该组合允许的条数>`

为什么用「路径 + 错误码 + 条数」而不是行号：
    行号会因任何无关的代码插入而整体位移，用行号做键会让一次无害改动
    误报几十条。按 (路径, 错误码) 计数则只关心同一类问题的数量是否增长，
    与代码位置无关。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = ROOT / "config" / "lint-baseline.txt"
DEFAULT_TARGET = "backend"

# 机器可读格式：路径|行|列|码|说明
FMT = "%(path)s|%(row)d|%(col)d|%(code)s|%(text)s"

HEADER = """\
# flake8 baseline —— 冻结既有 lint 债务
#
# 本文件由 `python scripts/flake8_baseline.py --update` 生成，请勿手工编辑。
# 每行格式：<相对路径>:<错误码>:<允许条数>
#
# 判定规则：同一个「路径 + 错误码」在当前代码中的条数超过本文件记录的条数，
# 即视为新增 lint 错误，CI 会失败。条数减少（问题被修复）不会失败，
# 但会在日志中提示可以收紧 baseline。
#
# 收紧基线时请一并清理对应问题，不要为了「刷绿」直接调高条数。
"""


def run_flake8(target: str) -> tuple[Counter, list[tuple[str, int, int, str, str]]]:
    """跑 flake8，返回 (path, code) 计数与明细列表。"""
    cmd = [sys.executable, "-m", "flake8", target, f"--format={FMT}"]
    proc = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    # flake8 退出码：0=无问题，1=有问题；其余值说明工具自身异常
    if proc.returncode not in (0, 1):
        sys.stderr.write(proc.stderr or "")
        raise SystemExit(f"flake8 执行异常，退出码 {proc.returncode}")

    counter: Counter = Counter()
    details: list[tuple[str, int, int, str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 5:
            continue
        path, row, col, code, text = parts
        # Windows 下 flake8 输出反斜杠，统一成 POSIX 风格，保证跨平台一致
        path = path.replace("\\", "/")
        counter[(path, code)] += 1
        details.append((path, int(row), int(col), code, text.strip()))
    return counter, details


def read_baseline() -> Counter:
    """读取 baseline 文件，返回 (path, code) 计数。"""
    counter: Counter = Counter()
    if not BASELINE_FILE.exists():
        return counter
    for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        path, code, count = line.rsplit(":", 2)
        counter[(path, code)] = int(count)
    return counter


def write_baseline(counter: Counter) -> None:
    """按当前计数写出 baseline 文件。"""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER.rstrip("\n")]
    for (path, code), count in sorted(counter.items()):
        lines.append(f"{path}:{code}:{count}")
    BASELINE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="flake8 baseline 闸门")
    parser.add_argument(
        "--update",
        action="store_true",
        help="按当前工作区状态重新生成 baseline 文件",
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help=f"flake8 扫描目标（默认 {DEFAULT_TARGET}）",
    )
    args = parser.parse_args()

    os.chdir(ROOT)
    current, details = run_flake8(args.target)

    if args.update:
        write_baseline(current)
        rel = BASELINE_FILE.relative_to(ROOT)
        print(
            f"baseline 已更新：{rel}"
            f"（{len(current)} 个「路径+错误码」组合，共 {sum(current.values())} 条）"
        )
        return 0

    baseline = read_baseline()

    # 按 (路径, 错误码) 分组，把超出 baseline 条数的那几条判定为新增
    groups: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for path, row, col, code, text in details:
        groups[(path, code)].append((row, col, text))

    regressions: list[tuple[str, int, int, str, str]] = []
    for (path, code), items in groups.items():
        allowed = baseline.get((path, code), 0)
        if len(items) > allowed:
            items.sort()
            for row, col, text in items[allowed:]:
                regressions.append((path, row, col, code, text))

    resolved = baseline - current
    if resolved:
        print(
            f"提示：{sum(resolved.values())} 条 baseline 记录的问题已被修复，"
            f"可运行 `python scripts/flake8_baseline.py --update` 收紧基线。"
        )

    if regressions:
        print(f"检测到 {len(regressions)} 条新增 lint 错误（超出 baseline）：")
        for path, row, col, code, text in regressions:
            print(f"  {path}:{row}:{col}: {code} {text}")
        print()
        print("修复这些问题；若确属有意引入，同步更新 baseline：")
        print("  python scripts/flake8_baseline.py --update")
        return 1

    print(
        f"flake8 baseline 校验通过：当前 {sum(current.values())} 条，"
        f"无新增错误。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
