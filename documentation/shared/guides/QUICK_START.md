# iMatuProject 快速入门指南

## 🚀 5分钟快速开始

### 1. 环境检查
```bash
# 检查 Node.js 版本
node --version  # 需要 v18+

# 检查 Python 版本
python --version  # 需要 3.8+
```

### 2. 项目初始化
```bash
# 克隆项目
git clone <your-repo-url>
cd iMato

# 安装前端依赖
npm install

# 设置后端环境
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

### 3. 启动开发环境
```bash
# 终端1: 启动后端
cd backend
uvicorn main:app --reload

# 终端2: 启动前端
npm run start
```

访问 http://localhost:4200 查看应用！

## 🔧 日常开发命令

### 代码质量检查
```bash
# 检查代码质量
npm run quality:check

# 自动修复格式问题
npm run quality:fix

# 跨平台检查脚本
./scripts/lint-all.sh  # Linux/macOS
scripts\lint-all.bat   # Windows
```

### Git 工作流程
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交代码（自动运行质量检查）
git add .
git commit -m "feat: 添加新功能"

# 推送代码
git push origin feature/new-feature
```

## 📋 开发规范速查

### 命名规范
```typescript
// ✅ 正确
const userProfile = {};           // 变量: camelCase
function getUserData() {}         // 函数: camelCase
class UserProfileComponent {}     // 类: PascalCase
interface IUserProfile {}         // 接口: I + PascalCase
const MAX_RETRY_COUNT = 5;        // 常量: UPPER_SNAKE_CASE
```

### 组件结构
```typescript
@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html'
})
export class UserProfileComponent implements OnInit {
  @Input() userId!: number;        // 输入属性
  @Output() userChange = new EventEmitter<User>(); // 输出属性
  
  user!: User;                     // 公共属性
  private isLoading = false;       // 私有属性
  
  constructor(private userService: UserService) {} // 依赖注入
  
  ngOnInit(): void {
    this.loadUser();               // 生命周期方法
  }
  
  updateUser(): void {             // 公共方法
    // 实现逻辑
  }
  
  private loadUser(): void {       // 私有方法
    // 实现逻辑
  }
}
```

### Python 后端规范
```python
# ✅ 正确的导入顺序
# 标准库
import json
from typing import List
from datetime import datetime

# 第三方库
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 本地导入
from app.database import get_db
from app.models.user import User

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 🛠️ IDE 配置推荐

### VS Code 扩展
```json
{
  "recommendations": [
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-eslint",
    "esbenp.prettier-vscode",
    "stylelint.vscode-stylelint",
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-vscode.vscode-node-azure-pack"
  ]
}
```

### VS Code 设置
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[scss]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

## 🎯 常用开发场景

### 1. 添加新页面
```bash
# 使用 Angular CLI 生成组件
ng generate component pages/user-management

# 或简写
ng g c pages/user-management
```

### 2. 创建 API 接口
```python
# backend/routes/user_routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: int):
    # 实现获取用户逻辑
    pass

@router.post("/")
async def create_user(user_data: dict):
    # 实现创建用户逻辑
    pass
```

### 3. 添加数据库模型
```python
# backend/models/user.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
```

### 4. 编写单元测试
```typescript
// 前端测试
describe('UserService', () => {
  let service: UserService;
  
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
  });
  
  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
```

```python
# 后端测试
def test_create_user(client):
    response = client.post("/api/users/", json={
        "email": "test@example.com",
        "name": "Test User"
    })
    assert response.status_code == 201
```

## 🔍 调试技巧

### 前端调试
```typescript
// 使用 console.table 查看对象
console.table(userList);

// 条件断点调试
debugger;

// 性能分析
console.time('operation');
// 执行操作
console.timeEnd('operation');
```

### 后端调试
```python
# 使用 pdb 调试
import pdb; pdb.set_trace()

# 或使用 breakpoint()
breakpoint()

# 日志调试
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Processing user: {user_id}")
```

## 🚨 常见问题解决

### 1. 依赖安装问题
```bash
# 清理并重新安装
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# 后端依赖问题
cd backend
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### 2. Git Hooks 不工作
```bash
# 重新安装 husky
npx husky install

# 手动运行检查
npx lint-staged
```

### 3. 端口占用问题
```bash
# 查找占用端口的进程
netstat -ano | findstr :4200  # Windows
lsof -i :4200                 # Linux/macOS

# 杀死进程
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Linux/macOS
```

## 📚 学习资源

### 官方文档
- [Angular 官方文档](https://angular.io/docs)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [TypeScript 手册](https://www.typescriptlang.org/docs/)
- [Python 官方文档](https://docs.python.org/)

### 项目文档
- [代码风格指南](./CODING_STYLE_GUIDE.md)
- [开发工作流程](./DEVELOPMENT_WORKFLOW.md)
- [API 文档](http://localhost:8000/docs) (本地运行后端后访问)

## 💡 小贴士

1. **定期更新依赖**: `npm outdated` 和 `pip list --outdated`
2. **使用别名**: 在 `.bashrc` 或 `.zshrc` 中设置常用命令别名
3. **代码片段**: 配置 IDE 代码片段提高效率
4. **键盘快捷键**: 熟练掌握 IDE 快捷键
5. **版本控制**: 频繁提交，小步快跑

## 🆘 获取帮助

- 查看 [Issues](https://github.com/your-org/iMato/issues)
- 联系团队负责人
- 参考项目 Wiki
- 查看提交历史和注释

---

*祝你开发愉快！🎉*

*遇到问题随时提问，我们一起让代码更美好！*