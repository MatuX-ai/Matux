@echo off
chcp 65001 >nul
echo ============================================================
echo 测试一键启动功能
echo ============================================================
echo.

REM 清理可能存在的旧进程
echo [准备] 清理旧进程...
taskkill /F /IM redis-server.exe 2>nul
taskkill /F /FI "WINDOWTITLE eq *Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *Frontend*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo 开始启动所有服务...
echo ============================================================
echo.

REM 启动 Redis（如果存在）
if exist "G:\iMato\backend\redis\redis-server.exe" (
    echo [1/3] 启动 Redis...
    start "Redis Server" cmd /k "cd /d G:\iMato\backend\redis && redis-server.exe redis.windows.conf"
    timeout /t 3 /nobreak >nul
    echo      ✓ Redis 启动命令已发送
) else (
    echo      ℹ Redis 未安装，将跳过
)

echo.
echo [2/3] 启动后端服务...
start "iMato Backend" cmd /k "cd /d G:\iMato\backend && G:\Python312\python.exe run.py"
timeout /t 5 /nobreak >nul
echo      ✓ 后端启动命令已发送

echo.
echo [3/3] 启动前端服务...
start "iMato Frontend" cmd /k "cd /d G:\iMato && npm start"
echo      ✓ 前端启动命令已发送

echo.
echo ============================================================
echo ✅ 所有启动命令已执行
echo ============================================================
echo.
echo 等待服务初始化...
echo.

REM 等待并检查服务状态
timeout /t 10 /nobreak >nul

echo 检查服务状态:
echo.

REM 检查 Redis
netstat -ano | findstr :6379 >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Redis: 端口 6379 正在监听
) else (
    echo   ℹ Redis: 未运行或不可用
)

REM 检查后端
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ 后端服务：端口 8000 正在监听
) else (
    echo   ✗ 后端服务：未在端口 8000 监听
)

REM 检查前端
netstat -ano | findstr :4200 >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ 前端服务：端口 4200 正在监听
) else (
    echo   ✗ 前端服务：未在端口 4200 监听
)

echo.
echo ============================================================
echo 测试完成!
echo ============================================================
echo.
echo 访问地址:
echo   - 前端：http://localhost:4200
echo   - 后端：http://localhost:8000
echo   - API 文档：http://localhost:8000/docs
echo.
echo 提示：可以打开浏览器访问上述地址验证服务是否正常
echo.
pause
