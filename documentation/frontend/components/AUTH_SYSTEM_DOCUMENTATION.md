# 用户认证系统完整文档

## 📋 概述

这是一个功能完整的用户认证系统，支持传统的邮箱密码认证和第三方OAuth认证（GitHub、Google）。系统采用模块化设计，可以在各种前端框架中使用。

## 🏗️ 系统架构

```
src/app/auth/
├── models/
│   └── auth.models.ts          # 数据模型定义
├── services/
│   ├── auth-state-manager.ts   # 状态管理
│   ├── auth-http-client.ts     # HTTP客户端
│   └── auth-main-service.ts    # 主认证服务
├── auth-page.html              # 认证页面模板
├── auth-page.scss              # 认证页面样式
└── index.ts                    # 入口文件
```

## 🔧 核心功能

### 1. 用户认证
- ✅ 邮箱密码注册/登录
- ✅ 第三方OAuth认证（GitHub、Google、微信、QQ）
- ✅ JWT令牌管理
- ✅ 自动令牌刷新
- ✅ 密码重置功能

### 2. 状态管理
- ✅ 用户认证状态跟踪
- ✅ 本地存储管理
- ✅ 实时状态更新
- ✅ 事件监听机制

### 3. 安全特性
- ✅ CSRF保护
- ✅ 令牌过期处理
- ✅ 权限验证
- ✅ 输入验证

## 🚀 快速开始

### 1. 安装和配置

```bash
# 系统已经包含在项目中，无需额外安装
```

### 2. 基本使用

```typescript
import { initAuth, getAuthService } from './auth';

// 初始化认证系统
const authService = initAuth({
  apiUrl: 'https://your-api.com',
  timeout: 10000,
  githubClientId: 'your_github_client_id',
  googleClientId: 'your_google_client_id'
});

// 检查认证状态
if (authService.isAuthenticated()) {
  console.log('用户已登录:', authService.getCurrentUser());
}

// 用户登录
await authService.signIn({
  email: 'user@example.com',
  password: 'password123'
});

// GitHub OAuth登录
await authService.signInWithGitHub();
```

### 3. 在HTML中使用

```html
<!-- 引入认证页面 -->
<iframe src="./auth/auth-page.html" width="100%" height="600px"></iframe>

<!-- 或者直接使用页面文件 -->
<!-- 打开 src/app/auth/auth-page.html -->
```

## 📊 API参考

### AuthService 方法

#### 基础认证方法

```typescript
// 用户注册
await authService.signUp({
  email: string,
  password: string,
  username?: string
}): Promise<AuthResponse>

// 用户登录
await authService.signIn({
  email: string,
  password: string
}): Promise<AuthResponse>

// 用户登出
await authService.logout(): Promise<void>

// 刷新令牌
await authService.refreshToken(): Promise<AuthResponse>
```

#### OAuth认证方法

```typescript
// GitHub登录
await authService.signInWithGitHub({
  redirectUri?: string,
  scopes?: string[],
  state?: string
}): Promise<void>

// Google登录
await authService.signInWithGoogle({
  redirectUri?: string,
  scopes?: string[],
  state?: string
}): Promise<void>

// 微信登录
await authService.signInWithWeChat({
  redirectUri?: string,
  scope?: 'snsapi_login' | 'snsapi_userinfo',
  state?: string
}): Promise<void>

// QQ登录
await authService.signInWithQQ({
  redirectUri?: string,
  scope?: string,
  state?: string
}): Promise<void>

// 处理OAuth回调
await authService.handleOAuthCallback(
  code: string,
  state: string
): Promise<AuthResponse>
```

#### 用户管理方法

```typescript
// 获取当前用户
authService.getCurrentUser(): User | null

// 检查认证状态
authService.isAuthenticated(): boolean

// 获取访问令牌
authService.getAccessToken(): string | null

// 更新用户信息
await authService.updateUser(userData: Partial<User>): Promise<User>

// 修改密码
await authService.changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void>
```

#### 权限管理方法

```typescript
// 获取用户权限
await authService.getUserPermissions(): Promise<string[]>

// 检查特定权限
await authService.hasPermission(permission: string): Promise<boolean>
```

### 状态监听

```typescript
// 添加状态变化监听器
authService.addAuthStateListener((isAuthenticated, user) => {
  console.log('认证状态变化:', isAuthenticated, user);
});

// 移除监听器
authService.removeAuthStateListener(listener);
```

## 🔐 安全配置

### 环境变量设置

```javascript
// 在全局window对象中设置
window.NG_APP_GITHUB_CLIENT_ID = 'your_github_client_id';
window.NG_APP_GOOGLE_CLIENT_ID = 'your_google_client_id';
```

### JWT令牌配置

```typescript
// 令牌管理器配置
const tokenManager = TokenManager.getInstance();
// 默认5分钟过期预警
```

## 🎨 UI组件

### 认证页面特点

- **响应式设计**：适配移动端和桌面端
- **暗色主题支持**：自动适配系统主题偏好
- **动画效果**：流畅的过渡动画
- **表单验证**：实时输入验证和错误提示
- **加载状态**：异步操作的视觉反馈

### 自定义样式

