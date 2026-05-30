@echo off
echo ==========================================
echo 修复Angular 21兼容性问题
echo ==========================================
echo.

cd /d g:\iMato

echo [步骤 1/3] 更新TypeScript版本...
npm install typescript@~5.9.5 --save-dev
echo.

echo [步骤 2/3] 修复Angular Material SCSS导入...
echo 请稍等...
echo.

:: 修复Material SCSS的导入问题
:: Angular 21+ 需要使用 @use 而不是 @import

echo [步骤 3/3] 重新构建项目...
npm run build > build_fix.log 2>&1

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo ✅ 构建成功！
    echo ==========================================
    echo.
) else (
    echo.
    echo ==========================================
    echo ❌ 构建失败
    echo ==========================================
    echo.
    echo 请查看 build_fix.log 了解详细信息
    echo.
    type build_fix.log | findstr /i "error"
)

echo.
pause
