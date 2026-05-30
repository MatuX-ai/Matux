#!/bin/bash

# iMatuProject 代码质量检查脚本 (Unix/Linux/macOS)
# 统一执行前端和后端的代码质量检查

echo "========================================"
echo "iMatuProject 代码质量检查"
echo "========================================"

# 检查Node.js环境
echo "检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 前端代码质量检查
echo ""
echo "========================================"
echo "前端代码质量检查"
echo "========================================"

if [ -f "package.json" ]; then
    echo "安装前端依赖..."
    npm install
    
    echo "执行TypeScript/JavaScript lint检查..."
    if ! npm run lint:ts-check; then
        echo "前端TypeScript检查失败"
        FRONTEND_FAILED=1
    fi
    
    echo "执行SCSS样式检查..."
    if ! npm run lint:scss-check; then
        echo "前端SCSS检查失败"
        FRONTEND_FAILED=1
    fi
    
    echo "执行代码格式检查..."
    if ! npm run format:check; then
        echo "前端格式检查失败"
        FRONTEND_FAILED=1
    fi
    
    if [ "$FRONTEND_FAILED" = "1" ]; then
        echo "❌ 前端代码质量检查未通过"
        exit 1
    else
        echo "✅ 前端代码质量检查通过"
    fi
else
    echo "警告: 未找到package.json，跳过前端检查"
fi

# 后端代码质量检查
echo ""
echo "========================================"
echo "后端代码质量检查"
echo "========================================"

if [ -d "backend" ]; then
    cd backend
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        echo "创建Python虚拟环境..."
        python3 -m venv .venv
    fi
    
    echo "激活虚拟环境..."
    source .venv/bin/activate
    
    echo "安装后端开发依赖..."
    pip install -r ../requirements.dev.txt
    
    echo "执行Black格式化检查..."
    if ! black --check .; then
        echo "Black格式化检查失败"
        BACKEND_FAILED=1
    fi
    
    echo "执行isort导入排序检查..."
    if ! isort --check-only .; then
        echo "isort导入排序检查失败"
        BACKEND_FAILED=1
    fi
    
    echo "执行Flake8代码质量检查..."
    if ! flake8 .; then
        echo "Flake8代码质量检查失败"
        BACKEND_FAILED=1
    fi
    
    echo "执行MyPy类型检查..."
    if ! mypy . --ignore-missing-imports; then
        echo "MyPy类型检查失败"
        BACKEND_FAILED=1
    fi
    
    cd ..
    
    if [ "$BACKEND_FAILED" = "1" ]; then
        echo "❌ 后端代码质量检查未通过"
        exit 1
    else
        echo "✅ 后端代码质量检查通过"
    fi
else
    echo "警告: 未找到backend目录，跳过后端检查"
fi

echo ""
echo "========================================"
echo "🎉 所有代码质量检查通过!"
echo "========================================"
exit 0