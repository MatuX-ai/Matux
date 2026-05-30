# 统一HTTP客户端使用指南

## 概述

本文档介绍了重构后的统一HTTP客户端的使用方法、特性以及最佳实践。

## 核心特性

### 1. 统一的API接口
- 基于原生fetch API实现
- 支持所有标准HTTP方法（GET、POST、PUT、DELETE、PATCH）
- 统一的请求/响应格式

### 2. 自动认证处理
- 自动添加认证头
- 令牌过期自动刷新
- 401错误自动重试

### 3. 智能重试机制
- 网络错误自动重试
- 服务器5xx错误重试
- 指数退避算法

### 4. 超时控制
- 可配置的请求超时
- AbortController支持

### 5. 拦截器支持
- 请求拦截器
- 响应拦截器

## 基本使用

### 导入和初始化

```typescript
import { unifiedHttpClient } from './core/services/unified-http-client';

// 设置基础URL（可选）
unifiedHttpClient.setBaseUrl('https://api.example.com');
// 设置默认超时时间（可选，默认10秒）
unifiedHttpClient.setDefaultTimeout(5000);
```

### 发起请求

```typescript
// GET请求
const getUsers = async () => {
  const response = await unifiedHttpClient.get('/users');
  return response.data;
};

// POST请求
const createUser = async (userData) => {
  const response = await unifiedHttpClient.post('/users', userData);
  return response.data;
};

// PUT请求
const updateUser = async (id, userData) => {
  const response = await unifiedHttpClient.put(`/users/${id}`, userData);
  return response.data;
};

// DELETE请求
const deleteUser = async (id) => {
  const response = await unifiedHttpClient.delete(`/users/${id}`);
  return response.data;
};
```

### 配置选项

```typescript
// 单次请求配置
const response = await unifiedHttpClient.get('/users', {
  timeout: 3000,        // 超时时间
  retries: 2,           // 重试次数
  retryDelay: 500,      // 重试延迟
  skipAuth: true,       // 跳过认证
  headers: {            // 自定义头
    'X-Custom-Header': 'value'
  }
});
```

## 高级功能

### 拦截器

```typescript
// 创建带拦截器的客户端实例
const clientWithInterceptors = UnifiedHttpClient.getInstance({
  interceptors: {
    request: (config) => {
      // 修改请求配置
      return {
        ...config,
        headers: {
          ...config.headers,
          'X-Request-ID': generateRequestId()
        }
      };
    },
    response: (response) => {
      // 修改响应数据
      return {
        ...response,
        data: {
          ...response.data,
          timestamp: new Date().toISOString()
        }
      };
    }
  }
});
```

### 错误处理

```typescript
import { HttpError } from './core/services/unified-http-client';

try {
  const response = await unifiedHttpClient.get('/users');
  console.log(response.data);
} catch (error) {
  if (error instanceof HttpError) {
    console.error(`HTTP错误 ${error.status}: ${error.message}`);
  } else {
    console.error('网络错误:', error.message);
  }
}
```

## 服务层集成示例

### 重构前的Angular服务

```typescript
@Injectable()
export class OldUserService {
  constructor(private http: HttpClient) {}
  
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>('/api/users')
      .pipe(catchError(this.handleError));
  }
  
  private handleError(error: any): Observable<never> {
    // 复杂的错误处理逻辑
    return throwError(() => new Error('请求失败'));
  }
}
```

### 重构后的服务

```typescript
@Injectable()
export class NewUserService {
  constructor() {}
  
  async getUsers(): Promise<User[]> {
    const response = await unifiedHttpClient.get<User[]>('/api/users');
    return response.data;
  }
}
```

## 最佳实践

### 1. 错误处理
```typescript
// 推荐：使用try-catch处理异步错误
async function fetchUserData(userId) {
  try {
    const response = await unifiedHttpClient.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    // 记录错误并返回默认值
    console.error('获取用户数据失败:', error);
    return null;
  }
}
```

### 2. 超时设置
```typescript
// 对于长时间运行的操作，设置合适的超时时间
const longRunningOperation = async () => {
  return await unifiedHttpClient.post('/process-data', data, {
    timeout: 30000 // 30秒超时
  });
};
```

