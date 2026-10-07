# -*- coding: utf-8 -*-
"""验证 dist 中 R-01/R-02 修复代码命中"""
import os, glob

dist_dir = r'I:\iMato\dist\imatuproject'
chunks = glob.glob(os.path.join(dist_dir, '*.js'))

# R-01: growth-trajectory page 应包含 backendAvailable + moduleStatusService + '演示数据'
r1_chunk = None
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'backendAvailable' in content and 'moduleStatusService' in content and ('\u6f14\u793a\u6570\u636e' in content or 'cloud_off' in content):
            r1_chunk = (c, len(content))
            break
    except:
        pass

print(f"[R-01 growth-trajectory] {'PASS' if r1_chunk else 'FAIL'} {r1_chunk}")

# R-02: ai-edu 应包含 fallback-banner-top + cloud_off + 顶部 banner
r2_chunk = None
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'fallback-banner-top' in content and '\u540e\u7aef\u4e0d\u53ef\u8fbe' in content:
            r2_chunk = (c, len(content))
            break
    except:
        pass

print(f"[R-02 ai-edu] {'PASS' if r2_chunk else 'FAIL'} {r2_chunk}")

# 总览
total_size = sum(os.path.getsize(c) for c in chunks)
print(f"\nTotal chunks: {len(chunks)}, total size: {total_size} bytes")
print(f"dist timestamp: {os.path.getmtime(os.path.join(dist_dir, 'index.html'))}")
