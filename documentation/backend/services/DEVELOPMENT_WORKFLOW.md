# iMatuProject 开发工作流程

## 概述

本文档描述了 iMatuProject 项目的标准化开发工作流程，包括环境设置、开发实践和质量保证流程。

## 环境准备

### 1. 系统要求

#### 前端开发环境
- **Node.js**: v18.x 或更高版本
- **npm**: v9.x 或更高版本
- **推荐IDE**: VS Code with recommended extensions

#### 后端开发环境
- **Python**: 3.8+ (推荐 3.11)
- **虚拟环境**: venv 或 conda
- **数据库**: PostgreSQL 13+ 或 MySQL 8+

### 2. 开发工具安装

#### Windows 环境
```batch
REM 安装 Node.js (从官网下载)
REM https://nodejs.org/

REM 安装 Python (从官网下载)
REM https://www.python.org/

REM 克隆项目
git clone <repository-url>
cd iMato

REM 安装前端依赖
npm install

REM 设置后端环境
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

#### Unix/Linux/macOS 环境
```bash
# 安装 Node.js 和 npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 或使用 Homebrew (macOS)
brew install node

# 安装 Python
sudo apt-get install python3 python3-pip python3-venv

# 克隆项目
git clone <repository-url>
cd iMato

# 安装前端依赖
npm install

# 设置后端环境
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## 日常开发流程

### 1. 启动开发服务器

#### 前端开发
```bash
# 启动 Angular 开发服务器
npm run start

# 启动带有代理的开发服务器（连接后端）
npm run start:proxy

# 构建生产版本
npm run build
```

#### 后端开发
```bash
# 激活虚拟环境
cd backend

# Windows
.venv\Scripts\activate.bat

# Unix/Linux/macOS
source .venv/bin/activate

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或使用配置文件启动
python run.py
```

### 2. 代码质量检查

#### 本地检查命令
```bash
# 运行所有质量检查
npm run quality:check

# 仅检查前端代码
npm run lint:ts-check
npm run lint:scss-check
npm run format:check

# 仅检查后端代码
cd backend
black --check .
isort --check-only .
flake8 .

# 自动修复可修复的问题
npm run quality:fix
```

#### 跨平台脚本
```bash
# Windows
scripts\lint-all.bat
scripts\format-all.bat

# Unix/Linux/macOS
./scripts/lint-all.sh
./scripts/format-all.sh
```

### 3. Git 工作流程

#### 分支策略
```
main          # 生产环境分支
develop       # 开发主分支
feature/*     # 功能开发分支
hotfix/*      # 紧急修复分支
release/*     # 发布准备分支
```

#### 标准开发流程
```bash
# 1. 从 develop 分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication

# 2. 开发过程中定期提交
git add .
git commit -m "feat(auth): 实现用户登录功能"

# 3. 推送到远程仓库
git push origin feature/user-authentication

# 4. 创建 Pull Request
# 在 GitHub/GitLab 上创建 PR，指向 develop 分支

# 5. 代码审查通过后合并
git checkout develop
git pull origin develop
git merge feature/user-authentication
git push origin develop
```

## 代码审查流程

### 1. Pull Request 检查清单

#### 代码质量
- [ ] 通过所有 CI 质量检查
- [ ] 无 ESLint/Flake8 警告和错误
- [ ] 代码格式符合规范
- [ ] 测试覆盖率达标

#### 功能实现
- [ ] 功能按需求实现
- [ ] 有适当的单元测试
- [ ] API 文档更新（如需要）
- [ ] 错误处理完善

#### 代码可维护性
- [ ] 代码结构清晰
- [ ] 有必要的注释和文档
- [ ] 遵循项目命名规范
- [ ] 无重复代码

### 2. 审查标准

#### 前端审查重点
- 组件职责单一
- 状态管理合理
- 性能优化考虑
- 用户体验友好

#### 后端审查重点
- 数据库设计合理
- API 设计 RESTful
- 安全性考虑充分
- 错误处理完善

