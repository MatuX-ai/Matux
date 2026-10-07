'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Zap, Clock, Award, Check, X, Lightbulb, Code2,
  Trophy, Flame, Target, RefreshCw, Share2, ChevronRight,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface DailyChallengePageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// ============ 调试日志 ============
const DEBUG = false; // 上线时设为 false 关闭日志
const log = (tag: string, ...args: unknown[]) => {
  if (DEBUG) {
    const colors: Record<string, string> = {
      Phase: '#6366f1', Timer: '#10b981', Submit: '#f59e0b',
      Step: '#3b82f6', Hint: '#8b5cf6', Grade: '#ec4899',
    };
    console.log(`%c[DailyChallenge][${tag}]`, `color:${colors[tag] || '#6366f1'};font-weight:bold`, ...args);
  }
};

// ============ 类型 ============
type Phase = 'intro' | 'taking' | 'result';

interface ChallengeStep {
  id: number;
  text: string;
  done: boolean;
}

interface ChallengeData {
  title: string;
  desc: string;
  difficulty: '初级' | '中级' | '高级';
  timeLimitSec: number;
  basePoints: number;
  steps: string[];
  hints: string[];
  starterCode: string;
  keywords: string[]; // 评分用：代码中应出现的关键字
}

// ============ 模拟数据 ============
const challengeData: ChallengeData = {
  title: 'PWM 舵机控制',
  desc: '使用 PWM 信号控制舵机在 0° 到 180° 之间平滑转动，并通过串口输出当前角度。',
  difficulty: '中级',
  timeLimitSec: 600, // 10 分钟
  basePoints: 50,
  steps: [
    '初始化 PWM 引脚（如 GPIO 13），设置频率 50Hz',
    '编写函数将角度（0-180）映射为占空比（20-120）',
    '实现 0° → 180° → 0° 的平滑往返转动',
    '通过 print() 输出当前角度值到串口',
  ],
  hints: [
    '舵机控制周期为 20ms（50Hz），占空比范围约 2.5%-12.5% 对应 0°-180°',
    '可以使用 machine.PWM(pin) 创建 PWM 对象，duty() 方法设置占空比',
    '平滑转动：在循环中每次增加 1° 并 sleep(0.02)，避免突然跳变',
  ],
  starterCode: `from machine import Pin, PWM
import time

# TODO: 初始化 PWM 引脚
# servo = PWM(Pin(13), freq=50)

# TODO: 编写角度映射函数
# def angle_to_duty(angle):
#     return ...

# TODO: 实现平滑转动
`,
  keywords: ['PWM', 'Pin', 'freq', 'duty', 'angle', 'for', 'range', 'print', 'sleep'],
};

// 模拟最近 7 天的挑战记录（用于连胜日历）
const streakHistory = [
  { day: '周一', date: '06-22', status: 'completed', score: 92 },
  { day: '周二', date: '06-23', status: 'completed', score: 85 },
  { day: '周三', date: '06-24', status: 'completed', score: 78 },
  { day: '周四', date: '06-25', status: 'failed', score: 0 },
  { day: '周五', date: '06-26', status: 'completed', score: 95 },
  { day: '周六', date: '06-27', status: 'completed', score: 88 },
  { day: '今天', date: '06-29', status: 'pending', score: 0 },
];

