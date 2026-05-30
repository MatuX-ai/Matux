"""
代码格式化工具 - Black (Python) + Prettier (JS/TS)
支持预览模式和实际执行模式
"""

import subprocess
import sys
from pathlib import Path


class CodeFormatter:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.python_files = []
        self.js_files = []
        self.ts_files = []
        
    def scan_files(self):
        """扫描需要格式化的文件"""
        print("=" * 80)
        print("🔍 扫描需要格式化的文件")
        print("=" * 80)
        
        # Python 文件（排除虚拟环境和迁移目录）
        print("\n📄 扫描 Python 文件...")
        for py_file in self.root_dir.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            self.python_files.append(py_file)
        print(f"  ✅ 发现 {len(self.python_files)} 个 Python 文件")
        
        # JavaScript/TypeScript 文件（排除 node_modules）
        print("\n📄 扫描 JavaScript/TypeScript 文件...")
        for js_file in self.root_dir.rglob("*.js"):
            if self._should_skip(js_file):
                continue
            self.js_files.append(js_file)
            
        for ts_file in self.root_dir.rglob("*.ts"):
            if self._should_skip(ts_file):
                continue
            self.ts_files.append(ts_file)
            
        print(f"  ✅ 发现 {len(self.js_files)} 个 JS 文件，{len(self.ts_files)} 个 TS 文件")
        
    def _should_skip(self, file_path: Path) -> bool:
        """判断是否应该跳过该文件"""
        skip_patterns = [
            'venv', '__pycache__', 'node_modules', 
            'build', 'dist', '.git', 'flutter_old',
            'migrations', 'third_party'
        ]
        
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in skip_patterns)
    
    def format_python_with_black(self, dry_run: bool = True):
        """使用 Black 格式化 Python 文件"""
        if not self.python_files:
            print("\n⚠️  没有 Python 文件需要格式化")
            return
            
        print("\n" + "=" * 80)
        mode = "👁️  预览模式 (Black)" if dry_run else "🔧 执行格式化 (Black)"
        print(f"{mode}")
        print("=" * 80)
        
        # 构建 Black 命令
        cmd = ["black", "--check" if dry_run else ""]
        
        # 添加文件列表
        files_to_format = [str(f) for f in self.python_files[:20]]  # 限制前 20 个作为示例
        
        if not files_to_format:
            print("\n✅ 所有 Python 文件都已格式化！")
            return
            
        print(f"\n示例文件 ({len(files_to_format)}/{len(self.python_files)}):")
        for f in files_to_format[:5]:
            print(f"  - {f}")
            
        if len(files_to_format) > 5:
            print(f"  ... 还有 {len(files_to_format) - 5} 个文件")
            
        # 执行命令
        try:
            result = subprocess.run(
                ["black", "--check", "--diff"] + files_to_format,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("\n✅ 所有 Python 文件已符合 Black 规范！")
            else:
                print("\n⚠️  以下文件需要格式化:")
                print(result.stdout)
                if result.stderr:
                    print("错误信息:", result.stderr)
                    
        except FileNotFoundError:
            print("\n❌ Black 未安装！请先运行：pip install black")
        except subprocess.TimeoutExpired:
            print("\n⏱️  格式化超时，建议分批执行")
        except Exception as e:
            print(f"\n❌ 格式化失败：{e}")
    
    def format_js_ts_with_prettier(self, dry_run: bool = True):
        """使用 Prettier 格式化 JS/TS 文件"""
        js_ts_files = self.js_files + self.ts_files
        
        if not js_ts_files:
            print("\n⚠️  没有 JS/TS 文件需要格式化")
            return
            
        print("\n" + "=" * 80)
        mode = "👁️  预览模式 (Prettier)" if dry_run else "🔧 执行格式化 (Prettier)"
        print(f"{mode}")
        print("=" * 80)
        
        # 限制示例文件数量
        files_to_format = [str(f) for f in js_ts_files[:20]]
        
        print(f"\n示例文件 ({len(files_to_format)}/{len(js_ts_files)}):")
        for f in files_to_format[:5]:
            print(f"  - {f}")
            
        if len(files_to_format) > 5:
            print(f"  ... 还有 {len(files_to_format) - 5} 个文件")
            
        # 执行命令
        try:
            # 检查 prettier 是否可用
            result = subprocess.run(
                ["npx", "prettier", "--check"] + (["--write"] if not dry_run else []),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.root_dir)
            )
            
            if result.returncode == 0:
                print("\n✅ 所有 JS/TS 文件已符合 Prettier 规范！")
            else:
                print("\n⚠️  以下文件需要格式化:")
                print(result.stdout[:500] if result.stdout else "查看上方输出")
                
        except FileNotFoundError:
            print("\n❌ Prettier 未安装！请先运行：npm install -D prettier")
            print("   或全局安装：npm install -g prettier")
        except subprocess.TimeoutExpired:
            print("\n⏱️  格式化超时，建议分批执行")
        except Exception as e:
            print(f"\n❌ 格式化失败：{e}")
    
    def generate_report(self):
        """生成格式化报告"""
        print("\n" + "=" * 80)
        print("📊 格式化统计报告")
        print("=" * 80)
        
        total_files = len(self.python_files) + len(self.js_files) + len(self.ts_files)
        
        print(f"\n总文件数：{total_files}")
        print(f"  - Python: {len(self.python_files)}")
        print(f"  - JavaScript: {len(self.js_files)}")
        print(f"  - TypeScript: {len(self.ts_files)}")
        
        print("\n推荐执行顺序:")
        print("  1. 先格式化 Python 文件 (Black)")
        print("  2. 再格式化 JS/TS 文件 (Prettier)")
        print("  3. 提交到 Git")


def main():
    formatter = CodeFormatter(".")
    
    # 扫描文件
    formatter.scan_files()
    
    # 询问执行模式
    print("\n" + "=" * 80)
    print("请选择执行模式:")
    print("  A. 仅预览（查看哪些文件需要格式化）")
    print("  B. 执行 Python 格式化 (Black)")
    print("  C. 执行 JS/TS 格式化 (Prettier)")
    print("  D. 全部执行")
    print("  X. 退出")
    
    choice = input("\n你的选择 (A/B/C/D/X): ").strip().upper()
    
    if choice == 'A':
        formatter.format_python_with_black(dry_run=True)
        formatter.format_js_ts_with_prettier(dry_run=True)
    elif choice == 'B':
        print("\n确认要执行 Python 格式化吗？(y/N): ", end="")
        confirm = input().strip().lower()
        if confirm == 'y':
            formatter.format_python_with_black(dry_run=False)
        else:
            formatter.format_python_with_black(dry_run=True)
    elif choice == 'C':
        print("\n确认要执行 JS/TS 格式化吗？(y/N): ", end="")
        confirm = input().strip().lower()
        if confirm == 'y':
            formatter.format_js_ts_with_prettier(dry_run=False)
        else:
            formatter.format_js_ts_with_prettier(dry_run=True)
    elif choice == 'D':
        print("\n⚠️  这将格式化所有文件，确定吗？(y/N): ", end="")
        confirm = input().strip().lower()
        if confirm == 'y':
            formatter.format_python_with_black(dry_run=False)
            formatter.format_js_ts_with_prettier(dry_run=False)
        else:
            print("⏭️  跳过执行")
    else:
        print("\n⏭️  已退出")
        return
    
    # 生成报告
    formatter.generate_report()


if __name__ == "__main__":
    main()
