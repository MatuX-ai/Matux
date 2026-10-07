'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Flame, Trophy, Star, Check, AlertCircle, Gift, CalendarCheck,
  Sparkles, Zap,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface StreakSystemProps {
  mode: DeviceMode;
}

// 里程碑配置
interface Milestone {
  days: number;
  reward: string;
  emoji: string;
  desc: string;
}

const milestones: Milestone[] = [
  { days: 3, reward: '+30 积分', emoji: '🎯', desc: '新手起步' },
  { days: 7, reward: '+70 积分 + 徽章', emoji: '🔥', desc: '一周坚持' },
  { days: 14, reward: '+150 积分 + 限定皮肤', emoji: '⭐', desc: '两周突破' },
  { days: 30, reward: '+500 积分 + 实物奖品', emoji: '🏆', desc: '月度冠军' },
  { days: 60, reward: '+1200 积分', emoji: '💎', desc: '双月传奇' },
  { days: 100, reward: '+2500 积分 + 限定', emoji: '👑', desc: '百日王者' },
];

// 本月签到数据：1=已签, 0=未签, -1=未来日期
const initialCalendar: number[] = (() => {
  const today = 16; // 模拟今天是 16 号
  const signedDays = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]; // 已签到日期（8 号断了）
  return Array.from({ length: 31 }, (_, i) => {
    const day = i + 1;
    if (day > today) return -1; // 未来
    if (signedDays.includes(day)) return 1; // 已签
    return 0; // 未签（可补签）
  });
})();

