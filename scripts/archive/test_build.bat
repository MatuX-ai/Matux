@echo off
echo 开始构建测试...
echo 时间: %TIME%
echo.

cd /d g:\iMato

:: 设置Node选项以提高内存限制
set NODE_OPTIONS=--max-old-space-size=8192

echo 正在运行 ng build...
echo 这可能需要3-5分钟...
echo.

:: 运行构建并实时显示输出
node_modules\.bin\ng build

echo.
echo 构建完成时间: %TIME%
echo 退出码: %ERRORLEVEL%
echo.

:: 检查结果
if %ERRORLEVEL% equ 0 (
    echo ========================================
    echo ✅ 构建成功！
    echo ========================================
    echo.
    dir dist\imatuproject
) else (
    echo ========================================
    echo ❌ 构建失败
    echo ========================================
    echo 退出码: %ERRORLEVEL%
)

echo.
pause
