@echo off
REM iMatuProject 代码质量检查脚本 (Windows)
REM 统一执行前端和后端的代码质量检查

echo ========================================
echo iMatuProject 代码质量检查
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

REM 前端代码质量检查
echo.
echo ========================================
echo 前端代码质量检查
echo ========================================

if exist "package.json" (
    echo 安装前端依赖...
    npm install
    
    echo 执行TypeScript/JavaScript lint检查...
    npm run lint:ts-check
    if %errorlevel% neq 0 (
        echo 前端TypeScript检查失败
        set FRONTEND_FAILED=1
    )
    
    echo 执行SCSS样式检查...
    npm run lint:scss-check
    if %errorlevel% neq 0 (
        echo 前端SCSS检查失败
        set FRONTEND_FAILED=1
    )
    
    echo 执行代码格式检查...
    npm run format:check
    if %errorlevel% neq 0 (
        echo 前端格式检查失败
        set FRONTEND_FAILED=1
    )
    
    if defined FRONTEND_FAILED (
        echo ❌ 前端代码质量检查未通过
        exit /b 1
    ) else (
        echo ✅ 前端代码质量检查通过
    )
) else (
    echo 警告: 未找到package.json，跳过前端检查
)

REM 后端代码质量检查
echo.
echo ========================================
echo 后端代码质量检查
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
    
    echo 执行Black格式化检查...
    black --check .
    if %errorlevel% neq 0 (
        echo Black格式化检查失败
        set BACKEND_FAILED=1
    )
    
    echo 执行isort导入排序检查...
    isort --check-only .
    if %errorlevel% neq 0 (
        echo isort导入排序检查失败
        set BACKEND_FAILED=1
    )
    
    echo 执行Flake8代码质量检查...
    flake8 .
    if %errorlevel% neq 0 (
        echo Flake8代码质量检查失败
        set BACKEND_FAILED=1
    )
    
    echo 执行MyPy类型检查...
    mypy . --ignore-missing-imports
    if %errorlevel% neq 0 (
        echo MyPy类型检查失败
        set BACKEND_FAILED=1
    )
    
    cd ..
    
    if defined BACKEND_FAILED (
        echo ❌ 后端代码质量检查未通过
        exit /b 1
    ) else (
        echo ✅ 后端代码质量检查通过
    )
) else (
    echo 警告: 未找到backend目录，跳过后端检查
)

echo.
echo ========================================
echo 🎉 所有代码质量检查通过!
echo ========================================
exit /b 0