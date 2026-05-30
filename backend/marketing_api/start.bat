@echo off
REM MatuX Marketing API 启动脚本 (Windows)

echo 🚀 启动 MatuX Marketing API...

REM 检查 Python 版本
python --version

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo ✅ 激活虚拟环境...
call venv\Scripts\activate

REM 安装依赖
echo 📦 安装依赖...
pip install -q -r requirements.txt

REM 创建数据目录
if not exist "data" mkdir data

REM 启动服务
echo 🚀 启动服务...
python main.py

pause
