'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Share2, Download, Shield, X, Check, Sparkles, Trophy,
} from 'lucide-react';

interface AchievementDetailProps {
  onNavigate?: (page: string) => void;
}

// ============ 徽章类型 ============
type Rarity = 'common' | 'rare' | 'epic' | 'legendary';
type Category = 'learning' | 'project' | 'streak' | 'social' | 'special';

interface Condition {
  text: string;
  done: boolean;
}

interface Badge {
  id: number;
  name: string;
  emoji: string;
  category: Category;
  rarity: Rarity;
  unlocked: boolean;
  date?: string;
  desc: string;
  conditions: Condition[];
  progress?: { current: number; total: number }; // 未解锁时的进度
  txHash?: string;
}

// ============ 徽章数据 ============
const badges: Badge[] = [
  {
    id: 1, name: 'STEM 探索者', emoji: '🔬', category: 'learning', rarity: 'epic',
    unlocked: true, date: '2026-05-05',
    desc: '完成 5 个不同类别的实验项目，展现了广泛的学习兴趣和动手能力。',
    conditions: [
      { text: '完成 5 个不同类别的实验项目', done: true },
      { text: '累计学习时长超过 20 小时', done: true },
      { text: '在社区分享至少 3 篇作品心得', done: true },
    ],
    txHash: '0x7f8a...3b2c',
  },
  {
    id: 2, name: '编程新星', emoji: '⭐', category: 'learning', rarity: 'common',
    unlocked: true, date: '2026-02-10',
    desc: '完成第一节 Python 编程课，迈出代码学习第一步。',
    conditions: [
      { text: '完成「Python 编程基础」第 1 章', done: true },
    ],
    txHash: '0xa1b2...c3d4',
  },
  {
    id: 3, name: '循环大师', emoji: '🔄', category: 'learning', rarity: 'rare',
    unlocked: true, date: '2026-04-28',
    desc: '掌握 for 和 while 循环，循环相关练习正确率达 75% 以上。',
    conditions: [
      { text: '完成 for/while 循环所有课程', done: true },
      { text: '循环练习正确率 ≥ 75%', done: true },
    ],
    txHash: '0xe5f6...7890',
  },
  {
    id: 4, name: '硬件达人', emoji: '🔧', category: 'project', rarity: 'rare',
    unlocked: true, date: '2026-03-15',
    desc: '独立完成首个硬件项目，学会使用传感器和执行器。',
    conditions: [
      { text: '完成「智能感应小夜灯」项目', done: true },
      { text: '提交实验报告', done: true },
    ],
    txHash: '0x1234...5678',
  },
  {
    id: 5, name: '百日坚持', emoji: '🔥', category: 'streak', rarity: 'legendary',
    unlocked: true, date: '2026-05-15',
    desc: '连续学习 100 天，展现了非凡的毅力和自律精神。',
    conditions: [
      { text: '连续签到 100 天', done: true },
    ],
    txHash: '0x9876...5432',
  },
  {
    id: 6, name: '一周不懈', emoji: '💪', category: 'streak', rarity: 'common',
    unlocked: true, date: '2026-02-06',
    desc: '连续学习 7 天，养成学习好习惯。',
    conditions: [
      { text: '连续签到 7 天', done: true },
    ],
  },
  {
    id: 7, name: '社区贡献者', emoji: '🤝', category: 'social', rarity: 'rare',
    unlocked: true, date: '2026-04-20',
    desc: '在社区分享 5 篇作品心得，帮助其他同学学习。',
    conditions: [
      { text: '分享 5 篇作品心得', done: true },
      { text: '获得 20 个点赞', done: true },
    ],
  },
  {
    id: 8, name: 'AI 对话高手', emoji: '🤖', category: 'learning', rarity: 'common',
    unlocked: true, date: '2026-03-01',
    desc: '与 AI 教师进行 50 次有效对话，善于提问和思考。',
    conditions: [
      { text: '与 AI 教师对话 50 次', done: true },
    ],
  },
  {
    id: 9, name: 'Blockly 通关者', emoji: '🧩', category: 'learning', rarity: 'rare',
    unlocked: false,
    desc: '完成所有 Blockly 可视化编程关卡，掌握编程逻辑基础。',
    conditions: [
      { text: '完成 10/15 个 Blockly 关卡', done: false },
      { text: '获得 3 星评价 ≥ 8 关', done: false },
    ],
    progress: { current: 7, total: 15 },
  },
  {
    id: 10, name: '电路实验家', emoji: '⚡', category: 'project', rarity: 'epic',
    unlocked: false,
    desc: '完成 10 个电路虚拟实验，深入理解电子电路原理。',
    conditions: [
      { text: '完成 10 个电路实验', done: false },
      { text: '至少 3 个实验获得满分', done: false },
    ],
    progress: { current: 4, total: 10 },
  },
  {
    id: 11, name: '知识分享家', emoji: '📝', category: 'social', rarity: 'epic',
    unlocked: false,
    desc: '在社区发布 20 篇高质量学习笔记，成为大家的学习榜样。',
    conditions: [
      { text: '发布 20 篇学习笔记', done: false },
      { text: '总阅读量超过 1000', done: false },
    ],
    progress: { current: 8, total: 20 },
  },
  {
    id: 12, name: '年度学霸', emoji: '👑', category: 'special', rarity: 'legendary',
    unlocked: false,
    desc: '全年学习时长超过 500 小时，成为 MatuX 平台年度学霸！',
    conditions: [
      { text: '年学习时长 ≥ 500 小时', done: false },
      { text: '完成 ≥ 30 门课程', done: false },
    ],
    progress: { current: 187, total: 500 },
  },
];

