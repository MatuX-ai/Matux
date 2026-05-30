# 链码生命周期手动执行指南

## 前提条件检查

### 1. 验证Docker环境
```bash
# 检查Docker是否正常运行
docker info

# 检查Docker Compose
docker-compose --version

# 检查网络容器状态
docker ps
```

### 2. 启动Fabric网络（如果尚未启动）
```bash
cd g:\iMato\blockchain\fabric-network

# 启动网络
docker-compose up -d

# 验证容器启动
docker ps | grep peer
docker ps | grep orderer
docker ps | grep cli
```

## 链码生命周期执行步骤

### 步骤1: 创建链码包
```bash
# 进入CLI容器创建链码包
docker exec cli peer lifecycle chaincode package integral_cc.tar.gz --path /opt/gopath/src/github.com/chaincode --lang golang --label integral_cc_1.0

# 验证包创建成功
docker exec cli ls -la integral_cc.tar.gz
```

### 步骤2: 安装链码到各Peer节点

#### 教育局组织 (Education Bureau)
```bash
# 设置环境变量
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=EducationBureauMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.education.imatu.com:7051

# 安装链码
docker exec cli peer lifecycle chaincode install integral_cc.tar.gz
```

#### 学校组织 (School)
```bash
# 设置环境变量
export CORE_PEER_LOCALMSPID=SchoolMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.school.imatu.com:9051

# 安装链码
docker exec cli peer lifecycle chaincode install integral_cc.tar.gz
```

#### 企业组织 (Enterprise)
```bash
# 设置环境变量
export CORE_PEER_LOCALMSPID=EnterpriseMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.enterprise.imatu.com:11051

# 安装链码
docker exec cli peer lifecycle chaincode install integral_cc.tar.gz
```

### 步骤3: 查询Package ID
```bash
# 查询已安装的链码
docker exec cli peer lifecycle chaincode queryinstalled

# 记录输出中的Package ID，格式类似: integral_cc_1.0:abcd1234...
```

### 步骤4: 各组织批准链码定义

假设Package ID为 `integral_cc_1.0:abcd1234ef567890`

#### 教育局组织批准
```bash
# 使用步骤2中的环境变量设置
export PACKAGE_ID=integral_cc_1.0:abcd1234ef567890

docker exec cli peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

#### 学校组织批准
```bash
# 切换到学校组织环境变量
export CORE_PEER_LOCALMSPID=SchoolMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.school.imatu.com:9051

docker exec cli peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

#### 企业组织批准
```bash
# 切换到企业组织环境变量
export CORE_PEER_LOCALMSPID=EnterpriseMSP
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp
export CORE_PEER_ADDRESS=peer0.enterprise.imatu.com:11051

docker exec cli peer lifecycle chaincode approveformyorg \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

### 步骤5: 验证提交准备状态
```bash
docker exec cli peer lifecycle chaincode checkcommitreadiness \
  --channelID imatu-channel \
  --name integral_cc \
  --version 1.0 \
  --sequence 1 \
  --output json
```

预期输出应该显示所有组织都已批准:
```json
{
    "approvals": {
        "EducationBureauMSP": true,
        "SchoolMSP": true,
        "EnterpriseMSP": true
    }
}
```

### 步骤6: 提交链码定义到通道
```bash
docker exec cli peer lifecycle chaincode commit \
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

### 步骤7: 验证链码已提交
```bash
docker exec cli peer lifecycle chaincode querycommitted --channelID imatu-channel --name integral_cc
```

### 步骤8: 初始化链码
```bash
docker exec cli peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C imatu-channel \
  -n integral_cc \
  -c '{"function":"InitLedger","Args":[]}'
```

### 步骤9: 测试链码功能

#### 查询所有证书
```bash
docker exec cli peer chaincode query -C imatu-channel -n integral_cc -c '{"function":"GetAllCerts","Args":[]}'
```

#### 颁发新证书
```bash
docker exec cli peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C imatu-channel \
  -n integral_cc \
  -c '{"function":"IssueCert","Args":["{\"id\":\"cert002\",\"holderDid\":\"did:example:user002\",\"issuerDid\":\"did:example:org002\",\"skillName\":\"人工智能\",\"skillLevel\":\"高级\"}"]}'
```

## 验证和故障排除

### 常见问题排查

1. **Peer节点连接失败**
   ```bash
   # 检查Peer容器状态
   docker ps | grep peer
   
   # 查看容器日志
   docker logs peer0.education.imatu.com
   ```

2. **TLS证书问题**
   ```bash
   # 验证证书路径
   docker exec cli ls -la /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/
   ```

3. **链码安装失败**
   ```bash
   # 检查链码包
   docker exec cli ls -la integral_cc.tar.gz
   
   # 重新创建链码包
   docker exec cli peer lifecycle chaincode package integral_cc.tar.gz --path /opt/gopath/src/github.com/chaincode --lang golang --label integral_cc_1.0
   ```

### 状态检查命令

```bash
# 检查通道状态
docker exec cli peer channel list

# 检查链码安装状态
docker exec cli peer lifecycle chaincode queryinstalled

# 检查链码定义提交状态
docker exec cli peer lifecycle chaincode querycommitted --channelID imatu-channel
```

## 成功验证标准

✅ 所有Peer节点正常运行
✅ 链码成功安装到所有Peer节点
✅ 所有组织成功批准链码定义
✅ `checkcommitreadiness` 显示所有组织批准
✅ 链码成功提交到通道
✅ 链码初始化成功
✅ 可以正常调用链码功能
