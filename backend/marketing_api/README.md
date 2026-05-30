# MatuX Marketing API

MatuX 营销页面后端 API - 基于 FastAPI

## 功能特性

- ✅ 联系表单提交和管理
- ✅ 邮件订阅管理
- ✅ 数据统计和分析
- ✅ Admin 后台数据接口
- ✅ CORS 支持
- ✅ 自动 API 文档

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将运行在：`http://localhost:8000`

API 文档：`http://localhost:8000/docs`

## API 端点

### 联系表单

#### POST `/api/marketing/contact`
提交联系表单

**请求体：**
```json
{
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "type": "business",
  "message": "我想了解更多关于商务合作的信息...",
  "source": "marketing_contact_page",
  "location": "北京市"
}
```

**响应：**
```json
{
  "success": true,
  "message": "提交成功！我们会尽快与您联系。",
  "data": {
    "id": "contact_1678901234.567"
  }
}
```

#### GET `/api/marketing/contacts`
获取联系表单列表

**查询参数：**
- `status`: 过滤状态（pending, processing, resolved）
- `type`: 过滤类型（business, school, personal, technical, investment, other）

#### PUT `/api/marketing/contacts/{contact_id}`
更新联系表单状态

**请求体：**
```json
{
  "status": "processing"
}
```

### 订阅

#### POST `/api/marketing/subscribe`
订阅邮件列表

**请求体：**
```json
{
  "email": "user@example.com",
  "name": "张三",
  "interests": ["AI教育", "机器人编程"],
  "source": "newsletter_signup",
  "consentGiven": true
}
```

#### POST `/api/marketing/unsubscribe`
取消订阅

**请求体：**
```json
{
  "email": "user@example.com",
  "unsubscribeToken": "token_123456"
}
```

#### GET `/api/marketing/subscribers`
获取订阅用户列表

**查询参数：**
- `status`: 过滤状态（active, inactive）

### 分析

#### POST `/api/marketing/analytics/track`
记录分析事件

**请求体：**
```json
{
  "event": "page_view",
  "timestamp": "2026-03-16T10:00:00.000Z",
  "sessionId": "session_123",
  "userId": "user_456",
  "page": {
    "url": "/marketing",
    "title": "营销首页 - MatuX"
  },
  "data": {}
}
```

### Admin 营销数据

#### GET `/api/admin/marketing/metrics`
获取营销数据指标

**查询参数：**
- `days`: 天数（默认 7）

**响应：**
```json
{
  "pageViews": 1234,
  "pageViewsTrend": 8,
  "contactForms": 23,
  "contactFormsTrend": 15,
  "newSubscribers": 45,
  "newSubscribersTrend": 12,
  "avgTimeOnPage": 45,
  "avgTimeOnPageTrend": 5
}
```

#### GET `/api/admin/marketing/page-stats`
获取页面访问统计

**响应：**
```json
[
  {
    "name": "营销首页",
    "views": 456,
    "uniqueVisitors": 312,
    "bounceRate": 35.5,
    "avgDuration": 58
  }
]
```

## 数据存储

数据以 JSON 格式存储在 `data/` 目录：

- `contacts.json` - 联系表单数据
- `subscribers.json` - 订阅用户数据
- `analytics.json` - 分析事件数据

**注意**: 生产环境应使用数据库（PostgreSQL/MySQL）替代 JSON 文件存储。

## 邮件功能

当前版本中邮件发送功能为占位实现。实际项目中需要：

1. 配置 SMTP 服务器
2. 实现邮件模板
3. 添加验证 token 生成
4. 实现邮件队列

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t matux-marketing-api .

# 运行容器
docker run -p 8000:8000 matux-marketing-api
```

### 环境变量

创建 `.env` 文件：

```env
# SMTP 配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 数据库配置（如使用数据库）
DATABASE_URL=postgresql://user:password@localhost/matux
```

## 开发

### 代码结构

```
marketing_api/
├── main.py              # 主应用文件
├── requirements.txt     # 依赖列表
├── README.md          # 本文件
└── data/             # 数据存储目录
    ├── contacts.json
    ├── subscribers.json
    └── analytics.json
```

### 扩展功能

1. **数据库集成**
   - 使用 SQLAlchemy + PostgreSQL
   - 替换 JSON 文件存储

2. **邮件服务**
   - 集成 SendGrid/Mailgun
   - 实现邮件模板引擎

3. **认证**
   - JWT Token 认证
   - Admin 用户管理

4. **缓存**
   - Redis 缓存热点数据
   - 提升响应速度

## 许可证

GPL-3.0 License

## 支持

如有问题，请联系：support@matux.ai
