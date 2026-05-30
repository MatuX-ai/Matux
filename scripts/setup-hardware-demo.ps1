# iMatuProject 硬件通信演示设置脚本
# 用于快速搭建和运行硬件通信原型

Write-Host "🚀 iMatuProject 硬件通信原型设置" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# 检查Flutter是否已安装
Write-Host "🔍 检查Flutter环境..." -ForegroundColor Yellow
try {
    $flutterVersion = flutter --version
    Write-Host "✅ Flutter已安装" -ForegroundColor Green
    Write-Host $flutterVersion.Split("`n")[0] -ForegroundColor Cyan
} catch {
    Write-Host "❌ 未找到Flutter，请先安装Flutter SDK" -ForegroundColor Red
    Write-Host "下载地址: https://flutter.dev/docs/get-started/install" -ForegroundColor Yellow
    Write-Host "安装完成后请重新运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 进入Flutter项目目录
Set-Location "$PSScriptRoot\..\flutter_app"

# 获取依赖
Write-Host "`n📦 获取项目依赖..." -ForegroundColor Yellow
flutter pub get

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 依赖获取成功" -ForegroundColor Green
} else {
    Write-Host "❌ 依赖获取失败" -ForegroundColor Red
    exit 1
}

# 运行测试
Write-Host "`n🧪 运行单元测试..." -ForegroundColor Yellow
flutter test

# 启动Web应用
Write-Host "`n🌐 启动Web应用..." -ForegroundColor Yellow
Write-Host "⚠️  请确保使用支持WebUSB的浏览器（Chrome 61+ 或 Edge 79+）" -ForegroundColor Yellow
Write-Host "💡 应用启动后，点击主页的'WebUSB 硬件通信演示'进入演示页面" -ForegroundColor Cyan

flutter run -d chrome

Write-Host "`n✨ 设置完成！" -ForegroundColor Green