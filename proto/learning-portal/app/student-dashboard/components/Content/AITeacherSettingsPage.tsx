'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, RotateCcw, Check } from 'lucide-react';
import { DeviceMode } from '../../types';

interface AITeacherSettingsPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// 偏好选项配置
const preferences = [
  {
    id: 'address',
    title: '称呼方式',
    options: [
      { value: 'name', label: '叫我"李明"' },
      { value: 'nickname', label: '叫我"明明"（昵称）' },
      { value: 'classmate', label: '叫我"同学"' },
    ],
  },
  {
    id: 'style',
    title: '语言风格',
    options: [
      { value: 'lively', label: '活泼开朗' },
      { value: 'rigorous', label: '严谨专业' },
      { value: 'concise', label: '简洁高效' },
      { value: 'humorous', label: '幽默风趣' },
    ],
  },
  {
    id: 'hint',
    title: '提示程度',
    options: [
      { value: 'answer', label: '直接给答案' },
      { value: 'guide', label: '引导我思考' },
      { value: 'direction', label: '只给方向，让我自己探索' },
    ],
  },
  {
    id: 'encourage',
    title: '鼓励频率',
    options: [
      { value: 'high', label: '高（经常夸我）' },
      { value: 'medium', label: '适中' },
      { value: 'low', label: '低（只在里程碑时）' },
    ],
  },
  {
    id: 'emoji',
    title: 'Emoji 使用',
    options: [
      { value: 'many', label: '多用 emoji，我喜欢！' },
      { value: 'some', label: '适量' },
      { value: 'none', label: '不用' },
    ],
  },
];

export function AITeacherSettingsPage({ mode, onBack }: AITeacherSettingsPageProps) {
  const isPhone = mode === 'phone';
  const [selected, setSelected] = useState<Record<string, string>>({
    address: 'nickname',
    style: 'rigorous',
    hint: 'guide',
    encourage: 'medium',
    emoji: 'many',
  });
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleSelect = (group: string, value: string) => {
    setSelected((prev) => ({ ...prev, [group]: value }));
  };

  const handleReset = () => {
    setShowResetConfirm(false);
    alert('AI 教师记忆已重置，将从下一次对话开始重新认识你。');
  };

  // 单选组渲染
  const renderRadioGroup = (group: typeof preferences[0]) => (
    <div className={isPhone ? 'space-y-2' : 'flex flex-wrap gap-3'}>
      {group.options.map((opt) => {
        const isChecked = selected[group.id] === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => handleSelect(group.id, opt.value)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm transition-all border-2 ${
              isChecked
                ? 'bg-indigo-50 border-indigo-500 text-indigo-700 font-semibold'
                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
            } ${isPhone ? 'w-full' : ''}`}
          >
            <span
              className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                isChecked ? 'border-indigo-500' : 'border-slate-300'
              }`}
            >
              {isChecked && <span className="w-2 h-2 rounded-full bg-indigo-500"></span>}
            </span>
            {opt.label}
            {isChecked && <Check className="h-3.5 w-3.5 text-indigo-500 ml-auto" />}
          </button>
        );
      })}
    </div>
  );

  // 卡片容器
  const Card = ({ children, title }: { children: React.ReactNode; title: string }) => (
    <div className={`bg-white rounded-2xl shadow-md ${isPhone ? 'p-4' : 'p-6'}`}>
      <h3 className={`font-bold text-slate-900 mb-3 ${isPhone ? 'text-sm' : 'text-base'}`}>{title}</h3>
      {children}
    </div>
  );

  const content = (
    <div className={isPhone ? 'space-y-3' : 'space-y-5'}>
      {/* 偏好分组 */}
      {preferences.map((group) => (
        <Card key={group.id} title={group.title}>
          {renderRadioGroup(group)}
        </Card>
      ))}

      {/* 重置记忆 */}
      <div className={`bg-red-50 rounded-2xl border-2 border-red-100 ${isPhone ? 'p-4' : 'p-6'}`}>
        <div className="flex items-start gap-3">
          <RotateCcw className={`text-red-500 flex-shrink-0 ${isPhone ? 'h-5 w-5' : 'h-6 w-6'}`} />
          <div className="flex-1">
            <h3 className={`font-bold text-red-700 ${isPhone ? 'text-sm' : 'text-base'}`}>🔄 重置 AI 教师记忆</h3>
            <p className={`text-slate-600 mt-1 ${isPhone ? 'text-xs' : 'text-sm'}`}>
              清除 AI 教师关于你的所有记忆，从头开始。此操作不可撤销。
            </p>
            <button
              onClick={() => setShowResetConfirm(true)}
              className="mt-3 bg-red-500 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors"
            >
              重置记忆
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // 手机模式
  if (isPhone) {
    return (
      <div className="px-5 space-y-4 pb-24">
        <div className="flex items-center gap-2">
          {onBack && (
            <button onClick={onBack} className="p-1 text-slate-500">←</button>
          )}
          <h2 className="text-xl font-bold text-slate-900">AI 教师设置</h2>
        </div>
        {content}
        {showResetConfirm && (
          <ConfirmModal isPhone onConfirm={handleReset} onCancel={() => setShowResetConfirm(false)} />
        )}
      </div>
    );
  }

  // 平板/桌面模式
  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex items-center gap-3">
        {onBack && (
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-xl transition-colors text-slate-600"
          >
            ←
          </button>
        )}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
            <Bot className="h-5 w-5" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900">AI 教师设置</h2>
        </div>
      </div>

      {/* 预览摘要 */}
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-5 border border-indigo-100">
        <p className="text-sm text-slate-600">
          📊 当前画像：G7 · 视觉型 · Python 中阶 · 
          AI 教师将以 <span className="font-semibold text-indigo-700">严谨专业</span> 的风格，
          <span className="font-semibold text-indigo-700"> 引导你思考</span>，
          <span className="font-semibold text-indigo-700"> 适度鼓励</span>
        </p>
      </div>

      {content}

      {showResetConfirm && (
        <ConfirmModal onConfirm={handleReset} onCancel={() => setShowResetConfirm(false)} />
      )}
    </div>
  );
}

// 重置确认弹窗
function ConfirmModal({
  onConfirm,
  onCancel,
  isPhone,
}: {
  onConfirm: () => void;
  onCancel: () => void;
  isPhone?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`bg-white rounded-2xl ${isPhone ? 'max-w-sm' : 'max-w-md'} w-full p-6 shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
            <RotateCcw className="h-5 w-5 text-red-500" />
          </div>
          <h3 className="font-bold text-lg text-slate-900">确认重置记忆？</h3>
        </div>
        <p className="text-sm text-slate-600 mb-5">
          AI 教师将忘记你的所有学习历史、对话记录和个性化偏好，并从头开始认识你。此操作不可撤销。
        </p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 bg-slate-100 text-slate-700 rounded-xl text-sm font-semibold hover:bg-slate-200 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors"
          >
            确认重置
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
