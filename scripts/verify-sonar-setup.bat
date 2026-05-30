@echo off
echo 正在验证SonarQube环境配置...
echo.

echo 1. 检查Docker容器状态:
docker-compose -f docker-compose.sonarqube.yml ps

echo.
echo 2. 检查SonarScanner是否可用:
sonar-scanner -v

if %errorlevel% equ 0 (
    echo SonarScanner CLI 工具已正确安装
) else (
    echo SonarScanner CLI 工具未找到，请运行 install-sonar-scanner.bat
)

echo.
echo 3. 测试连接到SonarQube服务:
timeout /t 30 /nobreak >nul
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:9000/sonarqube/api/system/status' -UseBasicParsing; Write-Host '连接成功:' $response.Content } catch { Write-Host '连接失败，请确保SonarQube服务正在运行' }"

echo.
echo 配置验证完成！
pause
