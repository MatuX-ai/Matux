#!/usr/bin/env python3
"""
SCSS 文件编码自动修复工具 v2
智能检测并修复乱码的中文注释
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 常见乱码字符映射（GBK/GB2312 被误读为 UTF-8）
COMMON_GARBAGE_PATTERNS = {
    # 基于实际文件内容推断的正确中文
    '鐎电厧鍙？': '导入',
    '閸╄櫣顢？': '定义',
    '閺嗘绮︽稉濠氼暯': '暗黑主题',
    '閸旀垵绨？': '布局',
    '閻╂帗膩閸ㄥ鍣哥纯？': '盒模型重置',
    '娑撴槒鍎楅弲顖濆': '主背景色',
    '闁插秶鐤？': '排版重置',
    '闁猴拷': '样式',
    '閸？': '',
    '[39m': '',  # ANSI 转义码残留

    # 其他可能的乱码
    '绠＄悊鍚庡彴鍏ㄥ眬鏍峰紡': '管理后台全局样式',
    '鍩虹鏂偣璁剧疆': '基础断点设置',
    '妫€娴嬪睆骞曞昂瀵告洿鏂颁富棰橀厤缃？': '检测屏幕尺寸更新主题配置',
}

def detect_encoding(file_path: Path) -> str:
    """检测文件实际编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # 尝试不同编码
    encodings_to_try = [
        ('utf-8', 'UTF-8'),
        ('gbk', 'GBK'),
        ('gb2312', 'GB2312'),
        ('cp936', 'CP936'),
        ('big5', 'Big5'),
    ]

    for encoding, name in encodings_to_try:
        try:
            decoded = raw_data.decode(encoding)
            # 如果包含常见中文字符，很可能是正确的
            if re.search(r'[\u4e00-\u9fff]', decoded):
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    return 'utf-8'  # 默认返回 UTF-8

def fix_garbled_text(content: str) -> Tuple[str, bool]:
    """修复乱码文本"""
    modified = False

    # 应用所有修复模式
    for garbage, correct in COMMON_GARBAGE_PATTERNS.items():
        if garbage in content:
            content = content.replace(garbage, correct)
            modified = True

    # 尝试智能检测和修复 GBK 被误读为 UTF-8 的情况
    # 这种乱码通常表现为连续的罕见汉字
    garbage_pattern = re.compile(r'[\u9000-\u9fff]{2,}')  # 连续罕见汉字
    matches = list(garbage_pattern.finditer(content))

    if matches:
        # 对于每个匹配的乱码，尝试找到对应的正确中文
        for match in reversed(matches):  # 反向遍历避免索引问题
            garbage_text = match.group()
            # 这里可以尝试更复杂的恢复逻辑，但简单起见先跳过
            # 实际项目中可以手动维护一个映射表
            pass

    return content, modified

def fix_file(file_path: Path, dry_run: bool = False) -> Dict:
    """
    修复单个文件

    Returns:
        dict: {'success': bool, 'modified': bool, 'message': str}
    """
    result = {'success': False, 'modified': False, 'message': ''}

    try:
        # 第一步：检测原始编码
        original_encoding = detect_encoding(file_path)

        # 第二步：用原始编码读取
        with open(file_path, 'r', encoding=original_encoding) as f:
            content = f.read()

        # 第三步：修复乱码
        fixed_content, was_modified = fix_garbled_text(content)

        if was_modified:
            if not dry_run:
                # 第四步：用 UTF-8 保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                result['modified'] = True
                result['message'] = f"已修复（原编码：{original_encoding}）"
            else:
                result['message'] = f"需要修复（原编码：{original_encoding}）"
        else:
            result['message'] = "无需修复"

        result['success'] = True

    except Exception as e:
        result['message'] = f"失败：{str(e)}"

    return result

def main():
    import sys
    import io
    # 设置标准输出为 UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')

    print("\nSCSS File Encoding Auto-Fix Tool v2")
    print("=" * 60 + "\n")

    # 查找所有 SCSS 文件
    scss_files = sorted(Path("src").rglob("*.scss"))

    if not scss_files:
        print("❌ No SCSS files found!")
        return

    print(f"📂 Found {len(scss_files)} SCSS files\n")

    # 检查是否有 --dry-run 参数
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")

    fixed_count = 0
    failed_count = 0
    unchanged_count = 0

    for file_path in scss_files:
        result = fix_file(file_path, dry_run=dry_run)

        if result['success']:
            if result['modified']:
                print(f"✅ {file_path.relative_to(Path.cwd())}")
                print(f"   {result['message']}")
                fixed_count += 1
            else:
                if '--verbose' in sys.argv or '-v' in sys.argv:
                    print(f"✓ {file_path.relative_to(Path.cwd())} ({result['message']})")
                unchanged_count += 1
        else:
            print(f"❌ {file_path.relative_to(Path.cwd())}")
            print(f"   {result['message']}")
            failed_count += 1

    print(f"\n{'=' * 60}")
    print(f"✅ Success: {fixed_count} files fixed")
    print(f"✓  Unchanged: {unchanged_count} files")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count}/{len(scss_files)} files")
    print(f"{'=' * 60}\n")

    if dry_run and fixed_count > 0:
        print("💡 Run without --dry-run to apply fixes\n")

if __name__ == "__main__":
    main()
