'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import {
  Sparkles, TrendingUp, GitBranch, BarChart3, Heart, ChevronDown, Calendar,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface GrowthTrajectoryPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// ============ 多时间范围趋势数据 ============
const trendDatasets = {
  '3m': [
    { month: '4月', coding: 65, stem: 52 },
    { month: '5月', coding: 78, stem: 60 },
    { month: '6月', coding: 85, stem: 66 },
  ],
  '6m': [
    { month: '1月', coding: 35, stem: 25 },
    { month: '2月', coding: 42, stem: 30 },
    { month: '3月', coding: 55, stem: 40 },
    { month: '4月', coding: 65, stem: 52 },
    { month: '5月', coding: 78, stem: 60 },
    { month: '6月', coding: 85, stem: 66 },
  ],
  '1y': [
    { month: '7月', coding: 10, stem: 5 },
    { month: '8月', coding: 15, stem: 8 },
    { month: '9月', coding: 22, stem: 12 },
    { month: '10月', coding: 28, stem: 18 },
    { month: '11月', coding: 30, stem: 22 },
    { month: '12月', coding: 33, stem: 24 },
    { month: '1月', coding: 35, stem: 25 },
    { month: '2月', coding: 42, stem: 30 },
    { month: '3月', coding: 55, stem: 40 },
    { month: '4月', coding: 65, stem: 52 },
    { month: '5月', coding: 78, stem: 60 },
    { month: '6月', coding: 85, stem: 66 },
  ],
};

const rangeLabels: Record<string, string> = { '3m': '近 3 个月', '6m': '近 6 个月', '1y': '近 1 年' };

// ============ 能力雷达图 ============
const radarData = [
  { ability: '编程', current: 85, prev: 55 },
  { ability: '逻辑', current: 72, prev: 48 },
  { ability: '硬件', current: 66, prev: 30 },
  { ability: '创意', current: 78, prev: 60 },
  { ability: '协作', current: 60, prev: 45 },
  { ability: '表达', current: 55, prev: 40 },
];

// ============ 学习里程碑 ============
interface Milestone {
  date: string;
  icon: string;
  title: string;
  future: boolean;
  detail: string;
  reward?: string;
}

const milestones: Milestone[] = [
  {
    date: '2026-01-15', icon: '🎓', title: '完成第一个 Blockly 关卡', future: false,
    detail: '使用积木块完成了"小猫走路"动画，掌握了运动类积木的基本使用方法。这是你 STEM 学习之旅的起点！',
    reward: '+10 积分',
  },
  {
    date: '2026-02-20', icon: '🐍', title: '开始学习 Python', future: false,
    detail: '从 Blockly 过渡到文本编程。学会了 print()、变量赋值和基本数据类型。第一次运行 Python 程序时非常兴奋！',
    reward: '+20 积分',
  },
  {
    date: '2026-03-10', icon: '🏗️', title: '首个独立项目：猜数字游戏', future: false,
    detail: '综合运用 input()、while 循环和条件判断，完成了第一个完整项目。代码共 28 行，运行成功！',
    reward: '+50 积分 + 🏅徽章',
  },
  {
    date: '2026-04-05', icon: '🔧', title: '独立 Debug 3 个错误', future: false,
    detail: '在电路实验项目中遇到 LED 不亮的问题，独立排查出是引脚配置错误。学会了用 print() 调试的技巧。',
  },
  {
    date: '2026-04-28', icon: '⚡', title: '突破：循环正确率 40% → 75%', future: false,
    detail: '通过每日挑战和专项练习，for/while 循环的正确率大幅提升。AI 教师评价：进步显著！',
    reward: '+30 积分',
  },
  {
    date: '2026-05-15', icon: '🚀', title: '连续学习 100 天！', future: false,
    detail: '从 2 月初到 5 月中，连续 100 天每天至少完成一个学习任务。这是坚持的力量！',
    reward: '+200 积分 + 🏆限定徽章',
  },
  {
    date: '未来', icon: '🔮', title: 'AI 预测：下个月达到 Python 中阶水平', future: true,
    detail: '基于当前学习速度和能力增长趋势，AI 预测你在 7 月中旬将达到 Python 中级水平，可以开始学习函数和面向对象编程。',
  },
];

const stats = [
  { label: '总学时', value: '187', unit: '小时' },
  { label: '完成课程', value: '23', unit: '门' },
  { label: '完成项目', value: '8', unit: '个' },
  { label: '提问次数', value: '156', unit: '次' },
];

