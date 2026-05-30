#!/usr/bin/env bash
# 一键链码部署脚本 (Bash版本)
# 适用于Docker环境正常的情况

set -e  # 遇到错误立即退出

echo "========================================="
echo "  Hyperledger Fabric 链码一键部署脚本  "
echo "========================================="

NETWORK_PATH="/fabric-network"
CHANNEL_NAME="imatu-channel"
CHAINCODE_NAME="integral_cc"
CHAINCODE_VERSION="1.0"
PACKAGE_NAME="${CHAINCODE_NAME}.tar.gz"
PACKAGE_ID=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker状态
check_docker() {
    log_info "检查Docker状态..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker未运行，请启动Docker Desktop"
        exit 1
    fi
    log_info "Docker运行正常"
}

# 检查网络容器
check_network() {
    log_info "检查Fabric网络容器..."
    local peer_count=$(docker ps --filter "name=peer0" --format "{{.Names}}" | wc -l)
    if [ $peer_count -lt 3 ]; then
        log_error "Peer节点数量不足，当前: $peer_count，需要: ≥3"
        exit 1
    fi
    log_info "检测到 $peer_count 个Peer节点"
}

# 创建链码包
create_package() {
    log_info "创建链码包..."

    # 清理旧包
    docker exec cli rm -f $PACKAGE_NAME 2>/dev/null || true

    # 创建新包
    docker exec cli peer lifecycle chaincode package $PACKAGE_NAME \
        --path /opt/gopath/src/github.com/chaincode \
        --lang golang \
        --label ${CHAINCODE_NAME}_${CHAINCODE_VERSION}

    # 验证包创建
    if docker exec cli ls $PACKAGE_NAME >/dev/null 2>&1; then
        log_info "链码包创建成功: $PACKAGE_NAME"
    else
        log_error "链码包创建失败"
        exit 1
    fi
}

# 安装链码到指定组织
install_chaincode_for_org() {
    local org_name=$1
    local msp_id=$2
    local peer_address=$3
    local tls_cert=$4
    local msp_path=$5

    log_info "安装链码到 $org_name 组织..."

    # 设置环境变量并安装
    docker exec cli bash -c "
        export CORE_PEER_TLS_ENABLED=true
        export CORE_PEER_LOCALMSPID=$msp_id
        export CORE_PEER_TLS_ROOTCERT_FILE=$tls_cert
        export CORE_PEER_MSPCONFIGPATH=$msp_path
        export CORE_PEER_ADDRESS=$peer_address

        peer lifecycle chaincode install $PACKAGE_NAME
    "

    if [ $? -eq 0 ]; then
        log_info "$org_name 链码安装成功"
    else
        log_error "$org_name 链码安装失败"
        exit 1
    fi
}

# 安装链码到所有组织
install_chaincode() {
    log_info "开始安装链码到所有Peer节点..."

    # 教育局组织
    install_chaincode_for_org \
        "Education Bureau" \
        "EducationBureauMSP" \
        "peer0.education.imatu.com:7051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"

    # 学校组织
    install_chaincode_for_org \
        "School" \
        "SchoolMSP" \
        "peer0.school.imatu.com:9051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"

    # 企业组织
    install_chaincode_for_org \
        "Enterprise" \
        "EnterpriseMSP" \
        "peer0.enterprise.imatu.com:11051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
}

# 获取Package ID
get_package_id() {
    log_info "获取Package ID..."

    local output=$(docker exec cli peer lifecycle chaincode queryinstalled)
    PACKAGE_ID=$(echo "$output" | grep -o 'Package ID: [^,]*' | cut -d' ' -f3)

    if [ -z "$PACKAGE_ID" ]; then
        log_error "无法获取Package ID"
        exit 1
    fi

    log_info "Package ID: $PACKAGE_ID"
}

# 批准链码定义
approve_chaincode_for_org() {
    local org_name=$1
    local msp_id=$2
    local peer_address=$3
    local tls_cert=$4
    local msp_path=$5

    log_info "批准 $org_name 组织链码定义..."

    docker exec cli bash -c "
        export CORE_PEER_TLS_ENABLED=true
        export CORE_PEER_LOCALMSPID=$msp_id
        export CORE_PEER_TLS_ROOTCERT_FILE=$tls_cert
        export CORE_PEER_MSPCONFIGPATH=$msp_path
        export CORE_PEER_ADDRESS=$peer_address

        peer lifecycle chaincode approveformyorg \
            --channelID $CHANNEL_NAME \
            --name $CHAINCODE_NAME \
            --version $CHAINCODE_VERSION \
            --package-id $PACKAGE_ID \
            --sequence 1 \
            --tls \
            --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    "

    if [ $? -eq 0 ]; then
        log_info "$org_name 链码批准成功"
    else
        log_error "$org_name 链码批准失败"
        exit 1
    fi
}

