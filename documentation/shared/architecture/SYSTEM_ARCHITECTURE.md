# MatuX STEM 学习平台 - 系统架构文档

## 1. 整体架构设计

### 1.1 架构模式
MatuX 采用**微服务架构**结合**前后端分离**的设计模式，并与其他两个独立项目通过 API 集成：

> **模块解耦说明**: 课件管理已解耦至 OpenMTSciEd，机构管理已解耦至 OpenMTEduInst。学生账号三项目互联互通。

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Web浏览器     │   移动APP       │   桌面客户端            │
│  (Angular 21)   │  (Flutter)      │  (Electron 28)          │
└─────────────────┴─────────────────┴─────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      API网关层                               │
├─────────────────────────────────────────────────────────────┤
│                    Nginx + FastAPI                          │
│            负载均衡 | SSL终止 | 请求路由                     │
└─────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│  MatuX 服务层   │ │ OpenMTSciEd API │ │ OpenMTEduInst API   │
├─────────────────┤ │  (课件资源)      │ │  (机构管理)          │
│ 认证 + AI服务   │ │  localhost:3000  │ │  独立部署端点        │
│ 推荐 + 硬件认证 │ │                 │ │                     │
│ 游戏化 + 学习   │ │                 │ │                     │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      中间件层                                │
├─────────────────────────────────────────────────────────────┤
│   认证验证 | 日志记录 | 缓存 | 监控                          │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│   PostgreSQL    │   Redis         │   消息队列(RabbitMQ)    │
│   (主数据库)    │   (缓存/会话)   │   (异步任务)            │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 1.2 技术选型原则

**前端选择依据：**
- Angular 16：企业级应用，TypeScript强类型支持
- Material Design：统一的UI规范和组件库
- RxJS：响应式编程处理异步数据流

**后端选择依据：**
- FastAPI：高性能，自动生成API文档，类型提示
- Python生态：丰富的AI/ML库支持
- SQLAlchemy：成熟的ORM框架

**基础设施选择：**
- PostgreSQL：支持复杂查询和事务
- Redis：高速缓存和会话存储
- Docker：容器化部署和环境一致性

## 2. 前端架构详解

### 2.1 Angular应用结构

```
src/app/
├── app.module.ts           # 根模块
├── app-routing.module.ts   # 路由配置
├── app.component.ts        # 根组件
├── core/                   # 核心模块
│   ├── services/          # 核心服务
│   │   ├── auth.service.ts
│   │   ├── http.service.ts
│   │   └── storage.service.ts
│   └── interceptors/      # HTTP拦截器
│       └── auth.interceptor.ts
├── shared/                # 共享模块
│   ├── components/       # 共享组件
│   ├── pipes/           # 管道
│   └── directives/      # 指令
├── features/             # 功能模块
│   ├── auth/            # 认证模块
│   ├── dashboard/       # 仪表板模块
│   ├── admin/           # 管理模块
│   └── learning/        # 学习模块
└── assets/              # 静态资源
```

### 2.2 状态管理模式

```typescript
// 状态管理策略
@Injectable({
  providedIn: 'root'
})
export class AppStateService {
  private userSubject = new BehaviorSubject<User | null>(null);
  private loadingSubject = new BehaviorSubject<boolean>(false);
  
  public user$ = this.userSubject.asObservable();
  public loading$ = this.loadingSubject.asObservable();
  
  setUser(user: User) {
    this.userSubject.next(user);
  }
  
  setLoading(loading: boolean) {
    this.loadingSubject.next(loading);
  }
}
```

### 2.3 组件通信机制

```
父子组件通信:
Parent Component ──Input()──► Child Component
Child Component ──Output()──► Parent Component

兄弟组件通信:
Component A ──Service──► Component B

跨层级通信:
Root Component ──State Management──► Any Component
```

### 2.4 多后台管理架构（已解耦）

> ⚠️ 多租户后台管理架构（Platform Admin / Tenant Management / Education Bureau）已整体解耦至 **OpenMTEduInst** 项目。
>
> MatuX 仅保留学生端和家长监护视图，不再包含以下功能：
> - 平台行政管理后台
> - 机构/学校/教育局管理门户
> - 多租户权限管理
> - 许可证管理
>
> 以上功能请在 `G:\OpenMTEduInst` 项目中查看和开发。
> 详细架构文档请参考 OpenMTEduInst 项目文档。

---

## 3. 后端架构详解

### 3.1 FastAPI应用结构

```
backend/
├── main.py                 # 应用入口
├── config/                # 配置管理
│   ├── settings.py        # 应用配置
│   └── database.py        # 数据库配置
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── course.py         # 课程模型
│   └── payment.py        # 支付模型
├── schemas/               # Pydantic模型
│   ├── user_schema.py
│   └── course_schema.py
├── routes/                # 路由定义
│   ├── auth_routes.py
│   ├── course_routes.py
│   └── payment_routes.py
├── services/              # 业务逻辑层
│   ├── auth_service.py
│   ├── course_service.py
│   └── payment_service.py
├── middleware/            # 中间件
│   ├── auth_middleware.py
│   └── logging_middleware.py
└── utils/                 # 工具函数
    ├── security.py
    └── helpers.py
```

