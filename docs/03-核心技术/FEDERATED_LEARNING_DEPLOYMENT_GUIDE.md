# 联邦学习隐私保护系统部署指南

## 部署准备

### 系统要求

#### 硬件要求
- **最小配置**: 4核CPU, 8GB内存, 50GB存储
- **推荐配置**: 8核CPU, 16GB内存, 100GB SSD存储
- **网络**: 稳定的互联网连接，带宽≥100Mbps

#### 软件依赖
```bash
# 操作系统
Ubuntu 20.04 LTS 或 CentOS 8+
Docker 20.10+
Kubernetes 1.24+

# Python环境
Python 3.8+
pip 21.0+

# 数据库
PostgreSQL 13+
Redis 6.0+
```

### 环境变量配置

创建 `.env` 文件：
```bash
# 基础配置
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# 数据库配置
DATABASE_URL=postgresql://user:password@host:5432/imato_fl
REDIS_URL=redis://localhost:6379/1

# 联邦学习配置
FL_PRIVACY_EPSILON=1.0
FL_NOISE_MULTIPLIER=1.0
FL_CLIPPING_THRESHOLD=1.0
FL_MAX_ROUNDS=100
FL_TIMEOUT_SECONDS=3600

# 安全配置
FL_JWT_SECRET=super-secret-jwt-key-here
FL_ENCRYPTION_KEY=32-byte-encryption-key-here!!
FL_TLS_ENABLED=True
FL_TLS_CERT_PATH=/etc/ssl/certs/fl-cert.pem
FL_TLS_KEY_PATH=/etc/ssl/private/fl-key.pem

# Kubernetes配置
KUBE_CONFIG_PATH=/home/user/.kube/config
FL_NAMESPACE=federated-learning
FL_SERVICE_ACCOUNT=fl-coordinator

# 监控配置
FL_MONITORING_ENABLED=True
FL_ALERT_EMAIL=admin@example.com
FL_LOG_LEVEL=INFO
```

## 部署步骤

### 1. 代码部署

```bash
# 克隆代码库
git clone https://github.com/your-org/imato.git
cd imato

# 安装Python依赖
pip install -r backend/requirements.txt

# 安装前端依赖
npm install
```

### 2. 数据库初始化

```bash
# 创建数据库
createdb imato_fl

# 运行迁移
cd backend
python setup_database.py

# 创建初始用户
python -c "
from models.user import User
from utils.database import get_db_sync
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

user = User(
    username='admin',
    email='admin@example.com',
    password_hash=pwd_context.hash('secure-password'),
    role='admin',
    is_active=True
)

db = get_db_sync()
db.add(user)
db.commit()
"
```

### 3. Kubernetes部署

#### 创建命名空间
```bash
kubectl create namespace federated-learning
```

#### 部署协调器服务
```yaml
# k8s/fl-coordinator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-coordinator
  namespace: federated-learning
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fl-coordinator
  template:
    metadata:
      labels:
        app: fl-coordinator
    spec:
      containers:
      - name: coordinator
        image: imato/fl-coordinator:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: fl-config
        - secretRef:
            name: fl-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        volumeMounts:
        - name: tls-certs
          mountPath: /etc/ssl
          readOnly: true
      volumes:
      - name: tls-certs
        secret:
          secretName: fl-tls-certs
---
apiVersion: v1
kind: Service
metadata:
  name: fl-coordinator-service
  namespace: federated-learning
spec:
  selector:
    app: fl-coordinator
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

#### 配置ConfigMap和Secret
```bash
# 创建配置
kubectl create configmap fl-config \
  --from-literal=FL_PRIVACY_EPSILON=1.0 \
  --from-literal=FL_NOISE_MULTIPLIER=1.0 \
  --from-literal=FL_MAX_ROUNDS=100 \
  --namespace=federated-learning

# 创建密钥
kubectl create secret generic fl-secrets \
  --from-literal=FL_JWT_SECRET=$(openssl rand -hex 32) \
  --from-literal=FL_ENCRYPTION_KEY=$(openssl rand -hex 16) \
  --namespace=federated-learning
```

### 4. 客户端部署

#### 客户端Docker镜像
```dockerfile
# Dockerfile.client
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ai_service/federated_learning/ ./federated_learning/
COPY backend/ai_service/fl_models.py .

