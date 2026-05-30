@echo off
echo ========================================
echo Flutter环境修复脚本
echo ========================================

echo 正在检查系统环境...

REM 检查Git安装
echo 检查Git安装状态...
where git >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Git已安装: 
    git --version
) else (
    echo ✗ 未找到Git，请先安装Git
    echo 下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM 检查PowerShell
echo 检查PowerShell...
where powershell >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ PowerShell可用
) else (
    echo ✗ PowerShell不可用，请检查系统环境
    pause
    exit /b 1
)

REM 设置Flutter环境变量
echo 设置Flutter环境变量...
set FLUTTER_ROOT=g:\iMato\flutter\flutter
set PATH=%FLUTTER_ROOT%\bin;%PATH%

echo 当前PATH: %PATH%

REM 验证Flutter命令
echo 验证Flutter安装...
"%FLUTTER_ROOT%\bin\flutter.bat" --version
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Flutter命令执行失败
    pause
    exit /b 1
)

echo ✓ Flutter环境修复完成！

REM 运行Flutter医生检查
echo 运行Flutter医生诊断...
"%FLUTTER_ROOT%\bin\flutter.bat" doctor -v

pause