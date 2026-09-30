@echo off
REM 【端口处理】清掉可能干扰的 BACKEND_PORT/PORT 环境变量（用户可能之前手动 set 过 8002 等）
REM launcher.js 默认使用 8000，需要自定义端口请在启动前手动 set BACKEND_PORT=8001
set BACKEND_PORT=
set PORT=
REM 【修复 #8】不设置 NODE_ENV=development，避免 main.js 走 dev 分支加载 localhost:4200
REM   原因：未启动 ng serve 时，dev 分支会一直重试连接 Angular dev server，
REM   导致主窗口黑屏无内容（Angular 资源未加载）。
REM   移除 dev 标记后，main.js 会走 app:// 自定义协议加载 dist/imatuproject 的构建产物。
REM   需要热重载开发时，请手动 set NODE_ENV=development 并先启动 npm start
set "PROJECT_ROOT=%~dp0"
echo [%date% %time%] Starting Electron... > "%PROJECT_ROOT%electron-startup.log"
cd /d "%PROJECT_ROOT%electron"
"%PROJECT_ROOT%electron\node_modules\electron\dist\electron.exe" . >> "%PROJECT_ROOT%electron-startup.log" 2>&1
