# 链码生命周期配置文档

## 任务概述
配置链码生命周期，包括安装、批准和提交链码定义。

## 环境要求
- Docker Desktop 已安装并正常运行
- Fabric 2.5 环境已配置
- 三个组织网络已启动 (EducationBureau, School, Enterprise)

## 链码信息
- 链码名称: integral_cc
- 版本: 1.0
- 通道: imatu-channel
- 链码类型: Go语言智能合约

## 配置步骤

### 1. 创建链码包
```bash
# 在链码目录下打包
peer lifecycle chaincode package integral_cc.tar.gz --path ../chaincode --lang golang --label integral_cc_1.0
```

### 2. 安装链码到各Peer节点

#### 教育局组织 (Education Bureau)
```bash
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=EducationBureauMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.education.imatu.com:7051

peer lifecycle chaincode install integral_cc.tar.gz
```

#### 学校组织 (School)
```bash
export CORE_PEER_LOCALMSPID=SchoolMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.school.imatu.com:9051

peer lifecycle chaincode install integral_cc.tar.gz
```

#### 企业组织 (Enterprise)
```bash
export CORE_PEER_LOCALMSPID=EnterpriseMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.enterprise.imatu.com:11051

peer lifecycle chaincode install integral_cc.tar.gz
```

### 3. 批准链码定义

获取Package ID:
```bash
peer lifecycle chaincode queryinstalled
```

#### 各组织批准链码定义

教育局组织:
```bash
peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

学校组织:
```bash
peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

企业组织:
```bash
peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### 4. 验证提交准备状态
```bash
peer lifecycle chaincode checkcommitreadiness \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --sequence 1 \
  --output json
```

### 5. 提交链码定义到通道
```bash
peer lifecycle chaincode commit \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses peer0.education.imatu.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt \
  --peerAddresses peer0.school.imatu.com:9051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt \
  --peerAddresses peer0.enterprise.imatu.com:11051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
```

### 6. 验证链码已提交
```bash
peer lifecycle chaincode querycommitted --channelID imatu-channel --name integral_cc
```

### 7. 调用链码初始化
```bash
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C imatu-channel \
  -n integral_cc \
  -c '{"function":"InitLedger","Args":[]}'
```

## 验证步骤

### 查询证书
```bash
peer chaincode query -C imatu-channel -n integral_cc -c '{"function":"GetAllCerts","Args":[]}'
```

### 颁发新证书
```bash
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C imatu-channel \
  -n integral_cc \
  -c '{"function":"IssueCert","Args":["{\"id\":\"cert002\",\"holderDid\":\"did:example:user002\",\"issuerDid\":\"did:example:org002\",\"skillName\":\"人工智能\",\"skillLevel\":\"高级\"}"]}'
```

## 注意事项

1. 确保所有Peer节点都在运行且网络连通
2. TLS证书路径必须正确
3. Package ID需要从安装输出中获取
4. 所有组织必须批准相同的链码定义才能提交
5. 序列号(sequence)必须递增，首次为1

## 故障排除

常见错误及解决方案:
- "could not connect to any of the peers" - 检查Peer节点是否运行
- "endorsement failure" - 检查链码是否在足够多的Peer上安装和批准
- "proposal response was not successful" - 检查链码逻辑和参数格式
