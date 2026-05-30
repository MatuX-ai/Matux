#!/usr/bin/env pwsh
# SCSS 文件编码修复脚本
param(
    [string]$Path = "src\styles",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$fixedCount = 0
$totalCount = 0

Write-Host "`n🔧 SCSS 文件编码修复工具" -ForegroundColor Cyan
Write-Host "========================================`n"

# 获取所有 SCSS 文件
$scssFiles = Get-ChildItem -Path $Path -Recurse -Filter "*.scss"
Write-Host "📂 找到 $($scssFiles.Count) 个 SCSS 文件`n"

foreach ($file in $scssFiles) {
    $totalCount++
    Write-Progress -Activity "修复 SCSS 文件" -Status "处理：$($file.Name)" -PercentComplete (($totalCount / $scssFiles.Count) * 100)

    try {
        # 读取文件内容
        $content = Get-Content $file.FullName -Raw -Encoding UTF8

        # 常见的乱码模式及修复
        $fixes = @{
            '鐎电厧鍙？' = '导入'
            '閸╄櫣顢？' = '定义'
            '閺嗘绮︽稉濠氼暯' = '暗黑主题'
            '閸旀垵绨？' = '布局'
            '閻╂帗膩閸ㄥ鍣哥纯？' = '盒模型重置'
            '娑撴槒鍎楅弲顖濆' = '主背景色'
            '闁插秶鐤？' = '排版重置'
            '闁猴拷' = '样式'
            '閸?/span>' = ''
            '[39m' = ''
        }

        $modified = $false
        foreach ($key in $fixes.Keys) {
            if ($content -match [regex]::Escape($key)) {
                $content = $content -replace [regex]::Escape($key), $fixes[$key]
                $modified = $true
            }
        }

        # 如果内容有修改，保存文件
        if ($modified) {
            [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
            Write-Host "✅ $($file.Name)" -ForegroundColor Green
            $fixedCount++
        } else {
            if ($Verbose) {
                Write-Host "✓ $($file.Name) (无需修复)" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "❌ $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n========================================"
Write-Host "✅ 完成！修复了 $fixedCount/$totalCount 个文件" -ForegroundColor Green
Write-Host "========================================`n"
