# iMato AI Service 部署指南

## 概述

本文档详细介绍如何部署iMato AI Service到生产环境，包括系统要求、部署步骤、配置说明和维护指南。

## 系统要求

### 最低配置
- **CPU**: 2核
- **内存**: 4GB RAM
- **存储**: 20GB可用空间
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

### 推荐配置
- **CPU**: 4核+
- **内存**: 8GB+ RAM
- **存储**: 50GB+ SSD
- **带宽**: 100Mbps+

## 部署前准备

### 1. 环境变量配置

复制并编辑环境配置文件：

```bash
cp .env.production.example .env.production
```

编辑 `.env.production` 文件，设置必要的配置：

```bash
# JWT密钥（必须修改）
SECRET_KEY=your-very-secure-secret-key-here

# AI服务API密钥（至少设置一个）
OPENAI_API_KEY=sk-your-openai-key
LINGMA_API_KEY=your-lingma-key
DEEPSEEK_API_KEY=your-deepseek-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# 数据库密码
DATABASE_PASSWORD=your-secure-db-password

# 允许的域名
ALLOWED_ORIGINS=https://yourdomain.com
```

### 2. SSL证书准备

为生产环境准备SSL证书：

```bash
# 创建SSL目录
mkdir -p ssl/certs ssl/private

# 复制证书文件
cp your-cert.crt ssl/certs/certificate.crt
cp your-private.key ssl/private/private.key

# 设置权限
chmod 600 ssl/private/private.key
chmod 644 ssl/certs/certificate.crt
```

### 3. 防火墙配置

开放必要端口：

```bash
# Ubuntu/Debian
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 5432  # PostgreSQL (仅内网)
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

## 部署方式

### 方式一：自动化部署脚本

#### Linux/macOS:

```bash
# 赋予执行权限
chmod +x scripts/deploy.sh

# 运行部署脚本
./scripts/deploy.sh
```

#### Windows:

```powershell
# 以管理员身份运行PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\deploy.ps1
```

### 方式二：手动Docker部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 检查服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f ai-backend
```

### 方式三：传统部署

```bash
# 1. 安装Python依赖
cd backend
pip install -r requirements.txt

# 2. 设置环境变量
export $(cat ../.env.production | xargs)

# 3. 初始化数据库
alembic upgrade head

# 4. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 配置说明

### Nginx配置

主要配置文件位于 `nginx/` 目录：

- `nginx.conf`: 主配置文件
- `conf.d/ai-service.conf`: 站点配置

关键配置项：

```nginx
# 限流配置
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;

