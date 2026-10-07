'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Code, Cpu, Send, CheckCircle,
  Cog, ClipboardList, Trophy, ChevronRight,
} from 'lucide-react';

interface ProjectDetailProps {
  onNavigate?: (page: string) => void;
}

// ============ 步骤数据 ============
interface Step {
  id: number;
  title: string;
  desc: string;
  hint: string;
  completed: boolean;
}

const initialSteps: Step[] = [
  {
    id: 1, title: '搭建电路', desc: '连接光敏电阻到 A0 引脚，LED 到 GPIO 2',
    hint: '光敏电阻一端接 3.3V，另一端接 A0 和 10KΩ 下拉电阻；LED 正极经 220Ω 电阻接 GPIO 2。',
    completed: true,
  },
  {
    id: 2, title: '读取数据', desc: '编写程序读取模拟值并打印到串口',
    hint: '使用 `adc = ADC(Pin(34))` 初始化，`adc.read()` 读取 0-4095 的原始值。',
    completed: true,
  },
  {
    id: 3, title: '逻辑判断', desc: '设定阈值，环境光低于阈值时点亮 LED',
    hint: '建议阈值 1500（约对应 10 lux）。低于阈值时 `led.value(1)`，高于时 `led.value(0)`。',
    completed: false,
  },
  {
    id: 4, title: '调试优化', desc: '调整灵敏度，添加渐变 PWM 过渡效果',
    hint: '用 `pwm.duty()` 替代 `led.value()`，根据光照差值计算 PWM 占空比实现平滑过渡。',
    completed: false,
  },
];

