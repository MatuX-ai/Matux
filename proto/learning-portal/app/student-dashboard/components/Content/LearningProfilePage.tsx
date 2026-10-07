'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Brain, TrendingUp, AlertTriangle, ChevronDown } from 'lucide-react';
import { DeviceMode } from '../../types';

interface LearningProfilePageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// 能力雷达图数据（本月 vs 上月）
const abilityData = [
  { subject: '编程思维', current: 85, previous: 70 },
  { subject: '算法能力', current: 72, previous: 60 },
  { subject: '调试能力', current: 78, previous: 65 },
  { subject: '项目实践', current: 80, previous: 68 },
  { subject: 'STEM实验', current: 66, previous: 55 },
];

// 技能树
const skillTree = [
  {
    category: 'Python 基础',
    icon: '🐍',
    skills: [
      { name: '变量与数据类型', progress: 100, status: 'done' },
      { name: '条件判断', progress: 95, status: 'done' },
      { name: '循环', progress: 60, status: 'current' },
      { name: '函数', progress: 0, status: 'locked' },
      { name: '面向对象', progress: 0, status: 'locked' },
    ],
  },
  {
    category: 'STEM 实验',
    icon: '🔧',
    skills: [
      { name: 'LED 控制', progress: 100, status: 'done' },
      { name: '传感器入门', progress: 45, status: 'current' },
      { name: '机器人编程', progress: 0, status: 'locked' },
    ],
  },
];

// 薄弱环节
const weakPoints = [
  { topic: 'range() 参数理解', accuracy: 55, advice: 'Blockly 对照练习' },
  { topic: '缩进规范', accuracy: 70, advice: '代码格式化插件' },
  { topic: '列表索引', accuracy: 65, advice: '互动小测验' },
];

