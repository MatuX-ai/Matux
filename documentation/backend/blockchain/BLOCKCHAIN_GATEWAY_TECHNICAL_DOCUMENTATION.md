# 区块链网关服务技术文档

## 概述

区块链网关服务是iMato平台的核心组件之一，提供统一的区块链接口访问入口，支持积分发行、余额查询、交易历史等核心功能。该服务集成了JWT/OAuth2认证、熔断器模式、降级处理等企业级特性。

## 架构设计

### 核心组件

```
区块链网关服务架构
├── API路由层 (blockchain_gateway_routes.py)
│   ├── JWT/OAuth2认证中间件
│   ├── 权限验证装饰器
│   └── RESTful API端点
├── 业务逻辑层 (gateway_service.py)
│   ├── 区块链接口调用
│   ├── 数据验证和处理
│   └── 业务流程控制
├── 容错处理层 (circuit_breaker.py + fallback_handler.py)
│   ├── 熔断器模式实现
│   ├── 降级策略管理
│   └── 缓存机制
└── 鉴权管理层 (blockchain_auth_middleware.py)
    ├── JWT令牌验证
    ├── OAuth2令牌处理
    └── 细粒度权限控制
```

## API接口说明

### 1. 健康检查接口

**Endpoint**: `GET /api/v1/blockchain/health`

**功能**: 检查区块链网关服务运行状态

**响应示例**:
```json
{
  "status": "healthy",
  "service": "Blockchain Gateway",
  "version": "1.0.0",
  "timestamp": "2026-02-28T22:56:29.181694",
  "blockchain_connected": true,
  "last_block_height": 1000
}
```

### 2. 积分发行接口

**Endpoint**: `POST /api/v1/blockchain/issue-integral`

**权限要求**: 教育局管理员或系统管理员角色

**请求参数**:
```json
{
  "student_id": "string",      // 学生唯一标识
  "amount": "integer",         // 积分数量
  "description": "string"      // 可选描述
}
```

**响应示例**:
```json
{
  "status": "success",
  "tx_id": "tx_1772290589_ab0b2b267e84",
  "timestamp": "2026-02-28T22:56:29.493527",
  "student_id": "student_001",
  "amount": 100,
  "description": "教育局发放奖励积分"
}
```

### 3. OAuth2令牌交换接口

**Endpoint**: `POST /api/v1/blockchain/oauth/token`

**请求参数**:
```json
{
  "grant_type": "client_credentials",
  "client_id": "string",
  "client_secret": "string",
  "scope": "string"
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "blockchain:read blockchain:write"
}
```

### 4. 学生余额查询接口

**Endpoint**: `GET /api/v1/blockchain/students/{student_id}/balance`

**响应示例**:
```json
{
  "student_id": "student_001",
  "balance": 1500,
  "last_updated": "2026-02-28T22:56:29.493527",
  "query_time": "2026-02-28T22:56:29.599984"
}
```

### 5. 交易历史查询接口

**Endpoint**: `GET /api/v1/blockchain/transactions/history`

**查询参数**:
- `student_id` (可选): 学生ID
- `limit` (默认50): 返回记录数限制
- `offset` (默认0): 偏移量

**响应示例**:
```json
{
  "transactions": [
    {
      "id": "tx_001",
      "student_id": "student_001",
      "amount": 100,
      "type": "issue",
      "timestamp": 1772290589
    }
  ],
  "total_count": 1,
  "limit": 50,
  "offset": 0,
  "query_time": "2026-02-28T22:56:29.599984"
}
```

## 认证与授权

### JWT令牌认证

服务支持标准的JWT令牌认证：

1. **令牌格式**: Bearer Token
2. **认证头**: `Authorization: Bearer <token>`
3. **令牌内容**: 包含用户身份、角色、权限等信息
4. **过期时间**: 默认1小时

### OAuth2客户端认证

支持OAuth2.0 Client Credentials流程：

