#!/bin/bash

# 简化版Fabric网络部署脚本
# 适用于演示和测试环境

echo "🔧 开始部署简化的Fabric网络..."

# 创建必要的目录结构
mkdir -p channel-artifacts crypto-config

# 创建创世区块（模拟）
echo "🏗️ 创建模拟创世区块..."
cat > channel-artifacts/genesis.block << EOF
{
  "data": {
    "data": [
      {
        "payload": {
          "header": {
            "channel_header": {
              "type": 1,
              "version": 1,
              "timestamp": "2026-02-28T12:00:00Z",
              "channel_id": "byfn-sys-channel",
              "epoch": "0"
            }
          },
          "data": {
            "config": {
              "channel_group": {
                "groups": {
                  "Orderer": {
                    "groups": {
                      "OrdererOrg": {
                        "values": {
                          "MSP": {
                            "value": {
                              "config": {
                                "name": "OrdererMSP"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    ]
  }
}
EOF

# 创建通道配置交易（模拟）
echo "🔗 创建模拟通道配置交易..."
cat > channel-artifacts/channel.tx << EOF
{
  "payload": {
    "header": {
      "channel_header": {
        "type": 2,
        "version": 1,
        "timestamp": "2026-02-28T12:00:00Z",
        "channel_id": "imatu-channel",
        "epoch": "0"
      }
    },
    "data": {
      "config_update": {
        "channel_id": "imatu-channel",
        "read_set": {},
        "write_set": {
          "groups": {
            "Application": {
              "groups": {
                "EducationBureauMSP": {},
                "SchoolMSP": {},
                "EnterpriseMSP": {}
              }
            }
          }
        }
      }
    }
  }
}
EOF

# 创建锚节点更新交易（模拟）
echo "⚓ 创建模拟锚节点更新交易..."
for org in EducationBureauMSP SchoolMSP EnterpriseMSP; do
  cat > channel-artifacts/${org}anchors.tx << EOF
{
  "payload": {
    "header": {
      "channel_header": {
        "type": 3,
        "version": 1,
        "timestamp": "2026-02-28T12:00:00Z",
        "channel_id": "imatu-channel",
        "epoch": "0"
      }
    },
    "data": {
      "config_update": {
        "channel_id": "imatu-channel",
        "read_set": {
          "groups": {
            "Application": {
              "groups": {
                "${org}": {}
              }
            }
          }
        },
        "write_set": {
          "groups": {
            "Application": {
              "groups": {
                "${org}": {
                  "values": {
                    "AnchorPeers": {
                      "value": {
                        "anchor_peers": [
                          {
                            "host": "peer0.${org,,}.imatu.com",
                            "port": 7051
                          }
                        ]
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
EOF
done

echo "✅ 模拟配置文件生成完成!"

# 显示生成的文件
echo "📋 生成的文件列表:"
ls -la channel-artifacts/
ls -la crypto-config/

echo "🚀 可以继续执行下一步部署操作"
