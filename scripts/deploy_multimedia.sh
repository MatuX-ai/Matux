#!/bin/bash
# 多媒体课件支持系统部署脚本

set -e

echo "🚀 开始部署多媒体课件支持系统..."

# 检查环境
echo "🔍 检查系统环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python3"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3，请先安装 pip3"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "⚠️  未找到 Docker，某些功能可能无法使用"
fi

# 创建虚拟环境
echo "🔧 创建 Python 虚拟环境..."
cd /path/to/imato/backend
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装多媒体相关依赖
echo "📥 安装多媒体处理依赖..."
pip install boto3 celery redis pillow python-magic
pip install pdfminer.six python-docx python-pptx markdown weasyprint
pip install trimesh numpy-stl pygltflib

# 数据库迁移
echo "💾 执行数据库迁移..."
python migrations/005_create_multimedia_tables.py upgrade --sync

# 创建上传目录
echo "📁 创建上传目录..."
mkdir -p uploads/{processed,thumbnails,temp}
chmod 755 uploads

# 配置环境变量
echo "⚙️  配置环境变量..."
cat > .env << EOF
# 多媒体系统配置
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./uploads
CDN_DOMAIN=

# AWS 配置 (如使用云存储)
AWS_S3_BUCKET=imato-multimedia
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS MediaConvert 配置
MEDIA_CONVERT_ROLE=
MEDIA_CONVERT_ENDPOINT=
MEDIA_CONVERT_QUEUE=Default
EOF

echo "📝 请根据实际情况修改 .env 文件中的配置"

# 启动 Redis (如果使用本地Redis)
echo "🔄 启动 Redis 服务..."
if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes
    echo "✅ Redis 服务已启动"
else
    echo "⚠️  未找到 Redis 服务器，请手动启动或使用 Docker"
fi

# 启动 Celery Worker
echo "🏃 启动 Celery Worker..."
celery -A celery_app worker --loglevel=info --detach

# 启动 Celery Beat
echo "⏰ 启动 Celery Beat..."
celery -A celery_app beat --loglevel=info --detach

# 启动主应用
echo "🚀 启动主应用服务..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

echo "🎉 部署完成！"
echo "应用查看地址: http://localhost:8000"
echo "API文档地址: http://localhost:8000/docs"
echo "注意: 请确保防火墙允许 8000 端口访问"