'use client';

import { motion } from 'framer-motion';
import { Zap, Globe } from 'lucide-react';
import { DeviceMode } from '../../types';

interface LearnPageProps {
  mode: DeviceMode;
  onNavigate?: (page: string) => void;
}

export function LearnPage({ mode, onNavigate }: LearnPageProps) {
  const isPhone = mode === 'phone';

  // 手机模式
  if (isPhone) {
    return (
      <div className="px-5 space-y-5">
        {/* Daily Challenge */}
        <motion.div
          whileTap={{ scale: 0.98 }}
          onClick={() => onNavigate?.('每日挑战')}
          className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-4 text-white shadow-md cursor-pointer"
        >
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-bold text-sm flex items-center"><Zap className="h-4 w-4 mr-1"/> 每日挑战</h3>
            <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full">剩余 2h</span>
          </div>
          <p className="text-xs text-orange-50 mb-3">使用 PWM 信号控制舵机转动到指定角度。</p>
          <button className="w-full bg-white text-orange-600 text-xs font-bold py-2 rounded-lg">接受挑战</button>
        </motion.div>

        <h3 className="font-bold text-blue-600 text-sm">我的课程表</h3>
        {[
          { name: 'Arduino 基础语法', p: 100, emoji: '🤖' },
          { name: '传感器数据采集', p: 75, emoji: '📡' },
          { name: '无线通信协议 (BLE)', p: 65, emoji: '📶' },
          { name: 'Python 硬件编程', p: 30, emoji: '🐍' }
        ].map((course, i) => (
          <motion.div
            key={i}
            whileTap={{ scale: 0.98 }}
            onClick={() => onNavigate?.('课程详情')}
            className="bg-white p-3 rounded-xl border shadow-sm flex items-center space-x-3 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-lg">
              {course.emoji}
            </div>
            <div className="flex-1">
              <div className="flex justify-between text-xs mb-1">
                <span className="font-bold">{course.name}</span>
                <span className="text-blue-600">{course.p}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5">
                <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${course.p}%` }}></div>
              </div>
            </div>
          </motion.div>
        ))}

        {/* Knowledge Graph Entry */}
        <motion.div
          whileTap={{ scale: 0.98 }}
          onClick={() => onNavigate?.('知识图谱')}
          className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between cursor-pointer"
        >
          <div>
            <h4 className="font-bold text-indigo-900 text-xs">STEM 知识图谱</h4>
            <p className="text-[10px] text-indigo-600 mt-1">探索电子、机械与编程的联系</p>
          </div>
          <div className="w-8 h-8 bg-indigo-200 rounded-full flex items-center justify-center text-indigo-700">
            <Globe className="h-4 w-4" />
          </div>
        </motion.div>
      </div>
    );
  }

  // 平板模式 - 课程列表页面
  return (
    <div className="space-y-6">
      {/* Daily Challenge Banner */}
      <motion.div
        whileHover={{ y: -2 }}
        onClick={() => onNavigate?.('每日挑战')}
        className="bg-gradient-to-r from-orange-500 to-red-500 rounded-2xl p-6 text-white cursor-pointer hover:shadow-xl transition-all"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-6 w-6" />
              <h3 className="text-xl font-bold">每日挑战</h3>
            </div>
            <p className="text-orange-100 mb-3">使用 PWM 信号控制舵机转动到指定角度</p>
            <div className="flex gap-3 text-sm">
              <span className="bg-white/20 px-3 py-1 rounded-full">剩余 2小时</span>
              <span className="bg-white/20 px-3 py-1 rounded-full">奖励 +50积分</span>
            </div>
          </div>
          <button className="bg-white text-orange-600 px-6 py-3 rounded-xl font-bold hover:shadow-lg transition-all">
            接受挑战
          </button>
        </div>
      </motion.div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-slate-900">我的课程 📚</h2>
      </div>
      <div className="grid grid-cols-2 gap-5">
        {[
          { title: 'Python 编程基础', progress: 75, total: 20, completed: 15, emoji: '🐍', color: 'from-blue-500 to-blue-600' },
          { title: 'Arduino 硬件开发', progress: 100, total: 15, completed: 15, emoji: '🔌', color: 'from-green-500 to-green-600' },
          { title: '机器学习入门', progress: 30, total: 25, completed: 8, emoji: '🤖', color: 'from-purple-500 to-purple-600' },
          { title: '3D 建模与设计', progress: 50, total: 18, completed: 9, emoji: '🎨', color: 'from-pink-500 to-pink-600' },
          { title: '物联网应用开发', progress: 10, total: 22, completed: 2, emoji: '📡', color: 'from-indigo-500 to-indigo-600' },
          { title: '机器人控制原理', progress: 0, total: 20, completed: 0, emoji: '⚙️', color: 'from-orange-500 to-orange-600' }
        ].map((course, i) => (
          <motion.div
            key={i}
            whileHover={{ y: -4 }}
            onClick={() => onNavigate?.('课程详情')}
            className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all cursor-pointer"
          >
            <div className={`h-32 bg-gradient-to-br ${course.color} flex items-center justify-center text-5xl`}>
              {course.emoji}
            </div>
            <div className="p-5">
              <h4 className="font-bold text-slate-900 mb-2">{course.title}</h4>
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600">进度</span>
                  <span className="font-semibold text-blue-600">{course.progress}%</span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full" style={{ width: `${course.progress}%` }}></div>
                </div>
              </div>
              <p className="text-xs text-slate-500 mb-3">已完成 {course.completed}/{course.total} 课时</p>
              <button className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-2 rounded-xl font-semibold text-sm hover:shadow-lg transition-all">
                {course.progress === 100 ? '复习课程' : '继续学习'}
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Knowledge Graph Entry */}
      <motion.div
        whileHover={{ y: -2 }}
        onClick={() => onNavigate?.('知识图谱')}
        className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-6 flex items-center justify-between cursor-pointer hover:shadow-lg transition-all"
      >
        <div>
          <h4 className="font-bold text-indigo-900 text-lg flex items-center gap-2">
            <Globe className="h-5 w-5" /> STEM 知识图谱
          </h4>
          <p className="text-sm text-indigo-600 mt-1">探索电子、机械与编程的联系，构建你的知识网络</p>
        </div>
        <div className="w-12 h-12 bg-indigo-200 rounded-full flex items-center justify-center text-indigo-700">
          <Globe className="h-6 w-6" />
        </div>
      </motion.div>
    </div>
  );
}