export function DailyChallengePage({ mode, onBack }: DailyChallengePageProps) {
  const isPhone = mode === 'phone';

  // ============ 状态 ============
  const [phase, setPhase] = useState<Phase>('intro');
  const [timeLeft, setTimeLeft] = useState(challengeData.timeLimitSec);
  const [steps, setSteps] = useState<ChallengeStep[]>(
    challengeData.steps.map((text, i) => ({ id: i, text, done: false }))
  );
  const [code, setCode] = useState(challengeData.starterCode);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [showHint, setShowHint] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    score: number;
    timeUsed: number;
    feedback: string;
    rewards: { points: number; streak: number; badge: string | null };
  } | null>(null);

  // ============ Refs（稳定闭包） ============
  const phaseRef = useRef(phase);
  const submittedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { phaseRef.current = phase; }, [phase]);

  // ============ 倒计时 ============
  useEffect(() => {
    if (phase !== 'taking') return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          log('Timer', '时间到，自动提交');
          if (!submittedRef.current) {
            submitQuiz('timeout');
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // ============ 开始挑战 ============
  const startChallenge = () => {
    log('Phase', 'intro → taking');
    setPhase('taking');
    setTimeLeft(challengeData.timeLimitSec);
    setSteps(challengeData.steps.map((text, i) => ({ id: i, text, done: false })));
    setCode(challengeData.starterCode);
    setHintsUsed(0);
    setShowHint(null);
    submittedRef.current = false;
  };

  // ============ 切换步骤完成状态 ============
  const toggleStep = (id: number) => {
    setSteps((prev) => prev.map((s) => s.id === id ? { ...s, done: !s.done } : s));
    log('Step', `步骤 ${id + 1} 切换`);
  };

  // ============ 使用提示 ============
  const useHint = () => {
    if (hintsUsed >= challengeData.hints.length) return;
    setShowHint(hintsUsed);
    setHintsUsed((prev) => prev + 1);
    log('Hint', `使用第 ${hintsUsed + 1} 个提示，累计 ${hintsUsed + 1}`);
  };

  // ============ 提交评测 ============
  const submitQuiz = (source: 'manual' | 'timeout') => {
    if (submittedRef.current) {
      log('Submit', `重复提交已拦截 (source=${source})`);
      return;
    }
    submittedRef.current = true;
    log('Submit', `提交评测 (source=${source})`);

    // 停止计时器
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setSubmitting(true);

    // 模拟 AI 评测延迟
    setTimeout(() => {
      const timeUsed = challengeData.timeLimitSec - timeLeft;
      const graded = gradeSubmission(code, steps, hintsUsed, timeUsed);
      log('Grade', `评分完成: ${graded.score}分`, graded);
      setResult(graded);
      setSubmitting(false);
      log('Phase', 'taking → result');
      setPhase('result');
    }, 1500);
  };

  // ============ 评分逻辑 ============
  const gradeSubmission = (
    codeContent: string,
    stepList: ChallengeStep[],
    hints: number,
    timeUsedSec: number
  ) => {
    // 1. 步骤完成度（每步 15 分，满分 60）
    const completedSteps = stepList.filter((s) => s.done).length;
    const stepScore = (completedSteps / stepList.length) * 60;

    // 2. 代码质量（关键字匹配，满分 25）
    const codeUpper = codeContent.toUpperCase();
    const matchedKeywords = challengeData.keywords.filter((k) =>
      codeUpper.includes(k.toUpperCase())
    );
    const keywordScore = (matchedKeywords.length / challengeData.keywords.length) * 25;

    // 3. 代码行数（非空非注释行，满分 5）
    const codeLines = codeContent.split('\n').filter((l) => {
      const trimmed = l.trim();
      return trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('//');
    });
    const lengthScore = Math.min(codeLines.length / 8, 1) * 5;

    // 4. 扣分项
    const hintPenalty = hints * 5; // 每个提示 -5 分
    const timeRatio = timeUsedSec / challengeData.timeLimitSec;
    const timePenalty = timeRatio > 0.8 ? 10 : timeRatio > 0.6 ? 5 : 0;

    const rawScore = stepScore + keywordScore + lengthScore - hintPenalty - timePenalty;
    const finalScore = Math.max(0, Math.min(100, Math.round(rawScore)));

    // 反馈文案
    let feedback: string;
    if (finalScore >= 90) {
      feedback = '太棒了！你的代码结构清晰，关键逻辑完整，时间控制也很好。继续保持！';
    } else if (finalScore >= 75) {
      feedback = '做得不错！核心逻辑已实现，但还有优化空间。建议检查代码注释和变量命名。';
    } else if (finalScore >= 60) {
      feedback = '基本完成，但部分步骤未勾选或代码缺少关键逻辑。回顾一下舵机占空比映射部分。';
    } else {
      feedback = '挑战未完全通过。建议复习 PWM 原理和 MicroPython 语法，再试一次！';
    }

    // 奖励计算
    const points = Math.round((finalScore / 100) * challengeData.basePoints);
    const streak = finalScore >= 60 ? 1 : 0; // 60 分以上维持连胜
    const badge = finalScore >= 95 ? '满分达人' : finalScore >= 80 ? '挑战先锋' : null;

    return { score: finalScore, timeUsed: timeUsedSec, feedback, rewards: { points, streak, badge } };
  };

  // ============ 重试 ============
  const retry = () => {
    log('Phase', 'result → intro');
    setResult(null);
    setPhase('intro');
  };

  // ============ 工具函数 ============
  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const timerColor = timeLeft > 300 ? 'text-green-400' : timeLeft > 120 ? 'text-yellow-400' : 'text-red-400';
  const allStepsDone = steps.every((s) => s.done);

  // ============ 分数环（SVG） ============
  const ScoreRing = ({ score, size = 120 }: { score: number; size?: number }) => {
    const radius = (size - 16) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const ringColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="#e2e8f0" strokeWidth="8"
          />
          <motion.circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={ringColor} strokeWidth="8" strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: 'spring' }}
            className="text-3xl font-bold"
            style={{ color: ringColor }}
          >
            {score}
          </motion.span>
          <span className="text-[10px] text-slate-400">分</span>
        </div>
      </div>
    );
  };

  // ============ 连胜日历 ============
  const StreakCalendar = () => (
    <div className="bg-white rounded-2xl border border-slate-100 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Flame className="h-4 w-4 text-orange-500" />
        <h3 className="font-bold text-sm text-slate-900">连胜日历</h3>
        <span className="ml-auto text-xs text-orange-600 font-semibold flex items-center gap-1">
          <Flame className="h-3 w-3" /> 连续 3 天
        </span>
      </div>
      <div className="flex justify-between gap-1">
        {streakHistory.map((d, i) => (
          <div key={i} className="flex-1 text-center">
            <div className={`w-full aspect-square rounded-lg flex items-center justify-center text-xs font-bold mb-1 ${
              d.status === 'completed' ? 'bg-green-100 text-green-700' :
              d.status === 'failed' ? 'bg-red-100 text-red-600' :
              'bg-slate-100 text-slate-400 border-2 border-dashed border-slate-300'
            }`}>
              {d.status === 'completed' ? <Check className="h-4 w-4" /> :
               d.status === 'failed' ? <X className="h-4 w-4" /> :
               <Zap className="h-3 w-3" />}
            </div>
            <div className="text-[9px] text-slate-500">{d.day}</div>
            {d.status === 'completed' && <div className="text-[9px] text-green-600 font-semibold">{d.score}</div>}
          </div>
        ))}
      </div>
    </div>
  );

  // ============ 难度标签颜色 ============
  const diffColor = challengeData.difficulty === '初级' ? 'bg-green-100 text-green-700' :
    challengeData.difficulty === '中级' ? 'bg-yellow-100 text-yellow-700' :
    'bg-red-100 text-red-700';

  // ============ INTRO 阶段 ============
  const IntroView = () => (
    <div className="space-y-5">
      {/* 挑战卡片头部 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-6 text-white shadow-lg shadow-orange-200"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <Zap className="h-5 w-5" />
            </div>
            <span className="text-sm font-medium opacity-90">今日挑战</span>
          </div>
          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${diffColor}`}>{challengeData.difficulty}</span>
        </div>
        <h2 className="text-2xl font-bold mb-2">{challengeData.title}</h2>
        <p className="text-sm text-orange-50 leading-relaxed">{challengeData.desc}</p>
      </motion.div>

      {/* 奖励预览 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 text-center">
          <Award className="h-6 w-6 text-yellow-600 mx-auto mb-1" />
          <div className="text-base font-bold text-yellow-700">+{challengeData.basePoints}</div>
          <div className="text-[9px] text-yellow-600">积分奖励</div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-3 text-center">
          <Trophy className="h-6 w-6 text-purple-600 mx-auto mb-1" />
          <div className="text-base font-bold text-purple-700">限定</div>
          <div className="text-[9px] text-purple-600">专属徽章</div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-3 text-center">
          <Flame className="h-6 w-6 text-orange-600 mx-auto mb-1" />
          <div className="text-base font-bold text-orange-700">+1</div>
          <div className="text-[9px] text-orange-600">连胜天数</div>
        </div>
      </div>

      {/* 时间限制 */}
      <div className="bg-slate-50 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-slate-500" />
          <span className="text-sm text-slate-600">时间限制</span>
        </div>
        <span className="text-lg font-bold text-slate-900">{challengeData.timeLimitSec / 60} 分钟</span>
      </div>

      {/* 挑战要求 */}
      <div className="bg-white rounded-2xl border border-slate-100 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Target className="h-4 w-4 text-blue-500" />
          <h3 className="font-bold text-sm text-slate-900">挑战要求</h3>
          <span className="ml-auto text-xs text-slate-400">{challengeData.steps.length} 个步骤</span>
        </div>
        <ul className="space-y-2.5">
          {challengeData.steps.map((step, i) => (
            <li key={i} className="flex items-start gap-2.5 text-xs text-slate-600">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-bold mt-0.5">
                {i + 1}
              </span>
              <span className="leading-relaxed pt-0.5">{step}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 连胜日历 */}
      <StreakCalendar />

      {/* 开始按钮 */}
      <motion.button
        whileTap={{ scale: 0.98 }}
        onClick={startChallenge}
        className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-orange-200 hover:shadow-xl transition-all"
      >
        <Zap className="h-5 w-5" /> 立即开始挑战
      </motion.button>
      {onBack && (
        <button onClick={onBack} className="w-full text-center text-xs text-slate-400 hover:text-slate-600 py-1">
          稍后再做
        </button>
      )}
    </div>
  );

  // ============ TAKING 阶段 ============
  const TakingView = () => (
    <div className="space-y-4">
      {/* 顶部状态栏：倒计时 + 进度 */}
      <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border border-slate-100 rounded-xl p-3 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-orange-500" />
            <span className="font-bold text-sm text-slate-900">{challengeData.title}</span>
          </div>
          <div className={`flex items-center gap-1.5 font-mono font-bold text-lg ${timerColor}`}>
            <Clock className="h-4 w-4" />
            <motion.span
              key={timeLeft}
              initial={{ scale: 1.2 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              {formatTime(timeLeft)}
            </motion.span>
          </div>
        </div>
        {/* 进度条 */}
        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${timeLeft > 300 ? 'bg-green-500' : timeLeft > 120 ? 'bg-yellow-500' : 'bg-red-500'}`}
            animate={{ width: `${(timeLeft / challengeData.timeLimitSec) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </div>

      {/* 步骤清单 */}
      <div className="bg-white rounded-2xl border border-slate-100 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Check className="h-4 w-4 text-blue-500" />
          <h3 className="font-bold text-sm text-slate-900">完成步骤</h3>
          <span className="ml-auto text-xs text-slate-400">
            {steps.filter((s) => s.done).length}/{steps.length}
          </span>
        </div>
        <div className="space-y-2">
          {steps.map((step) => (
            <motion.button
              key={step.id}
              whileTap={{ scale: 0.98 }}
              onClick={() => toggleStep(step.id)}
              className={`w-full flex items-start gap-2.5 p-2.5 rounded-lg text-left transition-all ${
                step.done ? 'bg-green-50 border border-green-200' : 'bg-slate-50 border border-transparent hover:border-slate-200'
              }`}
            >
              <span className={`flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center mt-0.5 transition-all ${
                step.done ? 'bg-green-500 text-white' : 'bg-white border-2 border-slate-300'
              }`}>
                {step.done && <Check className="h-3 w-3" />}
              </span>
              <span className={`text-xs leading-relaxed pt-0.5 ${step.done ? 'text-green-700 line-through' : 'text-slate-600'}`}>
                {step.text}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* 代码编辑器 */}
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div className="flex items-center justify-between bg-slate-800 px-4 py-2.5">
          <div className="flex items-center gap-2 text-white">
            <Code2 className="h-4 w-4" />
            <span className="text-xs font-bold font-mono">main.py</span>
          </div>
          <span className="text-[10px] text-slate-400">{code.split('\n').length} 行</span>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          className={`w-full bg-slate-900 text-slate-200 font-mono text-xs p-4 border-0 outline-none resize-none leading-relaxed ${
            isPhone ? 'h-48' : 'h-64'
          }`}
          placeholder="在这里编写你的代码..."
        />
      </div>

      {/* 提示区域 */}
      <div className="bg-white rounded-2xl border border-slate-100 p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            <h3 className="font-bold text-sm text-slate-900">提示</h3>
            <span className="text-[10px] text-slate-400">（每个 -5 分）</span>
          </div>
          <span className="text-xs text-slate-400">{hintsUsed}/{challengeData.hints.length} 已用</span>
        </div>
        <AnimatePresence>
          {showHint !== null && challengeData.hints[showHint] && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-2"
            >
              <p className="text-xs text-yellow-800 leading-relaxed">{challengeData.hints[showHint]}</p>
            </motion.div>
          )}
        </AnimatePresence>
        {hintsUsed < challengeData.hints.length ? (
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={useHint}
            className="w-full py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs font-medium text-yellow-700 hover:bg-yellow-100 transition-colors flex items-center justify-center gap-1.5"
          >
            <Lightbulb className="h-3.5 w-3.5" />
            {hintsUsed === 0 ? '获取提示' : '下一个提示'}
          </motion.button>
        ) : (
          <p className="text-center text-xs text-slate-400">提示已用完</p>
        )}
      </div>

      {/* 提交按钮 */}
      <div className="space-y-2">
        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={() => submitQuiz('manual')}
          disabled={!allStepsDone || submitting}
          className={`w-full py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
            allStepsDone
              ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-200 hover:shadow-xl'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed'
          }`}
        >
          {submitting ? (
            <>
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              AI 评测中...
            </>
          ) : (
            <>
              <Check className="h-5 w-5" /> 提交评测
            </>
          )}
        </motion.button>
        {!allStepsDone && (
          <p className="text-center text-[10px] text-slate-400">请先完成所有步骤</p>
        )}
        <button
          onClick={() => { if (confirm('确定放弃本次挑战？连胜将会中断。')) { onBack?.(); } }}
          className="w-full text-center text-xs text-slate-400 hover:text-red-500 py-1"
        >
          放弃挑战
        </button>
      </div>
    </div>
  );

  // ============ RESULT 阶段 ============
  const ResultView = () => {
    if (!result) return null;
    const passed = result.score >= 60;

    return (
      <div className="space-y-5">
        {/* 顶部结果卡片 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring' }}
          className={`rounded-2xl p-6 text-center shadow-lg ${
            passed ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-green-200' : 'bg-gradient-to-br from-slate-500 to-slate-700 shadow-slate-200'
          } text-white`}
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', delay: 0.2 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/20 mb-3"
          >
            {passed ? <Trophy className="h-8 w-8" /> : <X className="h-8 w-8" />}
          </motion.div>
          <h2 className="text-2xl font-bold mb-1">{passed ? '挑战成功！' : '挑战未通过'}</h2>
          <p className="text-sm opacity-90">{passed ? '恭喜完成今日挑战' : '不要灰心，再试一次吧'}</p>
        </motion.div>

        {/* 分数环 + 详情 */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6 flex flex-col items-center">
          <ScoreRing score={result.score} size={isPhone ? 120 : 140} />
          <div className="grid grid-cols-2 gap-4 w-full mt-5 pt-5 border-t border-slate-100">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-slate-400 text-xs mb-1">
                <Clock className="h-3 w-3" /> 用时
              </div>
              <div className="font-bold text-slate-900">{formatTime(result.timeUsed)}</div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-slate-400 text-xs mb-1">
                <Lightbulb className="h-3 w-3" /> 提示
              </div>
              <div className="font-bold text-slate-900">{hintsUsed} 个</div>
            </div>
          </div>
        </div>

        {/* AI 评语 */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm flex-shrink-0">
              🤖
            </div>
            <div>
              <p className="text-xs font-semibold text-indigo-900 mb-1">AI 教师点评</p>
              <p className="text-xs text-slate-700 leading-relaxed">{result.feedback}</p>
            </div>
          </div>
        </div>

        {/* 奖励明细 */}
        <div className="bg-white rounded-2xl border border-slate-100 p-4">
          <h3 className="font-bold text-sm text-slate-900 mb-3 flex items-center gap-2">
            <Award className="h-4 w-4 text-yellow-500" /> 获得奖励
          </h3>
          <div className="space-y-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="flex items-center justify-between p-2.5 bg-yellow-50 rounded-lg"
            >
              <div className="flex items-center gap-2">
                <Award className="h-4 w-4 text-yellow-600" />
                <span className="text-xs text-slate-700">积分</span>
              </div>
              <span className="font-bold text-yellow-700">+{result.rewards.points}</span>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="flex items-center justify-between p-2.5 bg-orange-50 rounded-lg"
            >
              <div className="flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-600" />
                <span className="text-xs text-slate-700">连胜</span>
              </div>
              <span className="font-bold text-orange-700">
                {result.rewards.streak > 0 ? `+${result.rewards.streak} 天` : '中断'}
              </span>
            </motion.div>
            {result.rewards.badge && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 }}
                className="flex items-center justify-between p-2.5 bg-purple-50 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <Trophy className="h-4 w-4 text-purple-600" />
                  <span className="text-xs text-slate-700">徽章</span>
                </div>
                <span className="font-bold text-purple-700">{result.rewards.badge}</span>
              </motion.div>
            )}
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="grid grid-cols-2 gap-3">
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={retry}
            className="py-3 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm flex items-center justify-center gap-1.5 hover:bg-slate-200 transition-colors"
          >
            <RefreshCw className="h-4 w-4" /> 再试一次
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => { /* 原型：模拟分享 */ alert('已生成分享卡片！'); }}
            className="py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold text-sm flex items-center justify-center gap-1.5 hover:shadow-lg transition-all"
          >
            <Share2 className="h-4 w-4" /> 分享成绩
          </motion.button>
        </div>
        {onBack && (
          <button onClick={onBack} className="w-full text-center text-xs text-slate-400 hover:text-slate-600 py-1 flex items-center justify-center gap-1">
            返回首页 <ChevronRight className="h-3 w-3" />
          </button>
        )}
      </div>
    );
  };

  // ============ 主渲染 ============
  return (
    <div className={isPhone ? 'space-y-5' : 'max-w-2xl mx-auto space-y-5'}>
      {/* 返回按钮（平板模式独立头部，手机模式由父级提供） */}
      {!isPhone && onBack && (
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 bg-slate-100 rounded-xl text-slate-500 hover:bg-slate-200 transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">每日挑战</h2>
            <p className="text-sm text-slate-500 mt-0.5">完成今日挑战，赢取积分和徽章</p>
          </div>
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={phase}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          {phase === 'intro' && <IntroView />}
          {phase === 'taking' && <TakingView />}
          {phase === 'result' && <ResultView />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
