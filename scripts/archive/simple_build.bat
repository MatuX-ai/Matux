@echo off
echo ========================================
echo 简单构建测试
echo ========================================
echo 开始时间: %TIME%
echo.

cd /d g:\iMato

echo 运行 ng build...
echo 这可能需要3-5分钟...
echo.

set start_time=%TIME%
node_modules\.bin\ng build
set build_exit_code=%ERRORLEVEL%
set end_time=%TIME%

echo.
echo ========================================
echo 构建完成
echo ========================================
echo 开始时间: %start_time%
echo 结束时间: %end_time%
echo 退出码: %build_exit_code%
echo.

if %build_exit_code% equ 0 (
    echo ✅ 构建成功！
    echo.
    echo 检查输出...
    if exist dist\imatuproject\index.html (
        echo ✅ index.html 已生成
    ) else (
        echo ⚠️  index.html 未找到
    )
) else (
    echo ❌ 构建失败
    echo 退出码: %build_exit_code%
)

echo.
echo 按任意键退出...
pause >nul