### 3. 重试策略
```typescript
// 对于关键操作，增加重试次数
const criticalOperation = async () => {
  return await unifiedHttpClient.post('/critical-action', data, {
    retries: 5,
    retryDelay: 1000
  });
};
```

### 4. 认证处理
```typescript
// 公共API跳过认证
const getPublicData = async () => {
  return await unifiedHttpClient.get('/public/data', {
    skipAuth: true
  });
};
```

## 迁移指南

### 从Angular HttpClient迁移

1. **替换导入**
```typescript
// 旧代码
import { HttpClient } from '@angular/common/http';

// 新代码
import { unifiedHttpClient } from './core/services/unified-http-client';
```

2. **修改方法签名**
```typescript
// 旧代码
getUsers(): Observable<User[]> {
  return this.http.get<User[]>('/api/users');
}

// 新代码
async getUsers(): Promise<User[]> {
  const response = await unifiedHttpClient.get<User[]>('/api/users');
  return response.data;
}
```

3. **处理响应**
```typescript
// 旧代码
this.userService.getUsers().subscribe(users => {
  this.users = users;
});

// 新代码
this.users = await this.userService.getUsers();
```

### 从自定义HTTP客户端迁移

如果你之前有自定义的HTTP客户端，可以直接替换为统一客户端：

```typescript
// 旧代码
class MyCustomClient {
  async get(url) {
    // 自定义实现
  }
}

// 新代码
// 直接使用 unifiedHttpClient
```

## 性能优化建议

### 1. 批量请求
```typescript
// 使用Promise.all进行并发请求
const [users, posts, comments] = await Promise.all([
  unifiedHttpClient.get('/users'),
  unifiedHttpClient.get('/posts'),
  unifiedHttpClient.get('/comments')
]);
```

### 2. 缓存策略
```typescript
// 对于不经常变化的数据，可以添加缓存层
class DataService {
  private cache = new Map();
  
  async getData(key) {
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }
    
    const response = await unifiedHttpClient.get(`/data/${key}`);
    this.cache.set(key, response.data);
    return response.data;
  }
}
```

### 3. 请求合并
```typescript
// 将多个小请求合并为一个批量请求
const batchRequest = async (ids) => {
  return await unifiedHttpClient.post('/batch-get', { ids });
};
```

## 故障排除

### 常见问题

1. **认证失败**
   - 检查localStorage中的access_token是否存在
   - 确认令牌是否过期
   - 查看控制台是否有401错误

2. **网络超时**
   - 增加timeout配置
   - 检查网络连接
   - 确认服务器响应时间

3. **重试过多**
   - 检查服务器状态
   - 确认请求参数是否正确
   - 查看是否有循环重试的情况

### 调试技巧

```typescript
// 启用详细日志
const debugClient = UnifiedHttpClient.getInstance({
  interceptors: {
    request: (config) => {
      console.log('请求发送:', config);
      return config;
    },
    response: (response) => {
      console.log('收到响应:', response);
      return response;
    }
  }
});
```

## API参考

### UnifiedHttpClient 类

#### 方法

- `get<T>(url, config?)`: Promise<HttpResponse<T>>
- `post<T>(url, body?, config?)`: Promise<HttpResponse<T>>
- `put<T>(url, body?, config?)`: Promise<HttpResponse<T>>
- `delete<T>(url, config?)`: Promise<HttpResponse<T>>
- `patch<T>(url, body?, config?)`: Promise<HttpResponse<T>>

#### 配置方法

- `setBaseUrl(url)`: void
- `setDefaultTimeout(timeout)`: void
- `setDefaultRetries(retries)`: void
- `setDefaultRetryDelay(delay)`: void

### 类型定义

```typescript
interface HttpRequestConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  skipAuth?: boolean;
}

interface HttpResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}
```

## 版本历史

- v1.0.0: 初始版本，包含基础HTTP功能
- v1.1.0: 添加拦截器支持
- v1.2.0: 优化重试机制和错误处理

## 贡献指南

如有改进建议或发现问题，请提交issue或pull request。