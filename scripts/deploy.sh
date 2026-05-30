#!/bin/bash

# iMato AI Service 部署脚本

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[INFO]$(date '+%Y-%m-%d %H:%M:%S')${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]$(date '+%Y-%m-%d %H:%M:%S')${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]$(date '+%Y-%m-%d %H:%M:%S')${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]$(date '+%Y-%m-%d %H:%M:%S')${NC} $1"
}

# 检查必需命令
check_dependencies() {
    log "检查系统依赖..."
    
    local deps=("docker" "docker-compose" "git")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "缺少必需的依赖: ${missing_deps[*]}"
        error "请先安装这些依赖后再运行部署脚本"
        exit 1
    fi
    
    success "所有依赖检查通过"
}

# 检查环境变量
check_env_vars() {
    log "检查环境变量..."
    
    local required_vars=(
        "SECRET_KEY"
        "OPENAI_API_KEY"
        "LINGMA_API_KEY"
        "DEEPSEEK_API_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        warning "以下环境变量未设置: ${missing_vars[*]}"
        warning "请在 .env.production 文件中设置这些变量"
    fi
    
    success "环境变量检查完成"
}

# 构建应用
build_app() {
    log "构建应用镜像..."
    
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        success "应用镜像构建成功"
    else
        error "应用镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log "启动服务..."
    
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        success "服务启动成功"
    else
        error "服务启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    log "等待服务启动..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            success "服务已就绪"
            return 0
        fi
        
        log "等待服务启动... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error "服务启动超时"
    return 1
}

# 运行数据库迁移
run_migrations() {
    log "运行数据库迁移..."
    
    docker-compose exec ai-backend alembic upgrade head
    
    if [ $? -eq 0 ]; then
        success "数据库迁移完成"
    else
        warning "数据库迁移失败，请手动检查"
    fi
}

# 创建备份
create_backup() {
    log "创建部署前备份..."
    
    local backup_dir="./backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="backup_$timestamp"
    
    mkdir -p "$backup_dir"
    
    # 备份数据库
    if docker-compose ps postgres | grep -q "Up"; then
        docker-compose exec postgres pg_dump -U postgres ai_service > "$backup_dir/${backup_name}_database.sql"
        success "数据库备份已创建: $backup_dir/${backup_name}_database.sql"
    fi
    
    # 备份配置文件
    cp .env.production "$backup_dir/${backup_name}_config.env" 2>/dev/null || true
    
    success "备份完成"
}

# 运行健康检查
run_health_check() {
    log "运行健康检查..."
    
    local checks=(
        "http://localhost:8000/health"
        "http://localhost:8000/docs"
    )
    
    local failed_checks=0
    
    for check in "${checks[@]}"; do
        if curl -f "$check" &> /dev/null; then
            success "健康检查通过: $check"
        else
            error "健康检查失败: $check"
            ((failed_checks++))
        fi
    done
    
    if [ $failed_checks -eq 0 ]; then
        success "所有健康检查通过"
        return 0
    else
        error "部分健康检查失败"
        return 1
    fi
}

# 显示部署信息
show_deployment_info() {
    echo
    echo "=========================================="
    echo "           部署完成信息"
    echo "=========================================="
    echo "应用查看地址: http://localhost:3000"
    echo "API文档地址: http://localhost:8000/docs"
    echo "健康检查: http://localhost:8000/health"
    echo "------------------------------------------"
    echo "服务状态:"
    docker-compose ps
    echo "------------------------------------------"
    echo "后续步骤:"
    echo "1. 配置域名和SSL证书"
    echo "2. 设置监控和告警"
    echo "3. 配置日志收集"
    echo "4. 设置定期备份"
    echo "=========================================="
}

# 回滚部署
rollback() {
    error "部署失败，正在回滚..."
    
    # 停止当前服务
    docker-compose down
    
    # 恢复备份
    if [ -d "./backups" ]; then
        latest_backup=$(ls -t ./backups/backup_*_database.sql | head -n1)
        if [ -n "$latest_backup" ]; then
            log "恢复数据库备份..."
            docker-compose up -d postgres
            sleep 10
            docker-compose exec -T postgres psql -U postgres ai_service < "$latest_backup"
        fi
    fi
    
    # 启动之前的版本
    if [ -f "./docker-compose.previous.yml" ]; then
        log "恢复之前的部署..."
        docker-compose -f ./docker-compose.previous.yml up -d
    fi
    
    error "回滚完成"
    exit 1
}

# 主部署流程
main() {
    echo "=========================================="
    echo "    iMato AI Service 部署脚本"
    echo "=========================================="
    
    # 检查依赖
    check_dependencies
    
    # 检查环境变量
    check_env_vars
    
    # 创建备份
    create_backup
    
    # 备份当前配置
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml docker-compose.previous.yml
    fi
    
    # 设置错误处理
    trap rollback ERR
    
    # 构建应用
    build_app
    
    # 启动服务
    start_services
    
    # 等待服务就绪
    wait_for_services
    
    # 运行迁移
    run_migrations
    
    # 运行健康检查
    run_health_check
    
    # 显示部署信息
    show_deployment_info
    
    success "部署完成!"
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi