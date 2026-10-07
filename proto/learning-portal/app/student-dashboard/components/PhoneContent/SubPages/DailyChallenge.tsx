'use client';

import { motion } from 'framer-motion';
import { Zap, Clock, Award } from 'lucide-react';

interface DailyChallengeProps {
  onNavigate: (page: string) => void;
}

export default function DailyChallenge({ onNavigate }: DailyChallengeProps) {
  return (
    <div className="space-y-6">
      {/* Challenge Header */}
      <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-6 text-white text-center">
        <Zap className="h-16 w-16 mx-auto mb-3 animate-pulse" />
        <h2 className="text-xl font-bold mb-2">每日挑战</h2>
        <p className="text-sm opacity-90 mb-4">使用 PWM 信号控制舵机转动到指定角度</p>
        <div className="flex items-center justify-center gap-2 text-xs bg-white/20 inline-block px-3 py-1 rounded-full">
          <Clock className="h-3 w-3" /> 剩余时间: 2小时 15分
        </div>
      </div>

      {/* Rewards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-center">
          <Award className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
          <div className="text-lg font-bold text-yellow-700">+50</div>
          <div className="text-[10px] text-yellow-600">积分奖励</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 text-center">
          <Zap className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <div className="text-lg font-bold text-purple-700">限定</div>
          <div className="text-[10px] text-purple-600">专属徽章</div>
        </div>
      </div>

      {/* Requirements */}
      <div className="bg-white rounded-xl p-4 border">
        <h3 className="font-bold text-sm mb-3">挑战要求</h3>
        <ul className="text-xs text-slate-600 space-y-2">
          <li className="flex items-start gap-2">
            <span className="text-blue-500">1.</span>
            <span>编写程序实现舵机 0° 到 180° 的平滑转动</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500">2.</span>
            <span>通过串口监控输出当前角度值</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500">3.</span>
            <span>录制一段 10 秒的运行视频</span>
          </li>
        </ul>
      </div>

      {/* Action */}
      <motion.button
        whileTap={{ scale: 0.98 }}
        onClick={() => onNavigate('代码编辑器')}
        className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-orange-200"
      >
        <Zap className="h-5 w-5" /> 立即接受挑战
      </motion.button>
    </div>
  );
}
