FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.enterprise.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.enterprise.txt

# 复制应用代码
COPY backend/enterprise_gateway/ ./enterprise_gateway/
COPY backend/config/ ./config/
COPY backend/utils/ ./utils/

# 创建必要的目录
RUN mkdir -p /app/logs /app/data

# 创建非root用户
RUN groupadd -r enterprise && useradd -r -g enterprise enterprise
RUN chown -R enterprise:enterprise /app
USER enterprise

# 设置环境变量
ENV PYTHONPATH=/app
ENV APP_ENV=production

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["uvicorn", "enterprise_gateway.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
