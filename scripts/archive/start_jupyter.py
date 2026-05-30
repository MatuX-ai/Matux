#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jupyter Notebook 启动脚本
"""

import os
import subprocess
import sys

def start_jupyter():
    """启动Jupyter Notebook"""
    print("正在启动 Jupyter Notebook...")
    print("请在浏览器中打开显示的URL地址")
    print("按 Ctrl+C 可以停止服务器")
    print("-" * 50)
    
    try:
        # 启动Jupyter Notebook
        subprocess.run([
            sys.executable, "-m", "jupyter", "notebook",
            "--ip=0.0.0.0",
            "--port=8888",
            "--no-browser",
            "--allow-root"
        ])
    except KeyboardInterrupt:
        print("\nJupyter Notebook 已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请确保已安装 jupyter 包")

if __name__ == "__main__":
    start_jupyter()