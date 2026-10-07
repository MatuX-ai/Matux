'use client';

import { motion } from 'framer-motion';
import { Award, Shield, ExternalLink, Share2, Download } from 'lucide-react';
import { DeviceMode } from '../../types';

interface BlockchainCertPageProps {
  mode: DeviceMode;
}

export function BlockchainCertPage({ mode }: BlockchainCertPageProps) {
  const isPhone = mode === 'phone';

  if (isPhone) {
    return (
      <div className="px-5 space-y-5">
        {/* Cert Header */}
        <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-2xl p-5 text-white text-center">
          <Shield className="h-12 w-12 mx-auto mb-3 opacity-80" />
          <h3 className="text-lg font-bold mb-2">区块链技能证书</h3>
          <p className="text-sm text-purple-100 mb-3">基于 Hyperledger Fabric 的不可篡改认证</p>
          <div className="flex justify-center gap-2 text-xs">
            <span className="bg-white/20 px-3 py-1 rounded-full">已颁发 5 张</span>
            <span className="bg-white/20 px-3 py-1 rounded-full">链上验证</span>
          </div>
        </div>

        {/* Certificate List */}
        <h3 className="font-bold text-slate-900 text-base">我的证书</h3>
        <div className="space-y-3">
          {[
            { 
              name: 'Python 编程基础', 
              level: '初级', 
              date: '2026-05-10', 
              emoji: '🐍',
              txHash: '0x7f8a...3b2c',
              verified: true
            },
            { 
              name: 'Arduino 硬件开发', 
              level: '中级', 
              date: '2026-05-08', 
              emoji: '🔌',
              txHash: '0x4e9d...7a1f',
              verified: true
            },
            { 
              name: 'STEM 探索者 Lv.5', 
              level: '成就', 
              date: '2026-05-05', 
              emoji: '🏆',
              txHash: '0x2c5b...9e4d',
              verified: true
            },
            { 
              name: 'AR 实验室先锋', 
              level: '限定', 
              date: '2026-04-28', 
              emoji: '🥽',
              txHash: '0x1a8f...6c3e',
              verified: true,
              limited: true
            },
            { 
              name: '机器学习入门', 
              level: '高级', 
              date: '进行中', 
              emoji: '🤖',
              progress: 75,
              verified: false
            }
          ].map((cert, i) => (
            <motion.div
              key={i}
              whileTap={{ scale: 0.98 }}
              className={`bg-white rounded-xl border overflow-hidden cursor-pointer hover:shadow-md transition-shadow ${
                cert.limited ? 'border-purple-300 bg-purple-50' : ''
              }`}
            >
              <div className="p-4">
                <div className="flex items-start gap-3 mb-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl ${
                    cert.verified ? 'bg-gradient-to-br from-purple-100 to-indigo-100' : 'bg-slate-100'
                  }`}>
                    {cert.emoji}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-bold text-sm">{cert.name}</h4>
                      {cert.limited && (
                        <span className="text-[9px] bg-purple-500 text-white px-2 py-0.5 rounded-full">限定</span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 mb-1">{cert.level} · {cert.date}</p>
                    {cert.verified ? (
                      <div className="flex items-center gap-1 text-[10px] text-green-600">
                        <Shield className="h-3 w-3" />
                        <span>已验证 · {cert.txHash}</span>
                      </div>
                    ) : (
                      <div className="text-[10px] text-slate-500">
                        完成进度: {cert.progress}%
                      </div>
                    )}
                  </div>
                </div>
                
                {cert.verified && (
                  <div className="flex gap-2">
                    <button className="flex-1 bg-purple-100 text-purple-700 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1 hover:bg-purple-200 transition-colors">
                      <Share2 className="h-3 w-3" />
                      分享
                    </button>
                    <button className="flex-1 bg-indigo-100 text-indigo-700 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1 hover:bg-indigo-200 transition-colors">
                      <Download className="h-3 w-3" />
                      下载
                    </button>
                    <button className="flex-1 bg-slate-100 text-slate-700 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1 hover:bg-slate-200 transition-colors">
                      <ExternalLink className="h-3 w-3" />
                      验证
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* NFT Showcase */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3">NFT 勋章展示</h3>
          <div className="grid grid-cols-3 gap-2">
            {['🎯', '💻', '🔧', '👥', '💡', '🔥'].map((emoji, i) => (
              <motion.div
                key={i}
                whileTap={{ scale: 0.95 }}
                className="aspect-square bg-gradient-to-br from-purple-100 to-indigo-100 rounded-xl flex items-center justify-center text-3xl border-2 border-purple-200 cursor-pointer hover:border-purple-400 transition-colors"
              >
                {emoji}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 平板模式 - 更丰富的展示
  return (
    <div className="space-y-6">
      {/* Cert Overview */}
      <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <Shield className="h-16 w-16 opacity-80" />
              <div>
                <p className="text-purple-100 text-sm mb-1">区块链技能认证</p>
                <h2 className="text-3xl font-bold">5 张已获证书</h2>
              </div>
            </div>
            <div className="flex gap-4 text-sm">
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-purple-100 text-xs mb-1">链上交易</div>
                <div className="font-bold">5 笔</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-purple-100 text-xs mb-1">Gas 费用</div>
                <div className="font-bold">0.00 ETH</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-purple-100 text-xs mb-1">网络</div>
                <div className="font-bold">Hyperledger</div>
              </div>
            </div>
          </div>
          <Award className="h-32 w-32 opacity-20" />
        </div>
      </div>

      {/* Certificate Gallery */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-4">证书画廊</h3>
        <div className="grid grid-cols-3 gap-5">
          {[
            { 
              name: 'Python 编程基础', 
              level: '初级认证', 
              date: '2026-05-10', 
              emoji: '🐍',
              txHash: '0x7f8a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0',
              issuer: 'iMato 教育平台',
              skills: ['变量', '循环', '函数', '类']
            },
            { 
              name: 'Arduino 硬件开发', 
              level: '中级认证', 
              date: '2026-05-08', 
              emoji: '🔌',
              txHash: '0x4e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9',
              issuer: 'iMato 教育平台',
              skills: ['GPIO', 'PWM', '传感器', '通信协议']
            },
            { 
              name: 'STEM 探索者 Lv.5', 
              level: '成就徽章', 
              date: '2026-05-05', 
              emoji: '🏆',
              txHash: '0x2c5b8a9f0e1d4c7b6a3f2e5d8c1b0a9f6e3d2c5b8a1f0e9d6c3b2a5f8e1d4c7',
              issuer: 'iMato 社区',
              skills: ['跨学科', '实践能力', '创新思维']
            },
            { 
              name: 'AR 实验室先锋', 
              level: '限定勋章', 
              date: '2026-04-28', 
              emoji: '🥽',
              txHash: '0x1a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8',
              issuer: 'iMato AR Lab',
              skills: ['AR交互', '3D建模', '空间计算'],
              limited: true
            },
            { 
              name: '团队协作大师', 
              level: '社交认证', 
              date: '2026-04-20', 
              emoji: '👥',
              txHash: '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8',
              issuer: 'iMato 社区',
              skills: ['协作', '沟通', '领导力']
            },
            { 
              name: '机器学习入门', 
              level: '高级认证', 
              date: '进行中', 
              emoji: '🤖',
              progress: 75,
              issuer: 'iMato AI Lab',
              skills: ['监督学习', '神经网络', '模型训练'],
              inProgress: true
            }
          ].map((cert, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -4 }}
              className={`bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all cursor-pointer relative ${
                cert.limited ? 'ring-2 ring-purple-500' : ''
              }`}
            >
              {cert.limited && (
                <div className="absolute top-3 right-3 bg-purple-500 text-white text-[10px] px-2 py-1 rounded-full font-bold z-10">
                  LIMITED
                </div>
              )}
              {cert.inProgress && (
                <div className="absolute top-3 right-3 bg-slate-500 text-white text-[10px] px-2 py-1 rounded-full font-bold z-10">
                  进行中
                </div>
              )}
              
              <div className={`h-48 bg-gradient-to-br ${
                cert.limited ? 'from-purple-500 to-indigo-600' : 
                cert.inProgress ? 'from-slate-400 to-slate-500' :
                'from-purple-100 to-indigo-100'
              } flex items-center justify-center text-7xl relative`}>
                {cert.emoji}
                {!cert.inProgress && cert.txHash && (
                  <div className="absolute bottom-3 left-3 right-3 bg-white/90 backdrop-blur rounded-lg p-2">
                    <div className="text-[10px] text-slate-600 truncate">Tx: {cert.txHash.slice(0, 20)}...</div>
                  </div>
                )}
              </div>
              
              <div className="p-5">
                <h4 className="font-bold text-slate-900 mb-1">{cert.name}</h4>
                <p className="text-xs text-slate-500 mb-3">{cert.level} · {cert.date}</p>
                
                {!cert.inProgress ? (
                  <>
                    <div className="mb-3">
                      <p className="text-[10px] text-slate-500 mb-1">获得技能</p>
                      <div className="flex flex-wrap gap-1">
                        {cert.skills?.map((skill, j) => (
                          <span key={j} className="text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button className="flex-1 bg-purple-100 text-purple-700 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1 hover:bg-purple-200 transition-colors">
                        <Share2 className="h-3 w-3" />
                        分享
                      </button>
                      <button className="flex-1 bg-indigo-100 text-indigo-700 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1 hover:bg-indigo-200 transition-colors">
                        <ExternalLink className="h-3 w-3" />
                        验证
                      </button>
                    </div>
                  </>
                ) : (
                  <div>
                    <div className="mb-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600">完成进度</span>
                        <span className="font-semibold text-purple-600">{cert.progress}%</span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full" style={{ width: `${cert.progress}%` }}></div>
                      </div>
                    </div>
                    <button className="w-full bg-slate-100 text-slate-700 py-2 rounded-lg text-xs font-medium hover:bg-slate-200 transition-colors">
                      继续学习
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Blockchain Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
        <h4 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
          <Shield className="h-5 w-5" />
          区块链技术说明
        </h4>
        <div className="grid grid-cols-3 gap-4 text-sm text-blue-800">
          <div>
            <div className="font-semibold mb-1">不可篡改</div>
            <div className="text-xs opacity-80">基于 Hyperledger Fabric 企业级区块链，确保证书永久有效</div>
          </div>
          <div>
            <div className="font-semibold mb-1">全球验证</div>
            <div className="text-xs opacity-80">任何人可通过交易哈希在链上验证书真伪</div>
          </div>
          <div>
            <div className="font-semibold mb-1">NFT化</div>
            <div className="text-xs opacity-80">每张证书都是独特的NFT，可展示、可交易、可收藏</div>
          </div>
        </div>
      </div>
    </div>
  );
}
