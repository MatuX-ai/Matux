#!/bin/bash

# Sentinel License Client 启动脚本

set -e

echo "🚀 启动 Sentinel License Client"

# 检查Go是否安装
if ! command -v go &> /dev/null; then
    echo "❌ 错误: 未找到Go命令，请先安装Go 1.21+"
    exit 1
fi

# 检查Redis是否运行
if ! nc -z localhost 6379; then
    echo "⚠️  警告: Redis服务未运行，某些功能可能不可用"
    echo "   请启动Redis: redis-server 或使用Docker运行"
fi

# 设置环境变量
export REDIS_HOST=${REDIS_HOST:-localhost}
export REDIS_PORT=${REDIS_PORT:-6379}
export REDIS_DB=${REDIS_DB:-1}
export LICENSE_ISSUER=${LICENSE_ISSUER:-iMatuProject}
export LICENSE_AUDIENCE=${LICENSE_AUDIENCE:-enterprise}
export SECRET_KEY=${SECRET_KEY:-super-secret-key-change-in-production}
export PORT=${PORT:-8080}

echo "🔧 配置信息:"
echo "   Redis Host: $REDIS_HOST:$REDIS_PORT"
echo "   License Issuer: $LICENSE_ISSUER"
echo "   Port: $PORT"

# 安装依赖
echo "📦 安装依赖..."
go mod tidy

# 构建项目
echo "🏗️  构建项目..."
go build -o bin/sentinel-client cmd/server/main.go

# 启动服务
echo "🚀 启动服务..."
echo "   服务地址: http://localhost:$PORT"
echo "   健康检查: http://localhost:$PORT/health"
echo "   API文档: 查看 README.md 获取API使用说明"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

./bin/sentinel-client