'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Camera, User, GraduationCap, Calendar, Users,
  Target, BookOpen, Save, Check, X,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface ProfileEditPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

const interestOptions = [
  'Python', 'Arduino', '机器人', '电路', '3D 建模',
  'AI/机器学习', '游戏开发', 'Web 开发', '物理实验', '数学',
];

const goalOptions = [
  '掌握 Python 编程', '考取编程等级证书', '完成首个独立项目',
  '参加编程竞赛', '理解 AI 原理', '提升逻辑思维',
];

export function ProfileEditPage({ mode, onBack }: ProfileEditPageProps) {
  const isPhone = mode === 'phone';
  const [form, setForm] = useState({
    avatar: '李',
    nickname: '李明',
    grade: 'G7',
    age: '13',
    gender: 'male',
    bio: '热爱编程和 STEM 实验，喜欢用代码创造有趣的东西。正在学习 Python 和 Arduino，梦想做一个自己的机器人！',
  });
  const [interests, setInterests] = useState<string[]>(['Python', 'Arduino', '机器人']);
  const [goals, setGoals] = useState<string[]>(['掌握 Python 编程', '完成首个独立项目']);
  const [saved, setSaved] = useState(false);

  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const toggleInterest = (tag: string) => {
    setInterests((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]);
  };
  const toggleGoal = (tag: string) => {
    setGoals((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => { setSaved(false); onBack?.(); }, 1200);
  };

  const avatarColors = [
    'from-blue-500 to-purple-600', 'from-green-500 to-teal-600',
    'from-orange-500 to-red-600', 'from-pink-500 to-rose-600',
  ];

  const inputCls = `w-full ${isPhone ? 'pl-10' : 'pl-12'} pr-4 py-${isPhone ? '2.5' : '3'} bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all`;
  const labelCls = `flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5`;

  const FormContent = (
    <>
      {/* 头像 */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative group cursor-pointer">
          <div className={`w-${isPhone ? '16' : '20'} h-${isPhone ? '16' : '20'} rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg`}>
            {form.avatar}
          </div>
          <div className="absolute inset-0 rounded-2xl bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
            <Camera className="h-6 w-6 text-white" />
          </div>
        </div>
        <div>
          <p className="font-bold text-slate-900">头像</p>
          <p className="text-xs text-slate-400 mt-0.5">点击更换头像</p>
          <div className="flex gap-1.5 mt-2">
            {avatarColors.map((c, i) => (
              <button
                key={i}
                onClick={() => {}}
                className={`w-5 h-5 rounded-full bg-gradient-to-br ${c} ${i === 0 ? 'ring-2 ring-offset-2 ring-blue-500' : ''}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 昵称 */}
      <div className="mb-4">
        <label className={labelCls}><User className="h-3.5 w-3.5" /> 昵称</label>
        <div className="relative">
          <User className={`absolute ${isPhone ? 'left-3' : 'left-4'} top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400`} />
          <input
            type="text"
            value={form.nickname}
            onChange={(e) => update('nickname', e.target.value)}
            className={inputCls}
            placeholder="输入昵称"
          />
        </div>
      </div>

      {/* 年级 + 年龄 */}
      <div className={`grid grid-cols-2 gap-${isPhone ? '3' : '4'} mb-4`}>
        <div>
          <label className={labelCls}><GraduationCap className="h-3.5 w-3.5" /> 年级</label>
          <div className="relative">
            <GraduationCap className={`absolute ${isPhone ? 'left-3' : 'left-4'} top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400`} />
            <select
              value={form.grade}
              onChange={(e) => update('grade', e.target.value)}
              className={`${inputCls} appearance-none cursor-pointer`}
            >
              {Array.from({ length: 12 }, (_, i) => `G${i + 1}`).map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className={labelCls}><Calendar className="h-3.5 w-3.5" /> 年龄</label>
          <div className="relative">
            <Calendar className={`absolute ${isPhone ? 'left-3' : 'left-4'} top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400`} />
            <input
              type="number"
              value={form.age}
              onChange={(e) => update('age', e.target.value)}
              className={inputCls}
              placeholder="年龄"
            />
          </div>
        </div>
      </div>

      {/* 性别 */}
      <div className="mb-4">
        <label className={labelCls}><Users className="h-3.5 w-3.5" /> 性别</label>
        <div className="flex gap-2">
          {[
            { id: 'male', label: '男', emoji: '👦' },
            { id: 'female', label: '女', emoji: '👧' },
            { id: 'other', label: '保密', emoji: '🔒' },
          ].map((g) => (
            <button
              key={g.id}
              onClick={() => update('gender', g.id)}
              className={`flex-1 py-2.5 rounded-xl text-sm font-medium border-2 transition-all flex items-center justify-center gap-1.5 ${
                form.gender === g.id
                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                  : 'border-slate-200 text-slate-600 hover:border-slate-300'
              }`}
            >
              <span>{g.emoji}</span> {g.label}
            </button>
          ))}
        </div>
      </div>

      {/* 兴趣标签 */}
      <div className="mb-4">
        <label className={labelCls}><Target className="h-3.5 w-3.5" /> 兴趣领域（可多选）</label>
        <div className="flex flex-wrap gap-2">
          {interestOptions.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleInterest(tag)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                interests.includes(tag)
                  ? 'border-blue-500 bg-blue-500 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-blue-300'
              }`}
            >
              {interests.includes(tag) && <Check className="h-3 w-3 inline mr-1" />}
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* 学习目标 */}
      <div className="mb-4">
        <label className={labelCls}><Target className="h-3.5 w-3.5" /> 学习目标（可多选）</label>
        <div className="flex flex-wrap gap-2">
          {goalOptions.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleGoal(tag)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                goals.includes(tag)
                  ? 'border-purple-500 bg-purple-500 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-purple-300'
              }`}
            >
              {goals.includes(tag) && <Check className="h-3 w-3 inline mr-1" />}
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* 自我介绍 */}
      <div className="mb-6">
        <label className={labelCls}><BookOpen className="h-3.5 w-3.5" /> 自我介绍</label>
        <textarea
          value={form.bio}
          onChange={(e) => update('bio', e.target.value)}
          rows={isPhone ? 3 : 4}
          className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
          placeholder="介绍一下自己吧..."
        />
        <p className="text-[10px] text-slate-400 mt-1 text-right">{form.bio.length}/200</p>
      </div>

      {/* 保存 / 取消 */}
      <div className="flex gap-3">
        <button
          onClick={() => onBack?.()}
          className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-xl text-sm font-semibold hover:bg-slate-200 transition-colors flex items-center justify-center gap-1.5"
        >
          <X className="h-4 w-4" /> 取消
        </button>
        <motion.button
          onClick={handleSave}
          whileTap={{ scale: 0.98 }}
          className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/30 hover:shadow-xl transition-all flex items-center justify-center gap-1.5"
        >
          {saved ? (
            <><Check className="h-4 w-4" /> 已保存</>
          ) : (
            <><Save className="h-4 w-4" /> 保存</>
          )}
        </motion.button>
      </div>
    </>
  );

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="space-y-4">
        {onBack && (
          <button onClick={onBack} className="flex items-center gap-1 text-sm text-slate-500">
            <ArrowLeft className="h-4 w-4" /> 返回
          </button>
        )}
        <h2 className="text-xl font-bold text-slate-900">编辑资料</h2>
        <div className="bg-white rounded-2xl border p-4">
          {FormContent}
        </div>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="flex items-center gap-4">
        {onBack && (
          <button onClick={onBack} className="p-2 bg-slate-100 rounded-xl text-slate-500 hover:bg-slate-200 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </button>
        )}
        <div>
          <h2 className="text-2xl font-bold text-slate-900">编辑个人资料</h2>
          <p className="text-sm text-slate-500 mt-0.5">完善信息，让 AI 教师更好地了解你</p>
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 p-8">
        {FormContent}
      </div>
    </div>
  );
}
