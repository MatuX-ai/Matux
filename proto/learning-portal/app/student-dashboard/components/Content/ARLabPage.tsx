'use client';

import { motion } from 'framer-motion';
import { Camera, Box, Zap } from 'lucide-react';
import { DeviceMode } from '../../types';

interface ARLabPageProps {
  mode: DeviceMode;
}

export function ARLabPage({ mode }: ARLabPageProps) {
  const isPhone = mode === 'phone';

  if (isPhone) {
    return (
      <div className="px-5 space-y-4">
        {/* AR Header */}
        <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-2xl p-6 text-white text-center">
          <Camera className="h-16 w-16 mx-auto mb-3 opacity-80" />
          <h3 className="text-xl font-bold mb-2">AR 实验环境</h3>
          <p className="text-sm text-purple-100 mb-4">通过增强现实技术，在真实环境中进行虚拟实验</p>
          <button className="bg-white text-purple-600 px-6 py-2.5 rounded-xl font-bold text-sm hover:shadow-lg transition-all">
            启动 AR 相机
          </button>
        </div>

        {/* AR Experiments */}
        <h3 className="font-bold text-slate-900 text-base">AR 实验项目</h3>
        <div className="space-y-3">
          {[
            { 
              title: '电路仿真实验', 
              desc: '虚拟搭建电路并测试', 
              emoji: '⚡', 
              users: 234,
              color: 'from-yellow-500 to-orange-500'
            },
            { 
              title: '机械结构组装', 
              desc: '3D 模型拆解与组装', 
              emoji: '🔧', 
              users: 189,
              color: 'from-blue-500 to-cyan-500'
            },
            { 
              title: '化学反应模拟', 
              desc: '安全的化学实验体验', 
              emoji: '🧪', 
              users: 156,
              color: 'from-green-500 to-emerald-500'
            }
          ].map((lab, i) => (
            <motion.div
              key={i}
              whileTap={{ scale: 0.98 }}
              className="bg-white rounded-xl border overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className={`h-24 bg-gradient-to-br ${lab.color} flex items-center justify-center text-4xl`}>
                {lab.emoji}
              </div>
              <div className="p-3">
                <h4 className="font-bold text-sm mb-1">{lab.title}</h4>
                <p className="text-[10px] text-slate-500 mb-2">{lab.desc}</p>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-purple-600 font-medium">{lab.users} 人正在实验</span>
                  <button className="text-[10px] bg-purple-100 text-purple-700 px-2 py-1 rounded-full font-medium">
                    开始实验
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 3D Model Library Preview */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3">3D 元件库</h3>
          <div className="grid grid-cols-3 gap-2">
            {['电阻', '电容', 'LED', 'Arduino', '传感器', '电机'].map((item, i) => (
              <motion.div
                key={i}
                whileTap={{ scale: 0.95 }}
                className="bg-slate-50 rounded-lg p-2 text-center border cursor-pointer hover:bg-slate-100 transition-colors"
              >
                <Box className="h-6 w-6 mx-auto mb-1 text-slate-600" />
                <span className="text-[10px] text-slate-700">{item}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Feature Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h4 className="font-bold text-sm text-blue-900 mb-2 flex items-center gap-2">
            <Zap className="h-4 w-4" />
            AR 实验特色
          </h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>✓ 真实的物理引擎模拟</li>
            <li>✓ 256+ 3D电子元件模型</li>
            <li>✓ 实时电路仿真验证</li>
            <li>✓ 安全无风险的实验环境</li>
          </ul>
        </div>
      </div>
    );
  }

  // 平板模式 - 更丰富的展示
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">AR 实验室 🥽</h2>
      </div>
      
      {/* AR Main Banner */}
      <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Camera className="h-20 w-20 mb-4 opacity-80" />
            <h3 className="text-2xl font-bold mb-3">增强现实实验平台</h3>
            <p className="text-purple-100 mb-6 text-lg">
              将虚拟实验带入真实世界，通过手势交互完成电路组装、机械结构拆解等复杂操作
            </p>
            <div className="flex gap-4">
              <button className="bg-white text-purple-600 px-8 py-3 rounded-xl font-bold hover:shadow-lg transition-all">
                启动 AR 相机
              </button>
              <button className="bg-white/20 backdrop-blur text-white px-8 py-3 rounded-xl font-bold hover:bg-white/30 transition-all">
                查看教程
              </button>
            </div>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold mb-2">256+</div>
            <div className="text-purple-200">3D元件模型</div>
          </div>
        </div>
      </div>

      {/* AR Experiments Grid */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-4">热门 AR 实验</h3>
        <div className="grid grid-cols-3 gap-5">
          {[
            { 
              title: '电路仿真实验', 
              desc: '虚拟搭建电路并测试，支持实时仿真验证', 
              emoji: '⚡', 
              users: 234,
              difficulty: '初级',
              duration: '15分钟',
              color: 'from-yellow-500 to-orange-500'
            },
            { 
              title: '机械结构组装', 
              desc: '3D 模型拆解与组装，学习机械原理', 
              emoji: '🔧', 
              users: 189,
              difficulty: '中级',
              duration: '30分钟',
              color: 'from-blue-500 to-cyan-500'
            },
            { 
              title: '化学反应模拟', 
              desc: '安全的化学实验体验，观察反应过程', 
              emoji: '🧪', 
              users: 156,
              difficulty: '高级',
              duration: '20分钟',
              color: 'from-green-500 to-emerald-500'
            }
          ].map((lab, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -4 }}
              className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all cursor-pointer"
            >
              <div className={`h-40 bg-gradient-to-br ${lab.color} flex items-center justify-center text-6xl`}>
                {lab.emoji}
              </div>
              <div className="p-5">
                <h4 className="font-bold text-slate-900 mb-2">{lab.title}</h4>
                <p className="text-sm text-slate-600 mb-3 line-clamp-2">{lab.desc}</p>
                <div className="flex gap-3 text-xs text-slate-500 mb-4">
                  <span>{lab.difficulty}</span>
                  <span>·</span>
                  <span>{lab.duration}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-purple-600 font-medium">{lab.users} 人正在实验</span>
                  <button className="bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:shadow-lg transition-all">
                    开始实验
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* 3D Model Library */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-4">3D 元件库预览</h3>
        <div className="grid grid-cols-6 gap-4">
          {['电阻', '电容', 'LED', 'Arduino', '传感器', '电机', '电池', '开关', '导线', '芯片', '继电器', '变压器'].map((item, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05 }}
              className="bg-white rounded-xl p-4 text-center border shadow-sm cursor-pointer hover:shadow-md transition-all"
            >
              <Box className="h-8 w-8 mx-auto mb-2 text-slate-600" />
              <span className="text-xs text-slate-700 font-medium">{item}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { icon: '🎯', title: '精准吸附', desc: '2cm精度自动对齐' },
          { icon: '⚡', title: '实时仿真', desc: '50ms快速响应' },
          { icon: '🛡️', title: '安全防护', desc: '零风险实验环境' },
          { icon: '🏆', title: '游戏激励', desc: '组装成功+10积分' }
        ].map((feature, i) => (
          <div key={i} className="bg-white rounded-xl p-4 border text-center">
            <div className="text-3xl mb-2">{feature.icon}</div>
            <h4 className="font-bold text-sm text-slate-900 mb-1">{feature.title}</h4>
            <p className="text-xs text-slate-600">{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
