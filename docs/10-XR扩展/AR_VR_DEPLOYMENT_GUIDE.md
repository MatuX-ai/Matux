# AR/VR课程集成部署指南

## 系统架构概述

AR/VR课程集成系统采用微服务架构，主要包括以下组件：

### 后端服务
- **FastAPI应用服务器**: 提供RESTful API和WebSocket接口
- **数据库服务**: PostgreSQL/MySQL存储业务数据
- **Redis缓存**: 会话管理和实时数据缓存
- **文件存储**: 本地存储或AWS S3存储Unity构建文件

### 前端应用
- **Angular单页应用**: 提供用户界面和交互体验
- **Unity WebGL**: 嵌入式的3D内容和AR体验
- **WebRTC客户端**: 实时传感器数据传输

### 基础设施
- **Nginx反向代理**: 负载均衡和SSL终止
- **Docker容器**: 应用容器化部署
- **监控系统**: Prometheus + Grafana

## 部署前提条件

### 硬件要求
```
最低配置：
- CPU: 4核
- 内存: 8GB RAM
- 存储: 50GB SSD
- 网络: 100Mbps带宽

推荐配置：
- CPU: 8核
- 内存: 16GB RAM
- 存储: 100GB SSD
- 网络: 1Gbps带宽
```

### 软件依赖
```
操作系统：Ubuntu 20.04 LTS / CentOS 8
Python: 3.8+
Node.js: 16+
Docker: 20.10+
Docker Compose: 1.29+
Nginx: 1.18+
PostgreSQL: 13+ 或 MySQL: 8.0+
Redis: 6.0+
```

## 部署步骤

### 1. 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget unzip

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 获取代码

```bash
# 克隆项目仓库
git clone https://github.com/your-org/imato-project.git
cd imato-project

# 切换到AR/VR分支
git checkout ar-vr-integration
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_NAME=imato_arvr
DB_USER=imato_user
DB_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# JWT密钥
JWT_SECRET_KEY=your_very_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 文件存储
STORAGE_TYPE=local  # 或 s3
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE=104857600  # 100MB

# WebRTC配置
WEBSOCKET_SENSOR_PORT=8765
WEBSOCKET_CLIENT_PORT=8766

# Unity WebGL配置
UNITY_BUILD_PATH=/app/arvr_contents/builds
UNITY_THUMBNAIL_PATH=/app/arvr_contents/thumbnails

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 4. 构建Docker镜像

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/arvr_contents/builds /app/arvr_contents/thumbnails /app/uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5. Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # 数据库服务
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - imato-network

  # Redis缓存
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    networks:
      - imato-network

  # 后端应用
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      - postgres
      - redis
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env
    ports:
      - "8000:8000"
      - "8765:8765"
      - "8766:8766"
    volumes:
      - ./backend:/app
      - arvr_contents:/app/arvr_contents
      - uploads:/app/uploads
    networks:
      - imato-network

  # 前端应用
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "4200:4200"
    depends_on:
      - backend
    networks:
      - imato-network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - arvr_contents:/usr/share/nginx/html/arvr_contents:ro
      - uploads:/usr/share/nginx/html/uploads:ro
    depends_on:
      - backend
      - frontend
    networks:
      - imato-network

volumes:
  postgres_data:
  arvr_contents:
  uploads:

networks:
  imato-network:
    driver: bridge
```

### 6. Nginx配置

```nginx
# nginx/conf.d/imato.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:4200;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # AR/VR内容静态文件
    location /arvr/ {
        alias /usr/share/nginx/html/arvr_contents/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件
    location /uploads/ {
        alias /usr/share/nginx/html/uploads/;
        expires 1d;
    }
    
    # API路由
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # WebSocket传感器数据流
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # 前端应用
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 8. 数据库初始化

```bash
# 运行数据库迁移
docker-compose exec backend python -m alembic upgrade head

# 创建初始数据
docker-compose exec backend python backend/migrations/006_create_ar_vr_tables.py
```

### 9. 健康检查

```bash
# 检查各服务状态
curl -f http://localhost:8000/health
curl -f http://localhost:4200/
curl -f http://localhost:5432/

# 检查AR/VR API
curl -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/v1/org/1/arvr/contents
```

## 生产环境配置

### SSL证书配置

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 监控和日志

```yaml
# 添加监控服务到docker-compose.yml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - imato-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - imato-network

volumes:
  grafana_data:
```

### 备份策略

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/imato"

# 数据库备份
docker-compose exec postgres pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 文件备份
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /app/arvr_contents /app/uploads

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 性能调优

```bash
# 系统级别优化
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
sysctl -p

# Docker资源限制
# 在docker-compose.yml中添加:
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查容器日志
   docker-compose logs backend
   
   # 检查端口占用
   netstat -tlnp | grep :8000
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务
   docker-compose exec postgres pg_isready
   
   # 检查连接参数
   docker-compose exec backend python -c "import psycopg2; print('DB OK')"
   ```

3. **WebSocket连接问题**
   ```bash
   # 检查防火墙设置
   sudo ufw status
   
   # 测试WebSocket连接
   wscat -c ws://localhost:8765
   ```

### 监控告警

```yaml
# alertmanager.yml
route:
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
```

## 升级维护

### 版本升级流程

```bash
# 1. 备份当前版本
./backup.sh

# 2. 拉取最新代码
git pull origin ar-vr-integration

# 3. 更新依赖
docker-compose build --no-cache

# 4. 运行迁移
docker-compose exec backend python -m alembic upgrade head

# 5. 重启服务
docker-compose down
docker-compose up -d

# 6. 验证功能
./health_check.sh
```

### 滚动更新

```bash
# 使用Docker Swarm或Kubernetes实现零停机更新
docker stack deploy -c docker-compose.prod.yml imato-arvr
```

## 安全加固

### 网络安全
```bash
# 配置防火墙
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 限制Docker端口暴露
# 只在docker-compose.yml中暴露必要端口
```

### 应用安全
```bash
# 定期更新依赖
docker-compose exec backend pip list --outdated

# 安全扫描
docker scan backend_imato
```

## 性能基准测试

```bash
# 使用Apache Bench进行压力测试
ab -n 10000 -c 100 -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/v1/org/1/arvr/contents/

# WebSocket性能测试
npm install -g wscat
wscat -c ws://localhost:8765 --exec "for(i=0;i<1000;i++){send(JSON.stringify({test:i}))}"
```

---

**部署团队**: DevOps Team  
**最后更新**: 2024年1月15日  
**版本**: v1.0