# iMato AI Service API 文档

## 概述

iMato AI Service 提供RESTful API接口，支持多种AI模型的代码生成服务。所有API端点都需要有效的JWT认证令牌。

## 基础信息

- **基础URL**: `http://localhost:8000` (开发环境)
- **API版本**: v1
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON

## 认证

### 获取访问令牌

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=testuser&password=testpass
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 使用访问令牌

在所有需要认证的请求中，在Authorization头中包含令牌：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## AI服务端点

### 生成代码

生成代码是AI服务的核心功能。

```http
POST /api/v1/generate-code
Authorization: Bearer {access_token}
Content-Type: application/json
```

**请求体:**
```json
{
  "prompt": "创建一个Python函数来计算斐波那契数列",
  "provider": "openai",
  "model": "gpt-4-turbo",
  "language": "python",
  "temperature": 0.7,
  "max_tokens": 2000,
  "system_prompt": "你是一个专业的Python开发者"
}
```

**参数说明:**

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| prompt | string | 是 | 代码生成的提示词，最少1个字符，最多5000字符 |
| provider | string | 否 | AI提供商，默认为"openai" |
| model | string | 否 | 具体模型名称，如未指定则使用默认模型 |
| language | string | 否 | 目标编程语言 |
| temperature | number | 否 | 生成温度(0.0-1.0)，默认0.7 |
| max_tokens | integer | 否 | 最大生成令牌数(1-8000)，默认2000 |
| system_prompt | string | 否 | 系统提示词 |

**支持的提供商:**
- `openai` - OpenAI GPT系列
- `lingma` - Lingma代码专用模型
- `deepseek` - DeepSeek代码模型
- `anthropic` - Anthropic Claude系列
- `google` - Google Gemini系列

**支持的编程语言:**
- `python`, `javascript`, `typescript`, `java`, `csharp`, `go`, `rust`, `cpp`, `php`, `ruby`

**成功响应 (200):**
```json
{
  "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "provider": "openai",
  "model": "gpt-4-turbo",
  "tokens_used": 45,
  "processing_time": 1.23,
  "language_detected": "python"
}
```

**错误响应:**
```json
{
  "detail": "Code generation failed: Invalid API key"
}
```

### 获取可用模型

获取当前支持的所有AI模型列表。

```http
GET /api/v1/models
Authorization: Bearer {access_token}
```

**响应 (200):**
```json
{
  "models": [
    {
      "provider": "openai",
      "model_name": "gpt-4-turbo",
      "description": "OpenAI最新的GPT-4 Turbo模型，适合复杂代码生成",
      "max_tokens": 4096,
      "supported_languages": ["python", "javascript", "typescript", "java", "csharp", "go", "rust", "cpp"]
    },
    {
      "provider": "lingma",
      "model_name": "lingma-code-pro",
      "description": "Lingma专业代码生成模型",
      "max_tokens": 4096,
      "supported_languages": ["python", "javascript", "typescript", "go"]
    }
  ]
}
```

### 获取使用统计

获取当前用户的AI使用统计信息。

```http
GET /api/v1/usage-stats
Authorization: Bearer {access_token}
```

**响应 (200):**
```json
{
  "total_requests": 45,
  "successful_requests": 42,
  "success_rate": 93.33,
  "provider_stats": [
    {
      "provider": "openai",
      "request_count": 30,
      "average_processing_time": 1.45
    },
    {
      "provider": "lingma",
      "request_count": 15,
      "average_processing_time": 0.87
    }
  ]
}
```

### 获取最近请求记录

获取用户最近的AI请求历史记录。

```http
GET /api/v1/recent-requests?limit=10
Authorization: Bearer {access_token}
```

**参数:**
- `limit` (可选): 返回记录数量，默认10，最大100

**响应 (200):**
```json
[
  {
    "id": 123,
    "prompt": "创建一个排序算法实现快速排序",
    "model_provider": "openai",
    "model_name": "gpt-4-turbo",
    "tokens_used": 156,
    "processing_time": 2.15,
    "success": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 122,
    "prompt": "生成一个React组件...",
    "model_provider": "lingma",
    "model_name": "lingma-code-pro",
    "tokens_used": 89,
    "processing_time": 1.23,
    "success": true,
    "created_at": "2024-01-15T09:15:00Z"
  }
]
```

## 认证端点

### 用户注册

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**请求体:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**响应 (200):**
```json
{
  "id": 123,
  "username": "newuser",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false
}
```

### 获取当前用户信息

```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**响应 (200):**
```json
{
  "id": 123,
  "username": "testuser",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false
}
```

## 错误处理

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/令牌无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 请求体验证失败 |
| 429 | 请求过于频繁/配额超限 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误

1. **认证失败 (401)**
   ```json
   {
     "detail": "Could not validate credentials"
   }
   ```

2. **配额超限 (429)**
   ```json
   {
     "detail": "Daily AI quota exceeded. Please upgrade your plan."
   }
   ```

3. **参数验证失败 (422)**
   ```json
   {
     "detail": [
       {
         "loc": ["body", "prompt"],
         "msg": "ensure this value has at least 1 characters",
         "type": "value_error.any_str.min_length"
       }
     ]
   }
   ```

## 速率限制

为保证服务质量，API实施以下速率限制：

- **普通用户**: 每小时100次请求
- **高级用户**: 每小时500次请求
- **管理员**: 无限制

超过限制将返回429状态码。

## SDK使用示例

### JavaScript/TypeScript

```javascript
import { AIServiceClient, ModelProvider } from './ai-sdk';

