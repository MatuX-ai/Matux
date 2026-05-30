# iMato AI Service SDK 文档

## 概述

iMato AI Service SDK 是一个TypeScript客户端库，用于与iMato AI服务进行交互。它支持多种AI模型提供商，提供完整的代码生成和管理功能。

## 安装

```bash
# 如果使用npm
npm install imato-ai-sdk

# 如果使用yarn
yarn add imato-ai-sdk
```

或者直接复制 `src/ai-sdk` 目录到你的项目中。

## 快速开始

### 1. 基础使用

```typescript
import { AIServiceClient, ModelProvider, ProgrammingLanguage } from './ai-sdk';

// 创建客户端实例
const client = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: 'your-access-token'
});

// 生成代码
const response = await client.generateCode({
  prompt: '创建一个计算斐波那契数列的函数',
  provider: ModelProvider.OPENAI,
  language: ProgrammingLanguage.PYTHON
});

console.log(response.code);
```

### 2. 使用预设模板

```typescript
// 生成React组件
const reactComponent = await client.generateWithTemplate(
  'reactComponent',
  'UserProfileCard',
  '{ name: string; email: string; avatar: string }'
);

// 生成API服务
const apiService = await client.generateWithTemplate(
  'apiService',
  'UserService',
  ['getUserById', 'createUser', 'updateUser', 'deleteUser']
);
```

## 核心概念

### 模型提供商

SDK支持以下AI模型提供商：

- `ModelProvider.OPENAI` - OpenAI GPT系列
- `ModelProvider.LINGMA` - Lingma代码专用模型
- `ModelProvider.DEEPSEEK` - DeepSeek代码模型
- `ModelProvider.ANTHROPIC` - Anthropic Claude系列
- `ModelProvider.GOOGLE` - Google Gemini系列

### 编程语言

支持的编程语言：

- `ProgrammingLanguage.PYTHON`
- `ProgrammingLanguage.JAVASCRIPT`
- `ProgrammingLanguage.TYPESCRIPT`
- `ProgrammingLanguage.JAVA`
- `ProgrammingLanguage.CSHARP`
- `ProgrammingLanguage.GO`
- `ProgrammingLanguage.RUST`
- `ProgrammingLanguage.CPP`
- `ProgrammingLanguage.PHP`
- `ProgrammingLanguage.RUBY`

## API参考

### AIServiceClient

#### 构造函数

```typescript
constructor(config: AIServiceConfig)
```

配置选项：
- `baseUrl`: API基础URL
- `accessToken`: 访问令牌（可选）
- `timeout`: 超时时间（毫秒，默认30000）
- `headers`: 默认请求头（可选）

#### 方法

##### generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse>

生成代码的主要方法。

```typescript
const response = await client.generateCode({
  prompt: '创建一个排序算法',
  provider: ModelProvider.OPENAI,
  language: ProgrammingLanguage.PYTHON,
  temperature: 0.7,
  maxTokens: 2000
});
```

##### getAvailableModels(): Promise<AvailableModelsResponse>

获取所有可用的AI模型。

##### getUsageStats(): Promise<UsageStats>

获取用户的使用统计信息。

##### getRecentRequests(limit?: number): Promise<AIRequestRecord[]>

获取最近的请求记录。

##### generateWithTemplate(template, ...args): Promise<CodeGenerationResponse>

使用预设模板生成代码。

##### generateCodeBatch(requests: CodeGenerationRequest[]): Promise<CodeGenerationResponse[]>

批量生成代码。

##### generateCodeWithRetry(request, maxRetries, retryDelay): Promise<CodeGenerationResponse>

带重试机制的代码生成。

### 预设模板

SDK提供了常用的代码生成模板：

```typescript
// React组件
client.generateReactComponent('Button', '{ onClick: () => void; children: React.ReactNode }')

// API服务
client.generateApiService('UserService', ['getUser', 'createUser', 'updateUser'])

// 数据模型
client.generateDataModel('User', ['id', 'name', 'email'])

// 工具函数
client.generateUtilityFunction('validateEmail', '验证邮箱格式')

// 单元测试
client.generateUnitTest('calculateSum', ['正数相加', '负数相加', '零值处理'])
```

