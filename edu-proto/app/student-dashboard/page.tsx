'use client';

import { motion } from 'framer-motion';
import { Cpu, MessageSquare, Box, User, Zap, Battery, Wifi, Play, Code, Camera, Globe, Award } from 'lucide-react';
import { useState } from 'react';

export default function StudentMobileDemo() {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center py-12 px-4">
      <div className="text-center mb-8 absolute top-8 left-0 w-full">
        <h1 className="text-3xl font-bold text-primary">MatuX 移动端体验</h1>
        <p className="text-gray-500 mt-2">随时随地探索 STEM 世界</p>
      </div>

      {/* Phone Frame */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative w-[360px] h-[720px] bg-black rounded-[3rem] shadow-2xl border-[8px] border-slate-800 overflow-hidden"
      >
        {/* Notch / Dynamic Island */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-20 flex items-center justify-center space-x-2">
          <div className="w-16 h-4 bg-slate-900 rounded-full"></div>
        </div>

        {/* Screen Content */}
        <div className="w-full h-full bg-slate-50 overflow-y-auto no-scrollbar pb-20 relative">
          {/* Status Bar */}
          <div className="h-10 w-full flex justify-between items-center px-6 pt-2 text-xs font-medium text-slate-900">
            <span>9:41</span>
            <div className="flex items-center space-x-1">
              <Wifi className="h-3 w-3" />
              <Battery className="h-3 w-3" />
            </div>
          </div>

          {/* App Header */}
          <div className="px-5 py-4 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-primary">Hi, 李明 👋</h2>
              <p className="text-xs text-gray-500">准备好开始今天的实验了吗？</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
              <User className="h-5 w-5 text-accent" />
            </div>
          </div>

          {/* Main Content Area - Dynamic Switching */}
          <div className="px-5 space-y-6">
            {activeTab === 'home' && (
              <>
                {/* Hardware Status Card */}
                <div className="bg-slate-900 rounded-2xl p-4 text-white shadow-lg">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-2">
                      <Cpu className="h-5 w-5 text-accent" />
                      <span className="font-bold text-sm">ESP32 开发板</span>
                    </div>
                    <span className="text-[10px] bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">在线</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-white/10 rounded-lg p-2 flex items-center space-x-2">
                      <Battery className="h-3 w-3 text-green-400" /> <span>85%</span>
                    </div>
                    <div className="bg-white/10 rounded-lg p-2 flex items-center space-x-2">
                      <Wifi className="h-3 w-3 text-blue-400" /> <span>-42dBm</span>
                    </div>
                  </div>
                </div>

                {/* AI Recommendation */}
                <div>
                  <h3 className="font-bold text-primary text-sm mb-3">AI 推荐项目</h3>
                  <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-4 text-white shadow-md relative overflow-hidden">
                    <Zap className="absolute -right-2 -bottom-2 h-20 w-20 text-white/10" />
                    <h4 className="font-bold text-base mb-1">智能感应小夜灯</h4>
                    <p className="text-[10px] text-indigo-100 mb-3 line-clamp-2">利用光敏电阻实现环境光自适应控制。</p>
                    <button className="bg-white text-indigo-600 text-xs font-bold px-4 py-2 rounded-full flex items-center">
                      <Play className="h-3 w-3 mr-1 fill-current" /> 开始实验
                    </button>
                  </div>
                </div>

                {/* Quick Actions Grid */}
                <div>
                  <h3 className="font-bold text-primary text-sm mb-3">常用工具</h3>
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { icon: Code, label: '代码', color: 'bg-blue-100 text-blue-600' },
                      { icon: Box, label: '3D模型', color: 'bg-orange-100 text-orange-600' },
                      { icon: Camera, label: 'AR扫描', color: 'bg-green-100 text-green-600' },
                      { icon: MessageSquare, label: 'AI助手', color: 'bg-purple-100 text-purple-600' }
                    ].map((item, i) => (
                      <div key={i} className="flex flex-col items-center space-y-2">
                        <div className={`w-12 h-12 rounded-xl ${item.color} flex items-center justify-center shadow-sm`}>
                          <item.icon className="h-6 w-6" />
                        </div>
                        <span className="text-[10px] font-medium text-gray-600">{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {activeTab === 'learn' && (
              <div className="space-y-5">
                {/* Daily Challenge */}
                <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-4 text-white shadow-md">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-sm flex items-center"><Zap className="h-4 w-4 mr-1"/> 每日挑战</h3>
                    <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full">剩余 2h</span>
                  </div>
                  <p className="text-xs text-orange-50 mb-3">使用 PWM 信号控制舵机转动到指定角度。</p>
                  <button className="w-full bg-white text-orange-600 text-xs font-bold py-2 rounded-lg">接受挑战</button>
                </div>

                <h3 className="font-bold text-primary text-sm">我的课程表</h3>
                {[{ name: 'Arduino 基础语法', p: 100 }, { name: '传感器数据采集', p: 75 }, { name: '无线通信协议 (BLE)', p: 65 }, { name: 'Python 硬件编程', p: 30 }].map((course, i) => (
                  <div key={i} className="bg-white p-3 rounded-xl border shadow-sm flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-lg">
                      {i % 2 === 0 ? '🤖' : '📡'}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-bold">{course.name}</span>
                        <span className="text-accent">{course.p}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-1.5">
                        <div className="bg-accent h-1.5 rounded-full" style={{ width: `${course.p}%` }}></div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Knowledge Graph Entry */}
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-indigo-900 text-xs">STEM 知识图谱</h4>
                    <p className="text-[10px] text-indigo-600 mt-1">探索电子、机械与编程的联系</p>
                  </div>
                  <div className="w-8 h-8 bg-indigo-200 rounded-full flex items-center justify-center text-indigo-700">
                    <Globe className="h-4 w-4" />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'community' && (
              <div className="space-y-4">
                {/* Topic Tabs */}
                <div className="flex space-x-2 overflow-x-auto no-scrollbar pb-1">
                  {['全部', '开源硬件', '3D打印', '机器人', 'AI应用'].map((tag, i) => (
                    <span key={i} className={`text-[10px] px-3 py-1.5 rounded-full whitespace-nowrap ${i === 0 ? 'bg-primary text-white' : 'bg-white border text-gray-600'}`}>
                      {tag}
                    </span>
                  ))}
                </div>

                <h3 className="font-bold text-primary text-sm">创客广场</h3>
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="bg-white rounded-xl border shadow-sm overflow-hidden">
                    <div className="h-28 bg-slate-200 flex items-center justify-center text-gray-400 text-xs relative">
                      [项目作品展示图]
                      <div className="absolute top-2 right-2 bg-black/50 text-white text-[9px] px-2 py-0.5 rounded-full flex items-center">
                        <User className="h-2 w-2 mr-1" /> 王同学
                      </div>
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-xs mb-1">基于 ESP32 的自动浇花系统</h4>
                      <p className="text-[10px] text-gray-500 mb-2 line-clamp-2">通过土壤湿度传感器实时监测，当数值低于阈值时自动开启水泵...</p>
                      <div className="flex justify-between items-center">
                        <div className="flex space-x-2">
                          <span className="text-[9px] bg-slate-100 px-2 py-0.5 rounded text-gray-600">#物联网</span>
                          <span className="text-[9px] bg-slate-100 px-2 py-0.5 rounded text-gray-600">#自动化</span>
                        </div>
                        <div className="flex items-center space-x-1 text-gray-400">
                          <Award className="h-3 w-3" /> <span className="text-[9px]">128</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="space-y-6 text-center pt-4">
                <div className="flex flex-col items-center">
                  <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mb-2">
                    <User className="h-10 w-10 text-accent" />
                  </div>
                  <h3 className="font-bold text-primary">李明</h3>
                  <p className="text-[10px] text-gray-500">STEM 探索者 Lv.5</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">12</div>
                    <div className="text-[9px] text-gray-500">完成项目</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">850</div>
                    <div className="text-[9px] text-gray-500">获得积分</div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border">
                    <div className="font-bold text-accent">5</div>
                    <div className="text-[9px] text-gray-500">数字勋章</div>
                  </div>
                </div>
                <div className="bg-white rounded-xl border text-left overflow-hidden">
                  {['我的硬件设备', '区块链证书', '学习报告', '系统设置'].map((item, i) => (
                    <div key={i} className="p-3 border-b last:border-0 flex justify-between items-center text-xs hover:bg-slate-50 cursor-pointer">
                      <span>{item}</span>
                      <span className="text-gray-400">&gt;</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Navigation Bar */}
        <div className="absolute bottom-0 w-full h-16 bg-white border-t flex justify-around items-center px-2 pb-2">
          {['home', 'learn', 'community', 'profile'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex flex-col items-center space-y-1 ${activeTab === tab ? 'text-accent' : 'text-gray-400'}`}
            >
              {tab === 'home' && <Box className="h-5 w-5" />}
              {tab === 'learn' && <Code className="h-5 w-5" />}
              {tab === 'community' && <MessageSquare className="h-5 w-5" />}
              {tab === 'profile' && <User className="h-5 w-5" />}
              <span className="text-[9px] font-medium capitalize">{tab}</span>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
