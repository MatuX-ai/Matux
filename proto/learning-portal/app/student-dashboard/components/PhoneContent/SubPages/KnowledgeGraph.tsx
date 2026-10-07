'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Network, Zap, Cpu, Code } from 'lucide-react';

interface KnowledgeGraphProps {
  onNavigate: (page: string) => void;
}

// 知识图谱节点（坐标基于 360×320 viewBox）
type GNode = {
  id: string;
  label: string;
  x: number;
  y: number;
  type: 'center' | 'branch' | 'leaf';
  mastery: number; // 0-100，-1 表示未开始
  parent?: string;
  desc: string;
};

const nodes: GNode[] = [
  { id: 'stem', label: 'STEM', x: 180, y: 160, type: 'center', mastery: -1, desc: '你的 STEM 学习知识体系' },
  { id: 'python', label: 'Python', x: 85, y: 85, type: 'branch', mastery: 75, parent: 'stem', desc: '编程逻辑主线 · 12 个知识点' },
  { id: 'arduino', label: 'Arduino', x: 275, y: 85, type: 'branch', mastery: 70, parent: 'stem', desc: '硬件控制主线 · 10 个知识点' },
  { id: 'ml', label: '机器学习', x: 85, y: 235, type: 'branch', mastery: 30, parent: 'stem', desc: 'AI 进阶主线 · 8 个知识点' },
  { id: 'circuit', label: '电路基础', x: 275, y: 235, type: 'branch', mastery: 55, parent: 'stem', desc: '物理原理主线 · 9 个知识点' },
  // Python 叶子
  { id: 'var', label: '变量', x: 30, y: 40, type: 'leaf', mastery: 75, parent: 'python', desc: '变量命名与赋值 · 已掌握' },
  { id: 'loop', label: '循环', x: 30, y: 130, type: 'leaf', mastery: 55, parent: 'python', desc: 'for/while · 薄弱点（range 参数）' },
  { id: 'func', label: '函数', x: 140, y: 30, type: 'leaf', mastery: 60, parent: 'python', desc: 'def 定义与调用 · 学习中' },
  // Arduino 叶子
  { id: 'led', label: 'LED', x: 330, y: 40, type: 'leaf', mastery: 90, parent: 'arduino', desc: '数字输出控制 · 已精通' },
  { id: 'sensor', label: '传感器', x: 330, y: 130, type: 'leaf', mastery: 70, parent: 'arduino', desc: '模拟读取 · 已掌握' },
  { id: 'servo', label: '舵机', x: 220, y: 30, type: 'leaf', mastery: 40, parent: 'arduino', desc: 'PWM 控制 · 入门' },
  // 机器学习 叶子
  { id: 'concept', label: 'ML 概念', x: 30, y: 280, type: 'leaf', mastery: 30, parent: 'ml', desc: '监督/无监督 · 入门' },
  { id: 'train', label: '模型训练', x: 140, y: 295, type: 'leaf', mastery: 20, parent: 'ml', desc: '训练流程 · 未开始' },
  // 电路 叶子
  { id: 'ohm', label: '欧姆定律', x: 330, y: 280, type: 'leaf', mastery: 65, parent: 'circuit', desc: 'V=IR · 已掌握' },
  { id: 'parallel', label: '串并联', x: 220, y: 295, type: 'leaf', mastery: 50, parent: 'circuit', desc: '电路组合 · 学习中' },
];

const edges = [
  { from: 'stem', to: 'python' }, { from: 'stem', to: 'arduino' },
  { from: 'stem', to: 'ml' }, { from: 'stem', to: 'circuit' },
  { from: 'python', to: 'var' }, { from: 'python', to: 'loop' }, { from: 'python', to: 'func' },
  { from: 'arduino', to: 'led' }, { from: 'arduino', to: 'sensor' }, { from: 'arduino', to: 'servo' },
  { from: 'ml', to: 'concept' }, { from: 'ml', to: 'train' },
  { from: 'circuit', to: 'ohm' }, { from: 'circuit', to: 'parallel' },
];

// 掌握度颜色
function masteryColor(m: number): string {
  if (m < 0) return 'bg-slate-400';
  if (m >= 70) return 'bg-green-500';
  if (m >= 40) return 'bg-yellow-500';
  return 'bg-red-400';
}
function masteryStroke(m: number): string {
  if (m < 0) return '#94a3b8';
  if (m >= 70) return '#22c55e';
  if (m >= 40) return '#eab308';
  return '#f87171';
}