CMD ["python", "-c", "
import asyncio
from federated_learning.federated_client import FederatedClient
from federated_learning.privacy_engine import PrivacyEngine

async def main():
    privacy_engine = PrivacyEngine()
    client = FederatedClient(
        participant_id='auto-generated',
        coordinator_url='http://fl-coordinator-service:8000',
        privacy_engine=privacy_engine
    )
    await client.register_with_coordinator()
    # 保持运行
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
"]
```

#### 部署客户端
```yaml
# k8s/fl-client-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-clients
  namespace: federated-learning
spec:
  replicas: 5  # 根据需求调整
  selector:
    matchLabels:
      app: fl-client
  template:
    metadata:
      labels:
        app: fl-client
    spec:
      containers:
      - name: fl-client
        image: imato/fl-client:latest
        env:
        - name: COORDINATOR_URL
          value: "http://fl-coordinator-service:8000"
        resources:
          requests:
            memory: "1Gi"
            cpu: "0.5"
          limits:
            memory: "2Gi"
            cpu: "1"
```

### 5. 网络配置

#### Ingress配置
```yaml
# k8s/fl-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fl-ingress
  namespace: federated-learning
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - fl.your-domain.com
    secretName: fl-tls
  rules:
  - host: fl.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fl-coordinator-service
            port:
              number: 8000
```

### 6. 监控部署

#### Prometheus配置
```yaml
# k8s/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: federated-learning
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      
    scrape_configs:
    - job_name: 'federated-learning'
      static_configs:
      - targets: ['fl-coordinator-service:8000']
      metrics_path: '/metrics'
```

#### Grafana仪表板
```json
{
  "dashboard": {
    "title": "联邦学习监控面板",
    "panels": [
      {
        "title": "训练进度",
        "type": "graph",
        "targets": [
          {
            "expr": "fl_training_progress_percentage",
            "legendFormat": "{{training_id}}"
          }
        ]
      },
      {
        "title": "活跃参与者数",
        "type": "stat",
        "targets": [
          {
            "expr": "fl_active_participants"
          }
        ]
      },
      {
        "title": "隐私预算消耗",
        "type": "gauge",
        "targets": [
          {
            "expr": "fl_privacy_budget_consumed"
          }
        ]
      }
    ]
  }
}
```

## 启动服务

### 1. 启动后端服务
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动前端服务
```bash
npm run start
```

### 3. 验证部署
```bash
# 检查服务状态
kubectl get pods -n federated-learning
kubectl get services -n federated-learning

# 测试API
curl -X GET "https://fl.your-domain.com/api/v1/federated/health" \
  -H "accept: application/json"

# 运行回测
python scripts/federated_learning_backtest.py
```

## 性能调优

### 1. 资源优化
```bash
# 调整容器资源限制
kubectl patch deployment fl-coordinator -n federated-learning -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "coordinator",
            "resources": {
              "requests": {"memory": "4Gi", "cpu": "2"},
              "limits": {"memory": "8Gi", "cpu": "4"}
            }
          }
        ]
      }
    }
  }
}'
```

### 2. 网络优化
```bash
# 启用HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment fl-coordinator \
  --cpu-percent=70 \
  --min=1 \
  --max=5 \
  -n federated-learning
```

### 3. 存储优化
```yaml
# 使用持久化存储
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fl-model-storage
  namespace: federated-learning
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
```

## 安全加固

### 1. 网络策略
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fl-network-policy
  namespace: federated-learning
spec:
  podSelector:
    matchLabels:
      app: fl-coordinator
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: federated-learning
    ports:
    - protocol: TCP
      port: 8000
```

### 2. 安全扫描
```bash
# 运行安全扫描
trivy image imato/fl-coordinator:latest
kube-bench --benchmark cis-1.6
```

### 3. 备份策略
```bash
# 创建备份脚本
cat > backup-fl.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
kubectl exec -n federated-learning fl-coordinator-0 -- pg_dump imato_fl > backup_$DATE.sql
kubectl cp federated-learning/fl-coordinator-0:/app/models/ models_backup_$DATE/
EOF

chmod +x backup-fl.sh
# 设置定时任务
echo "0 2 * * * /path/to/backup-fl.sh" | crontab -
```

## 故障排除

### 常见问题及解决方案

1. **服务无法启动**
```bash
# 检查Pod状态
kubectl describe pod -n federated-learning -l app=fl-coordinator

# 查看日志
kubectl logs -n federated-learning -l app=fl-coordinator --previous
```

2. **数据库连接失败**
```bash
# 检查数据库服务
kubectl get svc -n database
kubectl exec -it postgres-pod -- psql -U postgres -d imato_fl
```

3. **客户端注册失败**
```bash
# 检查网络连通性
kubectl exec -it fl-client-pod -- curl -v http://fl-coordinator-service:8000/health
```

## 维护计划

### 日常维护
- [ ] 每日检查服务状态
- [ ] 监控资源使用情况
- [ ] 审计安全日志

### 周期维护
- [ ] 每周备份数据
- [ ] 更新安全补丁
- [ ] 性能调优

### 月度维护
- [ ] 容量规划评估
- [ ] 安全渗透测试
- [ ] 灾难恢复演练

---
*部署指南版本: 1.0*  
*最后更新: 2026-02-27*