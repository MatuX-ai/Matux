#!/usr/bin/env pwsh

# 链码生命周期配置自动化脚本
# 适用于Windows PowerShell环境

param(
    [string]$NetworkPath = "g:\iMato\blockchain\fabric-network",
    [string]$ChaincodePath = "g:\iMato\blockchain\chaincode",
    [string]$ChannelName = "imatu-channel",
    [string]$ChaincodeName = "integral_cc",
    [string]$ChaincodeVersion = "1.0"
)

Write-Host "=== 链码生命周期配置自动化脚本 ===" -ForegroundColor Green
Write-Host "网络路径: $NetworkPath" -ForegroundColor Yellow
Write-Host "链码路径: $ChaincodePath" -ForegroundColor Yellow
Write-Host "通道名称: $ChannelName" -ForegroundColor Yellow
Write-Host "链码名称: $ChaincodeName" -ForegroundColor Yellow
Write-Host "链码版本: $ChaincodeVersion" -ForegroundColor Yellow

# 检查Docker状态
function Test-DockerStatus {
    Write-Host "检查Docker状态..." -ForegroundColor Cyan
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Docker正在运行" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Docker未运行，请启动Docker Desktop" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ 无法连接到Docker" -ForegroundColor Red
        return $false
    }
}

# 检查网络容器状态
function Test-NetworkStatus {
    Write-Host "检查Fabric网络状态..." -ForegroundColor Cyan
    $containers = docker ps --filter "name=peer0" --format "{{.Names}}"
    if ($containers.Count -ge 3) {
        Write-Host "✓ 检测到 $($containers.Count) 个Peer节点" -ForegroundColor Green
        return $true
    } else {
        Write-Host "✗ Peer节点数量不足，当前: $($containers.Count)" -ForegroundColor Red
        return $false
    }
}

# 进入网络目录
Set-Location $NetworkPath

# 检查环境
if (-not (Test-DockerStatus)) {
    Write-Host "请先启动Docker Desktop并确保其正常运行" -ForegroundColor Red
    exit 1
}

if (-not (Test-NetworkStatus)) {
    Write-Host "请先启动Fabric网络: docker-compose up -d" -ForegroundColor Red
    exit 1
}

# 步骤1: 创建链码包
Write-Host "`n=== 步骤1: 创建链码包 ===" -ForegroundColor Blue
try {
    $packageName = "${ChaincodeName}.tar.gz"
    if (Test-Path $packageName) {
        Remove-Item $packageName -Force
        Write-Host "删除旧的链码包" -ForegroundColor Yellow
    }

    # 使用CLI容器创建链码包
    docker exec cli peer lifecycle chaincode package $packageName --path /opt/gopath/src/github.com/chaincode --lang golang --label ${ChaincodeName}_${ChaincodeVersion}
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 链码包创建成功: $packageName" -ForegroundColor Green
    } else {
        throw "链码包创建失败"
    }
} catch {
    Write-Host "✗ 步骤1失败: $_" -ForegroundColor Red
    exit 1
}

# 步骤2: 安装链码到各Peer节点
Write-Host "`n=== 步骤2: 安装链码到Peer节点 ===" -ForegroundColor Blue

$organizations = @(
    @{
        Name = "Education Bureau"
        MSPID = "EducationBureauMSP"
        PeerAddress = "peer0.education.imatu.com:7051"
        TLSCert = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt"
        MSPPath = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"
    },
    @{
        Name = "School"
        MSPID = "SchoolMSP"
        PeerAddress = "peer0.school.imatu.com:9051"
        TLSCert = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt"
        MSPPath = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"
    },
    @{
        Name = "Enterprise"
        MSPID = "EnterpriseMSP"
        PeerAddress = "peer0.enterprise.imatu.com:11051"
        TLSCert = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt"
        MSPPath = "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
    }
)

$packageIds = @{}

foreach ($org in $organizations) {
    Write-Host "安装链码到 $($org.Name) 组织..." -ForegroundColor Cyan

    $envVars = @{
        "CORE_PEER_TLS_ENABLED" = "true"
        "CORE_PEER_LOCALMSPID" = $org.MSPID
        "CORE_PEER_TLS_ROOTCERT_FILE" = $org.TLSCert
        "CORE_PEER_MSPCONFIGPATH" = $org.MSPPath
        "CORE_PEER_ADDRESS" = $org.PeerAddress
    }

    # 设置环境变量
    foreach ($kv in $envVars.GetEnumerator()) {
        $env:$($kv.Key) = $kv.Value
    }

    # 安装链码
    docker exec cli peer lifecycle chaincode install $packageName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $($org.Name) 链码安装成功" -ForegroundColor Green
    } else {
        Write-Host "✗ $($org.Name) 链码安装失败" -ForegroundColor Red
    }

    # 清理环境变量
    foreach ($key in $envVars.Keys) {
        Remove-Item "env:$key" -ErrorAction SilentlyContinue
    }
}

