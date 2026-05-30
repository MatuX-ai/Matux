#!/usr/bin/env python3
"""
项目大体积目录检测工具
识别并清理旧代码目录以优化磁盘空间
"""

import os
from pathlib import Path
from typing import Dict, List


class DirectorySizeAnalyzer:
    """目录大小分析器"""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.dir_sizes: Dict[str, int] = {}

    def get_dir_size(self, path: Path) -> int:
        """获取目录总大小 (字节)"""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total

    def analyze(self, top_n: int = 15) -> List[tuple]:
        """分析前 N 个最大的目录"""
        print(f"🔍 正在分析项目目录：{self.root}...")

        # 扫描所有一级子目录
        dirs_to_check = [
            d for d in self.root.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

        # 计算每个目录的大小
        dir_data = []
        for directory in dirs_to_check:
            size = self.get_dir_size(directory)
            dir_data.append((directory.name, size))

        # 按大小排序
        dir_data.sort(key=lambda x: x[1], reverse=True)

        return dir_data[:top_n]

    def print_report(self, top_n: int = 15):
        """打印分析报告"""
        largest_dirs = self.analyze(top_n)

        print("\n" + "=" * 70)
        print("📊 项目大体积目录 TOP 15")
        print("=" * 70)

        for i, (name, size) in enumerate(largest_dirs, 1):
            size_mb = size / (1024 * 1024)
            size_gb = size / (1024 * 1024 * 1024)

            if size_gb >= 1:
                size_str = f"{size_gb:.2f} GB"
            else:
                size_str = f"{size_mb:.2f} MB"

            print(f"{i:2d}. {name:<30s} {size_str:>10s}")

        print("=" * 70)

        # 识别可清理的目录
        print("\n💡 建议清理的目录:")
        cleanup_candidates = [
            "flutter_old",
            "backup_*",
            "build",
            "dist",
            ".venv",
            "node_modules",
            "__pycache__",
        ]

        for name, size in largest_dirs:
            for pattern in cleanup_candidates:
                if pattern in name or name.endswith(pattern):
                    size_mb = size / (1024 * 1024)
                    print(f"  🗑️  {name} ({size_mb:.2f} MB) - 可以安全删除")

        print()


def main():
    """主函数"""
    # 获取项目根目录 (上一级)
    project_root = Path(__file__).parent.parent

    analyzer = DirectorySizeAnalyzer(project_root)
    analyzer.print_report(top_n=15)


if __name__ == "__main__":
    main()
