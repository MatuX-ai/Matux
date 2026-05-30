@echo off
REM Sentinel License Client Windows启动脚本

echo 🚀 启动 Sentinel License Client

REM 检查Go是否安装
go version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Go命令，请先安装Go 1.21+
    pause
    exit /b 1
)

REM 设置环境变量
set REDIS_HOST=%REDIS_HOST%
if "%REDIS_HOST%"=="" set REDIS_HOST=localhost

set REDIS_PORT=%REDIS_PORT%
if "%REDIS_PORT%"=="" set REDIS_PORT=6379

set REDIS_DB=%REDIS_DB%
if "%REDIS_DB%"=="" set REDIS_DB=1

set LICENSE_ISSUER=%LICENSE_ISSUER%
if "%LICENSE_ISSUER%"=="" set LICENSE_ISSUER=iMatuProject

set LICENSE_AUDIENCE=%LICENSE_AUDIENCE%
if "%LICENSE_AUDIENCE%"=="" set LICENSE_AUDIENCE=enterprise

set SECRET_KEY=%SECRET_KEY%
if "%SECRET_KEY%"=="" set SECRET_KEY=super-secret-key-change-in-production

set PORT=%PORT%
if "%PORT%"=="" set PORT=8080

echo 🔧 配置信息:
echo    Redis Host: %REDIS_HOST%:%REDIS_PORT%
echo    License Issuer: %LICENSE_ISSUER%
echo    Port: %PORT%

REM 安装依赖
echo 📦 安装依赖...
go mod tidy

REM 构建项目
echo 🏗️  构建项目...
go build -o bin\sentinel-client.exe cmd\server\main.go

REM 启动服务
echo 🚀 启动服务...
echo    服务地址: http://localhost:%PORT%
echo    健康检查: http://localhost:%PORT%/health
echo    API文档: 查看 README.md 获取API使用说明
echo.
echo 按 Ctrl+C 停止服务
echo.

bin\sentinel-client.exe

pause