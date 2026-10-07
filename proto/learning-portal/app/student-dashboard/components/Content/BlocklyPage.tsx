'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Square, Save, Trash2, RotateCcw, ChevronRight, ArrowLeft,
  Move, Eye, Volume2, Repeat, GitBranch, Calculator, Plus, X,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface BlocklyPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// 积木分类（Scratch 风格配色）
interface BlockCategory {
  id: string;
  label: string;
  icon: typeof Move;
  color: string;
  blocks: BlockDef[];
}

interface BlockDef {
  id: string;
  label: string;
  pyCode: string;
  params?: { label: string; value: string }[];
}

// 已放置到画布的积木
interface PlacedBlock {
  uid: string; // 唯一实例 id
  blockId: string;
  label: string;
  pyCode: string;
  color: string;
  category: string;
}

const categories: BlockCategory[] = [
  {
    id: 'move', label: '运动', icon: Move, color: '#3b82f6',
    blocks: [
      { id: 'move-steps', label: '移动 10 步', pyCode: 'character.move(10)' },
      { id: 'turn-right', label: '右转 15°', pyCode: 'character.turn(15)' },
      { id: 'turn-left', label: '左转 15°', pyCode: 'character.turn(-15)' },
      { id: 'go-to', label: '走到 (0, 0)', pyCode: 'character.goto(0, 0)' },
    ],
  },
  {
    id: 'look', label: '外观', icon: Eye, color: '#a855f7',
    blocks: [
      { id: 'say', label: '说 "你好" 2 秒', pyCode: 'character.say("你好", 2)' },
      { id: 'change-size', label: '增大 10', pyCode: 'character.size += 10' },
      { id: 'switch-costume', label: '切换造型', pyCode: 'character.next_costume()' },
    ],
  },
  {
    id: 'sound', label: '声音', icon: Volume2, color: '#ec4899',
    blocks: [
      { id: 'play-sound', label: '播放声音 "meow"', pyCode: 'sound.play("meow")' },
      { id: 'set-volume', label: '音量设为 50', pyCode: 'sound.set_volume(50)' },
    ],
  },
  {
    id: 'control', label: '控制', icon: Repeat, color: '#eab308',
    blocks: [
      { id: 'repeat', label: '重复 4 次', pyCode: 'for _ in range(4):' },
      { id: 'forever', label: '无限循环', pyCode: 'while True:' },
      { id: 'wait', label: '等待 1 秒', pyCode: 'time.sleep(1)' },
      { id: 'if', label: '如果...那么', pyCode: 'if condition:' },
    ],
  },
  {
    id: 'event', label: '事件', icon: GitBranch, color: '#f97316',
    blocks: [
      { id: 'on-start', label: '当开始时', pyCode: '# 程序入口' },
      { id: 'on-click', label: '当被点击时', pyCode: '@on_click' },
      { id: 'on-key', label: '当按下空格键', pyCode: '@on_key("space")' },
    ],
  },
  {
    id: 'math', label: '运算', icon: Calculator, color: '#14b8a6',
    blocks: [
      { id: 'add', label: '1 + 1', pyCode: '1 + 1' },
      { id: 'random', label: '随机 1 到 10', pyCode: 'random.randint(1, 10)' },
    ],
  },
];

