'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Eye, EyeOff, Sparkles } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // 原型：模拟登录后跳转设备选择页
    setTimeout(() => router.push('/'), 600);
  };

  const handleOAuth = (provider: string) => {
    setLoading(true);
    setTimeout(() => router.push('/'), 600);
  };

  const oauthProviders = [
    { id: 'qq', label: 'QQ', emoji: '🐧', color: 'hover:border-blue-400 hover:bg-blue-50' },
    { id: 'wechat', label: '微信', emoji: '💬', color: 'hover:border-green-400 hover:bg-green-50' },
    { id: 'google', label: 'Google', emoji: 'G', color: 'hover:border-red-400 hover:bg-red-50' },
    { id: 'github', label: 'GitHub', emoji: '🐙', color: 'hover:border-slate-700 hover:bg-slate-100' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 flex items-center justify-center p-4 overflow-hidden relative">
      {/* 背景动态光斑 */}
      <div className="absolute top-0 -left-20 w-72 h-72 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
      <div className="absolute top-0 -right-20 w-72 h-72 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-20 left-1/2 w-72 h-72 bg-indigo-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo + 标语 */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl shadow-purple-500/30 mb-4"
          >
            <span className="text-3xl">🧊</span>
          </motion.div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
            MatuX
          </h1>
          <p className="text-sm text-slate-400 mt-1.5 flex items-center justify-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            AI 驱动的 STEM 教育新纪元
          </p>
        </div>

        {/* 登录卡片 */}
        <motion.form
          onSubmit={handleLogin}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/95 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/20"
        >
          {/* 邮箱 */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">邮箱地址</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@matux.com"
                required
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all"
              />
            </div>
          </div>

          {/* 密码 */}
          <div className="mb-5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">密码</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full pl-11 pr-11 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* 记住我 + 忘记密码 */}
          <div className="flex items-center justify-between mb-6">
            <button
              type="button"
              onClick={() => setRemember(!remember)}
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              <span
                className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
                  remember ? 'bg-blue-500 border-blue-500' : 'border-slate-300 bg-white'
                }`}
              >
                {remember && (
                  <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={4}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </span>
              记住我
            </button>
            <Link href="#" className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors">
              忘记密码？
            </Link>
          </div>

          {/* 登录按钮 */}
          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3.5 rounded-xl font-semibold text-sm shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-purple-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-70"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                登录
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </motion.button>

          {/* 分隔线 */}
          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-slate-200"></div>
            <span className="text-xs text-slate-400">或使用第三方登录</span>
            <div className="flex-1 h-px bg-slate-200"></div>
          </div>

          {/* 第三方登录 */}
          <div className="grid grid-cols-4 gap-3">
            {oauthProviders.map((p) => (
              <motion.button
                key={p.id}
                type="button"
                onClick={() => handleOAuth(p.id)}
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className={`flex flex-col items-center justify-center gap-1 py-3 bg-white border-2 border-slate-200 rounded-xl text-xs font-medium text-slate-600 transition-all ${p.color}`}
              >
                <span className="text-lg">{p.emoji}</span>
                {p.label}
              </motion.button>
            ))}
          </div>
        </motion.form>

        {/* 注册入口 */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center text-sm text-slate-400 mt-6"
        >
          还没有账号？
          <Link href="/register" className="text-blue-400 hover:text-blue-300 font-semibold ml-1 inline-flex items-center gap-1 transition-colors">
            立即注册
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </motion.p>

        {/* 返回选择页 */}
        <div className="text-center mt-4">
          <Link href="/" className="text-xs text-slate-500 hover:text-slate-300 transition-colors inline-flex items-center gap-1">
            ← 返回设备选择页
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
