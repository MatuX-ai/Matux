# API 契约使用指南

## 🎯 快速开始

### 1. 访问 API 文档

**开发环境** (后端启动后):
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 2. 安装 TypeScript SDK

```bash
# 从 npm 安装 (发布后)
npm install @imatuproject/sdk

# 或本地链接
cd sdk/imatu-sdk-ts
npm link
```

### 3. 配置环境变量

**Angular 项目**:
```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000'
};
```

**React 项目**:
```bash
# .env 文件
REACT_APP_API_URL=http://localhost:8000
```

**Node.js 项目**:
```bash
# .env 文件或系统环境变量
API_BASE_URL=http://localhost:8000
```

---

## 💻 使用示例

### Angular 服务

```typescript
import { Injectable } from '@angular/core';
import { AuthService, AIServiceClient, LoginRequest } from '@imatuproject/sdk';
import { environment } from '../environments/environment';

@Injectable({ providedIn: 'root' })
export class MyAuthService {
  private authService: AuthService;

  constructor() {
    this.authService = new AuthService({
      baseUrl: environment.apiUrl
    });
  }

  async login(username: string, password: string) {
    const request: LoginRequest = { username, password };
    return await this.authService.login(request);
  }

  async logout() {
    return await this.authService.logout();
  }
}
```

### React 组件

```typescript
import React, { useState } from 'react';
import { AIAPI, CodeGenerationRequest } from '@imatuproject/sdk';

const CodeGenerator: React.FC = () => {
  const [code, setCode] = useState('');
  const aiApi = new AIAPI({ 
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    accessToken: userToken 
  });

  const handleGenerate = async (prompt: string) => {
    try {
      const request: CodeGenerationRequest = {
        prompt: '创建斐波那契数列函数',
        language: 'python',
        provider: 'openai'
      };
      
      const result = await aiApi.generateCode(request);
      setCode(result.code);
    } catch (error) {
      console.error('生成失败:', error);
    }
  };

  return (
    <button onClick={() => handleGenerate('fibonacci')}>
      生成代码
    </button>
  );
};
```

### 原生 JavaScript/TypeScript

```typescript
import { 
  createHttpClient, 
  httpGet, 
  httpPost 
} from '@imatuproject/sdk';

// 方法 1: 使用便捷函数
async function getUsers() {
  const response = await httpGet('/api/v1/users');
  return response.data;
}

// 方法 2: 使用自定义客户端
const client = createHttpClient('fetch', {
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  accessToken: 'your-token-here'
});

async function postData() {
  const response = await client.post('/api/v1/data', {
    name: 'test',
    value: 123
  });
  return response.data;
}
```

---

## 🔧 高级用法

### 1. 自定义 HTTP客户端

```typescript
import { FetchHttpClient } from '@imatuproject/sdk';

const httpClient = new FetchHttpClient({
  baseURL: 'https://api.imatuproject.com',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
  headers: {
    'X-Custom-Header': 'value',
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器
httpClient.interceptors.request.use((config) => {
  console.log('发送请求:', config.url);
  return config;
});

// 添加响应拦截器
httpClient.interceptors.response.use((response) => {
  console.log('收到响应:', response.status);
  return response;
}, (error) => {
  console.error('请求失败:', error);
  throw error;
});
```

### 2. 批量请求

```typescript
import { AIServiceClient } from '@imatuproject/sdk';

const aiClient = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: token
});

// 并行执行多个请求
async function batchGenerate() {
  const requests = [
    aiClient.generateCode({ prompt: 'Python 排序函数' }),
    aiClient.generateCode({ prompt: 'JS 数组去重' }),
    aiClient.generateCode({ prompt: 'TS 接口定义' })
  ];

  const results = await Promise.all(requests);
  return results;
}
```

### 3. 错误处理

