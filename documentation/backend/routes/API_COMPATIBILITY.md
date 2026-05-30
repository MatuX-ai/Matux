# API兼容性规范文档

## 1. 概述

本文档定义了iMato平台API的兼容性规范，包括版本控制策略、RESTful设计原则、OpenAPI规范集成以及监控指标体系。

## 2. 版本控制策略

### 2.1 API版本管理

#### 版本命名规范
- **主版本号**: 破坏性变更（不向后兼容）
- **次版本号**: 新增功能（向后兼容）
- **修订号**: Bug修复（向后兼容）

#### 版本标识方式
```
URL路径版本: /api/v1/, /api/v2/
请求头版本: Accept: application/vnd.imato.v1+json
查询参数版本: ?api_version=v1
```

### 2.2 向后兼容性保证

#### 兼容性原则
1. **新增字段**: 可以添加新的可选字段
2. **字段删除**: 仅删除已标记为废弃的字段
3. **枚举值**: 可以添加新的枚举值，不能删除现有值
4. **HTTP状态码**: 保持现有状态码含义不变
5. **请求方法**: 不改变现有端点的HTTP方法

#### 废弃机制
```json
{
  "field_name": "value",
  "deprecated_field": "old_value",
  "_deprecated": {
    "deprecated_field": {
      "since": "v2.1.0",
      "removal_date": "2026-12-31",
      "replacement": "new_field"
    }
  }
}
```

### 2.3 版本生命周期

```
开发阶段 → 测试阶段 → 生产阶段 → 维护阶段 → 废弃阶段
    ↓         ↓         ↓         ↓         ↓
v1.0.0    v1.0.0-rc1   v1.0.0    v1.0.x    v2.0.0
```

## 3. RESTful API设计规范

### 3.1 资源设计原则

#### URI结构
```
/api/{version}/{resource}/{id}/{sub-resource}
```

#### 示例
```
GET    /api/v1/users                    # 获取用户列表
POST   /api/v1/users                    # 创建用户
GET    /api/v1/users/123                # 获取特定用户
PUT    /api/v1/users/123                # 更新用户
DELETE /api/v1/users/123                # 删除用户
GET    /api/v1/users/123/orders         # 获取用户订单
```

### 3.2 HTTP方法语义

| 方法 | 语义 | 幂等性 | 安全性 |
|------|------|--------|--------|
| GET | 获取资源 | 是 | 是 |
| POST | 创建资源 | 否 | 否 |
| PUT | 更新完整资源 | 是 | 否 |
| PATCH | 部分更新资源 | 否 | 否 |
| DELETE | 删除资源 | 是 | 否 |

### 3.3 响应格式规范

#### 成功响应
```json
{
  "data": {
    "id": 123,
    "name": "用户名",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "version": "1.0.0",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### 错误响应
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ],
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_1234567890"
  }
}
```

## 4. OpenAPI规范集成

### 4.1 API文档生成

#### 自动生成配置
```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="iMato API",
    version="1.0.0",
    description="智能教育平台API文档",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加自定义安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 4.2 Schema验证

#### 请求体验证
```python
from pydantic import BaseModel, Field
from typing import Optional

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password_123"
            }
        }
```

#### 响应体验证
```python
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        orm_mode = True
```

## 5. 监控指标体系

### 5.1 Prometheus指标定义

#### 核心业务指标
```python
from prometheus_client import Counter, Histogram, Gauge, Summary

# 请求计数器
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# 请求延迟直方图
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 活跃用户数
ACTIVE_USERS = Gauge(
    'active_users_count',
    'Number of active users'
)

# 业务成功率
SUCCESS_RATE = Summary(
    'business_success_rate',
    'Business operation success rate',
    ['operation_type']
)
```

#### 熔断器专用指标
```python
# 熔断器状态
CIRCUIT_STATE = Enum(
    'circuit_breaker_state',
    'Circuit breaker current state',
    states=['closed', 'open', 'half_open']
)

