# iMatuProject 代码风格指南

## 概述

本文档定义了 iMatuProject 项目的代码风格规范和质量标准，适用于所有前端和后端开发人员。

## 前端代码规范 (Angular/TypeScript)

### 1. TypeScript 规范

#### 命名约定
- **文件名**: 使用 kebab-case (如: `user-profile.component.ts`)
- **类名**: 使用 PascalCase (如: `UserProfileComponent`)
- **变量/函数名**: 使用 camelCase (如: `userName`, `getUserData()`)
- **常量**: 使用 UPPER_SNAKE_CASE (如: `MAX_RETRY_COUNT`)
- **接口**: 使用 PascalCase 并以 `I` 开头 (如: `IUserResponse`)

#### 类型安全
```typescript
// ✅ 推荐：明确的类型定义
interface User {
  id: number;
  name: string;
  email: string;
  isActive: boolean;
}

// ❌ 避免：使用 any
function processData(data: any): any {
  // ...
}
```

#### 函数和方法
```typescript
// ✅ 推荐：明确的返回类型
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ✅ 推荐：使用可选参数和默认值
function createUser(name: string, email?: string, role: UserRole = 'user'): User {
  return { name, email, role };
}
```

### 2. Angular 特定规范

#### 组件结构
```typescript
@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.scss']
})
export class UserProfileComponent implements OnInit, OnDestroy {
  // 输入属性
  @Input() userId!: number;
  
  // 输出属性
  @Output() userChange = new EventEmitter<User>();
  
  // 公共属性
  user!: User;
  
  // 私有属性
  private subscription!: Subscription;
  
  constructor(
    private userService: UserService,
    private router: Router
  ) {}
  
  ngOnInit(): void {
    this.loadUser();
  }
  
  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }
  
  // 公共方法
  updateUser(): void {
    // 实现更新逻辑
  }
  
  // 私有方法
  private loadUser(): void {
    this.subscription = this.userService.getUser(this.userId)
      .subscribe(user => this.user = user);
  }
}
```

#### 服务规范
```typescript
@Injectable({
  providedIn: 'root'
})
export class UserService {
  private baseUrl = '/api/users';
  
  constructor(private http: HttpClient) {}
  
  getUser(id: number): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`);
  }
  
  createUser(user: Partial<User>): Observable<User> {
    return this.http.post<User>(this.baseUrl, user);
  }
}
```

### 3. SCSS/CSS 规范

#### BEM 命名法
```scss
// ✅ 推荐：使用 BEM 命名
.user-profile {
  &__avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
  }
  
  &__name {
    font-weight: bold;
    color: #333;
  }
  
  &--active {
    background-color: #e8f5e8;
  }
}
```

#### 设计令牌使用
```scss
// ✅ 推荐：使用设计令牌变量
.card {
  padding: $spacing-md;
  border-radius: $border-radius-card;
  background-color: $surface-color;
  box-shadow: $shadow-card;
  
  &__title {
    color: $text-primary-color;
    font-size: $font-size-heading-medium;
    margin-bottom: $spacing-sm;
  }
}
```

## 后端代码规范 (Python/FastAPI)

### 1. Python 基本规范

#### 命名约定
- **模块名**: 使用 snake_case (如: `user_service.py`)
- **类名**: 使用 PascalCase (如: `UserService`)
- **函数/方法名**: 使用 snake_case (如: `get_user_data()`)
- **变量名**: 使用 snake_case (如: `user_name`)
- **常量**: 使用 UPPER_SNAKE_CASE (如: `MAX_RETRY_COUNT`)

#### 代码结构
```python
# ✅ 推荐：标准的导入顺序
# 标准库导入
import json
from typing import List, Optional
from datetime import datetime

# 第三方库导入
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 本地导入
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter()

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 2. FastAPI 规范

#### 路由定义
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    user_service: UserService = Depends()
):
    """
    创建新用户
    
    Args:
        user_data: 用户创建数据
        db: 数据库会话
        user_service: 用户服务
        
    Returns:
        创建的用户信息
    """
    try:
        return user_service.create_user(user_data, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """根据ID获取用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
```

#### Pydantic 模型
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

### 3. SQLAlchemy 模型
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    posts = relationship("Post", back_populates="author")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
```

## 代码质量工具配置

### 1. 前端工具

#### ESLint 配置要点
- 严格模式启用
- TypeScript 类型检查
- 导入自动排序
- 未使用变量检测

#### Prettier 配置
```json
{
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true
}
```

#### Stylelint 配置
- BEM 命名规范检查
- CSS 属性顺序规范
- 设计令牌强制使用

### 2. 后端工具

#### Black 配置
- 行长度: 88字符
- 字符串引号: 双引号优先

#### isort 配置
```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app", "tests"]
```

#### Flake8 配置
- 最大复杂度: 10
- 最大行长度: 88
- 选择性规则启用

## Git 提交规范

### 提交消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 示例
```
feat(auth): 添加用户登录功能

实现了基于JWT的用户认证系统，包括：
- 用户注册和登录接口
- JWT token生成和验证
- 密码加密存储

Closes #123
```

## 开发工作流程

### 1. 本地开发
```bash
# 前端开发
npm run start

# 后端开发
cd backend
uvicorn main:app --reload

# 运行代码质量检查
npm run quality:check

# 自动修复格式问题
npm run quality:fix
```

### 2. 提交前检查
- 自动运行 pre-commit hooks
- 执行增量代码检查
- 确保格式统一

### 3. Pull Request 流程
- 通过所有 CI 质量检查
- 代码审查通过
- 测试覆盖率达标

## 质量门禁标准

### 前端标准
- ESLint 无警告和错误
- Prettier 格式检查通过
- Stylelint CSS 规范检查通过
- TypeScript 编译无错误

### 后端标准
- Black 格式化检查通过
- isort 导入排序正确
- Flake8 代码质量检查通过
- MyPy 类型检查通过
- 测试覆盖率 ≥ 80%

## 常见问题解答

### Q: 如何处理遗留代码不符合规范的情况？
A: 逐步重构，优先处理新代码，旧代码在修改时同步规范。

### Q: 工具报错如何处理？
A: 首先尝试自动修复，如无法自动修复则手动调整代码。

### Q: 团队成员 IDE 配置不同怎么办？
A: 提供统一的 IDE 配置文件和设置指南。

---

*最后更新: 2026年3月*
*版本: 1.0.0*