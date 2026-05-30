#!/usr/bin/env bash
# iMato Cloud Version - Docker 镜像构建脚本
# 用法：./scripts/build_docker_image.sh [选项]
# 选项:
#   --dev     开发环境构建（包含调试工具）
#   --prod    生产环境构建（默认）
#   --no-cache 不使用缓存（完全重新构建）
#   --help    显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 变量设置
IMAGE_NAME="imato-cloud"
TAG="latest"
DOCKERFILE="Dockerfile.cloud"
BUILD_ARGS=""

# 函数：显示帮助
show_help() {
    echo "iMato Cloud Docker 镜像构建脚本"
    echo ""
    echo "用法：$0 [选项]"
    echo ""
    echo "选项:"
    echo "  --dev       开发环境构建（包含调试工具，暴露更多端口）"
    echo "  --prod      生产环境构建（默认，优化体积和性能）"
    echo "  --no-cache  不使用缓存（完全重新构建）"
    echo "  --tag TAG   指定镜像标签（默认：latest）"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --prod              # 构建生产环境镜像"
    echo "  $0 --dev --no-cache    # 无缓存构建开发镜像"
    echo "  $0 --tag v1.0.0        # 构建带版本标签的镜像"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            BUILD_ARGS="--build-arg APP_ENV=development"
            TAG="dev"
            shift
            ;;
        --prod)
            BUILD_ARGS="--build-arg APP_ENV=production"
            TAG="latest"
            shift
            ;;
        --no-cache)
            BUILD_ARGS="$BUILD_ARGS --no-cache"
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项：$1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误：Docker 未运行或未启动${NC}"
    exit 1
fi

# 检查 Dockerfile 是否存在
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}错误：找不到 $DOCKERFILE${NC}"
    exit 1
fi

# 显示构建信息
echo -e "${GREEN}===================================${NC}"
echo -e "${GREEN}iMato Cloud Docker 镜像构建${NC}"
echo -e "${GREEN}===================================${NC}"
echo -e "镜像名称：${YELLOW}$IMAGE_NAME:${TAG}${NC}"
echo -e "Dockerfile: ${YELLOW}$DOCKERFILE${NC}"
echo -e "构建参数：${YELLOW}${BUILD_ARGS:-无}${NC}"
echo ""

# 进入项目根目录
cd "$(dirname "$0")/.."

# 开始构建
echo -e "${YELLOW}开始构建 Docker 镜像...${NC}"
START_TIME=$(date +%s)

docker build \
    $BUILD_ARGS \
    -f $DOCKERFILE \
    -t $IMAGE_NAME:$TAG \
    .

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 构建成功
echo ""
echo -e "${GREEN}✓ 构建成功！${NC}"
echo -e "耗时：${YELLOW}${DURATION}秒${NC}"
echo -e "镜像：${BLUE}$IMAGE_NAME:$TAG${NC}"
echo ""

# 显示镜像大小
IMAGE_SIZE=$(docker images $IMAGE_NAME:$TAG --format "{{.Size}}")
echo -e "镜像大小：${YELLOW}$IMAGE_SIZE${NC}"
echo ""

# 提示下一步
echo -e "${GREEN}下一步操作：${NC}"
echo "  1. 测试镜像：docker run --rm -p 80:80 $IMAGE_NAME:$TAG"
echo "  2. 查看日志：docker logs <container_id>"
echo "  3. 推送镜像：docker push $IMAGE_NAME:$TAG"
echo ""
