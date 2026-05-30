# iMato AI Service Windows部署脚本

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("deploy", "stop", "restart", "status", "backup")]
    [string]$Action = "deploy",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message" -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput $Message "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput $Message "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput $Message "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput $Message "Red"
}

# 检查必要工具
function Check-Dependencies {
    Write-Info "检查系统依赖..."
    
    $requiredTools = @("docker", "docker-compose")
    $missingTools = @()
    
    foreach ($tool in $requiredTools) {
        if (!(Get-Command $tool -ErrorAction SilentlyContinue)) {
            $missingTools += $tool
        }
    }
    
    if ($missingTools.Count -gt 0) {
        Write-Error "缺少必要的工具: $($missingTools -join ', ')"
        Write-Error "请先安装 Docker Desktop"
        exit 1
    }
    
    Write-Success "依赖检查通过"
}

# 检查环境变量
function Check-EnvironmentVariables {
    Write-Info "检查环境变量..."
    
    $requiredVars = @(
        "SECRET_KEY",
        "OPENAI_API_KEY",
        "LINGMA_API_KEY",
        "DEEPSEEK_API_KEY"
    )
    
    $missingVars = @()
    
    foreach ($var in $requiredVars) {
        if ([string]::IsNullOrEmpty($env:$var)) {
            $missingVars += $var
        }
    }
    
    if ($missingVars.Count -gt 0) {
        Write-Warning "以下环境变量未设置: $($missingVars -join ', ')"
        Write-Warning "请在 .env.$Environment 文件中设置这些变量"
    }
    
    Write-Success "环境变量检查完成"
}

# 构建应用
function Build-Application {
    Write-Info "构建应用镜像..."
    
    try {
        docker-compose build --no-cache
        if ($LASTEXITCODE -eq 0) {
            Write-Success "应用镜像构建成功"
        } else {
            throw "构建失败"
        }
    } catch {
        Write-Error "应用镜像构建失败: $_"
        exit 1
    }
}

# 启动服务
function Start-Services {
    Write-Info "启动服务..."
    
    try {
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Success "服务启动成功"
        } else {
            throw "启动失败"
        }
    } catch {
        Write-Error "服务启动失败: $_"
        exit 1
    }
}

# 停止服务
function Stop-Services {
    Write-Info "停止服务..."
    
    try {
        docker-compose down
        Write-Success "服务已停止"
    } catch {
        Write-Error "停止服务失败: $_"
    }
}

# 重启服务
function Restart-Services {
    Write-Info "重启服务..."
    Stop-Services
    Start-Services
}

# 检查服务状态
function Get-ServiceStatus {
    Write-Info "检查服务状态..."
    docker-compose ps
}

# 等待服务就绪
function Wait-ForServices {
    Write-Info "等待服务启动..."
    
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "服务已就绪"
                return
            }
        } catch {
            # 服务还未就绪，继续等待
        }
        
        Write-Info "等待服务启动... ($attempt/$maxAttempts)"
        Start-Sleep -Seconds 10
        $attempt++
    }
    
    Write-Error "服务启动超时"
    exit 1
}

# 创建备份
function Create-Backup {
    Write-Info "创建部署前备份..."
    
    $backupDir = ".\backups"
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "backup_$timestamp"
    
    if (!(Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    
    # 备份配置文件
    if (Test-Path ".env.$Environment") {
        Copy-Item ".env.$Environment" "$backupDir\${backupName}_config.env"
        Write-Success "配置文件备份已创建"
    }
    
    # 备份Docker卷
    try {
        docker run --rm -v ai_postgres_data:/data -v ${PWD}/$backupDir:/backup alpine tar czf /backup/${backupName}_postgres.tar.gz -C /data .
        Write-Success "数据库备份已创建: $backupDir\${backupName}_postgres.tar.gz"
    } catch {
        Write-Warning "数据库备份失败: $_"
    }
    
    Write-Success "备份完成"
}

# 运行健康检查
function Invoke-HealthCheck {
    Write-Info "运行健康检查..."
    
    $checks = @(
        @{Url = "http://localhost:8000/health"; Description = "健康检查端点"},
        @{Url = "http://localhost:8000/docs"; Description = "API文档"}
    )
    
    $failedChecks = 0
    
    foreach ($check in $checks) {
        try {
            $response = Invoke-WebRequest -Uri $check.Url -Method GET -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "✓ $($check.Description)"
            } else {
                Write-Error "✗ $($check.Description) - HTTP $($response.StatusCode)"
                $failedChecks++
            }
        } catch {
            Write-Error "✗ $($check.Description) - $_"
            $failedChecks++
        }
    }
    
    if ($failedChecks -eq 0) {
        Write-Success "所有健康检查通过"
        return $true
    } else {
        Write-Error "部分健康检查失败"
        return $false
    }
}

# 显示部署信息
function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "           部署完成信息" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "API地址: http://localhost:8000" -ForegroundColor White
    Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "健康检查: http://localhost:8000/health" -ForegroundColor White
    Write-Host "------------------------------------------" -ForegroundColor Gray
    Write-Host "服务状态:" -ForegroundColor White
    docker-compose ps
    Write-Host "------------------------------------------" -ForegroundColor Gray
    Write-Host "后续步骤:" -ForegroundColor Yellow
    Write-Host "1. 配置域名和SSL证书" -ForegroundColor White
    Write-Host "2. 设置监控和告警" -ForegroundColor White
    Write-Host "3. 配置日志收集" -ForegroundColor White
    Write-Host "4. 设置定期备份" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Green
}

# 主部署函数
function Deploy-Application {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "    iMato AI Service 部署脚本" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    # 检查依赖
    Check-Dependencies
    
    # 检查环境变量
    Check-EnvironmentVariables
    
    # 创建备份
    Create-Backup
    
    # 备份当前配置
    if (Test-Path "docker-compose.yml") {
        Copy-Item "docker-compose.yml" "docker-compose.previous.yml" -Force
    }
    
    # 构建应用
    Build-Application
    
    # 启动服务
    Start-Services
    
    # 等待服务就绪
    Wait-ForServices
    
    # 运行健康检查
    $healthCheckPassed = Invoke-HealthCheck
    
    if ($healthCheckPassed) {
        # 显示部署信息
        Show-DeploymentInfo
        Write-Success "部署完成!"
    } else {
        Write-Error "部署完成但健康检查失败，请检查服务状态"
        exit 1
    }
}

# 根据参数执行相应操作
switch ($Action) {
    "deploy" {
        Deploy-Application
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Restart-Services
    }
    "status" {
        Get-ServiceStatus
    }
    "backup" {
        Create-Backup
    }
    default {
        Write-Error "未知的操作: $Action"
        Write-Host "可用操作: deploy, stop, restart, status, backup"
        exit 1
    }
}