// ============ 生成学习热力图数据（12 周 x 7 天） ============
const generateHeatmap = () => {
  const weeks = 12;
  const days = 7;
  return Array.from({ length: weeks }, (_, w) =>
    Array.from({ length: days }, (_, d) => {
      // 模拟：周末学习更多，近期学习更多
      const weekendBoost = (d === 0 || d === 6) ? 0.3 : 0;
      const recentBoost = w / weeks * 0.4;
      const base = 0.2 + weekendBoost + recentBoost;
      const random = Math.random();
      const level = random < base * 0.3 ? 0 :
                    random < base * 0.6 ? 1 :
                    random < base * 0.85 ? 2 :
                    random < base ? 3 : 4;
      return level;
    })
  );
};

const heatmapColors = ['bg-slate-100', 'bg-green-200', 'bg-green-400', 'bg-green-500', 'bg-green-600'];
const heatmapLabels = ['无', '少', '中', '多', '密集'];

export function GrowthTrajectoryPage({ mode, onBack }: GrowthTrajectoryPageProps) {
  const isPhone = mode === 'phone';
  const [timeRange, setTimeRange] = useState<'3m' | '6m' | '1y'>('6m');
  const [showRangeMenu, setShowRangeMenu] = useState(false);
  const [expandedMilestone, setExpandedMilestone] = useState<number | null>(null);
  const [heatmap] = useState(generateHeatmap);

  const trendData = useMemo(() => trendDatasets[timeRange], [timeRange]);

  // 热力图统计
  const heatmapStats = useMemo(() => {
    const all = heatmap.flat();
    const active = all.filter(v => v > 0).length;
    const total = all.length;
    return { active, total, rate: Math.round((active / total) * 100) };
  }, [heatmap]);

  // ============ 时间范围选择器 ============
  const RangeSelector = () => (
    <div className="relative">
      <button
        onClick={() => setShowRangeMenu(!showRangeMenu)}
        className="text-sm text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-slate-200 transition-colors"
      >
        <Calendar className="h-3.5 w-3.5" />
        {rangeLabels[timeRange]}
        <ChevronDown className="h-3.5 w-3.5" />
      </button>
      <AnimatePresence>
        {showRangeMenu && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            className="absolute right-0 mt-1 bg-white rounded-lg shadow-xl border z-20 py-1 min-w-[140px]"
          >
            {Object.entries(rangeLabels).map(([key, label]) => (
              <button
                key={key}
                onClick={() => { setTimeRange(key as '3m' | '6m' | '1y'); setShowRangeMenu(false); }}
                className={`w-full text-left px-3 py-1.5 text-sm hover:bg-slate-50 transition-colors ${
                  timeRange === key ? 'text-blue-600 font-bold' : 'text-slate-600'
                }`}
              >
                {label}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  // ============ 热力图组件 ============
  const Heatmap = () => (
    <div>
      <div className="flex gap-1 overflow-x-auto pb-2">
        {heatmap.map((week, w) => (
          <div key={w} className="flex flex-col gap-1">
            {week.map((level, d) => (
              <motion.div
                key={d}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: (w * 7 + d) * 0.003 }}
                whileHover={{ scale: 1.3 }}
                className={`w-3 h-3 rounded-sm ${heatmapColors[level]}`}
                title={`第${w + 1}周 周${['日', '一', '二', '三', '四', '五', '六'][d]}: ${heatmapLabels[level]}`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between mt-2 text-[10px] text-slate-400">
        <span>12 周学习活动</span>
        <div className="flex items-center gap-1">
          <span>少</span>
          {heatmapColors.map((c, i) => (
            <div key={i} className={`w-2.5 h-2.5 rounded-sm ${c}`}></div>
          ))}
          <span>多</span>
        </div>
      </div>
    </div>
  );

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="px-5 space-y-4 pb-24">
        <h2 className="text-xl font-bold text-slate-900">我的成长轨迹</h2>

        {/* AI 寄语 */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-4 border border-indigo-100">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-600" /> AI 教师寄语（2026年5月）
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">
            "李明，这个月你进步非常大！从月初对循环一知半解，到现在已经能独立写出 for/while 两种循环了。
            下个月建议重点攻克函数，加油！💪"
          </p>
        </div>

        {/* 趋势图 + 时间筛选 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-slate-900 text-sm">能力趋势</h3>
            <RangeSelector />
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 9, fill: '#94a3b8' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ fontSize: 11 }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="coding" name="编程" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
              <Line type="monotone" dataKey="stem" name="STEM" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 能力雷达图 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <h3 className="font-bold text-slate-900 text-sm mb-2">能力雷达</h3>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="ability" tick={{ fontSize: 10, fill: '#64748b' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 8 }} />
              <Radar name="当前" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Radar name="3个月前" dataKey="prev" stroke="#cbd5e1" fill="#cbd5e1" fillOpacity={0.2} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 学习热力图 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-slate-900 text-sm">学习热力图</h3>
            <span className="text-[10px] text-green-500">{heatmapStats.rate}% 活跃</span>
          </div>
          <Heatmap />
        </div>

        {/* 里程碑时间轴 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <h3 className="font-bold text-slate-900 text-sm mb-3">学习里程碑</h3>
          <div className="space-y-2">
            {milestones.map((m, i) => (
              <div key={i}>
                <motion.div
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setExpandedMilestone(expandedMilestone === i ? null : i)}
                  className="flex gap-3 cursor-pointer"
                >
                  <div className="flex flex-col items-center">
                    <span className="text-base">{m.icon}</span>
                    {i < milestones.length - 1 && <span className="w-px flex-1 bg-slate-200 my-1"></span>}
                  </div>
                  <div className={`pb-2 flex-1 ${m.future ? 'opacity-70' : ''}`}>
                    <p className="text-[10px] text-slate-400">{m.date}</p>
                    <p className={`text-xs ${m.future ? 'text-purple-600 italic' : 'text-slate-700'}`}>{m.title}</p>
                  </div>
                  <ChevronDown className={`h-3 w-3 text-slate-400 mt-2 transition-transform ${expandedMilestone === i ? 'rotate-180' : ''}`} />
                </motion.div>
                <AnimatePresence>
                  {expandedMilestone === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden ml-7"
                    >
                      <div className="bg-slate-50 rounded-lg p-3 mb-2">
                        <p className="text-[11px] text-slate-600 mb-1">{m.detail}</p>
                        {m.reward && (
                          <p className="text-[10px] text-orange-500 font-medium">🎁 {m.reward}</p>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* 统计 + 兴趣 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white rounded-2xl p-3 shadow-md">
            <h4 className="font-bold text-slate-900 text-xs mb-2">学习统计</h4>
            {stats.map((s) => (
              <div key={s.label} className="flex justify-between text-[10px] py-1">
                <span className="text-slate-500">{s.label}</span>
                <span className="font-semibold text-slate-900">{s.value}{s.unit}</span>
              </div>
            ))}
          </div>
          <div className="bg-white rounded-2xl p-3 shadow-md">
            <h4 className="font-bold text-slate-900 text-xs mb-2">兴趣演变</h4>
            <p className="text-[10px] text-slate-600">Jan: 🎮 游戏 60%</p>
            <p className="text-[10px] text-slate-600">Mar: 🤖 机器人 30%</p>
            <p className="text-[10px] text-slate-600">May: 🤖 机器人 45%</p>
            <p className="text-[10px] text-purple-600 mt-1">→ 向机器人/硬件偏移</p>
          </div>
        </div>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-600"
            >
              ←
            </button>
          )}
          <h2 className="text-3xl font-bold text-slate-900">我的成长轨迹</h2>
        </div>
        <span className="text-sm text-slate-500">2026 年 6 月</span>
      </div>

      {/* AI 教师寄语 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100"
      >
        <h3 className="font-bold text-slate-900 text-lg mb-3 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-600" /> AI 教师寄语（2026 年 5 月）
        </h3>
        <p className="text-sm text-slate-700 leading-relaxed">
          "李明，这个月你进步非常大！从月初对循环一知半解，到现在已经能独立写出 for/while 两种循环了。
          特别让我惊喜的是，你在电路实验里独立完成了红绿灯项目——这是很多同学觉得难的地方！
          下个月我建议你重点攻克函数，这是通往更复杂项目的必经之路。加油，我相信你能做到！💪"
        </p>
      </motion.div>

      {/* 能力趋势 + 时间筛选 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-md"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" /> 能力趋势
          </h3>
          <RangeSelector />
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#475569' }} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} unit="%" />
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="coding" name="编程" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
            <Line type="monotone" dataKey="stem" name="STEM 实验" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 4 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      {/* 雷达图 + 热力图 */}
      <div className="grid grid-cols-2 gap-5">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl p-6 shadow-md"
        >
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-purple-600" /> 能力雷达
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="ability" tick={{ fontSize: 12, fill: '#475569' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="当前" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} strokeWidth={2} />
              <Radar name="3个月前" dataKey="prev" stroke="#cbd5e1" fill="#cbd5e1" fillOpacity={0.15} strokeWidth={1.5} strokeDasharray="5 3" />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl p-6 shadow-md"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5 text-green-600" /> 学习热力图
            </h3>
            <span className="text-sm text-green-500 font-medium">{heatmapStats.rate}% 活跃</span>
          </div>
          <Heatmap />
          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="text-lg font-bold text-slate-900">{heatmapStats.active}</div>
              <div className="text-[10px] text-slate-500">活跃天数</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="text-lg font-bold text-green-600">{heatmap.filter(w => w.some(d => d === 4)).length}</div>
              <div className="text-[10px] text-slate-500">密集学习周</div>
            </div>
            <div className="bg-slate-50 rounded-lg p-2">
              <div className="text-lg font-bold text-orange-500">{heatmapStats.total - heatmapStats.active}</div>
              <div className="text-[10px] text-slate-500">休息天数</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* 里程碑时间轴 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-6 shadow-md"
      >
        <h3 className="font-bold text-slate-900 text-lg mb-5 flex items-center gap-2">
          <GitBranch className="h-5 w-5 text-purple-600" /> 学习里程碑时间轴
          <span className="text-xs text-slate-400 ml-2">点击展开详情</span>
        </h3>
        <div className="relative pl-2">
          {milestones.map((m, i) => (
            <div key={i} className="pb-3 last:pb-0 relative">
              <motion.div
                whileHover={{ x: 4 }}
                onClick={() => setExpandedMilestone(expandedMilestone === i ? null : i)}
                className="flex gap-4 cursor-pointer"
              >
                {/* 竖线 */}
                {i < milestones.length - 1 && (
                  <span className="absolute left-[18px] top-10 bottom-0 w-0.5 bg-slate-200"></span>
                )}
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 z-10 transition-colors ${
                    m.future ? 'bg-purple-100' :
                    expandedMilestone === i ? 'bg-blue-500' : 'bg-blue-100'
                  }`}
                >
                  <span className="text-base">{m.icon}</span>
                </div>
                <div className="pt-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-400">{m.date}</p>
                      <p className={`text-sm font-medium mt-0.5 ${m.future ? 'text-purple-600 italic' : 'text-slate-800'}`}>
                        {m.title}
                      </p>
                    </div>
                    <motion.div animate={{ rotate: expandedMilestone === i ? 180 : 0 }}>
                      <ChevronDown className="h-4 w-4 text-slate-400" />
                    </motion.div>
                  </div>
                </div>
              </motion.div>

              {/* 展开详情 */}
              <AnimatePresence>
                {expandedMilestone === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden ml-13"
                  >
                    <div className="ml-13 mt-2 bg-slate-50 rounded-xl p-4 border-l-4 border-blue-400">
                      <p className="text-sm text-slate-600 mb-2">{m.detail}</p>
                      {m.reward && (
                        <div className="inline-flex items-center gap-1.5 bg-orange-50 text-orange-600 px-3 py-1 rounded-lg text-xs font-medium">
                          🎁 {m.reward}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 统计 + 兴趣演变 */}
      <div className="grid grid-cols-2 gap-5">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl p-6 shadow-md"
        >
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-600" /> 学习统计
          </h3>
          <div className="space-y-3">
            {stats.map((s) => (
              <div key={s.label} className="flex justify-between items-center py-2 border-b last:border-0 border-slate-100">
                <span className="text-sm text-slate-600">{s.label}</span>
                <span className="text-lg font-bold text-slate-900">
                  {s.value}<span className="text-xs font-normal text-slate-400 ml-1">{s.unit}</span>
                </span>
              </div>
            ))}
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-slate-600">提问质量</span>
              <span className="text-sm font-semibold text-green-600">中 → 高 ↑</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl p-6 shadow-md"
        >
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <Heart className="h-5 w-5 text-pink-500" /> 兴趣演变
          </h3>
          <div className="space-y-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">1 月</p>
              <div className="flex gap-2 text-sm">
                <span className="bg-pink-50 text-pink-600 px-2 py-1 rounded-lg">🎮 游戏开发 60%</span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">3 月</p>
              <div className="flex gap-2 text-sm">
                <span className="bg-blue-50 text-blue-600 px-2 py-1 rounded-lg">🤖 机器人 30%</span>
                <span className="bg-pink-50 text-pink-600 px-2 py-1 rounded-lg">🎮 游戏 50%</span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">5 月</p>
              <div className="flex gap-2 text-sm">
                <span className="bg-blue-50 text-blue-600 px-2 py-1 rounded-lg">🤖 机器人 45%</span>
                <span className="bg-pink-50 text-pink-600 px-2 py-1 rounded-lg">🎮 游戏 35%</span>
              </div>
            </div>
            <div className="mt-3 p-3 bg-purple-50 rounded-xl">
              <p className="text-xs text-purple-700">📈 趋势：从游戏开发向机器人 / 硬件方向偏移</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
