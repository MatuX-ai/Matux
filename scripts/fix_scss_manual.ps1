#!/usr/bin/env pwsh
# SCSS 文件手动乱码修复脚本
# 批量修复 6 个文件中的已知乱码

$ErrorActionPreference = "Stop"

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "🔧 SCSS Manual Encoding Fix Tool" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 定义需要修复的文件
$files = @(
    "src\styles\layout.scss",
    "src\styles\main.scss",
    "src\styles\reset.scss",
    "src\styles\typography.scss",
    "src\styles\themes\_custom-theme.scss",
    "src\styles\themes\_dark-theme.scss"
)

# 定义乱码映射表（基于实际文件内容推断）
$replacements = @{
    # layout.scss
    '鍏ㄥ眬甯冨眬瀹瑰櫒绯荤粺锛屾彁渚涘搷搴斿紡甯冨眬瑙e喅鏂规' = '全局布局容器系统，提供响应式布局解决方案'
    '瀵煎叆 Design Tokens' = '导入 Design Tokens'
    '鍩虹瀹瑰櫒绫？' = '基础容器类'
    '鏍囧噯鍥哄畾瀹藉害瀹瑰櫒' = '标准固定宽度容器'

    # main.scss
    '鐎电厧鍙？Design Tokens' = '导入 Design Tokens'

    # reset.scss
    '閻╂帗膩閸ㄥ鍣哥纯？' = '盒模型重置'

    # typography.scss
    '閸╄櫣顢呴幒鎺斿闁插秶鐤？' = '排版重置'

    # _custom-theme.scss
    '閸╄桨绨？Design Tokens 閻ㄥ嚜aterial Design 娑撳顣？' = '基于 Design Tokens 的 Material Design 主题'
    '鐎规矮绠熺拫鍐閺？' = '定义调色板'

    # _dark-theme.scss
    '閺嗘绮︽稉濠氼暯CSS閸欐﹢鍣虹€规矮绠？' = '暗黑主题 CSS 变量定义'
    '閸╄櫣顢呴懗灞炬珯閸滃矁銆冮棃銏ゎ杹閼？' = '基础背景和表面颜色'
}

$fixedCount = 0
$skippedCount = 0

foreach ($file in $files) {
    if (Test-Path $file) {
        try {
            # 读取文件内容
            $content = Get-Content $file.FullName -Raw -Encoding UTF8
            $originalContent = $content
            $modified = $false

            # 应用所有替换
            foreach ($key in $replacements.Keys) {
                if ($content -match [regex]::Escape($key)) {
                    $content = $content -replace [regex]::Escape($key), $replacements[$key]
                    $modified = $true
                }
            }

            # 如果有修改，保存文件
            if ($modified) {
                # 使用 UTF-8 无 BOM 编码保存
                [System.IO.File]::WriteAllText(
                    $file.FullName,
                    $content,
                    (New-Object System.Text.UTF8Encoding $false)
                )
                Write-Host "✅ Fixed: $file" -ForegroundColor Green
                $fixedCount++
            } else {
                Write-Host "✓ No changes: $file" -ForegroundColor Gray
                $skippedCount++
            }
        } catch {
            Write-Host "❌ Error: $file - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️ Not found: $file" -ForegroundColor Yellow
        $skippedCount++
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Fixed: $fixedCount files" -ForegroundColor Green
Write-Host "  ✓ Skipped: $skippedCount files" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if ($fixedCount -gt 0) {
    Write-Host "💡 Next step: Run Prettier to verify" -ForegroundColor Yellow
    Write-Host "   npx prettier --write `"src/**/*.scss`"" -ForegroundColor Cyan
    Write-Host ""
}
