# Phase 5 Electron 测试脚本
# 使用方法: .\test-phase5-electron.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Phase 5 Electron 功能测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 检查 Angular 开发服务器
Write-Host "[1/5] 检查 Angular 开发服务器..." -ForegroundColor Yellow
$angularRunning = (netstat -ano | Select-String ":4200").Count -gt 0
if ($angularRunning) {
    Write-Host "  ✅ Angular 开发服务器正在运行 (端口 4200)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Angular 开发服务器未运行" -ForegroundColor Red
    Write-Host "  💡 请先运行: npm run dev" -ForegroundColor Yellow
    exit 1
}

# 检查 Electron 主进程文件
Write-Host "`n[2/5] 检查 Electron 文件..." -ForegroundColor Yellow
$mainJsExists = Test-Path "electron\main.js"
$preloadJsExists = Test-Path "electron\preload.js"

if ($mainJsExists -and $preloadJsExists) {
    Write-Host "  ✅ electron\main.js 存在" -ForegroundColor Green
    Write-Host "  ✅ electron\preload.js 存在" -ForegroundColor Green
} else {
    Write-Host "  ❌ Electron 文件缺失" -ForegroundColor Red
    exit 1
}

# 检查 Phase 5 模块
Write-Host "`n[3/5] 检查 Phase 5 模块..." -ForegroundColor Yellow
$phase5Modules = @(
    "electron\plugin-recommender.js",
    "electron\install-config.js",
    "electron\plugin-store-enhancer.js"
)

$allModulesExist = $true
foreach ($module in $phase5Modules) {
    if (Test-Path $module) {
        Write-Host "  ✅ $module" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $module 缺失" -ForegroundColor Red
        $allModulesExist = $false
    }
}

if (-not $allModulesExist) {
    Write-Host "`n  ❌ Phase 5 模块不完整" -ForegroundColor Red
    exit 1
}

# 检查 Phase 5 前端组件
Write-Host "`n[4/5] 检查 Phase 5 前端组件..." -ForegroundColor Yellow
$phase5Components = @(
    "src\app\shared\components\plugin-recommendations",
    "src\app\shared\components\first-run-guide",
    "src\app\shared\components\plugin-reviews",
    "src\app\shared\components\plugin-usage-stats",
    "src\app\shared\components\plugin-updates"
)

$allComponentsExist = $true
foreach ($component in $phase5Components) {
    if (Test-Path $component) {
        Write-Host "  ✅ $component" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $component 缺失" -ForegroundColor Red
        $allComponentsExist = $false
    }
}

if (-not $allComponentsExist) {
    Write-Host "`n  ❌ Phase 5 组件不完整" -ForegroundColor Red
    exit 1
}

# 启动 Electron
Write-Host "`n[5/5] 启动 Electron 应用..." -ForegroundColor Yellow
Write-Host "`n💡 提示: 在 Electron 窗口中访问插件商店测试 Phase 5 功能" -ForegroundColor Cyan
Write-Host "   1. 点击左侧导航的'插件商店'" -ForegroundColor Cyan
Write-Host "   2. 首次启动会显示引导流程" -ForegroundColor Cyan
Write-Host "   3. 查看推荐插件卡片" -ForegroundColor Cyan
Write-Host "   4. 点击插件查看详情面板" -ForegroundColor Cyan
Write-Host "   5. 查看评分评论和使用统计" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 可停止 Electron`n" -ForegroundColor Yellow

# 启动 Electron（加载 Angular 开发服务器）
npx electron electron/main.js