# 代理设置
location /api/ {
    proxy_pass http://ai_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 数据库配置

PostgreSQL配置要点：

```yaml
# docker-compose.yml
postgres:
  environment:
    - POSTGRES_DB=ai_service
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=your-secure-password
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 监控配置

启用应用监控：

```bash
# 安装监控工具
pip install sentry-sdk[fastapi]

# 配置Sentry
SENTRY_DSN=your-sentry-dsn-here
ENABLE_MONITORING=True
```

## 维护操作

### 日常维护

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f ai-backend

# 重启服务
docker-compose restart ai-backend

# 更新应用
git pull
docker-compose build --no-cache
docker-compose up -d
```

### 数据备份

```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

# 数据库备份
docker-compose exec postgres pg_dump -U postgres ai_service > "$BACKUP_DIR/db_backup_$DATE.sql"

# 配置文件备份
cp .env.production "$BACKUP_DIR/config_backup_$DATE.env"

# 压缩备份
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" -C "$BACKUP_DIR" .

echo "备份完成: backup_$DATE.tar.gz"
```

### 性能监控

```bash
# 监控容器资源使用
docker stats

# 监控应用性能
curl http://localhost:8000/metrics

# 数据库性能
docker-compose exec postgres pg_stat_statements
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :8000
   
   # 查看详细日志
   docker-compose logs ai-backend
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务
   docker-compose exec postgres pg_isready
   
   # 查看数据库日志
   docker-compose logs postgres
   ```

3. **API调用失败**
   ```bash
   # 检查Nginx配置
   docker-compose exec nginx nginx -t
   
   # 测试API连通性
   curl -v http://localhost:8000/health
   ```

### 日志分析

```bash
# 应用日志位置
/var/log/ai_service/production.log

# Nginx访问日志
/var/log/nginx/access.log

# Nginx错误日志
/var/log/nginx/error.log

# 分析访问模式
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -20
```

## 安全加固

### 1. 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 启用防火墙
sudo ufw enable

# 禁用不必要的服务
sudo systemctl disable [service-name]
```

### 2. 应用安全

```bash
# 定期更新依赖
pip list --outdated
pip install --upgrade -r requirements.txt

# 扫描安全漏洞
pip install bandit
bandit -r backend/

# 配置安全头
# 在Nginx配置中已包含
```

### 3. 数据安全

```bash
# 数据库加密
# 在PostgreSQL中启用SSL连接

# 定期备份和测试恢复
# 建立备份验证流程
```

## 扩展部署

### 负载均衡

```yaml
# docker-compose.loadbalancer.yml
version: '3.8'
services:
  loadbalancer:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/loadbalancer.conf:/etc/nginx/nginx.conf
    depends_on:
      - ai-backend-1
      - ai-backend-2

  ai-backend-1:
    # 第一个应用实例
    
  ai-backend-2:
    # 第二个应用实例
```

### Jenkins CI/CD流水线

#### Jenkinsfile配置

```groovy
// Jenkinsfile
def branchName = env.BRANCH_NAME ?: 'develop'
def imageTag = "${branchName}-${env.BUILD_NUMBER}"
def registryUrl = 'your-registry.com'
def imageName = "${registryUrl}/imatuproject:${imageTag}"

def slackChannel = '#deployment-notifications'
def slackCredentialId = 'slack-webhook'

def sonarProperties = [
    'sonar.projectKey=imatuproject',
    'sonar.projectName=iMatuProject',
    'sonar.projectVersion=1.0',
    'sonar.sources=.',
    'sonar.exclusions=**/node_modules/**,**/dist/**,**/*.min.js,**/coverage/**',
    'sonar.coverage.exclusions=**/*.test.*,**/test/**'
]

pipeline {
    agent any
    
    tools {
        nodejs "NodeJS-16"
        jdk "JDK-11"
    }
    
    environment {
        DOCKER_REGISTRY = "$registryUrl"
        IMAGE_NAME = "$imageName"
        SONAR_TOKEN = credentials('sonar-token')
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
                script {
                    echo "检出分支: ${branchName}"
                    echo "构建编号: ${env.BUILD_NUMBER}"
                }
            }
        }
        
        stage('代码质量检查') {
            parallel {
                stage('ESLint检查') {
                    steps {
                        sh 'npm ci'
                        sh 'npm run lint'
                    }
                }
                stage('Stylelint检查') {
                    steps {
                        sh 'npm run lint:css'
                    }
                }
                stage('安全性扫描') {
                    steps {
                        sh 'npm audit'
                    }
                }
            }
        }
        
        stage('单元测试') {
            steps {
                sh 'npm run test:coverage'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'coverage/lcov-report',
                    reportFiles: 'index.html',
                    reportName: '测试覆盖率报告'
                ])
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverage adapters: [jacocoAdapter('coverage/jacoco.xml')]
                }
            }
        }
        
        stage('SonarQube分析') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh "sonar-scanner -D${sonarProperties.join(' -D')}"
                }
            }
        }
        
        stage('构建Docker镜像') {
            steps {
                script {
                    docker.build(imageName, '.').push()
                    echo "镜像构建完成: ${imageName}"
                }
            }
        }
        
        stage('安全扫描') {
            steps {
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image ${imageName}'
            }
        }
        
        stage('部署到测试环境') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    sh "kubectl set image deployment/ai-service ai-backend=${imageName}"
                    sh 'kubectl rollout status deployment/ai-service'
                }
            }
        }
        
        stage('集成测试') {
            when {
                branch 'develop'
            }
            steps {
                sh './scripts/run-integration-tests.sh'
            }
        }
        
        stage('部署到生产环境') {
            when {
                branch 'main'
            }
            steps {
                input message: '确认部署到生产环境?', ok: '部署'
                script {
                    sh "kubectl set image deployment/ai-service-prod ai-backend=${imageName}"
                    sh 'kubectl rollout status deployment/ai-service-prod'
                }
            }
        }
    }
    
    post {
        success {
            script {
                slackSend channel: slackChannel, 
                         color: 'good', 
                         message: "✅ 构建成功! 分支: ${branchName}, 镜像: ${imageName}"
            }
        }
        failure {
            script {
                slackSend channel: slackChannel, 
                         color: 'danger', 
                         message: "❌ 构建失败! 分支: ${branchName}, 请检查Jenkins日志"
            }
        }
        unstable {
            script {
                slackSend channel: slackChannel, 
                         color: 'warning', 
                         message: "⚠️ 构建不稳定! 分支: ${branchName}, 存在警告或测试失败"
            }
        }
    }
}
```

#### Jenkins配置要求

##### 必需插件
- Docker Pipeline
- SonarQube Scanner
- Slack Notification
- HTML Publisher
- JaCoCo
- Kubernetes CLI

##### 凭据配置
```bash
# SonarQube Token
SONAR_TOKEN=your-sonar-token