export function LearningProfilePage({ mode, onBack }: LearningProfilePageProps) {
  const isPhone = mode === 'phone';
  const [expanded, setExpanded] = useState(false);

  const statusMap: Record<string, { icon: string; color: string; label: string }> = {
    done: { icon: '✅', color: 'text-green-600', label: '已掌握' },
    current: { icon: '🔄', color: 'text-blue-600', label: '学习中' },
    locked: { icon: '🔒', color: 'text-slate-400', label: '未解锁' },
  };

  // 手机模式
  if (isPhone) {
    return (
      <div className="px-5 space-y-4 pb-24">
        <h2 className="text-xl font-bold text-slate-900">我的学习画像</h2>

        {/* AI 教师眼中的你 */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-4 border border-indigo-100">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Brain className="h-4 w-4 text-indigo-600" /> AI 教师眼中的你
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">
            "李明是一个视觉型学习者，擅长通过动画和图表理解概念。编程逻辑很强，但代码规范还需注意。"
          </p>
          <div className="grid grid-cols-2 gap-2 mt-3 text-[10px]">
            <div className="bg-white/60 rounded-lg p-2">
              <span className="text-slate-500">最喜欢的领域</span>
              <p className="font-semibold text-slate-900">游戏开发</p>
            </div>
            <div className="bg-white/60 rounded-lg p-2">
              <span className="text-slate-500">最佳学习时段</span>
              <p className="font-semibold text-slate-900">下午 3-5 点</p>
            </div>
          </div>
          <p className="text-xs text-orange-600 mt-2 flex items-center gap-1">
            🔥 连续学习 15 天
          </p>
        </div>

        {/* 雷达图 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <h3 className="font-bold text-slate-900 text-sm mb-2">能力雷达图</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={abilityData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#64748b' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <Radar name="本月" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
              <Radar name="上月" dataKey="previous" stroke="#cbd5e1" fill="#cbd5e1" fillOpacity={0.3} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* 技能树 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <h3 className="font-bold text-slate-900 text-sm mb-3">技能树</h3>
          {skillTree.map((tree) => (
            <div key={tree.category} className="mb-3 last:mb-0">
              <p className="text-xs font-semibold text-slate-700 mb-1.5">{tree.icon} {tree.category}</p>
              {tree.skills.slice(0, expanded ? undefined : 2).map((skill) => {
                const st = statusMap[skill.status];
                return (
                  <div key={skill.name} className="flex items-center gap-2 py-1 text-[11px]">
                    <span>{st.icon}</span>
                    <span className={skill.status === 'locked' ? 'text-slate-400' : 'text-slate-700'}>
                      {skill.name}
                    </span>
                    {skill.status !== 'locked' && (
                      <span className="ml-auto text-slate-500">{skill.progress}%</span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-600 flex items-center gap-1 mt-1"
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
            {expanded ? '收起' : '展开全部'}
          </button>
        </div>

        {/* 薄弱环节 */}
        <div className="bg-white rounded-2xl p-4 shadow-md">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" /> 薄弱环节
          </h3>
          {weakPoints.map((wp) => (
            <div key={wp.topic} className="py-2 border-b last:border-0">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-700">⚠ {wp.topic}</span>
                <span className="font-semibold text-red-500">{wp.accuracy}%</span>
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">建议：{wp.advice}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // 平板/桌面模式
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
          <h2 className="text-3xl font-bold text-slate-900">我的学习画像</h2>
        </div>
        <span className="text-sm text-slate-500">最后更新：今天 14:30</span>
      </div>

      {/* 上：AI 摘要 + 雷达图 */}
      <div className="grid grid-cols-12 gap-5">
        {/* AI 教师眼中的你 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="col-span-5 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100"
        >
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <Brain className="h-5 w-5 text-indigo-600" /> AI 教师眼中的你
          </h3>
          <p className="text-sm text-slate-700 leading-relaxed mb-4">
            "李明是一个视觉型学习者，擅长通过动画和图表理解概念。你的编程逻辑很强，但在代码规范上还需要多加注意。"
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/70 rounded-xl p-3">
              <p className="text-xs text-slate-500 mb-1">最喜欢的领域</p>
              <p className="font-semibold text-slate-900 text-sm">🎮 游戏开发</p>
            </div>
            <div className="bg-white/70 rounded-xl p-3">
              <p className="text-xs text-slate-500 mb-1">最佳学习时段</p>
              <p className="font-semibold text-slate-900 text-sm">🕒 下午 3-5 点</p>
            </div>
          </div>
          <div className="mt-4 bg-orange-50 rounded-xl p-3 flex items-center gap-2">
            <span className="text-2xl">🔥</span>
            <div>
              <p className="font-bold text-orange-600 text-lg">连续学习 15 天</p>
              <p className="text-xs text-orange-500">再坚持 7 天解锁"三周不辍"徽章</p>
            </div>
          </div>
        </motion.div>

        {/* 能力雷达图 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="col-span-7 bg-white rounded-2xl p-6 shadow-md"
        >
          <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" /> 能力雷达图
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={abilityData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#475569' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Radar name="本月" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
              <Radar name="上月" dataKey="previous" stroke="#cbd5e1" fill="#cbd5e1" fillOpacity={0.3} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* 中：技能树 */}
      <div className="bg-white rounded-2xl p-6 shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-900 text-lg">技能树</h3>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 flex items-center gap-1 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition-colors"
          >
            <ChevronDown className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
            {expanded ? '收起全部' : '展开全部'}
          </button>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {skillTree.map((tree) => (
            <div key={tree.category}>
              <p className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <span className="text-xl">{tree.icon}</span> {tree.category}
              </p>
              <div className="space-y-2">
                {tree.skills.slice(0, expanded ? undefined : 3).map((skill) => {
                  const st = statusMap[skill.status];
                  return (
                    <div
                      key={skill.name}
                      className={`flex items-center gap-3 py-2 px-3 rounded-lg ${
                        skill.status === 'current' ? 'bg-blue-50' : 'hover:bg-slate-50'
                      }`}
                    >
                      <span className="text-base">{st.icon}</span>
                      <span className={`text-sm flex-1 ${skill.status === 'locked' ? 'text-slate-400' : 'text-slate-700'}`}>
                        {skill.name}
                        {skill.status === 'current' && (
                          <span className="ml-2 text-[10px] text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">当前</span>
                        )}
                      </span>
                      {skill.status !== 'locked' && (
                        <div className="flex items-center gap-2 w-32">
                          <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${skill.status === 'done' ? 'bg-green-500' : 'bg-blue-500'}`}
                              style={{ width: `${skill.progress}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-slate-500 min-w-[30px]">{skill.progress}%</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 下：薄弱环节 */}
      <div className="bg-white rounded-2xl p-6 shadow-md">
        <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" /> 薄弱环节（AI 教师诊断）
        </h3>
        <div className="space-y-3">
          {weakPoints.map((wp) => (
            <div
              key={wp.topic}
              className="flex items-center gap-4 p-4 rounded-xl bg-amber-50/50 border border-amber-100"
            >
              <span className="text-lg">⚠</span>
              <div className="flex-1">
                <p className="font-semibold text-slate-900 text-sm">{wp.topic}</p>
                <p className="text-xs text-slate-500 mt-0.5">建议：{wp.advice}</p>
              </div>
              <div className="flex items-center gap-3 min-w-[160px]">
                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-400 to-red-500 rounded-full"
                    style={{ width: `${wp.accuracy}%` }}
                  ></div>
                </div>
                <span className="text-sm font-semibold text-red-500 min-w-[40px]">{wp.accuracy}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
