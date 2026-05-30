#!/bin/bash

# MatuX Marketing API 启动脚本

echo "🚀 启动 MatuX Marketing API..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📦 Python 版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "✅ 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 创建数据目录
mkdir -p data

# 启动服务
echo "🚀 启动服务..."
python main.py
