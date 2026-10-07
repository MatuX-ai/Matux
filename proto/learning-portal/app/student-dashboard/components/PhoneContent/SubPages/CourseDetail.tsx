'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayCircle, CheckCircle, Lock, ChevronDown, ChevronLeft, ChevronRight,
  Bot, Send, X, Video, Target, BookOpen, Award,
} from 'lucide-react';

interface CourseDetailProps {
  onNavigate?: (page: string) => void;
}

// ============ 章节数据 ============
interface Chapter {
  id: number;
  title: string;
  duration: string;
  completed: boolean;
  locked: boolean;
  videoDesc: string;
  objectives: string[];
  knowledgePoints: string[];
}

const initialChapters: Chapter[] = [
  {
    id: 1, title: '变量与数据类型', duration: '15:00', completed: true, locked: false,
    videoDesc: '讲解 Python 中 int、float、str、bool 四种基本数据类型，以及变量命名规则和赋值操作。',
    objectives: ['掌握变量定义和赋值', '理解动态类型特性', '熟练使用 type() 函数'],
    knowledgePoints: ['int / float / str / bool', '变量命名规范', 'type() 函数', '类型转换 int() / str()'],
  },
  {
    id: 2, title: '条件判断语句', duration: '20:00', completed: true, locked: false,
    videoDesc: '学习 if / elif / else 条件分支结构，理解比较运算符和逻辑运算符的使用场景。',
    objectives: ['掌握 if-elif-else 语法', '理解布尔表达式', '熟练使用 and / or / not'],
    knowledgePoints: ['if / elif / else', '比较运算符 == != > <', '逻辑运算符 and / or / not', '嵌套条件判断'],
  },
  {
    id: 3, title: 'For 循环详解', duration: '25:00', completed: false, locked: false,
    videoDesc: '深入讲解 for 循环的 range() 函数、遍历列表/字符串，以及 break 和 continue 的使用。',
    objectives: ['掌握 for + range() 模式', '学会遍历序列类型', '理解 break / continue'],
    knowledgePoints: ['range(start, stop, step)', 'for item in list', 'for char in string', 'break / continue'],
  },
  {
    id: 4, title: 'While 循环应用', duration: '18:00', completed: false, locked: true,
    videoDesc: '学习 while 循环的条件控制、无限循环避免，以及 while-else 语法。',
    objectives: ['掌握 while 循环语法', '避免死循环', '理解 while-else'],
    knowledgePoints: ['while condition:', '无限循环 while True:', '循环计数器', 'while-else 语法'],
  },
  {
    id: 5, title: '综合练习：猜数字', duration: '30:00', completed: false, locked: true,
    videoDesc: '通过猜数字游戏综合运用变量、条件判断和循环，完成第一个完整 Python 程序。',
    objectives: ['综合运用所学知识', '掌握随机数生成', '完成完整项目'],
    knowledgePoints: ['import random', 'random.randint()', 'input() 交互', 'while + if 综合应用'],
  },
];

interface AIMessage {
  role: 'user' | 'ai';
  content: string;
}

