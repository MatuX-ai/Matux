#!/usr/bin/env powershell
# ════════════════════════════════════════════════════════════════════
# 营销页面文件重命名脚本
# ════════════════════════════════════════════════════════════════════
# 功能: 批量重命名营销页面组件文件
# 用法: 右键 → "使用 PowerShell 运行" 或从终端执行
# ════════════════════════════════════════════════════════════════════

# 设置错误处理
$ErrorActionPreference = "Stop"

# 配置输出颜色
$colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    Write-Host $Message -ForegroundColor $colors[$Type]
}

# ════════════════════════════════════════════════════════════════════
# 配置区域
# ════════════════════════════════════════════════════════════════════

$projectRoot = "g:\iMato\src\app\marketing"
$backupCreated = $false

# 定义重命名映射
$renames = @(
    @{
        Directory = "marketing-home"
        From = "marketing-home-matu.component.ts"
        To = "home.component.ts"
        ComponentName = "营销首页"
    },
    @{
        Directory = "marketing-pricing"
        From = "marketing-pricing-matu.component.ts"
        To = "pricing.component.ts"
        ComponentName = "定价页面"
    },
    @{
        Directory = "marketing-features"
        From = "marketing-features-matu.component.ts"
        To = "features.component.ts"
        ComponentName = "功能页面"
    },
    @{
        Directory = "marketing-about"
        From = "marketing-about-matu.component.ts"
        To = "about.component.ts"
        ComponentName = "关于页面"
    },
    @{
        Directory = "marketing-contact"
        From = "marketing-contact-matu.component.ts"
        To = "contact.component.ts"
        ComponentName = "联系页面"
    }
)

# ════════════════════════════════════════════════════════════════════
# 主逻辑
# ════════════════════════════════════════════════════════════════════

Write-ColorMessage "`n╔════════════════════════════════════════════════════════════╗" "Info"
Write-ColorMessage "║     营销页面文件重命名脚本 - MatuX Project                ║" "Info"
Write-ColorMessage "╚════════════════════════════════════════════════════════════╝" "Info"
Write-ColorMessage "`n📍 项目路径: $projectRoot`n" "Info"

# 检查项目目录
if (-not (Test-Path $projectRoot)) {
    Write-ColorMessage "❌ 错误: 项目目录不存在！`n   $projectRoot" "Error"
    Write-ColorMessage "`n请检查路径是否正确。`n" "Warning"
    pause
    exit 1
}

# 显示重命名计划
Write-ColorMessage "═══════════════════════════════════════════════════════════════" "Info"
Write-ColorMessage "📋 重命名计划:" "Info"
Write-ColorMessage "═══════════════════════════════════════════════════════════════" "Info"

$totalLengthBefore = 0
$totalLengthAfter = 0

foreach ($item in $renames) {
    $fromPath = Join-Path $projectRoot $item.Directory $item.From
    $toPath = Join-Path $projectRoot $item.Directory $item.To
    
    $fromLength = $fromPath.Length
    $toLength = $toPath.Length
    $saved = $fromLength - $toLength
    $percent = [math]::Round(($saved / $fromLength) * 100, 1)
    
    $totalLengthBefore += $fromLength
    $totalLengthAfter += $toLength
    
    Write-ColorMessage "`n📄 $($item.ComponentName):" "Info"
    Write-Host "   从: $($item.From)"
    Write-Host "   到: $($item.To)"
    Write-Host "   缩短: $saved 字符 ($percent%)" -ForegroundColor Green
}

$totalSaved = $totalLengthBefore - $totalLengthAfter
$totalPercent = [math]::Round(($totalSaved / $totalLengthBefore) * 100, 1)

Write-ColorMessage "`n═══════════════════════════════════════════════════════════════" "Info"
Write-ColorMessage "📊 总计:" "Info"
Write-ColorMessage "   文件数: $($renames.Count)" "Info"
Write-ColorMessage "   总缩短: $totalSaved 字符 ($totalPercent%)" "Success"
Write-ColorMessage "═══════════════════════════════════════════════════════════════" "Info"

# 确认执行
Write-ColorMessage "`n⚠️  即将执行重命名操作，此操作无法撤销！" "Warning"
$response = Read-Host "是否继续? (Y/N)"

if ($response -ne 'Y' -and $response -ne 'y') {
    Write-ColorMessage "`n❌ 操作已取消。`n" "Warning"
    pause
    exit 0
}

