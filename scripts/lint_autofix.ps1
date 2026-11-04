#!/usr/bin/env pwsh
# WIP lint 机械修复脚本 —— 供各任务线在提交前自行运行（Windows PowerShell / pwsh）
#
# 只做一件事：用 ruff 批量修复「可安全自动修复」的机械类 lint 问题，
# 然后打印本次被改动的文件清单。
# 与 scripts/lint-all.sh（只检查、不修改）互补。
#
# 明确不做的事：
#   - 不执行 git add / git commit
#   - 不修改 config/lint-baseline.txt（基线需人工确认后再更新）
#   - 不触碰本任务线之外的 WIP 代码
#
# 修复的规则集（全部为纯机械问题）：
#   W292 文件末尾缺少换行
#   E127 连续行缩进不一致
#   E131 续行缩进不一致
#   E306 期望一个空行分隔的嵌套定义
#   F541 f-string 缺少占位符
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts/lint_autofix.ps1
#   pwsh -File scripts/lint_autofix.ps1

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root

$Rules = 'W292,E127,E131,E306,F541'
$Target = 'backend'

if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) {
    Write-Host '错误：未找到 ruff。请先安装开发依赖：pip install -r requirements.dev.txt' -ForegroundColor Red
    exit 127
}

# 以本次运行开始的时间为基准；之后被 ruff 改写过的文件即为本次改动清单。
$Ref = Get-Date
Start-Sleep -Seconds 1

Write-Host '== 运行 ruff 批量修复 =='
$ErrorActionPreference = 'Continue'
& ruff check --select $Rules --fix $Target
$RuffExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
Write-Host "(ruff 退出码: $RuffExit；非 0 表示仍有无法自动修复的问题，需人工处理)"

Write-Host ''
Write-Host '== 本次被改动的文件 =='
$Base = (Get-Location).Path
$Changed = Get-ChildItem -LiteralPath $Target -Recurse -Filter '*.py' -File |
    Where-Object { $_.LastWriteTime -gt $Ref } |
    ForEach-Object { $_.FullName.Substring($Base.Length + 1).Replace('\', '/') } |
    Sort-Object

if ($Changed) {
    $Changed | ForEach-Object { Write-Host $_ }
} else {
    Write-Host '（无）'
}

Write-Host ''
Write-Host '提示：本脚本不执行 git add / git commit，请自行 review diff 后再提交。'
exit 0