### 3.2 数据库设计

#### 核心实体关系图

```mermaid
erDiagram
    USERS ||--o{ USER_LICENSES : has
    USERS ||--o{ COURSES : creates
    USERS ||--o{ PAYMENTS : makes
    ORGANIZATIONS ||--o{ USERS : contains
    ORGANIZATIONS ||--o{ LICENSES : owns
    LICENSES ||--o{ USER_LICENSES : assigned_to
    COURSES ||--o{ ENROLLMENTS : includes
    USERS ||--o{ ENROLLMENTS : enrolled_in
    HARDWARE_DEVICES ||--|| USERS : belongs_to
    
    USERS {
        int id PK
        string username
        string email
        string password_hash
        datetime created_at
        int organization_id FK
    }
    
    ORGANIZATIONS {
        int id PK
        string name
        string domain
        datetime created_at
    }
    
    LICENSES {
        int id PK
        string license_key
        int organization_id FK
        string product_name
        datetime expiry_date
        int max_users
    }
    
    USER_LICENSES {
        int id PK
        int user_id FK
        int license_id FK
        datetime assigned_at
        boolean is_active
    }
```

### 3.3 缓存策略

```
Redis缓存层次:
├── 会话缓存 (Session Cache)
│   - 用户登录状态
│   - 权限信息
│   - TTL: 2小时
├── 数据缓存 (Data Cache)
│   - 用户信息
│   - 课程详情
│   - 配置参数
│   - TTL: 1小时
└── 计算结果缓存 (Result Cache)
    - AI生成结果
    - 推荐算法输出
    - 统计报表数据
    - TTL: 30分钟
```

## 4. 安全架构

### 4.1 认证授权体系

```
认证流程:
1. 用户提交凭据
2. 服务验证身份
3. 生成JWT Token
4. 返回Token给客户端
5. 客户端存储Token
6. 后续请求携带Token

授权检查:
请求到达 → JWT验证 → 权限检查 → 业务处理 → 响应返回
```

### 4.2 安全防护措施

```python
# 安全中间件配置
class SecurityMiddleware:
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window=60)
        self.ip_whitelist = load_ip_whitelist()
        
    async def __call__(self, request: Request, call_next):
        # IP白名单检查
        if request.client.host not in self.ip_whitelist:
            # 请求频率限制
            if not self.rate_limiter.is_allowed(request.client.host):
                raise HTTPException(status_code=429, detail="Too Many Requests")
        
        # XSS防护
        response = await call_next(request)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
```

### 4.3 数据加密

```
数据保护策略:
├── 传输加密
│   - HTTPS/TLS 1.3
│   - HSTS头部设置
├── 存储加密
│   - 密码使用bcrypt哈希
│   - 敏感字段AES加密
│   - 数据库透明加密(TDE)
└── 应用层加密
    - JWT签名密钥轮换
    - API密钥加密存储
    - 敏感配置文件加密
```

## 5. 部署架构

### 5.1 Docker容器化

```dockerfile
# 后端Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 前端Dockerfile
FROM node:16-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --silent
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 5.2 Kubernetes部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: imatu-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: imatu-backend
  template:
    metadata:
      labels:
        app: imatu-backend
    spec:
      containers:
      - name: backend
        image: imatu/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 5.3 CI/CD流水线

```
GitHub Actions流水线:
├── 代码推送触发
├── 静态代码分析
├── 单元测试运行
├── 构建Docker镜像
├── 安全扫描
├── 部署到测试环境
├── 集成测试
├── 部署到生产环境
└── 通知和回滚机制
```

## 6. 监控与运维

### 6.1 监控体系

```
监控维度:
├── 应用性能监控(APM)
│   - 响应时间
│   - 错误率
│   - 吞吐量
├── 基础设施监控
│   - CPU使用率
│   - 内存使用
│   - 磁盘空间
│   - 网络流量
├── 业务指标监控
│   - 用户活跃度
│   - 支付转化率
│     - AI服务使用统计
└── 日志监控
    - 应用日志收集
    - 错误日志分析
    - 安全日志审计
```

### 6.2 告警策略

```yaml
# alert-rules.yaml
groups:
- name: backend-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected"
```

## 7. 扩展性设计

### 7.1 水平扩展

```
无状态服务扩展:
Load Balancer → [App Server 1] [App Server 2] [App Server 3]
                     │              │              │
                     ▼              ▼              ▼
                Shared Database & Cache

有状态服务扩展:
Master DB ← Read Replica 1
           ← Read Replica 2
           ← Read Replica 3
```

### 7.2 微服务拆分策略

```
服务边界划分原则:
├── 业务领域驱动设计(DDD)
├── 高内聚低耦合
├── 独立部署单元
├── 数据库独立
└── 团队自治

当前服务拆分:
├── 用户服务 (User Service)
├── 课程服务 (Course Service)
├── 支付服务 (Payment Service)
├── AI服务 (AI Service)
├── 认证服务 (Auth Service)
└── 通知服务 (Notification Service)
```

---
*架构文档版本：v1.0 | 最后更新：2026年2月*
