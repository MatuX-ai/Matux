#!/bin/bash
# 教育数据联邦学习系统生产环境部署脚本
# Production Deployment Script for Education Data Federated Learning System

set -e  # 遇到错误立即退出

# 配置变量
PROJECT_NAME="edu-federated-learning"
DEPLOY_ENV="production"
VERSION="1.0.0"
DEPLOY_TIME=$(date '+%Y%m%d_%H%M%S')

# 目录配置
INSTALL_DIR="/opt/${PROJECT_NAME}"
CONFIG_DIR="/etc/${PROJECT_NAME}"
LOG_DIR="/var/log/${PROJECT_NAME}"
DATA_DIR="/var/lib/${PROJECT_NAME}"

# 用户配置
SERVICE_USER="edufl"
SERVICE_GROUP="edufl"

# 日志配置
LOG_FILE="${LOG_DIR}/deployment_${DEPLOY_TIME}.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此脚本需要root权限运行"
    fi
}

# 创建必要的目录
create_directories() {
    log "创建系统目录..."

    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR"

    # 设置目录权限
    chown -R "$SERVICE_USER":"$SERVICE_GROUP" "$INSTALL_DIR" "$LOG_DIR" "$DATA_DIR" 2>/dev/null || true
    chmod 755 "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR"

    success "目录创建完成"
}

# 创建系统用户
create_system_user() {
    log "创建系统用户..."

    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
        success "系统用户 $SERVICE_USER 创建成功"
    else
        warning "系统用户 $SERVICE_USER 已存在"
    fi
}

# 安装依赖
install_dependencies() {
    log "安装系统依赖..."

    # 更新包管理器
    if command -v apt-get &>/dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv nginx supervisor redis-server
    elif command -v yum &>/dev/null; then
        yum update -y
        yum install -y python3 python3-pip nginx supervisor redis
    else
        error "不支持的操作系统包管理器"
    fi

    success "系统依赖安装完成"
}

