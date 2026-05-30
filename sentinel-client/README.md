# Sentinel License Client - Golang 实现

这是一个基于Golang实现的Sentinel许可证客户端，提供完整的许可证生成、验证和管理功能。

## 项目结构

```
sentinel-client/
├── api/
│   ├── handlers/
│   │   └── license_handlers.go    # API处理器
│   └── middleware/
│       ├── auth.go               # 认证中间件
│       └── license_validator.go  # 许可证验证中间件
├── cmd/
│   └── server/
│       └── main.go              # 主程序入口
├── config/
│   └── config.go                # 配置管理
├── internal/
│   └── sentinel/
│       └── client.go            # Sentinel核心客户端
├── go.mod                       # Go模块文件
└── README.md                    # 本文档
```

## 功能特性

- ✅ JWT-based 许可证生成和验证
- ✅ Redis缓存支持
- ✅ RESTful API接口
- ✅ 完整的中间件链（认证、日志、恢复）
- ✅ 许可证状态管理和吊销
- ✅ 特性权限控制
- ✅ 速率限制
- ✅ 审计日志
- ✅ 健康检查

## API 端点

### 许可证管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/licenses` | 生成新的许可证 |
| GET | `/api/licenses/{token}` | 查询许可证信息 |
| DELETE | `/api/licenses/{token}` | 吊销许可证 |
| GET | `/api/licenses` | 列出许可证 |
| POST | `/api/licenses/validate` | 验证许可证 |

### 系统端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/ping` | 简单存活检查 |

## 快速开始

### 1. 环境要求

- Go 1.21+
- Redis 6.0+

### 2. 安装依赖

```bash
cd sentinel-client
go mod tidy
```

### 3. 配置环境变量

```bash
# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=
export REDIS_DB=1

# 许可证配置
export LICENSE_ISSUER=iMatuProject
export LICENSE_AUDIENCE=enterprise
export SECRET_KEY=your-super-secret-key-here
export LICENSE_EXPIRATION_HOURS=24

# 服务器配置
export PORT=8080
```

### 4. 启动服务

```bash
go run cmd/server/main.go
```

服务将在 `http://localhost:8080` 启动。

## 使用示例

### 1. 生成许可证

```bash
curl -X POST http://localhost:8080/api/licenses \
  -H "Content-Type: application/json" \
  -H "X-Org-ID: org-123" \
  -d '{
    "features": ["bulk_users", "custom_courses"],
    "days": 30
  }'
```

或者使用完整请求体：

```bash
curl -X POST http://localhost:8080/api/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "org-123",
    "features": ["bulk_users", "custom_courses"],
    "days": 30
  }'
```

### 2. 查询许可证

```bash
curl -X GET "http://localhost:8080/api/licenses/YOUR_LICENSE_TOKEN"
```

### 3. 验证许可证

```bash
curl -X POST http://localhost:8080/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_LICENSE_TOKEN"}'
```

### 4. 吊销许可证

```bash
curl -X DELETE "http://localhost:8080/api/licenses/YOUR_LICENSE_TOKEN"
```

## 中间件使用

### 许可证验证中间件

```go
validator := middleware.NewLicenseValidator(sentinelClient)

// 基本许可证验证
handler := validator.RequireLicense(yourHandler)

// 特定功能要求
handler = validator.RequireFeature("premium_feature")(handler)

// 速率限制
handler = validator.RateLimit(100, time.Hour)(handler)

// 审计日志
handler = validator.AuditLogging("api_call")(handler)
```

### 认证中间件

```go
auth := middleware.NewAuthMiddleware()

// API密钥验证
handler := auth.RequireAPIKey(yourHandler)

// CORS支持
handler = auth.CORS(handler)

// 日志记录
handler = auth.Logging(handler)

// 异常恢复
handler = auth.Recovery(handler)
```

## 与Python系统的集成

该Golang实现完全兼容现有的Python许可证系统，可以通过以下方式集成：

### 1. API网关模式

将Golang服务作为API网关，处理许可证相关的高并发请求。

### 2. 微服务架构

独立部署许可证服务，通过HTTP API与主应用通信。

### 3. 混合模式

关键操作使用Golang服务，复杂业务逻辑仍由Python处理。

## 配置选项

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `REDIS_HOST` | localhost | Redis主机地址 |
| `REDIS_PORT` | 6379 | Redis端口 |
| `REDIS_PASSWORD` | "" | Redis密码 |
| `REDIS_DB` | 1 | Redis数据库编号 |
| `LICENSE_ISSUER` | iMatuProject | JWT发行人 |
| `LICENSE_AUDIENCE` | enterprise | JWT受众 |
| `SECRET_KEY` | your-secret-key-here | JWT签名密钥 |
| `LICENSE_EXPIRATION_HOURS` | 24 | 默认过期小时数 |
| `PORT` | 8080 | 服务端口 |

## 错误处理

所有API端点都返回标准的JSON错误格式：

```json
{
  "error": "Bad Request",
  "message": "详细错误信息",
  "code": 400
}
```

## 日志级别

支持标准的日志级别：
- DEBUG: 调试信息
- INFO: 一般信息
- WARN: 警告信息
- ERROR: 错误信息

## 性能优化建议

1. **连接池**: Redis使用内置连接池
2. **缓存策略**: 合理设置TTL时间
3. **并发控制**: 使用goroutine限制并发数
4. **监控指标**: 集成Prometheus指标收集

## 安全考虑

- 使用HTTPS在生产环境
- 定期轮换SECRET_KEY
- 实施适当的速率限制
- 启用详细的审计日志
- 定期清理过期的许可证数据

## 故障排除

### 常见问题

1. **Redis连接失败**: 检查Redis服务状态和网络连接
2. **JWT验证失败**: 确认SECRET_KEY一致
3. **端口占用**: 更改PORT环境变量
4. **权限不足**: 检查Redis数据库权限

### 调试技巧

```bash
# 启用调试日志
export LOG_LEVEL=debug

# 检查服务健康状态
curl http://localhost:8080/health

# 测试基本连通性
curl http://localhost:8080/ping
```

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License