# 熔断器请求统计
CIRCUIT_REQUESTS = Counter(
    'circuit_breaker_requests_total',
    'Requests handled by circuit breaker',
    ['state', 'result']
)

# 失败率
FAILURE_RATE = Gauge(
    'circuit_breaker_failure_rate',
    'Current failure rate percentage'
)
```

### 5.2 告警规则配置

#### 关键告警阈值
```yaml
# 告警规则示例
groups:
  - name: api_performance
    rules:
      # 高延迟告警
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          
      # 高错误率告警
      - alert: HighAPIErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
```

### 5.3 Grafana仪表板配置

#### 核心监控面板
```json
{
  "dashboard": {
    "title": "API Compatibility Monitoring",
    "panels": [
      {
        "title": "请求量趋势",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "响应时间分布",
        "type": "heatmap",
        "targets": [
          {
            "expr": "http_request_duration_seconds_bucket"
          }
        ]
      },
      {
        "title": "熔断器状态",
        "type": "stat",
        "targets": [
          {
            "expr": "circuit_breaker_state"
          }
        ]
      }
    ]
  }
}
```

## 6. 回测验证方案

### 6.1 服务熔断测试

#### 测试场景设计
```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class CircuitBreakerTester:
    def __init__(self, base_url: str, threshold: int = 5):
        self.base_url = base_url
        self.threshold = threshold
        self.failure_count = 0
        
    async def simulate_high_concurrency(self, concurrency: int = 100):
        """模拟高并发请求场景"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(concurrency):
                task = asyncio.create_task(self.make_faulty_request(session))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    async def make_faulty_request(self, session):
        """发送故障请求"""
        try:
            async with session.get(f"{self.base_url}/faulty-endpoint") as response:
                if response.status >= 500:
                    self.failure_count += 1
                return response.status
        except Exception as e:
            self.failure_count += 1
            return str(e)
```

### 6.2 API版本兼容性测试

#### 并行版本测试
```python
def test_api_version_compatibility():
    """测试API v1/v2并行运行"""
    test_cases = [
        {
            "version": "v1",
            "endpoint": "/api/v1/users",
            "expected_fields": ["id", "username", "email"]
        },
        {
            "version": "v2", 
            "endpoint": "/api/v2/users",
            "expected_fields": ["id", "username", "email", "profile"]
        }
    ]
    
    for case in test_cases:
        response = requests.get(case["endpoint"])
        assert response.status_code == 200
        
        data = response.json()
        for field in case["expected_fields"]:
            assert field in data
```

## 7. 部署和运维

### 7.1 灰度发布策略

#### 蓝绿部署
```
Production (v1.0) ←→ Staging (v2.0)
     ↓                    ↓
  [流量切分] ←→ [监控验证] ←→ [回滚机制]
```

#### 金丝雀发布
```yaml
# Istio VirtualService配置示例
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: api-canary
spec:
  hosts:
  - api.imato.com
  http:
  - route:
    - destination:
        host: api-v1
        subset: stable
      weight: 90
    - destination:
        host: api-v2
        subset: canary
      weight: 10
```

### 7.2 监控告警配置

#### 告警通道设置
```yaml
receivers:
  - name: 'team-alerts'
    webhook_configs:
    - url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    email_configs:
    - to: 'dev-team@imato.com'
      send_resolved: true
```

## 8. 最佳实践

### 8.1 设计原则
- **一致性**: 保持API设计风格统一
- **简洁性**: 避免过度复杂的设计
- **可扩展性**: 预留扩展空间
- **安全性**: 实施适当的安全措施

### 8.2 文档维护
- API变更时同步更新文档
- 提供丰富的示例代码
- 维护版本变更日志
- 定期审查文档准确性

### 8.3 测试策略
- 单元测试覆盖率≥80%
- 集成测试覆盖核心业务流程
- 性能测试验证SLA指标
- 兼容性测试确保版本平滑升级

---
*文档版本: 1.0.0*
*最后更新: 2026-02-28*
*负责人: 架构团队*