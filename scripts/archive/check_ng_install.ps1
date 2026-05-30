# Angular安装状态快速检查
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Angular 21 安装状态检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置路径
$projectPath = "g:\iMato"
$nodeModulesPath = Join-Path $projectPath "node_modules"
$angularCorePath = Join-Path $nodeModulesPath "@angular\core"

# 检查项目目录
Write-Host "[检查 1/4] 项目目录..." -ForegroundColor Yellow
if (Test-Path $projectPath) {
    Write-Host "✅ 项目目录存在: $projectPath" -ForegroundColor Green
} else {
    Write-Host "❌ 项目目录不存在!" -ForegroundColor Red
    exit
}

# 检查node_modules
Write-Host "`n[检查 2/4] node_modules..." -ForegroundColor Yellow
if (Test-Path $nodeModulesPath) {
    Write-Host "✅ node_modules 存在" -ForegroundColor Green
    
    # 计算大小
    $files = Get-ChildItem $nodeModulesPath -Recurse -File -ErrorAction SilentlyContinue
    if ($files) {
        $sizeMB = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        Write-Host "   大小: $sizeMB MB" -ForegroundColor Gray
        
        if ($sizeMB -gt 200) {
            Write-Host "   ✅ 大小正常 ( > 200MB )" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  大小偏小，可能未完全安装" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ node_modules 不存在!" -ForegroundColor Red
}

# 检查Angular
Write-Host "`n[检查 3/4] Angular核心包..." -ForegroundColor Yellow
if (Test-Path $angularCorePath) {
    Write-Host "✅ @angular/core 已安装" -ForegroundColor Green
    
    # 读取版本
    $packageJson = Join-Path $angularCorePath "package.json"
    if (Test-Path $packageJson) {
        try {
            $version = (Get-Content $packageJson | ConvertFrom-Json).version
            Write-Host "   版本: $version" -ForegroundColor Gray
            
            if ($version -like "21.*") {
                Write-Host "   ✅ 版本正确 (21.x)" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  版本不是21.x" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "   无法读取版本信息" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "❌ @angular/core 未安装!" -ForegroundColor Red
}

# 检查ng命令
Write-Host "`n[检查 4/4] ng命令..." -ForegroundColor Yellow
$ngCommand = Get-Command ng -ErrorAction SilentlyContinue
if ($ngCommand) {
    Write-Host "✅ ng 命令可用" -ForegroundColor Green
    Write-Host "   路径: $($ngCommand.Source)" -ForegroundColor Gray
} else {
    Write-Host "⚠️  ng 命令不可用 (将在node_modules/.bin中)" -ForegroundColor Yellow
}

# 总结
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "总结" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ((Test-Path $angularCorePath) -and (Test-Path $nodeModulesPath)) {
    Write-Host "✅ 安装看起来已完成!" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Yellow
    Write-Host "  1. 运行: cd $projectPath" -ForegroundColor White
    Write-Host "  2. 运行: ng serve" -ForegroundColor White
    Write-Host "  3. 打开浏览器: http://localhost:4200" -ForegroundColor White
} else {
    Write-Host "❌ 安装未完成或失败!" -ForegroundColor Red
    Write-Host ""
    Write-Host "建议操作:" -ForegroundColor Yellow
    Write-Host "  1. 运行: cd $projectPath" -ForegroundColor White
    Write-Host "  2. 运行: npm install" -ForegroundColor White
    Write-Host "  或双击运行: quick_install.bat" -ForegroundColor White
}

Write-Host ""