export function StreakSystem({ mode }: StreakSystemProps) {
  const isPhone = mode === 'phone';
  const TODAY = 16;

  // ============ 状态 ============
  const [calendar, setCalendar] = useState<number[]>(initialCalendar);
  const [streakDays, setStreakDays] = useState(7); // 当前连胜 7 天（14号签了，15号签了，16号待签）
  const [maxStreak, setMaxStreak] = useState(21); // 历史最高
  const [makeupCards, setMakeupCards] = useState(3); // 补签卡
  const [signing, setSigning] = useState(false);
  const [rewardModal, setRewardModal] = useState<Milestone | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);

  // 已签到天数
  const signedCount = useMemo(() => calendar.filter(v => v === 1).length, [calendar]);
  // 今天是否已签
  const signedToday = calendar[TODAY - 1] === 1;
  // 当前里程碑
  const currentMilestone = useMemo(() => {
    const achieved = milestones.filter(m => streakDays >= m.days);
    const next = milestones.find(m => streakDays < m.days);
    return {
      current: achieved[achieved.length - 1] || null,
      next,
    };
  }, [streakDays]);

  // ============ Toast ============
  const showToast = (type: 'success' | 'error' | 'info', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 2500);
  };

  // ============ 里程碑检测 ============
  const checkMilestone = (newStreak: number) => {
    const milestone = milestones.find(m => m.days === newStreak);
    if (milestone) {
      setTimeout(() => setRewardModal(milestone), 800);
    }
  };

  // ============ 每日签到 ============
  const handleSignIn = () => {
    if (signedToday) {
      showToast('info', '今天已经签到过了');
      return;
    }
    setSigning(true);

    setTimeout(() => {
      setCalendar(prev => {
        const next = [...prev];
        next[TODAY - 1] = 1;
        return next;
      });
      const newStreak = streakDays + 1;
      setStreakDays(newStreak);
      if (newStreak > maxStreak) setMaxStreak(newStreak);
      setSigning(false);
      showToast('success', `签到成功！连胜 ${newStreak} 天 🔥`);
      checkMilestone(newStreak);
    }, 1000);
  };

  // ============ 补签 ============
  const handleMakeup = (day: number) => {
    if (day >= TODAY) {
      showToast('info', '只能补签过去的日期');
      return;
    }
    if (calendar[day - 1] === 1) {
      showToast('info', '该日期已签到');
      return;
    }
    if (makeupCards <= 0) {
      showToast('error', '补签卡已用完，请去积分商城兑换');
      return;
    }

    setCalendar(prev => {
      const next = [...prev];
      next[day - 1] = 1;
      return next;
    });
    setMakeupCards(prev => prev - 1);

    // 检查补签后是否形成新的连续（简化：如果补的是断点，连胜 +1）
    // 这里简化处理，实际应重新计算连续天数
    showToast('success', `补签成功！${day} 号已签到（剩余 ${makeupCards - 1} 张补签卡）`);
  };

  // ============ Toast 组件 ============
  const Toast = () => (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: '-50%' }}
          animate={{ opacity: 1, y: 0, x: '-50%' }}
          exit={{ opacity: 0, y: -20, x: '-50%' }}
          className={`fixed top-6 left-1/2 z-[60] flex items-center gap-2 px-5 py-3 rounded-xl shadow-2xl text-sm font-medium text-white ${
            toast.type === 'success' ? 'bg-green-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
          }`}
        >
          {toast.type === 'success' ? <Check className="h-4 w-4" /> : toast.type === 'error' ? <AlertCircle className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
          {toast.msg}
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ============ 里程碑奖励弹窗 ============
  const RewardModal = () => (
    <AnimatePresence>
      {rewardModal && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setRewardModal(null)}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.5, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0.5, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl w-full max-w-sm p-8 text-center shadow-2xl relative overflow-hidden"
          >
            {/* 背景光效 */}
            <div className="absolute inset-0 bg-gradient-to-br from-orange-100 via-yellow-50 to-transparent pointer-events-none" />

            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
              className="relative inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-orange-400 to-red-500 mb-4 shadow-lg"
            >
              <span className="text-5xl">{rewardModal.emoji}</span>
              <motion.div
                initial={{ scale: 1, opacity: 0.5 }}
                animate={{ scale: 1.5, opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="absolute inset-0 rounded-full bg-orange-400"
              />
            </motion.div>

            <h3 className="relative text-2xl font-bold text-slate-900 mb-2">
              🎉 里程碑达成！
            </h3>
            <p className="relative text-lg font-semibold text-orange-600 mb-1">
              {rewardModal.days} 天连胜
            </p>
            <p className="relative text-sm text-slate-500 mb-4">{rewardModal.desc}</p>

            <div className="relative bg-orange-50 rounded-xl p-4 mb-5">
              <div className="flex items-center justify-center gap-2 text-orange-700">
                <Gift className="h-5 w-5" />
                <span className="font-bold">{rewardModal.reward}</span>
              </div>
            </div>

            <button
              onClick={() => setRewardModal(null)}
              className="relative w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-semibold text-sm hover:shadow-lg transition-all"
            >
              领取奖励
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ============ 签到日历格子 ============
  const CalendarCell = ({ day }: { day: number }) => {
    const state = calendar[day - 1];
    const isToday = day === TODAY;
    const isFuture = state === -1;
    const isSigned = state === 1;
    const canMakeup = !isSigned && !isFuture && !isToday && makeupCards > 0;

    if (isFuture) {
      return (
        <div className={`aspect-square rounded-lg flex items-center justify-center text-sm bg-slate-50 text-slate-300 ${isPhone ? '' : 'cursor-not-allowed'}`}>
          {day}
        </div>
      );
    }

    return (
      <motion.div
        whileHover={canMakeup || isToday ? { scale: 1.1 } : undefined}
        whileTap={canMakeup || (isToday && !signedToday) ? { scale: 0.95 } : undefined}
        onClick={() => {
          if (isToday && !signedToday) { handleSignIn(); return; }
          if (canMakeup) handleMakeup(day);
        }}
        className={`aspect-square rounded-lg flex items-center justify-center text-sm font-medium relative ${
          isSigned
            ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white font-bold shadow-md'
            : isToday
              ? signedToday
                ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white font-bold'
                : 'bg-blue-100 text-blue-600 border-2 border-blue-500 font-bold cursor-pointer animate-pulse'
              : canMakeup
                ? 'bg-slate-100 text-slate-500 hover:bg-blue-50 hover:border-blue-300 border-2 border-dashed border-slate-300 cursor-pointer'
                : 'bg-slate-100 text-slate-400'
        }`}
      >
        {isSigned ? (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring' }}
          >
            ✓
          </motion.span>
        ) : canMakeup ? (
          <span className="text-[9px] text-blue-400">补签</span>
        ) : (
          day
        )}
        {isToday && !signedToday && (
          <motion.div
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full"
          />
        )}
      </motion.div>
    );
  };

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="px-5 space-y-4">
        <Toast />
        <RewardModal />

        {/* 当前连胜 */}
        <motion.div
          key={streakDays}
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          className="bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-5 text-white text-center"
        >
          <motion.div
            animate={signedToday ? {} : { rotate: [0, -10, 10, -10, 0] }}
            transition={{ duration: 0.5, repeat: signedToday ? 0 : Infinity, repeatDelay: 2 }}
          >
            <Flame className={`h-12 w-12 mx-auto mb-2 ${signedToday ? '' : 'animate-pulse'}`} />
          </motion.div>
          <div className="text-4xl font-bold mb-1">{streakDays}</div>
          <div className="text-sm opacity-90 mb-3">天连续学习</div>
          <div className="flex justify-center gap-2 text-xs">
            <span className="bg-white/20 px-3 py-1 rounded-full">
              {signedToday ? '✓ 今日已签' : '🔥 待签到'}
            </span>
            <span className="bg-white/20 px-3 py-1 rounded-full">历史最高 {maxStreak} 天</span>
          </div>
        </motion.div>

        {/* 签到按钮 */}
        {!signedToday && (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleSignIn}
            disabled={signing}
            className="w-full py-3.5 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg disabled:opacity-70"
          >
            {signing ? (
              <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> 签到中...</>
            ) : (
              <><CalendarCheck className="h-5 w-5" /> 立即签到</>
            )}
          </motion.button>
        )}

        {/* 本周签到 */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
            <CalendarCheck className="h-4 w-4 text-orange-500" />
            本月签到日历
            <span className="ml-auto text-xs text-slate-400">{signedCount}/16 天</span>
          </h3>
          <div className="bg-white rounded-xl border p-3">
            <div className="grid grid-cols-7 gap-1.5 mb-2">
              {['一', '二', '三', '四', '五', '六', '日'].map((d, i) => (
                <div key={i} className="text-center text-[9px] text-slate-400 font-medium">周{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1.5">
              {Array.from({ length: 31 }, (_, i) => (
                <CalendarCell key={i} day={i + 1} />
              ))}
            </div>
          </div>
        </div>

        {/* 补签卡 */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Zap className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <div className="text-xs font-bold text-blue-900">补签卡</div>
              <div className="text-[10px] text-blue-600">点击日历中未签到日期使用</div>
            </div>
          </div>
          <span className="text-lg font-bold text-blue-700">{makeupCards}<span className="text-xs">/3</span></span>
        </div>

        {/* 里程碑 */}
        <div>
          <h3 className="font-bold text-slate-900 text-base mb-3 flex items-center gap-2">
            <Trophy className="h-4 w-4 text-orange-500" />
            连胜里程碑
          </h3>
          <div className="space-y-2">
            {milestones.slice(0, 4).map((m) => {
              const achieved = streakDays >= m.days;
              const isCurrent = currentMilestone.current?.days === m.days;
              return (
                <div
                  key={m.days}
                  className={`bg-white rounded-xl p-3 border flex items-center gap-3 transition-all ${
                    isCurrent ? 'border-orange-500 bg-orange-50' : ''
                  } ${achieved && !isCurrent ? 'opacity-75' : ''}`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl ${
                    achieved ? 'bg-orange-100' : 'bg-slate-100 grayscale'
                  }`}>
                    {m.emoji}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <h4 className="text-xs font-bold">{m.days} 天连胜</h4>
                      {isCurrent && (
                        <span className="text-[9px] bg-orange-500 text-white px-2 py-0.5 rounded-full">当前</span>
                      )}
                      {!achieved && currentMilestone.next?.days === m.days && (
                        <span className="text-[9px] bg-blue-500 text-white px-2 py-0.5 rounded-full">下一目标</span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-600">{m.reward}</p>
                  </div>
                  {achieved && (
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <Check className="h-3 w-3 text-white" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 小贴士 */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <h4 className="font-bold text-sm text-blue-900 mb-2 flex items-center gap-2">
            <Star className="h-4 w-4" /> 连胜小贴士
          </h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>✓ 每天完成任意课程即可保持连胜</li>
            <li>✓ 中断后可用补签卡补救（每月 3 次）</li>
            <li>✓ 连胜天数越高，奖励越丰厚</li>
          </ul>
        </div>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-6">
      <Toast />
      <RewardModal />

      {/* 连胜概览 */}
      <motion.div
        key={streakDays}
        initial={{ scale: 0.98 }}
        animate={{ scale: 1 }}
        className="bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-8 text-white"
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <motion.div
                animate={signedToday ? {} : { rotate: [0, -10, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: signedToday ? 0 : Infinity, repeatDelay: 2 }}
              >
                <Flame className={`h-16 w-16 ${signedToday ? '' : 'animate-pulse'}`} />
              </motion.div>
              <div>
                <p className="text-orange-100 text-sm mb-1">当前连胜</p>
                <h2 className="text-6xl font-bold">{streakDays} 天</h2>
              </div>
            </div>
            <div className="flex gap-4 text-sm">
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">签到状态</div>
                <div className="font-bold">{signedToday ? '✓ 今日已签' : '待签到'}</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">历史最高</div>
                <div className="font-bold">{maxStreak} 天</div>
              </div>
              <div className="bg-white/20 backdrop-blur px-4 py-2 rounded-lg">
                <div className="text-orange-100 text-xs mb-1">本月签到</div>
                <div className="font-bold">{signedCount} 天</div>
              </div>
            </div>
          </div>
          <Trophy className="h-32 w-32 opacity-20" />
        </div>

        {/* 签到按钮 */}
        {!signedToday && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSignIn}
            disabled={signing}
            className="mt-6 px-8 py-3 bg-white text-orange-600 rounded-xl font-bold text-base flex items-center gap-2 shadow-lg disabled:opacity-70"
          >
            {signing ? (
              <><span className="w-5 h-5 border-2 border-orange-200 border-t-orange-600 rounded-full animate-spin" /> 签到中...</>
            ) : (
              <><CalendarCheck className="h-5 w-5" /> 立即签到</>
            )}
          </motion.button>
        )}
      </motion.div>

      {/* 月度日历 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <CalendarCheck className="h-5 w-5 text-orange-600" />
            本月签到日历
          </h3>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 px-4 py-2 rounded-xl">
              <Zap className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">补签卡: {makeupCards}/3</span>
            </div>
            <span className="text-sm text-slate-500">已签 {signedCount} 天</span>
          </div>
        </div>
        <div className="bg-white rounded-2xl border p-6">
          <div className="grid grid-cols-7 gap-3 mb-3">
            {['一', '二', '三', '四', '五', '六', '日'].map((d, i) => (
              <div key={i} className="text-center text-xs font-medium text-slate-500">周{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-3">
            {Array.from({ length: 31 }, (_, i) => (
              <CalendarCell key={i} day={i + 1} />
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-6 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded bg-gradient-to-br from-orange-500 to-red-500"></div>
              已签到
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded bg-blue-100 border-2 border-blue-500"></div>
              今日待签
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded bg-slate-100 border-2 border-dashed border-slate-300"></div>
              可补签
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded bg-slate-50"></div>
              未来日期
            </div>
          </div>
        </div>
      </div>

      {/* 里程碑 */}
      <div>
        <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-orange-600" />
          连胜里程碑
        </h3>
        <div className="grid grid-cols-3 gap-5">
          {milestones.map((m) => {
            const achieved = streakDays >= m.days;
            const isCurrent = currentMilestone.current?.days === m.days;
            const isNext = currentMilestone.next?.days === m.days;
            return (
              <motion.div
                key={m.days}
                whileHover={{ y: -4 }}
                className={`bg-white rounded-2xl p-5 border text-center relative transition-all ${
                  isCurrent ? 'border-orange-500 shadow-lg' : 'border-slate-100'
                } ${achieved && !isCurrent ? 'opacity-75' : ''}`}
              >
                {isCurrent && (
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-orange-500 text-white text-[10px] px-3 py-1 rounded-full font-bold">
                    当前目标
                  </div>
                )}
                {isNext && !achieved && (
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white text-[10px] px-3 py-1 rounded-full font-bold">
                    下一目标
                  </div>
                )}
                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mx-auto mb-3 ${
                  achieved ? 'bg-gradient-to-br from-orange-100 to-red-100' : 'bg-slate-100 grayscale'
                }`}>
                  {m.emoji}
                </div>
                <h4 className="font-bold text-slate-900 mb-1">{m.days} 天</h4>
                <p className="text-xs text-slate-600 mb-2">{m.desc}</p>
                <p className="text-sm font-semibold text-orange-600">{m.reward}</p>
                {achieved && (
                  <div className="mt-3 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mx-auto">
                    <Check className="h-4 w-4 text-white" />
                  </div>
                )}
                {/* 进度条（下一个目标） */}
                {isNext && !achieved && (
                  <div className="mt-3">
                    <div className="text-[10px] text-slate-400 mb-1">
                      进度 {streakDays}/{m.days}
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(streakDays / m.days) * 100}%` }}
                        transition={{ duration: 0.8 }}
                        className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full"
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* 规则说明 */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-6">
        <h4 className="font-bold text-indigo-900 mb-3 flex items-center gap-2">
          <Star className="h-5 w-5" /> 连胜规则说明
        </h4>
        <div className="grid grid-cols-2 gap-4 text-sm text-indigo-800">
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">如何保持连胜</div>
              <div className="text-xs opacity-80 mt-1">每天完成任意课程、项目或挑战即可</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">中断后果</div>
              <div className="text-xs opacity-80 mt-1">连续 2 天未学习将重置为 0 天</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">奖励发放</div>
              <div className="text-xs opacity-80 mt-1">达到里程碑自动发放积分和道具</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-lg">✓</span>
            <div>
              <div className="font-semibold">补签功能</div>
              <div className="text-xs opacity-80 mt-1">每月 3 次补签卡，点击日历补签</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