# 部署应用程序
deploy_application() {
    log "部署应用程序..."

    # 创建Python虚拟环境
    python3 -m venv "$INSTALL_DIR/venv"

    # 激活虚拟环境并安装依赖
    source "$INSTALL_DIR/venv/bin/activate"

    # 升级pip
    pip install --upgrade pip

    # 安装应用依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # 安装核心依赖
        pip install fastapi uvicorn[standard] pydantic pysyft torch tensorflow opacus
        pip install pandas numpy scikit-learn matplotlib seaborn plotly
        pip install jinja2 pdfkit openpyxl
        pip install redis celery kubernetes
    fi

    # 复制应用文件
    if [ -d "backend" ]; then
        cp -r backend/* "$INSTALL_DIR/"
    fi

    # 设置权限
    chown -R "$SERVICE_USER":"$SERVICE_GROUP" "$INSTALL_DIR"

    success "应用程序部署完成"
}

# 配置环境变量
configure_environment() {
    log "配置环境变量..."

    cat > "$CONFIG_DIR/.env" << EOF
# 教育数据联邦学习系统环境配置
# Education Data Federated Learning System Configuration

# 基础配置
APP_NAME=Education Data Federated Learning
APP_VERSION=${VERSION}
ENVIRONMENT=${DEPLOY_ENV}
DEBUG=False
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://edufl:password@localhost:5432/edu_federated
REDIS_URL=redis://localhost:6379/1

# 联邦学习配置
FL_PRIVACY_EPSILON=1.0
FL_NOISE_MULTIPLIER=1.1
FL_CLIPPING_THRESHOLD=1.0
FL_MAX_ROUNDS=50
FL_TIMEOUT_SECONDS=7200
FL_MIN_PARTICIPANTS=3

# 教育数据配置
EDU_DATA_PRIVACY_LEVEL=high
EDU_SUBJECTS=math,science,technology,engineering
EDU_GRADE_LEVELS=elementary,middle,high

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=${LOG_DIR}/application.log

# 监控配置
ENABLE_MONITORING=True
METRICS_PORT=9090

# SSL配置
SSL_CERTIFICATE=/etc/ssl/certs/edufl.crt
SSL_PRIVATE_KEY=/etc/ssl/private/edufl.key
EOF

    chown "$SERVICE_USER":"$SERVICE_GROUP" "$CONFIG_DIR/.env"
    chmod 600 "$CONFIG_DIR/.env"

    success "环境变量配置完成"
}

# 配置系统服务
configure_system_service() {
    log "配置系统服务..."

    # 创建systemd服务文件
    cat > "/etc/systemd/system/${PROJECT_NAME}.service" << EOF
[Unit]
Description=Education Data Federated Learning Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${CONFIG_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd配置
    systemctl daemon-reload

    success "系统服务配置完成"
}

# 配置Web服务器
configure_web_server() {
    log "配置Web服务器..."

    # 配置Nginx反向代理
    cat > "/etc/nginx/sites-available/${PROJECT_NAME}" << EOF
upstream edu_federated_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;

    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/ssl/certs/edufl.crt;
    ssl_certificate_key /etc/ssl/private/edufl.key;

    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://edu_federated_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件处理
    location /static/ {
        alias ${INSTALL_DIR}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查端点
    location /health {
        access_log off;
        proxy_pass http://edu_federated_backend;
    }
}
EOF

    # 启用站点
    ln -sf "/etc/nginx/sites-available/${PROJECT_NAME}" "/etc/nginx/sites-enabled/"

    # 测试Nginx配置
    nginx -t

    success "Web服务器配置完成"
}

# 配置监控和告警
configure_monitoring() {
    log "配置监控系统..."

    # 安装监控依赖
    pip install prometheus-client

    # 创建监控配置
    cat > "$CONFIG_DIR/monitoring.yml" << EOF
# 监控配置
scrape_configs:
  - job_name: 'edu_federated_learning'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "alert_rules.yml"
EOF

    # 创建告警规则
    cat > "$CONFIG_DIR/alert_rules.yml" << EOF
groups:
  - name: edu_federated_alerts
    rules:
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) > 0.8
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "进程CPU使用率超过80%"

      - alert: LowMemory
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "内存不足"
          description: "可用内存低于10%"

      - alert: TrainingFailureRate
        expr: rate(training_failures_total[10m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "训练失败率过高"
          description: "联邦学习训练失败率超过5%"
EOF

    success "监控系统配置完成"
}

# 配置备份策略
configure_backup() {
    log "配置备份策略..."

    # 创建备份脚本
    cat > "/usr/local/bin/edufl-backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/edu_federated"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# 备份数据库
pg_dump edu_federated > "$BACKUP_DIR/db_backup_$DATE.sql"

# 备份配置文件
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" /etc/edu-federated-learning/

# 备份重要数据
tar -czf "$BACKUP_DIR/data_backup_$DATE.tar.gz" /var/lib/edu-federated-learning/

# 清理旧备份
find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 记录备份日志
echo "$(date): Backup completed" >> /var/log/edu-federated-learning/backup.log
EOF

    chmod +x "/usr/local/bin/edufl-backup.sh"

    # 配置cron定时任务
    echo "0 2 * * * /usr/local/bin/edufl-backup.sh" | crontab -

    success "备份策略配置完成"
}

# 启动服务
start_services() {
    log "启动系统服务..."

    # 启动基础服务
    systemctl start redis
    systemctl start nginx

    # 启动应用服务
    systemctl start "${PROJECT_NAME}"

    # 设置开机自启
    systemctl enable redis
    systemctl enable nginx
    systemctl enable "${PROJECT_NAME}"

    # 检查服务状态
    sleep 5
    if systemctl is-active --quiet "${PROJECT_NAME}"; then
        success "应用服务启动成功"
    else
        error "应用服务启动失败"
    fi

    success "所有服务启动完成"
}

# 健康检查
health_check() {
    log "执行健康检查..."

    # 检查应用是否响应
    for i in {1..30}; do
        if curl -f -s "http://localhost:8000/health" > /dev/null; then
            success "应用健康检查通过"
            return 0
        fi
        sleep 2
    done

    error "应用健康检查失败"
}

# 部署后清理
cleanup() {
    log "执行部署后清理..."

    # 清理临时文件
    rm -rf /tmp/edu_deploy_*

    # 清理包缓存
    if command -v apt-get &>/dev/null; then
        apt-get clean
    elif command -v yum &>/dev/null; then
        yum clean all
    fi

    success "清理完成"
}

# 主部署流程
main() {
    echo "==============================================="
    echo "教育数据联邦学习系统生产环境部署"
    echo "Education Data Federated Learning System Deployment"
    echo "版本: ${VERSION}"
    echo "环境: ${DEPLOY_ENV}"
    echo "时间: ${DEPLOY_TIME}"
    echo "==============================================="

    # 检查权限
    check_root

    # 创建日志文件
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    log "开始部署流程..."

    # 执行部署步骤
    create_system_user
    create_directories
    install_dependencies
    deploy_application
    configure_environment
    configure_system_service
    configure_web_server
    configure_monitoring
    configure_backup
    start_services
    health_check
    cleanup

    echo ""
    echo "==============================================="
    success "部署完成!"
    echo "部署详情:"
    echo "- 应用目录: ${INSTALL_DIR}"
    echo "- 配置目录: ${CONFIG_DIR}"
    echo "- 日志目录: ${LOG_DIR}"
    echo "- 数据目录: ${DATA_DIR}"
    echo "- 服务名称: ${PROJECT_NAME}"
    echo "- 访问地址: https://your-domain.com"
    echo "- 健康检查: https://your-domain.com/health"
    echo "- API文档: https://your-domain.com/docs"
    echo ""
    echo "部署日志: ${LOG_FILE}"
    echo "==============================================="
}

# 错误处理
trap 'error "部署过程中发生错误，请检查日志: $LOG_FILE"' ERR

# 执行主函数
main "$@"
