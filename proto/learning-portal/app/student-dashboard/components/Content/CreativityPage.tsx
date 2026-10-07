'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Send, Lightbulb, Save, RotateCcw, CheckCircle2 } from 'lucide-react';
import { DeviceMode } from '../../types';

interface CreativityPageProps {
  mode: DeviceMode;
}

export function CreativityPage({ mode }: CreativityPageProps) {
  const isPhone = mode === 'phone';
  const [hasRun, setHasRun] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  // 代码内容（带行号展示）
  const codeLines = [
    { no: 1, text: 'for i in range(10):' },
    { no: 2, text: '    print(f"第 {i+1} 次循环")' },
    { no: 3, text: '    if i == 5:' },
    { no: 4, text: '        break' },
    { no: 5, text: '' },
    { no: 6, text: '# 💡 AI 建议：试试 while 循环写法' },
  ];

  const outputLines = [
    '第 1 次循环',
    '第 2 次循环',
    '第 3 次循环',
    '第 4 次循环',
    '第 5 次循环',
    '第 6 次循环',
  ];

  // 手机模式：简化堆叠布局
  if (isPhone) {
    return (
      <div className="px-5 space-y-4">
        <div className="bg-slate-900 rounded-2xl p-4 text-white">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-sm flex items-center gap-2">
              🧊 Python 基础语法 · 循环语句
            </span>
          </div>
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => setHasRun(true)}
              className="flex-1 bg-green-600 text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
            >
              <Play className="h-3 w-3 fill-current" /> 运行
            </button>
            <button
              onClick={() => setHasSubmitted(true)}
              className="flex-1 bg-blue-600 text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1"
            >
              <Send className="h-3 w-3" /> 提交
            </button>
            <button className="flex-1 bg-purple-600 text-white text-xs font-semibold py-2 rounded-lg flex items-center justify-center gap-1">
              <Lightbulb className="h-3 w-3" /> AI
            </button>
          </div>

          {/* 题目描述 */}
          <div className="bg-slate-800 rounded-xl p-3 mb-3 text-xs text-slate-300">
            <p className="font-semibold text-white mb-1">📝 题目描述</p>
            <p>编写一个 for 循环输出数字 0 到 9，当 i=5 时退出循环。</p>
          </div>

          {/* 代码区 */}
          <div className="bg-slate-950 rounded-xl p-3 font-mono text-xs leading-relaxed mb-3">
            {codeLines.map((line) => (
              <div key={line.no} className="flex">
                <span className="text-slate-600 w-6 select-none">{line.no}</span>
                <span className="text-green-400 whitespace-pre">{line.text}</span>
              </div>
            ))}
          </div>

          {/* 运行结果 */}
          {hasRun && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-800 rounded-xl p-3"
            >
              <p className="text-xs text-slate-400 mb-2">📤 运行结果</p>
              {outputLines.map((line, i) => (
                <p key={i} className="text-xs text-slate-200 font-mono">{line}</p>
              ))}
              {hasSubmitted && (
                <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> 测试通过！获得 +50 积分 🎉
                </p>
              )}
            </motion.div>
          )}
        </div>
      </div>
    );
  }

  // 平板/桌面模式：左题目 + 右代码分栏
  return (
    <div className="space-y-4">
      {/* 标题栏 */}
      <div className="bg-white rounded-2xl shadow-md p-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-pink-600 flex items-center justify-center text-white text-lg">
            🎨
          </div>
          <div>
            <h2 className="font-bold text-slate-900">创意引擎 · 代码编辑器</h2>
            <p className="text-xs text-slate-500">Python 基础语法 · 循环语句</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setHasRun(true)}
            className="flex items-center gap-1.5 bg-green-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-green-700 transition-colors"
          >
            <Play className="h-4 w-4 fill-current" /> 运行
          </button>
          <button
            onClick={() => { setHasRun(true); setHasSubmitted(true); }}
            className="flex items-center gap-1.5 bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
          >
            <Send className="h-4 w-4" /> 提交
          </button>
          <button className="flex items-center gap-1.5 bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:shadow-lg transition-all">
            <Lightbulb className="h-4 w-4" /> AI 提示
          </button>
        </div>
      </div>

      {/* 主体：左题目 + 右代码 */}
      <div className="grid grid-cols-12 gap-4">
        {/* 左侧：题目描述 + 提示 */}
        <div className="col-span-4 space-y-4">
          <div className="bg-white rounded-2xl shadow-md p-5">
            <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
              📝 题目描述
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed mb-4">
              编写一个 for 循环输出数字 0 到 9，当 <code className="px-1.5 py-0.5 bg-slate-100 rounded text-blue-600 font-mono text-xs">i=5</code> 时退出循环。
            </p>
            <div className="border-t border-slate-100 pt-4">
              <h4 className="font-semibold text-slate-900 text-sm mb-2 flex items-center gap-2">
                📌 提示
              </h4>
              <ul className="text-xs text-slate-600 space-y-1.5">
                <li>• 使用 <code className="px-1 bg-slate-100 rounded font-mono">range(10)</code></li>
                <li>• 注意缩进规则（4 个空格）</li>
                <li>• <code className="px-1 bg-slate-100 rounded font-mono">break</code> 可提前退出循环</li>
              </ul>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl p-5 border border-purple-100">
            <h4 className="font-semibold text-purple-900 text-sm mb-2 flex items-center gap-2">
              <Lightbulb className="h-4 w-4" /> AI 学习建议
            </h4>
            <p className="text-xs text-purple-700 leading-relaxed">
              你上次测验正确率 60%，主要是 range() 参数混淆。建议先用 Blockly 搭 3 个循环积木，再翻译成 Python！
            </p>
          </div>
        </div>

        {/* 右侧：代码编辑器 + 输出 */}
        <div className="col-span-8 space-y-4">
          {/* 代码编辑器 */}
          <div className="bg-slate-900 rounded-2xl shadow-md overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800 border-b border-slate-700">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-xs text-slate-400 ml-2 font-mono">main.py</span>
              </div>
              <div className="flex items-center gap-2 text-slate-400">
                <button className="hover:text-white transition-colors" title="重置">
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button className="hover:text-white transition-colors flex items-center gap-1 text-xs">
                  <Save className="h-4 w-4" /> 已自动保存
                </button>
              </div>
            </div>
            <div className="p-4 font-mono text-sm leading-relaxed overflow-x-auto">
              {codeLines.map((line) => (
                <div key={line.no} className="flex hover:bg-slate-800/50 -mx-4 px-4">
                  <span className="text-slate-600 w-8 select-none flex-shrink-0">{line.no}</span>
                  <span className="text-green-400 whitespace-pre">{line.text || ' '}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 运行结果 */}
          <div className="bg-slate-900 rounded-2xl shadow-md overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-800 border-b border-slate-700">
              <span className="text-xs text-slate-400 font-mono flex items-center gap-2">
                📤 运行结果
              </span>
            </div>
            <div className="p-4 font-mono text-sm min-h-[120px]">
              {!hasRun ? (
                <p className="text-slate-500 text-xs">点击「运行」查看输出...</p>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-0.5"
                >
                  {outputLines.map((line, i) => (
                    <p key={i} className="text-slate-200">{line}</p>
                  ))}
                  {hasSubmitted && (
                    <p className="text-green-400 mt-3 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4" /> 测试通过！获得 +50 积分 🎉
                    </p>
                  )}
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
