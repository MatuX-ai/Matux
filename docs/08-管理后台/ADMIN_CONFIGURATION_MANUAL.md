# 教育数据联邦学习系统管理员配置手册

## 版本信息
- **文档版本**: 1.0
- **适用对象**: 系统管理员、运维工程师
- **更新日期**: 2026年2月28日

## 目录
1. [系统架构概述](#系统架构概述)
2. [环境配置要求](#环境配置要求)
3. [安装部署指南](#安装部署指南)
4. [系统配置详解](#系统配置详解)
5. [用户和权限管理](#用户和权限管理)
6. [监控和维护](#监控和维护)
7. [故障排除](#故障排除)
8. [安全加固](#安全加固)
9. [备份和恢复](#备份和恢复)
10. [性能调优](#性能调优)

## 系统架构概述

### 系统组成
```
教育数据联邦学习系统架构图:

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户接入层     │    │   业务逻辑层     │    │   数据存储层     │
│                 │    │                 │    │                 │
│  Web UI/API     │◄──►│  联邦学习引擎    │◄──►│   PostgreSQL    │
│  身份认证       │    │  隐私保护模块    │    │   Redis缓存     │
│  权限控制       │    │  数据处理服务    │    │   文件存储      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   监控告警层     │    │   安全防护层     │    │   基础设施层     │
│                 │    │                 │    │                 │
│  Prometheus     │    │  防火墙/WAF     │    │   Docker/K8s    │
│  Grafana        │    │  SSL/TLS        │    │   负载均衡      │
│  日志收集       │    │  访问控制       │    │   网络配置      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件说明
1. **API服务层**: FastAPI构建的RESTful服务
2. **联邦学习引擎**: 基于PySyft的分布式训练框架
3. **隐私保护模块**: 差分隐私和数据脱敏组件
4. **数据存储**: PostgreSQL主数据库 + Redis缓存
5. **监控系统**: Prometheus + Grafana监控套件

## 环境配置要求

### 硬件要求

#### 最小配置
```
CPU: 4核
内存: 8GB RAM
存储: 100GB SSD
网络: 100Mbps带宽
```

#### 推荐配置
```
CPU: 8核及以上
内存: 16GB RAM及以上
存储: 500GB SSD
网络: 1Gbps带宽
GPU: NVIDIA Tesla T4 (可选，用于加速训练)
```

### 软件环境

#### 操作系统
```
推荐: Ubuntu 20.04 LTS / CentOS 8+
最低: Ubuntu 18.04 / CentOS 7+
```

#### 必需软件
```bash
# Python环境
Python 3.8+
pip 21.0+

# 数据库
PostgreSQL 13+
Redis 6.0+

# Web服务器
Nginx 1.18+
Supervisor 4.0+

# 容器化(可选)
Docker 20.10+
Kubernetes 1.24+(集群部署)
```

### 网络配置
```
防火墙开放端口:
- 80: HTTP服务
- 443: HTTPS服务
- 8000: 应用服务(内部)
- 9090: 监控服务(内部)
- 5432: PostgreSQL(内部)
- 6379: Redis(内部)
```

## 安装部署指南

### 自动化部署

#### 使用部署脚本
```bash
# 下载部署脚本
wget https://github.com/imato-edu/deployment-scripts/deploy_production.sh

# 赋予执行权限
chmod +x deploy_production.sh

# 执行部署(需要root权限)
sudo ./deploy_production.sh

# 部署参数配置
./deploy_production.sh --env production --version 1.0.0
```

#### 部署脚本功能
- ✅ 系统环境检查和依赖安装
- ✅ 用户和组创建
- ✅ 应用程序部署
- ✅ 配置文件生成
- ✅ 系统服务配置
- ✅ Web服务器配置
- ✅ 监控系统配置
- ✅ 备份策略设置
- ✅ 健康检查验证

### 手动部署步骤

#### 步骤1: 系统准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib redis-server \
    nginx supervisor git

# 创建应用用户
sudo useradd -r -s /bin/false -d /opt/edu-federated edufl
```

#### 步骤2: 数据库配置
```bash
# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE edu_federated;
CREATE USER edufl WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE edu_federated TO edufl;
ALTER USER edufl CREATEDB;
EOF

# 配置PostgreSQL
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf
```

#### 步骤3: 应用部署
```bash
# 克隆代码
cd /opt
sudo git clone https://github.com/imato-edu/edu-federated-learning.git
sudo chown -R edufl:edufl edu-federated-learning

# 创建虚拟环境
cd edu-federated-learning
sudo -u edufl python3 -m venv venv
sudo -u edufl venv/bin/pip install -r requirements.txt

# 初始化数据库
sudo -u edufl venv/bin/python setup_database.py
```

#### 步骤4: 配置系统服务
```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/edu-federated.service << EOF
[Unit]
Description=Education Data Federated Learning Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=edufl
Group=edufl
WorkingDirectory=/opt/edu-federated-learning
EnvironmentFile=/etc/edu-federated/.env
ExecStart=/opt/edu-federated-learning/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable edu-federated
```

#### 步骤5: Web服务器配置
```bash
# 配置Nginx反向代理
sudo tee /etc/nginx/sites-available/edu-federated << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/edu-federated /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

## 系统配置详解

### 环境变量配置

#### 主配置文件 (/etc/edu-federated/.env)
```bash
# 基础应用配置
APP_NAME=Education Data Federated Learning
APP_VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://edufl:secure_password@localhost:5432/edu_federated
REDIS_URL=redis://localhost:6379/1

# 联邦学习配置
FL_PRIVACY_EPSILON=1.0
FL_NOISE_MULTIPLIER=1.1
FL_CLIPPING_THRESHOLD=1.0
FL_MAX_ROUNDS=50
FL_TIMEOUT_SECONDS=7200

# 教育数据配置
EDU_DATA_PRIVACY_LEVEL=high
EDU_SUBJECTS=math,science,technology,engineering
EDU_GRADE_LEVELS=elementary,middle,high

# 安全配置
SECRET_KEY=your-32-character-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-16-byte-encryption-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/edu-federated/application.log

# 监控配置
ENABLE_MONITORING=True
METRICS_PORT=9090
```

### 数据库配置优化

#### PostgreSQL配置 (/etc/postgresql/*/main/postgresql.conf)
```conf
# 内存配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接配置
max_connections = 100
superuser_reserved_connections = 3

# 性能优化
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100

# 日志配置
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'error'
log_min_duration_statement = 1000
```

### Redis配置优化

#### Redis配置 (/etc/redis/redis.conf)
```conf
# 内存管理
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000

# 安全配置
bind 127.0.0.1
protected-mode yes
requirepass your_redis_password

# 性能调优
tcp-keepalive 300
timeout 0
tcp-backlog 511
```

## 用户和权限管理

### 用户角色配置

#### 角色定义
```python
# 用户角色枚举
class UserRole(Enum):
    SUPER_ADMIN = "super_admin"      # 超级管理员
    EDUCATION_ADMIN = "education_admin"  # 教育局管理员
    SCHOOL_ADMIN = "school_admin"    # 学校管理员
    TEACHER = "teacher"              # 教师
    ANALYST = "analyst"              # 数据分析师

# 权限定义
PERMISSIONS = {
    'education_data': ['read', 'write', 'delete'],
    'federated_learning': ['train', 'monitor', 'manage'],
    'reports': ['generate', 'view', 'export'],
    'users': ['create', 'modify', 'delete'],
    'system': ['configure', 'monitor', 'maintain']
}
```

#### 权限分配策略
```python
# 基于角色的权限分配
ROLE_PERMISSIONS = {
    'super_admin': {
        'education_data': ['read', 'write', 'delete'],
        'federated_learning': ['train', 'monitor', 'manage'],
        'reports': ['generate', 'view', 'export'],
        'users': ['create', 'modify', 'delete'],
        'system': ['configure', 'monitor', 'maintain']
    },
    'education_admin': {
        'education_data': ['read', 'write'],
        'federated_learning': ['train', 'monitor'],
        'reports': ['generate', 'view', 'export'],
        'users': ['create', 'modify']
    },
    'school_admin': {
        'education_data': ['read', 'write'],
        'reports': ['view', 'export']
    },
    'teacher': {
        'education_data': ['read'],
        'reports': ['view']
    }
}
```

### 用户管理命令

#### 创建管理员用户
```bash
# 创建超级管理员
python -c "
from models.user import User
from utils.database import get_db_sync
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

admin_user = User(
    username='admin',
    email='admin@education.gov.cn',
    password_hash=pwd_context.hash('secure_admin_password'),
    role='super_admin',
    is_active=True,
    permissions=['system.configure', 'system.maintain']
)

db = get_db_sync()
db.add(admin_user)
db.commit()
print('超级管理员创建成功')
"
```

#### 批量创建用户
```python
# 批量创建学校管理员
import csv
from models.user import User

def bulk_create_school_admins(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = User(
                username=row['username'],
                email=row['email'],
                password_hash=pwd_context.hash(row['password']),
                role='school_admin',
                organization_id=row['school_id'],
                is_active=True
            )
            db.add(user)
        db.commit()
```

## 监控和维护

### 监控指标配置

#### Prometheus监控配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'edu_federated_app'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

#### 关键监控指标
```python
# 应用层面指标
METRICS = {
    'http_requests_total': 'HTTP请求总数',
    'http_request_duration_seconds': 'HTTP请求响应时间',
    'fl_training_active': '活跃训练数量',
    'fl_participants_online': '在线参与方数量',
    'privacy_budget_consumed': '隐私预算消耗',
    'data_processing_rate': '数据处理速率'
}

# 系统层面指标
SYSTEM_METRICS = {
    'cpu_usage_percent': 'CPU使用率',
    'memory_usage_bytes': '内存使用量',
    'disk_usage_percent': '磁盘使用率',
    'network_bytes_transmitted': '网络传输量'
}
```

### 日志管理

#### 日志配置
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/edu-federated/application.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'edu_federated': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
```

#### 日志分析脚本
```bash
#!/bin/bash
# log_analyzer.sh

LOG_FILE="/var/log/edu-federated/application.log"
ERROR_PATTERN="ERROR|CRITICAL|Exception"

# 统计错误数量
error_count=$(grep -c "$ERROR_PATTERN" "$LOG_FILE")
echo "错误日志数量: $error_count"

# 分析错误类型
echo "错误类型统计:"
grep "$ERROR_PATTERN" "$LOG_FILE" | \
    awk '{print $4}' | \
    sort | uniq -c | sort -nr

# 最近的错误
echo "最近10条错误:"
tail -n 1000 "$LOG_FILE" | grep "$ERROR_PATTERN" | tail -10
```

## 故障排除

### 常见问题诊断

#### 服务启动失败
```bash
# 检查服务状态
systemctl status edu-federated

# 查看详细错误日志
journalctl -u edu-federated -f

# 检查端口占用
netstat -tlnp | grep :8000

# 验证配置文件
python -c "from config.settings import Settings; print(Settings())"
```

#### 数据库连接问题
```bash
# 检查数据库服务
systemctl status postgresql

# 测试数据库连接
psql -h localhost -U edufl -d edu_federated -c "SELECT version();"

# 检查连接池
python -c "
import asyncio
from utils.database import get_db
async def test_connection():
    db = get_db()
    result = await db.execute('SELECT 1')
    print('数据库连接正常')
asyncio.run(test_connection())
"
```

#### 性能问题排查
```bash
# 系统资源监控
htop
iotop
iftop

# Python性能分析
python -m cProfile -o profile.out main.py
pyprof2calltree -i profile.out -o calltree.out

# 数据库慢查询
psql -U edufl -d edu_federated -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

### 应急处理流程

#### 服务中断应急响应
```bash
#!/bin/bash
# emergency_recovery.sh

EMERGENCY_CONTACT="admin@education.gov.cn"

# 立即重启服务
systemctl restart edu-federated
sleep 10

# 检查服务状态
if systemctl is-active --quiet edu-federated; then
    echo "服务恢复成功" | mail -s "服务恢复通知" "$EMERGENCY_CONTACT"
else
    echo "服务恢复失败，启动备用方案" | mail -s "紧急故障" "$EMERGENCY_CONTACT"
    # 启动备用服务或降级方案
fi
```

## 安全加固

### 系统安全配置

#### 防火墙配置
```bash
# UFW防火墙配置
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# IP白名单
ufw allow from 192.168.1.0/24 to any port 8000
```

#### SSL证书配置
```bash
# Let's Encrypt证书自动续期
certbot --nginx -d your-domain.com

# 自动续期脚本
echo "0 2 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 应用安全加固

#### 输入验证和过滤
```python
# 数据验证装饰器
from functools import wraps
from pydantic import ValidationError

def validate_input(model_class):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 验证输入数据
                validated_data = model_class(**kwargs)
                return await func(*args, validated_data=validated_data)
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
        return wrapper
    return decorator
```

#### 安全头配置
```python
# FastAPI安全中间件
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## 备份和恢复

### 自动备份策略

#### 数据库备份
```bash
#!/bin/bash
# database_backup.sh

BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 数据库备份
pg_dump -U edufl -h localhost edu_federated > "$BACKUP_DIR/db_backup_$DATE.sql"

# 压缩备份文件
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# 清理旧备份(保留30天)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

# 记录备份日志
echo "$(date): Database backup completed" >> /var/log/backup.log
```

#### 配置文件备份
```bash
#!/bin/bash
# config_backup.sh

BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 备份配置文件
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
    /etc/edu-federated/ \
    /opt/edu-federated-learning/config/

# 备份SSL证书
tar -czf "$BACKUP_DIR/ssl_backup_$DATE.tar.gz" \
    /etc/ssl/certs/ \
    /etc/ssl/private/

# 清理旧备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +90 -delete
```

### 灾难恢复流程

#### 完整恢复脚本
```bash
#!/bin/bash
# disaster_recovery.sh

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "请指定备份日期，格式: YYYYMMDD_HHMMSS"
    exit 1
fi

# 停止服务
systemctl stop edu-federated

# 恢复数据库
gunzip -c "/backup/database/db_backup_${BACKUP_DATE}.sql.gz" | \
    psql -U edufl -h localhost edu_federated

# 恢复配置文件
tar -xzf "/backup/config/config_backup_${BACKUP_DATE}.tar.gz" -C /
tar -xzf "/backup/config/ssl_backup_${BACKUP_DATE}.tar.gz" -C /

# 重启服务
systemctl start edu-federated

# 验证恢复
sleep 30
if curl -f http://localhost:8000/health; then
    echo "灾难恢复成功"
else
    echo "恢复验证失败"
    exit 1
fi
```

## 性能调优

### 应用层优化

#### 数据库连接池优化
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql://edufl:password@localhost:5432/edu_federated"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 连接池大小
    max_overflow=30,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600,     # 连接回收时间
    echo=False             # 生产环境关闭SQL日志
)
```

#### 缓存策略优化
```python
# cache_config.py
from redis import Redis
import pickle

class CacheManager:
    def __init__(self):
        self.redis = Redis(
            host='localhost',
            port=6379,
            db=1,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    def get_cached_result(self, key, expire_time=3600):
        """获取缓存结果"""
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        return None
    
    def set_cached_result(self, key, data, expire_time=3600):
        """设置缓存结果"""
        try:
            serialized_data = pickle.dumps(data)
            self.redis.setex(key, expire_time, serialized_data)
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
```

### 系统层优化

#### 内核参数调优
```bash
# /etc/sysctl.conf
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535

# 内存优化
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 文件系统优化
fs.file-max = 2097152
fs.nr_open = 2097152

# 应用sysctl配置
sysctl -p
```

#### 进程资源限制
```bash
# /etc/security/limits.conf
edufl soft nofile 65536
edufl hard nofile 65536
edufl soft nproc 65536
edufl hard nproc 65536
```

### 负载均衡配置

#### Nginx负载均衡
```nginx
upstream edu_federated_backend {
    least_conn;
    server 192.168.1.10:8000 weight=3 max_fails=3 fail_timeout=30s;
    server 192.168.1.11:8000 weight=3 max_fails=3 fail_timeout=30s;
    server 192.168.1.12:8000 weight=2 max_fails=3 fail_timeout=30s backup;
}

server {
    listen 80;
    server_name edu-federated.example.com;
    
    location / {
        proxy_pass http://edu_federated_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 超时设置
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

**维护计划**:
- 📅 每日: 系统健康检查、日志清理
- 📅 每周: 安全补丁更新、备份验证
- 📅 每月: 性能评估、容量规划
- 📅 每季度: 安全审计、架构评审

**文档维护**: 系统运维团队
**最后更新**: 2026年2月28日
