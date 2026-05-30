#!/usr/bin/env powershell
#
# 3D 模型库开发环境自动部署脚本
#
# 用途：自动安装依赖、配置环境、验证部署
# 运行时间：预计 10-20 分钟
# 系统要求：Windows 10/11, PowerShell 5.1+
#

param(
    [switch]$SkipPython = $false,
    [switch]$SkipNode = $false,
    [switch]$SkipBlender = $false,
    [switch]$OnlyVerify = $false,
    [switch]$Help = $false
)

# 配置颜色主题
$Host.UI.RawUI.WindowTitle = "🚀 iMatu 3D 模型库 - 自动部署工具"
$WarningColor = "Yellow"
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"

# ============================================================================
# 辅助函数
# ============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor $InfoColor
    Write-Host "  $Text" -ForegroundColor $InfoColor
    Write-Host ("=" * 70) -ForegroundColor $InfoColor
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $SuccessColor
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $ErrorColor
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor $WarningColor
}

function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Test-PythonVersion {
    try {
        $version = python --version 2>&1
        return $version -match 'Python 3\.[9-9]|Python 3\.1[0-9]'
    } catch {
        return $false
    }
}

function Test-NodeVersion {
    try {
        $version = node --version 2>&1
        return $version -match 'v1[8-9]|v2[0-9]'
    } catch {
        return $false
    }
}

function Test-BlenderVersion {
    try {
        $version = blender --version 2>&1
        return $version -match 'Blender 3\.[6-9]|Blender [4-9]\.'
    } catch {
        return $false
    }
}

function Install-PythonPackage {
    param(
        [string]$PackageName,
        [string]$Version = ""
    )

    $spec = if ($Version) { "$PackageName==$Version" } else { $PackageName }

    Write-Host "  正在安装 $PackageName..." -NoNewline
    try {
        pip install $spec --quiet
        Write-Success "已安装"
        return $true
    } catch {
        Write-Error-Custom "安装失败：$_"
        return $false
    }
}

function Install-NpmPackage {
    param(
        [string]$PackageName,
        [string]$Version = "",
        [switch]$SaveDev = $false
    )

    $args = @("install", $PackageName)
    if ($Version) { $args += "@$Version" }
    if ($SaveDev) { $args += "--save-dev" }

    Write-Host "  正在安装 $PackageName..." -NoNewline
    try {
        npm @args --silent
        Write-Success "已安装"
        return $true
    } catch {
        Write-Error-Custom "安装失败：$_"
        return $false
    }
}

function Create-Directory {
    param([string]$Path)
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
        Write-Host "  创建目录：$Path" -ForegroundColor $InfoColor
    }
}

# ============================================================================
# 主部署流程
# ============================================================================

Write-Header "iMatu 3D 模型库开发环境部署"

Write-Host "工作目录：G:\iMato" -ForegroundColor $InfoColor
Write-Host "部署时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $InfoColor
Write-Host ""

# 切换到工作目录
Set-Location G:\iMato

# ============================================================================
# 阶段 1: 显示帮助信息
# ============================================================================

if ($Help) {
    Write-Header "使用说明"
    Write-Host @"
用法：.\setup_development_environment.ps1 [选项]

选项:
  -SkipPython     跳过 Python 环境检查
  -SkipNode       跳过 Node.js 环境检查
  -SkipBlender    跳过 Blender 环境检查
  -OnlyVerify     仅验证现有环境，不安装新包
  -Help           显示此帮助信息

示例:
  .\setup_development_environment.ps1              # 完整部署
  .\setup_development_environment.ps1 -OnlyVerify  # 仅验证
  .\setup_development_environment.ps1 -SkipBlender # 跳过 Blender

"@ -ForegroundColor $InfoColor
    exit 0
}

# ============================================================================
# 阶段 2: 环境检查
# ============================================================================

Write-Header "步骤 1: 环境检查"

$envStatus = @{
    Python = $false
    Node = $false
    Npm = $false
    Blender = $false
    Git = $false
}

