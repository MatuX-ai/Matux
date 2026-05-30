# iMato Cloud Version - Docker 镜像构建脚本 (PowerShell)
# 用法：.\scripts\build-docker-image.ps1 [-dev] [-prod] [-noCache] [-tag <TAG>]
# 示例:
#   .\scripts\build-docker-image.ps1 -prod              # 构建生产环境镜像
#   .\scripts\build-docker-image.ps1 -dev -noCache      # 无缓存构建开发镜像
#   .\scripts\build-docker-image.ps1 -tag v1.0.0        # 构建带版本标签的镜像

param(
    [switch]$dev,
    [switch]$prod,
    [switch]$noCache,
    [string]$tag = "latest"
)

$ErrorActionPreference = "Stop"

# 变量设置
$IMAGE_NAME = "imato-cloud"
$DOCKERFILE = "Dockerfile.cloud"
$BUILD_ARGS = @()

# 解析参数
if ($dev) {
    $BUILD_ARGS += "--build-arg", "APP_ENV=development"
    $tag = "dev"
}
if ($prod) {
    $BUILD_ARGS += "--build-arg", "APP_ENV=production"
    $tag = "latest"
}
if ($noCache) {
    $BUILD_ARGS += "--no-cache"
}

# 检查 Docker 是否运行
Write-Host "检查 Docker 状态..." -ForegroundColor Cyan
try {
    $dockerInfo = docker info 2>&1
    if (-not $dockerInfo) {
        throw "Docker 未运行"
    }
} catch {
    Write-Host "错误：Docker 未运行或未启动" -ForegroundColor Red
    Write-Host "请启动 Docker Desktop 或 Docker 服务" -ForegroundColor Yellow
    exit 1
}

# 检查 Dockerfile 是否存在
if (-not (Test-Path $DOCKERFILE)) {
    Write-Host "错误：找不到 $DOCKERFILE" -ForegroundColor Red
    exit 1
}

# 显示构建信息
Write-Host "`n===================================" -ForegroundColor Green
Write-Host "iMato Cloud Docker 镜像构建" -ForegroundColor Green
Write-Host "===================================`n" -ForegroundColor Green
Write-Host "镜像名称：" -NoNewline
Write-Host "$IMAGE_NAME:$tag" -ForegroundColor Yellow
Write-Host "Dockerfile: " -NoNewline
Write-Host "$DOCKERFILE" -ForegroundColor Yellow
Write-Host "构建参数：" -NoNewline
Write-Host $($BUILD_ARGS -join ' ') -ForegroundColor Yellow
Write-Host ""

# 进入项目根目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDir "..")

# 开始构建
Write-Host "开始构建 Docker 镜像..." -ForegroundColor Yellow
$START_TIME = Get-Date

try {
    $dockerArgs = @("build") + $BUILD_ARGS + @("-f", $DOCKERFILE, "-t", "$IMAGE_NAME:$tag", ".")

    & docker $dockerArgs

    $END_TIME = Get-Date
    $DURATION = ($END_TIME - $START_TIME).TotalSeconds

    # 构建成功
    Write-Host "`n✓ 构建成功！" -ForegroundColor Green
    Write-Host "耗时："$DURATION.ToString("F2") "秒" -ForegroundColor Yellow
    Write-Host "镜像：$IMAGE_NAME:$tag`n" -ForegroundColor Blue

    # 显示镜像大小
    $IMAGE_SIZE = (docker images $IMAGE_NAME:$tag --format "{{.Size}}")[0]
    Write-Host "镜像大小：$IMAGE_SIZE`n" -ForegroundColor Yellow

    # 提示下一步
    Write-Host "下一步操作：" -ForegroundColor Green
    Write-Host "  1. 测试镜像：docker run --rm -p 80:80 $IMAGE_NAME:$tag"
    Write-Host "  2. 查看日志：docker logs <container_id>"
    Write-Host "  3. 推送镜像：docker push $IMAGE_NAME:$tag"
    Write-Host ""

} catch {
    Write-Host "`n构建失败！" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    exit 1
}
