#!/bin/bash

# 安装Hyperledger Fabric二进制文件脚本

echo "📥 开始安装Hyperledger Fabric工具..."

# 创建安装目录
mkdir -p ~/fabric-binaries
cd ~/fabric-binaries

# 下载Fabric 2.5版本工具
echo "⬇️ 下载Fabric 2.5二进制文件..."
curl -sSL https://github.com/hyperledger/fabric/releases/download/v2.5.0/hyperledger-fabric-windows-amd64-2.5.0.tar.gz -o fabric-2.5.0.tar.gz

# 下载Fabric CA 1.5版本工具
echo "⬇️ 下载Fabric CA 1.5二进制文件..."
curl -sSL https://github.com/hyperledger/fabric-ca/releases/download/v1.5.0/hyperledger-fabric-ca-windows-amd64-1.5.0.tar.gz -o fabric-ca-1.5.0.tar.gz

# 解压文件
echo "📦 解压二进制文件..."
tar -xzf fabric-2.5.0.tar.gz
tar -xzf fabric-ca-1.5.0.tar.gz

# 清理压缩包
rm fabric-2.5.0.tar.gz fabric-ca-1.5.0.tar.gz

# 添加到PATH环境变量
echo "🔧 配置环境变量..."
echo 'export PATH=$PATH:~/fabric-binaries/bin' >> ~/.bashrc
export PATH=$PATH:~/fabric-binaries/bin

echo "✅ Fabric工具安装完成!"
echo "📁 工具位置: ~/fabric-binaries/bin"
echo "🔧 请重新打开终端或运行: source ~/.bashrc"
