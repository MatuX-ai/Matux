'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, User, GraduationCap, ArrowRight, Eye, EyeOff, Sparkles, Check } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    nickname: '',
    grade: 'G7',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (key: string, value: string) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: '' }));
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.email) e.email = '请输入邮箱';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = '邮箱格式不正确';
    if (!form.password) e.password = '请输入密码';
    else if (form.password.length < 6) e.password = '密码至少 6 位';
    if (form.password !== form.confirmPassword) e.confirmPassword = '两次密码不一致';
    if (!form.nickname) e.nickname = '请输入昵称';
    if (!agreed) e.agreed = '请同意用户协议';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleRegister = (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setTimeout(() => router.push('/login'), 800);
  };

  const handleOAuth = (provider: string) => {
    setLoading(true);
    setTimeout(() => router.push('/'), 600);
  };

  const grades = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12'];

  const oauthProviders = [
    { id: 'qq', label: 'QQ', emoji: '🐧', color: 'hover:border-blue-400 hover:bg-blue-50' },
    { id: 'wechat', label: '微信', emoji: '💬', color: 'hover:border-green-400 hover:bg-green-50' },
    { id: 'google', label: 'Google', emoji: 'G', color: 'hover:border-red-400 hover:bg-red-50' },
    { id: 'github', label: 'GitHub', emoji: '🐙', color: 'hover:border-slate-700 hover:bg-slate-100' },
  ];

  // 密码强度
  const pwdStrength = (() => {
    const p = form.password;
    if (!p) return 0;
    let s = 0;
    if (p.length >= 6) s++;
    if (p.length >= 10) s++;
    if (/[A-Z]/.test(p) && /[a-z]/.test(p)) s++;
    if (/\d/.test(p)) s++;
    if (/[^A-Za-z0-9]/.test(p)) s++;
    return Math.min(s, 4);
  })();
  const strengthLabels = ['', '弱', '一般', '较强', '强'];
  const strengthColors = ['', 'bg-red-400', 'bg-yellow-400', 'bg-blue-400', 'bg-green-400'];

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
        <div className="text-center mb-6">
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl shadow-purple-500/30 mb-4"
          >
            <span className="text-3xl">🧊</span>
          </motion.div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
            创建账号
          </h1>
          <p className="text-sm text-slate-400 mt-1.5 flex items-center justify-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            开启你的 AI 编程与 STEM 学习之旅
          </p>
        </div>

        {/* 注册卡片 */}
        <motion.form
          onSubmit={handleRegister}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/95 backdrop-blur-xl rounded-3xl p-7 shadow-2xl border border-white/20"
        >
          {/* 昵称 */}
          <div className="mb-3.5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">昵称</label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={form.nickname}
                onChange={(e) => update('nickname', e.target.value)}
                placeholder="你的昵称"
                className={`w-full pl-11 pr-4 py-3 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${errors.nickname ? 'border-red-400' : 'border-slate-200 focus:border-blue-500'}`}
              />
            </div>
            {errors.nickname && <p className="text-[11px] text-red-500 mt-1 ml-1">{errors.nickname}</p>}
          </div>

          {/* 邮箱 */}
          <div className="mb-3.5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">邮箱地址</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="student@matux.com"
                className={`w-full pl-11 pr-4 py-3 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${errors.email ? 'border-red-400' : 'border-slate-200 focus:border-blue-500'}`}
              />
            </div>
            {errors.email && <p className="text-[11px] text-red-500 mt-1 ml-1">{errors.email}</p>}
          </div>

          {/* 年级 */}
          <div className="mb-3.5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">年级</label>
            <div className="relative">
              <GraduationCap className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <select
                value={form.grade}
                onChange={(e) => update('grade', e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all appearance-none cursor-pointer"
              >
                {grades.map((g) => (
                  <option key={g} value={g}>{g}（{g.startsWith('G') && parseInt(g.slice(1)) <= 6 ? '小学' : parseInt(g.slice(1)) <= 9 ? '初中' : '高中'} {g}）</option>
                ))}
              </select>
            </div>
          </div>

          {/* 密码 */}
          <div className="mb-3.5">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">密码</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                placeholder="至少 6 位"
                className={`w-full pl-11 pr-11 py-3 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${errors.password ? 'border-red-400' : 'border-slate-200 focus:border-blue-500'}`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {/* 密码强度条 */}
            {form.password && (
              <div className="flex items-center gap-1.5 mt-1.5">
                <div className="flex-1 flex gap-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-all ${i <= pwdStrength ? strengthColors[pwdStrength] : 'bg-slate-200'}`}
                    />
                  ))}
                </div>
                <span className="text-[10px] text-slate-400 w-8">{strengthLabels[pwdStrength]}</span>
              </div>
            )}
            {errors.password && <p className="text-[11px] text-red-500 mt-1 ml-1">{errors.password}</p>}
          </div>

          {/* 确认密码 */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">确认密码</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.confirmPassword}
                onChange={(e) => update('confirmPassword', e.target.value)}
                placeholder="再次输入密码"
                className={`w-full pl-11 pr-11 py-3 bg-slate-50 border rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${errors.confirmPassword ? 'border-red-400' : 'border-slate-200 focus:border-blue-500'}`}
              />
              {form.confirmPassword && form.password === form.confirmPassword && (
                <Check className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
              )}
            </div>
            {errors.confirmPassword && <p className="text-[11px] text-red-500 mt-1 ml-1">{errors.confirmPassword}</p>}
          </div>

          {/* 用户协议 */}
          <div className="mb-5">
            <button
              type="button"
              onClick={() => { setAgreed(!agreed); setErrors((e) => ({ ...e, agreed: '' })); }}
              className="flex items-start gap-2 text-xs text-slate-600 hover:text-slate-900 transition-colors"
            >
              <span
                className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all flex-shrink-0 mt-0.5 ${
                  agreed ? 'bg-blue-500 border-blue-500' : 'border-slate-300 bg-white'
                }`}
              >
                {agreed && <Check className="w-2.5 h-2.5 text-white" />}
              </span>
              <span>
                我已阅读并同意
                <span className="text-blue-600 font-medium">《用户协议》</span>
                和
                <span className="text-blue-600 font-medium">《隐私政策》</span>
              </span>
            </button>
            {errors.agreed && <p className="text-[11px] text-red-500 mt-1 ml-1">{errors.agreed}</p>}
          </div>

          {/* 注册按钮 */}
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
                创建账号
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </motion.button>

          {/* 分隔线 */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-slate-200"></div>
            <span className="text-xs text-slate-400">或使用第三方注册</span>
            <div className="flex-1 h-px bg-slate-200"></div>
          </div>

          {/* 第三方注册 */}
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

        {/* 登录入口 */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-center text-sm text-slate-400 mt-6"
        >
          已有账号？
          <Link href="/login" className="text-blue-400 hover:text-blue-300 font-semibold ml-1 inline-flex items-center gap-1 transition-colors">
            去登录
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