# 检查 Python
if (!$SkipPython) {
    if (Test-PythonVersion) {
        $pythonVersion = python --version 2>&1
        Write-Success "Python: $pythonVersion"
        $envStatus.Python = $true
    } else {
        Write-Error-Custom "Python 未安装或版本不符合要求 (需要 3.9+)"
        if (!$OnlyVerify) {
            Write-Host "  建议运行：winget install Python.Python.3.11" -ForegroundColor $WarningColor
        }
    }
} else {
    Write-Warning-Custom "跳过 Python 检查"
    $envStatus.Python = $true
}

# 检查 Node.js
if (!$SkipNode) {
    if (Test-NodeVersion) {
        $nodeVersion = node --version 2>&1
        Write-Success "Node.js: $nodeVersion"
        $envStatus.Node = $true

        # 检查 npm
        if (Test-CommandExists npm) {
            $npmVersion = npm --version 2>&1
            Write-Success "npm: $npmVersion"
            $envStatus.Npm = $true
        } else {
            Write-Error-Custom "npm 未找到"
        }
    } else {
        Write-Error-Custom "Node.js 未安装或版本不符合要求 (需要 18+)"
        if (!$OnlyVerify) {
            Write-Host "  建议运行：winget install OpenJS.NodeJS.LTS" -ForegroundColor $WarningColor
        }
    }
} else {
    Write-Warning-Custom "跳过 Node.js 检查"
    $envStatus.Node = $true
    $envStatus.Npm = $true
}

# 检查 Blender
if (!$SkipBlender) {
    if (Test-BlenderVersion) {
        $blenderVersion = blender --version 2>&1 | Select-String "Blender" | Select-Object -First 1
        Write-Success "Blender: $blenderVersion"
        $envStatus.Blender = $true
    } else {
        Write-Warning-Custom "Blender 未安装或版本不符合要求 (需要 3.6+)"
        Write-Host "  模型转换功能将不可用 (可选组件)" -ForegroundColor $WarningColor
    }
} else {
    Write-Warning-Custom "跳过 Blender 检查"
    $envStatus.Blender = $true
}

# 检查 Git
if (Test-CommandExists git) {
    $gitVersion = git --version 2>&1
    Write-Success "Git: $gitVersion"
    $envStatus.Git = $true
} else {
    Write-Warning-Custom "Git 未安装 (推荐安装)"
}

