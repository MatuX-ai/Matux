# 硬件模块租赁系统 API 文档

## 概述

硬件模块租赁系统提供了一套完整的API接口，用于管理硬件模块的租赁、归还、库存管理以及损坏赔付等功能。所有API端点都遵循RESTful设计原则。

## 基础信息

- **基础URL**: `/api/v1/hardware/modules`
- **认证方式**: JWT Token (通过Authorization头部传递)
- **内容类型**: `application/json`

## API 端点

### 1. 获取硬件模块列表

**GET** `/api/v1/hardware/modules`

获取所有硬件模块列表，支持筛选和分页。

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_type | string | 否 | 模块类型筛选 |
| status | enum | 否 | 状态筛选 (available, rented, maintenance, retired) |
| available_only | boolean | 否 | 只显示可租赁的模块，默认false |
| page | integer | 否 | 页码，默认1 |
| size | integer | 否 | 每页大小，默认20 |

#### 响应示例

```json
[
  {
    "id": 1,
    "name": "Arduino Uno R3",
    "module_type": "microcontroller",
    "serial_number": "ARD-UNO-001",
    "price_per_day": 1.0,
    "deposit_amount": 50.0,
    "total_quantity": 10,
    "quantity_available": 8,
    "description": "标准Arduino Uno开发板",
    "status": "available",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  }
]
```

### 2. 获取单个硬件模块

**GET** `/api/v1/hardware/modules/{module_id}`

获取指定ID的硬件模块详细信息。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_id | integer | 是 | 硬件模块ID |

#### 响应示例

