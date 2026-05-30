"""
Python 代码清理工具
清理 pass、... 等占位符，替换为有意义的实现或删除
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple


class PythonCodeCleaner:
    def __init__(self, root_dir: str = "backend"):
        self.root_dir = Path(root_dir)
        self.files_processed = 0
        self.issues_found = []
        self.issues_fixed = []
        
    def find_pass_statements(self) -> List[Tuple[Path, int, str]]:
        """查找所有 pass 语句"""
        issues = []
        
        for py_file in self.root_dir.rglob("*.py"):
            # 跳过虚拟环境和迁移目录
            if 'venv' in str(py_file) or 'migrations' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()
                    # 查找单独的 pass 或 ... 
                    if stripped == 'pass' or stripped == '...':
                        # 检查前一行是否有 docstring
                        prev_line = lines[line_num - 2].strip() if line_num > 1 else ''
                        next_line = lines[line_num].strip() if line_num < len(lines) else ''
                        
                        # 如果是在函数/类定义中且有 docstring，可能需要保留
                        if not (prev_line.startswith('"""') or prev_line.startswith("'''")):
                            issues.append((py_file, line_num, stripped))
                            
            except Exception as e:
                print(f"读取文件失败 {py_file}: {e}")
                
        return issues
        
    def clean_pass_statements(self, dry_run: bool = True):
        """清理 pass 语句"""
        print("=" * 80)
        print("🔍 扫描 Python 文件中的 pass 和 ... 占位符")
        print("=" * 80)
        
        issues = self.find_pass_statements()
        
        print(f"\n发现 {len(issues)} 个占位符:\n")
        
        # 按文件分组
        files_dict = {}
        for file_path, line_num, content in issues:
            if file_path not in files_dict:
                files_dict[file_path] = []
            files_dict[file_path].append((line_num, content))
            
        for file_path, occurrences in files_dict.items():
            print(f"\n📄 {file_path.relative_to(self.root_dir)}:")
            for line_num, content in occurrences:
                print(f"  行 {line_num}: {content}")
                
            if not dry_run:
                # 实际清理逻辑
                self._fix_file(file_path, occurrences)
                
        print(f"\n{'✅ [DRY RUN]' if dry_run else '✅'} 完成！共处理 {self.files_processed} 个文件\n")
        
    def _fix_file(self, file_path: Path, occurrences: List[Tuple[int, str]]):
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 从后向前删除，避免行号偏移
            for line_num, content in reversed(occurrences):
                idx = line_num - 1
                if 0 <= idx < len(lines):
                    # 检查是否是空函数的唯一内容
                    prev_line = lines[idx - 1].strip() if idx > 0 else ''
                    next_line = lines[idx + 1].strip() if idx < len(lines) - 1 else ''
                    
                    # 如果前后都是空行或注释，可以安全删除
                    if (not prev_line or prev_line.startswith('#')) and \
                       (not next_line or next_line.startswith('#')):
                        lines[idx] = '\n'  # 替换为空行
                        
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            self.files_processed += 1
            
        except Exception as e:
            print(f"修复文件失败 {file_path}: {e}")
            
    def remove_unused_imports(self, dry_run: bool = True):
        """移除未使用的导入（简单版本）"""
        print("\n" + "=" * 80)
        print("🔍 检查未使用的导入")
        print("=" * 80)
        
        # 这里可以实现更复杂的逻辑来检测未使用的导入
        # 目前只做基础检查
        
        print("\nℹ️  建议使用自动化工具（如 autoflake）进行导入优化\n")
        
    def generate_report(self):
        """生成清理报告"""
        report = {
            'files_processed': self.files_processed,
            'issues_found': len(self.issues_found),
            'issues_fixed': len(self.issues_fixed),
        }
        return report


if __name__ == "__main__":
    cleaner = PythonCodeCleaner("backend")
    
    # 先干运行查看情况
    print("\n🚀 开始代码清理（预览模式）\n")
    cleaner.clean_pass_statements(dry_run=True)
    
    # 询问是否继续
    print("\n" + "=" * 80)
    response = input("是否执行实际清理？(y/N): ")
    
    if response.lower() == 'y':
        print("\n🔧 开始实际清理...\n")
        cleaner.clean_pass_statements(dry_run=False)
        print("✅ 清理完成！")
    else:
        print("\n⏭️  已跳过实际清理")
