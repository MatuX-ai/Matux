# iMato Cloud - Kubernetes 部署指南

## 📦 概述

本目录包含 iMato Cloud 在 Kubernetes 集群的完整部署配置，支持高可用、自动扩展和滚动更新。

## 🎯 特性

- ✅ **高可用部署**: 多副本 + Pod 反亲和性
- ✅ **自动水平扩展**: HPA 基于 CPU/内存使用率
- ✅ **零停机更新**: RollingUpdate 策略
- ✅ **健康检查**: Liveness/Readiness/Startup Probe
- ✅ **资源配额**: ResourceQuota + LimitRange
- ✅ **持久化存储**: PVC 数据卷
- ✅ **网络隔离**: Namespace + NetworkPolicy（可选）
- ✅ **Ingress 路由**: Nginx Ingress Controller
- ✅ **监控集成**: Prometheus + Grafana

## 📁 文件结构

```
k8s/
├── namespace.yaml          # 命名空间 + 资源配额
├── configmap.yaml          # ConfigMap 配置
├── secret.yaml             # Secret 密钥管理
├── pvc.yaml                # 持久化卷声明
├── deployment.yaml         # Deployment + HPA + PDB
├── service.yaml            # Service 服务暴露
├── ingress.yaml            # Ingress 路由规则
└── README.md               # 本文档

scripts/
├── deploy-k8s.sh           # Linux/Mac 部署脚本
└── deploy-k8s.ps1          # Windows PowerShell 部署脚本
```

## 🚀 快速开始

### 前置要求

1. **Kubernetes 集群**: v1.20+
   - Minikube（本地测试）
   - Kind（本地测试）
   - EKS/GKE/AKS（云厂商）
   - 自建集群

2. **kubectl 工具**: v1.20+
   ```bash
   # 安装 kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   ```

3. **Nginx Ingress Controller**（可选，用于外部访问）
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
   ```

### 步骤 1: 配置 kubeconfig

```bash
# 设置 KUBECONFIG 环境变量（可选）
export KUBECONFIG=~/.kube/config

# 验证集群连接
kubectl cluster-info
kubectl get nodes
```

### 步骤 2: 修改配置

#### a) 更新 Secret
```bash
# 编辑 k8s/secret.yaml，修改敏感信息：
# - DATABASE_URL（数据库密码）
# - REDIS_URL（Redis 密码）
# - SECRET_KEY（JWT 密钥）
# - OPENAI_API_KEY（API 密钥）
```

#### b) 更新 ConfigMap
```bash
# 编辑 k8s/configmap.yaml，根据实际需求调整：
# - Token 计费配置
# - AI 降级配置
# - 特性开关
```

#### c) 更新镜像地址
```bash
# 编辑 k8s/deployment.yaml，修改 image 字段：
image: your-registry/imato-cloud:latest
```

### 步骤 3: 部署应用

#### 方式一：使用部署脚本（推荐）

```bash
# Linux/Mac
./scripts/deploy-k8s.sh --apply

# Windows PowerShell
.\scripts\deploy-k8s.ps1 -apply
```

#### 方式二：手动应用配置

```bash
# 按顺序应用 YAML 文件
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### 步骤 4: 验证部署

```bash
# 查看 Pod 状态
kubectl get pods -n imato-cloud

# 查看服务状态
kubectl get services -n imato-cloud

# 查看 Ingress
kubectl get ingress -n imato-cloud

# 查看事件日志
kubectl get events -n imato-cloud --sort-by='.lastTimestamp'
```

等待所有 Pod 状态变为 `Running`。

## 🔍 访问应用

### 本地集群（Minikube/Kind）

```bash
# 获取服务 URL
minikube service imato-ingress-nginx -n imato-cloud --url

# 或使用 port-forward
kubectl port-forward svc/imato-backend -n imato-cloud 8000:8000
```

### 生产集群

根据 Ingress 配置的域名访问：
- 前端：https://app.imato.cloud
- API: https://api.imato.cloud
- Grafana: https://monitor.imato.cloud/grafana
- Prometheus: https://monitor.imato.cloud/prometheus

## 🛠️ 运维操作

### 查看部署状态

```bash
# 使用脚本
./scripts/deploy-k8s.sh --status

# 手动命令
kubectl get all -n imato-cloud
```

### 扩展副本数

```bash
# 扩展到 5 个副本
kubectl scale deployment imato-backend -n imato-cloud --replicas=5

# 或使用脚本
./scripts/deploy-k8s.sh --scale=5
```

### 滚动更新