# 环境检查总结
Write-Host ""
Write-Host "环境检查摘要:" -ForegroundColor $InfoColor
$requiredOk = ($envStatus.Python -and $envStatus.Node -and $envStatus.Npm)
if ($requiredOk) {
    Write-Success "必需环境满足，可以继续部署"
} else {
    Write-Error-Custom "必需环境不满足，请先安装缺失的组件"
    Write-Host "`n按任意键退出..." -ForegroundColor $WarningColor
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# 如果只验证，到这里结束
if ($OnlyVerify) {
    Write-Header "验证完成"
    Write-Success "环境配置正常"
    exit 0
}

# ============================================================================
# 阶段 3: 安装 Python 依赖
# ============================================================================

if ($envStatus.Python) {
    Write-Header "步骤 2: 安装 Python 依赖"

    Write-Host "核心依赖:" -ForegroundColor $InfoColor
    Install-PythonPackage -PackageName "requests"

    Write-Host "`n开发工具 (可选):" -ForegroundColor $InfoColor
    $installDevTools = Read-Host "  安装开发工具？(black/flake8/mypy/pytest) (y/n)"
    if ($installDevTools -eq 'y' -or $installDevTools -eq 'Y') {
        Install-PythonPackage -PackageName "black"
        Install-PythonPackage -PackageName "flake8"
        Install-PythonPackage -PackageName "mypy"
        Install-PythonPackage -PackageName "pytest"
        Install-PythonPackage -PackageName "pytest-cov"
    }
}

# ============================================================================
# 阶段 4: 安装 Angular 依赖
# ============================================================================

if ($envStatus.Npm) {
    Write-Header "步骤 3: 安装 Angular 依赖"

    Write-Host "核心依赖:" -ForegroundColor $InfoColor
    Install-NpmPackage -PackageName "three" -SaveDev
    Install-NpmPackage -PackageName "@types/three" -SaveDev

    Write-Host "`n可选依赖:" -ForegroundColor $InfoColor
    $installWebSocket = Read-Host "  安装 WebSocket 支持？(ws) (y/n)"
    if ($installWebSocket -eq 'y' -or $installWebSocket -eq 'Y') {
        Install-NpmPackage -PackageName "ws" -SaveDev
        Install-NpmPackage -PackageName "@types/ws" -SaveDev
    }
}

# ============================================================================
# 阶段 5: 创建目录结构
# ============================================================================

Write-Header "步骤 4: 创建目录结构"

$directories = @(
    "models\electronic_components",
    "models\electronic_components_lod",
    "data\kicad_models",
    "logs",
    "src\assets\models",
    "temp\conversions"
)

foreach ($dir in $directories) {
    Create-Directory -Path (Join-Path G:\iMato $dir)
}

Write-Success "目录结构创建完成"

# ============================================================================
# 阶段 6: 复制资源文件
# ============================================================================

Write-Header "步骤 5: 配置资源文件"

# 复制模型索引
$modelIndexSource = "data\kicad_model_index.json"
$modelIndexDest = "src\assets\models\kicad_model_index.json"

if (Test-Path $modelIndexSource) {
    Copy-Item -Path $modelIndexSource -Destination $modelIndexDest -Force
    Write-Success "模型索引已复制到: $modelIndexDest"
} else {
    Write-Warning-Custom "模型索引不存在，稍后可以通过爬虫生成"
}

# ============================================================================
# 阶段 7: 运行验证
# ============================================================================

Write-Header "步骤 6: 运行部署验证"

Write-Host "正在运行验证脚本..." -ForegroundColor $InfoColor
try {
    & python scripts\validate_3d_model_implementation.py
    Write-Success "验证通过！"
} catch {
    Write-Error-Custom "验证失败：$_"
    Write-Host "`n请检查错误信息并修复" -ForegroundColor $WarningColor
}

# ============================================================================
# 阶段 8: 生成模型索引 (如果有爬虫)
# ============================================================================

Write-Header "步骤 7: 生成模型索引"

$generateIndex = Read-Host "  运行爬虫生成模型索引？(y/n)"
if ($generateIndex -eq 'y' -or $generateIndex -eq 'Y') {
    Write-Host "正在运行爬虫脚本..." -ForegroundColor $InfoColor
    try {
        & python scripts\kicad_model_scraper.py
        Write-Success "模型索引生成成功"

        # 显示统计
        if (Test-Path "data\kicad_model_index.json") {
            $indexData = Get-Content "data\kicad_model_index.json" -Raw | ConvertFrom-Json
            $modelCount = $indexData.models.Count
            Write-Success "共收录 $modelCount 个模型"
        }
    } catch {
        Write-Warning-Custom "爬虫执行失败，可以稍后手动运行"
    }
}

# ============================================================================
# 阶段 9: 部署完成总结
# ============================================================================

Write-Header "部署完成!"

Write-Host @"
✅ 部署成功!

已完成项目:
  • Python 依赖安装
  • Angular 依赖安装
  • 目录结构创建
  • 资源文件配置
  • 环境验证通过

下一步建议:
  1. 查看快速启动指南: docs\QUICK_START_3D_MODEL_LIBRARY.md
  2. 获取真实模型数据: python scripts\kicad_model_scraper.py
  3. 转换模型格式: python scripts\model_converter.py
  4. 启动开发服务器: ng serve

文档位置:
  • 本地部署指南：docs\LOCAL_DEPLOYMENT_GUIDE.md
  • 快速启动指南：docs\QUICK_START_3D_MODEL_LIBRARY.md
  • 模型选择指南：docs\KICAD_MODEL_SELECTION_GUIDE.md

技术支持:
  遇到问题请访问文档或运行诊断:
  python scripts\validate_3d_model_implementation.py --verbose

"@ -ForegroundColor $SuccessColor

Write-Host "按任意键退出..." -ForegroundColor $InfoColor
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

exit 0
