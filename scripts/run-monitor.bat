@echo off
REM iMato 营销页面监控脚本（Windows）
REM 快捷启动监控工具

echo ========================================
echo iMato 营销页面监控工具
echo ========================================
echo.

REM 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未安装Node.js
    echo 请先安装Node.js: https://nodejs.org/
    exit /b 1
)

REM 检查依赖
echo 📦 检查依赖...
if not exist "node_modules" (
    echo 📥 安装依赖...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        exit /b 1
    )
)

REM 检查Playwright
echo 🔍 检查Playwright...
if not exist "node_modules\playwright" (
    echo 📥 安装Playwright...
    npm install playwright
    npx playwright install
)

REM 显示菜单
echo.
echo 请选择操作:
echo 1. 监控所有页面（无头模式）
echo 2. 监控所有页面（可视化模式）
echo 3. 移动端测试
echo 4. 执行全部测试（桌面+移动）
echo 5. 自定义配置
set /p choice="输入选项 (1-5): "

echo.

if "%choice%"=="1" (
    echo 🚀 开始监控（无头模式）...
    node marketing-page-monitor.js
) else if "%choice%"=="2" (
    echo 🚀 开始监控（可视化模式）...
    node marketing-page-monitor.js --no-headless
) else if "%choice%"=="3" (
    echo 🚀 开始移动端测试...
    node marketing-page-monitor.js --mobile
) else if "%choice%"=="4" (
    echo 🚀 执行全部测试...
    echo 步骤 1/2: 桌面端测试...
    node marketing-page-monitor.js
    echo.
    echo 步骤 2/2: 移动端测试...
    node marketing-page-monitor.js --mobile
) else if "%choice%"=="5" (
    set /p baseUrl="请输入基础URL (默认: http://localhost:4200): "
    set /p timeout="请输入超时时间毫秒 (默认: 30000): "
    
    set "args="
    if not "%baseUrl%"=="" set "args=%args% --base-url=%baseUrl%"
    if not "%timeout%"=="" set "args=%args% --timeout=%timeout%"
    
    echo 🚀 开始自定义监控...
    node marketing-page-monitor.js %args%
) else (
    echo ❌ 无效选项
    exit /b 1
)

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ 监控完成！
    echo ========================================
    echo 📊 查看报告: monitoring-reports/
    echo.
    timeout /t 5
) else (
    echo.
    echo ❌ 监控失败
    exit /b 1
)