## 测试策略

### 1. 测试分类

#### 单元测试
```bash
# 前端单元测试
npm run test

# 后端单元测试
cd backend
pytest tests/unit/

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

#### 集成测试
```bash
# 前端集成测试
npm run test:integration

# 后端集成测试
cd backend
pytest tests/integration/
```

#### 端到端测试
```bash
# 使用 Cypress 进行 E2E 测试
npm run e2e
npm run e2e:open  # 打开 Cypress GUI
```

### 2. 测试编写规范

#### 前端测试示例
```typescript
describe('UserService', () => {
  let service: UserService;
  let httpClient: HttpClient;
  
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
    httpClient = TestBed.inject(HttpTestingController);
  });
  
  it('should be created', () => {
    expect(service).toBeTruthy();
  });
  
  it('should fetch user data', () => {
    const mockUser = { id: 1, name: 'John Doe' };
    
    service.getUser(1).subscribe(user => {
      expect(user).toEqual(mockUser);
    });
    
    const req = httpClient.expectOne('/api/users/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });
});
```

#### 后端测试示例
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    Base.metadata.drop_all(bind=engine)

def test_create_user(client):
    response = client.post("/api/users/", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

## 部署流程

### 1. 前端部署

#### 构建优化
```bash
# 生产构建
npm run build

# 分析打包结果
npm run build:analyze

# 预览生产构建
npm run preview
```

#### 部署配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 后端部署

#### Docker 部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 启动命令
```bash
# 构建镜像
docker build -t imatuproject-backend .

# 运行容器
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/imatu \
  imatuproject-backend

# 使用 docker-compose
docker-compose up -d
```

## 监控和维护

### 1. 性能监控

#### 前端性能指标
- 页面加载时间 < 3秒
- 首屏渲染时间 < 1秒
- Bundle 大小 < 2MB

#### 后端性能指标
- API 响应时间 < 200ms
- 数据库查询时间 < 100ms
- 内存使用率 < 80%

### 2. 日志管理

#### 前端日志
```typescript
// 推荐的日志级别
console.debug('调试信息');
console.info('一般信息');
console.warn('警告信息');
console.error('错误信息');

// 结构化日志
logger.info('User login', {
  userId: user.id,
  timestamp: new Date().toISOString(),
  userAgent: navigator.userAgent
});
```

#### 后端日志
```python
import logging

logger = logging.getLogger(__name__)

def process_user_data(user_id: int):
    logger.info(f"Processing user data for user {user_id}")
    
    try:
        # 业务逻辑
        result = some_operation()
        logger.debug(f"Operation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to process user {user_id}: {str(e)}")
        raise
```

## 故障排除

### 1. 常见问题

#### 前端问题
```bash
# 清理缓存并重新安装
rm -rf node_modules package-lock.json
npm install

# 清理 Angular 缓存
npm run clean
npx ng cache clean

# 重置 Git 钩子
npx husky install
```

#### 后端问题
```bash
# 重建虚拟环境
cd backend
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # Unix/Linux/macOS
# 或 .venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

### 2. 调试技巧

#### 前端调试
- 使用 Chrome DevTools
- 启用 Angular DevTools
- 查看网络请求和响应
- 检查组件状态和 props

#### 后端调试
- 使用 pdb 断点调试
- 查看 uvicorn 日志输出
- 数据库查询日志
- 性能分析工具

## 最佳实践

### 1. 代码组织
- 按功能模块组织代码
- 保持组件和函数职责单一
- 合理使用设计模式
- 文档驱动开发

### 2. 性能优化
- 懒加载非关键资源
- 图片压缩和格式优化
- 数据库查询优化
- 缓存策略实施

### 3. 安全考虑
- 输入验证和 sanitization
- CSRF 和 XSS 防护
- 权限控制实施
- 安全头设置

---

*最后更新: 2026年3月*
*版本: 1.0.0*