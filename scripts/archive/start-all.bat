@echo off
chcp 65001 >nul
echo ============================================================
echo iMato Project - All Services One-Click Startup
echo ============================================================
echo.
echo 💡 提示：推荐使用 VSCode 任务启动 (Ctrl+Shift+B)
echo 📖 详细说明请查看：docs/一键启动指南.md
echo.============================================================
echo.

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not installed
    pause
    exit /b 1
)

REM 检查 Python
G:\Python312\python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not installed
    pause
    exit /b 1
)

echo [INFO] Environment check passed
echo.

REM 启动 Redis（如果存在）
if exist "G:\iMato\backend\redis\redis-server.exe" (
    echo [Step 0/3] Starting Redis Service...
    start "Redis Server" cmd /k "cd /d G:\iMato\backend\redis && redis-server.exe redis.windows.conf"
    timeout /t 2 /nobreak >nul
) else (
    echo [INFO] Redis not found, will use memory mode
)

REM 启动后端
echo [Step 1/3] Starting Backend Service...
start "iMato Backend" cmd /k "cd /d G:\iMato\backend && G:\Python312\python.exe run.py"
timeout /t 5 /nobreak >nul

REM 启动前端
echo [Step 2/3] Starting Frontend Service...
start "iMato Frontend" cmd /k "cd /d G:\iMato && npm start"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo ✅ Services Started!
echo ============================================================
echo.
echo Access URLs:
echo   - Frontend: http://localhost:4200
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo To stop services:
echo   - Close the command windows
echo   - Or use VSCode task: Kill All Services
echo.
echo ============================================================
echo.
pause