```json
{
  "id": 1,
  "name": "Arduino Uno R3",
  "module_type": "microcontroller",
  "serial_number": "ARD-UNO-001",
  "price_per_day": 1.0,
  "deposit_amount": 50.0,
  "total_quantity": 10,
  "quantity_available": 8,
  "description": "标准Arduino Uno开发板",
  "status": "available",
  "is_active": true,
  "rental_records": [
    {
      "id": 1,
      "user_license_id": 1,
      "rental_start_date": "2024-01-15T10:00:00Z",
      "rental_end_date": "2024-01-22T10:00:00Z",
      "daily_rate": 1.0,
      "total_amount": 7.0,
      "status": "active"
    }
  ],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### 3. 创建硬件模块

**POST** `/api/v1/hardware/modules`

创建新的硬件模块。

#### 请求体

```json
{
  "name": "ESP32 Development Board",
  "module_type": "microcontroller",
  "serial_number": "ESP-32-001",
  "price_per_day": 1.5,
  "deposit_amount": 75.0,
  "total_quantity": 5,
  "description": "ESP32 Wi-Fi蓝牙开发板",
  "is_active": true
}
```

#### 响应示例

```json
{
  "id": 2,
  "name": "ESP32 Development Board",
  "module_type": "microcontroller",
  "serial_number": "ESP-32-001",
  "price_per_day": 1.5,
  "deposit_amount": 75.0,
  "total_quantity": 5,
  "quantity_available": 5,
  "description": "ESP32 Wi-Fi蓝牙开发板",
  "status": "available",
  "is_active": true,
  "created_at": "2024-01-01T11:00:00Z",
  "updated_at": "2024-01-01T11:00:00Z"
}
```

### 4. 更新硬件模块

**PUT** `/api/v1/hardware/modules/{module_id}`

更新指定硬件模块的信息。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_id | integer | 是 | 硬件模块ID |

#### 请求体

```json
{
  "name": "ESP32 Development Board Pro",
  "price_per_day": 2.0,
  "description": "升级版ESP32开发板，支持更多功能"
}
```

### 5. 删除硬件模块

**DELETE** `/api/v1/hardware/modules/{module_id}`

删除指定的硬件模块。

> **注意**: 只能删除没有活跃租赁记录的模块。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_id | integer | 是 | 硬件模块ID |

#### 响应示例

```json
{
  "message": "硬件模块删除成功"
}
```

### 6. 租赁硬件模块

**POST** `/api/v1/hardware/modules/{module_id}/rent`

租赁指定的硬件模块。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_id | integer | 是 | 硬件模块ID |

#### 请求体

```json
{
  "user_license_id": 1,
  "rental_days": 7,
  "purpose": "学习Arduino编程"
}
```

#### 响应示例

```json
{
  "id": 3,
  "module_id": 1,
  "user_license_id": 1,
  "rental_start_date": "2024-01-01T12:00:00Z",
  "rental_end_date": "2024-01-08T12:00:00Z",
  "daily_rate": 1.0,
  "total_amount": 7.0,
  "deposit_paid": 50.0,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 7. 归还硬件模块

**POST** `/api/v1/hardware/modules/{module_id}/return`

归还已租赁的硬件模块。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| module_id | integer | 是 | 硬件模块ID |

#### 请求体

```json
{
  "actual_return_date": "2024-01-07T14:30:00Z",
  "is_damaged": true,
  "damage_level": "light",
  "damage_description": "外壳有轻微刮痕"
}
```

#### 响应示例

```json
{
  "id": 3,
  "module_id": 1,
  "user_license_id": 1,
  "rental_start_date": "2024-01-01T12:00:00Z",
  "rental_end_date": "2024-01-08T12:00:00Z",
  "actual_return_date": "2024-01-07T14:30:00Z",
  "daily_rate": 1.0,
  "total_amount": 7.0,
  "deposit_paid": 50.0,
  "is_damaged": true,
  "damage_level": "light",
  "damage_description": "外壳有轻微刮痕",
  "compensation_amount": 10.0,
  "status": "returned",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-07T14:30:00Z"
}
```

### 8. 获取用户租赁历史

**GET** `/api/v1/hardware/modules/user/{user_license_id}/rentals`

获取指定用户的租赁历史记录。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| user_license_id | integer | 是 | 用户许可证ID |

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| status | enum | 否 | 状态筛选 (active, overdue, returned, completed) |

### 9. 获取用户租赁摘要

**GET** `/api/v1/hardware/modules/user/{user_license_id}/summary`

获取指定用户的租赁摘要信息。

#### 路径参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| user_license_id | integer | 是 | 用户许可证ID |

#### 响应示例

```json
{
  "total_rentals": 15,
  "active_rentals": 2,
  "overdue_rentals": 0,
  "total_spent": 45.50,
  "pending_deposit": 100.00,
  "rental_limit": 5,
  "can_rent_more": true
}
```

## 错误响应

所有API错误都会返回标准的错误格式：

```json
{
  "detail": "错误描述信息"
}
```

### 常见HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

## 枚举值说明

### 硬件模块状态 (status)

- `available`: 可租赁
- `rented`: 已出租
- `maintenance`: 维护中
- `retired`: 已退役

### 租赁记录状态 (status)

- `active`: 活跃租赁中
- `overdue`: 逾期未还
- `returned`: 已归还
- `completed`: 已完成

### 损坏等级 (damage_level)

- `light`: 轻微损坏
- `moderate`: 中等损坏
- `severe`: 严重损坏

## 损坏赔付规则

| 损坏等级 | 赔付比例 | 示例(50元押金) |
|----------|----------|----------------|
| 轻微损坏 | 20% | 10元 |
| 中等损坏 | 50% | 25元 |
| 严重损坏 | 100% | 50元 |

## 并发控制

系统采用数据库级别的锁机制确保库存一致性：
- 租赁时先检查库存再预留
- 归还时先更新状态再释放库存
- 支持高并发场景下的库存同步

## 使用示例

### Python客户端示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/hardware/modules"
HEADERS = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

# 获取可租赁模块列表
response = requests.get(
    f"{BASE_URL}",
    params={"available_only": True},
    headers=HEADERS
)
modules = response.json()

# 租赁模块
rental_data = {
    "user_license_id": 1,
    "rental_days": 7
}
response = requests.post(
    f"{BASE_URL}/1/rent",
    json=rental_data,
    headers=HEADERS
)
rental_record = response.json()

# 归还模块并报告损坏
return_data = {
    "actual_return_date": "2024-01-07T14:30:00Z",
    "is_damaged": True,
    "damage_level": "light",
    "damage_description": "外壳轻微刮痕"
}
response = requests.post(
    f"{BASE_URL}/1/return",
    json=return_data,
    headers=HEADERS
)
```

## 注意事项

1. 所有时间字段均使用ISO 8601格式
2. 金额字段使用Decimal类型，保留2位小数
3. 序列号必须唯一
4. 租赁期限最长不超过30天
5. 损坏赔付从押金中扣除
6. 系统自动处理逾期提醒