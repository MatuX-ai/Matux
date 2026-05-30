@echo off
setlocal
set "NODE_PATH=C:\Program Files\nodejs"
set "PATH=%NODE_PATH%;%PATH%"

cd /d %~dp0

echo 🔧 开始格式化前端 TypeScript 代码...
echo.
echo 📁 格式化 src/app/...
call npx prettier --write "src/app/**/*.ts"

echo.
echo ✅ 前端代码格式化完成！
endlocal
