#!/bin/bash
# APM监控系统部署脚本

set -e

echo "🚀 开始部署APM监控系统..."

# 配置变量
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.apm.yml"

# 检查必要工具
check_dependencies() {
    echo "🔍 检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    echo "✅ 依赖检查通过"
}

# 创建必要的目录
create_directories() {
    echo "📁 创建必要目录..."
    
    mkdir -p "$PROJECT_DIR/apm-data/prometheus"
    mkdir -p "$PROJECT_DIR/apm-data/grafana"
    mkdir -p "$PROJECT_DIR/apm-data/skywalking"
    mkdir -p "$PROJECT_DIR/logs/apm"
    
    echo "✅ 目录创建完成"
}

# 配置环境变量
setup_environment() {
    echo "⚙️  配置环境变量..."
    
    if [ ! -f "$PROJECT_DIR/.env.apm" ]; then
        if [ -f "$PROJECT_DIR/.env.apm.example" ]; then
            cp "$PROJECT_DIR/.env.apm.example" "$PROJECT_DIR/.env.apm"
            echo "✅ 环境配置文件已创建，请根据实际情况修改 .env.apm 文件"
        else
            echo "❌ 未找到环境配置模板文件"
            exit 1
        fi
    else
        echo "✅ 环境配置文件已存在"
    fi
}

# 部署APM服务
deploy_apm_services() {
    echo "🐳 部署APM监控服务..."
    
    # 启动APM服务
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 30
    
    # 检查服务状态
    echo "📋 服务状态检查:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    # 检查关键端口
    check_ports() {
        local port=$1
        local service=$2
        if nc -z localhost $port; then
            echo "✅ $service (端口 $port) 正常运行"
        else
            echo "⚠️  $service (端口 $port) 可能未正常启动"
        fi
    }
    
    check_ports 11800 "SkyWalking OAP"
    check_ports 8080 "SkyWalking UI"
    check_ports 9090 "Prometheus"
    check_ports 3000 "Grafana"
}

# 配置Prometheus
configure_prometheus() {
    echo "📊 配置Prometheus..."
    
    cat > "$PROJECT_DIR/apm-data/prometheus/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert.rules"

scrape_configs:
  - job_name: 'imato-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
EOF

    echo "✅ Prometheus配置完成"
}

# 配置Grafana
configure_grafana() {
    echo "📈 配置Grafana..."
    
    # 创建数据源配置
    mkdir -p "$PROJECT_DIR/apm-data/grafana/provisioning/datasources"
    cat > "$PROJECT_DIR/apm-data/grafana/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    echo "✅ Grafana配置完成"
}

# 验证部署
verify_deployment() {
    echo "✅ 验证部署..."
    
    # 测试Prometheus指标端点
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        echo "✅ Prometheus运行正常"
    else
        echo "❌ Prometheus可能存在问题"
    fi
    
    # 测试应用指标端点
    if curl -s http://localhost:8000/metrics > /dev/null; then
        echo "✅ 应用指标端点正常"
    else
        echo "❌ 应用指标端点可能存在问题"
    fi
    
    echo "✅ 部署验证完成"
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "🎉 APM监控系统部署完成！"
    echo ""
    echo "📊 访问地址:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3000 (默认用户: admin/admin)"
    echo "  SkyWalking UI: http://localhost:8080"
    echo ""
    echo "🔧 后续步骤:"
    echo "  1. 登录Grafana配置仪表板"
    echo "  2. 在SkyWalking中查看分布式追踪"
    echo "  3. 配置告警规则"
    echo ""
    echo "📝 日志查看:"
    echo "  docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
}

# 主执行流程
main() {
    check_dependencies
    create_directories
    setup_environment
    configure_prometheus
    configure_grafana
    deploy_apm_services
    verify_deployment
    show_access_info
}

# 执行主函数
main "$@"