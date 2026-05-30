@echo off
REM iMatuProject 代码格式化脚本 (Windows)
REM 统一执行前端和后端的代码格式化

echo ========================================
echo iMatuProject 代码格式化
echo ========================================

REM 检查Node.js环境
echo 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js
    exit /b 1
)

REM 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    exit /b 1
)

REM 前端代码格式化
echo.
echo ========================================
echo 前端代码格式化
echo ========================================

if exist "package.json" (
    echo 安装前端依赖...
    npm install
    
    echo 执行代码格式化...
    npm run format
    
    echo 执行TypeScript/JavaScript lint修复...
    npm run lint:ts
    
    echo 执行SCSS样式修复...
    npm run lint:scss
    
    echo ✅ 前端代码格式化完成
) else (
    echo 警告: 未找到package.json，跳过前端格式化
)

REM 后端代码格式化
echo.
echo ========================================
echo 后端代码格式化
echo ========================================

if exist "backend" (
    cd backend
    
    REM 检查虚拟环境
    if not exist ".venv" (
        echo 创建Python虚拟环境...
        python -m venv .venv
    )
    
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
    
    echo 安装后端开发依赖...
    pip install -r ../requirements.dev.txt
    
    echo 执行Black代码格式化...
    black .
    
    echo 执行isort导入排序...
    isort .
    
    echo 执行Flake8代码质量检查...
    flake8 .
    
    cd ..
    
    echo ✅ 后端代码格式化完成
) else (
    echo 警告: 未找到backend目录，跳过后端格式化
)

echo.
echo ========================================
echo 🎉 所有代码格式化完成!
echo ========================================
exit /b 0