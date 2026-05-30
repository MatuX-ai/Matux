#!/usr/bin/env bash
# iMato Cloud - 一键部署启动脚本
# 用法：./scripts/deploy-cloud.sh [选项]
# 选项:
#   --start     启动所有服务
#   --stop      停止所有服务
#   --restart   重启所有服务
#   --status    查看服务状态
#   --logs      查看实时日志
#   --clean     清理容器和卷（危险操作）
#   --help      显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 变量设置
COMPOSE_FILE="docker-compose.cloud.yml"
PROJECT_NAME="imato-cloud"

# 函数：显示帮助
show_help() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}iMato Cloud 一键部署脚本${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo ""
    echo "用法：$0 [选项]"
    echo ""
    echo "选项:"
    echo "  --start     启动所有服务（包括构建镜像）"
    echo "  --stop      停止所有服务（保留数据）"
    echo "  --restart   重启所有服务"
    echo "  --status    查看所有服务运行状态"
    echo "  --logs      查看实时日志（支持 Ctrl+C 退出）"
    echo "  --clean     清理所有容器、网络和卷（⚠️ 危险操作，数据将丢失）"
    echo "  --build     仅构建镜像，不启动服务"
    echo "  --scale     扩展后端服务副本数（需配合 --scale=n）"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --start                    # 首次部署启动"
    echo "  $0 --restart                  # 重启服务"
    echo "  $0 --status                   # 查看状态"
    echo "  $0 --logs                     # 查看日志"
    echo "  $0 --clean && $0 --start      # 完全重置环境"
    echo ""
}

# 函数：检查 Docker
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}错误：Docker 未运行${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误：docker-compose 未安装${NC}"
        exit 1
    fi
}

# 函数：检查配置文件
check_config() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}错误：找不到 $COMPOSE_FILE${NC}"
        exit 1
    fi

    if [ ! -f "docker/.env.production" ]; then
        echo -e "${YELLOW}警告：未找到 docker/.env.production 文件${NC}"
        echo -e "${YELLOW}建议：cp docker/.env.example docker/.env.production${NC}"
        echo ""
    fi
}

# 函数：启动服务
start_services() {
    echo -e "${GREEN}===================================${NC}"
    echo -e "${GREEN}启动 iMato Cloud 服务...${NC}"
    echo -e "${GREEN}===================================${NC}"

    check_config

    echo -e "${YELLOW}[1/3] 构建 Docker 镜像...${NC}"
    docker-compose -f $COMPOSE_FILE build

    echo -e "${YELLOW}[2/3] 启动所有服务...${NC}"
    docker-compose -f $COMPOSE_FILE up -d

    echo -e "${YELLOW}[3/3] 等待服务健康检查...${NC}"
    sleep 10

    echo -e "${GREEN}✓ 服务启动完成！${NC}"
    echo ""
    echo -e "${BLUE}访问地址：${NC}"
    echo "  前端应用：http://localhost"
    echo "  API 端点：http://localhost/api/v1"
    echo "  Grafana: http://localhost:3000 (admin/admin123)"
    echo "  Prometheus: http://localhost:9090"
    echo ""
    echo -e "${YELLOW}提示：使用 '$0 --status' 查看服务状态${NC}"
}

# 函数：停止服务
stop_services() {
    echo -e "${YELLOW}停止所有服务...${NC}"
    docker-compose -f $COMPOSE_FILE stop
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

# 函数：重启服务
restart_services() {
    echo -e "${YELLOW}重启所有服务...${NC}"
    docker-compose -f $COMPOSE_FILE restart
    echo -e "${GREEN}✓ 服务已重启${NC}"
}

# 函数：查看状态
show_status() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}iMato Cloud 服务状态${NC}"
    echo -e "${BLUE}===================================${NC}"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    echo -e "${BLUE}资源占用：${NC}"
    docker stats --no-stream
}

# 函数：查看日志
show_logs() {
    echo -e "${YELLOW}实时日志输出（Ctrl+C 退出）...${NC}"
    docker-compose -f $COMPOSE_FILE logs -f
}

# 函数：清理环境
clean_environment() {
    echo -e "${RED}⚠️  警告：此操作将删除所有容器、网络和数据卷！${NC}"
    read -p "确认继续？(yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}停止服务...${NC}"
        docker-compose -f $COMPOSE_FILE down -v
        echo -e "${YELLOW}清理悬空镜像...${NC}"
        docker image prune -f
        echo -e "${GREEN}✓ 清理完成${NC}"
    else
        echo -e "${YELLOW}操作已取消${NC}"
    fi
}

# 函数：构建镜像
build_images() {
    echo -e "${YELLOW}构建 Docker 镜像...${NC}"
    docker-compose -f $COMPOSE_FILE build
    echo -e "${GREEN}✓ 构建完成${NC}"
}

# 解析参数
case "$1" in
    --start)
        check_docker
        start_services
        ;;
    --stop)
        stop_services
        ;;
    --restart)
        restart_services
        ;;
    --status)
        show_status
        ;;
    --logs)
        show_logs
        ;;
    --clean)
        clean_environment
        ;;
    --build)
        build_images
        ;;
    --help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知选项：$1${NC}"
        show_help
        exit 1
        ;;
esac