1. **授权类型**: `client_credentials`
2. **客户端注册**: 预先注册的客户端ID和密钥
3. **作用域控制**: 支持细粒度的权限控制
4. **令牌刷新**: 自动令牌过期处理

### 权限控制

基于角色的访问控制(RBAC)：

- **ADMIN**: 系统管理员，拥有所有权限
- **ORG_ADMIN**: 组织管理员（教育局），可发行积分
- **PREMIUM**: 高级用户，可查询数据
- **USER**: 普通用户，基础查询权限

## 容错与降级机制

### 熔断器模式

**配置参数**:
- `failure_threshold`: 5 (连续失败阈值)
- `timeout`: 60秒 (熔断超时时间)
- `half_open_attempts`: 3 (半开状态尝试次数)

**状态转换**:
```
CLOSED → OPEN → HALF_OPEN → CLOSED
```

### 降级策略

当服务不可用时自动触发降级：

1. **积分发行降级**: 返回模拟成功响应，记录请求待后续处理
2. **查询降级**: 返回缓存数据或默认值
3. **认证降级**: 使用备用认证机制

### 缓存机制

- **余额缓存**: 5分钟TTL
- **交易历史缓存**: 5分钟TTL
- **自动清理**: 定期清除过期缓存

## 部署与配置

### 环境变量

```bash
# 区块链网关配置
BLOCKCHAIN_CIRCUIT_BREAKER_THRESHOLD=5
BLOCKCHAIN_CIRCUIT_BREAKER_TIMEOUT=60
BLOCKCHAIN_CIRCUIT_BREAKER_HALF_OPEN=3

# 客户端注册
BLOCKCHAIN_CLIENT_REGISTRY='{"client1":{"secret":"secret1","scopes":["read","write"]}}'
```

### 启动服务

```bash
# 启动主应用（包含区块链网关）
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 或使用gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 监控与日志

### 健康监控

- **服务状态**: 通过 `/api/v1/blockchain/health` 接口监控
- **连接状态**: 区块链网络连接检测
- **性能指标**: 响应时间、吞吐量统计

### 日志级别

```python
# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 关键日志事件

- 服务启动/停止
- 认证成功/失败
- 熔断器状态变化
- 降级处理触发
- 区块链调用结果

## 测试与验证

### 单元测试

```bash
# 运行单元测试
python -m pytest tests/test_blockchain_gateway.py -v

# 运行特定测试
python -m pytest tests/test_blockchain_gateway.py::TestBlockchainGatewayService::test_issue_integral_success -v
```

### 集成测试

```bash
# 运行集成测试
python -m pytest tests/test_blockchain_gateway_integration.py -v
```

### 回测验证

```bash
# 执行完整回测
python tests/blockchain_gateway_backtest.py
```

## 性能优化

### 并发处理

- 异步IO操作
- 连接池管理
- 批量请求处理

### 缓存策略

- LRU缓存算法
- 多级缓存架构
- 智能预热机制

### 负载均衡

- 多实例部署
- 请求分发策略
- 故障转移机制

## 安全考虑

### 数据安全

- TLS/SSL加密传输
- 敏感数据脱敏
- 访问日志审计

### 认证安全

- 令牌过期机制
- 刷新令牌支持
- 多因子认证扩展

### 防护机制

- 速率限制
- 请求验证
- 异常检测

## 故障排除

### 常见问题

1. **认证失败**: 检查JWT令牌有效性
2. **权限不足**: 验证用户角色和权限配置
3. **熔断器开启**: 等待超时或手动重置
4. **区块链连接失败**: 检查网络连接和配置

### 调试技巧

```python
# 启用调试日志
import logging
logging.getLogger('services.blockchain').setLevel(logging.DEBUG)

# 监控熔断器状态
print(blockchain_gateway_service.circuit_breaker.get_state())
```

## 版本历史

### v1.0.0 (2026-02-28)
- 初始版本发布
- 核心功能实现
- 完整测试覆盖
- 企业级特性集成

---

**文档维护**: 开发团队  
**最后更新**: 2026-02-28  
**适用版本**: v1.0.0+