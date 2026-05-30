# API设计规范：RESTful + OpenAPI

## 概述

本文档定义了iMatuProject项目的API设计规范，确保前后端接口的一致性和可维护性。

## RESTful API原则

### 资源命名规范

1. **使用名词而非动词**
   ```
   ✅ GET /users          // 获取用户列表
   ❌ GET /getUsers       // 避免使用动词
   
   ✅ POST /users         // 创建用户
   ❌ POST /createUser    // 避免使用动词
   ```

2. **使用复数形式**
   ```
   ✅ /users
   ✅ /products
   ✅ /orders
   ```

3. **层次化资源关系**
   ```
   ✅ /users/{userId}/orders
   ✅ /products/{productId}/reviews
   ✅ /organizations/{orgId}/licenses
   ```

### HTTP方法使用

| 方法 | 用途 | 幂等性 | 安全性 |
|------|------|--------|--------|
| GET | 获取资源 | 是 | 是 |
| POST | 创建资源 | 否 | 否 |
| PUT | 更新整个资源 | 是 | 否 |
| PATCH | 部分更新资源 | 否 | 否 |
| DELETE | 删除资源 | 是 | 否 |

### 状态码规范

#### 成功状态码
```
200 OK - GET、PUT、PATCH请求成功
201 Created - POST请求成功创建资源
204 No Content - DELETE请求成功，无返回内容
```

#### 客户端错误状态码
```
400 Bad Request - 请求参数错误
401 Unauthorized - 未认证或认证失败
403 Forbidden - 权限不足
404 Not Found - 资源不存在
409 Conflict - 资源冲突
422 Unprocessable Entity - 请求格式正确但语义错误
```

#### 服务器错误状态码
```
500 Internal Server Error - 服务器内部错误
502 Bad Gateway - 网关错误
503 Service Unavailable - 服务不可用
504 Gateway Timeout - 网关超时
```

## 统一响应格式

### 成功响应
```json
{
  "data": {
    "id": 1,
    "name": "用户名",
    "email": "user@example.com"
  },
  "status": 200,
  "message": "操作成功",
  "timestamp": "2026-03-01T10:00:00Z"
}
```

### 列表响应
```json
{
  "data": {
    "items": [
      {
        "id": 1,
        "name": "项目1"
      },
      {
        "id": 2,
        "name": "项目2"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 100,
      "pages": 10
    }
  },
  "status": 200,
  "message": "获取成功"
}
```

### 错误响应
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
    ]
  },
  "status": 400,
  "timestamp": "2026-03-01T10:00:00Z"
}
```

## 请求参数规范

### 查询参数
```http
GET /users?page=1&limit=20&sort=name&order=asc&status=active

参数说明：
- page: 页码（从1开始）
- limit: 每页数量
- sort: 排序字段
- order: 排序方向（asc/desc）
- 其他过滤条件
```

### 路径参数
```http
GET /users/{userId}
PUT /products/{productId}
DELETE /orders/{orderId}
```

### 请求体
```json
{
  "name": "用户名",
  "email": "user@example.com",
  "profile": {
    "age": 25,
    "location": "北京"
  }
}
```

## 认证和授权

### JWT Token
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 权限控制
```http
X-User-Roles: admin,user
X-Organization-ID: 12345
```

## 版本控制

### URL版本控制
```
✅ https://api.imatuproject.com/v1/users
✅ https://api.imatuproject.com/v2/users
```

### Header版本控制
```http
Accept: application/vnd.imatu.v1+json
API-Version: 2
```

## 分页规范

### 请求参数
```
?page=1&limit=20
```

### 响应格式
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "pages": 5,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

## 过滤和搜索

### 基本过滤
```
GET /users?status=active&role=admin
GET /products?category=electronics&price_min=100&price_max=500
```

### 搜索
```
GET /users?q=john
GET /products?search=laptop
```

### 高级过滤
```
GET /orders?created_after=2026-01-01&created_before=2026-12-31
GET /users?last_login_gte=2026-01-01
```

## 排序规范

```
GET /users?sort=name&order=asc
GET /products?sort=price&order=desc
GET /orders?sort=-created_at  // 负号表示降序
```

## 批量操作

### 批量创建
```http
POST /users/batch
Content-Type: application/json

