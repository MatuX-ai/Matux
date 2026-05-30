# PowerShell脚本 - 检查Angular安装状态
# 使用方法: powershell -File check_installation_status.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Angular 21 安装状态检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查node_modules是否存在
$nodeModulesExists = Test-Path "g:\iMato\node_modules"
if ($nodeModulesExists) {
    Write-Host "✅ node_modules 目录已创建" -ForegroundColor Green
    
    # 检查关键包是否安装
    $angularCoreExists = Test-Path "g:\iMato\node_modules\@angular\core"
    if ($angularCoreExists) {
        Write-Host "✅ @angular/core 已安装" -ForegroundColor Green
        
        # 读取版本
        $packageJsonPath = "g:\iMato\node_modules\@angular\core\package.json"
        if (Test-Path $packageJsonPath) {
            $packageJson = Get-Content $packageJsonPath | ConvertFrom-Json
            $version = $packageJson.version
            Write-Host "   版本: $version" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ @angular/core 未找到" -ForegroundColor Red
    }
    
    # 检查node_modules大小
    $nodeModulesSize = (Get-ChildItem "g:\iMato\node_modules" -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $sizeInMB = [math]::Round($nodeModulesSize / 1MB, 2)
    Write-Host "   目录大小: $sizeInMB MB" -ForegroundColor Yellow
    
} else {
    Write-Host "⏳ node_modules 不存在 - 安装可能仍在进行中" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "建议操作:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "如果安装完成，运行: ng version" -ForegroundColor White
Write-Host "如果安装失败，查看: yarn-error.log" -ForegroundColor White
Write-Host "如果需要重试，运行: yarn install" -ForegroundColor White
Write-Host ""

# 检查是否有错误日志
$errorLogExists = Test-Path "g:\iMato\yarn-error.log"
if ($errorLogExists) {
    Write-Host "⚠️  发现 yarn-error.log 文件，可能安装出错" -ForegroundColor Red
    Write-Host "   查看错误: type g:\iMato\yarn-error.log" -ForegroundColor Yellow
}
