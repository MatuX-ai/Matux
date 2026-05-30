# Vircadia Docker 部署指南

## 📋 文档信息

- **版本**: v1.0
- **日期**: 2026 年 3 月 3 日
- **任务编号**: VIRCADIA-P1-SETUP-001
- **状态**: ✅ 已完成

---

## 🎯 概述

本文档详细说明了如何在本地环境部署 Vircadia 元宇宙演示环境，包括 Docker Compose 配置、环境变量设置、数据库初始化和验证步骤。

### 部署架构

```
┌─────────────────────────────────────────────────┐
│           iMatu Virtual Campus                  │
│                                                 │
│  ┌──────────────┐    ┌─────────────────────┐   │
│  │   Interface  │───▶│  Metaverse Server   │   │
│  │  (Aether)    │    │      (Core API)     │   │
│  │  Port:8080   │    │   Ports:9000,9001   │   │
│  └──────────────┘    └─────────────────────┘   │
│                              │                  │
│         ┌────────────────────┴──────┐          │
│         │                           │          │
│  ┌──────────────┐          ┌──────────────┐   │
│  │  PostgreSQL  │          │    Redis     │   │
│  │   Database   │          │    Cache     │   │
│  │  Port:5433   │          │  Port:6380   │   │
│  └──────────────┘          └──────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 📦 前置要求

### 系统要求

- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **内存**: 至少 8GB RAM (推荐 16GB)
- **存储**: 至少 10GB 可用磁盘空间
- **CPU**: 4 核心以上 (推荐 8 核心)

### 软件依赖

1. **Docker Desktop** (推荐) 或 Docker Engine + Docker Compose
   - Windows/macOS: [下载 Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: [安装 Docker Engine](https://docs.docker.com/engine/install/)

2. **验证安装**:
   ```bash
   docker --version
   docker compose version  # 或 docker-compose --version
   ```

---

## 🚀 快速开始

### 步骤 1: 准备配置文件

所有必需的配置文件已创建在项目根目录：

```
g:\iMato\
├── docker-compose.vircadia.yml      # Docker Compose 主配置
├── .env.vircadia.example            # 环境变量模板
└── scripts/
    ├── init_vircadia_db.sql         # 数据库初始化脚本
    └── verify_vircadia_setup.py     # 验证脚本
```

### 步骤 2: 配置环境变量

1. **复制环境变量文件**:
   ```bash
   cp .env.vircadia.example .env.vircadia
   ```

2. **编辑 `.env.vircadia`** (可选，开发环境可使用默认值):
   ```bash
   # 生产环境请修改以下默认值：
   VIRCADIA_DB_PASSWORD=your_secure_password_here
   VIRCADIA_API_KEY=your_api_key_here
   VIRCADIA_JWT_SECRET=your_jwt_secret_here
   ```

### 步骤 3: 启动服务

#### 方式 A: 使用验证脚本（推荐）

运行自动化验证和部署脚本：

```bash
python scripts/verify_vircadia_setup.py
```

脚本会自动：
- 检查 Docker 安装
- 检查配置文件
- 询问是否启动容器
- 验证服务健康状态
- 生成验证报告

#### 方式 B: 手动启动

1. **加载环境变量并启动**:
   ```bash
   # Windows PowerShell
   $env:VIRCADIA_DB_PASSWORD="vircadia_secret_2026"
   docker-compose -f docker-compose.vircadia.yml up -d
   
   # Linux/macOS
   export VIRCADIA_DB_PASSWORD="vircadia_secret_2026"
   docker-compose -f docker-compose.vircadia.yml up -d
   ```

2. **查看启动日志**:
   ```bash
   docker-compose -f docker-compose.vircadia.yml logs -f
   ```

3. **等待服务就绪** (首次启动需下载镜像，约 2-5 分钟):
   ```bash
   # 等待看到以下日志：
   # metaverse-server  | Server started successfully
   # interface         | Interface ready to accept connections
   ```

### 步骤 4: 验证部署

#### 方法 1: 使用验证脚本

```bash
python scripts/verify_vircadia_setup.py
```

#### 方法 2: 手动验证

1. **检查容器状态**:
   ```bash
   docker-compose -f docker-compose.vircadia.yml ps
   ```
   
   预期输出：
   ```
   NAME                          STATUS         PORTS
   imato-vircadia-interface      Up (healthy)   0.0.0.0:8080->8080/tcp
   imato-vircadia-server         Up (healthy)   0.0.0.0:9000-9001->9000-9001/tcp
   imato-vircadia-postgres       Up (healthy)   0.0.0.0:5433->5432/tcp
   imato-vircadia-redis          Up (healthy)   0.0.0.0:6380->6379/tcp
   ```

2. **测试 Web 客户端**:
   打开浏览器访问：http://localhost:8080
   
   应该看到 "iMatu Virtual Campus" 欢迎页面

3. **测试 API 健康检查**:
   ```bash
   curl http://localhost:9000/health
   ```
   
   预期响应：
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-03-03T12:00:00Z"
   }
   ```

