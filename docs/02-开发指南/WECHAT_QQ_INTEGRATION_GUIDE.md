# 微信QQ登录集成指南

## 📋 概述

本文档详细介绍如何配置和集成微信、QQ第三方登录功能到认证系统中。

## 🚀 平台申请与配置

### 微信开放平台配置

#### 1. 注册开发者账号
- 访问 [微信开放平台](https://open.weixin.qq.com/)
- 注册企业开发者账号（个人账号不支持网站应用）

#### 2. 创建网站应用
1. 进入管理中心 → 网站应用 → 创建网站应用
2. 填写应用信息：
   - 应用名称：您的应用名称
   - 应用简介：应用描述
   - 应用官网：https://yourdomain.com
   - 授权回调域名：yourdomain.com（不带http://前缀）

#### 3. 获取应用凭证
```
AppID: wx******************
AppSecret: **************************
```

### QQ互联平台配置

#### 1. 注册开发者账号
- 访问 [QQ互联](https://connect.qq.com/)
- 使用QQ账号登录并完善开发者信息

#### 2. 创建应用
1. 进入应用管理 → 创建应用 → 网站应用
2. 填写应用信息：
   - 应用名称：您的应用名称
   - 应用简介：应用描述
   - 网站地址：https://yourdomain.com
   - 回调地址：https://yourdomain.com/auth/callback

#### 3. 获取应用凭证
```
AppID: **********
AppKey: ********************************
```

## ⚙️ 环境变量配置

### 前端环境变量

在项目根目录创建 `.env` 文件：

```bash
# 微信配置
NG_APP_WECHAT_APP_ID=wx******************

# QQ配置  
NG_APP_QQ_APP_ID=**********

# 其他OAuth配置
NG_APP_GITHUB_CLIENT_ID=**********
NG_APP_GOOGLE_CLIENT_ID=**********
```

### 后端环境变量

```bash
# 微信密钥
WECHAT_APP_SECRET=**************************

# QQ密钥
QQ_APP_SECRET=********************************

# 其他配置
GITHUB_CLIENT_SECRET=**********
GOOGLE_CLIENT_SECRET=**********
```

## 🔧 代码集成示例

### 前端使用示例

```typescript
import { getAuthService } from './auth';

const authService = getAuthService();

// 微信登录
async function loginWithWeChat() {
  try {
    await authService.signInWithWeChat({
      redirectUri: 'https://yourdomain.com/auth/callback',
      scope: 'snsapi_login', // 或 'snsapi_userinfo'
      state: generateRandomState()
    });
  } catch (error) {
    console.error('微信登录失败:', error);
  }
}

// QQ登录
async function loginWithQQ() {
  try {
    await authService.signInWithQQ({
      redirectUri: 'https://yourdomain.com/auth/callback',
      scope: 'get_user_info',
      state: generateRandomState()
    });
  } catch (error) {
    console.error('QQ登录失败:', error);
  }
}
```

### 回调处理示例

```typescript
// 处理OAuth回调
async function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  const state = urlParams.get('state');
  
  if (code && state) {
    try {
      const authResponse = await authService.handleOAuthCallback(code, state);
      console.log('认证成功:', authResponse.user);
      // 跳转到首页或其他页面
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('认证失败:', error);
      // 显示错误信息
    }
  }
}
```

## 🛠️ 后端API接口

### 微信登录回调接口

```python
# FastAPI示例
@app.post("/auth/wechat/callback")
async def wechat_callback(code: str, state: str):
    # 1. 验证state参数
    if not validate_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # 2. 通过code获取access_token
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(token_url, params=params)
        token_data = token_response.json()
        
        if "errcode" in token_data:
            raise HTTPException(status_code=400, detail=token_data["errmsg"])
        
        # 3. 获取用户信息
        user_info_url = "https://api.weixin.qq.com/sns/userinfo"
        user_params = {
            "access_token": token_data["access_token"],
            "openid": token_data["openid"],
            "lang": "zh_CN"
        }
        
        user_response = await client.get(user_info_url, params=user_params)
        user_info = user_response.json()
        
        # 4. 创建或更新用户
        user = await create_or_update_user_from_wechat(user_info)
        
        # 5. 生成JWT令牌
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return {
            "user": user,
            "accessToken": access_token,
            "refreshToken": refresh_token
        }
```

### QQ登录回调接口

```python
@app.post("/auth/qq/callback")
async def qq_callback(code: str, state: str):
    # 1. 验证state参数
    if not validate_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # 2. 获取access_token
    token_url = "https://graph.qq.com/oauth2.0/token"
    params = {
        "client_id": settings.QQ_APP_ID,
        "client_secret": settings.QQ_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://yourdomain.com/auth/callback"
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(token_url, params=params)
        # QQ返回的是URL编码格式，需要解析
        token_data = parse_qs(token_response.text)
        
        access_token = token_data.get("access_token", [None])[0]
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # 3. 获取openid
        openid_url = "https://graph.qq.com/oauth2.0/me"
        openid_params = {"access_token": access_token}
        openid_response = await client.get(openid_url, params=openid_params)
        openid_data = json.loads(
            openid_response.text.replace("callback(", "").replace(");", "")
        )
        openid = openid_data["openid"]
        
        # 4. 获取用户信息
        user_info_url = "https://graph.qq.com/user/get_user_info"
        user_params = {
            "access_token": access_token,
            "oauth_consumer_key": settings.QQ_APP_ID,
            "openid": openid
        }
        
        user_response = await client.get(user_info_url, params=user_params)
        user_info = user_response.json()
        
        if user_info["ret"] != 0:
            raise HTTPException(status_code=400, detail=user_info["msg"])
        
        # 5. 创建或更新用户
        user = await create_or_update_user_from_qq(user_info, openid)
        
        # 6. 生成JWT令牌
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return {
            "user": user,
            "accessToken": access_token,
            "refreshToken": refresh_token
        }
```

## 🎨 UI组件定制

### 微信登录按钮样式

```scss
.wechat-login-btn {
  background: #07c160;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: background 0.2s;
  
  &:hover {
    background: #06ad56;
  }
  
  .wechat-icon {
    font-size: 18px;
  }
}
```

### QQ登录按钮样式

```scss
.qq-login-btn {
  background: #12b7f5;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: background 0.2s;
  
  &:hover {
    background: #0fa9e6;
  }
  
  .qq-icon {
    font-size: 18px;
  }
}
```

## 🔒 安全注意事项

### 1. State参数验证
```typescript
// 生成安全的state参数
function generateSecureState(): string {
  return crypto.randomUUID() + Date.now().toString(36);
}

// 验证state参数
function validateState(receivedState: string, storedState: string): boolean {
  return receivedState === storedState && 
         Date.now() - parseInt(storedState.split('-')[1], 36) < 300000; // 5分钟过期
}
```

### 2. 回调域名白名单
确保只允许预配置的域名进行回调：
```python
ALLOWED_REDIRECT_URIS = [
    "https://yourdomain.com/auth/callback",
    "http://localhost:3000/auth/callback"
]
```

### 3. 令牌安全存储
```javascript
// 安全存储访问令牌
function storeAccessToken(token: string): void {
  // 使用HttpOnly cookie存储刷新令牌
  document.cookie = `refresh_token=${token}; Secure; HttpOnly; SameSite=Strict; Path=/`;
  
  // 内存中存储访问令牌
  sessionStorage.setItem('access_token', token);
}
```

## 📱 移动端适配

### 微信内嵌网页
```typescript
// 检测是否在微信浏览器中
function isInWeChat(): boolean {
  return /MicroMessenger/i.test(navigator.userAgent);
}

// 微信内使用不同的授权方式
if (isInWeChat()) {
  // 使用微信JS-SDK进行授权
  await wechatJsSdkAuth();
} else {
  // 使用普通网页授权
  await authService.signInWithWeChat();
}
```

### 手机QQ内嵌网页
```typescript
// 检测是否在手机QQ中
function isInMobileQQ(): boolean {
  return /QQ/i.test(navigator.userAgent);
}

if (isInMobileQQ()) {
  // 使用QQ提供的JSBridge
  await qqJsBridgeAuth();
} else {
  // 使用普通网页授权
  await authService.signInWithQQ();
}
```

## 🐛 常见问题排查

### 1. 回调地址不匹配
**问题**：出现"redirect_uri参数错误"
**解决方案**：
- 确保回调地址与平台配置完全一致
- 注意http/https协议的区别
- 检查是否有端口号差异

### 2. State参数验证失败
**问题**：state参数不匹配或已过期
**解决方案**：
- 检查state生成和存储逻辑
- 确保state在前后端传递过程中未被修改
- 调整过期时间设置

### 3. 获取用户信息失败
**问题**：access_token无效或权限不足
**解决方案**：
- 检查AppSecret是否正确
- 确认应用权限配置
- 验证scope参数设置

## 📊 监控和日志

### 认证成功率监控
```typescript
// 记录认证事件
function logAuthEvent(provider: string, success: boolean, error?: string) {
  analytics.track('oauth_login', {
    provider,
    success,
    error,
    timestamp: new Date().toISOString()
  });
}
```

### 错误日志收集
```python
# 后端错误日志
logger.error(f"WeChat auth failed: {error_detail}", extra={
    "provider": "wechat",
    "error_code": error_code,
    "user_agent": request.headers.get("User-Agent")
})
```

## 🔄 后续优化建议

### 1. 统一认证流程
```typescript
// 创建统一的OAuth处理器
class OAuthHandler {
  async handleLogin(provider: 'wechat' | 'qq' | 'github' | 'google', options: any) {
    switch (provider) {
      case 'wechat':
        return this.handleWeChatLogin(options);
      case 'qq':
        return this.handleQQLogin(options);
      // ... 其他提供商
    }
  }
}
```

### 2. 缓存优化
```typescript
// 缓存用户信息减少API调用
const userCache = new Map();
const CACHE_TTL = 3600000; // 1小时

function getCachedUserInfo(openid: string) {
  const cached = userCache.get(openid);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  return null;
}
```

---

*文档更新时间：2024年*