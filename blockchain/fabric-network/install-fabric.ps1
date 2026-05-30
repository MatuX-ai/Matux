# Install Hyperledger Fabric binaries for Windows

Write-Host "📥 开始安装Hyperledger Fabric工具..." -ForegroundColor Green

# 创建安装目录
$installDir = "$env:USERPROFILE\fabric-binaries"
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force
}

Set-Location $installDir

# 下载Fabric 2.5版本工具
Write-Host "⬇️ 下载Fabric 2.5二进制文件..." -ForegroundColor Yellow
$webClient = New-Object System.Net.WebClient
$webClient.DownloadFile("https://github.com/hyperledger/fabric/releases/download/v2.5.0/hyperledger-fabric-windows-amd64-2.5.0.zip", "$installDir\fabric-2.5.0.zip")

# 下载Fabric CA 1.5版本工具
Write-Host "⬇️ 下载Fabric CA 1.5二进制文件..." -ForegroundColor Yellow
$webClient.DownloadFile("https://github.com/hyperledger/fabric-ca/releases/download/v1.5.0/hyperledger-fabric-ca-windows-amd64-1.5.0.zip", "$installDir\fabric-ca-1.5.0.zip")

# 解压文件
Write-Host "📦 解压二进制文件..." -ForegroundColor Yellow
Expand-Archive -Path "$installDir\fabric-2.5.0.zip" -DestinationPath $installDir -Force
Expand-Archive -Path "$installDir\fabric-ca-1.5.0.zip" -DestinationPath $installDir -Force

# 清理压缩包
Remove-Item "$installDir\fabric-2.5.0.zip"
Remove-Item "$installDir\fabric-ca-1.5.0.zip"

# 获取bin目录路径
$binPath = "$installDir\bin"
Write-Host "🔧 配置环境变量..." -ForegroundColor Yellow

# 添加到当前会话的PATH
$env:PATH = "$binPath;$env:PATH"

# 添加到用户环境变量（持久化）
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$binPath*") {
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$binPath", "User")
}

Write-Host "✅ Fabric工具安装完成!" -ForegroundColor Green
Write-Host "📁 工具位置: $binPath" -ForegroundColor Cyan
Write-Host "🔧 环境变量已更新，重启终端后生效" -ForegroundColor Cyan

# 验证安装
Write-Host "🔍 验证工具安装..." -ForegroundColor Yellow
& "$binPath\cryptogen.exe" version
& "$binPath\configtxgen.exe" version
