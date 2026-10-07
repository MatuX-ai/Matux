# -*- coding: utf-8 -*-
"""验证 dist 中 3 个 P1 修复的代码命中情况"""
import os, glob

dist_dir = r'I:\iMato\dist\imatuproject'
chunks = glob.glob(os.path.join(dist_dir, '*.js'))

# 1. ai-edu-dashboard: 找包含 runOutsideAngular + applyModulesFallback + fallbackTimer
ai_edu_chunk = None
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'applyModulesFallback' in content and 'fallbackTimer' in content and 'runOutsideAngular' in content:
            ai_edu_chunk = (c, len(content))
            break
    except Exception as e:
        pass

print(f"[BUG02 ai-edu-dashboard] {'PASS' if ai_edu_chunk else 'FAIL'} {ai_edu_chunk}")

# 2. NgxEchartsModule: 找包含 echarts() 动态 import + forRoot 配对
echarts_chunk = None
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'ngx-echarts' in content.lower() or ('echarts' in content and 'forRoot' in content):
            echarts_chunk = (c, len(content))
            break
    except Exception as e:
        pass

print(f"[BUG01 NgxEchartsModule] {'PASS' if echarts_chunk else 'FAIL'} {echarts_chunk}")

# 3. ModuleActiveGuard: 找包含 "后端不可达" 字符串（中文 minify 后保留）
guard_chunk = None
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if '\u540e\u7aef\u4e0d\u53ef\u8fbe' in content and 'ModuleActiveGuard' in content:
            guard_chunk = (c, len(content))
            break
    except Exception as e:
        pass

# 也尝试更宽泛的搜索
if not guard_chunk:
    for c in chunks:
        try:
            with open(c, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if '\u540e\u7aef\u4e0d\u53ef\u8fbe\uff0c\u4ee5\u964d\u7ea7\u6a21\u5f0f\u8bbf\u95ee' in content:
                guard_chunk = (c, len(content), 'partial')
                break
        except Exception as e:
            pass

print(f"[BUG03 ModuleActiveGuard] {'PASS' if guard_chunk else 'FAIL'} {guard_chunk}")

# 4. 总览
total_size = sum(os.path.getsize(c) for c in chunks)
print(f"\nTotal chunks: {len(chunks)}, total size: {total_size} bytes")
print(f"dist timestamp: {os.path.getmtime(os.path.join(dist_dir, 'index.html'))}")
