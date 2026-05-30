# 简化版Fabric网络部署脚本 (PowerShell版本)
# 适用于Windows环境和演示测试

Write-Host "🔧 开始部署简化的Fabric网络..." -ForegroundColor Green

# 创建必要的目录结构
Write-Host "📁 创建必要目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "channel-artifacts" -Force
New-Item -ItemType Directory -Path "crypto-config" -Force

# 创建创世区块（模拟）
Write-Host "🏗️ 创建模拟创世区块..." -ForegroundColor Yellow
$genesisBlock = @{
    data = @{
        data = @(
            @{
                payload = @{
                    header = @{
                        channel_header = @{
                            type = 1
                            version = 1
                            timestamp = "2026-02-28T12:00:00Z"
                            channel_id = "byfn-sys-channel"
                            epoch = "0"
                        }
                    }
                    data = @{
                        config = @{
                            channel_group = @{
                                groups = @{
                                    Orderer = @{
                                        groups = @{
                                            OrdererOrg = @{
                                                values = @{
                                                    MSP = @{
                                                        value = @{
                                                            config = @{
                                                                name = "OrdererMSP"
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
        )
    }
} | ConvertTo-Json -Depth 10

$genesisBlock | Out-File -FilePath "channel-artifacts/genesis.block" -Encoding UTF8

# 创建通道配置交易（模拟）
Write-Host "🔗 创建模拟通道配置交易..." -ForegroundColor Yellow
$channelTx = @{
    payload = @{
        header = @{
            channel_header = @{
                type = 2
                version = 1
                timestamp = "2026-02-28T12:00:00Z"
                channel_id = "imatu-channel"
                epoch = "0"
            }
        }
        data = @{
            config_update = @{
                channel_id = "imatu-channel"
                read_set = @{}
                write_set = @{
                    groups = @{
                        Application = @{
                            groups = @{
                                EducationBureauMSP = @{}
                                SchoolMSP = @{}
                                EnterpriseMSP = @{}
                            }
                        }
                    }
                }
            }
        }
    }
} | ConvertTo-Json -Depth 10

$channelTx | Out-File -FilePath "channel-artifacts/channel.tx" -Encoding UTF8

# 创建锚节点更新交易（模拟）
Write-Host "⚓ 创建模拟锚节点更新交易..." -ForegroundColor Yellow
$organizations = @("EducationBureauMSP", "SchoolMSP", "EnterpriseMSP")

foreach ($org in $organizations) {
    $anchorTx = @{
        payload = @{
            header = @{
                channel_header = @{
                    type = 3
                    version = 1
                    timestamp = "2026-02-28T12:00:00Z"
                    channel_id = "imatu-channel"
                    epoch = "0"
                }
            }
            data = @{
                config_update = @{
                    channel_id = "imatu-channel"
                    read_set = @{
                        groups = @{
                            Application = @{
                                groups = @{
                                    $org = @{}
                                }
                            }
                        }
                    }
                    write_set = @{
                        groups = @{
                            Application = @{
                                groups = @{
                                    $org = @{
                                        values = @{
                                            AnchorPeers = @{
                                                value = @{
                                                    anchor_peers = @(
                                                        @{
                                                            host = "peer0.$($org.ToLower()).imatu.com"
                                                            port = 7051
                                                        }
                                                    )
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
    } | ConvertTo-Json -Depth 10

    $filename = "channel-artifacts/$org anchors.tx"
    $anchorTx | Out-File -FilePath $filename -Encoding UTF8
    Write-Host "  创建文件: $filename" -ForegroundColor Cyan
}

Write-Host "✅ 模拟配置文件生成完成!" -ForegroundColor Green

# 显示生成的文件
Write-Host "📋 生成的文件列表:" -ForegroundColor Yellow
Get-ChildItem "channel-artifacts/" | Format-Table Name, Length, LastWriteTime
Get-ChildItem "crypto-config/" | Format-Table Name, Length, LastWriteTime

Write-Host "🚀 可以继续执行下一步部署操作" -ForegroundColor Green