```scss
// 导入认证样式
@import './auth/auth-page.scss';

// 自定义变量覆盖
:root {
  --primary-color: #your-brand-color;
  --surface-color: #your-surface-color;
}
```

## 🛡️ 路由守卫

### 基础守卫

```typescript
import { authGuard } from './auth';

// 简单认证守卫
const isAuthenticated = await authGuard();
if (!isAuthenticated) {
  // 重定向到登录页面
  window.location.href = '/auth/login';
}

// 权限守卫
const hasPermission = await authGuard(['admin', 'editor']);
if (!hasPermission) {
  // 显示无权限页面
  showUnauthorizedPage();
}
```

### 框架集成示例

#### React Hook

```javascript
import { useAuth } from './auth';

function ProtectedComponent() {
  const { isAuthenticated, user, signIn, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <LoginForm />;
  }
  
  return (
    <div>
      <h1>欢迎, {user.username}!</h1>
      <button onClick={logout}>登出</button>
    </div>
  );
}
```

#### Vue Composition API

```javascript
import { useAuth } from './auth';

export default {
  setup() {
    const { isAuthenticated, user, signIn, logout } = useAuth();
    
    return {
      isAuthenticated,
      user,
      signIn,
      logout
    };
  }
};
```

## ⚙️ 高级配置

### 自动令牌刷新

```typescript
import { setupAutoTokenRefresh } from './auth';

// 启用自动刷新
setupAutoTokenRefresh();

// 现在所有401错误都会自动尝试刷新令牌
```

### 事件监听

```typescript
import { setupAuthEventListeners } from './auth';

// 设置事件监听器
const authService = setupAuthEventListeners();

// 监听自定义事件
window.addEventListener('auth:logout', () => {
  console.log('用户已登出');
  // 执行登出后的清理工作
});
```

### HTTP客户端配置

```typescript
import { authHttpClient } from './auth';

// 设置基础URL
authHttpClient.setBaseUrl('https://api.yourdomain.com');

// 设置超时时间
authHttpClient.setDefaultTimeout(15000);

// 带重试的请求
import { requestWithRetry } from './auth';

const response = await requestWithRetry(
  authHttpClient,
  { url: '/api/data', method: 'GET' },
  3, // 最大重试次数
  1000 // 重试延迟
);
```

## 🧪 测试和调试

### 开发工具

```typescript
// 启用详细日志
localStorage.setItem('debug_auth', 'true');

// 查看当前状态
console.log('认证状态:', {
  isAuthenticated: authService.isAuthenticated(),
  user: authService.getCurrentUser(),
  token: authService.getAccessToken()
});
```

### 模拟数据

```typescript
// 在开发环境中模拟认证
if (process.env.NODE_ENV === 'development') {
  // 预设测试用户
  const mockUser = {
    id: 'test-user-id',
    email: 'test@example.com',
    username: 'testuser'
  };
  
  authService.storeMockAuthData(mockUser, 'mock-token');
}
```

## 📱 移动端优化

### 触摸友好设计

- 大型触摸目标（最小44px）
- 适当的间距和边距
- 手势支持

### 性能优化

- 懒加载非关键资源
- 本地存储优化
- 减少重绘和回流

## 🔧 故障排除

### 常见问题

1. **令牌刷新失败**
   ```typescript
   // 检查网络连接
   // 验证刷新令牌有效性
   // 查看服务器日志
   ```

2. **OAuth回调失败**
   ```typescript
   // 验证state参数
   // 检查重定向URI配置
   // 确认客户端ID正确
   ```

3. **样式显示异常**
   ```scss
   // 检查CSS变量定义
   // 确认SCSS编译正确
   // 验证设计令牌导入
   ```

### 调试技巧

```typescript
// 启用调试模式
localStorage.setItem('auth_debug', 'true');

// 查看详细错误信息
window.addEventListener('auth:error', (event) => {
  console.error('认证错误详情:', event.detail);
});
```

## 📈 性能监控

### 关键指标

- 认证请求响应时间
- 令牌刷新成功率
- OAuth流程完成率
- 用户会话持续时间

### 监控实现

```typescript
// 性能监控示例
const metrics = {
  loginAttempts: 0,
  loginSuccess: 0,
  avgLoginTime: 0
};

// 记录性能数据
function recordMetric(name: string, value: number) {
  // 发送到分析服务
  analytics.track(name, { value });
}
```

## 🔄 未来扩展

### 计划功能

- [ ] 生物识别认证（指纹、面部识别）
- [ ] 多因素认证（MFA）
- [ ] 社交媒体集成（微信、QQ等）
- [ ] 企业认证（LDAP、SAML）
- [ ] 离线认证支持

### 架构改进

- [ ] 微前端架构支持
- [ ] 插件化认证提供者
- [ ] 更细粒度的权限控制
- [ ] 认证审计日志

## 📞 技术支持

如有问题，请联系：
- 📧 邮箱：support@imatuproject.com
- 🐛 GitHub Issues：[项目仓库](https://github.com/iMatuProject/auth-system)
- 💬 开发者社区：[Discord](https://discord.gg/imatuproject)

---

*本文档最后更新于：2024年*