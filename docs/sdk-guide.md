# MatuX Project TypeScript SDK 使用指南

## 目录
1. [快速开始](#快速开始)
2. [安装和配置](#安装和配置)
3. [核心概念](#核心概念)
4. [API参考](#api参考)
5. [最佳实践](#最佳实践)
6. [故障排除](#故障排除)

## 快速开始

### 安装SDK

```bash
npm install @imatuproject/sdk
```

### 基本使用

```typescript
import { createSDK } from '@imatuproject/sdk';

// 创建SDK实例
const sdk = createSDK({
  baseURL: 'https://api.imatuproject.com',
  timeout: 10000
});

// 用户登录
const loginResult = await sdk.auth.login({
  username: 'your_username',
  password: 'your_password'
});

// 设置访问令牌
if (loginResult.success) {
  sdk.setAccessToken(loginResult.data.access_token);
}

// 获取用户信息
const user = await sdk.users.getCurrentUser();
console.log('当前用户:', user.data);
```

## 安装和配置

### 环境要求
- Node.js >= 16.0.0
- TypeScript >= 4.0.0 (可选，但推荐)
- 支持ES6+的现代浏览器或Node.js环境

### 安装方式

#### NPM安装
```bash
npm install @imatuproject/sdk
```

#### Yarn安装
```bash
yarn add @imatuproject/sdk
```

### 配置选项

```typescript
interface SDKConfig {
  baseURL: string;           // API基础URL
  accessToken?: string;      // 访问令牌
  timeout?: number;          // 请求超时时间(ms)
  headers?: Record<string, string>; // 自定义请求头
  onUnauthorized?: () => void;      // 未授权回调
  retries?: number;          // 重试次数
  retryDelay?: number;       // 重试延迟(ms)
}
```

### 完整配置示例

```typescript
import { createSDK, defaultConfig } from '@imatuproject/sdk';

const sdk = createSDK({
  ...defaultConfig,
  baseURL: 'https://api.imatuproject.com',
  timeout: 15000,
  headers: {
    'X-API-Version': '1.0.0',
    'X-Client-Version': '1.2.3'
  },
  onUnauthorized: () => {
    // 处理未授权情况
    console.warn('用户会话已过期，请重新登录');
    // 跳转到登录页面
    window.location.href = '/login';
  },
  retries: 3,
  retryDelay: 1000
});
```

## 核心概念

### SDK架构

SDK采用模块化设计，主要包含以下几个核心模块：

1. **认证模块** (`auth`) - 用户认证和授权
2. **用户模块** (`users`) - 用户管理相关功能
3. **AI模块** (`ai`) - AI服务接口
4. **课程模块** (`courses`) - 课程管理功能

### 错误处理

SDK统一了错误处理机制，所有API调用都返回标准化的响应格式：

```typescript
interface BaseResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
    status?: number;
    timestamp?: string;
  };
  timestamp: string;
}
```

### 使用示例

```typescript
try {
  const result = await sdk.users.getUserById('123');
  
  if (result.success) {
    console.log('用户信息:', result.data);
  } else {
    console.error('获取用户失败:', result.error?.message);
  }
} catch (error) {
  console.error('网络请求失败:', error);
}
```

## API参考

### 认证模块 (AuthAPI)

#### 用户登录
```typescript
const result = await sdk.auth.login({
  username: 'user@example.com',
  password: 'password123'
});
```

#### 用户注册
```typescript
const result = await sdk.auth.register({
  username: 'newuser',
  email: 'newuser@example.com',
  password: 'password123',
  confirmPassword: 'password123'
});
```

#### 刷新令牌
```typescript
const result = await sdk.auth.refreshToken({
  refresh_token: 'refresh-token-here'
});
```

#### 用户登出
```typescript
const result = await sdk.auth.logout();
```

### 用户模块 (UsersAPI)

#### 获取当前用户
```typescript
const result = await sdk.users.getCurrentUser();
```

#### 获取用户列表
```typescript
const result = await sdk.users.getUsers({
  page: 1,
  limit: 20,
  sort_by: 'created_at',
  sort_order: 'desc'
});
```

#### 搜索用户
```typescript
const result = await sdk.users.searchUsers('john', {
  page: 1,
  limit: 10
});
```

#### 获取指定用户
```typescript
const result = await sdk.users.getUserById('123');
```

### AI模块 (AIAPI)

#### 代码生成
```typescript
const result = await sdk.ai.generateCode({
  prompt: '创建一个计算斐波那契数列的函数',
  language: 'typescript',
  model: 'gpt-4',
  temperature: 0.7,
  max_tokens: 1000
});
```

#### 获取可用模型
```typescript
const result = await sdk.ai.getAvailableModels();
```

#### 获取使用统计
```typescript
const result = await sdk.ai.getUsageStats();
```

### 课程模块 (CoursesAPI)

#### 获取课程列表
```typescript
const result = await sdk.courses.getCourses({
  page: 1,
  limit: 20,
  category: 'programming',
  level: 'beginner'
});
```

#### 搜索课程
```typescript
const result = await sdk.courses.searchCourses('typescript', {
  page: 1,
  limit: 10
});
```

#### 获取课程详情
```typescript
const result = await sdk.courses.getCourseById('course-123');
```

#### 获取课程章节
```typescript
const result = await sdk.courses.getCourseChapters('course-123');
```

## 最佳实践

### 1. 令牌管理

```typescript
// 登录后保存令牌
const loginResult = await sdk.auth.login(credentials);
if (loginResult.success) {
  const token = loginResult.data.access_token;
  sdk.setAccessToken(token);
  localStorage.setItem('access_token', token);
}

// 应用启动时恢复令牌
const savedToken = localStorage.getItem('access_token');
if (savedToken) {
  sdk.setAccessToken(savedToken);
}
```

### 2. 错误处理

```typescript
async function handleAPIError(apiCall: () => Promise<any>) {
  try {
    const result = await apiCall();
    if (!result.success) {
      throw new Error(result.error?.message || 'API调用失败');
    }
    return result.data;
  } catch (error) {
    if (error.status === 401) {
      // 处理未授权
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    throw error;
  }
}

// 使用示例
const user = await handleAPIError(() => sdk.users.getCurrentUser());
```

### 3. 请求拦截和日志

```typescript
// 添加请求日志
const originalGet = sdk.client.get;
sdk.client.get = async function(...args) {
  console.log('API请求:', args[0]);
  const result = await originalGet.apply(this, args);
  console.log('API响应:', result);
  return result;
};
```

### 4. 批量操作

```typescript
// 批量获取用户信息
async function batchGetUsers(userIds: string[]) {
  const promises = userIds.map(id => sdk.users.getUserById(id));
  const results = await Promise.all(promises);
  return results.filter(result => result.success).map(result => result.data);
}
```

## 故障排除

### 常见问题

#### 1. CORS错误
**问题**: 浏览器控制台显示CORS错误
**解决方案**: 
- 确保API服务器配置了正确的CORS头
- 检查请求的Origin是否被允许
- 在开发环境中可以使用代理服务器

#### 2. 401未授权错误
**问题**: API返回401状态码
**解决方案**:
```typescript
// 检查令牌是否过期
if (error.status === 401) {
  // 清除本地存储的令牌
  localStorage.removeItem('access_token');
  sdk.clearAccessToken();
  // 重定向到登录页面
  window.location.href = '/login';
}
```

#### 3. 网络超时
**问题**: 请求经常超时
**解决方案**:
```typescript
const sdk = createSDK({
  baseURL: 'https://api.imatuproject.com',
  timeout: 30000, // 增加超时时间
  retries: 3,     // 启用重试机制
  retryDelay: 2000
});
```

#### 4. 类型不匹配
**问题**: TypeScript类型检查报错
**解决方案**:
```typescript
// 使用类型断言
const userData = result.data as User;

// 或者使用类型守卫
if (result.success && result.data) {
  const user: User = result.data;
}
```

### 调试技巧

#### 1. 启用详细日志
```typescript
// 在开发环境中启用详细日志
if (process.env.NODE_ENV === 'development') {
  sdk.client.interceptors.request.use(config => {
    console.log('请求配置:', config);
    return config;
  });
  
  sdk.client.interceptors.response.use(response => {
    console.log('响应数据:', response.data);
    return response;
  });
}
```

#### 2. 网络监控
```typescript
// 监控请求性能
const startTime = Date.now();
const result = await sdk.users.getUsers();
const endTime = Date.now();
console.log(`请求耗时: ${endTime - startTime}ms`);
```

### 支持和反馈

如遇到问题或有改进建议，请：
1. 查看[GitHub Issues](https://github.com/imatuproject/sdk/issues)
2. 联系技术支持邮箱: support@imatuproject.com
3. 加入开发者交流群组

---

*文档版本: 1.0.0*
*最后更新: 2026年2月28日*
