@echo off
chcp 65001 >nul
echo ========================================
echo   iMatu Blog - Ghost CMS 停止脚本
echo ========================================
echo.

:: 检查 Docker Compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)

:: 进入项目目录
cd /d "%~dp0.."

echo 🛑 正在停止 Ghost CMS...
echo.

%COMPOSE_CMD% -f docker-compose.blog.yml down

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 停止失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ✅ Ghost CMS 已停止
echo.
echo 📌 重启：%COMPOSE_CMD% -f docker-compose.blog.yml up -d
echo.

pause