# 步骤3: 获取Package ID并批准链码定义
Write-Host "`n=== 步骤3: 批准链码定义 ===" -ForegroundColor Blue

# 查询已安装的链码获取Package ID
Write-Host "查询Package ID..." -ForegroundColor Cyan
$installedOutput = docker exec cli peer lifecycle chaincode queryinstalled
$packageIdMatch = [regex]::Match($installedOutput, 'Package ID: ([^,]+)')
if ($packageIdMatch.Success) {
    $packageId = $packageIdMatch.Groups[1].Value.Trim()
    Write-Host "找到Package ID: $packageId" -ForegroundColor Green
} else {
    Write-Host "✗ 无法获取Package ID" -ForegroundColor Red
    exit 1
}

# 各组织批准链码定义
foreach ($org in $organizations) {
    Write-Host "批准 $($org.Name) 组织链码定义..." -ForegroundColor Cyan

    $envVars = @{
        "CORE_PEER_TLS_ENABLED" = "true"
        "CORE_PEER_LOCALMSPID" = $org.MSPID
        "CORE_PEER_TLS_ROOTCERT_FILE" = $org.TLSCert
        "CORE_PEER_MSPCONFIGPATH" = $org.MSPPath
        "CORE_PEER_ADDRESS" = $org.PeerAddress
    }

    foreach ($kv in $envVars.GetEnumerator()) {
        $env:$($kv.Key) = $kv.Value
    }

    $approveCmd = "peer lifecycle chaincode approveformyorg --channelID $ChannelName --name $ChaincodeName --version $ChaincodeVersion --package-id $packageId --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

    docker exec cli $approveCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $($org.Name) 链码批准成功" -ForegroundColor Green
    } else {
        Write-Host "✗ $($org.Name) 链码批准失败" -ForegroundColor Red
    }

    foreach ($key in $envVars.Keys) {
        Remove-Item "env:$key" -ErrorAction SilentlyContinue
    }
}

# 步骤4: 验证提交准备状态
Write-Host "`n=== 步骤4: 验证提交准备状态 ===" -ForegroundColor Blue
$checkCmd = "peer lifecycle chaincode checkcommitreadiness --channelID $ChannelName --name $ChaincodeName --version $ChaincodeVersion --sequence 1 --output json"
$readinessOutput = docker exec cli $checkCmd
Write-Host "提交准备状态检查结果:" -ForegroundColor Cyan
Write-Host $readinessOutput

# 步骤5: 提交链码定义到通道
Write-Host "`n=== 步骤5: 提交链码定义到通道 ===" -ForegroundColor Blue

$commitCmd = @"
peer lifecycle chaincode commit \
  --channelID $ChannelName \
  --name $ChaincodeName \
  --version $ChaincodeVersion \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses peer0.education.imatu.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt \
  --peerAddresses peer0.school.imatu.com:9051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt \
  --peerAddresses peer0.enterprise.imatu.com:11051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
"@

docker exec cli $commitCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 链码定义提交成功" -ForegroundColor Green
} else {
    Write-Host "✗ 链码定义提交失败" -ForegroundColor Red
}

# 步骤6: 验证链码已提交
Write-Host "`n=== 步骤6: 验证链码提交状态 ===" -ForegroundColor Blue
$queryCmd = "peer lifecycle chaincode querycommitted --channelID $ChannelName --name $ChaincodeName"
$committedOutput = docker exec cli $queryCmd
Write-Host "链码提交状态:" -ForegroundColor Cyan
Write-Host $committedOutput

# 步骤7: 初始化链码
Write-Host "`n=== 步骤7: 初始化链码 ===" -ForegroundColor Blue
$initCmd = "peer chaincode invoke -o orderer.example.com:7050 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C $ChannelName -n $ChaincodeName -c '{`"function`":`"InitLedger`",`"Args`":[]}'"
docker exec cli $initCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 链码初始化成功" -ForegroundColor Green
} else {
    Write-Host "✗ 链码初始化失败" -ForegroundColor Red
}

Write-Host "`n=== 链码生命周期配置完成 ===" -ForegroundColor Green
Write-Host "链码名称: $ChaincodeName" -ForegroundColor Yellow
Write-Host "链码版本: $ChaincodeVersion" -ForegroundColor Yellow
Write-Host "通道名称: $ChannelName" -ForegroundColor Yellow
Write-Host "Package ID: $packageId" -ForegroundColor Yellow
