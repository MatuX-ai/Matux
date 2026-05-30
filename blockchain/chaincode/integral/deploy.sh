#!/bin/bash

# 积分智能合约部署脚本

set -e

echo "🚀 开始部署积分智能合约..."

# 配置变量
CHAINCODE_NAME="integral"
CHAINCODE_VERSION="1.0"
CHANNEL_NAME="imatu-channel"
PACKAGE_NAME="${CHAINCODE_NAME}_cc.tar.gz"

# 进入链码目录
cd "$(dirname "$0")"

echo "🔧 编译链码..."
GOOS=linux GOARCH=amd64 go build -o integral-chaincode

echo "📦 创建链码包..."
peer lifecycle chaincode package ${PACKAGE_NAME} \
  --path . \
  --lang golang \
  --label ${CHAINCODE_NAME}_${CHAINCODE_VERSION}

echo "📤 安装链码到各组织..."

# 教育局组织
export CORE_PEER_LOCALMSPID=EducationBureauMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.education.imatu.com:7051

peer lifecycle chaincode install ${PACKAGE_NAME}

# 学校组织
export CORE_PEER_LOCALMSPID=SchoolMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.school.imatu.com:9051

peer lifecycle chaincode install ${PACKAGE_NAME}

# 企业组织
export CORE_PEER_LOCALMSPID=EnterpriseMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.enterprise.imatu.com:11051

peer lifecycle chaincode install ${PACKAGE_NAME}

echo "🔍 查询Package ID..."
peer lifecycle chaincode queryinstalled

echo "✅ 部署完成！请使用以下命令批准链码定义："
echo "peer lifecycle chaincode approveformyorg --channelID ${CHANNEL_NAME} --name ${CHAINCODE_NAME} --version ${CHAINCODE_VERSION} --package-id PACKAGE_ID --sequence 1"