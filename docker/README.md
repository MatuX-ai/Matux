# iMato Cloud - Docker 部署文档

## 📦 概述

本目录包含 iMato 云托管版本的完整 Docker配置，支持多阶段构建、生产环境优化和一键部署。

## 🎯 特性

- ✅ **多阶段构建**：减小最终镜像体积（目标 <500MB）
- ✅ **Alpine 基础镜像**：使用轻量级 Linux 发行版
- ✅ **非 root 用户**：增强容器安全性
- ✅ **健康检查**：自动监控服务状态
- ✅ **进程管理**：Supervisor 管理 Nginx + FastAPI
- ✅ **静态资源优化**：Gzip 压缩、浏览器缓存
- ✅ **反向代理**：Nginx 统一处理 API 请求

## 📁 文件结构

```
docker/
├── nginx.conf              # Nginx 配置文件
├── supervisord.conf        # Supervisor 进程管理配置
└── README.md               # 本文档

Dockerfile.cloud            # 主 Dockerfile（多阶段构建）
.dockerignore              # Docker 构建忽略文件
docker-compose.test.yml    # 本地测试配置
scripts/
├── build_docker_image.sh   # Linux/Mac 构建脚本
└── build-docker-image.ps1  # Windows PowerShell 构建脚本
```

## 🚀 快速开始

### 方式一：使用构建脚本（推荐）

#### Windows (PowerShell)
```powershell
# 构建生产环境镜像
.\scripts\build-docker-image.ps1 -prod

# 构建开发环境镜像
.\scripts\build-docker-image.ps1 -dev

# 无缓存完全重新构建
.\scripts\build-docker-image.ps1 -prod -noCache

# 自定义标签
.\scripts\build-docker-image.ps1 -tag v1.0.0
```

#### Linux/Mac (Bash)
```bash
# 构建生产环境镜像
./scripts/build_docker_image.sh --prod

# 构建开发环境镜像
./scripts/build_docker_image.sh --dev

# 无缓存完全重新构建
./scripts/build_docker_image.sh --prod --no-cache

# 自定义标签
./scripts/build_docker_image.sh --tag v1.0.0
```

### 方式二：手动构建

```bash
# 构建镜像
docker build -f Dockerfile.cloud -t imato-cloud:latest .

# 查看镜像大小
docker images imato-cloud

# 运行容器
docker run -d -p 80:80 -p 443:443 -p 8000:8000 \
  --name imato-app \
  imato-cloud:latest

# 查看日志
docker logs -f imato-app

# 停止容器
docker stop imato-app

# 删除容器
docker rm imato-app
```

## 🧪 本地测试

使用 Docker Compose 快速启动完整的测试环境（包含数据库和 Redis）：

```bash
# 启动所有服务
docker-compose -f docker-compose.test.yml up -d

# 查看服务状态
docker-compose -f docker-compose.test.yml ps

# 查看应用日志
docker-compose -f docker-compose.test.yml logs -f imato-cloud

# 访问应用
# 浏览器打开：http://localhost

# 停止所有服务
docker-compose -f docker-compose.test.yml down

# 清理数据卷（谨慎使用）
docker-compose -f docker-compose.test.yml down -v
```

## 🔍 验证安装

### 1. 检查容器状态
```bash
docker ps | grep imato
```

### 2. 测试健康检查端点
```bash
curl http://localhost:8000/health
```

### 3. 测试前端页面
```bash
curl http://localhost/
```

### 4. 测试 API 端点
```bash
curl http://localhost/api/v1/info
```

## ⚙️ 环境变量配置

在生产环境中，建议通过环境变量配置敏感信息：

```bash
docker run -d -p 80:80 \
  -e SECRET_KEY=your-secret-key-here \
  -e DATABASE_URL=postgresql://user:pass@db:5432/imato \
  -e REDIS_URL=redis://:password@redis:6379/0 \
  -e APP_ENV=production \
  imato-cloud:latest
```

