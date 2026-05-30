# 技能认证区块链系统部署指南

## 系统架构概述

技能认证区块链系统采用混合部署架构，结合云端和本地组件：

```
云端组件 (AWS/Azure):
├── Fabric Orderer节点
├── Fabric CA节点  
└── 后端API服务

本地组件:
├── Fabric Peer节点
└── 数据库服务
```

## 部署前提条件

### 硬件要求

**云端服务器 (推荐):**
- CPU: 4核以上
- 内存: 16GB以上
- 存储: 100GB SSD以上
- 网络: 100Mbps带宽

**本地服务器 (推荐):**
- CPU: 8核以上
- 内存: 32GB以上
- 存储: 500GB SSD以上
- 网络: 千兆局域网

### 软件依赖

```bash
# 操作系统
Ubuntu 20.04 LTS 或 CentOS 8+

# 容器环境
Docker >= 20.10
Docker Compose >= 1.29

# 区块链组件
Hyperledger Fabric 2.5
Go >= 1.19

# 后端服务
Python >= 3.9
Node.js >= 16 (用于监控工具)
```

## 部署步骤

### 1. 环境准备

#### 云端服务器设置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装Go
wget https://go.dev/dl/go1.19.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.19.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
```

#### 本地服务器设置

```bash
# 类似云端服务器设置，但需要更大的资源配置
# 确保防火墙允许必要的端口通信
sudo ufw allow 7050:7053/tcp  # Fabric Peer端口
sudo ufw allow 9050:9053/tcp  # Fabric Peer备用端口
```

### 2. Fabric网络部署

#### 下载Fabric二进制文件

```bash
# 创建Fabric工作目录
mkdir -p ~/fabric-binaries
cd ~/fabric-binaries

# 下载Fabric工具
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.0

# 将工具添加到PATH
echo 'export PATH=$PATH:~/fabric-binaries/bin' >> ~/.bashrc
source ~/.bashrc
```

#### Windows环境安装

对于Windows环境，可以使用提供的PowerShell脚本：

```powershell
# 运行安装脚本
powershell -ExecutionPolicy Bypass -File install-fabric.ps1

# 或者使用Docker方式（推荐）
docker run --rm -v ${PWD}:/fabric hyperledger/fabric-tools:2.5 cryptogen generate --config=/fabric/crypto-config.yaml
```

#### 配置网络

```bash
# 复制项目中的配置文件
cp -r /path/to/project/blockchain/fabric-network ~/fabric-network
cd ~/fabric-network

# 生成加密材料
./start-network.sh

# Windows环境下可以使用演示脚本
powershell -ExecutionPolicy Bypass -File setup-demo-network.ps1
```
# 启动网络
docker-compose up -d
```

### 3. Chaincode部署

```bash
# 进入CLI容器
docker exec -it cli bash

# 安装Chaincode
peer lifecycle chaincode package skillcc.tar.gz --path /opt/gopath/src/github.com/chaincode/skill_certification --lang golang --label skillcc_1.0

# 安装到Peer节点
peer lifecycle chaincode install skillcc.tar.gz

# 批准Chaincode定义
peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --channelID mychannel --name skillcc --version 1.0 --package-id $PACKAGE_ID --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# 提交Chaincode
peer lifecycle chaincode commit -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --channelID mychannel --name skillcc --version 1.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

# 初始化Chaincode
peer chaincode invoke -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C mychannel -n skillcc --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt -c '{"function":"InitLedger","Args":[]}'

exit
```

### 4. 后端服务部署

#### 安装Python依赖

```bash
# 克隆项目代码
git clone <repository-url> /opt/skill-certification
cd /opt/skill-certification/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装区块链相关依赖
pip install hfc cryptography
```

#### 配置环境变量

```bash
# 创建环境配置文件
cat > .env << EOF
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/skill_cert
REDIS_URL=redis://localhost:6379

# 区块链配置
FABRIC_NETWORK_CONFIG=/opt/skill-certification/blockchain/config/network.json
CHANNEL_NAME=mychannel
CHAINCODE_NAME=skillcc

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
EOF
```

#### 启动服务

```bash
# 使用systemd管理服务
sudo tee /etc/systemd/system/skill-certification.service > /dev/null << EOF
[Unit]
Description=Skill Certification Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/skill-certification/backend
EnvironmentFile=/opt/skill-certification/backend/.env
ExecStart=/opt/skill-certification/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable skill-certification
sudo systemctl start skill-certification
```

### 5. 反向代理配置

