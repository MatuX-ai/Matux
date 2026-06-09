# AI代码生成功能认证集成方案

## 概述

本文档描述如何将AI代码生成功能与现有的认证系统集成，确保只有授权用户才能使用AI服务。

## 当前认证系统分析

从项目代码可以看出，已有完善的认证系统：

### 核心认证组件

1. **AuthService** (`src/app/core/services/auth.service.ts`)
   - 提供完整的用户认证功能
   - 支持JWT令牌管理
   - 包含登录、注册、令牌刷新等功能

2. **AuthStateManager** (`src/app/core/services/auth-state-manager.ts`)
   - 管理认证状态
   - 处理令牌存储和验证

3. **AuthHttpClient** (`src/app/core/services/auth-http-client.ts`)
   - 带认证的HTTP客户端
   - 自动处理令牌刷新

## 集成方案

### 1. 后端认证集成

#### 修改AI路由添加认证中间件

```python
# backend/routes/ai_routes.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前认证用户"""
    # 验证JWT令牌
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# 在路由中添加依赖
@router.post("/generate-code")
async def generate_code(
    request: CodeGenerationRequest,
    current_user_id: int = Depends(get_current_user)  # 添加认证依赖
):
    # 记录用户ID
    ai_request = AIRequest(
        user_id=current_user_id,  # 使用认证的用户ID
        prompt=request.prompt,
        # ... 其他字段
    )
```

### 2. 前端认证集成

#### 修改AI SDK添加认证支持

```typescript
// src/ai-sdk/ai-client.ts
export class AIServiceClient {
  private accessToken: string | null = null;
  
  setAccessToken(token: string): void {
    this.accessToken = token;
  }
  
  clearAccessToken(): void {
    this.accessToken = null;
  }
  
  private getAuthHeaders(): Record<string, string> {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }
    return {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json'
    };
  }
  
  async generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse> {
    if (!this.accessToken) {
      throw new Error('Authentication required');
    }
    
    const response = await this.httpClient.post<CodeGenerationResponse>(
      '/api/v1/generate-code',
      request,
      { headers: this.getAuthHeaders() }
    );
    
    return response.data;
  }
}
```

#### 与现有AuthService集成

```typescript
// src/app/ai-code-generator/ai-code-generator.component.ts
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-ai-code-generator',
  templateUrl: './ai-code-generator.component.html'
})
export class AICodeGeneratorComponent implements OnInit {
  private subscription: Subscription;
  
  constructor(
    private authService: AuthService,
    private aiService: AngularAIService
  ) {}
  
  ngOnInit(): void {
    // 监听认证状态变化
    this.subscription = this.authService.isAuthenticated$.subscribe(isAuthenticated => {
      if (isAuthenticated) {
        // 获取访问令牌并设置到AI服务
        const token = this.authService.getAccessToken();
        this.aiService.setAccessToken(token);
      } else {
        // 清除AI服务的令牌
        this.aiService.clearAccessToken();
      }
    });
  }
  
  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
```

### 3. 权限控制系统

#### 用户角色定义

```typescript
// src/app/core/models/auth.models.ts
export enum UserRole {
  USER = 'user',
  PREMIUM = 'premium',
  ADMIN = 'admin'
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  // ... 其他字段
}
```

#### AI使用权限控制

```python
# backend/models/user.py
class User(Base):
    # ... 现有字段
    role = Column(String(20), default=UserRole.USER)
    ai_quota_daily = Column(Integer, default=10)  # 每日AI使用额度
    ai_quota_reset_at = Column(DateTime(timezone=True))

# backend/routes/ai_routes.py
async def check_ai_quota(user_id: int, db: AsyncSession):
    """检查用户AI使用配额"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查每日限额
    today = datetime.utcnow().date()
    if user.ai_quota_reset_at and user.ai_quota_reset_at.date() < today:
        # 重置配额
        user.ai_quota_daily = 10 if user.role == UserRole.USER else 100
        user.ai_quota_reset_at = datetime.utcnow()
        await db.commit()
    
    if user.ai_quota_daily <= 0:
        raise HTTPException(
            status_code=429, 
            detail="Daily AI quota exceeded. Please upgrade your plan."
        )
    
    # 减少配额
    user.ai_quota_daily -= 1
    await db.commit()

@router.post("/generate-code")
async def generate_code(
    request: CodeGenerationRequest,
    current_user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 检查配额
    await check_ai_quota(current_user_id, db)
    
    # 继续处理AI请求...
```

### 4. 前端权限控制

#### 基于角色的UI控制

