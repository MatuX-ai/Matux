#!/usr/bin/env bash
# iMato Cloud - Kubernetes 部署脚本
# 用法：./scripts/deploy-k8s.sh [选项]
# 选项:
#   --apply     应用所有配置
#   --dry-run   仅验证配置，不实际部署
#   --clean     清理所有资源（危险操作）
#   --status    查看部署状态
#   --help      显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="imato-cloud"
K8S_DIR="k8s"

# 函数：显示帮助
show_help() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}iMato Cloud Kubernetes 部署脚本${NC}"
    echo -e "${BLUE}===================================${NC}"
    echo ""
    echo "用法：$0 [选项]"
    echo ""
    echo "选项:"
    echo "  --apply     应用所有资源配置到集群"
    echo "  --dry-run   仅验证 YAML 配置，不实际部署"
    echo "  --clean     删除命名空间和所有资源（⚠️ 危险操作）"
    echo "  --status    查看部署状态和服务信息"
    echo "  --logs      查看 Pod 实时日志"
    echo "  --restart   重启所有 Deployment"
    echo "  --scale=N   扩展 Backend 副本数到 N"
    echo "  --help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --apply                    # 首次部署"
    echo "  $0 --dry-run                  # 验证配置"
    echo "  $0 --status                   # 查看状态"
    echo "  $0 --scale=5                  # 扩展到 5 副本"
    echo "  $0 --clean && $0 --apply      # 完全重置"
    echo ""
}

# 函数：检查 kubectl
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}错误：kubectl 未安装${NC}"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}错误：无法连接到 Kubernetes 集群${NC}"
        echo -e "${YELLOW}请确保已配置 kubeconfig 并且集群可访问${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Kubernetes 集群连接正常${NC}"
}

# 函数：验证 YAML
validate_yaml() {
    echo -e "${YELLOW}[1/2] 验证 YAML 配置...${NC}"

    for file in "$K8S_DIR"/*.yaml; do
        if [ -f "$file" ]; then
            echo -e "  验证：${BLUE}$(basename $file)${NC}"
            kubectl apply --dry-run=client -f "$file" || {
                echo -e "${RED}✗ 验证失败：$file${NC}"
                exit 1
            }
        fi
    done

    echo -e "${GREEN}✓ 所有 YAML 配置验证通过${NC}"
}

# 函数：应用配置
apply_config() {
    echo -e "${GREEN}===================================${NC}"
    echo -e "${GREEN}部署 iMato Cloud 到 Kubernetes${NC}"
    echo -e "${GREEN}===================================${NC}"

    check_kubectl

    validate_yaml

    echo -e "${YELLOW}[2/2] 应用资源配置...${NC}"

    # 按顺序应用配置
    echo -e "${BLUE}创建 Namespace...${NC}"
    kubectl apply -f "$K8S_DIR/namespace.yaml"

    echo -e "${BLUE}创建 ConfigMap...${NC}"
    kubectl apply -f "$K8S_DIR/configmap.yaml"

    echo -e "${BLUE}创建 Secret...${NC}"
    kubectl apply -f "$K8S_DIR/secret.yaml"

    echo -e "${BLUE}创建 PVC...${NC}"
    kubectl apply -f "$K8S_DIR/pvc.yaml"

    echo -e "${BLUE}创建 Service...${NC}"
    kubectl apply -f "$K8S_DIR/service.yaml"

    echo -e "${BLUE}创建 Deployment...${NC}"
    kubectl apply -f "$K8S_DIR/deployment.yaml"

    echo -e "${BLUE}创建 Ingress...${NC}"
    kubectl apply -f "$K8S_DIR/ingress.yaml"

    echo ""
    echo -e "${GREEN}✓ 部署完成！${NC}"
    echo ""
    echo -e "${YELLOW}等待 Pod 就绪...${NC}"
    sleep 10
    kubectl get pods -n $NAMESPACE -w &

    echo ""
    echo -e "${BLUE}提示：使用 '$0 --status' 查看服务状态${NC}"
}

# 函数：查看状态
show_status() {
    echo -e "${BLUE}===================================${NC}"
    echo -e "${BLUE}iMato Cloud 部署状态${NC}"
    echo -e "${BLUE}===================================${NC}"

    echo -e "\n${YELLOW}Namespace:${NC}"
    kubectl get namespace $NAMESPACE

    echo -e "\n${YELLOW}Pods:${NC}"
    kubectl get pods -n $NAMESPACE -o wide

    echo -e "\n${YELLOW}Deployments:${NC}"
    kubectl get deployments -n $NAMESPACE

    echo -e "\n${YELLOW}Services:${NC}"
    kubectl get services -n $NAMESPACE

    echo -e "\n${YELLOW}Ingress:${NC}"
    kubectl get ingress -n $NAMESPACE

    echo -e "\n${YELLOW}PVC:${NC}"
    kubectl get pvc -n $NAMESPACE

    echo -e "\n${YELLOW}HPA:${NC}"
    kubectl get hpa -n $NAMESPACE 2>/dev/null || echo "未配置 HPA"

    echo -e "\n${YELLOW}资源配额:${NC}"
    kubectl get resourcequota -n $NAMESPACE

    echo -e "\n${YELLOW}Pod 详情:${NC}"
    kubectl describe pods -n $NAMESPACE | head -50
}

# 函数：查看日志
show_logs() {
    echo -e "${YELLOW}实时日志输出（Ctrl+C 退出）...${NC}"
    kubectl logs -n $NAMESPACE -l app=imato-backend -f
}

# 函数：重启部署
restart_deployments() {
    echo -e "${YELLOW}重启所有 Deployments...${NC}"
    kubectl rollout restart deployment -n $NAMESPACE
    echo -e "${GREEN}✓ 重启命令已发送${NC}"
}

# 函数：扩展副本
scale_replicas() {
    local replicas=$1
    echo -e "${YELLOW}扩展 Backend 副本到 $replicas...${NC}"
    kubectl scale deployment imato-backend -n $NAMESPACE --replicas=$replicas
    echo -e "${GREEN}✓ 扩展完成${NC}"
}

# 函数：清理环境
clean_environment() {
    echo -e "${RED}⚠️  警告：此操作将删除命名空间和所有资源！${NC}"
    read -p "确认继续？(yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        echo -e "${YELLOW}删除命名空间...${NC}"
        kubectl delete namespace $NAMESPACE --ignore-not-found
        echo -e "${GREEN}✓ 清理完成${NC}"
    else
        echo -e "${YELLOW}操作已取消${NC}"
    fi
}

# 解析参数
case "$1" in
    --apply)
        apply_config
        ;;
    --dry-run)
        check_kubectl
        validate_yaml
        ;;
    --clean)
        clean_environment
        ;;
    --status)
        show_status
        ;;
    --logs)
        show_logs
        ;;
    --restart)
        restart_deployments
        ;;
    --scale=*)
        scale_replicas "${1#*=}"
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
