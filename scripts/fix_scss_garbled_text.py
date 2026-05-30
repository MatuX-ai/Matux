#!/usr/bin/env python3
"""
SCSS 文件批量乱码修复工具
基于已知的乱码映射表自动修复 6 个文件
"""

from pathlib import Path
import sys
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')

# 定义需要修复的文件
FILES_TO_FIX = [
    "src/styles/layout.scss",
    "src/styles/main.scss",
    "src/styles/reset.scss",
    "src/styles/typography.scss",
    "src/styles/themes/_custom-theme.scss",
    "src/styles/themes/_dark-theme.scss",
]

# 定义乱码映射表（基于实际文件内容推断）
GARBAGE_MAP = {
    # layout.scss
    '鍏ㄥ眬甯冨眬瀹瑰櫒绯荤粺锛屾彁渚涘搷搴斿紡甯冨眬瑙e喅鏂规': '全局布局容器系统，提供响应式布局解决方案',
    '瀵煎叆 Design Tokens': '导入 Design Tokens',
    '鍩虹瀹瑰櫒绫？': '基础容器类',
    '鏍囧噯鍥哄畾瀹藉害瀹瑰櫒': '标准固定宽度容器',

    # main.scss
    '鐎电厧鍙？Design Tokens': '导入 Design Tokens',

    # reset.scss
    '閻╂帗膩閸ㄥ鍣哥纯？': '盒模型重置',

    # typography.scss
    '閸╄櫣顢呴幒鎺斿闁插秶鐤？': '排版重置',

    # _custom-theme.scss
    '閸╄桨绨？Design Tokens 閻ㄥ嚜aterial Design 娑撳顣？': '基于 Design Tokens 的 Material Design 主题',
    '鐎规矮绠熺拫鍐閺？': '定义调色板',

    # _dark-theme.scss
    '閺嗘绮︽稉濠氼暯CSS閸欐﹢鍣虹€规矮绠？': '暗黑主题 CSS 变量定义',
    '閸╄櫣顢呴懗灞炬珯閸滃矁銆冮棃銏ゎ杹閼？': '基础背景和表面颜色',
}

def fix_file(file_path: Path) -> bool:
    """修复单个文件，返回是否成功"""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        modified = False

        # 应用所有替换
        for garbage, correct in GARBAGE_MAP.items():
            if garbage in content:
                content = content.replace(garbage, correct)
                modified = True
                print(f"  ✓ Replaced: '{garbage[:20]}...' -> '{correct}'")

        # 如果有修改，保存文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"✓ No changes: {file_path}")
            return True

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🔧 SCSS Manual Encoding Fix Tool")
    print("=" * 60 + "\n")

    fixed_count = 0
    skipped_count = 0

    for file_str in FILES_TO_FIX:
        file_path = Path(file_str)
        if fix_file(file_path):
            fixed_count += 1
        else:
            skipped_count += 1

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  ✅ Fixed: {fixed_count}/{len(FILES_TO_FIX)} files")
    print(f"  ⚠️  Skipped: {skipped_count}/{len(FILES_TO_FIX)} files")
    print("=" * 60 + "\n")

    if fixed_count > 0:
        print("💡 Next step: Run Prettier to verify")
        print("   npx prettier --write \"src/**/*.scss\"\n")

if __name__ == "__main__":
    main()
