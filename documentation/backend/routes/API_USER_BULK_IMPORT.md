# 用户批量导入API文档

## 📋 API概览

批量用户导入API允许通过文件上传的方式批量创建用户账户。

**Base URL**: `/api/v1/auth`

## 🔐 认证

所有批量导入API都需要有效的JWT访问令牌。

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## 📤 批量导入用户

### `POST /bulk-import`

批量导入用户数据。

### 请求参数

#### Form Data
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| file | file | 是 | CSV或Excel文件 |
| conflict_resolution | string | 否 | 冲突处理策略 (默认: skip) |
| generate_password | boolean | 否 | 是否自动生成密码 (默认: true) |

#### 冲突处理策略选项
- `skip`: 跳过重复项
- `update`: 更新现有用户
- `overwrite`: 完全覆盖
- `error`: 发现冲突时停止

### 支持的文件类型
- `text/csv` (CSV文件)
- `application/vnd.ms-excel` (Excel .xls)
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (Excel .xlsx)

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/auth/bulk-import" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@users.csv" \
  -F "conflict_resolution=skip" \
  -F "generate_password=true"
```

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success_count": 150,
  "failed_count": 2,
  "conflicts_count": 3,
  "errors": [
    "第5行: 邮箱格式不正确"
  ],
  "conflicts": {
    "email_conflicts": [
      {
        "row": 10,
        "email": "existing@example.com",
        "existing": true
      }
    ],
    "username_conflicts": [
      {
        "row": 15,
        "username": "duplicate_user",
        "existing": true
      }
    ],
    "invalid_data": [
      {
        "row": 5,
        "field": "email",
        "value": "invalid-email",
        "error": "邮箱格式不正确"
      }
    ]
  },
  "imported_users": [
    {
      "id": 1001,
      "username": "newuser",
      "email": "newuser@example.com",
      "role": "user",
      "is_active": true,
      "is_superuser": false
    }
  ]
}
```

#### 错误响应

##### 400 Bad Request
```json
{
  "detail": "只支持CSV和Excel文件格式"
}
```

##### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

##### 403 Forbidden
```json
{
  "detail": "只有管理员才能执行批量导入操作"
}
```

##### 500 Internal Server Error
```json
{
  "detail": "批量导入过程中发生错误: 具体错误信息"
}
```

## 📁 文件格式要求

### CSV格式示例

```csv
username,email,role
张三,zhangsan@example.com,user
李四,lisi@example.com,admin
王五,wangwu@example.com,user
```

### Excel格式
Excel文件应包含相同的列结构，第一行为列标题。

### 字段说明

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| username | 是 | string | 用户名 (3-50字符) |
| email | 是 | string | 邮箱地址 (有效格式) |
| role | 否 | string | 用户角色 (默认: user) |

### 字段验证规则

#### 用户名验证
- 长度: 3-50个字符
- 不能包含特殊字符
- 必须唯一

#### 邮箱验证
- 符合标准邮箱格式
- 长度不超过100字符
- 必须唯一

#### 角色验证
- 可选字段
- 有效值: `user`, `admin`, `org_admin`, `premium`
- 默认值: `user`

## ⚡ 性能考虑

### 文件大小限制
- 最大文件大小: 10MB
- 建议单次导入记录数: 不超过1000条

### 处理时间
- 小文件(<100记录): 几秒钟
- 中等文件(100-500记录): 30秒-2分钟
- 大文件(500+记录): 2-5分钟

## 🔒 安全注意事项

1. **权限控制**: 仅管理员可访问
2. **文件验证**: 严格验证文件类型和内容
3. **数据清理**: 自动清理和标准化输入数据
4. **审计日志**: 记录所有导入操作
5. **事务处理**: 失败时自动回滚

## 🛠️ 错误处理

### 常见错误及解决方案

| 错误代码 | 错误信息 | 解决方案 |
|----------|----------|----------|
| 400 | 文件格式不支持 | 使用CSV或Excel格式 |
| 400 | 文件过大 | 减少文件大小或分批导入 |
| 401 | 认证失败 | 检查访问令牌有效性 |
| 403 | 权限不足 | 使用管理员账户 |
| 422 | 数据验证失败 | 检查数据格式和必填字段 |

### 数据验证错误处理

系统会返回详细的行级错误信息：

```json
{
  "errors": [
    "第5行: 用户名不能为空",
    "第8行: 邮箱格式不正确",
    "第12行: 无效的角色"
  ]
}
```

## 📊 监控和日志

### 成功指标
- `success_count`: 成功导入的用户数
- `failed_count`: 导入失败的记录数
- `conflicts_count`: 发生冲突的记录数
- 处理时间

### 日志记录
所有批量导入操作都会记录：
- 操作时间戳
- 操作用户
- 文件信息
- 处理结果统计
- 详细错误信息

## 🔄 最佳实践

### 准备阶段
1. 使用模板文件作为参考
2. 验证数据质量和格式
3. 备份现有用户数据

### 执行阶段
1. 先用小量数据测试
2. 选择合适的冲突处理策略
3. 监控导入进度

### 验证阶段
1. 检查导入结果统计
2. 验证关键用户的准确性
3. 确认权限分配正确

## 📞 技术支持

遇到问题时请提供：
- 完整的错误响应
- 导入文件样本(脱敏后)
- 操作时间和环境信息
- 相关的日志片段