{
  "users": [
    {"name": "用户1", "email": "user1@example.com"},
    {"name": "用户2", "email": "user2@example.com"}
  ]
}
```

### 批量更新
```http
PUT /users/batch
Content-Type: application/json

{
  "updates": [
    {"id": 1, "name": "新名字1"},
    {"id": 2, "name": "新名字2"}
  ]
}
```

### 批量删除
```http
DELETE /users/batch
Content-Type: application/json

{
  "ids": [1, 2, 3, 4, 5]
}
```

## 错误处理规范

### 错误码分类
```
AUTH_* - 认证相关错误
VALIDATION_* - 参数验证错误
PERMISSION_* - 权限相关错误
RESOURCE_* - 资源相关错误
SYSTEM_* - 系统错误
```

### 错误响应示例
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "邮箱格式不正确"
      },
      {
        "field": "password",
        "code": "TOO_SHORT",
        "message": "密码长度至少8位"
      }
    ]
  },
  "status": 400,
  "timestamp": "2026-03-01T10:00:00Z",
  "requestId": "req_1234567890"
}
```

## 速率限制

### 响应头
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

### 错误响应
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超过限制"
  },
  "status": 429,
  "retryAfter": 60
}
```

## 缓存策略

### 缓存控制头
```http
Cache-Control: max-age=3600
ETag: "abc123"
Last-Modified: Wed, 21 Oct 2026 07:28:00 GMT
```

### 条件请求
```http
GET /users/1
If-None-Match: "abc123"
If-Modified-Since: Wed, 21 Oct 2026 07:28:00 GMT
```

## 文件上传

### 单文件上传
```http
POST /files
Content-Type: multipart/form-data

file: (binary)
metadata: {"description": "文件描述"}
```

### 多文件上传
```http
POST /files/batch
Content-Type: multipart/form-data

files: [(binary), (binary), (binary)]
```

## WebSocket实时通信

### 连接
```websocket
wss://api.imatuproject.com/ws
Authorization: Bearer token
```

### 消息格式
```json
{
  "type": "message_type",
  "data": {
    "payload": "数据内容"
  },
  "timestamp": "2026-03-01T10:00:00Z"
}
```

## OpenAPI规范

### 基本结构
```yaml
openapi: 3.0.3
info:
  title: iMatuProject API
  version: 1.0.0
  description: iMatuProject后端API文档
servers:
  - url: https://api.imatuproject.com/v1
    description: 生产环境
paths:
  /users:
    get:
      summary: 获取用户列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: 成功获取用户列表
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
```

### 组件定义
```yaml
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
      required:
        - id
        - name
        - email
        
    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
        status:
          type: integer
        timestamp:
          type: string
          format: date-time
```

## 最佳实践

### 1. 一致性
- 所有API端点遵循相同的命名和结构规范
- 统一的错误处理和响应格式
- 一致的参数验证规则

### 2. 文档化
- 所有API端点都有详细的文档说明
- 提供API使用示例
- 保持文档与代码同步更新

### 3. 测试
- 为所有API端点编写自动化测试
- 包括正常流程和异常流程测试
- 定期进行性能测试

### 4. 监控
- 记录所有API调用日志
- 监控API性能指标
- 设置告警机制

### 5. 安全
- 实施适当的认证和授权机制
- 防止常见安全漏洞
- 定期进行安全审计

## 迁移指南

### 从旧版API迁移

1. **版本兼容性**
   - v1/v2并行运行期间确保向后兼容
   - 逐步迁移客户端到新版API
   - 设置合理的弃用时间线

2. **数据迁移**
   - 制定详细的数据迁移计划
   - 进行充分的测试验证
   - 准备回滚方案

3. **客户端适配**
   - 提供详细的迁移文档
   - 开发迁移工具或脚本
   - 提供技术支持

## 参考资料

- [RESTful API Design Guidelines](https://restfulapi.net/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Google API Design Guide](https://cloud.google.com/apis/design)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)

---
*本文档版本：1.0.0*
*最后更新：2026年3月1日*