## 错误处理

```typescript
try {
  const response = await client.generateCode(request);
  console.log(response.code);
} catch (error) {
  if (error instanceof HttpErrorImpl) {
    console.error('HTTP错误:', error.status, error.message);
  } else {
    console.error('未知错误:', error);
  }
}
```

## Angular集成

如果在Angular项目中使用，可以使用Angular包装器：

```typescript
import { AngularAIService } from './ai-sdk/angular-wrapper';

@Component({
  selector: 'app-code-generator',
  template: `
    <button (click)="generateCode()">生成代码</button>
    <pre>{{ generatedCode }}</pre>
  `
})
export class CodeGeneratorComponent {
  generatedCode = '';

  constructor(private aiService: AngularAIService) {
    // 设置访问令牌
    this.aiService.setAccessToken('your-token');
  }

  async generateCode() {
    try {
      const response = await this.aiService.generateCode({
        prompt: '创建一个简单的计算器函数',
        provider: ModelProvider.OPENAI
      });
      this.generatedCode = response.code;
    } catch (error) {
      console.error('生成失败:', error);
    }
  }
}
```

## 高级用法

### 动态配置切换

```typescript
// 切换不同的AI提供商
client.updateConfig({
  baseUrl: 'https://new-api.example.com'
});

// 切换访问令牌
client.setAccessToken('new-access-token');
```

### 自定义HTTP客户端

```typescript
import { HttpClient } from './ai-sdk/http-client';

const customClient = new HttpClient('https://api.example.com', 5000, {
  'X-Custom-Header': 'value'
});
```

### 批量处理

```typescript
const requests = [
  { prompt: '创建排序函数', language: ProgrammingLanguage.PYTHON },
  { prompt: '创建搜索函数', language: ProgrammingLanguage.JAVASCRIPT },
  { prompt: '创建验证函数', language: ProgrammingLanguage.TYPESCRIPT }
];

const responses = await client.generateCodeBatch(requests);
responses.forEach(response => {
  console.log(response.code);
});
```

## 最佳实践

### 1. 错误处理

```typescript
async function safeGenerateCode(client, request) {
  try {
    return await client.generateCode(request);
  } catch (error) {
    if (error.status === 401) {
      // 处理认证错误
      console.error('认证失败，请重新登录');
    } else if (error.status === 429) {
      // 处理限流错误
      console.error('请求过于频繁，请稍后再试');
    } else {
      console.error('生成代码失败:', error.message);
    }
    throw error;
  }
}
```

### 2. 性能优化

```typescript
// 使用缓存避免重复请求
const cache = new Map();

async function getCachedModels(client) {
  const cacheKey = 'available-models';
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }
  
  const models = await client.getAvailableModels();
  cache.set(cacheKey, models);
  return models;
}
```

### 3. 监控和日志

```typescript
// 添加请求监控
async function monitoredGenerateCode(client, request) {
  const startTime = Date.now();
  
  try {
    const response = await client.generateCode(request);
    const duration = Date.now() - startTime;
    
    console.log(`代码生成成功，耗时: ${duration}ms`);
    return response;
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`代码生成失败，耗时: ${duration}ms`, error);
    throw error;
  }
}
```

## 故障排除

### 常见问题

1. **认证错误 (401)**
   - 检查访问令牌是否正确
   - 确认令牌未过期
   - 验证API权限

2. **限流错误 (429)**
   - 实现重试机制
   - 增加请求间隔
   - 联系管理员提高配额

3. **超时错误**
   - 增加超时时间
   - 检查网络连接
   - 减少生成内容长度

4. **模型不可用**
   - 检查模型是否支持
   - 确认API密钥有效
   - 查看服务商状态

### 调试技巧

```typescript
// 启用详细日志
const client = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: 'token',
  timeout: 60000
});

// 监控请求
client.httpClient.request = async (config) => {
  console.log('发送请求:', config);
  const response = await originalRequest(config);
  console.log('收到响应:', response);
  return response;
};
```

## 贡献

欢迎提交Issue和Pull Request来改进SDK！

## 许可证

GPL-3.0