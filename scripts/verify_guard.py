# -*- coding: utf-8 -*-
import os, glob

dist_dir = r'I:\iMato\dist\imatuproject'
chunks = glob.glob(os.path.join(dist_dir, '*.js'))

# 1. 找含 ModuleActiveGuard 的所有 chunk
guard_chunks = []
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'ModuleActiveGuard' in content:
            guard_chunks.append((c, len(content)))
    except:
        pass

print(f"[ModuleActiveGuard 出现 chunks] {len(guard_chunks)} 个")
for c, n in guard_chunks:
    print(f"  {c} [{n}b]")

# 2. 找含 showFailedMessage 的 chunk
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'showFailedMessage' in content:
            # 检查邻近字符串
            idx = content.find('showFailedMessage')
            nearby = content[idx:idx+1500]
            print(f"\n[{os.path.basename(c)}] showFailedMessage 上下文:")
            print(nearby[:600])
            break
    except:
        pass

# 3. 检查 ModuleActiveGuard 全部字符串
all_msg = set()
for c in chunks:
    try:
        with open(c, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'ModuleActiveGuard' in content:
            # 提取中文字符串
            import re
            msgs = re.findall(r'[\u4e00-\u9fff][\u4e00-\u9fff\u3000-\u303f\uff00-\uffef，。：；！？、·\(\)（）]{2,30}', content)
            all_msg.update(msgs)
    except:
        pass

print(f"\n[Guard 相关中文短语样例]")
samples = [m for m in all_msg if any(k in m for k in ['功能', '不可达', '降级', '重试', '启动', '不可', '等待', '激活'])]
for s in sorted(samples)[:20]:
    print(f"  {s}")
