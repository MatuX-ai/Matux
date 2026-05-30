@echo off
echo 正在生成测试覆盖率报告...
echo.

REM 创建覆盖率报告目录
if not exist "coverage-reports" mkdir "coverage-reports"

echo 1. 生成Python测试覆盖率报告...
cd backend

REM 运行Python测试并生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=xml:coverage.xml --cov-report=html:htmlcov --junitxml=test-results.xml

if %errorlevel% equ 0 (
    echo ✓ Python测试覆盖率报告生成完成
    echo   - XML报告: coverage.xml
    echo   - HTML报告: htmlcov/index.html
    echo   - JUnit报告: test-results.xml
) else (
    echo ⚠ Python测试执行出现问题
)

cd ..

echo.
echo 2. 生成TypeScript测试覆盖率报告...
npm run test:coverage

if %errorlevel% equ 0 (
    echo ✓ TypeScript测试覆盖率报告生成完成
    echo   - LCOV报告: coverage/lcov.info
    echo   - HTML报告: coverage/index.html
) else (
    echo ⚠ TypeScript测试执行出现问题
)

echo.
echo 3. 复制报告到统一目录...
xcopy backend\coverage.xml coverage-reports\ /Y >nul 2>&1
xcopy backend\test-results.xml coverage-reports\ /Y >nul 2>&1
xcopy coverage\lcov.info coverage-reports\ /Y >nul 2>&1

echo.
echo 测试覆盖率报告生成完成！
echo 报告位置: coverage-reports/
pause
