# 开发指南

## 环境搭建

### 前置条件
- Node.js >= 16.0
- Python >= 3.9
- Docker (可选)
- Redis (可选)

### 本地开发环境
```bash
# 克隆项目
git clone <repository-url>
cd iMato

# 安装前端依赖
npm install

# 安装后端依赖
cd backend
pip install -r requirements.txt
```

## 前端开发

### 技术栈
- **框架**: Angular 16
- **UI组件库**: Angular Material + MUI
- **状态管理**: RxJS
- **样式系统**: SCSS + Design Tokens

### 开发命令
```bash
# 启动开发服务器
npm start

# 构建生产版本
npm run build

# 代码检查
npm run lint:css
npm run lint:ts
```

### 设计系统
- [组件样式指南](../02-开发指南/component-style-guide.md)
- [Design Tokens使用](../02-开发指南/design-tokens.md)

## 后端开发

### 技术栈
- **框架**: FastAPI (Python)
- **数据库**: SQLAlchemy ORM
- **缓存**: Redis
- **认证**: JWT + OAuth2

### 开发命令
```bash
# 启动后端服务
cd backend
python main.py

# 或使用uvicorn
uvicorn main:app --reload
```

## 移动端开发

### Flutter开发
- ARCore/ARKit集成
- WebRTC实时通信
- 跨平台兼容性

## 开发规范

### 代码规范
- 遵循ESLint和Prettier配置
- 使用TypeScript严格模式
- 统一的命名约定

### Git工作流
- Feature branch开发模式
- Pull Request代码审查
- 自动化测试集成

---
*iMatu开发指南 | 版本 v1.0*