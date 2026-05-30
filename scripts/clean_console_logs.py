"""
清理 TypeScript 中的 console.log 和调试代码
"""

import os
import re
from pathlib import Path


class DebugCodeCleaner:
    def __init__(self, root_dir: str = "src/app"):
        self.root_dir = Path(root_dir)
        self.console_pattern = re.compile(
            r'^\s*console\.(log|warn|error|debug|info)\([^)]*\);?\s*$',
            re.MULTILINE
        )
        self.modified_files = []
        
    def scan_and_clean(self):
        """扫描并清理所有 TS 文件"""
        print("=" * 80)
        print("🔍 开始清理 console.log 和调试代码")
        print("=" * 80)
        
        ts_files = list(self.root_dir.rglob("*.ts"))
        print(f"\n📄 发现 {len(ts_files)} 个 TypeScript 文件")
        
        for ts_file in ts_files:
            try:
                self._process_file(ts_file)
            except Exception as e:
                print(f"  ⚠️  {ts_file}: {e}")
        
        print("\n" + "=" * 80)
        print(f"✅ 完成！共修改 {len(self.modified_files)} 个文件")
        print("=" * 80)
        
        if self.modified_files:
            print("\n修改的文件:")
            for file in self.modified_files[:20]:  # 显示前 20 个
                print(f"  - {file}")
            if len(self.modified_files) > 20:
                print(f"  ... 还有 {len(self.modified_files) - 20} 个文件")
    
    def _process_file(self, file_path: Path):
        """处理单个文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找 console 语句
        matches = list(self.console_pattern.finditer(content))
        
        if not matches:
            return
        
        # 移除 console 语句
        new_content = self.console_pattern.sub('', content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.modified_files.append(str(file_path))
        print(f"  ✅ {file_path.name}: 清理 {len(matches)} 处 console 语句")


def main():
    cleaner = DebugCodeCleaner()
    cleaner.scan_and_clean()


if __name__ == "__main__":
    main()
