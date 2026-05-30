@echo off
echo ==================================================
echo 开始验证Fabric网络部署环境...
echo ==================================================

echo.
echo 检查Docker环境:
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Docker已安装
    docker info >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ Docker服务正在运行
    ) else (
        echo   × Docker服务未运行，请启动Docker Desktop
        exit /b 1
    )
) else (
    echo   × Docker未安装或不可用
    echo     请先安装Docker Desktop
    exit /b 1
)

echo.
echo 检查Docker Compose:
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Docker Compose已安装
) else (
    echo   ! Docker Compose未找到，尝试使用docker compose命令
    docker compose version >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ Docker Compose插件可用
    ) else (
        echo   × Docker Compose不可用
        exit /b 1
    )
)

echo.
echo 检查必要端口占用情况:
set occupied_ports=0
for %%p in (7050 7051 7054 8051 8054 9051 9054 11051 11054) do (
    netstat -an | findstr ":%%p " >nul
    if %errorlevel% equ 0 (
        echo   ! 端口 %%p 已被占用
        set /a occupied_ports+=1
    ) else (
        echo   ✓ 端口 %%p 可用
    )
)

if %occupied_ports% gtr 0 (
    echo.
    echo 警告: 发现 %occupied_ports% 个端口被占用，可能影响部署
    echo 建议关闭占用这些端口的应用程序或修改配置
)

echo.
echo 检查磁盘空间:
for /f "tokens=2" %%i in ('wmic LogicalDisk Where "DeviceID='%cd:~0,2%'" Get FreeSpace ^| findstr [0-9]') do set free_space=%%i
set /a free_gb=%free_space%/1073741824
echo   可用空间: %free_gb% GB

if %free_gb% lss 5 (
    echo   ! 可用空间不足5GB，建议清理磁盘空间
) else (
    echo   ✓ 磁盘空间充足
)

echo.
echo 检查Fabric工具:
set tools_found=0
for %%t in (cryptogen configtxgen peer orderer) do (
    where %%t >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ %%t 已安装
        set /a tools_found+=1
    ) else (
        echo   ! %%t 未找到
    )
)

echo.
echo ==================================================
echo 环境验证总结:
echo ==================================================
echo   验证时间: %date% %time%
echo   Docker状态: 已安装并运行
echo   Docker Compose: 可用
echo   磁盘空间: %free_gb% GB 可用
echo   Fabric工具: %tools_found%/4 已找到

if %occupied_ports% gtr 0 (
    echo   端口冲突: %occupied_ports% 个端口被占用
) else (
    echo   端口状态: 全部可用
)

echo.
echo ✓ 环境验证完成!

if %occupied_ports% gtr 3 (
    echo.
    echo 警告: 检测到多个端口冲突，是否继续部署? (y/N)
    set /p continue=
    if /i not "%continue%"=="y" (
        echo 部署已取消
        exit /b 1
    )
)