export default function CourseDetail(_: CourseDetailProps) {
  const [chapters, setChapters] = useState<Chapter[]>(initialChapters);
  const [expandedId, setExpandedId] = useState<number | null>(3); // 默认展开当前章节
  const [showAIChat, setShowAIChat] = useState(false);
  const [aiMessages, setAiMessages] = useState<AIMessage[]>([
    { role: 'ai', content: '你好！我是 AI 助教 🤖 关于这门课程有什么问题吗？' },
  ]);
  const [aiInput, setAiInput] = useState('');

  // 进度计算
  const progress = useMemo(() => {
    const completed = chapters.filter(c => c.completed).length;
    return Math.round((completed / chapters.length) * 100);
  }, [chapters]);

  const currentChapter = useMemo(
    () => chapters.find(c => !c.completed && !c.locked) || chapters[chapters.length - 1],
    [chapters]
  );

  // 展开/折叠章节
  const toggleChapter = (id: number) => {
    const chapter = chapters.find(c => c.id === id);
    if (chapter?.locked) return;
    setExpandedId(expandedId === id ? null : id);
  };

  // 标记章节完成
  const markComplete = (id: number) => {
    setChapters(prev => {
      const next = [...prev];
      const idx = next.findIndex(c => c.id === id);
      if (idx === -1) return prev;
      next[idx] = { ...next[idx], completed: true };
      // 解锁下一章
      if (idx + 1 < next.length) {
        next[idx + 1] = { ...next[idx + 1], locked: false };
      }
      return next;
    });
    // 自动展开下一章
    const nextChapter = chapters.find(c => c.id === id + 1);
    if (nextChapter) {
      setTimeout(() => setExpandedId(nextChapter.id), 300);
    }
  };

  // AI 问答
  const handleAISend = () => {
    if (!aiInput.trim()) return;
    const userMsg = aiInput.trim();
    setAiMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setAiInput('');

    // 模拟 AI 回答
    setTimeout(() => {
      const responses: Record<string, string> = {
        'for': 'for 循环的语法是 `for 变量 in range(起始, 结束):`，例如 `for i in range(5):` 会循环 5 次（0-4）。',
        'while': 'while 循环会在条件为 True 时持续执行。注意要在循环体内修改条件变量，避免死循环！',
        'range': '`range(5)` 生成 0-4 的序列，`range(2, 8)` 生成 2-7，`range(0, 10, 2)` 生成 0,2,4,6,8（步长为 2）。',
        'break': '`break` 用于立即跳出当前循环，`continue` 是跳过本次循环的剩余语句，进入下一次循环。',
      };
      const lower = userMsg.toLowerCase();
      let response = '';
      for (const [key, val] of Object.entries(responses)) {
        if (lower.includes(key)) { response = val; break; }
      }
      if (!response) {
        response = `关于「${userMsg}」，建议你查看课程视频中的对应章节。简单来说：多动手实践是最好的学习方式！如果还有疑问可以继续问我 😊`;
      }
      setAiMessages(prev => [...prev, { role: 'ai', content: response }]);
    }, 800);
  };

  return (
    <div className="space-y-5">
      {/* ============ Header ============ */}
      <div className="relative h-44 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
            <PlayCircle className="h-16 w-16 text-white/80" />
          </motion.div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent text-white">
          <h2 className="text-xl font-bold">Python 编程基础</h2>
          <p className="text-xs opacity-90">第 3 章：循环与逻辑 · 共 5 节课</p>
        </div>
      </div>

      {/* ============ 进度卡片 ============ */}
      <div className="bg-white rounded-xl p-4 border shadow-sm">
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center gap-2">
            <Award className="h-4 w-4 text-orange-500" />
            <span className="text-sm font-bold text-slate-900">学习进度</span>
          </div>
          <span className="text-sm text-blue-600 font-bold">{progress}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
          />
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-slate-400">
          <span>已完成 {chapters.filter(c => c.completed).length}/{chapters.length} 节</span>
          <span>预计还需 2 小时</span>
        </div>
      </div>

      {/* ============ 章节导航 ============ */}
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-blue-500" />
          课程大纲
        </h3>
        <div className="flex gap-1.5">
          <button
            onClick={() => {
              const prevCh = [...chapters].reverse().find(c => !c.locked && c.id < (expandedId || 0));
              if (prevCh) setExpandedId(prevCh.id);
            }}
            className="p-1.5 bg-slate-100 rounded-lg text-slate-500 hover:bg-slate-200 transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              const nextCh = chapters.find(c => !c.locked && c.id > (expandedId || 0));
              if (nextCh) setExpandedId(nextCh.id);
            }}
            className="p-1.5 bg-slate-100 rounded-lg text-slate-500 hover:bg-slate-200 transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ============ 章节列表 ============ */}
      <div className="space-y-2">
        {chapters.map((chapter, i) => (
          <div key={chapter.id}>
            <motion.div
              whileTap={chapter.locked ? undefined : { scale: 0.98 }}
              onClick={() => toggleChapter(chapter.id)}
              className={`bg-white rounded-xl p-3 border flex items-center gap-3 transition-all ${
                chapter.locked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-md'
              } ${
                expandedId === chapter.id ? 'border-blue-500 bg-blue-50' :
                chapter.id === currentChapter.id ? 'border-blue-300' : ''
              }`}
            >
              {/* 状态图标 */}
              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                chapter.completed ? 'bg-green-100 text-green-600' :
                chapter.locked ? 'bg-slate-100 text-slate-400' :
                expandedId === chapter.id ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-600'
              }`}>
                {chapter.completed ? <CheckCircle className="h-5 w-5" /> :
                 chapter.locked ? <Lock className="h-4 w-4" /> :
                 <PlayCircle className="h-5 w-5" />}
              </div>

              {/* 章节信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 font-mono">第{i + 1}节</span>
                  {chapter.id === currentChapter.id && !chapter.completed && (
                    <span className="text-[9px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full">当前</span>
                  )}
                </div>
                <h4 className={`text-sm font-bold ${chapter.completed ? 'text-slate-500' : 'text-slate-900'}`}>
                  {chapter.title}
                </h4>
                <p className="text-[10px] text-slate-500">{chapter.duration}</p>
              </div>

              {/* 展开箭头 */}
              {!chapter.locked && (
                <motion.div animate={{ rotate: expandedId === chapter.id ? 180 : 0 }}>
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                </motion.div>
              )}
            </motion.div>

            {/* ============ 章节展开内容 ============ */}
            <AnimatePresence>
              {expandedId === chapter.id && !chapter.locked && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="overflow-hidden"
                >
                  <div className="mt-2 ml-12 bg-white rounded-xl border p-4 space-y-3">
                    {/* 视频占位 */}
                    <div className="bg-slate-900 rounded-lg p-4 flex items-center gap-3">
                      <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center">
                        <Video className="h-6 w-6 text-white/60" />
                      </div>
                      <div className="flex-1">
                        <p className="text-xs text-white/80 font-medium">{chapter.videoDesc}</p>
                        <p className="text-[10px] text-white/40 mt-1">视频时长 {chapter.duration}</p>
                      </div>
                    </div>

                    {/* 学习目标 */}
                    <div>
                      <h5 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1.5">
                        <Target className="h-3.5 w-3.5 text-orange-500" />
                        学习目标
                      </h5>
                      <ul className="space-y-1">
                        {chapter.objectives.map((obj, j) => (
                          <li key={j} className="text-[11px] text-slate-600 flex items-start gap-1.5">
                            <span className="text-green-500 mt-0.5">✓</span> {obj}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* 知识点 */}
                    <div>
                      <h5 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5 text-blue-500" />
                        知识点
                      </h5>
                      <div className="flex flex-wrap gap-1.5">
                        {chapter.knowledgePoints.map((pt, j) => (
                          <span key={j} className="text-[10px] bg-blue-50 text-blue-700 px-2 py-1 rounded-md border border-blue-100">
                            {pt}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* 完成按钮 */}
                    {!chapter.completed ? (
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => markComplete(chapter.id)}
                        className="w-full py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-bold text-xs flex items-center justify-center gap-1.5"
                      >
                        <CheckCircle className="h-4 w-4" /> 标记为已完成
                      </motion.button>
                    ) : (
                      <div className="w-full py-2 bg-green-50 text-green-600 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5">
                        <CheckCircle className="h-4 w-4" /> 已完成
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* ============ AI 助教入口 ============ */}
      <motion.button
        whileTap={{ scale: 0.98 }}
        onClick={() => setShowAIChat(true)}
        className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg"
      >
        <Bot className="h-5 w-5" /> 向 AI 助教提问
      </motion.button>

      {/* ============ AI 助教弹窗 ============ */}
      <AnimatePresence>
        {showAIChat && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAIChat(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center"
          >
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 50, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-t-3xl sm:rounded-2xl w-full max-w-md h-[70vh] flex flex-col shadow-2xl"
            >
              {/* 头部 */}
              <div className="flex items-center justify-between p-4 border-b">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm">AI 助教</h3>
                    <p className="text-[10px] text-green-500">● 在线</p>
                  </div>
                </div>
                <button onClick={() => setShowAIChat(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* 消息列表 */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {aiMessages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] px-3 py-2 rounded-2xl text-xs ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white rounded-br-md'
                        : 'bg-slate-100 text-slate-800 rounded-bl-md'
                    }`}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* 快捷问题 */}
              <div className="px-4 pb-2 flex gap-1.5 flex-wrap">
                {['for循环怎么用', 'range参数', 'break和continue'].map(q => (
                  <button
                    key={q}
                    onClick={() => { setAiInput(q); }}
                    className="text-[10px] bg-slate-100 text-slate-600 px-2 py-1 rounded-full hover:bg-slate-200 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* 输入框 */}
              <div className="p-4 border-t flex gap-2">
                <input
                  value={aiInput}
                  onChange={(e) => setAiInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAISend()}
                  placeholder="输入问题..."
                  className="flex-1 px-3 py-2 bg-slate-50 border rounded-xl text-xs focus:outline-none focus:border-blue-500"
                />
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={handleAISend}
                  className="bg-blue-500 text-white p-2 rounded-xl"
                >
                  <Send className="h-4 w-4" />
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