# ════════════════════════════════════════════════════════════════════
# 执行重命名
# ════════════════════════════════════════════════════════════════════

Write-ColorMessage "`n═══════════════════════════════════════════════════════════════" "Info"
Write-ColorMessage "🚀 开始执行重命名..." "Info"
Write-ColorMessage "═══════════════════════════════════════════════════════════════" "Info"

$successCount = 0
$skipCount = 0
$errorCount = 0

foreach ($item in $renames) {
    $dirPath = Join-Path $projectRoot $item.Directory
    $fromPath = Join-Path $dirPath $item.From
    $toPath = Join-Path $dirPath $item.To
    
    Write-ColorMessage "`n📁 $($item.ComponentName):" "Info"
    Write-Host "   路径: $dirPath"
    
    # 检查目录
    if (-not (Test-Path $dirPath)) {
        Write-ColorMessage "   ❌ 目录不存在，跳过" "Error"
        $errorCount++
        continue
    }
    
    # 检查源文件
    if (-not (Test-Path $fromPath)) {
        # 检查是否已重命名
        if (Test-Path $toPath) {
            Write-ColorMessage "   ⚠️  已重命名，跳过" "Warning"
            $skipCount++
            continue
        } else {
            Write-ColorMessage "   ❌ 源文件不存在" "Error"
            Write-Host "      期望: $fromPath" -ForegroundColor Gray
            $errorCount++
            continue
        }
    }
    
    # 检查目标文件是否已存在
    if (Test-Path $toPath) {
        Write-ColorMessage "   ❌ 目标文件已存在" "Error"
        Write-Host "      文件: $toPath" -ForegroundColor Gray
        $errorCount++
        continue
    }
    
    # 执行重命名
    try {
        Rename-Item -Path $fromPath -NewName $item.To -ErrorAction Stop
        Write-ColorMessage "   ✅ 重命名成功" "Success"
        $successCount++
    } catch {
        Write-ColorMessage "   ❌ 重命名失败: $($_.Exception.Message)" "Error"
        $errorCount++
    }
}

# ════════════════════════════════════════════════════════════════════
# 结果汇总
# ════════════════════════════════════════════════════════════════════

Write-ColorMessage "`n═══════════════════════════════════════════════════════════════" "Info"
Write-ColorMessage "📊 执行结果:" "Info"
Write-ColorMessage "═══════════════════════════════════════════════════════════════" "Info"

Write-ColorMessage "   ✅ 成功: $successCount" "Success"
Write-ColorMessage "   ⚠️  跳过: $skipCount" "Warning"
Write-ColorMessage "   ❌ 失败: $errorCount" "Error"

# ════════════════════════════════════════════════════════════════════
# 后续操作
# ════════════════════════════════════════════════════════════════════

if ($errorCount -eq 0) {
    Write-ColorMessage "`n🎉 所有文件重命名成功！" "Success"
    
    if ($skipCount -gt 0) {
        Write-ColorMessage "   (部分文件已存在，已跳过)" "Warning"
    }
    
    Write-ColorMessage "`n📋 建议后续操作:" "Info"
    Write-Host "   1. 运行 'cd g:\iMato'"
    Write-Host "   2. 运行 'npm run build' 验证构建"
    Write-Host "   3. 运行 'npm start' 测试功能"
    Write-Host "   4. 访问 http://localhost:4200/marketing"
    Write-Host "   5. 提交 Git 更改"
    
    Write-ColorMessage "`n✨ 项目即将完成！" "Success"
} else {
    Write-ColorMessage "`n⚠️  部分文件重命名失败" "Warning"
    Write-ColorMessage "   请查看上面的错误信息" "Warning"
    Write-ColorMessage "   可以手动重命名失败的文件" "Warning"
}

Write-ColorMessage "`n═══════════════════════════════════════════════════════════════" "Info"

# 可选：自动打开项目目录
$openFolder = Read-Host "是否打开项目目录? (Y/N)"
if ($openFolder -eq 'Y' -or $openFolder -eq 'y') {
    Start-Process $projectRoot
}

Write-ColorMessage "`n👋 脚本执行完成！`n" "Info"
pause

# ════════════════════════════════════════════════════════════════════
# 脚本结束
# ════════════════════════════════════════════════════════════════════
