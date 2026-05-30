#!/bin/bash

# Hyperledger Fabric网络启动脚本

echo "🔧 开始设置Hyperledger Fabric网络..."

# 设置环境变量
export FABRIC_VERSION=2.5
export CA_VERSION=1.5
export FABRIC_CA_HOME=${PWD}/fabric-ca-server

# 创建必要的目录
mkdir -p channel-artifacts crypto-config

# 生成加密材料
echo "🔐 生成加密材料..."
cryptogen generate --config=./crypto-config.yaml
if [ "$?" -ne 0 ]; then
  echo "❌ 加密材料生成失败"
  exit 1
fi

# 生成创世区块
echo "🏗️ 生成创世区块..."
configtxgen -profile ThreeOrgsOrdererGenesis -channelID byfn-sys-channel -outputBlock ./channel-artifacts/genesis.block
if [ "$?" -ne 0 ]; then
  echo "❌ 创世区块生成失败"
  exit 1
fi

# 生成通道配置交易
echo "🔗 生成通道配置交易..."
configtxgen -profile ThreeOrgsChannel -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID imatu-channel
if [ "$?" -ne 0 ]; then
  echo "❌ 通道配置交易生成失败"
  exit 1
fi

# 生成锚节点更新交易
echo "⚓ 生成锚节点更新交易..."
configtxgen -profile ThreeOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/EducationBureauMSPanchors.tx -channelID imatu-channel -asOrg EducationBureauMSP
configtxgen -profile ThreeOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/SchoolMSPanchors.tx -channelID imatu-channel -asOrg SchoolMSP
configtxgen -profile ThreeOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/EnterpriseMSPanchors.tx -channelID imatu-channel -asOrg EnterpriseMSP

echo "✅ 网络配置文件生成完成!"

# 启动Docker容器
echo "🐳 启动Fabric网络容器..."
docker-compose up -d

if [ "$?" -ne 0 ]; then
  echo "❌ Docker容器启动失败"
  exit 1
fi

echo "✅ Fabric网络启动成功!"
echo "📊 网络状态:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
