"""
修复 multimedia_routes.py 的编码损坏问题
"""

import re

file_path = "backend/routes/multimedia_routes.py"

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换损坏的字符串（包括各种变体）
replacements = {
    '筛？': '筛选',
    '详？': '详情',
    '失？': '失败',
    '错？': '错误',
    '误？': '错误',
    '存？)': '存在")',
    '信？)': '信息")',
    '格？)': '格式")',
    '败":': '失败":',
}

for damaged, correct in replacements.items():
    content = content.replace(damaged, correct)

# 修复可能的换行符问题
content = content.replace('"\n)', '")\n')

# 替换 Unicode 替换字符 (\ufffd) - 这通常表示编码损坏
# 先找到所有包含 \ufffd 的行并尝试修复
lines = content.split('\n')
for i, line in enumerate(lines):
    if '\ufffd' in line:
        # 尝试根据上下文修复
        if '资源不' in line:
            lines[i] = line.replace('\ufffd', '在")')
        elif '列表失' in line:
            lines[i] = line.replace('\ufffd', '败")')
        elif '文档格' in line:
            lines[i] = line.replace('\ufffd', '式")')
        elif '统计信' in line:
            lines[i] = line.replace('\ufffd', '息")')
        elif '详' in line and '情' not in line:
            lines[i] = line.replace('\ufffd', '情")')
        
content = '\n'.join(lines)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 文件已修复")
