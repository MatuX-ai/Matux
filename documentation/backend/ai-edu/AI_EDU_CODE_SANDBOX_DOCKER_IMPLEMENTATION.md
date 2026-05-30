# AI-Edu 代码沙箱 Docker 容器隔离实现方案

## 📋 目录

- [概述](#概述)
- [安全风险分析](#安全风险分析)
- [Docker 容器隔离架构](#docker 容器隔离架构)
- [实现步骤](#实现步骤)
- [配置文件](#配置文件)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)

---

## 概述

### 目标
为 AI-Edu 平台的代码执行功能提供安全的沙箱环境，防止恶意代码对系统造成危害。

### 核心功能
- ✅ **容器化执行**: 每个代码执行请求在独立的 Docker 容器中运行
- ✅ **资源限制**: CPU、内存、磁盘空间配额管理
- ✅ **网络隔离**: 禁止容器访问外部网络（可选白名单）
- ✅ **文件系统隔离**: 只读根文件系统，临时写入目录限制
- ✅ **超时控制**: 自动终止长时间运行的代码
- ✅ **安全审计**: 记录所有代码执行日志

---

## 安全风险分析

### 潜在威胁

1. **系统调用攻击**
   - `os.system()`, `subprocess` 执行系统命令
   - 文件操作：删除、修改敏感文件
   - 进程注入、提权

2. **资源耗尽攻击**
   - CPU 占用 100%
   - 内存泄漏/溢出
   - 磁盘空间填满

3. **网络攻击**
   - DDoS 攻击
   - 数据外泄
   - 端口扫描

4. **Python 内置危险函数**
   ```python
   eval(), exec(), compile()  # 动态代码执行
   open()                      # 文件访问
   __import__()                # 模块导入
   ```

---

## Docker 容器隔离架构

### 架构图

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Code Execution API Endpoint    │  │
│  └────────────┬─────────────────────┘  │
│               │                         │
│  ┌────────────▼─────────────────────┐  │
│  │   Sandbox Manager (Python)       │  │
│  │   - 验证代码                     │  │
│  │   - 创建容器                     │  │
│  │   - 监控执行                     │  │
│  │   - 清理资源                     │  │
│  └────────────┬─────────────────────┘  │
└───────────────┼─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      Docker Daemon                      │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Container 1 (Student A)        │   │
│  │  ├─ CPU: 0.5 core              │   │
│  │  ├─ Memory: 128MB              │   │
│  │  ├─ Network: Disabled          │   │
│  │  ├─ Storage: /tmp only         │   │
│  │  └─ Timeout: 5s                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Container 2 (Student B)        │   │
│  │  └─ ... (完全隔离)             │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 技术栈

- **运行时**: Docker Engine 20.10+
- **Python SDK**: docker-py >= 5.0
- **基础镜像**: python:3.9-slim (精简版，减少攻击面)
- **编排工具**: Docker Compose (开发环境)

---

## 实现步骤

### 步骤 1: 安装依赖

```bash
# 后端依赖
pip install docker==6.1.0
```

### 步骤 2: 创建 Docker 基础镜像

```dockerfile
# backend/docker/sandbox-base/Dockerfile
FROM python:3.9-slim

# 创建非 root 用户
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# 安装必要的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /sandbox

# 切换到非特权用户
USER sandbox

# 默认命令
CMD ["python", "-c", "print('Sandbox ready')"]
```

### 步骤 3: 实现沙箱管理器

```python
# backend/services/code_sandbox_service.py
```

### 步骤 4: 更新代码执行路由

```python
# backend/routes/ai_edu_code_execution.py
```

### 步骤 5: 配置 Docker Compose

```yaml
# docker-compose.ai-edu.yml
```

---

## 配置文件

### Dockerfile: 沙箱基础镜像

```dockerfile
# backend/docker/sandbox-base/Dockerfile
FROM python:3.9-slim

LABEL maintainer="AI-Edu Team"
LABEL description="Secure code execution sandbox for AI-Edu platform"

# 创建非 root 用户和用户组
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# 安装最小化的系统包
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /sandbox

# 复制 requirements（如果有）
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# 限制权限：只读文件系统
# 通过 Docker run 时的 read_only 参数实现

# 切换到非特权用户
USER sandbox

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "print('OK')" || exit 1

# 默认命令
CMD ["python", "-c", "import sys; print(f'Python {sys.version}')"]
```

### Docker Compose: 开发环境配置

```yaml
# docker-compose.ai-edu.dev.yml
version: '3.8'

services:
  ai-edu-api:
    build:
      context: ./backend
      dockerfile: docker/sandbox-base/Dockerfile
    container_name: ai-edu-sandbox-dev
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app:ro  # 只读挂载代码
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
    ports:
      - "8000:8000"
    networks:
      - ai-edu-network
    restart: unless-stopped

networks:
  ai-edu-network:
    driver: bridge
```

### Python 服务实现

详见下一个文件：`code_sandbox_service.py`

---

## 使用示例

### 1. HTTP API 调用

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/org/1/ai-edu/execute-code',
    json={
        'code': '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
''',
        'language': 'python',
        'timeout_seconds': 5
    }
)

result = response.json()
print(result)
# {
#   "success": true,
#   "data": {
#     "output": "55\n",
#     "execution_time_ms": 45.2,
#     "memory_used_kb": 8192
#   }
# }
```

### 2. WebSocket 实时输出

```typescript
// Angular 服务
this.wsService.connect(userId, orgId, baseUrl);

this.wsService.sendMessage({
  type: 'execute_code',
  data: {
    code: 'print("Hello from sandbox!")',
    language: 'python'
  }
});

this.wsService.onMessageType('code_output').subscribe(data => {
  console.log('实时输出:', data.output);
});
```

---

## 最佳实践

### 1. 安全配置清单

- ✅ **始终使用非 root 用户**
- ✅ **限制资源配额** (CPU 50%, Memory 128MB)
- ✅ **禁用网络访问** (除非必要)
- ✅ **只读文件系统** (除 /tmp 外)
- ✅ **设置执行超时** (默认 5 秒)
- ✅ **记录所有执行日志**
- ✅ **定期更新基础镜像**
- ✅ **监控异常行为**

### 2. 代码审查规则

```python
DANGEROUS_PATTERNS = [
    r'__import__',
    r'eval\s*\(',
    r'exec\s*\(',
    r'compile\s*\(',
    r'open\s*\([^)]*[\'"][^\'"]*[\'"]',  # 文件路径
    r'os\.(system|popen|spawn)',
    r'subprocess\.',
    r'socket\.',
    r'requests\.',
    r'urllib\.',
]
```

### 3. 监控指标

```python
MONITORING_METRICS = {
    'execution_count': '总执行次数',
    'avg_execution_time': '平均执行时间',
    'timeout_rate': '超时率',
    'error_rate': '错误率',
    'container_reuse_rate': '容器复用率',
    'memory_usage_p95': 'P95 内存使用',
    'cpu_usage_p95': 'P95 CPU 使用',
}
```

### 4. 故障恢复策略

```python
RETRY_STRATEGY = {
    'max_retries': 3,
    'retry_delay_seconds': 1,
    'exponential_backoff': True,
    'retry_on': ['TimeoutError', 'ContainerCrashed', 'ResourceExhausted']
}
```

---

## 性能优化

### 1. 容器预热池

```python
class ContainerPool:
    def __init__(self, pool_size=5):
        self.pool = []
        for _ in range(pool_size):
            container = self.create_container()
            self.pool.append(container)
    
    def acquire(self):
        # 获取空闲容器
        pass
    
    def release(self, container):
        # 重置并返回容器到池中
        pass
```

### 2. 镜像分层缓存

```dockerfile
# 利用 Docker 层缓存加速构建
FROM python:3.9-slim

# 先复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制代码（经常变化）
COPY . .
```

---

## 故障排查

### 常见问题

1. **Docker Socket 权限不足**
   ```bash
   sudo usermod -aG docker $USER
   ```

2. **容器无法启动**
   ```bash
   docker logs <container_id>
   ```

3. **内存限制过严**
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 256M  # 调整为 256MB
   ```

---

## 下一步计划

- [ ] 实现 gVisor 或 Kata Containers 增强隔离
- [ ] 添加 eBPF 系统调用监控
- [ ] 支持多种编程语言沙箱
- [ ] 实现分布式沙箱集群
- [ ] 集成 AI 代码安全检测

---

## 参考资源

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Code Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html)
- [Python Sandbox Security](https://nedbatchelder.com/blog/201206/breaking_python_with_1_line.html)

---

**文档版本**: v1.0  
**更新日期**: 2026-03-03  
**维护团队**: AI-Edu Development Team
