# iMato Cloud - Kubernetes 部署脚本 (PowerShell)
# 用法：.\scripts\deploy-k8s.ps1 [选项]
# 示例:
#   .\scripts\deploy-k8s.ps1 -apply      # 首次部署
#   .\scripts\deploy-k8s.ps1 -status     # 查看状态
#   .\scripts\deploy-k8s.ps1 -scale 5    # 扩展到 5 副本

param(
    [switch]$apply,
    [switch]$dryRun,
    [switch]$clean,
    [switch]$status,
    [switch]$logs,
    [switch]$restart,
    [string]$scale,
    [switch]$help
)

$NAMESPACE = "imato-cloud"
$K8S_DIR = "k8s"

# 颜色函数
function Write-Info { Write-Host $args[0] -ForegroundColor Blue }
function Write-Success { Write-Host $args[0] -ForegroundColor Green }
function Write-Warning-Custom { Write-Host $args[0] -ForegroundColor Yellow }
function Write-Error-Custom { Write-Host $args[0] -ForegroundColor Red }

# 显示帮助
function Show-Help {
    Write-Info "==================================="
    Write-Info "iMato Cloud Kubernetes 部署脚本"
    Write-Info "==================================="
    Write-Host ""
    Write-Host "用法：.\scripts\deploy-k8s.ps1 [选项]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -apply      应用所有资源配置到集群"
    Write-Host "  -dryRun     仅验证 YAML 配置，不实际部署"
    Write-Host "  -clean      删除命名空间和所有资源（⚠️ 危险操作）"
    Write-Host "  -status     查看部署状态和服务信息"
    Write-Host "  -logs       查看 Pod 实时日志"
    Write-Host "  -restart    重启所有 Deployment"
    Write-Host "  -scale=N    扩展 Backend 副本数到 N"
    Write-Host "  -help       显示此帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\scripts\deploy-k8s.ps1 -apply     # 首次部署"
    Write-Host "  .\scripts\deploy-k8s.ps1 -dryRun    # 验证配置"
    Write-Host "  .\scripts\deploy-k8s.ps1 -status    # 查看状态"
    Write-Host "  .\scripts\deploy-k8s.ps1 -scale 5   # 扩展到 5 副本"
    Write-Host ""
}

# 检查 kubectl
function Check-Kubectl {
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "错误：kubectl 未安装"
        exit 1
    }

    try {
        $null = kubectl cluster-info 2>&1
    } catch {
        Write-Error-Custom "错误：无法连接到 Kubernetes 集群"
        Write-Warning-Custom "请确保已配置 kubeconfig 并且集群可访问"
        exit 1
    }

    Write-Success "✓ Kubernetes 集群连接正常"
}

# 验证 YAML
function Validate-Yaml {
    Write-Warning-Custom "[1/2] 验证 YAML 配置..."

    $files = Get-ChildItem -Path "$K8S_DIR\*.yaml"
    foreach ($file in $files) {
        Write-Host "  验证：$($file.Name)" -ForegroundColor Cyan
        $result = kubectl apply --dry-run=client -f $file.FullName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "✗ 验证失败：$($file.Name)"
            Write-Error-Custom $result
            exit 1
        }
    }

    Write-Success "✓ 所有 YAML 配置验证通过"
}

# 应用配置
function Apply-Config {
    Write-Success "==================================="
    Write-Success "部署 iMato Cloud 到 Kubernetes"
    Write-Success "==================================="

    Check-Kubectl
    Validate-Yaml

    Write-Warning-Custom "[2/2] 应用资源配置..."

    # 按顺序应用配置
    Write-Info "创建 Namespace..."
    kubectl apply -f "$K8S_DIR/namespace.yaml"

    Write-Info "创建 ConfigMap..."
    kubectl apply -f "$K8S_DIR/configmap.yaml"

    Write-Info "创建 Secret..."
    kubectl apply -f "$K8S_DIR/secret.yaml"

    Write-Info "创建 PVC..."
    kubectl apply -f "$K8S_DIR/pvc.yaml"

    Write-Info "创建 Service..."
    kubectl apply -f "$K8S_DIR/service.yaml"

    Write-Info "创建 Deployment..."
    kubectl apply -f "$K8S_DIR/deployment.yaml"

    Write-Info "创建 Ingress..."
    kubectl apply -f "$K8S_DIR/ingress.yaml"

    Write-Host ""
    Write-Success "✓ 部署完成！"
    Write-Host ""
    Write-Warning-Custom "等待 Pod 就绪..."
    Start-Sleep -Seconds 10

    Write-Info "提示：使用 '.\scripts\deploy-k8s.ps1 -status' 查看服务状态"
}

# 查看状态
function Show-Status {
    Write-Info "==================================="
    Write-Info "iMato Cloud 部署状态"
    Write-Info "==================================="

    Write-Host "`nNamespace:" -ForegroundColor Cyan
    kubectl get namespace $NAMESPACE

    Write-Host "`nPods:" -ForegroundColor Cyan
    kubectl get pods -n $NAMESPACE -o wide

    Write-Host "`nDeployments:" -ForegroundColor Cyan
    kubectl get deployments -n $NAMESPACE

    Write-Host "`nServices:" -ForegroundColor Cyan
    kubectl get services -n $NAMESPACE

    Write-Host "`nIngress:" -ForegroundColor Cyan
    kubectl get ingress -n $NAMESPACE

    Write-Host "`nPVC:" -ForegroundColor Cyan
    kubectl get pvc -n $NAMESPACE

    Write-Host "`nHPA:" -ForegroundColor Cyan
    kubectl get hpa -n $NAMESPACE 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "未配置 HPA" -ForegroundColor Yellow }

    Write-Host "`n资源配额:" -ForegroundColor Cyan
    kubectl get resourcequota -n $NAMESPACE
}

# 查看日志
function Show-Logs {
    Write-Warning-Custom "实时日志输出（Ctrl+C 退出）..."
    kubectl logs -n $NAMESPACE -l app=imato-backend -f
}

# 重启部署
function Restart-Deployments {
    Write-Warning-Custom "重启所有 Deployments..."
    kubectl rollout restart deployment -n $NAMESPACE
    Write-Success "✓ 重启命令已发送"
}

# 扩展副本
function Scale-Replicas {
    param([string]$replicas)

    Write-Warning-Custom "扩展 Backend 副本到 $replicas..."
    kubectl scale deployment imato-backend -n $NAMESPACE --replicas=$replicas
    Write-Success "✓ 扩展完成"
}

# 清理环境
function Clean-Environment {
    Write-Error-Custom "⚠️  警告：此操作将删除命名空间和所有资源！"
    $confirm = Read-Host "确认继续？(yes/no)"

    if ($confirm -eq "yes") {
        Write-Warning-Custom "删除命名空间..."
        kubectl delete namespace $NAMESPACE -IgnoreNotFound
        Write-Success "✓ 清理完成"
    } else {
        Write-Warning-Custom "操作已取消"
    }
}

# 主逻辑
if ($apply) {
    Apply-Config
} elseif ($dryRun) {
    Check-Kubectl
    Validate-Yaml
} elseif ($clean) {
    Clean-Environment
} elseif ($status) {
    Show-Status
} elseif ($logs) {
    Show-Logs
} elseif ($restart) {
    Restart-Deployments
} elseif ($scale) {
    Scale-Replicas -replicas $scale
} elseif ($help) {
    Show-Help
} else {
    Write-Error-Custom "未知选项"
    Show-Help
    exit 1
}