export default function ProjectDetail({ onNavigate }: ProjectDetailProps) {
  const [steps, setSteps] = useState<Step[]>(initialSteps);
  const [reportText, setReportText] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showHint, setShowHint] = useState<number | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // 进度计算
  const progress = useMemo(() => {
    const completed = steps.filter(s => s.completed).length;
    return Math.round((completed / steps.length) * 100);
  }, [steps]);

  const allStepsCompleted = steps.every(s => s.completed);
  const reportValid = reportText.trim().length >= 10;

  // 切换步骤完成状态
  const toggleStep = (id: number) => {
    setSteps(prev => prev.map(s =>
      s.id === id ? { ...s, completed: !s.completed } : s
    ));
  };

  // 提交报告
  const handleSubmit = () => {
    if (!allStepsCompleted) return;
    if (!reportValid) return;
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setSubmitted(true);
      setShowSuccess(true);
    }, 1500);
  };

  return (
    <div className="space-y-5">
      {/* ============ Header ============ */}
      <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-5 text-white relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-bold">智能感应小夜灯</h2>
            <span className={`text-xs px-2 py-1 rounded-full ${
              submitted ? 'bg-white/30' : 'bg-white/20'
            }`}>
              {submitted ? '✓ 已完成' : '进行中'}
            </span>
          </div>
          <p className="text-sm opacity-90 mb-4">
            利用光敏电阻实现环境光自适应控制，学习模拟信号读取与 PWM 输出。
          </p>
          <div className="flex gap-2">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => onNavigate?.('代码编辑器')}
              className="flex-1 bg-white text-green-600 py-2.5 rounded-lg font-bold text-sm flex items-center justify-center gap-1.5"
            >
              <Code className="h-4 w-4" /> 编写代码
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => onNavigate?.('设备连接')}
              className="flex-1 bg-white/20 backdrop-blur text-white py-2.5 rounded-lg font-bold text-sm flex items-center justify-center gap-1.5"
            >
              <Cpu className="h-4 w-4" /> 硬件连接
            </motion.button>
          </div>
        </div>
        <Cog className="absolute -bottom-4 -right-4 h-32 w-32 opacity-10" />
      </div>

      {/* ============ 进度卡片 ============ */}
      <div className="bg-white rounded-xl p-4 border shadow-sm">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-2">
            <ClipboardList className="h-4 w-4 text-green-500" />
            <span className="text-sm font-bold text-slate-900">实验进度</span>
          </div>
          <span className="text-sm text-green-600 font-bold">{progress}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
          />
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-slate-400">
          <span>已完成 {steps.filter(s => s.completed).length}/{steps.length} 步</span>
          {allStepsCompleted ? (
            <span className="text-green-500">✓ 可提交报告</span>
          ) : (
            <span>完成所有步骤后可提交</span>
          )}
        </div>
      </div>

      {/* ============ 实验步骤 ============ */}
      <div>
        <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
          <span className="w-1 h-4 bg-green-500 rounded-full"></span>
          实验步骤
        </h3>
        <div className="space-y-2">
          {steps.map((step, i) => (
            <div key={step.id}>
              <motion.div
                whileTap={{ scale: 0.98 }}
                onClick={() => toggleStep(step.id)}
                className={`bg-white rounded-xl p-3 border flex items-start gap-3 cursor-pointer transition-all ${
                  step.completed ? 'border-green-200 bg-green-50/50' : 'hover:shadow-md'
                }`}
              >
                {/* 步骤圆圈 */}
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5 transition-colors ${
                  step.completed
                    ? 'bg-green-500 text-white'
                    : 'border-2 border-slate-300 text-slate-400'
                }`}>
                  {step.completed ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <span className="text-xs font-bold">{i + 1}</span>
                  )}
                </div>

                {/* 步骤内容 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className={`text-sm font-bold ${step.completed ? 'text-slate-500' : 'text-slate-900'}`}>
                      {step.title}
                    </h4>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowHint(showHint === step.id ? null : step.id);
                      }}
                      className="text-[10px] text-blue-500 hover:text-blue-600 flex items-center gap-0.5"
                    >
                      💡 提示
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{step.desc}</p>
                </div>
              </motion.div>

              {/* 提示展开 */}
              <AnimatePresence>
                {showHint === step.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="ml-11 mt-1 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-[11px] text-yellow-800 flex items-start gap-1.5">
                        <span>💡</span> {step.hint}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>

      {/* ============ 提交报告 ============ */}
      <div className={`rounded-xl border p-4 transition-all ${
        allStepsCompleted
          ? 'bg-indigo-50 border-indigo-200'
          : 'bg-slate-50 border-slate-200 opacity-60'
      }`}>
        <h4 className="font-bold text-sm mb-1 flex items-center gap-2">
          <Trophy className="h-4 w-4 text-indigo-500" />
          提交实验报告
        </h4>
        <p className="text-[10px] text-slate-500 mb-3">
          {allStepsCompleted
            ? '描述你的实验心得或遇到的问题（至少 10 字）'
            : '请先完成所有实验步骤'}
        </p>

        <textarea
          value={reportText}
          onChange={(e) => setReportText(e.target.value)}
          disabled={!allStepsCompleted || submitted}
          placeholder="例如：通过本次实验，我学会了使用 ADC 读取模拟信号，理解了光敏电阻的工作原理..."
          className={`w-full bg-white border rounded-lg p-3 text-sm focus:outline-none transition-colors resize-none ${
            submitted
              ? 'border-green-300 bg-green-50/50'
              : reportValid
                ? 'border-indigo-400 focus:border-indigo-500'
                : 'border-slate-200 focus:border-indigo-400'
          } ${(!allStepsCompleted || submitted) ? 'cursor-not-allowed' : ''}`}
          rows={3}
        />

        {/* 字数提示 */}
        {!submitted && allStepsCompleted && (
          <div className="flex justify-between items-center mt-2 text-[10px]">
            <span className={reportValid ? 'text-green-500' : 'text-slate-400'}>
              {reportText.trim().length >= 10 ? '✓ 字数达标' : `还需 ${10 - reportText.trim().length} 字`}
            </span>
            <span className="text-slate-400">{reportText.trim().length} 字</span>
          </div>
        )}

        {/* 提交按钮 */}
        {!submitted ? (
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={handleSubmit}
            disabled={!allStepsCompleted || !reportValid || submitting}
            className={`w-full mt-3 py-2.5 rounded-lg font-bold text-sm flex items-center justify-center gap-1.5 transition-all ${
              !allStepsCompleted || !reportValid
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:shadow-lg'
            }`}
          >
            {submitting ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> 提交中...</>
            ) : (
              <><Send className="h-4 w-4" /> 提交报告</>
            )}
          </motion.button>
        ) : (
          <div className="mt-3 py-2.5 bg-green-500 text-white rounded-lg font-bold text-sm flex items-center justify-center gap-1.5">
            <CheckCircle className="h-4 w-4" /> 报告已提交
          </div>
        )}
      </div>

      {/* ============ 成功弹窗 ============ */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowSuccess(false)}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.5, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 200 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl w-full max-w-xs p-6 text-center shadow-2xl"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 300 }}
                className="w-20 h-20 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg"
              >
                <Trophy className="h-10 w-10 text-white" />
              </motion.div>
              <h3 className="text-xl font-bold text-slate-900 mb-1">🎉 实验完成！</h3>
              <p className="text-sm text-slate-500 mb-4">智能感应小夜灯项目已提交</p>

              <div className="bg-slate-50 rounded-xl p-3 mb-4 space-y-2 text-left">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-600">获得积分</span>
                  <span className="font-bold text-orange-500">+50</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-600">项目徽章</span>
                  <span className="font-bold text-purple-500">🏅 硬件达人</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-600">经验值</span>
                  <span className="font-bold text-blue-500">+120 EXP</span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowSuccess(false)}
                  className="flex-1 py-2.5 bg-slate-100 text-slate-600 rounded-xl font-semibold text-sm"
                >
                  继续查看
                </button>
                <button
                  onClick={() => onNavigate?.('积分商城')}
                  className="flex-1 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold text-sm flex items-center justify-center gap-1"
                >
                  去领奖 <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
