# API参考文档

## 目录
1. [认证接口](#认证接口)
2. [用户管理接口](#用户管理接口)
3. [AI服务接口](#ai服务接口)
4. [课程管理接口](#课程管理接口)
5. [数据模型](#数据模型)

## 认证接口

### POST /api/v1/auth/login
用户登录认证

**请求参数:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user"
    }
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### POST /api/v1/auth/register
用户注册

**请求参数:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirmPassword": "string"
}
```

### POST /api/v1/auth/refresh
刷新访问令牌

**请求参数:**
```json
{
  "refresh_token": "string"
}
```

### POST /api/v1/auth/logout
用户登出

**响应:**
```json
{
  "success": true,
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## 用户管理接口

### GET /api/v1/users/me
获取当前用户信息

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "avatar": "https://example.com/avatar.jpg",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-02-28T12:00:00Z"
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### GET /api/v1/users
获取用户列表

**查询参数:**
- `page` (integer, optional): 页码，默认1
- `limit` (integer, optional): 每页数量，默认20
- `sort_by` (string, optional): 排序字段
- `sort_order` (string, optional): 排序方向 (asc/desc)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "user",
        "created_at": "2026-01-01T00:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### GET /api/v1/users/{id}
获取指定用户信息

**路径参数:**
- `id` (string): 用户ID

### GET /api/v1/users/search
搜索用户

**查询参数:**
- `q` (string, required): 搜索关键词
- `page` (integer, optional): 页码
- `limit` (integer, optional): 每页数量

## AI服务接口

### POST /api/v1/ai/generate-code
AI代码生成

**请求参数:**
```json
{
  "prompt": "string",
  "language": "string",
  "model": "string",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "code": "function fibonacci(n) {\n  if (n <= 1) return n;\n  return fibonacci(n - 1) + fibonacci(n - 2);\n}",
    "explanation": "这是一个递归实现的斐波那契数列函数...",
    "language": "javascript",
    "model": "gpt-4",
    "usage": {
      "prompt_tokens": 50,
      "completion_tokens": 120,
      "total_tokens": 170
    }
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### POST /api/v1/ai/generate-text
AI文本生成

**请求参数:**
```json
{
  "prompt": "string",
  "model": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1
}
```

### POST /api/v1/ai/generate-image
AI图像生成

**请求参数:**
```json
{
  "prompt": "string",
  "model": "string",
  "size": "1024x1024",
  "quality": "standard"
}
```

### GET /api/v1/ai/models
获取可用AI模型列表

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "OpenAI",
      "capabilities": ["text-generation", "code-generation"],
      "is_available": true
    }
  ],
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### GET /api/v1/ai/usage
获取AI使用统计

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_requests": 1000,
    "total_tokens": 50000,
    "daily_usage": [
      {
        "date": "2026-02-28",
        "requests": 50,
        "tokens": 2500
      }
    ]
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## 课程管理接口

### GET /api/v1/courses
获取课程列表

**查询参数:**
- `page` (integer, optional): 页码
- `limit` (integer, optional): 每页数量
- `category` (string, optional): 课程分类
- `level` (string, optional): 课程难度级别
- `sort_by` (string, optional): 排序字段
- `sort_order` (string, optional): 排序方向

**响应示例:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": 1,
        "title": "TypeScript入门教程",
        "description": "从零开始学习TypeScript",
        "category": "programming",
        "level": "beginner",
        "duration": 120,
        "instructor_id": 1,
        "price": 99.99,
        "thumbnail": "https://example.com/thumbnail.jpg",
        "is_published": true,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-02-28T12:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20,
    "totalPages": 3
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### GET /api/v1/courses/{id}
获取课程详情

**路径参数:**
- `id` (string): 课程ID

### POST /api/v1/courses
创建课程

**请求参数:**
```json
{
  "title": "string",
  "description": "string",
  "category": "string",
  "level": "string",
  "duration": 120,
  "price": 99.99,
  "thumbnail": "string"
}
```

### PUT /api/v1/courses/{id}
更新课程

**路径参数:**
- `id` (string): 课程ID

**请求参数:**
```json
{
  "title": "string",
  "description": "string",
  "category": "string",
  "level": "string",
  "duration": 120,
  "price": 99.99,
  "thumbnail": "string",
  "is_published": true
}
```

### DELETE /api/v1/courses/{id}
删除课程

**路径参数:**
- `id` (string): 课程ID

### GET /api/v1/courses/{id}/chapters
获取课程章节

**路径参数:**
- `id` (string): 课程ID

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "course_id": 1,
      "title": "第一章：基础概念",
      "order": 1,
      "content": "本章介绍TypeScript的基本概念...",
      "video_url": "https://example.com/video.mp4",
      "duration": 30,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### POST /api/v1/courses/{id}/enroll
注册课程

**路径参数:**
- `id` (string): 课程ID

### GET /api/v1/courses/my
获取我的课程

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "TypeScript入门教程",
      "progress": 0.75,
      "enrolled_at": "2026-02-01T00:00:00Z"
    }
  ],
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### GET /api/v1/courses/search
搜索课程

**查询参数:**
- `q` (string, required): 搜索关键词
- `page` (integer, optional): 页码
- `limit` (integer, optional): 每页数量
- `category` (string, optional): 课程分类
- `level` (string, optional): 课程难度

## 数据模型

### User (用户)
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
}
```

### Course (课程)
```typescript
interface Course {
  id: number;
  title: string;
  description: string;
  category: string;
  level: string;
  duration: number;
  instructor_id: number;
  price?: number;
  thumbnail?: string;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}
```

### Chapter (章节)
```typescript
interface Chapter {
  id: number;
  course_id: number;
  title: string;
  order: number;
  content?: string;
  video_url?: string;
  duration: number;
  created_at: string;
}
```

### AuthResponse (认证响应)
```typescript
interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
```

### CodeGenerationResponse (代码生成响应)
```typescript
interface CodeGenerationResponse {
  code: string;
  explanation: string;
  language: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
```

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "details": {
      "field": "username",
      "message": "用户名不能为空"
    },
    "status": 400,
    "timestamp": "2026-02-28T12:00:00Z"
  },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### 常见错误码
- `VALIDATION_ERROR`: 输入验证错误
- `AUTHENTICATION_FAILED`: 认证失败
- `UNAUTHORIZED`: 未授权访问
- `NOT_FOUND`: 资源不存在
- `INTERNAL_SERVER_ERROR`: 服务器内部错误
- `RATE_LIMIT_EXCEEDED`: 请求频率超限

---
*API版本: v1.0*
*最后更新: 2026年2月28日*