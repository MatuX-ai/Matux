@echo off
echo ========================================
echo Go单元测试执行脚本
echo ========================================

cd /d "G:\iMato\blockchain\chaincode\integral"

echo 当前目录: %cd%
echo Go版本: 
G:\Go\bin\go version

echo 正在下载依赖...
G:\Go\bin\go mod tidy

echo 正在安装测试依赖...
G:\Go\bin\go get github.com/stretchr/testify/assert
G:\Go\bin\go get github.com/stretchr/testify/mock

echo 正在运行核心测试...
G:\Go\bin\go test -v issue_integral_unit_test.go integral_chaincode.go models.go permission_test.go

echo 测试完成！
pause