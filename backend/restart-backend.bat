@echo off
REM iMato 后端启动脚本（main_ai_edu.py 简化版，无需 Redis/Neo4j）
REM 端口由 PORT 环境变量控制，默认 8000
cd /d g:\iMato\backend
if "%PORT%"=="" set PORT=8000
REM 强制 UTF-8 避免 GBK 编码问题（emoji/中文）
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo [%date% %time%] Starting MatuX backend (main_ai_edu.py) on port %PORT%...
g:\Python312\python.exe main_ai_edu.py