export default function KnowledgeGraph({ onNavigate }: KnowledgeGraphProps) {
  const [selected, setSelected] = useState<string>('stem');
  const [hovered, setHovered] = useState<string | null>(null);

  const selectedNode = nodes.find((n) => n.id === selected) || nodes[0];
  // 高亮：选中节点的邻居 + 选中节点本身
  const highlightIds = new Set<string>();
  highlightIds.add(selected);
  edges.forEach((e) => {
    if (e.from === selected) highlightIds.add(e.to);
    if (e.to === selected) highlightIds.add(e.from);
  });
  if (hovered) {
    highlightIds.add(hovered);
    edges.forEach((e) => {
      if (e.from === hovered) highlightIds.add(e.to);
      if (e.to === hovered) highlightIds.add(e.from);
    });
  }

  const isDim = (id: string) => highlightIds.size > 1 && !highlightIds.has(id);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-slate-900">STEM 知识图谱</h2>

      {/* 图谱可视化 */}
      <div className="bg-slate-900 rounded-2xl relative overflow-hidden border border-slate-700">
        <svg viewBox="0 0 360 320" className="w-full h-72">
          {/* 连线 */}
          {edges.map((e, i) => {
            const from = nodes.find((n) => n.id === e.from)!;
            const to = nodes.find((n) => n.id === e.to)!;
            const active = e.from === selected || e.to === selected || e.from === hovered || e.to === hovered;
            return (
              <line
                key={i}
                x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                stroke={active ? '#6366f1' : '#334155'}
                strokeWidth={active ? 2 : 1}
                strokeDasharray={active ? '0' : '4 3'}
                className="transition-all"
              />
            );
          })}
          {/* 节点 */}
          {nodes.map((n) => {
            const r = n.type === 'center' ? 22 : n.type === 'branch' ? 16 : 11;
            const dim = isDim(n.id);
            const isSel = n.id === selected;
            return (
              <g
                key={n.id}
                onClick={() => setSelected(n.id)}
                onMouseEnter={() => setHovered(n.id)}
                onMouseLeave={() => setHovered(null)}
                className="cursor-pointer"
                style={{ opacity: dim ? 0.35 : 1, transition: 'opacity 0.2s' }}
              >
                <circle
                  cx={n.x} cy={n.y} r={r}
                  fill={n.type === 'center' ? 'url(#centerGrad)' : masteryStroke(n.mastery)}
                  stroke={isSel ? '#fff' : 'transparent'}
                  strokeWidth={isSel ? 2 : 0}
                />
                <text
                  x={n.x} y={n.y + r + 12}
                  textAnchor="middle"
                  fontSize={n.type === 'leaf' ? 8 : 10}
                  fill={isSel ? '#fff' : '#cbd5e1'}
                  fontWeight={n.type === 'center' || isSel ? 700 : 400}
                >
                  {n.label}
                </text>
                {n.mastery >= 0 && (
                  <text x={n.x} y={n.y + 3} textAnchor="middle" fontSize={8} fill="#fff" fontWeight={700}>
                    {n.mastery}
                  </text>
                )}
              </g>
            );
          })}
          <defs>
            <radialGradient id="centerGrad">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#6d28d9" />
            </radialGradient>
          </defs>
        </svg>

        {/* 图例 */}
        <div className="absolute top-2 left-2 flex flex-col gap-1 text-[9px] text-slate-300">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span>已掌握 ≥70%</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"></span>学习中 40-69%</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400"></span>薄弱 &lt;40%</span>
        </div>
      </div>

      {/* 选中节点详情 */}
      <motion.div
        key={selected}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-4 shadow-md border border-slate-100"
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${masteryColor(selectedNode.mastery)}`}></span>
            {selectedNode.label}
          </h3>
          {selectedNode.mastery >= 0 && (
            <span className={`text-xs font-bold ${selectedNode.mastery >= 70 ? 'text-green-600' : selectedNode.mastery >= 40 ? 'text-yellow-600' : 'text-red-500'}`}>
              掌握度 {selectedNode.mastery}%
            </span>
          )}
        </div>
        <p className="text-xs text-slate-600">{selectedNode.desc}</p>
        {selectedNode.mastery >= 0 && selectedNode.mastery < 70 && (
          <button
            onClick={() => onNavigate('每日挑战')}
            className="mt-3 w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold py-2 rounded-lg"
          >
            🚀 前往练习提升
          </button>
        )}
      </motion.div>

      {/* 分类入口 */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { name: '编程逻辑', icon: Code, color: 'from-blue-500 to-blue-600', count: 12 },
          { name: '硬件电路', icon: Cpu, color: 'from-green-500 to-green-600', count: 10 },
          { name: '物理原理', icon: Zap, color: 'from-orange-500 to-orange-600', count: 9 },
          { name: '工程设计', icon: Network, color: 'from-purple-500 to-purple-600', count: 8 },
        ].map((cat, i) => (
          <motion.div
            key={i}
            whileTap={{ scale: 0.98 }}
            className={`bg-gradient-to-br ${cat.color} rounded-xl p-4 text-white cursor-pointer`}
          >
            <cat.icon className="h-6 w-6 mb-2" />
            <h4 className="font-bold text-sm">{cat.name}</h4>
            <p className="text-[10px] opacity-80 mt-1">{cat.count} 个关联知识点</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
