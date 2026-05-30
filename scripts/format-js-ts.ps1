# JS/TS 代码格式化脚本
$nodePath = "C:\Program Files\nodejs"
$env:Path = "$nodePath;" + $env:Path

Write-Host "🔧 开始格式化前端 TypeScript 代码..." -ForegroundColor Cyan
Write-Host ""

# 格式化 src/app 目录
Write-Host "📁 格式化 src/app/..." -ForegroundColor Yellow
npx prettier --write "src/app/**/*.ts" --config "{`"singleQuote`":true,`"semi`":true,`"tabWidth`":2,`"trailingComma`":`"es5`",`"printWidth`":100}"

Write-Host ""
Write-Host "✅ 前端代码格式化完成！" -ForegroundColor Green
