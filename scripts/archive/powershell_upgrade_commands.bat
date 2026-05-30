@echo off
echo =================================
echo Angular 21 升级 PowerShell 命令
echo =================================
echo.

echo 步骤 1: 清理旧依赖...
powershell -Command "cd 'g:\iMato'; Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue; Remove-Item package-lock.json, yarn.lock -ErrorAction SilentlyContinue"
echo.

echo 步骤 2: 安装新依赖...
powershell -Command "cd 'g:\iMato'; yarn install"
echo.

echo 步骤 3: 验证安装...
powershell -Command "cd 'g:\iMato'; ng version"
echo.

echo 步骤 4: 启动开发服务器...
powershell -Command "cd 'g:\iMato'; ng serve"
echo.

pause
