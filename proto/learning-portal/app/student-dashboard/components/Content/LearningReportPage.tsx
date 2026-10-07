'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Download, Clock, BookOpen, Award, Flame, TrendingUp, TrendingDown,
  Brain, Target, Sparkles, ArrowLeft, ChevronRight,
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell,
} from 'recharts';
import { DeviceMode } from '../../types';

interface LearningReportPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

type Range = 'week' | 'month' | 'term';

// 能力雷达图数据
const abilityData = [
  { subject: '编程逻辑', score: 78, full: 100 },
  { subject: '硬件控制', score: 85, full: 100 },
  { subject: '算法思维', score: 62, full: 100 },
  { subject: '电路知识', score: 70, full: 100 },
  { subject: '数据分析', score: 55, full: 100 },
  { subject: '创意表达', score: 88, full: 100 },
];

// 各范围的数据
const rangeData: Record<Range, {
  totalMinutes: number;
  coursesCompleted: number;
  avgScore: number;
  streak: number;
  weekly: { day: string; minutes: number }[];
  subjects: { name: string; progress: number; change: number }[];
  aiComment: string;
}> = {
  week: {
    totalMinutes: 285,
    coursesCompleted: 3,
    avgScore: 87,
    streak: 7,
    weekly: [
      { day: '周一', minutes: 45 },
      { day: '周二', minutes: 60 },
      { day: '周三', minutes: 30 },
      { day: '周四', minutes: 50 },
      { day: '周五', minutes: 40 },
      { day: '周六', minutes: 35 },
      { day: '周日', minutes: 25 },
    ],
    subjects: [
      { name: 'Python 基础', progress: 75, change: 5 },
      { name: 'Arduino', progress: 90, change: 8 },
      { name: '电路入门', progress: 60, change: -2 },
      { name: '数据结构', progress: 40, change: 3 },
    ],
    aiComment: '本周学习状态很好！你在 Arduino 模块进步明显（+8%），LED 控制实验全部完成。但电路入门略有退步，建议回顾欧姆定律章节。继续保持连续学习的习惯！',
  },
  month: {
    totalMinutes: 1240,
    coursesCompleted: 12,
    avgScore: 82,
    streak: 15,
    weekly: [
      { day: '第1周', minutes: 280 },
      { day: '第2周', minutes: 340 },
      { day: '第3周', minutes: 310 },
      { day: '第4周', minutes: 310 },
    ],
    subjects: [
      { name: 'Python 基础', progress: 75, change: 12 },
      { name: 'Arduino', progress: 90, change: 20 },
      { name: '电路入门', progress: 60, change: 5 },
      { name: '数据结构', progress: 40, change: 8 },
    ],
    aiComment: '本月累计学习 20.7 小时，完成 12 个课程，表现优秀！Arduino 模块月度进步 20%，是进步最大的领域。建议下月增加数据结构的学习时间，当前进度仅 40%。',
  },
  term: {
    totalMinutes: 5680,
    coursesCompleted: 48,
    avgScore: 84,
    streak: 15,
    weekly: [
      { day: '9月', minutes: 1200 },
      { day: '10月', minutes: 1500 },
      { day: '11月', minutes: 1380 },
      { day: '12月', minutes: 1600 },
    ],
    subjects: [
      { name: 'Python 基础', progress: 75, change: 45 },
      { name: 'Arduino', progress: 90, change: 60 },
      { name: '电路入门', progress: 60, change: 35 },
      { name: '数据结构', progress: 40, change: 20 },
    ],
    aiComment: '本学期累计学习 94.7 小时，完成 48 个课程，全面成长！编程能力和硬件控制进步显著。下学期建议聚焦数据结构与算法，为进阶编程做准备。',
  },
};

