@echo off
REM Angular 18 升级脚本
REM 适用于 Windows 系统
REM 在运行前请确保已备份项目

echo ============================================
echo Angular 18 升级脚本
echo ============================================
echo.

REM 检查Node.js版本
echo 检查Node.js版本...
node --version
echo.

REM 步骤1: 全局安装Angular 18 CLI
echo 步骤1: 全局安装Angular 18 CLI...
call npm install -g @angular/cli@^18.2.0
if %errorlevel% neq 0 (
    echo [错误] Angular CLI安装失败
    pause
    exit /b 1
)
echo [成功] Angular CLI安装完成
echo.

REM 步骤2: 更新Angular核心包
echo 步骤2: 更新Angular核心包...
call npx ng update @angular/core@^18.2.0 @angular/cli@^18.2.0 --force
if %errorlevel% neq 0 (
    echo [警告] Angular核心包更新可能需要手动处理
    echo 继续执行下一步...
)
echo.

REM 步骤3: 更新Angular Material
echo 步骤3: 更新Angular Material...
call npx ng update @angular/material@^18.2.0 --force
if %errorlevel% neq 0 (
    echo [警告] Angular Material更新可能需要手动处理
    echo 继续执行下一步...
)
echo.

REM 步骤4: 更新相关依赖
echo 步骤4: 更新相关依赖...
call npm install ngx-monaco-editor-v2@^18.0.0 --save
call npm install ng2-charts@^6.0.0 --save
call npm install @types/node@^20.0.0 --save-dev
echo [成功] 相关依赖更新完成
echo.

REM 步骤5: 清理旧的构建缓存
echo 步骤5: 清理旧的构建缓存...
if exist node_modules (
    rmdir /s /q node_modules
    echo [成功] 删除node_modules
)
if exist package-lock.json (
    del package-lock.json
    echo [成功] 删除package-lock.json
)
if exist dist (
    rmdir /s /q dist
    echo [成功] 删除dist目录
)
echo.

REM 步骤6: 重新安装依赖
echo 步骤6: 重新安装依赖...
call npm install
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    echo 请检查网络连接和npm配置
    pause
    exit /b 1
)
echo [成功] 依赖安装完成
echo.

REM 步骤7: 运行TypeScript检查
echo 步骤7: 运行TypeScript检查...
call npx tsc --noEmit --watch false
if %errorlevel% neq 0 (
    echo [警告] TypeScript检查发现有错误
    echo 请查看错误信息并修复
) else (
    echo [成功] TypeScript检查通过，无错误
)
echo.

REM 步骤8: 运行开发构建测试
echo 步骤8: 运行开发构建测试...
call ng build --configuration development --progress=false
if %errorlevel% neq 0 (
    echo [警告] 开发构建失败
    echo 请查看错误信息并修复
    pause
    exit /b 1
)
echo [成功] 开发构建完成
echo.

REM 步骤9: 运行生产构建测试
echo 步骤9: 运行生产构建测试...
call ng build --configuration production --progress=false
if %errorlevel% neq 0 (
    echo [警告] 生产构建失败
    echo 请查看错误信息并修复
    pause
    exit /b 1
)
echo [成功] 生产构建完成
echo.

REM 完成
echo ============================================
echo Angular 18 升级完成！
echo ============================================
echo.
echo 下一步操作：
echo 1. 运行 'npm start' 启动开发服务器
echo 2. 打开浏览器访问 http://localhost:4200/marketing
echo 3. 测试所有功能是否正常工作
echo.
echo 如果遇到问题，请查看：
echo - ANGULAR_UPGRADE_GUIDE.md 升级指南
echo - BUILD_DIAGNOSTIC_REPORT.md 诊断报告
echo.
pause
