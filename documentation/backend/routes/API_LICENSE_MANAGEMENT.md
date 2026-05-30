# 许可证管理系统API文档

## 概述

许可证管理系统提供完整的许可证生命周期管理功能，包括组织管理、许可证生成、验证、撤销等操作。系统基于Sentinel社区版设计，支持多租户架构和高性能缓存。

## 基础配置

### 环境变量配置

```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=

# 许可证配置
LICENSE_ISSUER=iMatuProject
LICENSE_AUDIENCE=enterprise
LICENSE_ALGORITHM=HS256
LICENSE_EXPIRATION_HOURS=24
LICENSE_KEY_LENGTH=32
LICENSE_PREFIX=LICENSE

# 缓存配置
CACHE_TTL_SECONDS=3600
CACHE_CLEANUP_INTERVAL=300
```

## API端点

### 组织管理

#### 创建组织
```
POST /api/v1/organizations
```

**请求体:**
```json
{
  "name": "示例教育机构",
  "contact_email": "contact@example.com",
  "phone": "+86-138-0000-0000",
  "address": "北京市朝阳区示例路123号",
  "website": "https://www.example.com",
  "max_users": 500
}
```

**响应:**
```json
{
  "id": 1,
  "name": "示例教育机构",
  "contact_email": "contact@example.com",
  "phone": "+86-138-0000-0000",
  "address": "北京市朝阳区示例路123号",
  "website": "https://www.example.com",
  "license_count": 0,
  "max_users": 500,
  "current_users": 0,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

#### 获取组织列表
```
GET /api/v1/organizations?skip=0&limit=100&is_active=true
```

#### 获取组织详情
```
GET /api/v1/organizations/{org_id}
```

#### 更新组织
```
PUT /api/v1/organizations/{org_id}
```

### 许可证管理

#### 生成许可证
```
POST /api/v1/licenses
```

**请求体:**
```json
{
  "organization_id": 1,
  "product_id": 1,
  "license_type": "education",
  "duration_days": 365,
  "max_users": 100,
  "max_devices": 50,
  "features": ["basic_access", "advanced_features"],
  "notes": "教育版许可证"
}
```

**响应:**
```json
{
  "id": 1,
  "license_key": "LICENSE-ABCDEF123456-1A2B",
  "organization_id": 1,
  "product_id": 1,
  "license_type": "education",
  "status": "active",
  "issued_at": "2026-01-01T00:00:00",
  "expires_at": "2027-01-01T00:00:00",
  "activated_at": null,
  "max_users": 100,
  "max_devices": 50,
  "current_users": 0,
  "current_devices": 0,
  "features": ["basic_access", "advanced_features"],
  "restrictions": {},
  "metadata": {},
  "notes": "教育版许可证",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00",
  "is_expired": false,
  "is_valid": true,
  "days_until_expiry": 365
}
```

#### 获取许可证列表
```
GET /api/v1/licenses?skip=0&limit=100&organization_id=1&status=active
```

#### 获取许可证详情
```
GET /api/v1/licenses/{license_key}
```

#### 验证许可证
```
POST /api/v1/licenses/{license_key}/validate
```

**响应 (有效):**
```json
{
  "valid": true,
  "license_info": {
    "id": 1,
    "license_key": "LICENSE-ABCDEF123456-1A2B",
    "status": "active",
    "expires_at": "2027-01-01T00:00:00",
    "max_users": 100,
    "current_users": 10,
    "features": ["basic_access", "advanced_features"]
  }
}
```

**响应 (无效):**
```json
{
  "detail": "许可证已过期"
}
```

#### 更新许可证
```
PUT /api/v1/licenses/{license_key}
```

#### 撤销许可证
```
POST /api/v1/licenses/{license_key}/revoke
```

**请求体:**
```json
{
  "reason": "违反使用条款"
}
```

#### 获取组织许可证
```
GET /api/v1/organizations/{org_id}/licenses
```

### 系统管理

#### 获取统计信息
```
GET /api/v1/statistics
```

**响应:**
```json
{
  "database_stats": {
    "total_licenses": 150,
    "active_licenses": 120,
    "expired_licenses": 25,
    "revoked_licenses": 5
  },
  "cache_stats": {
    "total_licenses": 120,
    "active_licenses": 120,
    "expired_licenses": 0,
    "redis_info": {
      "used_memory": "1048576"
    }
  },
  "generated_at": "2026-01-01T00:00:00"
}
```

#### 健康检查
```
GET /api/v1/health
```

## 许可证密钥格式

许可证密钥采用以下格式：
```
LICENSE-{RANDOM_STRING}-{CHECKSUM}
```

- `LICENSE`: 固定前缀
- `RANDOM_STRING`: 32位随机字符（字母和数字）
- `CHECKSUM`: 4位MD5校验和

示例：`LICENSE-ABCDEF1234567890GHIJKL-1A2B`

## 错误响应

### 通用错误格式
```json
{
  "detail": "错误描述信息"
}
```

### 常见HTTP状态码

- `200`: 请求成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权（缺少许可证）
- `403`: 禁止访问（许可证无效）
- `404`: 资源不存在
- `422`: 请求体验证失败
- `429`: 请求频率超限
- `500`: 服务器内部错误

## 安全说明

### 许可证验证
所有API请求（除许可证管理API外）都需要在请求头中包含有效的许可证密钥：

```
X-License-Key: LICENSE-ABCDEF123456-1A2B
```

或者使用Authorization头：
```
Authorization: Bearer LICENSE-ABCDEF123456-1A2B
```

### 功能权限控制
许可证可以包含特定功能标识，只有具备相应功能的许可证才能访问特定API：

```python
@api_access_required
@license_required(required_features=["api_access"])
async def protected_endpoint():
    pass
