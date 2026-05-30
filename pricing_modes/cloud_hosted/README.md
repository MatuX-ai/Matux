# iMato 云托管版 - 运维文档

**版本**: v1.0  
**类型**: SaaS 年费订阅 + Token 消耗  
**目标用户**: 大型机构、企业、教育局

---

## ☁️ 部署架构

### **生产环境架构**

```
                    ┌─────────────────┐
                    │   Cloudflare    │
                    │      CDN        │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                              │
    ┌─────────▼─────────┐         ┌─────────▼─────────┐
    │  Nginx Ingress    │         │  Nginx Ingress    │
    │   (Primary)       │         │   (Secondary)     │
    └─────────┬─────────┘         └─────────┬─────────┘
              │                              │
    ┌─────────▼─────────────────────────────▼─────────┐
    │           Kubernetes Cluster                     │
    │  ┌──────────────┐  ┌──────────────┐             │
    │  │   Frontend   │  │   Frontend   │  (Pods x3)  │
    │  │  Deployment  │  │  Deployment  │             │
    │  └──────────────┘  └──────────────┘             │
    │  ┌──────────────┐  ┌──────────────┐             │
    │  │   Backend    │  │   Backend    │  (Pods x5)  │
    │  │  Deployment  │  │  Deployment  │             │
    │  └──────────────┘  └──────────────┘             │
    │  ┌──────────────┐                               │
    │  │    Redis     │  (Cache & Session)            │
    │  │  StatefulSet │                               │
    │  └──────────────┘                               │
    └─────────────────────────────────────────────────┘
              │
    ┌─────────▼─────────┐
    │  PostgreSQL DB    │
    │  (Managed RDS)    │
    └───────────────────┘
```

---

## 📂 目录结构

```
cloud_hosted/
├── docker/                   # Docker 配置
│   ├── Dockerfile.cloud     # 生产镜像
│   ├── docker-compose.cloud.yml
│   └── .env.production.example
│
├── k8s/                      # Kubernetes 配置
│   ├── namespace.yaml       # 命名空间
│   ├── deployment.yaml      # 应用部署
│   ├── service.yaml         # 服务暴露
│   ├── ingress.yaml         # 入口路由
│   ├── configmap.yaml       # 配置文件
│   ├── secret.yaml          # 敏感信息
│   ├── pvc.yaml             # 持久化存储
│   └── hpa.yaml             # 自动扩缩容
│
├── monitoring/               # 监控配置
│   ├── prometheus/
│   │   ├── prometheus.yml   # Prometheus 配置
│   │   └── rules/           # 告警规则
│   └── grafana/
│       ├── dashboards/      # Grafana 仪表盘
│       └── datasources/     # 数据源配置
│
└── docs/                     # 运维文档
    ├── DEPLOYMENT.md        # 部署指南
    ├── MONITORING.md        # 监控手册
    ├── BACKUP.md            # 备份策略
    └── SCALING.md           # 扩容方案
```

---

## 💰 价格方案

### **基础套餐**
- **年费**: ¥300/年
- **包含**: 
  - 云端托管服务
  - 每月 1000 Token 赠送
  - 10GB 存储空间
  - 基础技术支持

### **Token 套餐**（额外购买）
| 套餐 | Token 数量 | 价格 | 备注 |
|------|-----------|------|------|
| 标准包 | 1000 | ¥99 | 有效期 1 年 |
| 高级包 | 3000 | ¥249 | 有效期 1 年 |
| 企业包 | 10000 | ¥699 | 有效期 1 年 |

---

## 🚀 一键部署

### **前提条件**
- Kubernetes 集群 (v1.25+)
- Helm 3.x
- 已配置的 StorageClass
- 外部 PostgreSQL 数据库（或云数据库 RDS）

### **快速部署脚本**

```bash
cd pricing_modes/cloud_hosted

# 1. 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 2. 配置 Secret 和 ConfigMap
kubectl create secret generic imato-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/imato" \
  --from-literal=jwt-secret="your-jwt-secret" \
  -n imato-cloud

# 3. 应用所有配置
kubectl apply -f k8s/ -n imato-cloud

# 4. 查看部署状态
kubectl get pods -n imato-cloud

# 5. 获取访问地址
kubectl get ingress -n imato-cloud
```

---

## 📊 资源配置

### **Frontend (Angular)**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
replicas: 3  # 最小可用实例数
```

### **Backend (FastAPI)**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
replicas: 5  # 支持 500+ 并发用户
```

### **Database (PostgreSQL)**
- **推荐**: AWS RDS / 阿里云 RDS
- **配置**: 2 核 4GB，SSD 存储
- **备份**: 每日自动备份，保留 7 天

---

## 🔍 监控指标

### **核心指标**
- API 响应时间（P95 < 200ms）
- 错误率（< 0.1%）
- CPU 使用率（< 70%）
- 内存使用率（< 80%）
- 数据库连接池（< 80%）

### **业务指标**
- Token 消耗速率
- 活跃用户数
- AI 功能调用次数
- 课程生成成功率

---

## 🛡️ 安全加固

### **网络安全**
- ✅ HTTPS/TLS 加密传输
- ✅ NetworkPolicy 网络隔离
- ✅ WAF Web 应用防火墙
- ✅ DDoS 防护

### **数据安全**
- ✅ 数据库加密存储
- ✅ 敏感信息加密（AES-256）
- ✅ 定期安全审计
- ✅ 访问日志留存 6 个月

### **认证授权**
- ✅ JWT Token 认证
- ✅ RBAC 权限控制
- ✅ OAuth2 第三方登录
- ✅ 双因素认证（可选）

---

## 🔄 持续集成/持续部署

### **CI/CD流程**

```mermaid
graph LR
    A[Git Push] --> B[GitHub Actions]
    B --> C[构建 Docker 镜像]
    C --> D[推送到镜像仓库]
    D --> E[更新 K8s 部署]
    E --> F[健康检查]
    F --> G[流量切换]
    G --> H[部署完成]
```

### **自动化测试**
- 单元测试覆盖率 > 80%
- 集成测试全通过
- 性能测试达标（P95 < 300ms）
- 安全扫描无高危漏洞

---

## 📞 技术支持

- **工单系统**: support@imato.com
- **紧急联系**: 400-XXX-XXXX
- **SLA**: 99.9% 可用性保证
- **响应时间**: 
  - P0（严重）: 15 分钟响应
  - P1（高）: 1 小时响应
  - P2（中）: 4 小时响应
  - P3（低）: 24 小时响应

---

## 📄 服务协议

详见 `docs/SERVICE_LEVEL_AGREEMENT.pdf`

**关键条款**:
- 月度停机时间 < 43 分钟
- 数据持久性 > 99.999999%
- 支持弹性扩缩容
- 7 天无理由退款
