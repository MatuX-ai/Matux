@echo off
setlocal enabledelayedexpansion

echo 正在执行SonarQube代码扫描...
echo.

REM 检查SonarQube服务状态
echo 1. 检查SonarQube服务状态...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:9000/sonarqube/api/system/status' -UseBasicParsing; Write-Host '✓ SonarQube服务运行正常'; $status = $response.Content | ConvertFrom-Json; Write-Host '  版本:' $status.version } catch { Write-Host '✗ SonarQube服务未运行，请先启动服务'; exit 1 }"

if %errorlevel% neq 0 (
    echo 请运行 scripts\start-sonarqube.bat 启动服务后再试
    pause
    exit /b 1
)

REM 设置扫描参数
set SCAN_TIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set SCAN_TIME=%SCAN_TIME: =0%

echo.
echo 2. 开始根项目扫描...
sonar-scanner -Dsonar.projectKey=imatuproject-full -Dsonar.host.url=http://localhost:9000/sonarqube -Dsonar.login=admin -Dsonar.password=admin

if %errorlevel% equ 0 (
    echo ✓ 根项目扫描完成
    set ROOT_SCAN_SUCCESS=1
) else (
    echo ⚠ 根项目扫描遇到问题
    set ROOT_SCAN_SUCCESS=0
)

echo.
echo 3. 开始后端项目扫描...
cd backend
sonar-scanner -Dsonar.projectKey=imatuproject-backend -Dsonar.host.url=http://localhost:9000/sonarqube -Dsonar.login=admin -Dsonar.password=admin

if %errorlevel% equ 0 (
    echo ✓ 后端项目扫描完成
    set BACKEND_SCAN_SUCCESS=1
) else (
    echo ⚠ 后端项目扫描遇到问题
    set BACKEND_SCAN_SUCCESS=0
)

cd ..

echo.
echo 4. 开始前端项目扫描...
cd src
sonar-scanner -Dsonar.projectKey=imatuproject-frontend -Dsonar.host.url=http://localhost:9000/sonarqube -Dsonar.login=admin -Dsonar.password=admin

if %errorlevel% equ 0 (
    echo ✓ 前端项目扫描完成
    set FRONTEND_SCAN_SUCCESS=1
) else (
    echo ⚠ 前端项目扫描遇到问题
    set FRONTEND_SCAN_SUCCESS=0
)

cd ..

echo.
echo 5. 扫描状态汇总:
echo    根项目: %ROOT_SCAN_SUCCESS%
echo    后端项目: %BACKEND_SCAN_SUCCESS%
echo    前端项目: %FRONTEND_SCAN_SUCCESS%

REM 生成扫描摘要报告
echo. > scan-summary-%SCAN_TIME%.txt
echo SonarQube扫描摘要报告 >> scan-summary-%SCAN_TIME%.txt
echo ========================= >> scan-summary-%SCAN_TIME%.txt
echo 扫描时间: %date% %time% >> scan-summary-%SCAN_TIME%.txt
echo. >> scan-summary-%SCAN_TIME%.txt
echo 项目扫描状态: >> scan-summary-%SCAN_TIME%.txt
echo - 根项目: %ROOT_SCAN_SUCCESS% >> scan-summary-%SCAN_TIME%.txt
echo - 后端项目: %BACKEND_SCAN_SUCCESS% >> scan-summary-%SCAN_TIME%.txt
echo - 前端项目: %FRONTEND_SCAN_SUCCESS% >> scan-summary-%SCAN_TIME%.txt
echo. >> scan-summary-%SCAN_TIME%.txt
echo 访问SonarQube查看详细结果: >> scan-summary-%SCAN_TIME%.txt
echo http://localhost:9000/sonarqube >> scan-summary-%SCAN_TIME%.txt

echo.
echo 扫描完成！摘要报告已保存为 scan-summary-%SCAN_TIME%.txt
echo 请访问 http://localhost:9000/sonarqube 查看详细分析结果

pause
