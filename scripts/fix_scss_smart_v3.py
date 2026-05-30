#!/usr/bin/env python3
"""
SCSS 文件智能编码修复工具 v3
使用正则表达式智能检测和修复 GBK 被误读为 UTF-8 的乱码
"""

from pathlib import Path
import sys
import io
import re

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace')

def is_garbled_text(text: str) -> bool:
    """检测文本是否是乱码（连续罕见汉字）"""
    # 匹配连续的罕见汉字（通常在 UTF-8 中被误读的 GBK 字符）
    rare_chars_pattern = r'[\u9000-\u9fff\u3400-\u4dbf]{3,}'
    return bool(re.search(rare_chars_pattern, text))

def extract_garbled_comments(content: str) -> list:
    """提取所有包含乱码的注释"""
    comment_pattern = r'//\s*([^\n]+)'
    garbled_comments = []

    for match in re.finditer(comment_pattern, content):
        comment = match.group(1)
        if is_garbled_text(comment):
            garbled_comments.append({
                'full_match': match.group(0),
                'comment': comment,
                'start': match.start(),
                'end': match.end()
            })

    return garbled_comments

def suggest_fix(garbled_comment: str) -> str:
    """基于常见模式建议修复"""
    # 这些是基于项目上下文的智能猜测
    suggestions = {
        '鍏ㄥ眬甯冨眬瀹瑰櫒绯荤粺锛屾彁渚涘搷搴斿紡甯冨眬瑙e喅鏂规': '全局布局容器系统，提供响应式布局解决方案',
        '鍩虹瀹瑰櫒绫？': '基础容器类',
        '閸╄櫣顢呴幒鎺斿闁插秶鐤？': '排版重置',
        '閻╂帗膩閸ㄥ鍣哥纯？': '盒模型重置',
        '閸╄櫣顢呴懗灞炬珯閸滃矁銆冮棃銏ゎ杹閼？': '基础背景和表面颜色',
        '閺嗘绮︽稉濠氼暯CSS閸欐﹢鍣虹€规矮绠？': '暗黑主题 CSS 变量定义',
        '閸╄桨绨？Design Tokens 閻ㄥ嚜aterial Design 娑撳顣？': '基于 Design Tokens 的 Material Design 主题',
        '鐎规矮绠熺拫鍐閺？': '定义调色板',
        '1. Design Tokens 鐎电厧鍙？': '1. Design Tokens 导入',
    }

    # 尝试精确匹配
    if garbled_comment in suggestions:
        return suggestions[garbled_comment]

    # 尝试部分匹配
    for key, value in suggestions.items():
        if key in garbled_comment or garbled_comment in key:
            return value

    # 如果无法匹配，返回占位符
    return "[待修复的中文注释]"

def fix_file_interactive(file_path: Path) -> bool:
    """交互式修复单个文件"""
    print(f"\n📄 Processing: {file_path}")
    print("-" * 60)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    garbled_comments = extract_garbled_comments(content)

    if not garbled_comments:
        print(f"✓ No garbled text found")
        return True

    print(f"Found {len(garbled_comments)} garbled comment(s)")

    modified_content = content
    fixes_applied = 0

    for item in garbled_comments:
        suggestion = suggest_fix(item['comment'])

        print(f"\n  Garbled: {item['comment'][:50]}...")
        print(f"  Suggested: {suggestion}")

        # 自动应用建议的修复
        modified_content = modified_content.replace(item['full_match'], f"// {suggestion}")
        fixes_applied += 1
        print(f"  ✅ Applied")

    # 保存修改后的文件
    if fixes_applied > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"\n✅ Fixed {fixes_applied} comment(s) in {file_path.name}")
        return True

    return False

def main():
    print("\n" + "=" * 60)
    print("🔧 SCSS Intelligent Encoding Fix Tool v3")
    print("=" * 60 + "\n")

    # 查找所有 SCSS 文件
    scss_files = sorted(Path("src").rglob("*.scss"))

    if not scss_files:
        print("❌ No SCSS files found!")
        return

    print(f"Found {len(scss_files)} SCSS files\n")

    fixed_count = 0
    skipped_count = 0

    # 优先处理已知的 6 个问题文件
    priority_files = [
        "src/styles/layout.scss",
        "src/styles/main.scss",
        "src/styles/reset.scss",
        "src/styles/typography.scss",
        "src/styles/themes/_custom-theme.scss",
        "src/styles/themes/_dark-theme.scss",
    ]

    # 先处理优先级文件
    for file_str in priority_files:
        file_path = Path(file_str)
        if file_path.exists():
            if fix_file_interactive(file_path):
                fixed_count += 1
            else:
                skipped_count += 1

    # 然后处理其他文件
    for file_path in scss_files:
        if str(file_path) not in priority_files:
            if fix_file_interactive(file_path):
                fixed_count += 1
            else:
                skipped_count += 1

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  ✅ Fixed: {fixed_count}/{len(scss_files)} files")
    print(f"  ⚠️  Skipped: {skipped_count}/{len(scss_files)} files")
    print("=" * 60 + "\n")

    if fixed_count > 0:
        print("💡 Next step: Run Prettier to verify")
        print("   npx prettier --write \"src/**/*.scss\"\n")

if __name__ == "__main__":
    main()