# 批准所有组织的链码定义
approve_chaincode() {
    log_info "开始批准链码定义..."

    # 教育局组织
    approve_chaincode_for_org \
        "Education Bureau" \
        "EducationBureauMSP" \
        "peer0.education.imatu.com:7051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"

    # 学校组织
    approve_chaincode_for_org \
        "School" \
        "SchoolMSP" \
        "peer0.school.imatu.com:9051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"

    # 企业组织
    approve_chaincode_for_org \
        "Enterprise" \
        "EnterpriseMSP" \
        "peer0.enterprise.imatu.com:11051" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt" \
        "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
}

# 验证提交准备状态
check_commit_readiness() {
    log_info "验证提交准备状态..."

    local output=$(docker exec cli peer lifecycle chaincode checkcommitreadiness \
        --channelID $CHANNEL_NAME \
        --name $CHAINCODE_NAME \
        --version $CHAINCODE_VERSION \
        --sequence 1 \
        --output json)

    echo "$output"

    # 检查是否所有组织都批准
    local approvals=$(echo "$output" | grep -o '"[^"]*": true' | wc -l)
    if [ $approvals -ge 2 ]; then
        log_info "提交准备就绪: $approvals/3 组织批准"
    else
        log_error "提交准备不足: $approvals/3 组织批准"
        exit 1
    fi
}

# 提交链码定义
commit_chaincode() {
    log_info "提交链码定义到通道..."

    docker exec cli peer lifecycle chaincode commit \
        --channelID $CHANNEL_NAME \
        --name $CHAINCODE_NAME \
        --version $CHAINCODE_VERSION \
        --sequence 1 \
        --tls \
        --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
        --peerAddresses peer0.education.imatu.com:7051 \
        --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt \
        --peerAddresses peer0.school.imatu.com:9051 \
        --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt \
        --peerAddresses peer0.enterprise.imatu.com:11051 \
        --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt

    if [ $? -eq 0 ]; then
        log_info "链码定义提交成功"
    else
        log_error "链码定义提交失败"
        exit 1
    fi
}

# 验证链码提交
verify_commit() {
    log_info "验证链码提交状态..."

    local output=$(docker exec cli peer lifecycle chaincode querycommitted \
        --channelID $CHANNEL_NAME \
        --name $CHAINCODE_NAME)

    echo "$output"
    log_info "链码提交验证完成"
}

# 初始化链码
initialize_chaincode() {
    log_info "初始化链码..."

    docker exec cli peer chaincode invoke \
        -o orderer.example.com:7050 \
        --tls \
        --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
        -C $CHANNEL_NAME \
        -n $CHAINCODE_NAME \
        -c '{"function":"InitLedger","Args":[]}'

    if [ $? -eq 0 ]; then
        log_info "链码初始化成功"
    else
        log_error "链码初始化失败"
        exit 1
    fi
}

# 测试链码功能
test_chaincode() {
    log_info "测试链码功能..."

    # 等待链码初始化完成
    sleep 3

    # 查询证书
    log_info "查询证书数据..."
    docker exec cli peer chaincode query \
        -C $CHANNEL_NAME \
        -n $CHAINCODE_NAME \
        -c '{"function":"GetAllCerts","Args":[]}'

    log_info "链码功能测试完成"
}

# 主执行流程
main() {
    echo "开始执行链码生命周期配置..."

    check_docker
    check_network
    create_package
    install_chaincode
    get_package_id
    approve_chaincode
    check_commit_readiness
    commit_chaincode
    verify_commit
    initialize_chaincode
    test_chaincode

    echo ""
    echo "========================================="
    echo "  链码生命周期配置完成!                 "
    echo "========================================="
    echo "链码名称: $CHAINCODE_NAME"
    echo "链码版本: $CHAINCODE_VERSION"
    echo "通道名称: $CHANNEL_NAME"
    echo "Package ID: $PACKAGE_ID"
    echo "========================================="
}

# 执行主函数
main "$@"