```typescript
// src/app/ai-code-generator/ai-code-generator.component.ts
export class AICodeGeneratorComponent {
  userRole: UserRole = UserRole.USER;
  dailyQuota: number = 0;
  usedQuota: number = 0;
  
  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.userRole = user.role;
        this.loadUserQuota(user.id);
      }
    });
  }
  
  async loadUserQuota(userId: number): Promise<void> {
    try {
      const stats = await this.aiService.getUsageStats();
      this.dailyQuota = this.getQuotaByRole(this.userRole);
      this.usedQuota = stats.todayUsage;
    } catch (error) {
      console.error('Failed to load user quota:', error);
    }
  }
  
  getQuotaByRole(role: UserRole): number {
    switch (role) {
      case UserRole.USER: return 10;
      case UserRole.PREMIUM: return 100;
      case UserRole.ADMIN: return 1000;
      default: return 10;
    }
  }
  
  get remainingQuota(): number {
    return Math.max(0, this.dailyQuota - this.usedQuota);
  }
  
  get isQuotaExceeded(): boolean {
    return this.remainingQuota <= 0;
  }
}
```

#### HTML模板中的权限控制

```html
<!-- src/app/ai-code-generator/ai-code-generator.component.html -->
<div class="quota-info" *ngIf="userRole !== UserRole.ADMIN">
  <div class="quota-bar">
    <div class="quota-used" [style.width.%]="(usedQuota / dailyQuota) * 100"></div>
  </div>
  <p>今日剩余配额: {{ remainingQuota }}/{{ dailyQuota }}</p>
</div>

<button 
  type="submit" 
  class="btn btn-primary"
  [disabled]="isGenerating || isQuotaExceeded"
  *ngIf="isAuthenticated">
  <span *ngIf="!isQuotaExceeded">✨ 生成代码</span>
  <span *ngIf="isQuotaExceeded">🚫 配额已用完</span>
</button>

<div class="upgrade-prompt" *ngIf="isQuotaExceeded && userRole === UserRole.USER">
  <p>升级到高级账户可获得更多AI使用配额</p>
  <button class="btn btn-secondary" (click)="upgradeAccount()">立即升级</button>
</div>
```

### 5. 错误处理和用户体验

#### 认证错误处理

```typescript
// src/ai-sdk/ai-client.ts
export class AIServiceClient {
  async generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse> {
    try {
      const response = await this.makeRequest(request);
      return response;
    } catch (error) {
      if (error.status === 401) {
        // 令牌过期，触发重新登录
        this.authService.logout();
        this.router.navigate(['/auth/login']);
        throw new Error('会话已过期，请重新登录');
      } else if (error.status === 429) {
        throw new Error('今日AI使用配额已用完');
      } else {
        throw error;
      }
    }
  }
}
```

### 6. 部署配置

#### 环境变量配置

```bash
# .env
# 认证配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI服务配额配置
DEFAULT_USER_QUOTA=10
PREMIUM_USER_QUOTA=100
ADMIN_USER_QUOTA=1000
```

## 安全考虑

### 1. 令牌安全
- 使用HTTPS传输所有认证相关数据
- 实施合理的令牌过期策略
- 支持令牌刷新机制

### 2. 输入验证
- 对所有用户输入进行严格验证
- 防止SQL注入和XSS攻击
- 限制请求频率防止滥用

### 3. 日志记录
- 记录所有AI请求和响应
- 监控异常使用模式
- 审计用户操作

## 测试方案

### 单元测试
```typescript
// tests/auth.integration.spec.ts
describe('AI Service Authentication Integration', () => {
  it('should reject requests without valid token', async () => {
    const client = new AIServiceClient({ baseUrl: 'http://localhost:8000' });
    await expect(client.generateCode(testRequest)).rejects.toThrow('Authentication required');
  });
  
  it('should allow requests with valid token', async () => {
    const client = new AIServiceClient({ baseUrl: 'http://localhost:8000' });
    client.setAccessToken(validToken);
    const response = await client.generateCode(testRequest);
    expect(response).toBeDefined();
  });
});
```

### 集成测试
```python
# backend/tests/test_ai_auth.py
def test_generate_code_with_valid_token(client, valid_token):
    response = client.post(
        "/api/v1/generate-code",
        json={"prompt": "test prompt"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200

def test_generate_code_without_token(client):
    response = client.post("/api/v1/generate-code", json={"prompt": "test prompt"})
    assert response.status_code == 401
```

## 部署步骤

1. 更新后端数据库模型
2. 部署新的认证中间件
3. 更新前端SDK认证逻辑
4. 集成前端组件认证状态
5. 配置权限控制规则
6. 运行集成测试
7. 监控系统性能和安全性

## 后续优化

- 实施更细粒度的权限控制
- 添加用户行为分析
- 优化配额管理系统
- 增强安全审计功能