# Docker Registry凭据
DOCKER_REGISTRY_USERNAME=your-username
DOCKER_REGISTRY_PASSWORD=your-password

# Slack Webhook
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

##### 环境变量设置
```bash
# 在Jenkins系统配置中添加
NODEJS_HOME=/usr/local/nodejs
JAVA_HOME=/usr/lib/jvm/java-11-openjdk
DOCKER_HOST=unix:///var/run/docker.sock
```

#### 触发配置

##### Webhook设置
```bash
# GitHub webhook URL
http://your-jenkins-url/github-webhook/

# 触发事件
- Push events
- Pull request events
- Tag events
```

##### 定时构建
```bash
# 每日凌晨2点执行主分支构建
H 2 * * * %BRANCH_NAME=main

# 每小时执行开发分支构建
H * * * * %BRANCH_NAME=develop
```

### Kubernetes部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-backend
        image: your-registry/ai-service:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: ai-service-secrets
```

## 监控告警

### 基础监控

```bash
# 安装监控工具
sudo apt install prometheus-node-exporter

# 配置告警规则
# prometheus/alert.rules.yml
groups:
- name: ai-service-alerts
  rules:
  - alert: HighCPUUsage
    expr: rate(node_cpu_seconds_total{mode!="idle"}[5m]) > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
```

### 应用监控

```python
# backend/utils/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def setup_monitoring():
    if settings.ENABLE_MONITORING:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0
        )
```

## 升级指南

### 版本升级流程

```bash
# 1. 备份当前版本
./scripts/deploy.sh backup

# 2. 拉取新版本
git pull origin main

# 3. 检查变更
git diff HEAD~1 --name-only

# 4. 更新依赖
docker-compose build --no-cache

# 5. 执行迁移
docker-compose exec ai-backend alembic upgrade head

# 6. 重启服务
docker-compose up -d

# 7. 验证升级
curl http://localhost:8000/health
```

## 支持和维护

### 联系方式

- **技术支持**: support@imatuproject.com
- **文档**: https://docs.imatuproject.com
- **社区**: https://community.imatuproject.com

### 商业支持

提供以下商业支持服务：
- 7×24小时技术支持
- 架构咨询和优化
- 定制开发服务
- 培训和技术转移

---

*最后更新: 2024年2月*