```typescript
import { APIError } from '@imatuproject/sdk';

async function safeAPICall() {
  try {
    const result = await api.someEndpoint();
    return result;
  } catch (error) {
    if (error instanceof APIError) {
      // API 错误
      console.error('API 错误:', {
        code: error.code,
        message: error.message,
        status: error.status,
        details: error.details
      });
    } else if (error instanceof NetworkError) {
      // 网络错误
      console.error('网络连接失败');
    } else if (error instanceof TimeoutError) {
      // 超时错误
      console.error('请求超时');
    } else {
      // 其他错误
      console.error('未知错误:', error);
    }
    throw error;
  }
}
```

---

## 📦 SDK 模块说明

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| HTTP Client | `@imatuproject/sdk/http-client` | 统一的 HTTP客户端 |
| Types | `@imatuproject/sdk/types` | 类型定义 |
| Config | `@imatuproject/sdk/config` | 配置管理 |

### API 模块

| 模块 | 路径 | 端点前缀 | 说明 |
|------|------|----------|------|
| Auth API | `@imatuproject/sdk/auth` | `/api/v1/auth` | 认证授权 |
| AI API | `@imatuproject/sdk/ai` | `/api/v1/ai` | AI 服务 |
| Users API | `@imatuproject/sdk/users` | `/api/v1/users` | 用户管理 |
| Courses API | `@imatuproject/sdk/courses` | `/courses` | 课程管理 |

---

## 🔄 更新 SDK

### 自动更新 (推荐)

```bash
# 1. 确保后端服务运行
# 2. 导出最新 OpenAPI 规范
python scripts/export-openapi-simple.py

# 3. 重新生成 SDK (需要 Node.js)
node scripts/generate-sdk-simple.js

# 4. 发布新版本
cd sdk/imatu-sdk-ts
npm version patch  # 或 minor/major
npm publish
```

### 手动更新

```bash
# 1. 从后端获取最新 openapi.json
curl http://localhost:8000/openapi.json > sdk/imatu-sdk-ts/openapi.json

# 2. 使用 openapi-generator-cli 生成
npx @openapitools/openapi-generator-cli generate \
  -i sdk/imatu-sdk-ts/openapi.json \
  -g typescript-axios \
  -o sdk/imatu-sdk-ts/src/generated
```

---

## 🐛 常见问题

### Q1: 遇到 CORS 错误怎么办？

A: 确保后端已正确配置 CORS:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:4200', 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Q2: 如何处理认证令牌？

A: 在客户端初始化时传入:
```typescript
const client = new APIClient({
  baseURL: 'http://localhost:8000',
  accessToken: userToken  // JWT 令牌
});

// 或在运行时更新
client.setAccessToken(newToken);
```

### Q3: TypeScript 类型错误？

A: 确保安装了所有依赖:
```bash
npm install typescript @types/node --save-dev
```

### Q4: 如何在测试中使用 Mock?

A: 使用 Jest mock:
```typescript
jest.mock('@imatuproject/sdk', () => ({
  AuthService: jest.fn().mockImplementation(() => ({
    login: jest.fn().mockResolvedValue({ user: { id: 1 } })
  }))
}));
```

---

## 📚 相关资源

- **完整文档**: [API_CONTRACT_OPTIMIZATION_REPORT.md](./API_CONTRACT_OPTIMIZATION_REPORT.md)
- **后端API 映射**: [BACKEND_API_MAPPING.md](./BACKEND_API_MAPPING.md)
- **HTTP客户端指南**: [UNIFIED_HTTP_CLIENT_GUIDE.md](./UNIFIED_HTTP_CLIENT_GUIDE.md)
- **API设计规范**: [API_DESIGN_SPECIFICATION.md](./API_DESIGN_SPECIFICATION.md)

---

## ✅ 检查清单

在使用 API 契约前，请确认:

- [ ] 后端服务已启动并可以访问
- [ ] 能够访问 http://localhost:8000/docs
- [ ] SDK 已正确安装 (`npm list @imatuproject/sdk`)
- [ ] 环境变量已配置 (apiUrl 或 REACT_APP_API_URL)
- [ ] TypeScript 配置正确 (tsconfig.json)
- [ ] 能够导入 SDK 模块无错误

---

*最后更新：2026-03-02*  
*iMatuProject 开发团队*