```bash
# 安装Nginx
sudo apt install nginx -y

# 配置SSL证书 (使用Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 配置Nginx反向代理
sudo tee /etc/nginx/sites-available/skill-certification > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/skill-certification /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 监控和日志

#### 配置日志轮转

```bash
sudo tee /etc/logrotate.d/skill-certification > /dev/null << EOF
/opt/skill-certification/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data adm
}
EOF
```

#### 安装监控工具

```bash
# 安装Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
sudo cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

sudo tee /etc/systemd/system/node_exporter.service > /dev/null << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
```

## 网络安全配置

### 防火墙设置

```bash
# 云端服务器防火墙
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 7050  # Orderer端口
sudo ufw enable

# 本地服务器防火墙
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from <cloud-server-ip> to any port 7051  # Peer端口
sudo ufw allow from <cloud-server-ip> to any port 9051  # Peer备用端口
sudo ufw enable
```

### 安全加固

```bash
# 限制SSH访问
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 定期安全更新
echo "0 2 * * * apt update && apt upgrade -y" | sudo crontab -
```

## 备份和恢复

### 数据备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/skill-certification"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE

# 备份区块链数据
docker exec peer0.org1.example.com tar -czf - -C /var/hyperledger/production . > $BACKUP_DIR/$DATE/blockchain.tar.gz

# 备份数据库
pg_dump skill_cert > $BACKUP_DIR/$DATE/database.sql

# 备份配置文件
tar -czf $BACKUP_DIR/$DATE/config.tar.gz /opt/skill-certification/backend/.env /opt/skill-certification/blockchain/config/

# 清理旧备份（保留30天）
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### 恢复流程

```bash
# 停止服务
sudo systemctl stop skill-certification
docker-compose -f ~/fabric-network/docker-compose.yml down

# 恢复区块链数据
cd ~/fabric-network
tar -xzf /backup/skill-certification/latest/blockchain.tar.gz -C crypto-config/

# 恢复数据库
psql skill_cert < /backup/skill-certification/latest/database.sql

# 重启服务
docker-compose up -d
sudo systemctl start skill-certification
```

## 故障排除

### 常见问题

1. **Fabric网络无法启动**
   ```bash
   # 检查Docker状态
   docker ps -a
   
   # 查看容器日志
   docker logs orderer.example.com
   ```

2. **Chaincode调用失败**
   ```bash
   # 检查Chaincode是否正确安装
   peer lifecycle chaincode queryinstalled
   
   # 检查Chaincode定义
   peer lifecycle chaincode querycommitted -C mychannel
   ```

3. **API服务连接失败**
   ```bash
   # 检查服务状态
   sudo systemctl status skill-certification
   
   # 查看服务日志
   sudo journalctl -u skill-certification -f
   ```

### 性能调优

```bash
# 调整系统参数
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65535' >> /etc/sysctl.conf
sysctl -p

# 优化Docker
sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker
```

## 升级维护

### 版本升级流程

```bash
# 1. 备份当前系统
./backup.sh

# 2. 停止服务
sudo systemctl stop skill-certification
docker-compose -f ~/fabric-network/docker-compose.yml down

# 3. 更新代码
cd /opt/skill-certification
git pull origin main

# 4. 更新依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 5. 升级Chaincode（如果需要）
# 按照Chaincode部署步骤重新部署新版本

# 6. 重启服务
docker-compose up -d
sudo systemctl start skill-certification
```

## 监控指标

关键监控指标包括：

- **区块链性能**: 交易处理速度、区块生成时间
- **API服务**: 响应时间、错误率、吞吐量
- **系统资源**: CPU使用率、内存使用、磁盘IO
- **网络状态**: 连接数、带宽使用情况

建议使用Prometheus + Grafana建立完整的监控体系。

## 最新更新

### 三组织联盟配置 (2026-02-28)

项目已更新为支持教育局、学校、企业三方联盟的区块链基础设施：

- **组织数量**: 从2个增加到3个组织
- **通道名称**: imatu-channel (替代mychannel)
- **配置文件**: ThreeOrgsChannel (替代TwoOrgsChannel)
- **Peer节点**: 每个组织配置独立的Peer节点
- **CA服务**: 每个组织配置独立的CA服务

详细配置信息请参考: [BLOCKCHAIN_INFRASTRUCTURE_DEPLOYMENT_UPDATE.md](BLOCKCHAIN_INFRASTRUCTURE_DEPLOYMENT_UPDATE.md)

---

*本文档最后更新时间: 2026-02-28*