export function BlocklyPage({ mode, onBack }: BlocklyPageProps) {
  const isPhone = mode === 'phone';
  const [activeCategory, setActiveCategory] = useState('move');
  const [placedBlocks, setPlacedBlocks] = useState<PlacedBlock[]>([
    { uid: 'b0', blockId: 'on-start', label: '当开始时', pyCode: '# 程序入口', color: '#f97316', category: 'event' },
    { uid: 'b1', blockId: 'repeat', label: '重复 4 次', pyCode: 'for _ in range(4):', color: '#eab308', category: 'control' },
    { uid: 'b2', blockId: 'move-steps', label: '移动 10 步', pyCode: '    character.move(10)', color: '#3b82f6', category: 'move' },
    { uid: 'b3', blockId: 'turn-right', label: '右转 15°', pyCode: '    character.turn(15)', color: '#3b82f6', category: 'move' },
    { uid: 'b4', blockId: 'say', label: '说 "你好" 2 秒', pyCode: '    character.say("你好", 2)', color: '#a855f7', category: 'look' },
  ]);
  const [isRunning, setIsRunning] = useState(false);
  const [charPos, setCharPos] = useState({ x: 50, y: 50, rot: 0 });
  const [showCode, setShowCode] = useState(!isPhone);

  const currentCat = categories.find((c) => c.id === activeCategory)!;

  const addBlock = (block: BlockDef, cat: BlockCategory) => {
    const uid = `b${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    // 缩进：如果前一个块在 control 类（循环/条件），自动缩进
    const lastBlock = placedBlocks[placedBlocks.length - 1];
    let indent = '';
    if (lastBlock && (lastBlock.blockId === 'repeat' || lastBlock.blockId === 'forever' || lastBlock.blockId === 'if')) {
      indent = '    ';
    }
    setPlacedBlocks([...placedBlocks, {
      uid, blockId: block.id, label: block.label,
      pyCode: indent + block.pyCode, color: cat.color, category: cat.id,
    }]);
  };

  const removeBlock = (uid: string) => {
    setPlacedBlocks(placedBlocks.filter((b) => b.uid !== uid));
  };

  const clearAll = () => setPlacedBlocks([]);

  // 生成 Python 代码
  const pythonCode = useMemo(() => {
    return placedBlocks.map((b) => b.pyCode).join('\n');
  }, [placedBlocks]);

  // 运行角色动画
  const runProgram = () => {
    if (isRunning) {
      setIsRunning(false);
      return;
    }
    setIsRunning(true);
    setCharPos({ x: 50, y: 50, rot: 0 });
    let step = 0;
    const moves = placedBlocks.filter((b) => b.blockId === 'move-steps').length;
    const turns = placedBlocks.filter((b) => b.blockId === 'turn-right').length;
    const repeat = placedBlocks.find((b) => b.blockId === 'repeat');
    const repeatCount = repeat ? 4 : 1;
    const totalSteps = (moves + turns) * repeatCount;

    const animate = setInterval(() => {
      step++;
      if (step > totalSteps * 3 || !isRunning) {
        clearInterval(animate);
        setIsRunning(false);
        return;
      }
      setCharPos((prev) => {
        const angle = (prev.rot * Math.PI) / 180;
        return {
          x: Math.max(5, Math.min(95, prev.x + Math.cos(angle) * 8)),
          y: Math.max(5, Math.min(95, prev.y + Math.sin(angle) * 8)),
          rot: step % 3 === 0 ? prev.rot + 15 : prev.rot,
        };
      });
    }, 400);
  };

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="space-y-4">
        {/* 工具栏 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCode(!showCode)}
            className={`px-3 py-2 rounded-lg text-xs font-semibold ${showCode ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}
          >
            {showCode ? '积木' : '代码'}
          </button>
          <button
            onClick={runProgram}
            className={`flex-1 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 ${isRunning ? 'bg-red-500 text-white' : 'bg-green-600 text-white'}`}
          >
            {isRunning ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isRunning ? '停止' : '运行'}
          </button>
          <button onClick={clearAll} className="p-2 bg-slate-100 rounded-lg text-slate-500">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>

        {/* 角色预览 */}
        <div className="bg-slate-900 rounded-2xl h-40 relative overflow-hidden">
          <div className="absolute top-2 left-2 text-[10px] text-slate-400">3D 角色预览</div>
          <motion.div
            animate={{ left: `${charPos.x}%`, top: `${charPos.y}%`, rotate: charPos.rot }}
            transition={{ duration: 0.4 }}
            className="absolute w-10 h-10 -ml-5 -mt-5 text-2xl flex items-center justify-center"
          >
            🐱
          </motion.div>
          {/* 网格背景 */}
          <div className="absolute inset-0 opacity-20" style={{
            backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }} />
        </div>

        <AnimatePresence mode="wait">
          {showCode ? (
            <motion.div key="code" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <pre className="bg-slate-900 text-green-400 rounded-2xl p-4 text-[11px] font-mono overflow-x-auto leading-relaxed max-h-60">
                {pythonCode || '# 点击积木块添加代码'}
              </pre>
            </motion.div>
          ) : (
            <motion.div key="blocks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
              {/* 积木分类条 */}
              <div className="flex gap-1.5 overflow-x-auto pb-1">
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setActiveCategory(cat.id)}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-[11px] font-semibold whitespace-nowrap transition-all ${
                      activeCategory === cat.id ? 'text-white' : 'bg-slate-100 text-slate-600'
                    }`}
                    style={activeCategory === cat.id ? { backgroundColor: cat.color } : {}}
                  >
                    <cat.icon className="h-3 w-3" />
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* 当前分类积木列表 */}
              <div className="grid grid-cols-2 gap-2">
                {currentCat.blocks.map((block) => (
                  <motion.button
                    key={block.id}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => addBlock(block, currentCat)}
                    className="text-white text-[11px] font-medium px-3 py-2.5 rounded-xl flex items-center gap-1.5 shadow-sm"
                    style={{ backgroundColor: currentCat.color }}
                  >
                    <Plus className="h-3 w-3 flex-shrink-0" />
                    {block.label}
                  </motion.button>
                ))}
              </div>

              {/* 画布已放置积木 */}
              <div className="bg-slate-50 rounded-2xl p-3 min-h-[200px] space-y-1.5">
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-1">积木画布</div>
                <AnimatePresence>
                  {placedBlocks.map((block) => (
                    <motion.div
                      key={block.uid}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="text-white text-[11px] font-medium px-3 py-2 rounded-lg flex items-center justify-between shadow-sm"
                      style={{ backgroundColor: block.color }}
                    >
                      <span className="flex items-center gap-1.5">
                        <ChevronRight className="h-3 w-3 opacity-60" />
                        {block.label}
                      </span>
                      <button onClick={() => removeBlock(block.uid)} className="opacity-60 hover:opacity-100">
                        <X className="h-3 w-3" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {placedBlocks.length === 0 && (
                  <div className="text-center text-slate-400 text-xs py-8">从上方选择积木添加到这里</div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-4">
      {/* 标题栏 + 工具栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Blockly 可视化编程 🧩</h2>
          <p className="text-sm text-slate-500 mt-0.5">拖拽积木块编程 · 自动生成 Python 代码</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearAll} className="px-4 py-2 bg-slate-100 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-200 flex items-center gap-1.5">
            <Trash2 className="h-4 w-4" /> 清空
          </button>
          <button className="px-4 py-2 bg-slate-100 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-200 flex items-center gap-1.5">
            <Save className="h-4 w-4" /> 保存
          </button>
          <button
            onClick={runProgram}
            className={`px-6 py-2 rounded-xl text-sm font-bold flex items-center gap-1.5 text-white shadow-lg ${
              isRunning ? 'bg-red-500 shadow-red-500/30' : 'bg-green-600 shadow-green-500/30'
            }`}
          >
            {isRunning ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isRunning ? '停止运行' : '运行程序'}
          </button>
        </div>
      </div>

      {/* 三栏布局：积木库 | 画布 | 代码预览 */}
      <div className="grid grid-cols-12 gap-4">
        {/* 左：积木库 */}
        <div className="col-span-3 bg-white rounded-2xl border border-slate-100 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-sm">积木库</h3>
          </div>
          {/* 分类标签 */}
          <div className="flex flex-wrap gap-1.5 p-3 border-b border-slate-50">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                  activeCategory === cat.id ? 'text-white' : 'bg-slate-100 text-slate-600'
                }`}
                style={activeCategory === cat.id ? { backgroundColor: cat.color } : {}}
              >
                <cat.icon className="h-3 w-3" />
                {cat.label}
              </button>
            ))}
          </div>
          {/* 积木列表 */}
          <div className="p-3 space-y-1.5 max-h-[460px] overflow-y-auto">
            {currentCat.blocks.map((block) => (
              <motion.button
                key={block.id}
                whileHover={{ scale: 1.02, x: 2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => addBlock(block, currentCat)}
                className="w-full text-white text-xs font-medium px-3 py-2.5 rounded-lg flex items-center gap-2 shadow-sm"
                style={{ backgroundColor: currentCat.color }}
              >
                <Plus className="h-3.5 w-3.5 opacity-70" />
                {block.label}
              </motion.button>
            ))}
          </div>
        </div>

        {/* 中：积木画布 */}
        <div className="col-span-5 bg-slate-50 rounded-2xl border border-slate-100 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-white flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm">积木画布</h3>
            <span className="text-[10px] text-slate-400">{placedBlocks.length} 个积木</span>
          </div>
          <div className="p-4 space-y-1.5 min-h-[460px] max-h-[460px] overflow-y-auto">
            <AnimatePresence>
              {placedBlocks.map((block) => (
                <motion.div
                  key={block.uid}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  whileHover={{ x: 2 }}
                  className="text-white text-sm font-medium px-4 py-3 rounded-xl flex items-center justify-between shadow-sm cursor-grab"
                  style={{ backgroundColor: block.color }}
                >
                  <span className="flex items-center gap-2">
                    <ChevronRight className="h-4 w-4 opacity-50" />
                    {block.label}
                  </span>
                  <button
                    onClick={() => removeBlock(block.uid)}
                    className="opacity-50 hover:opacity-100 transition-opacity"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
            {placedBlocks.length === 0 && (
              <div className="flex flex-col items-center justify-center h-80 text-slate-400">
                <Plus className="h-12 w-12 mb-2 opacity-30" />
                <p className="text-sm">从左侧积木库点击添加积木块</p>
              </div>
            )}
          </div>
        </div>

        {/* 右：代码预览 */}
        <div className="col-span-4 bg-slate-900 rounded-2xl overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              Python 代码
            </h3>
            <span className="text-[10px] text-slate-400">自动生成</span>
          </div>
          <pre className="flex-1 p-4 text-green-400 text-xs font-mono overflow-auto leading-relaxed max-h-[490px]">
            {pythonCode || '# 从左侧添加积木块\n# 代码将自动生成'}
          </pre>
        </div>
      </div>

      {/* 3D 角色预览 */}
      <div className="bg-slate-900 rounded-2xl overflow-hidden">
        <div className="px-4 py-2.5 border-b border-slate-700 flex items-center justify-between">
          <h3 className="font-bold text-white text-sm">3D 角色预览</h3>
          <span className={`text-[10px] ${isRunning ? 'text-green-400' : 'text-slate-500'}`}>
            {isRunning ? '● 运行中' : '○ 已停止'}
          </span>
        </div>
        <div className="h-48 relative">
          {/* 网格背景 */}
          <div className="absolute inset-0 opacity-15" style={{
            backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
            backgroundSize: '30px 30px',
          }} />
          {/* 角色 */}
          <motion.div
            animate={{ left: `${charPos.x}%`, top: `${charPos.y}%`, rotate: charPos.rot }}
            transition={{ duration: 0.4, ease: 'linear' }}
            className="absolute w-12 h-12 -ml-6 -mt-6 text-3xl flex items-center justify-center"
          >
            🐱
          </motion.div>
          {/* 坐标提示 */}
          <div className="absolute bottom-2 right-3 text-[10px] text-slate-500 font-mono">
            x: {Math.round(charPos.x)} y: {Math.round(charPos.y)} rot: {charPos.rot}°
          </div>
        </div>
      </div>
    </div>
  );
}
