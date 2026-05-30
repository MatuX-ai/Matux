@echo off
REM APM监控系统Windows部署脚本

echo 🚀 开始部署APM监控系统...

REM 设置变量
set PROJECT_DIR=%~dp0..\backend
set COMPOSE_FILE=%PROJECT_DIR%\docker-compose.apm.yml

REM 检查必要工具
echo 🔍 检查依赖...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

echo ✅ 依赖检查通过

REM 创建必要的目录
echo 📁 创建必要目录...
mkdir "%PROJECT_DIR%\apm-data\prometheus" 2>nul
mkdir "%PROJECT_DIR%\apm-data\grafana" 2>nul
mkdir "%PROJECT_DIR%\apm-data\skywalking" 2>nul
mkdir "%PROJECT_DIR%\logs\apm" 2>nul
echo ✅ 目录创建完成

REM 配置环境变量
echo ⚙️  配置环境变量...
if not exist "%PROJECT_DIR%\.env.apm" (
    if exist "%PROJECT_DIR%\.env.apm.example" (
        copy "%PROJECT_DIR%\.env.apm.example" "%PROJECT_DIR%\.env.apm"
        echo ✅ 环境配置文件已创建，请根据实际情况修改 .env.apm 文件
    ) else (
        echo ❌ 未找到环境配置模板文件
        pause
        exit /b 1
    )
) else (
    echo ✅ 环境配置文件已存在
)

REM 配置Prometheus
echo 📊 配置Prometheus...
(
echo global:
echo   scrape_interval: 15s
echo   evaluation_interval: 15s
echo.
echo rule_files:
echo   - "alert.rules"
echo.
echo scrape_configs:
echo   - job_name: 'imato-backend'
echo     static_configs:
echo       - targets: ['host.docker.internal:8000']
echo     metrics_path: '/metrics'
echo.
echo   - job_name: 'prometheus'
echo     static_configs:
echo       - targets: ['localhost:9090']
echo.
echo alerting:
echo   alertmanagers:
echo     - static_configs:
echo         - targets: ['alertmanager:9093']
) > "%PROJECT_DIR%\apm-data\prometheus\prometheus.yml"
echo ✅ Prometheus配置完成

REM 配置Grafana
echo 📈 配置Grafana...
mkdir "%PROJECT_DIR%\apm-data\grafana\provisioning\datasources" 2>nul
(
echo apiVersion: 1
echo.
echo datasources:
echo   - name: Prometheus
echo     type: prometheus
echo     access: proxy
echo     url: http://prometheus:9090
echo     isDefault: true
) > "%PROJECT_DIR%\apm-data\grafana\provisioning\datasources\prometheus.yml"
echo ✅ Grafana配置完成

REM 部署APM服务
echo 🐳 部署APM监控服务...
docker-compose -f "%COMPOSE_FILE%" up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 30 /nobreak >nul

REM 检查服务状态
echo 📋 服务状态检查:
docker-compose -f "%COMPOSE_FILE%" ps

REM 验证部署
echo ✅ 验证部署...

REM 测试Prometheus指标端点
curl -s http://localhost:9090/-/healthy >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Prometheus运行正常
) else (
    echo ⚠️  Prometheus可能存在问题
)

REM 测试应用指标端点
curl -s http://localhost:8000/metrics >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 应用指标端点正常
) else (
    echo ⚠️  应用指标端点可能存在问题
)

echo ✅ 部署验证完成

REM 显示访问信息
echo.
echo 🎉 APM监控系统部署完成！
echo.
echo 📊 访问地址:
echo   Prometheus: http://localhost:9090
echo   Grafana: http://localhost:3000 (默认用户: admin/admin)
echo   SkyWalking UI: http://localhost:8080
echo.
echo 🔧 后续步骤:
echo   1. 登录Grafana配置仪表板
echo   2. 在SkyWalking中查看分布式追踪
echo   3. 配置告警规则
echo.
echo 📝 日志查看:
echo   docker-compose -f "%COMPOSE_FILE%" logs -f
echo.

pause