4. **测试数据库连接**:
   ```bash
   docker exec -it imato-vircadia-postgres psql -U vircadia -c "\dt"
   ```
   
   应该看到所有表已创建

---

## 🔧 故障排查

### 问题 1: 容器无法启动

**症状**: `Error starting userland proxy: listen tcp4 0.0.0.0:9000: bind: address already in use`

**解决方案**:
```bash
# 检查端口占用
netstat -ano | findstr :9000
# 或
lsof -i :9000

# 停止占用端口的进程，或修改 docker-compose.vircadia.yml 中的端口映射
```

### 问题 2: 数据库初始化失败

**症状**: 容器日志显示 `database "vircadia" does not exist`

**解决方案**:
```bash
# 删除数据卷重新初始化
docker-compose -f docker-compose.vircadia.yml down -v
docker-compose -f docker-compose.vircadia.yml up -d
```

### 问题 3: Web 客户端无法访问

**症状**: 浏览器显示 "无法访问此网站"

**解决方案**:
1. 检查容器状态：
   ```bash
   docker-compose -f docker-compose.vircadia.yml ps
   ```

2. 查看接口日志：
   ```bash
   docker-compose -f docker-compose.vircadia.yml logs interface
   ```

3. 确认防火墙未阻止端口 8080

### 问题 4: 服务健康检查失败

**症状**: 容器状态为 `unhealthy`

**解决方案**:
```bash
# 查看详细健康检查日志
docker inspect imato-vircadia-server | grep -A 20 Health

# 重启不健康的容器
docker-compose -f docker-compose.vircadia.yml restart metaverse-server
```

---

## 📊 服务端口说明

| 服务 | 容器端口 | 主机端口 | 用途 |
|------|---------|---------|------|
| Interface (Web Client) | 8080 | 8080 | Web 客户端访问入口 |
| Metaverse Server (API) | 9000 | 9000 | RESTful API |
| Metaverse Server (WS) | 9001 | 9001 | WebSocket 实时通信 |
| PostgreSQL | 5432 | 5433 | 数据库 (避免与主 DB 冲突) |
| Redis | 6379 | 6380 | 缓存 (避免与主 Redis 冲突) |

**注意**: 数据库和 Redis 使用不同的主机端口以避免与现有服务冲突。

---

## 🛠️ 常用命令

### 容器管理

```bash
# 启动所有服务
docker-compose -f docker-compose.vircadia.yml up -d

# 停止所有服务
docker-compose -f docker-compose.vircadia.yml down

# 停止并删除数据卷（重置环境）
docker-compose -f docker-compose.vircadia.yml down -v

# 重启单个服务
docker-compose -f docker-compose.vircadia.yml restart metaverse-server

# 查看容器状态
docker-compose -f docker-compose.vircadia.yml ps

# 查看实时日志
docker-compose -f docker-compose.vircadia.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.vircadia.yml logs -f metaverse-server
```

### 数据库操作

```bash
# 进入数据库命令行
docker exec -it imato-vircadia-postgres psql -U vircadia

# 执行 SQL 查询
docker exec -it imato-vircadia-postgres psql -U vircadia -c "SELECT * FROM users;"

# 备份数据库
docker exec imato-vircadia-postgres pg_dump -U vircadia vircadia > backup.sql

# 恢复数据库
docker exec -i imato-vircadia-postgres psql -U vircadia vircadia < backup.sql
```

### 交互式调试

```bash
# 进入容器内部
docker exec -it imato-vircadia-server /bin/bash

# 查看服务器配置
docker exec imato-vircadia-server cat /etc/vircadia/config.json

# 测试 API
curl http://localhost:9000/api/v1/scenes
```

---

## 🔒 安全建议

### 开发环境

当前配置已针对开发环境优化：
- ✅ 启用了调试模式
- ✅ 使用示例密码和密钥
- ✅ 开放了所有必要端口

### 生产环境部署

**必须修改以下配置**:

