# 多媒体课件支持系统部署指南

## 系统要求

### 硬件要求
- CPU: 2核以上
- 内存: 4GB以上
- 存储: 50GB以上可用空间
- 网络: 稳定的互联网连接

### 软件要求
- Python 3.8+
- Node.js 14+ (前端)
- Redis 6.0+ (任务队列)
- Docker (可选，用于容器化部署)

## 部署步骤

### 1. 环境准备

```bash
# 克隆项目代码
git clone <repository-url>
cd imato

# 创建后端虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据库配置

```bash
# 执行多媒体相关数据库迁移
python migrations/005_create_multimedia_tables.py upgrade --sync
```

### 3. 环境变量配置

创建 `.env` 文件：

```env
# 存储配置
STORAGE_TYPE=local  # 或 s3
LOCAL_STORAGE_PATH=./uploads

# AWS S3配置 (如使用云存储)
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# CDN配置
CDN_DOMAIN=your-cdn-domain.com

# Redis配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS MediaConvert配置
MEDIA_CONVERT_ROLE=arn:aws:iam::account:role/MediaConvertRole
MEDIA_CONVERT_ENDPOINT=https://your-endpoint.mediaconvert.region.amazonaws.com
MEDIA_CONVERT_QUEUE=Default
```

### 4. 启动服务

#### 方法一：手动启动
```bash
# 启动Redis
redis-server

# 启动Celery Worker
celery -A celery_app worker --loglevel=info

# 启动Celery Beat (定时任务)
celery -A celery_app beat --loglevel=info

# 启动主应用
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 方法二：使用部署脚本
```bash
# Linux/Mac
chmod +x scripts/deploy_multimedia.sh
./scripts/deploy_multimedia.sh

# Windows
# 使用 PowerShell 脚本 (需要单独创建)
```

### 5. 前端构建

```bash
# 安装前端依赖
npm install

# 构建生产版本
npm run build

# 启动开发服务器
npm start
```

## 云服务配置

### AWS S3存储配置

1. 创建S3存储桶
2. 配置存储桶策略允许上传和访问
3. 创建IAM用户并分配相应权限
4. 在环境变量中配置访问密钥

### AWS MediaConvert配置

1. 在AWS控制台启用MediaConvert服务
2. 创建IAM角色用于MediaConvert访问S3
3. 获取服务终端节点
4. 配置转码模板和队列

### CDN配置示例

```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your-cdn-domain.com;
    
    location /uploads/ {
        alias /path/to/imato/uploads/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location /processed/ {
        alias /path/to/imato/uploads/processed/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

## 容器化部署

### Docker Compose配置

```yaml
version: '3.8'

services:
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./backend/uploads:/app/uploads

  celery-worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - backend

  celery-beat:
    build: ./backend
    command: celery -A celery_app beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - backend

volumes:
  redis_data:
```

### Kubernetes部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: imato-multimedia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: imato-multimedia
  template:
    metadata:
      labels:
        app: imato-multimedia
    spec:
      containers:
      - name: backend
        image: your-registry/imato-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: imato-config
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: imato-multimedia-service
spec:
  selector:
    app: imato-multimedia
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 性能调优

### Redis优化
```redis
# redis.conf 优化配置
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 300
```

### 数据库优化
```sql
-- 创建必要索引
CREATE INDEX idx_multimedia_org_course ON multimedia_resources(org_id, course_id);
CREATE INDEX idx_multimedia_media_type ON multimedia_resources(media_type);
CREATE INDEX idx_transcoding_status ON media_transcoding_jobs(status);
```

### 应用层优化
```python
# celery配置优化
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
task_acks_late = True
```

## 监控配置

### 健康检查端点
```
GET /health                    # 应用健康检查
GET /api/v1/multimedia/stats   # 多媒体系统统计
```

### 日志配置
```python
# logging.conf
[loggers]
keys=root,multimedia

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_multimedia]
level=INFO
handlers=fileHandler
qualname=multimedia
propagate=0
```

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查存储权限配置
   - 验证文件大小限制
   - 确认网络连接稳定

2. **视频转码失败**
   - 检查AWS MediaConvert配置
   - 验证IAM角色权限
   - 查看转码任务日志

3. **3D模型无法预览**
   - 确认文件格式支持
   - 检查Three.js库加载
   - 验证浏览器兼容性

4. **文档处理异常**
   - 检查相关Python库安装
   - 验证文件格式正确性
   - 查看处理日志

### 日志查看
```bash
# 查看应用日志
tail -f logs/multimedia.log

# 查看Celery日志
tail -f logs/celery.log

# 查看Redis日志
redis-cli monitor
```

## 安全加固

### 访问控制
- 配置HTTPS证书
- 实施严格的文件类型验证
- 设置合理的文件大小限制
- 启用CSRF保护

### 数据保护
- 敏感信息加密存储
- 定期备份重要数据
- 实施访问审计日志
- 配置防火墙规则

## 维护计划

### 日常维护
- 监控系统资源使用
- 检查任务队列状态
- 清理临时文件
- 更新安全补丁

### 定期维护
- 数据库性能优化
- 系统容量规划
- 备份恢复测试
- 安全漏洞扫描

---

*部署指南最后更新: 2024年*