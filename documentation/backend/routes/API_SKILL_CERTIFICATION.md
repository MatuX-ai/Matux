# 技能认证区块链系统API文档

## 概述

技能认证区块链系统提供基于Hyperledger Fabric的去中心化技能认证服务，支持W3C可验证凭证标准。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1
- **协议**: HTTP/HTTPS
- **数据格式**: JSON

## 认证方式

所有API端点都需要通过标准的HTTP头进行认证：

```
Authorization: Bearer <your-jwt-token>
```

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## API端点

### 1. 健康检查

#### GET `/blockchain/health`

检查区块链服务健康状态

**响应示例:**
```json
{
  "status": "healthy",
  "initialized": true,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

### 2. 证书管理

#### POST `/blockchain/certificates`

颁发技能证书

**请求体:**
```json
{
  "holderDID": "did:example:user123",
  "issuerDID": "did:example:org456",
  "skillName": "区块链开发",
  "skillLevel": "专家级",
  "evidence": ["项目经验", "认证考试"],
  "expiryDate": "2028-01-01T00:00:00Z"
}
```

**响应:**
```json
{
  "success": true,
  "message": "证书颁发成功",
  "data": {
    "transactionId": "tx_123456",
    "certificateId": "cert_001"
  }
}
```

#### GET `/blockchain/certificates/{cert_id}`

获取证书详情

**响应:**
```json
{
  "id": "cert_001",
  "holderDID": "did:example:user123",
  "issuerDID": "did:example:org456",
  "skillName": "区块链开发",
  "skillLevel": "专家级",
  "issueDate": "2026-01-01T00:00:00Z",
  "expiryDate": "2028-01-01T00:00:00Z",
  "status": "active",
  "evidence": ["项目经验", "认证考试"]
}
```

#### DELETE `/blockchain/certificates/{cert_id}`

撤销证书

**请求体:**
```json
{
  "reason": "违反使用条款"
}
```

**响应:**
```json
{
  "success": true,
  "message": "证书撤销成功",
  "data": {
    "transactionId": "tx_789012"
  }
}
```

#### GET `/blockchain/certificates/holder/{holder_did}`

根据持有者查询证书

**响应:**
```json
[
  {
    "id": "cert_001",
    "holderDID": "did:example:user123",
    "skillName": "区块链开发",
    "skillLevel": "专家级",
    "status": "active"
  }
]
```

### 3. 认证请求管理

#### POST `/blockchain/requests`

创建认证请求

**请求体:**
```json
{
  "holderDID": "did:example:user123",
  "skillName": "Python编程",
  "skillLevel": "高级",
  "evidence": ["项目作品"]
}
```

**响应:**
```json
{
  "success": true,
  "message": "认证请求创建成功",
  "data": {
    "requestId": "req_345678"
  }
}
```

#### POST `/blockchain/requests/{request_id}/approve`

批准认证请求

**请求体:**
```json
{
  "issuerDID": "did:example:org456"
}
```

#### POST `/blockchain/requests/{request_id}/reject`

拒绝认证请求

**请求体:**
```json
{
  "comments": "申请材料不完整"
}
```

#### GET `/blockchain/requests/pending`

获取待处理的认证请求

**响应:**
```json
[
  {
    "requestId": "req_123",
    "holderDID": "did:example:user123",
    "skillName": "区块链开发",
    "status": "pending"
  }
]
```

### 4. 证书验证

#### GET `/blockchain/verify/{cert_id}`

验证证书有效性

**响应 (有效证书):**
```json
{
  "success": true,
  "message": "证书验证通过",
  "data": {
    "valid": true,
    "certificate": {
      "id": "cert_001",
      "holderDID": "did:example:user123",
      "status": "active"
    },
    "verifiedAt": "2026-01-01T12:00:00Z"
  }
}
```

**响应 (无效证书):**
```json
{
  "success": false,
  "message": "证书已撤销",
  "data": {
    "valid": false,
    "error": "证书已撤销",
    "verifiedAt": "2026-01-01T12:00:00Z"
  }
}
```

## 数据模型

### 证书创建请求
```json
{
  "holderDID": "string",           // 必需，持有者DID
  "issuerDID": "string",           // 必需，颁发者DID
  "skillName": "string",           // 必需，技能名称
  "skillLevel": "string",          // 必需，技能等级
  "evidence": ["string"],          // 可选，证明材料
  "expiryDate": "string",          // 可选，过期日期(ISO 8601)
  "credentialSubject": {}          // 可选，凭证主体属性
}
```

### 证书响应
```json
{
  "id": "string",                  // 证书ID
  "holderDID": "string",           // 持有者DID
  "issuerDID": "string",           // 颁发者DID
  "skillName": "string",           // 技能名称
  "skillLevel": "string",          // 技能等级
  "issueDate": "string",           // 颁发日期
  "expiryDate": "string",          // 过期日期
  "status": "string",              // 状态(active/revoked)
  "evidence": ["string"]           // 证明材料
}
```

## 状态码说明

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 示例代码

### Python客户端示例

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def issue_certificate():
    url = f"{BASE_URL}/blockchain/certificates"
    headers = {"Content-Type": "application/json"}
    data = {
        "holderDID": "did:example:user123",
        "issuerDID": "did:example:org456",
        "skillName": "区块链开发",
        "skillLevel": "专家级",
        "evidence": ["项目经验"]
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def verify_certificate(cert_id):
    url = f"{BASE_URL}/blockchain/verify/{cert_id}"
    response = requests.get(url)
    return response.json()
```

### JavaScript客户端示例

```javascript
const BASE_URL = 'http://localhost:8000';

async function issueCertificate() {
    const response = await fetch(`${BASE_URL}/blockchain/certificates`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            holderDID: 'did:example:user123',
            issuerDID: 'did:example:org456',
            skillName: '区块链开发',
            skillLevel: '专家级',
            evidence: ['项目经验']
        })
    });
    
    return await response.json();
}

async function verifyCertificate(certId) {
    const response = await fetch(`${BASE_URL}/blockchain/verify/${certId}`);
    return await response.json();
}
```

## 错误处理

常见错误及解决方案：

1. **证书不存在**: 确保证书ID正确
2. **权限不足**: 检查认证令牌是否有效
3. **参数验证失败**: 检查请求参数格式和必填字段
4. **区块链网络错误**: 检查Fabric网络连接状态

## 版本历史

- **v1.0.0** (2026-02-27): 初始版本发布