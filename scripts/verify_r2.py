# -*- coding: utf-8 -*-
"""验证 R-02 修复 — 检查 cloud_off + 后端不可达"""
import os, glob

dist_dir = r'I:\iMato\dist\imatuproject'
chunks = glob.glob(os.path.join(dist_dir, '*.js'))

# R-02 宽松匹配
r2_chunks = []
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'cloud_off' in content and '\u540e\u7aef\u4e0d\u53ef\u8fbe' in content and 'refresh' in content:
            r2_chunks.append((c, len(content)))
    except:
        pass

print(f"[R-02 ai-edu 候选 chunks] {len(r2_chunks)}")
for c, n in r2_chunks:
    print(f"  {c} [{n}b]")

# 也确认模板中 .fallback-banner-top 在 ai-edu chunk
for c, n in r2_chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # 检查 cloud_off + fallback-banner-top 一起
        if 'cloud_off' in content and 'fallback-banner-top' in content:
            print(f"  [{os.path.basename(c)}] 同时包含 cloud_off + fallback-banner-top: PASS")
        elif 'cloud_off' in content:
            print(f"  [{os.path.basename(c)}] 含 cloud_off 但 fallback-banner-top 被 minify 了,需进一步检查")
    except:
        pass