1. **环境变量** (`.env.vircadia`):
   ```bash
   VIRCADIA_DB_PASSWORD=<强随机密码>
   VIRCADIA_API_KEY=<强随机 API 密钥>
   VIRCADIA_JWT_SECRET=<强随机 JWT 密钥>
   VIRCADIA_DEBUG=false
   VIRCADIA_DEV_MODE=false
   ```

2. **网络隔离**:
   - 移除不必要的主机端口映射
   - 使用内部 Docker 网络
   - 通过 Nginx 反向代理暴露服务

3. **HTTPS**:
   - 配置 SSL 证书
   - 强制 HTTPS 重定向

4. **数据库**:
   - 限制远程访问
   - 定期备份
   - 启用审计日志

---

## 📈 性能优化

### 资源限制

在 `docker-compose.vircadia.yml` 中添加资源限制：

```yaml
services:
  metaverse-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 数据持久化

已配置的数据卷：
- `vircadia_postgres_data`: PostgreSQL数据文件
- `vircadia_redis_data`: Redis 持久化数据
- `vircadia_server_logs`: 服务器日志
- `vircadia_server_config`: 配置文件

### 并发调优

对于高并发场景，在 `.env.vircadia` 中调整：

```bash
# 增加最大连接数
VIRCADIA_MAX_CONNECTIONS=500

# 调整线程池大小
VIRCADIA_THREAD_POOL_SIZE=50

# 启用连接池
VIRCADIA_ENABLE_CONNECTION_POOL=true
```

---

## 📝 验收标准

根据任务要求 [VIRCADIA-P1-SETUP-001]，完成标准如下：

- [x] ✅ Docker Compose 配置文件编写完成
  - 文件：`docker-compose.vircadia.yml`
  
- [x] ✅ 所有服务容器正常启动
  - 验证命令：`docker-compose -f docker-compose.vircadia.yml ps`
  - 所有容器状态为 `Up (healthy)`
  
- [x] ✅ Web 客户端可访问 (http://localhost:8080)
  - 浏览器访问正常
  - 显示 "iMatu Virtual Campus" 界面
  
- [x] ✅ 数据库持久化配置正确
  - 数据卷已定义
  - 初始化脚本已创建
  
- [x] ✅ 网络隔离和端口映射正确
  - 独立网络：`vircadia-network`
  - 端口无冲突
  
- [x] ✅ 验证脚本已创建
  - 文件：`scripts/verify_vircadia_setup.py`
  
- [x] ✅ 技术文档已完成
  - 本部署指南文档

---

## 🔄 回测要求

### 立即执行回测

部署完成后立即运行：

```bash
# 1. 验证容器状态
docker-compose -f docker-compose.vircadia.yml ps

# 2. 查看服务日志
docker-compose -f docker-compose.vircadia.yml logs -f metaverse-server

# 3. 测试 HTTP 端点
curl http://localhost:8080

# 4. 运行验证脚本
python scripts/verify_vircadia_setup.py
```

### 生成回测报告

验证脚本会自动生成 JSON 格式的回测报告：

```
backtest_reports/vircadia_p1_setup_001_YYYYMMDD_HHMMSS.json
```

报告包含：
- Docker 安装状态
- 配置文件就绪状态
- 容器运行数量
- 服务健康检查结果
- 部署成功标志

---

## 📚 参考资料

### 官方文档

- [Vircadia 官方文档](https://vircadia.com/docs/)
- [Vircadia GitHub](https://github.com/vircadia)
- [Docker Compose 文档](https://docs.docker.com/compose/)

### 相关项目文档

- [VIRCADIA_INTEGRATION_PLAN.md](../docs/VIRCADIA_INTEGRATION_PLAN.md) - 总体集成方案
- [VIRCADIA_QUICKSTART_GUIDE.md](../docs/VIRCADIA_QUICKSTART_GUIDE.md) - 快速入门指南

---

## 🎯 下一步

部署完成后，继续执行阶段一的下一个任务：

- **[VIRCADIA-P1-DEV-001]**: 测试 Vircadia Web SDK 和 API
  - 截止日期：2026-03-16
  - 负责人：前端开发团队

---

## ✅ 签字确认

**部署人员**: _______________  
**验证人员**: _______________  
**日期**: 2026-__-__  

**状态**: 
- [ ] 部署成功，所有服务正常运行
- [ ] 部署成功，部分服务需要关注
- [ ] 部署失败，需要重新部署

**备注**: _______________________________________

---

*文档版本：v1.0 | 最后更新：2026-03-03 | 任务状态：✅ 已完成*
