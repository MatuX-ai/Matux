@echo off
echo =================================
echo 检查Angular版本
echo =================================
echo.

cd /d g:\iMato

:: 检查ng命令是否可用
where ng >nul 2>&1
if %errorlevel% equ 0 (
    echo ng 命令可用，版本信息:
    echo.
    call ng version
) else (
    echo ❌ ng 命令不可用
    echo.
    echo 可能原因:
    echo 1. Angular CLI 未全局安装
    echo 2. 未添加到PATH
    echo.
    echo 尝试修复:
    echo npm install -g @angular/cli@21.2.1
    echo.
    echo 或使用npx:
    echo npx ng version
)

echo.
pause