// ============ 分类配置 ============
const categories: { key: Category | 'all'; label: string; icon: string }[] = [
  { key: 'all', label: '全部', icon: '🎯' },
  { key: 'learning', label: '学习', icon: '📚' },
  { key: 'project', label: '项目', icon: '🛠️' },
  { key: 'streak', label: '连胜', icon: '🔥' },
  { key: 'social', label: '社交', icon: '🤝' },
  { key: 'special', label: '特殊', icon: '👑' },
];

// ============ 稀有度配置 ============
const rarityConfig: Record<Rarity, { label: string; color: string; bg: string; border: string; glow: string }> = {
  common: { label: '普通', color: 'text-slate-600', bg: 'bg-slate-100', border: 'border-slate-200', glow: '' },
  rare: { label: '稀有', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', glow: 'shadow-blue-200' },
  epic: { label: '史诗', color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200', glow: 'shadow-purple-200' },
  legendary: { label: '传说', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', glow: 'shadow-amber-300' },
};

export default function AchievementDetail(_: AchievementDetailProps) {
  const [activeCategory, setActiveCategory] = useState<Category | 'all'>('all');
  const [selectedBadge, setSelectedBadge] = useState<Badge | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  };

  // 过滤徽章
  const filteredBadges = useMemo(() => {
    return activeCategory === 'all'
      ? badges
      : badges.filter(b => b.category === activeCategory);
  }, [activeCategory]);

  // 统计
  const stats = useMemo(() => {
    const unlocked = badges.filter(b => b.unlocked).length;
    const byRarity = (r: Rarity) => badges.filter(b => b.unlocked && b.rarity === r).length;
    return {
      unlocked,
      total: badges.length,
      rate: Math.round((unlocked / badges.length) * 100),
      legendary: byRarity('legendary'),
      epic: byRarity('epic'),
      rare: byRarity('rare'),
      common: byRarity('common'),
    };
  }, []);

  return (
    <div className="space-y-5 pb-8">
      <h2 className="text-xl font-bold text-slate-900">学习成就</h2>

      {/* ============ 统计卡片 ============ */}
      <div className="bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl p-4 text-white relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-xs opacity-80">已获得徽章</div>
              <div className="text-3xl font-bold">{stats.unlocked}<span className="text-lg opacity-70">/{stats.total}</span></div>
            </div>
            <div className="text-right">
              <div className="text-xs opacity-80">完成度</div>
              <div className="text-2xl font-bold">{stats.rate}%</div>
            </div>
          </div>
          {/* 进度条 */}
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${stats.rate}%` }}
              transition={{ duration: 0.8, type: 'spring' }}
              className="h-full bg-white rounded-full"
            />
          </div>
          {/* 稀有度统计 */}
          <div className="flex gap-3 mt-3 text-[10px]">
            <span className="flex items-center gap-1">👑 {stats.legendary}</span>
            <span className="flex items-center gap-1">💎 {stats.epic}</span>
            <span className="flex items-center gap-1">🔵 {stats.rare}</span>
            <span className="flex items-center gap-1">⚪ {stats.common}</span>
          </div>
        </div>
        <Trophy className="absolute -bottom-4 -right-4 h-28 w-28 opacity-15" />
      </div>

      {/* ============ 分类筛选 ============ */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {categories.map((cat) => (
          <motion.button
            key={cat.key}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveCategory(cat.key)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeCategory === cat.key
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-500 border border-slate-200'
            }`}
          >
            <span className="mr-1">{cat.icon}</span>{cat.label}
          </motion.button>
        ))}
      </div>

      {/* ============ 徽章网格 ============ */}
      <div className="grid grid-cols-3 gap-3">
        {filteredBadges.map((badge, i) => {
          const rc = rarityConfig[badge.rarity];
          return (
            <motion.button
              key={badge.id}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.04 }}
              whileTap={{ scale: 0.92 }}
              onClick={() => setSelectedBadge(badge)}
              className={`relative aspect-square rounded-2xl border-2 ${rc.border} ${rc.bg} flex flex-col items-center justify-center p-2 ${
                badge.unlocked ? `shadow-md ${rc.glow}` : 'opacity-60'
              }`}
            >
              {/* 稀有度标记 */}
              <div className={`absolute top-1 right-1 text-[8px] px-1 py-0.5 rounded-full ${rc.bg} ${rc.color} font-bold`}>
                {rc.label}
              </div>

              {/* 徽章图标 */}
              <div className={`text-3xl mb-1 ${badge.unlocked ? '' : 'grayscale'}`}>
                {badge.unlocked ? badge.emoji : '🔒'}
              </div>

              {/* 名称 */}
              <div className={`text-[10px] font-bold text-center leading-tight ${badge.unlocked ? 'text-slate-700' : 'text-slate-400'}`}>
                {badge.name}
              </div>

              {/* 未解锁进度 */}
              {!badge.unlocked && badge.progress && (
                <div className="absolute bottom-1 left-1 right-1">
                  <div className="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-slate-400 rounded-full"
                      style={{ width: `${(badge.progress.current / badge.progress.total) * 100}%` }}
                    />
                  </div>
                  <div className="text-[8px] text-slate-400 text-center mt-0.5">
                    {badge.progress.current}/{badge.progress.total}
                  </div>
                </div>
              )}

              {/* 传说徽章特效 */}
              {badge.unlocked && badge.rarity === 'legendary' && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                  className="absolute inset-0 rounded-2xl pointer-events-none"
                  style={{
                    background: 'conic-gradient(from 0deg, transparent, rgba(251,191,36,0.3), transparent)',
                  }}
                />
              )}
            </motion.button>
          );
        })}
      </div>

      {/* ============ 徽章详情弹窗 ============ */}
      <AnimatePresence>
        {selectedBadge && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedBadge(null)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.7, y: 30 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.7, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl w-full max-w-sm max-h-[85vh] overflow-y-auto shadow-2xl"
            >
              {/* 头部渐变背景 */}
              <div className={`relative p-6 text-center ${
                selectedBadge.unlocked
                  ? selectedBadge.rarity === 'legendary'
                    ? 'bg-gradient-to-br from-amber-400 to-orange-500'
                    : selectedBadge.rarity === 'epic'
                      ? 'bg-gradient-to-br from-purple-500 to-indigo-600'
                      : selectedBadge.rarity === 'rare'
                        ? 'bg-gradient-to-br from-blue-500 to-cyan-500'
                        : 'bg-gradient-to-br from-slate-400 to-slate-500'
                  : 'bg-gradient-to-br from-slate-300 to-slate-400'
              } rounded-t-3xl`}>
                <button
                  onClick={() => setSelectedBadge(null)}
                  className="absolute top-3 right-3 w-8 h-8 bg-white/20 backdrop-blur rounded-full flex items-center justify-center text-white"
                >
                  <X className="h-4 w-4" />
                </button>

                {/* 徽章图标 */}
                <motion.div
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: 'spring', stiffness: 200, delay: 0.1 }}
                  className="w-24 h-24 bg-white/20 backdrop-blur rounded-full flex items-center justify-center mx-auto mb-3 border-2 border-white/40"
                >
                  <span className="text-5xl">{selectedBadge.unlocked ? selectedBadge.emoji : '🔒'}</span>
                </motion.div>

                <h3 className="text-xl font-bold text-white">{selectedBadge.name}</h3>
                <div className="inline-block mt-1 px-2 py-0.5 bg-white/20 rounded-full text-[10px] text-white font-medium">
                  {rarityConfig[selectedBadge.rarity].label} · {categories.find(c => c.key === selectedBadge.category)?.label}
                </div>
                {selectedBadge.unlocked && selectedBadge.date && (
                  <p className="text-xs text-white/80 mt-2">获得于 {selectedBadge.date}</p>
                )}
              </div>

              {/* 内容区 */}
              <div className="p-5 space-y-4">
                {/* 描述 */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-1">描述</h4>
                  <p className="text-sm text-slate-700 leading-relaxed">{selectedBadge.desc}</p>
                </div>

                {/* 获得条件 */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">
                    {selectedBadge.unlocked ? '获得条件' : '解锁条件'}
                  </h4>
                  <ul className="space-y-2">
                    {selectedBadge.conditions.map((cond, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        {cond.done ? (
                          <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Check className="h-3 w-3 text-green-600" />
                          </div>
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-slate-300 flex-shrink-0 mt-0.5"></div>
                        )}
                        <span className={cond.done ? 'text-slate-700' : 'text-slate-400'}>
                          {cond.text}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 进度（未解锁时） */}
                {!selectedBadge.unlocked && selectedBadge.progress && (
                  <div className="bg-slate-50 rounded-xl p-3">
                    <div className="flex justify-between text-xs mb-2">
                      <span className="text-slate-500">当前进度</span>
                      <span className="font-bold text-slate-700">
                        {selectedBadge.progress.current} / {selectedBadge.progress.total}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(selectedBadge.progress.current / selectedBadge.progress.total) * 100}%` }}
                        transition={{ duration: 0.6 }}
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                      />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2">
                      还差 {selectedBadge.progress.total - selectedBadge.progress.current} 步即可解锁
                    </p>
                  </div>
                )}

                {/* 区块链认证（已解锁时） */}
                {selectedBadge.unlocked && selectedBadge.txHash && (
                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                    <div className="flex items-center gap-2 text-slate-600 mb-1">
                      <Shield className="h-3.5 w-3.5" />
                      <span className="text-xs font-bold">区块链认证</span>
                    </div>
                    <p className="text-[10px] text-slate-400 break-all font-mono">TxHash: {selectedBadge.txHash}</p>
                  </div>
                )}

                {/* 操作按钮 */}
                {selectedBadge.unlocked ? (
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => { showToast('成就已分享到社区'); }}
                      className="bg-purple-100 text-purple-700 py-2.5 rounded-xl font-bold text-sm flex items-center justify-center gap-1.5"
                    >
                      <Share2 className="h-4 w-4" /> 分享
                    </motion.button>
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={() => { showToast('证书已下载（演示）'); }}
                      className="bg-indigo-100 text-indigo-700 py-2.5 rounded-xl font-bold text-sm flex items-center justify-center gap-1.5"
                    >
                      <Download className="h-4 w-4" /> 证书
                    </motion.button>
                  </div>
                ) : (
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => {
                      showToast('继续学习以解锁此徽章！');
                      setSelectedBadge(null);
                    }}
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2.5 rounded-xl font-bold text-sm flex items-center justify-center gap-1.5"
                  >
                    <Sparkles className="h-4 w-4" /> 去解锁
                  </motion.button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ============ Toast ============ */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 30, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 30, x: '-50%' }}
            className="fixed bottom-24 left-1/2 z-[60] px-4 py-2 rounded-full text-xs font-medium shadow-lg bg-slate-800 text-white flex items-center gap-1.5"
          >
            <Check className="h-3.5 w-3.5" /> {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
