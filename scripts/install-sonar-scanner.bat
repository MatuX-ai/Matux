@echo off
setlocal enabledelayedexpansion

echo 正在安装SonarScanner CLI工具...
echo.

REM 设置安装路径
set INSTALL_DIR=%USERPROFILE%\sonar-scanner
set DOWNLOAD_URL=https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-windows.zip

echo 安装目录: %INSTALL_DIR%
echo 下载地址: %DOWNLOAD_URL%

REM 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM 下载SonarScanner
echo 正在下载SonarScanner...
powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALL_DIR%\sonar-scanner.zip'"

if !errorlevel! neq 0 (
    echo 下载失败，请检查网络连接
    pause
    exit /b 1
)

REM 解压文件
echo 正在解压文件...
powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\sonar-scanner.zip' -DestinationPath '%INSTALL_DIR%' -Force"

REM 找到解压后的目录
for /d %%D in ("%INSTALL_DIR%\sonar-scanner-*") do (
    set SCANNER_DIR=%%D
)

REM 重命名为固定名称
ren "%SCANNER_DIR%" "sonar-scanner-current"

REM 添加到PATH环境变量
echo 正在配置环境变量...
setx PATH "%PATH%;%INSTALL_DIR%\sonar-scanner-current\bin" /M

echo.
echo SonarScanner安装完成！
echo 安装路径: %INSTALL_DIR%\sonar-scanner-current
echo 请重新打开命令提示符以使环境变量生效
echo.
echo 验证安装:
echo sonar-scanner -v
echo.

pause
