#!/usr/bin/env python3
"""
SCSS 文件编码批量转换工具
将 GBK/GB2312 编码的文件转换为 UTF-8
"""

from pathlib import Path
import sys
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')

def convert_file(file_path: Path) -> bool:
    """
    尝试将文件从 GBK 转换为 UTF-8

    Returns:
        bool: 是否成功转换
    """
    try:
        # 用 GBK 读取
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()

        # 检查是否包含中文
        if not any('\u4e00' <= c <= '\u9fff' for c in content):
            return False

        # 用 UTF-8 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except UnicodeDecodeError:
        # 不是 GBK 编码
        return False
    except Exception as e:
        print(f"Error converting {file_path}: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("SCSS File Encoding Batch Converter")
    print("=" * 60 + "\n")

    # 查找所有 SCSS 文件
    scss_files = sorted(Path("src").rglob("*.scss"))

    if not scss_files:
        print("No SCSS files found!")
        return

    print(f"Found {len(scss_files)} SCSS files\n")

    converted_count = 0
    failed_count = 0
    skipped_count = 0

    for file_path in scss_files:
        try:
            if convert_file(file_path):
                print(f"[OK] Converted: {file_path.relative_to(Path.cwd())}")
                converted_count += 1
            else:
                print(f"[SKIP] Already UTF-8 or no Chinese: {file_path.name}")
                skipped_count += 1
        except Exception as e:
            print(f"[FAIL] {file_path.name}: {str(e)}")
            failed_count += 1

    print(f"\n{'=' * 60}")
    print(f"Converted: {converted_count} files")
    print(f"Skipped: {skipped_count} files")
    if failed_count > 0:
        print(f"Failed: {failed_count} files")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    main()
