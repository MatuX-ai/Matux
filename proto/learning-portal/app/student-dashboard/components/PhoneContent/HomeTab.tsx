'use client';

import { motion } from 'framer-motion';
import { Cpu, Battery, Wifi, Zap, Box, Code, Camera, MessageSquare, Play, User, Award, Globe } from 'lucide-react';
import { PhoneTab, PhoneSubPage } from '../../types';

interface HomeTabProps {
  onNavigate: (page: PhoneSubPage) => void;
}

export function HomeTab({ onNavigate }: HomeTabProps) {
  return (
    <>
      {/* Hardware Status Card */}
      <motion.div
        whileHover={{ y: -2 }}
        className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-5 text-white shadow-xl"
      >
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="h-5 w-5 text-blue-500" />
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
      </motion.div>

      {/* AI Recommendation */}
      <div>
        <h3 className="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
          <span className="w-1 h-5 bg-gradient-to-b from-blue-600 to-purple-600 rounded-full"></span>
          AI 推荐项目
        </h3>
        <motion.div
          whileTap={{ scale: 0.98 }}
          onClick={() => onNavigate('项目详情')}
          className="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-5 text-white shadow-xl relative overflow-hidden cursor-pointer group"
        >
          <Zap className="absolute -right-2 -bottom-2 h-20 w-20 text-white/10" />
          <h4 className="font-bold text-base mb-1">智能感应小夜灯</h4>
          <p className="text-[10px] text-indigo-100 mb-3 line-clamp-2">利用光敏电阻实现环境光自适应控制。</p>
          <button className="bg-white/95 backdrop-blur text-indigo-600 text-xs font-bold px-5 py-2.5 rounded-full flex items-center gap-1.5 hover:bg-white hover:shadow-lg transition-all group-hover:scale-105">
            <Play className="h-3.5 w-3.5 fill-current" /> 开始实验
          </button>
        </motion.div>
      </div>

      {/* Quick Actions Grid */}
      <div>
        <h3 className="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
          <span className="w-1 h-5 bg-gradient-to-b from-blue-600 to-purple-600 rounded-full"></span>
          常用工具
        </h3>
        <div className="grid grid-cols-4 gap-4">
          {[
            { icon: Code, label: '代码', color: 'text-blue-600', bg: 'from-blue-50 to-blue-100' },
            { icon: Box, label: '3D模型', color: 'text-orange-600', bg: 'from-orange-50 to-orange-100' },
            { icon: Camera, label: 'AR扫描', color: 'text-green-600', bg: 'from-green-50 to-green-100' },
            { icon: MessageSquare, label: 'AI助手', color: 'text-purple-600', bg: 'from-purple-50 to-purple-100' }
          ].map((item, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.08, y: -4 }}
              whileTap={{ scale: 0.95 }}
              className="flex flex-col items-center gap-2.5 cursor-pointer"
            >
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${item.bg} flex items-center justify-center shadow-md hover:shadow-xl transition-all`}>
                <item.icon className={`h-7 w-7 ${item.color}`} />
              </div>
              <span className="text-[11px] font-semibold text-slate-700">{item.label}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </>
  );
}