```bash
# 更新镜像
kubectl set image deployment/imato-backend backend=imato-cloud:v2.0 -n imato-cloud

# 查看更新状态
kubectl rollout status deployment/imato-backend -n imato-cloud

# 回滚到上一版本
kubectl rollout undo deployment/imato-backend -n imato-cloud
```

### 重启服务

```bash
# 使用脚本
./scripts/deploy-k8s.sh --restart

# 手动命令
kubectl rollout restart deployment -n imato-cloud
```

### 查看日志

```bash
# 实时日志
./scripts/deploy-k8s.sh --logs

# 查看特定 Pod 日志
kubectl logs -n imato-cloud -l app=imato-backend -f

# 查看历史日志（崩溃前）
kubectl logs -n imato-cloud <pod-name> --previous
```

## 📊 监控和告警

### Prometheus 访问

```bash
kubectl port-forward svc/imato-prometheus -n imato-cloud 9090:9090
# 访问 http://localhost:9090
```

### Grafana 访问

```bash
kubectl port-forward svc/imato-grafana -n imato-cloud 3000:3000
# 访问 http://localhost:3000 (admin/admin123)
```

### 自定义指标查询

PromQL 示例：
```promql
# Backend Pod CPU 使用率
sum(rate(container_cpu_usage_seconds_total{namespace="imato-cloud"}[5m])) by (pod)

# API 请求成功率
sum(rate(http_requests_total{status=~"2.."}[5m])) / sum(rate(http_requests_total[5m]))

# 数据库连接池使用率
pg_stat_activity_count / pg_settings_max_connections
```

## 🐛 故障排查

### Pod 无法启动

```bash
# 查看 Pod 详情
kubectl describe pod <pod-name> -n imato-cloud

# 查看日志
kubectl logs <pod-name> -n imato-cloud

# 进入容器调试
kubectl exec -it <pod-name> -n imato-cloud -- /bin/bash
```

### 常见问题

#### 问题 1: ImagePullBackOff
```bash
# 检查镜像地址和密钥
kubectl get secret imato-registry-secret -n imato-cloud -o yaml
kubectl describe pod <pod-name> -n imato-cloud | grep -i pull
```

#### 问题 2: CrashLoopBackOff
```bash
# 检查健康检查配置
kubectl describe pod <pod-name> -n imato-cloud | grep -A 10 Liveness

# 检查环境变量
kubectl exec <pod-name> -n imato-cloud -- env | grep DATABASE
```

#### 问题 3: Pending 状态
```bash
# 检查资源配额
kubectl describe resourcequota -n imato-cloud

# 检查节点资源
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

## 🔒 安全最佳实践

### 1. Secret 加密
```bash
# 使用 SealedSecrets（推荐）
kubectl create secret generic imato-secrets --from-literal=key=value \
  --dry-run=client -o yaml | kubeseal > sealed-secret.yaml

# 或使用外部密钥管理（AWS Secrets Manager 等）
```

### 2. 网络策略
```yaml
# 限制 Pod 间通信
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: imato-cloud
spec:
  podSelector:
    matchLabels:
      app: imato-backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: nginx-ingress
      ports:
        - protocol: TCP
          port: 8000
```

### 3. Pod 安全上下文
已在 deployment.yaml 中配置：
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

## 📈 性能优化

### 1. 资源请求调整
根据实际负载调整 requests/limits：
```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
  limits:
    cpu: "1000m"
    memory: "512Mi"
```

### 2. HPA 参数优化
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # 缩容稳定窗口
  scaleUp:
    stabilizationWindowSeconds: 0    # 扩容立即执行
```

### 3. 节点亲和性
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: workload-type
              operator: In
              values:
                - backend
```

## 🔄 CI/CD 集成

### GitHub Actions 示例
```yaml
name: Deploy to Kubernetes

on:
  push:
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      
      - name: Update image
        run: |
          kubectl set image deployment/imato-backend \
            backend=my-registry/imato-cloud:${GITHUB_REF#refs/tags/} \
            -n imato-cloud
      
      - name: Verify deployment
        run: |
          kubectl rollout status deployment/imato-backend -n imato-cloud
```

## 📚 相关文档

- [Docker 部署指南](../docker/README.md)
- [Docker Compose 编排](../docker-compose.cloud.yml)
- [监控系统集成](../docs/MONITORING_SETUP.md)

## 🆘 获取帮助

如遇到问题：
1. 查看本文档的故障排查部分
2. 检查 Pod 日志：`kubectl logs <pod-name> -n imato-cloud`
3. 查看事件：`kubectl get events -n imato-cloud`
4. 提交 Issue 到项目仓库

---

**最后更新**: 2026-03-14  
**维护者**: iMato Team