const client = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: 'your-access-token'
});

// 生成代码
const response = await client.generateCode({
  prompt: '创建一个计算阶乘的函数',
  provider: ModelProvider.OPENAI,
  language: 'python',
  temperature: 0.7
});

console.log(response.code);
```

### Python

```python
import requests

headers = {
    'Authorization': 'Bearer your-access-token',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:8000/api/v1/generate-code',
    headers=headers,
    json={
        'prompt': '创建一个计算阶乘的函数',
        'provider': 'openai',
        'language': 'python'
    }
)

result = response.json()
print(result['code'])
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/generate-code" \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个计算阶乘的函数",
    "provider": "openai",
    "language": "python"
  }'
```

## WebSocket支持（未来规划）

计划支持WebSocket实现实时代码生成和流式响应。

## 版本历史

### v1.0.0 (当前版本)
- 基础AI代码生成功能
- 多模型提供商支持
- 用户认证和配额管理
- 使用统计和历史记录
- 实时代码补全系统
- 上下文感知预测
- 多语言语法支持

### 未来版本规划
- v1.1.0: WebSocket支持、流式响应
- v1.2.0: 代码解释和优化建议
- v1.3.0: 多语言同时生成、代码对比

## 代码补全API

### 获取代码补全建议

#### POST /api/v1/completion/suggest
根据代码前缀和上下文获取智能补全建议。

**请求头**:
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

**请求体**:
```json
{
  "prefix": "def calculate_",
  "context": [
    "def add(a, b):",
    "    return a + b",
    ""
  ],
  "language": "python",
  "provider": "openai",
  "max_suggestions": 5,
  "temperature": 0.7
}
```

**参数说明**:
- `prefix` (必需): 待补全的代码前缀
- `context` (可选): 上下文代码行列表
- `language` (可选): 编程语言，默认为python
- `provider` (可选): AI提供商，默认为openai
- `max_suggestions` (可选): 最大建议数量，默认为5
- `temperature` (可选): 生成温度，默认为0.7

**成功响应 (200)**:
```json
{
  "suggestions": [
    {
      "text": "sum(numbers)",
      "confidence": 0.95,
      "relevance_score": 0.92,
      "language_features": ["function_call"],
      "metadata": {
        "models": ["gpt-4-turbo"],
        "consensus_score": 1.0
      }
    },
    {
      "text": "total(values)",
      "confidence": 0.85,
      "relevance_score": 0.78,
      "language_features": ["variable_reference"],
      "metadata": {}
    }
  ],
  "processing_time": 0.123,
  "tokens_used": 42,
  "model_used": "gpt-4-turbo",
  "cache_hit": false,
  "context_analyzed": true
}
```

### 分析代码上下文

#### POST /api/v1/completion/analyze-context
分析代码上下文以提供更精准的补全建议。

**请求参数**:
- `code_lines` (必需): 代码行列表的JSON字符串
- `cursor_position` (必需): 光标位置
- `language` (必需): 编程语言

**响应**:
```json
{
  "scope_level": "function",
  "syntax_context": "function_definition",
  "variable_declarations": ["a", "b"],
  "function_signatures": ["add"],
  "imported_modules": [],
  "current_indentation": 4
}
```

### 获取用户代码模式

#### GET /api/v1/completion/user-patterns
获取用户的代码使用模式和偏好。

**查询参数**:
- `language` (可选): 编程语言，默认为python
- `limit` (可选): 返回记录数限制，默认为10

**响应**:
```json
{
  "patterns": [
    {
      "code_snippet": "def test_function():\n    pass",
      "context": "",
      "usage_count": 5,
      "last_used": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### WebSocket实时连接

#### WebSocket /api/v1/completion/ws
建立实时WebSocket连接用于即时代码补全。

**连接示例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/completion/ws');

ws.onopen = () => {
  // 发送补全请求
  ws.send(JSON.stringify({
    type: 'completion_request',
    data: {
      prefix: 'def hello_',
      context: [],
      language: 'python'
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'completion_response') {
    console.log('补全建议:', message.data.suggestions);
  }
};
```

**支持的消息类型**:
- `completion_request`: 请求补全建议
- `context_update`: 更新上下文信息
- `completion_response`: 补全响应
- `context_analysis`: 上下文分析结果
- `error`: 错误信息

## 模型和类型定义

### CodeCompletion 接口
```typescript
interface CodeCompletion {
  suggest(prefix: string, context: string[]): Promise<string[]>
}
```

### 补全请求模型
```typescript
interface CompletionRequest {
  prefix: string;
  context: string[];
  language?: ProgrammingLanguage;
  provider?: ModelProvider;
  maxSuggestions?: number;
  temperature?: number;
  userId?: number;
}
```

### 补全建议模型
```typescript
interface CompletionSuggestion {
  text: string;
  confidence: number;
  relevanceScore: number;
  languageFeatures: string[];
  metadata: any;
}
```

## 技术支持

如有问题，请联系技术支持团队或查看GitHub Issues.