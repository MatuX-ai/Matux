# iMato Cloud - 一键部署启动脚本 (PowerShell)
# 用法：.\scripts\deploy-cloud.ps1 [选项]
# 示例:
#   .\scripts\deploy-cloud.ps1 --start      # 首次部署启动
#   .\scripts\deploy-cloud.ps1 --restart    # 重启服务
#   .\scripts\deploy-cloud.ps1 --status     # 查看状态
#   .\scripts\deploy-cloud.ps1 --logs       # 查看日志

param(
    [switch]$start,
    [switch]$stop,
    [switch]$restart,
    [switch]$status,
    [switch]$logs,
    [switch]$clean,
    [switch]$build,
    [switch]$help
)

$COMPOSE_FILE = "docker-compose.cloud.yml"
$PROJECT_NAME = "imato-cloud"

# 颜色函数
function Write-Info { Write-Host $args[0] -ForegroundColor Blue }
function Write-Success { Write-Host $args[0] -ForegroundColor Green }
function Write-Warning { Write-Host $args[0] -ForegroundColor Yellow }
function Write-Error-Custom { Write-Host $args[0] -ForegroundColor Red }

# 显示帮助
function Show-Help {
    Write-Info "==================================="
    Write-Info "iMato Cloud 一键部署脚本"
    Write-Info "==================================="
    Write-Host ""
    Write-Host "用法：.\scripts\deploy-cloud.ps1 [选项]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  --start     启动所有服务（包括构建镜像）"
    Write-Host "  --stop      停止所有服务（保留数据）"
    Write-Host "  --restart   重启所有服务"
    Write-Host "  --status    查看所有服务运行状态"
    Write-Host "  --logs      查看实时日志（支持 Ctrl+C 退出）"
    Write-Host "  --clean     清理所有容器、网络和卷（⚠️ 危险操作，数据将丢失）"
    Write-Host "  --build     仅构建镜像，不启动服务"
    Write-Host "  --help      显示此帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\scripts\deploy-cloud.ps1 --start     # 首次部署启动"
    Write-Host "  .\scripts\deploy-cloud.ps1 --restart   # 重启服务"
    Write-Host "  .\scripts\deploy-cloud.ps1 --status    # 查看状态"
    Write-Host ""
}

# 检查 Docker
function Check-Docker {
    try {
        $null = docker info 2>&1
    } catch {
        Write-Error-Custom "错误：Docker 未运行"
        exit 1
    }

    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "错误：docker-compose 未安装"
        exit 1
    }
}

# 检查配置文件
function Check-Config {
    if (-not (Test-Path $COMPOSE_FILE)) {
        Write-Error-Custom "错误：找不到 $COMPOSE_FILE"
        exit 1
    }

    if (-not (Test-Path "docker\.env.production")) {
        Write-Warning "警告：未找到 docker\.env.production 文件"
        Write-Warning "建议：Copy docker\.env.example docker\.env.production"
        Write-Host ""
    }
}

# 启动服务
function Start-Services {
    Write-Success "==================================="
    Write-Success "启动 iMato Cloud 服务..."
    Write-Success "==================================="

    Check-Config

    Write-Warning "[1/3] 构建 Docker 镜像..."
    docker-compose -f $COMPOSE_FILE build

    Write-Warning "[2/3] 启动所有服务..."
    docker-compose -f $COMPOSE_FILE up -d

    Write-Warning "[3/3] 等待服务健康检查..."
    Start-Sleep -Seconds 10

    Write-Success "✓ 服务启动完成！"
    Write-Host ""
    Write-Info "访问地址："
    Write-Host "  前端应用：http://localhost"
    Write-Host "  API 端点：http://localhost/api/v1"
    Write-Host "  Grafana: http://localhost:3000 (admin/admin123)"
    Write-Host "  Prometheus: http://localhost:9090"
    Write-Host ""
    Write-Warning "提示：使用 '.\scripts\deploy-cloud.ps1 --status' 查看服务状态"
}

# 停止服务
function Stop-Services {
    Write-Warning "停止所有服务..."
    docker-compose -f $COMPOSE_FILE stop
    Write-Success "✓ 服务已停止"
}

# 重启服务
function Restart-Services {
    Write-Warning "重启所有服务..."
    docker-compose -f $COMPOSE_FILE restart
    Write-Success "✓ 服务已重启"
}

# 查看状态
function Show-Status {
    Write-Info "==================================="
    Write-Info "iMato Cloud 服务状态"
    Write-Info "==================================="
    docker-compose -f $COMPOSE_FILE ps
    Write-Host ""
    Write-Info "资源占用："
    docker stats --no-stream
}

# 查看日志
function Show-Logs {
    Write-Warning "实时日志输出（Ctrl+C 退出）..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# 清理环境
function Clean-Environment {
    Write-Error-Custom "⚠️  警告：此操作将删除所有容器、网络和数据卷！"
    $confirm = Read-Host "确认继续？(yes/no)"

    if ($confirm -eq "yes") {
        Write-Warning "停止服务..."
        docker-compose -f $COMPOSE_FILE down -v
        Write-Warning "清理悬空镜像..."
        docker image prune -f
        Write-Success "✓ 清理完成"
    } else {
        Write-Warning "操作已取消"
    }
}

# 构建镜像
function Build-Images {
    Write-Warning "构建 Docker 镜像..."
    docker-compose -f $COMPOSE_FILE build
    Write-Success "✓ 构建完成"
}

# 主逻辑
if ($start) {
    Check-Docker
    Start-Services
} elseif ($stop) {
    Stop-Services
} elseif ($restart) {
    Restart-Services
} elseif ($status) {
    Show-Status
} elseif ($logs) {
    Show-Logs
} elseif ($clean) {
    Clean-Environment
} elseif ($build) {
    Build-Images
} elseif ($help) {
    Show-Help
} else {
    Write-Error-Custom "未知选项"
    Show-Help
    exit 1
}
