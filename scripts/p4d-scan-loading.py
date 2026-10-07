#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-D 扫查：找出 user/ 下所有可能在数据加载失败时陷入无限 loading 的组件。
   检查模式：
   - isLoading = true 但没有错误处理路径（无 loadError / catch）
   - HTTP 订阅只有 next 没有 error
   - 没有 timeout / retry 限制
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path("I:/iMato/src/app/user")
COMPONENTS = list(ROOT.rglob("*.component.ts"))

def scan_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")

    findings = []

    # 1. isLoading / loading 字段
    loading_vars = re.findall(r"(?:this\.)?(\b\w*[Ll]oading\w*\b)\s*=\s*true", text)
    if loading_vars:
        findings.append(f"loading vars set true: {set(loading_vars)}")

    # 2. 查找 .subscribe({...}) 检查是否有 error 处理
    subscribes = list(re.finditer(r"\.subscribe\s*\(\s*\{", text))
    for m in subscribes:
        start = m.end()
        # 简单括号匹配
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        block = text[start:i]
        if "error" not in block and "catchError" not in block:
            # 找上下 100 字看看是哪个调用
            ctx_start = max(0, m.start() - 200)
            ctx = text[ctx_start:start]
            # 找出是 http.get/post/etc
            call = re.search(r"this\.http\.(get|post|put|delete|patch|request)\s*\(", ctx)
            if call:
                findings.append(f"{m.start()}: http.{call.group(1)}() subscribe lacks error handler")

    # 3. fetch() 调用但没有 catch
    fetches = list(re.finditer(r"\bfetch\s*\(", text))
    for m in fetches:
        start = m.end()
        # 看是否有 .catch
        tail = text[start:start + 500]
        if ".catch(" not in tail:
            findings.append(f"{m.start()}: fetch() lacks .catch")

    # 4. interval() 调用但没有 takeUntil
    intervals = list(re.finditer(r"\binterval\s*\(", text))
    for m in intervals:
        start = m.end()
        # 看附近 500 字是否有 takeUntil
        ctx_start = max(0, m.start() - 200)
        ctx = text[ctx_start:start + 100]
        if "takeUntil" not in ctx:
            findings.append(f"{m.start()}: interval() without takeUntil - possible leak")

    # 5. 是否有 timeout/race/retry
    has_timeout = "timeout" in text.lower()
    has_retry = "retry" in text.lower()
    if loading_vars and not has_timeout and not has_retry:
        findings.append(f"loading vars without any timeout/retry strategy")

    return findings

def main():
    print(f"扫描 {len(COMPONENTS)} 个组件文件\n")
    total_findings = 0
    for c in sorted(COMPONENTS):
        findings = scan_file(c)
        if findings:
            rel = c.relative_to(ROOT.parent.parent)
            print(f"=== {rel} ===")
            for f in findings:
                print(f"  ⚠ {f}")
            print()
            total_findings += len(findings)

    print(f"\n=== 总计 {total_findings} 条 findings ===")

if __name__ == "__main__":
    main()
