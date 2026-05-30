#!/usr/bin/env python3
"""
SCSS 文件编码修复工具
批量修复 SCSS 文件中的中文乱码问题
"""

import os
import re
from pathlib import Path

# 常见乱码模式映射（需要根据实际情况调整）
FIX_PATTERNS = {
    # 这些是实际文件中的乱码，需要替换为正确的中文
    r'鐎电厧鍙？': '导入',
    r'閸╄櫣顢？': '定义',
    r'閺嗘绮︽稉濠氼暯': '暗黑主题',
    r'閸旀垵绨？': '布局',
    r'閻╂帗膩閸ㄥ鍣哥纯？': '盒模型重置',
    r'娑撴槒鍎楅弲顖濆': '主背景色',
    r'闁插秶鐤？': '排版重置',
    r'闁猴拷': '样式',
    r'\[39m': '',  # ANSI 转义码残留
}

def fix_file(file_path: Path) -> bool:
    """修复单个文件的编码问题"""
    try:
        # 尝试不同的编码读取
        content = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'cp936']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if not content:
            print(f"❌ {file_path.name} - 无法读取文件")
            return False

        # 应用所有修复模式
        modified = False
        for pattern, replacement in FIX_PATTERNS.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True

        # 如果内容有修改，保存文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path.name}")
            return True
        else:
            print(f"✓ {file_path.name} (无需修复)")
            return True

    except Exception as e:
        print(f"❌ {file_path.name} - {str(e)}")
        return False

def main():
    # 设置控制台编码为 UTF-8
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n🔧 SCSS File Encoding Fix Tool")
    print("=" * 50 + "\n")

    # 查找所有 SCSS 文件（包括 src 目录下所有子目录）
    scss_files = list(Path("src").rglob("*.scss"))
    if not scss_files:
        print(f"❌ 未找到 SCSS 文件")
        return

    print(f"📂 找到 {len(scss_files)} 个 SCSS 文件\n")

    fixed_count = 0
    total_count = len(scss_files)

    for file_path in scss_files:
        if fix_file(file_path):
            fixed_count += 1

    print(f"\n{'=' * 50}")
    print(f"✅ 完成！修复了 {fixed_count}/{total_count} 个文件")
    print(f"{'=' * 50}\n")

if __name__ == "__main__":
    main()