```

### 速率限制
基于许可证的请求频率限制：
- 默认：每小时1000次请求
- 可通过许可证配置调整

## 使用示例

### Python客户端示例
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
LICENSE_KEY = "LICENSE-YOUR-KEY-HERE"

# 创建组织
org_data = {
    "name": "我的教育机构",
    "contact_email": "admin@school.edu.cn"
}

response = requests.post(
    f"{BASE_URL}/organizations",
    json=org_data,
    headers={"X-License-Key": LICENSE_KEY}
)

# 生成许可证
license_data = {
    "organization_id": 1,
    "license_type": "education",
    "duration_days": 365,
    "max_users": 50
}

response = requests.post(
    f"{BASE_URL}/licenses",
    json=license_data,
    headers={"X-License-Key": LICENSE_KEY}
)

# 验证许可证
response = requests.post(
    f"{BASE_URL}/licenses/LICENSE-KEY-HERE/validate",
    headers={"X-License-Key": LICENSE_KEY}
)
```

### JavaScript/Angular示例
```typescript
import { LicenseService } from './license.service';

constructor(private licenseService: LicenseService) {}

// 创建组织
const orgData = {
  name: '我的教育机构',
  contact_email: 'admin@school.edu.cn'
};

this.licenseService.createOrganization(orgData).subscribe(
  (organization) => {
    console.log('组织创建成功:', organization);
  },
  (error) => {
    console.error('创建失败:', error);
  }
);

// 验证许可证
this.licenseService.validateLicense('LICENSE-KEY-HERE').subscribe(
  (result) => {
    if (result.valid) {
      console.log('许可证有效:', result.license_info);
    } else {
      console.log('许可证无效:', result.error);
    }
  }
);
```

## 性能优化

### Redis缓存策略
- 许可证信息缓存24小时
- 自动清理过期缓存
- 支持缓存预热

### 数据库优化
- 关键字段建立索引
- 支持分页查询
- 连接池管理

## 监控和日志

### 日志级别
- `INFO`: 正常操作日志
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 监控指标
- 许可证验证成功率
- API响应时间
- Redis缓存命中率
- 数据库连接状态

## 故障排除

### 常见问题

1. **许可证验证失败**
   - 检查许可证密钥格式
   - 确认许可证未过期
   - 验证Redis连接状态

2. **数据库连接错误**
   - 检查数据库配置
   - 确认数据库服务运行状态
   - 查看连接池配置

3. **Redis连接失败**
   - 检查Redis服务状态
   - 验证网络连接
   - 确认认证信息

### 调试信息
启用调试模式可获得更详细的错误信息：
```env
DEBUG=True
LOG_LEVEL=DEBUG
```