export function LearningReportPage({ mode, onBack }: LearningReportPageProps) {
  const isPhone = mode === 'phone';
  const [range, setRange] = useState<Range>('week');
  const data = rangeData[range];

  const rangeLabels: { id: Range; label: string }[] = [
    { id: 'week', label: '本周' },
    { id: 'month', label: '本月' },
    { id: 'term', label: '本学期' },
  ];

  const hours = (data.totalMinutes / 60).toFixed(1);

  // 汇总卡片
  const summaryCards = [
    { icon: Clock, label: '学习时长', value: `${hours}h`, sub: `${data.totalMinutes} 分钟`, color: 'from-blue-500 to-blue-600' },
    { icon: BookOpen, label: '完成课程', value: `${data.coursesCompleted}`, sub: '个课程', color: 'from-green-500 to-green-600' },
    { icon: Award, label: '平均成绩', value: `${data.avgScore}`, sub: '分', color: 'from-orange-500 to-red-500' },
    { icon: Flame, label: '连续学习', value: `${data.streak}`, sub: '天', color: 'from-purple-500 to-pink-500' },
  ];

  const handleExport = () => {
    alert(`📊 学习报告已导出！\n范围：${rangeLabels.find((r) => r.id === range)?.label}\n学习时长：${hours} 小时\n完成课程：${data.coursesCompleted} 个\n平均成绩：${data.avgScore} 分`);
  };

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="space-y-5">
        {/* 标题 + 返回 */}
        {onBack && (
          <button onClick={onBack} className="flex items-center gap-1 text-sm text-slate-500">
            <ArrowLeft className="h-4 w-4" /> 返回
          </button>
        )}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900">学习报告 📊</h2>
            <p className="text-xs text-slate-500 mt-0.5">AI 教师定期生成 · 可导出分享</p>
          </div>
          <button onClick={handleExport} className="px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold flex items-center gap-1">
            <Download className="h-3.5 w-3.5" /> 导出
          </button>
        </div>

        {/* 时间范围选择 */}
        <div className="flex gap-1.5 bg-slate-100 p-1 rounded-xl">
          {rangeLabels.map((r) => (
            <button
              key={r.id}
              onClick={() => setRange(r.id)}
              className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${
                range === r.id ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        {/* 汇总卡片 */}
        <div className="grid grid-cols-2 gap-3">
          {summaryCards.map((card, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`bg-gradient-to-br ${card.color} rounded-2xl p-4 text-white`}
            >
              <card.icon className="h-5 w-5 mb-2 opacity-80" />
              <div className="text-2xl font-bold">{card.value}</div>
              <div className="text-[10px] opacity-90">{card.label} · {card.sub}</div>
            </motion.div>
          ))}
        </div>

        {/* 能力雷达图 */}
        <div className="bg-white rounded-2xl border p-4">
          <h3 className="font-bold text-slate-900 text-sm mb-3 flex items-center gap-2">
            <Brain className="h-4 w-4 text-indigo-600" /> 能力雷达
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={abilityData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8 }} />
              <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 学科进度 */}
        <div className="bg-white rounded-2xl border p-4">
          <h3 className="font-bold text-slate-900 text-sm mb-3 flex items-center gap-2">
            <Target className="h-4 w-4 text-purple-600" /> 学科进度
          </h3>
          <div className="space-y-3">
            {data.subjects.map((s, i) => (
              <div key={i}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-700 font-medium">{s.name}</span>
                  <span className={`flex items-center gap-1 font-bold ${s.change >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                    {s.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {s.change >= 0 ? '+' : ''}{s.change}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${s.progress}%` }}
                    transition={{ delay: i * 0.1, duration: 0.6 }}
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 学习时长柱状图 */}
        <div className="bg-white rounded-2xl border p-4">
          <h3 className="font-bold text-slate-900 text-sm mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-600" /> 学习时长分布
          </h3>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data.weekly} margin={{ top: 5, right: 5, bottom: 0, left: -25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 9 }} />
              <YAxis tick={{ fontSize: 9 }} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v) => [`${v} 分钟`, '学习时长']} />
              <Bar dataKey="minutes" radius={[4, 4, 0, 0]}>
                {data.weekly.map((_, i) => (
                  <Cell key={i} fill={`hsl(${240 + i * 15}, 70%, 60%)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* AI 教师评语 */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-4 border border-indigo-100">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-600" /> AI 教师评语
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">{data.aiComment}</p>
        </div>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        {onBack && (
          <button onClick={onBack} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
            <ArrowLeft className="h-4 w-4" /> 返回
          </button>
        )}
        <div className="flex-1 ml-4">
          <h2 className="text-3xl font-bold text-slate-900">学习报告 📊</h2>
          <p className="text-sm text-slate-500 mt-0.5">AI 教师定期生成 · 可导出分享</p>
        </div>
        <button onClick={handleExport} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/30 hover:bg-indigo-700">
          <Download className="h-4 w-4" /> 导出报告
        </button>
      </div>

      {/* 时间范围选择 */}
      <div className="flex gap-2 bg-slate-100 p-1.5 rounded-xl w-fit">
        {rangeLabels.map((r) => (
          <button
            key={r.id}
            onClick={() => setRange(r.id)}
            className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${
              range === r.id ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* 汇总卡片 */}
      <div className="grid grid-cols-4 gap-5">
        {summaryCards.map((card, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            whileHover={{ y: -4 }}
            className={`bg-gradient-to-br ${card.color} rounded-2xl p-6 text-white shadow-lg`}
          >
            <card.icon className="h-8 w-8 mb-3 opacity-80" />
            <div className="text-4xl font-bold">{card.value}</div>
            <div className="text-sm opacity-90 mt-1">{card.label}</div>
            <div className="text-xs opacity-75">{card.sub}</div>
          </motion.div>
        ))}
      </div>

      {/* 图表区：雷达图 + 柱状图 */}
      <div className="grid grid-cols-2 gap-5">
        {/* 能力雷达图 */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" /> 能力雷达图
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={abilityData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2.5} />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 学习时长柱状图 */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <Clock className="h-5 w-5 text-blue-600" /> 学习时长分布
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.weekly} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} label={{ value: '分钟', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 12 }} formatter={(v) => [`${v} 分钟`, '学习时长']} />
              <Bar dataKey="minutes" radius={[6, 6, 0, 0]}>
                {data.weekly.map((_, i) => (
                  <Cell key={i} fill={`hsl(${240 + i * 15}, 70%, 60%)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 学科进度 */}
      <div className="bg-white rounded-2xl border border-slate-100 p-6">
        <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
          <Target className="h-5 w-5 text-purple-600" /> 学科进度与变化
        </h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-5">
          {data.subjects.map((s, i) => (
            <div key={i}>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-700 font-medium">{s.name}</span>
                <span className="flex items-center gap-2">
                  <span className="text-slate-400 text-xs">当前 {s.progress}%</span>
                  <span className={`flex items-center gap-0.5 font-bold text-xs px-2 py-0.5 rounded-full ${s.change >= 0 ? 'text-green-600 bg-green-50' : 'text-red-500 bg-red-50'}`}>
                    {s.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {s.change >= 0 ? '+' : ''}{s.change}%
                  </span>
                </span>
              </div>
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${s.progress}%` }}
                  transition={{ delay: i * 0.1, duration: 0.8, ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI 教师评语 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100"
      >
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl flex-shrink-0">
            🤖
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-slate-900 text-lg mb-2 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" /> AI 教师评语
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed">{data.aiComment}</p>
            <div className="mt-3 flex items-center gap-2 text-xs text-indigo-600">
              <span className="w-1 h-1 bg-indigo-400 rounded-full"></span>
              <span>基于 {rangeLabels.find((r) => r.id === range)?.label} 学习数据自动生成</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
