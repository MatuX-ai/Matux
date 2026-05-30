# iMato AI Service

基于FastAPI的AI代码生成服务，支持多种AI模型提供商。

## 功能特性

- ✅ 支持多种AI模型提供商（OpenAI、Lingma、DeepSeek、Anthropic、Google）
- ✅ 完整的认证和授权系统
- ✅ 请求记录和使用统计
- ✅ RESTful API设计
- ✅ 异步处理提高性能
- ✅ 详细的日志记录
- ✅ 数据库存储历史记录

## 技术栈

- **框架**: FastAPI + Uvicorn
- **数据库**: SQLAlchemy (支持SQLite、PostgreSQL等)
- **AI库**: LangChain
- **认证**: JWT + OAuth2
- **日志**: Python logging
- **测试**: pytest

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写相关配置：

```bash
cp .env.example .env
```

### 3. 启动服务

```bash
# 开发模式
python run.py

# 或者使用uvicorn直接启动
uvicorn main:app --reload
```

服务将在 `http://localhost:8000` 启动。

## API文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 支持的AI模型

### OpenAI
- `gpt-4-turbo` (推荐)
- `gpt-4`
- `gpt-3.5-turbo`

### Lingma
- `lingma-code-pro`

### DeepSeek
- `deepseek-coder`

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`

### Google
- `gemini-pro`

## API端点

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/token` - 获取访问令牌
- `GET /api/v1/auth/me` - 获取当前用户信息

### AI服务
- `POST /api/v1/generate-code` - 生成代码
- `GET /api/v1/models` - 获取可用模型列表
- `GET /api/v1/usage-stats` - 获取使用统计
- `GET /api/v1/recent-requests` - 获取最近请求记录

## 使用示例

### 生成代码

```bash
curl -X POST "http://localhost:8000/api/v1/generate-code" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个Python函数来计算斐波那契数列",
    "provider": "openai",
    "language": "python",
    "temperature": 0.7
  }'
```

## 项目结构

```
backend/
├── ai_service/          # AI服务核心模块
│   ├── __init__.py
│   ├── ai_manager.py    # AI模型管理器
│   └── models.py        # 数据模型
├── config/              # 配置模块
│   └── settings.py      # 应用配置
├── models/              # 数据库模型
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   └── ai_request.py    # AI请求记录模型
├── routes/              # API路由
│   ├── __init__.py
│   ├── ai_routes.py     # AI相关路由
│   └── auth_routes.py   # 认证相关路由
├── utils/               # 工具模块
│   ├── database.py      # 数据库工具
│   └── logger.py        # 日志工具
├── tests/               # 测试文件
├── main.py             # 应用入口
├── run.py              # 启动脚本
├── requirements.txt    # 依赖列表
└── README.md           # 本文档
```

## 开发指南

### 添加新的AI提供商

1. 在 `config/settings.py` 中添加相关配置
2. 在 `ai_service/ai_manager.py` 中添加对应的客户端设置方法
3. 实现具体的调用方法
4. 在 `routes/ai_routes.py` 的模型列表中添加相关信息

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 初始化迁移
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### 生产环境部署建议

1. 使用Gunicorn作为WSGI服务器
2. 配置反向代理（Nginx）
3. 使用PostgreSQL作为生产数据库
4. 配置SSL证书
5. 设置适当的环境变量

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

GPL-3.0