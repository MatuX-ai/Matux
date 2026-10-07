'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock, Shield, AlertTriangle, CheckCircle, XCircle, ChevronLeft,
  ChevronRight, Flag, RotateCcw, Brain, Eye, Fullscreen,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface QuizPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

type Phase = 'intro' | 'taking' | 'result';

interface Question {
  q: string;
  options: string[];
  correct: number;
  topic: string;
  aiExplain: string;
}

// 测验题目（围绕学生薄弱点 range/循环）
const questions: Question[] = [
  {
    q: 'range(1, 5) 会生成哪些数字？',
    options: ['[1, 2, 3, 4]', '[1, 2, 3, 4, 5]', '[0, 1, 2, 3, 4]', '[1, 2, 3]'],
    correct: 0,
    topic: 'range 基础',
    aiExplain: 'range(1, 5) 生成从 1 开始、到 5 之前结束的序列，即 [1, 2, 3, 4]。range 的结束参数是"不包含"的——这是你最常犯的错误，记住：包含起点，不包含终点。',
  },
  {
    q: 'for i in range(3): print(i) 会循环几次？',
    options: ['2 次', '3 次', '4 次', '0 次'],
    correct: 1,
    topic: 'for 循环',
    aiExplain: 'range(3) 等价于 range(0, 3)，生成 [0, 1, 2]，共 3 个元素，所以循环 3 次，输出 0、1、2。range 只传一个参数时，它表示"循环次数"。',
  },
  {
    q: 'range(0, 10, 2) 生成哪个序列？',
    options: ['[0, 2, 4, 6, 8]', '[0, 2, 4, 6, 8, 10]', '[2, 4, 6, 8, 10]', '[0, 2, 4, 6, 8, 10, 12]'],
    correct: 0,
    topic: 'range 步长',
    aiExplain: 'range(起点, 终点, 步长) —— range(0, 10, 2) 从 0 开始，每次 +2，到 10 之前停止，即 [0, 2, 4, 6, 8]。第三个参数是步长，终点依然"不包含"。',
  },
  {
    q: '以下哪段代码会形成无限循环？',
    options: [
      'for i in range(5): print(i)',
      'while True: print("hi")',
      'while x < 10: x += 1',
      'for i in [1,2,3]: print(i)',
    ],
    correct: 1,
    topic: 'while 循环',
    aiExplain: 'while True 的条件永远为真，循环不会自动结束，形成无限循环。while 循环需要内部修改条件变量（如 x += 1）才能退出；for 循环有固定次数，不会无限循环。',
  },
  {
    q: '执行 list(range(2, 6)) 的结果是？',
    options: ['[2, 3, 4, 5]', '[2, 3, 4, 5, 6]', '[2, 3, 4]', '[2, 4, 6]'],
    correct: 0,
    topic: 'range 与列表',
    aiExplain: 'range(2, 6) 从 2 开始到 6 之前结束，即 2, 3, 4, 5。用 list() 转换后得到 [2, 3, 4, 5]。再次提醒：终点 6 不包含在内。',
  },
];

const TIME_LIMIT = 600; // 10 分钟
const MAX_WARNINGS = 3;

