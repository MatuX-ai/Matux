@echo off
echo 正在运行代码质量检查工具...
echo.

REM 创建输出目录
if not exist "quality-reports" mkdir "quality-reports"

echo 1. 运行ESLint检查前端代码...
npm run lint:ts-check > quality-reports\eslint-report.txt 2>&1
if %errorlevel% equ 0 (
    echo ✓ ESLint检查完成
) else (
    echo ⚠ ESLint发现一些问题，请查看 quality-reports\eslint-report.txt
)

echo.
echo 2. 运行Stylelint检查CSS/SCSS...
npm run lint:scss-check > quality-reports\stylelint-report.txt 2>&1
if %errorlevel% equ 0 (
    echo ✓ Stylelint检查完成
) else (
    echo ⚠ Stylelint发现一些问题，请查看 quality-reports\stylelint-report.txt
)

echo.
echo 3. 运行Python Flake8检查...
cd backend
flake8 . --format=pylint --output-file=..\quality-reports\flake8-report.txt
if %errorlevel% equ 0 (
    echo ✓ Flake8检查完成
) else (
    echo ⚠ Flake8发现一些问题，请查看 quality-reports\flake8-report.txt
)

echo.
echo 4. 运行Python Black格式化检查...
black --check . > ..\quality-reports\black-report.txt 2>&1
if %errorlevel% equ 0 (
    echo ✓ Black格式化检查通过
) else (
    echo ⚠ 代码格式需要调整，请查看 quality-reports\black-report.txt
)

cd ..

echo.
echo 5. 运行安全扫描...
npm audit --audit-level=moderate > quality-reports\npm-audit-report.txt 2>&1
echo ✓ npm安全扫描完成

echo.
echo 所有质量检查完成！报告保存在 quality-reports 目录中。
pause
