# 积分智能合约部署PowerShell脚本

Write-Host "🚀 开始部署积分智能合约..." -ForegroundColor Green

# 配置变量
$CHAINCODE_NAME = "integral"
$CHAINCODE_VERSION = "1.0"
$CHANNEL_NAME = "imatu-channel"
$PACKAGE_NAME = "${CHAINCODE_NAME}_cc.tar.gz"

# 进入链码目录
Set-Location $PSScriptRoot

# 检查Go环境
if (!(Get-Command go -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 未找到Go环境，请先安装Go 1.19+" -ForegroundColor Red
    exit 1
}

Write-Host "🔧 编译链码..." -ForegroundColor Yellow
$env:GOOS = "linux"
$env:GOARCH = "amd64"
go build -o integral-chaincode

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 链码编译失败" -ForegroundColor Red
    exit 1
}

Write-Host "📦 创建链码包..." -ForegroundColor Yellow
docker exec cli peer lifecycle chaincode package $PACKAGE_NAME --path /opt/gopath/src/github.com/chaincode/integral --lang golang --label ${CHAINCODE_NAME}_${CHAINCODE_VERSION}

Write-Host "📤 安装链码到各组织..." -ForegroundColor Yellow

# 教育局组织
$env:CORE_PEER_LOCALMSPID = "EducationBureauMSP"
$env:CORE_PEER_TLS_ROOTCERT_FILE = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt"
$env:CORE_PEER_MSPCONFIGPATH = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"
$env:CORE_PEER_ADDRESS = "peer0.education.imatu.com:7051"

docker exec cli peer lifecycle chaincode install $PACKAGE_NAME

# 学校组织
$env:CORE_PEER_LOCALMSPID = "SchoolMSP"
$env:CORE_PEER_TLS_ROOTCERT_FILE = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt"
$env:CORE_PEER_MSPCONFIGPATH = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"
$env:CORE_PEER_ADDRESS = "peer0.school.imatu.com:9051"

docker exec cli peer lifecycle chaincode install $PACKAGE_NAME

# 企业组织
$env:CORE_PEER_LOCALMSPID = "EnterpriseMSP"
$env:CORE_PEER_TLS_ROOTCERT_FILE = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt"
$env:CORE_PEER_MSPCONFIGPATH = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
$env:CORE_PEER_ADDRESS = "peer0.enterprise.imatu.com:11051"

docker exec cli peer lifecycle chaincode install $PACKAGE_NAME

Write-Host "🔍 查询Package ID..." -ForegroundColor Yellow
docker exec cli peer lifecycle chaincode queryinstalled

Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host "请使用以下命令批准链码定义：" -ForegroundColor Cyan
Write-Host "docker exec cli peer lifecycle chaincode approveformyorg --channelID $CHANNEL_NAME --name $CHAINCODE_NAME --version $CHAINCODE_VERSION --package-id PACKAGE_ID --sequence 1" -ForegroundColor White