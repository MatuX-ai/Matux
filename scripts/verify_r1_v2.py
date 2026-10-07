# -*- coding: utf-8 -*-
"""验证 R-01 修复在 dist 中的代码命中"""
import glob

dist_dir = r'I:\iMato\dist\imatuproject'
chunks = glob.glob(f'{dist_dir}/*.js')

# R-01: backendAvailable + BACKEND_PROBE_TIMEOUT_MS + http.get('health-detail')
r1_matches = []
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'backendAvailable' in content and 'health-detail' in content:
            r1_matches.append((c, len(content)))
    except:
        pass

print(f'[R-01 growth-trajectory 候选 chunks] {len(r1_matches)}')
for c, n in r1_matches:
    with open(c, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print(f'\n[{c}] [{n}b]')
    print(f'  backendAvailable: {content.count("backendAvailable")}')
    print(f'  health-detail: {content.count("health-detail")}')
    print(f'  演示数据: {content.count("\u6f14\u793a\u6570\u636e")}')
    print(f'  cloud_off: {content.count("cloud_off")}')
    # 取 backendAvailable 上下文
    idx = content.find('backendAvailable')
    if idx >= 0:
        print(f'  context: {content[max(0,idx-80):idx+200]}')