### 关键环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_ENV` | 运行环境 | `production` | 否 |
| `LOG_LEVEL` | 日志级别 | `info` | 否 |
| `SECRET_KEY` | JWT 密钥 | - | **是** |
| `DATABASE_URL` | 数据库连接 | - | **是** |
| `REDIS_URL` | Redis 连接 | - | 否 |
| `JWT_ALGORITHM` | JWT 算法 | `HS256` | 否 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 | `30` | 否 |

## 🛡️ 安全最佳实践

### 1. 使用非 root 用户
Dockerfile 已创建 `appuser` 用户（UID 1001），容器以非特权模式运行。

### 2. 密钥管理
**不要**将密钥硬编码在 Dockerfile 中，使用以下方式之一：
- Docker Secrets（推荐用于 Swarm）
- Kubernetes Secrets（推荐用于 K8s）
- 环境变量注入

### 3. 最小权限原则
仅暴露必要的端口：
- `80` - HTTP（前端 + API 代理）
- `443` - HTTPS（如果启用 SSL）
- `8000` - 直接访问后端 API（可选，调试用）

### 4. 定期更新基础镜像
```bash
# 更新 Alpine 基础镜像
docker pull python:3.11-alpine
docker pull node:20-alpine
```

## 📊 镜像优化技巧

### 当前优化措施
- ✅ 多阶段构建（分离构建时和运行时依赖）
- ✅ 使用 Alpine 基础镜像
- ✅ `.dockerignore` 排除不必要文件
- ✅ 清理缓存和临时文件
- ✅ 合并 RUN 指令减少层数

### 进一步减小体积
```bash
# 使用 distroless 镜像（极致精简，但调试困难）
FROM gcr.io/distroless/python3-debian11

# 使用 UPX 压缩二进制文件
RUN apk add --no-cache upx && \
    upx --best /home/appuser/.local/bin/*
```

## 🐛 故障排查

### 问题 1：容器启动后立即退出
```bash
# 查看日志
docker logs imato-app

# 进入容器调试
docker run -it --entrypoint /bin/bash imato-cloud:latest
```

### 问题 2：无法连接数据库
```bash
# 检查网络连通性
docker exec imato-app ping db

# 验证数据库凭据
docker exec imato-app env | grep DATABASE
```

### 问题 3：前端页面 404
```bash
# 检查静态文件是否存在
docker exec imato-app ls -la /var/www/html

# 查看 Nginx 错误日志
docker exec imato-app cat /var/log/nginx/error.log
```

### 问题 4：健康检查失败
```bash
# 手动执行健康检查
docker exec imato-app curl -f http://localhost:8000/health

# 增加健康检查宽限期
HEALTHCHECK --start-period=60s ...
```

## 📈 性能基准

### 典型指标（参考）
- **镜像大小**: ~450MB（优化后）
- **首次启动时间**: ~30-45 秒
- **内存占用**: ~300-500MB（空闲）
- **并发能力**: ~100-500 QPS（单容器）

### 性能优化建议
1. 使用多副本部署提高并发
2. 启用 Redis 缓存热点数据
3. 配置 Nginx 静态资源缓存
4. 调整 FastAPI worker 数量（CPU 核心数 × 2 + 1）

## 🔄 CI/CD 集成

### GitHub Actions 示例
```yaml
name: Build and Push Docker Image

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and Push
        run: |
          ./scripts/build_docker_image.sh --prod --tag ${GITHUB_REF#refs/tags/}
          docker push imato-cloud:${GITHUB_REF#refs/tags/}
```

## 📚 相关文档

- [Kubernetes 部署指南](../k8s/README.md)
- [Docker Compose 编排](docker-compose.cloud.yml)
- [监控系统集成](../docs/MONITORING_SETUP.md)

## 🆘 获取帮助

如遇到问题：
1. 查看本文档的故障排查部分
2. 检查容器日志：`docker logs <container_id>`
3. 进入容器调试：`docker exec -it <container_id> bash`
4. 提交 Issue 到项目仓库

---

**最后更新**: 2026-03-14  
**维护者**: iMato Team
