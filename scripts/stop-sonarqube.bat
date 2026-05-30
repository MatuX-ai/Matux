@echo off
echo 正在停止SonarQube服务...
echo.

docker-compose -f docker-compose.sonarqube.yml down

if %errorlevel% equ 0 (
    echo SonarQube服务已停止
) else (
    echo 停止服务时出现错误
)

pause
