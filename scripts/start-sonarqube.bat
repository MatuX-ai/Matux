@echo off
echo 正在启动SonarQube服务...
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

REM 启动SonarQube服务
echo 启动SonarQube和PostgreSQL容器...
docker-compose -f docker-compose.sonarqube.yml up -d

if %errorlevel% equ 0 (
    echo.
    echo SonarQube服务启动成功！
    echo 访问地址: http://localhost:9000/sonarqube
    echo 默认用户名: admin
    echo 默认密码: admin
    echo.
    echo 首次登录后请修改默认密码
    echo 等待服务完全启动可能需要1-2分钟...
) else (
    echo 启动失败，请检查错误信息
)

pause