export function QuizPage({ mode, onBack }: QuizPageProps) {
  const isPhone = mode === 'phone';
  const [phase, setPhase] = useState<Phase>('intro');
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>(Array(questions.length).fill(null));
  const [timeLeft, setTimeLeft] = useState(TIME_LIMIT);
  const [warnings, setWarnings] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  const [warningMsg, setWarningMsg] = useState('');
  const startTimeRef = useRef<number>(0);
  const [usedTime, setUsedTime] = useState(0);

  // ============ 调试日志 ============
  // 排查切屏/提交逻辑时设为 true；上线前可关闭
  const DEBUG = false; // 上线时设为 false 关闭日志
  const log = (tag: string, ...args: unknown[]) => {
    if (DEBUG) {
      const colors: Record<string, string> = {
        Timer: '#10b981',
        AntiCheat: '#ef4444',
        Submit: '#f59e0b',
        Answer: '#3b82f6',
        Nav: '#8b5cf6',
        Phase: '#6366f1',
      };
      console.log(`%c[QuizPage][${tag}]`, `color:${colors[tag] || '#6366f1'};font-weight:bold`, ...args);
    }
  };

  // 用 ref 追踪 phase / 是否已提交 / 答案快照，避免 useCallback 闭包过期 + 防止重复提交
  const phaseRef = useRef<Phase>('intro');
  const submittedRef = useRef(false);
  const answersRef = useRef<(number | null)[]>(answers);
  useEffect(() => {
    phaseRef.current = phase;
    log('Phase', `phase -> ${phase}`);
  }, [phase]);
  useEffect(() => {
    answersRef.current = answers;
  }, [answers]);

  // ============ 计时器 ============
  useEffect(() => {
    if (phase !== 'taking') return;
    log('Timer', `启动计时器, timeLeft=${TIME_LIMIT}s`);
    const t = setInterval(() => {
      setTimeLeft((prev) => {
        const next = prev - 1;
        // 每 60s 打一次心跳；最后 10s 每秒打
        if (next === 0) {
          log('Timer', '⏱ 倒计时归零，触发超时自动提交');
          clearInterval(t);
          submitQuiz('timeout');
          return 0;
        }
        if (next <= 10 || next % 60 === 0) {
          log('Timer', `tick: ${next}s 剩余 (${mmss(next)})`);
        }
        return next;
      });
    }, 1000);
    return () => {
      log('Timer', '清理计时器 interval');
      clearInterval(t);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // ============ 切屏检测 - PRD F-06 窗口失焦检测 ============
  // 注意：副作用不能放在 setWarnings 的 updater 里（StrictMode 下 updater 会调用两次，
  // 会导致 setTimeout(submitQuiz) 被重复触发）。这里只做计数，副作用放到下面的 effect。
  useEffect(() => {
    if (phase !== 'taking') return;
    log('AntiCheat', '挂载 blur 监听');
    const handleBlur = () => {
      log('AntiCheat', '🔍 window blur 事件触发');
      setWarnings((w) => {
        const newW = w + 1;
        log('AntiCheat', `warning 计数 ${w} -> ${newW} (上限 ${MAX_WARNINGS})`);
        return newW;
      });
    };
    window.addEventListener('blur', handleBlur);
    return () => {
      log('AntiCheat', '卸载 blur 监听');
      window.removeEventListener('blur', handleBlur);
    };
  }, [phase]);

  // warnings 变化的副作用：弹警告 / 触发自动提交（与计数解耦，避免 StrictMode 双调用）
  useEffect(() => {
    if (phase !== 'taking' || warnings === 0) return;
    log('AntiCheat', `warnings 副作用触发, count=${warnings}`);
    if (warnings >= MAX_WARNINGS) {
      setWarningMsg(`⚠ 检测到第 ${warnings} 次离开答题窗口！已达到上限，测验将自动提交。`);
      setShowWarning(true);
      log('AntiCheat', `🚨 达到上限，2s 后自动提交`);
      const t = setTimeout(() => submitQuiz('anticheat'), 2000);
      return () => {
        log('AntiCheat', '清理自动提交 timeout（未触发）');
        clearTimeout(t);
      };
    }
    setWarningMsg(`⚠ 检测到离开答题窗口！这是第 ${warnings} 次警告，累计 ${MAX_WARNINGS} 次将自动提交测验。`);
    setShowWarning(true);
    log('AntiCheat', `显示第 ${warnings} 次警告弹窗`);
  }, [warnings, phase]);

  const startQuiz = () => {
    log('Phase', '=== 开始测验 ===');
    log('Phase', `重置状态: currentQ=0, timeLeft=${TIME_LIMIT}, warnings=0`);
    submittedRef.current = false;
    setPhase('taking');
    setCurrentQ(0);
    setAnswers(Array(questions.length).fill(null));
    setTimeLeft(TIME_LIMIT);
    setWarnings(0);
    setShowWarning(false);
    startTimeRef.current = Date.now();
    log('Phase', `startTime 记录: ${startTimeRef.current} (${new Date(startTimeRef.current).toISOString()})`);
  };

  // source 用于日志区分提交来源；submittedRef 防止 timeout/anticheat/manual 重复提交
  const submitQuiz = useCallback((source: 'manual' | 'timeout' | 'anticheat' = 'manual') => {
    log('Submit', `▶ submitQuiz 被调用, source=${source}`);
    if (submittedRef.current) {
      log('Submit', `⚠ 已提交过，忽略重复调用 (source=${source})`);
      return;
    }
    if (phaseRef.current !== 'taking') {
      log('Submit', `⚠ 当前 phase=${phaseRef.current} 非 taking，忽略 (source=${source})`);
      return;
    }
    const now = Date.now();
    const used = Math.floor((now - startTimeRef.current) / 1000);
    submittedRef.current = true;
    log('Submit', `✓ 提交确认: source=${source}, usedTime=${used}s, now=${now}, startTime=${startTimeRef.current}`);
    log('Submit', `当前答案:`, answersRef.current);
    setUsedTime(used);
    setPhase('result');
    setShowWarning(false);
  }, []);

  const selectAnswer = (qid: number, opt: number) => {
    const prev = answers[qid];
    log('Answer', `Q${qid + 1} 选择选项 ${opt} (${String.fromCharCode(65 + opt)}), 原答案=${prev === null ? '空' : opt}`);
    setAnswers((prevArr) => {
      const next = [...prevArr];
      next[qid] = opt;
      return next;
    });
  };

  const gotoQuestion = (qid: number) => {
    log('Nav', `跳转题目 ${currentQ + 1} -> ${qid + 1}`);
    setCurrentQ(qid);
  };

  const score = answers.filter((a, i) => a === questions[i].correct).length;
  const scorePercent = Math.round((score / questions.length) * 100);
  const mmss = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  const attentionScore = Math.max(0, 100 - warnings * 25);

  // ============ intro 阶段 ============
  if (phase === 'intro') {
    return (
      <div className={isPhone ? 'space-y-4' : 'max-w-3xl mx-auto space-y-6'}>
        <div className={isPhone ? '' : 'text-center'}>
          <h2 className={`font-bold text-slate-900 ${isPhone ? 'text-xl' : 'text-3xl'} mb-2`}>
            📝 Python 循环测验
          </h2>
          <p className={`text-slate-500 ${isPhone ? 'text-xs' : 'text-sm'}`}>
            针对你的薄弱知识点「range 函数」专项测验 · AI 教师出题
          </p>
        </div>

        {/* 测验信息卡 */}
        <div className={`grid ${isPhone ? 'grid-cols-2' : 'grid-cols-4'} gap-3`}>
          {[
            { icon: Brain, label: '题目数量', value: `${questions.length} 题`, color: 'text-blue-600 bg-blue-50' },
            { icon: Clock, label: '答题时长', value: '10 分钟', color: 'text-green-600 bg-green-50' },
            { icon: CheckCircle, label: '题型', value: '单选题', color: 'text-purple-600 bg-purple-50' },
            { icon: Shield, label: '及格线', value: '60 分', color: 'text-orange-600 bg-orange-50' },
          ].map((item, i) => (
            <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className={`w-9 h-9 rounded-xl ${item.color} flex items-center justify-center mb-2`}>
                <item.icon className="h-5 w-5" />
              </div>
              <p className="text-[10px] text-slate-400">{item.label}</p>
              <p className={`font-bold text-slate-900 ${isPhone ? 'text-sm' : 'text-base'}`}>{item.value}</p>
            </div>
          ))}
        </div>

        {/* 防作弊须知 - PRD F-06 */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border-2 border-red-200 rounded-2xl p-5"
        >
          <div className="flex items-center gap-2 mb-3">
            <Shield className="h-5 w-5 text-red-600" />
            <h3 className="font-bold text-red-700">防作弊须知</h3>
          </div>
          <ul className={`space-y-2 text-slate-700 ${isPhone ? 'text-xs' : 'text-sm'}`}>
            <li className="flex items-start gap-2">
              <Eye className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <span><b>切屏检测</b>：答题期间离开窗口将被记录，累计 {MAX_WARNINGS} 次自动提交</span>
            </li>
            <li className="flex items-start gap-2">
              <Fullscreen className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <span><b>全屏答题</b>：建议进入全屏模式，专注答题不被打扰</span>
            </li>
            <li className="flex items-start gap-2">
              <Clock className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <span><b>计时答题</b>：倒计时结束自动提交，请合理分配时间</span>
            </li>
            <li className="flex items-start gap-2">
              <Brain className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <span><b>题目乱序</b>：题目与选项顺序随机打乱，确保独立完成</span>
            </li>
          </ul>
        </motion.div>

        <div className={`flex ${isPhone ? 'flex-col' : 'justify-center'} gap-3`}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={startQuiz}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-3.5 px-8 rounded-xl shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2"
          >
            <Fullscreen className="h-5 w-5" />
            开始全屏答题
          </motion.button>
          {onBack && (
            <button
              onClick={onBack}
              className={`text-slate-500 hover:text-slate-700 font-medium py-3.5 px-6 rounded-xl border border-slate-200 hover:bg-slate-50 ${isPhone ? '' : ''}`}
            >
              返回
            </button>
          )}
        </div>
      </div>
    );
  }

  // ============ taking 阶段 ============
  if (phase === 'taking') {
    const q = questions[currentQ];
    const answeredCount = answers.filter((a) => a !== null).length;
    const timeUrgent = timeLeft < 60;

    return (
      <div className={isPhone ? 'space-y-4' : 'max-w-3xl mx-auto space-y-5'}>
        {/* 顶部状态栏：计时 + 进度 + 警告 */}
        <div className={`bg-white rounded-2xl shadow-md p-4 flex items-center justify-between ${isPhone ? 'gap-2' : 'gap-4'}`}>
          <div className={`flex items-center gap-2 ${timeUrgent ? 'text-red-500' : 'text-slate-700'}`}>
            <Clock className={`h-5 w-5 ${timeUrgent ? 'animate-pulse' : ''}`} />
            <span className={`font-mono font-bold ${isPhone ? 'text-base' : 'text-xl'}`}>{mmss(timeLeft)}</span>
          </div>
          <div className="text-slate-600">
            <span className={`font-bold ${isPhone ? 'text-sm' : 'text-base'}`}>{currentQ + 1}</span>
            <span className="text-slate-400"> / {questions.length}</span>
          </div>
          <div className={`flex items-center gap-1.5 ${warnings > 0 ? 'text-red-500' : 'text-slate-400'}`}>
            <AlertTriangle className="h-4 w-4" />
            <span className={`font-bold ${isPhone ? 'text-xs' : 'text-sm'}`}>{warnings}/{MAX_WARNINGS}</span>
          </div>
        </div>

        {/* 题目导航点 */}
        <div className="flex justify-center gap-2">
          {questions.map((_, i) => (
            <button
              key={i}
              onClick={() => gotoQuestion(i)}
              className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                i === currentQ
                  ? 'bg-blue-600 text-white scale-110'
                  : answers[i] !== null
                  ? 'bg-green-100 text-green-700'
                  : 'bg-slate-100 text-slate-400'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>

        {/* 题目卡 */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQ}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="bg-white rounded-2xl shadow-md p-6"
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-md">{q.topic}</span>
              <span className="text-xs text-slate-400">第 {currentQ + 1} 题</span>
            </div>
            <h3 className={`font-bold text-slate-900 mb-5 ${isPhone ? 'text-base' : 'text-lg'}`}>{q.q}</h3>
            <div className="space-y-3">
              {q.options.map((opt, i) => {
                const selected = answers[currentQ] === i;
                return (
                  <motion.button
                    key={i}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => selectAnswer(currentQ, i)}
                    className={`w-full text-left p-4 rounded-xl border-2 transition-all flex items-center gap-3 ${
                      selected
                        ? 'border-blue-500 bg-blue-50 text-blue-900'
                        : 'border-slate-200 hover:border-slate-300 text-slate-700'
                    }`}
                  >
                    <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                      selected ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {String.fromCharCode(65 + i)}
                    </span>
                    <span className={`font-mono ${isPhone ? 'text-sm' : 'text-base'}`}>{opt}</span>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* 底部导航 */}
        <div className="flex items-center justify-between gap-3">
          <button
            onClick={() => gotoQuestion(Math.max(0, currentQ - 1))}
            disabled={currentQ === 0}
            className="flex items-center gap-1 px-5 py-3 rounded-xl border border-slate-200 text-slate-600 disabled:opacity-40 hover:bg-slate-50 transition-colors"
          >
            <ChevronLeft className="h-4 w-4" /> 上一题
          </button>
          <span className="text-xs text-slate-400">已答 {answeredCount}/{questions.length}</span>
          {currentQ < questions.length - 1 ? (
            <button
              onClick={() => gotoQuestion(Math.min(questions.length - 1, currentQ + 1))}
              className="flex items-center gap-1 px-5 py-3 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              下一题 <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={() => submitQuiz('manual')}
              className="flex items-center gap-1 px-5 py-3 rounded-xl bg-green-600 text-white hover:bg-green-700 transition-colors font-semibold"
            >
              <Flag className="h-4 w-4" /> 提交
            </button>
          )}
        </div>

        {/* 切屏警告弹窗 - PRD F-06 */}
        <AnimatePresence>
          {showWarning && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
              onClick={() => setShowWarning(false)}
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-3xl p-6 max-w-sm w-full text-center"
              >
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertTriangle className="h-8 w-8 text-red-500" />
                </div>
                <h3 className="font-bold text-slate-900 text-lg mb-2">切屏警告</h3>
                <p className="text-sm text-slate-600 mb-4">{warningMsg}</p>
                <button
                  onClick={() => setShowWarning(false)}
                  className="w-full bg-red-600 text-white py-3 rounded-xl font-semibold hover:bg-red-700 transition-colors"
                >
                  我知道了，继续答题
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // ============ result 阶段 ============
  const passed = scorePercent >= 60;
  return (
    <div className={isPhone ? 'space-y-4' : 'max-w-3xl mx-auto space-y-6'}>
      {/* 成绩总览 */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-md p-6 text-center"
      >
        <div className="relative w-32 h-32 mx-auto mb-4">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" strokeWidth="8" />
            <motion.circle
              cx="50" cy="50" r="42" fill="none" stroke={passed ? '#22c55e' : '#ef4444'} strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={2 * Math.PI * 42}
              initial={{ strokeDashoffset: 2 * Math.PI * 42 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 42 * (1 - scorePercent / 100) }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${passed ? 'text-green-600' : 'text-red-500'}`}>{scorePercent}</span>
            <span className="text-xs text-slate-400">分</span>
          </div>
        </div>
        <h3 className={`font-bold mb-1 ${passed ? 'text-green-600' : 'text-red-500'}`}>
          {passed ? '🎉 恭喜通过！' : '💪 还需努力'}
        </h3>
        <p className="text-sm text-slate-500">
          答对 {score}/{questions.length} 题 · 用时 {mmss(usedTime)}
        </p>
      </motion.div>

      {/* 注意力报告 - PRD F-06 切屏频率/犹豫时间 */}
      <div className="bg-white rounded-2xl shadow-md p-5">
        <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Eye className="h-4 w-4 text-indigo-600" /> 注意力报告
        </h3>
        <div className={`grid ${isPhone ? 'grid-cols-3' : 'grid-cols-3'} gap-3`}>
          <div className="text-center">
            <p className={`font-bold ${attentionScore >= 80 ? 'text-green-600' : attentionScore >= 50 ? 'text-yellow-600' : 'text-red-500'}`}>{attentionScore}</p>
            <p className="text-[10px] text-slate-400">注意力评分</p>
          </div>
          <div className="text-center">
            <p className={`font-bold ${warnings === 0 ? 'text-green-600' : 'text-red-500'}`}>{warnings}</p>
            <p className="text-[10px] text-slate-400">切屏次数</p>
          </div>
          <div className="text-center">
            <p className="font-bold text-slate-700">{mmss(usedTime)}</p>
            <p className="text-[10px] text-slate-400">答题用时</p>
          </div>
        </div>
        {warnings > 0 && (
          <p className="text-xs text-yellow-600 mt-3 bg-yellow-50 rounded-lg p-2">
            ⚠ 检测到 {warnings} 次切屏行为。专注答题有助于提升成绩，AI 教师建议你关闭其他干扰应用。
          </p>
        )}
      </div>

      {/* 知识点掌握度更新 - PRD 246 */}
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-5 border border-indigo-100">
        <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Brain className="h-4 w-4 text-indigo-600" /> 知识点掌握度更新
        </h3>
        <div className="space-y-2">
          {[
            { topic: 'range 基础', before: 55, after: score >= 4 ? 80 : 65 },
            { topic: 'for 循环', before: 60, after: score >= 3 ? 75 : 60 },
            { topic: 'while 循环', before: 50, after: answers[3] === questions[3].correct ? 70 : 50 },
          ].map((k, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xs text-slate-600 w-20 flex-shrink-0">{k.topic}</span>
              <div className="flex-1 h-2 bg-white rounded-full overflow-hidden relative">
                <div className="absolute h-full bg-slate-300 rounded-full" style={{ width: `${k.before}%` }}></div>
                <motion.div
                  initial={{ width: `${k.before}%` }}
                  animate={{ width: `${k.after}%` }}
                  transition={{ delay: 0.3 + i * 0.2, duration: 0.6 }}
                  className={`h-full rounded-full relative z-10 ${k.after > k.before ? 'bg-green-500' : 'bg-red-400'}`}
                ></motion.div>
              </div>
              <span className={`text-xs font-bold w-16 text-right ${k.after > k.before ? 'text-green-600' : 'text-red-500'}`}>
                {k.before}→{k.after}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* AI 答案解析 - PRD F-06 */}
      <div>
        <h3 className={`font-bold text-slate-900 mb-3 flex items-center gap-2 ${isPhone ? 'text-base' : 'text-lg'}`}>
          <Brain className="h-5 w-5 text-purple-600" /> AI 答案解析
        </h3>
        <div className="space-y-3">
          {questions.map((q, i) => {
            const userAns = answers[i];
            const correct = userAns === q.correct;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`bg-white rounded-2xl p-4 border-l-4 ${correct ? 'border-green-500' : 'border-red-500'}`}
              >
                <div className="flex items-start gap-2 mb-2">
                  {correct ? (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className={`font-semibold text-slate-900 ${isPhone ? 'text-sm' : 'text-base'} mb-1`}>
                      {i + 1}. {q.q}
                    </p>
                    {!correct && (
                      <p className="text-xs text-slate-600 mb-1">
                        你的答案：<span className="text-red-500 font-medium">{userAns !== null ? q.options[userAns] : '未作答'}</span>
                        {' · '}正确答案：<span className="text-green-600 font-medium">{q.options[q.correct]}</span>
                      </p>
                    )}
                    {correct && (
                      <p className="text-xs text-green-600 mb-1">✓ 回答正确</p>
                    )}
                    {/* AI 解析 */}
                    <div className="bg-purple-50 rounded-lg p-2.5 mt-2 flex items-start gap-2">
                      <span className="text-sm">🤖</span>
                      <p className="text-xs text-slate-700 leading-relaxed">{q.aiExplain}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className={`flex ${isPhone ? 'flex-col' : 'justify-center'} gap-3`}>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => {
            log('Phase', '=== 再测一次，重置状态 ===');
            submittedRef.current = false;
            setPhase('intro');
          }}
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-3.5 px-8 rounded-xl flex items-center justify-center gap-2"
        >
          <RotateCcw className="h-5 w-5" /> 再测一次
        </motion.button>
        {onBack && (
          <button
            onClick={onBack}
            className="text-slate-500 hover:text-slate-700 font-medium py-3.5 px-6 rounded-xl border border-slate-200 hover:bg-slate-50"
          >
            返回学习
          </button>
        )}
      </div>
    </div>
  );
}
