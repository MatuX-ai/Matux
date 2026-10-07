'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Monitor, Smartphone, ArrowRight, Sparkles, LogIn } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 flex items-center justify-center p-4 overflow-hidden relative">
      {/* Background Blobs */}
      <div className="absolute top-0 -left-20 w-72 h-72 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
      <div className="absolute top-0 -right-20 w-72 h-72 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-20 left-1/2 w-72 h-72 bg-indigo-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

      {/* 右上角登录入口 */}
      <Link
        href="/login"
        className="absolute top-6 right-6 z-20 flex items-center gap-2 bg-white/10 backdrop-blur border border-white/20 text-white text-sm font-medium px-4 py-2 rounded-full hover:bg-white/20 transition-all"
      >
        <LogIn className="h-4 w-4" />
        登录
      </Link>

      <div className="relative z-10 max-w-5xl w-full">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur px-4 py-2 rounded-full text-white/80 text-sm mb-6 border border-white/20">
            <Sparkles className="h-4 w-4" />
            <span>MatuX 学习端原型设计</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent mb-4">
            STEM 学习平台
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            融合 AI、AR、硬件编程的下一代 STEM 教育体验 · 选择适合你的设备开始探索
          </p>
        </motion.div>

        {/* Version Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Web Version */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Link href="/web">
              <div className="group relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all cursor-pointer h-full overflow-hidden">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl group-hover:bg-blue-500/30 transition-all"></div>
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-6 shadow-lg">
                    <Monitor className="h-8 w-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Web 版</h2>
                  <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                    桌面端全屏体验，顶部导航栏，宽屏布局展示更多课程内容、AR 实验室与数据看板。
                  </p>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['顶部导航栏', '宽屏布局', '多面板看板', 'AR 实验室', '区块链证书'].map((tag) => (
                      <span key={tag} className="text-xs bg-white/5 text-slate-300 px-3 py-1 rounded-full border border-white/10">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-blue-400 font-semibold group-hover:gap-3 transition-all">
                    进入 Web 版
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>

          {/* Mobile Version */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Link href="/mobile">
              <div className="group relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 hover:bg-white/10 transition-all cursor-pointer h-full overflow-hidden">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl group-hover:bg-purple-500/30 transition-all"></div>
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mb-6 shadow-lg">
                    <Smartphone className="h-8 w-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">移动版</h2>
                  <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                    手机端原生体验，底部标签栏导航，硬件连接与传感器监控随时随地掌控。
                  </p>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {['底部标签栏', '硬件连接', '传感器监控', '语音指令', '每日挑战'].map((tag) => (
                      <span key={tag} className="text-xs bg-white/5 text-slate-300 px-3 py-1 rounded-full border border-white/10">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-purple-400 font-semibold group-hover:gap-3 transition-all">
                    进入移动版
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-12 text-slate-500 text-sm"
        >
          MatuX Lab · 学习端原型设计 · 共享同一套数据与组件
        </motion.div>
      </div>
    </div>
  );
}
