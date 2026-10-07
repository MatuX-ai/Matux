'use client';

import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Battery, Zap, Lightbulb, ToggleRight, Minus, Plus, X, RotateCw,
  Trash2, Play, Square, Keyboard, Activity, AlertCircle,
} from 'lucide-react';
import { DeviceMode } from '../../types';

interface CircuitLabPageProps {
  mode: DeviceMode;
  onBack?: () => void;
}

// 元件类型
type ComponentType = 'battery' | 'resistor' | 'led' | 'switch' | 'wire';

interface CircuitComponent {
  uid: string;
  type: ComponentType;
  label: string;
  value: string;
  icon: string;
  color: string;
  // 画布坐标（百分比）
  x: number;
  y: number;
  rotated: boolean;
}

interface PaletteItem {
  type: ComponentType;
  label: string;
  value: string;
  icon: string;
  color: string;
  desc: string;
}

const palette: PaletteItem[] = [
  { type: 'battery', label: '电池', value: '5V', icon: '🔋', color: '#f97316', desc: '提供电压' },
  { type: 'resistor', label: '电阻', value: '220Ω', icon: '▭', color: '#64748b', desc: '限制电流' },
  { type: 'led', label: 'LED', value: '2V/20mA', icon: '💡', color: '#ef4444', desc: '发光二极管' },
  { type: 'switch', label: '开关', value: 'ON', icon: '🔘', color: '#3b82f6', desc: '控制通断' },
  { type: 'wire', label: '导线', value: '—', icon: '─', color: '#eab308', desc: '连接元件' },
];

// 预置示例电路：电池→开关→电阻→LED（串联回路）
const initialCircuit: CircuitComponent[] = [
  { uid: 'c1', type: 'battery', label: '电池', value: '5V', icon: '🔋', color: '#f97316', x: 15, y: 30, rotated: false },
  { uid: 'c2', type: 'switch', label: '开关', value: 'ON', icon: '🔘', color: '#3b82f6', x: 45, y: 30, rotated: false },
  { uid: 'c3', type: 'resistor', label: '电阻', value: '220Ω', icon: '▭', color: '#64748b', x: 45, y: 60, rotated: true },
  { uid: 'c4', type: 'led', label: 'LED', value: '2V/20mA', icon: '💡', color: '#ef4444', x: 75, y: 60, rotated: false },
];

export function CircuitLabPage({ mode, onBack }: CircuitLabPageProps) {
  const isPhone = mode === 'phone';
  const [components, setComponents] = useState<CircuitComponent[]>(initialCircuit);
  const [selected, setSelected] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(true);
  const [showShortcutHint, setShowShortcutHint] = useState(false);

  const addComponent = (item: PaletteItem) => {
    const uid = `c${Date.now()}`;
    setComponents([...components, {
      uid, type: item.type, label: item.label, value: item.value,
      icon: item.icon, color: item.color,
      x: 30 + Math.random() * 40, y: 30 + Math.random() * 40, rotated: false,
    }]);
  };

  const removeComponent = (uid: string) => {
    setComponents(components.filter((c) => c.uid !== uid));
    if (selected === uid) setSelected(null);
  };

  const rotateComponent = (uid: string) => {
    setComponents(components.map((c) => c.uid === uid ? { ...c, rotated: !c.rotated } : c));
  };

  // 键盘快捷键：R=旋转, Delete=删除（PRD F-07）
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (!selected) return;
      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        rotateComponent(selected);
      }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault();
        removeComponent(selected);
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, components]);

  // 仿真计算（简化串联回路）
  const simulation = useMemo(() => {
    const hasBattery = components.some((c) => c.type === 'battery');
    const hasLED = components.some((c) => c.type === 'led');
    const hasSwitch = components.some((c) => c.type === 'switch');
    const switchOn = !hasSwitch || components.find((c) => c.type === 'switch')?.value === 'ON';
    const resistors = components.filter((c) => c.type === 'resistor');
    const totalResistance = resistors.reduce((sum, r) => {
      const m = r.value.match(/(\d+)/);
      return sum + (m ? parseInt(m[1]) : 0);
    }, 0);
    const battery = components.find((c) => c.type === 'battery');
    const voltage = battery ? parseInt(battery.value) || 5 : 0;
    const ledDrop = hasLED ? 2 : 0;

    if (!hasBattery) return { voltage: 0, current: 0, resistance: totalResistance, power: 0, status: '⚠ 缺少电池', ledOn: false, ok: false };
    if (!hasLED && !resistors.length) return { voltage, current: 0, resistance: 0, power: 0, status: '⚠ 请添加元件', ledOn: false, ok: false };
    if (!switchOn) return { voltage, current: 0, resistance: totalResistance, power: 0, status: '⚪ 开关已断开', ledOn: false, ok: true };

    const effectiveR = totalResistance || 220;
    const current = ((voltage - ledDrop) / effectiveR * 1000); // mA
    const power = voltage * current / 1000;
    const ledOn = hasLED && current > 5 && current < 30;
    let status = '✓ 电路正常运行';
    if (current > 30) status = '⚠ 电流过大！LED 可能烧毁';
    if (current < 5 && hasLED) status = '⚠ 电流过小，LED 不亮';
    return { voltage, current: Math.round(current * 10) / 10, resistance: effectiveR, power: Math.round(power * 1000) / 1000, status, ledOn, ok: true };
  }, [components]);

  // ============ 手机模式 ============
  if (isPhone) {
    return (
      <div className="space-y-4">
        {/* 工具栏 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            className={`flex-1 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 ${isSimulating ? 'bg-green-600 text-white' : 'bg-slate-200 text-slate-600'}`}
          >
            {isSimulating ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isSimulating ? '停止仿真' : '开始仿真'}
          </button>
          <button
            onClick={() => setComponents(initialCircuit)}
            className="p-2 bg-slate-100 rounded-lg text-slate-500"
          >
            <RotateCw className="h-4 w-4" />
          </button>
          <button
            onClick={() => setShowShortcutHint(!showShortcutHint)}
            className="p-2 bg-slate-100 rounded-lg text-slate-500"
          >
            <Keyboard className="h-4 w-4" />
          </button>
        </div>

        {/* 仿真状态条 */}
        <div className={`rounded-xl p-3 text-xs font-medium ${simulation.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
          {simulation.status}
        </div>

        {/* 面包板画布 */}
        <div className="bg-slate-900 rounded-2xl h-56 relative overflow-hidden">
          {/* 网格 */}
          <div className="absolute inset-0 opacity-15" style={{
            backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }} />
          {/* 元件 */}
          {components.map((c) => (
            <motion.div
              key={c.uid}
              initial={false}
              animate={{ left: `${c.x}%`, top: `${c.y}%`, rotate: c.rotated ? 90 : 0 }}
              onClick={() => setSelected(selected === c.uid ? null : c.uid)}
              className={`absolute -ml-6 -mt-6 w-12 h-12 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${selected === c.uid ? 'ring-2 ring-white scale-110' : ''}`}
              style={{ backgroundColor: c.color + '40', border: `2px solid ${c.color}` }}
            >
              <span className="text-lg">{c.icon}</span>
              <span className="text-[7px] text-white font-bold">{c.value}</span>
            </motion.div>
          ))}
          {/* 连线（简化：电池→开关→电阻→LED 串联） */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
            {components.length >= 2 && components.slice(0, -1).map((c, i) => {
              const next = components[i + 1];
              return (
                <line key={i} x1={c.x} y1={c.y} x2={next.x} y2={next.y}
                  stroke={simulation.ledOn ? '#22c55e' : '#475569'} strokeWidth="0.5" strokeDasharray="1 1" />
              );
            })}
          </svg>
          {/* LED 发光效果 */}
          {simulation.ledOn && components.find((c) => c.type === 'led') && (
            <motion.div
              animate={{ opacity: [0.3, 0.7, 0.3], scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 1 }}
              className="absolute w-20 h-20 rounded-full bg-red-400 blur-xl pointer-events-none"
              style={{ left: `${components.find((c) => c.type === 'led')!.x}%`, top: `${components.find((c) => c.type === 'led')!.y}%`, transform: 'translate(-50%, -50%)' }}
            />
          )}
        </div>

        {/* 选中元件操作 */}
        <AnimatePresence>
          {selected && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <div className="flex gap-2">
                <button onClick={() => rotateComponent(selected)} className="flex-1 py-2 bg-blue-50 text-blue-600 rounded-lg text-xs font-semibold flex items-center justify-center gap-1">
                  <RotateCw className="h-3 w-3" /> 旋转 (R)
                </button>
                <button onClick={() => removeComponent(selected)} className="flex-1 py-2 bg-red-50 text-red-600 rounded-lg text-xs font-semibold flex items-center justify-center gap-1">
                  <Trash2 className="h-3 w-3" /> 删除 (Del)
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 元件库 */}
        <div>
          <h3 className="font-bold text-slate-900 text-sm mb-2">元件库</h3>
          <div className="grid grid-cols-5 gap-2">
            {palette.map((item) => (
              <motion.button
                key={item.type}
                whileTap={{ scale: 0.95 }}
                onClick={() => addComponent(item)}
                className="flex flex-col items-center gap-1 p-2 rounded-xl border-2 border-slate-100 hover:border-slate-300"
              >
                <span className="text-xl">{item.icon}</span>
                <span className="text-[9px] font-medium text-slate-600">{item.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* 仿真读数 */}
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: '电压', value: `${simulation.voltage}V`, color: 'text-orange-600' },
            { label: '电流', value: `${simulation.current}mA`, color: 'text-blue-600' },
            { label: '电阻', value: `${simulation.resistance}Ω`, color: 'text-slate-600' },
            { label: '功率', value: `${simulation.power}W`, color: 'text-purple-600' },
          ].map((r) => (
            <div key={r.label} className="bg-white rounded-xl border p-3 text-center">
              <p className={`text-xl font-bold ${r.color}`}>{r.value}</p>
              <p className="text-[10px] text-slate-400">{r.label}</p>
            </div>
          ))}
        </div>

        {/* 快捷键提示 */}
        {showShortcutHint && (
          <div className="bg-indigo-50 rounded-xl p-3 text-xs text-indigo-700 space-y-1">
            <p className="font-bold mb-1">⌨ 快捷键</p>
            <p>• <kbd className="bg-white px-1.5 rounded">R</kbd> 旋转选中元件</p>
            <p>• <kbd className="bg-white px-1.5 rounded">Delete</kbd> 删除选中元件</p>
            <p>• 点击元件进行选中/取消</p>
          </div>
        )}
      </div>
    );
  }

  // ============ 平板模式 ============
  return (
    <div className="space-y-4">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">电路虚拟实验 ⚡</h2>
          <p className="text-sm text-slate-500 mt-0.5">拖拽元件搭建电路 · 实时仿真电流电压</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowShortcutHint(!showShortcutHint)}
            className="px-3 py-2 bg-slate-100 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-200 flex items-center gap-1.5"
          >
            <Keyboard className="h-4 w-4" /> 快捷键
          </button>
          <button
            onClick={() => setComponents(initialCircuit)}
            className="px-3 py-2 bg-slate-100 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-200 flex items-center gap-1.5"
          >
            <RotateCw className="h-4 w-4" /> 重置
          </button>
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            className={`px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-1.5 text-white shadow-lg ${
              isSimulating ? 'bg-red-500 shadow-red-500/30' : 'bg-green-600 shadow-green-500/30'
            }`}
          >
            {isSimulating ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isSimulating ? '停止仿真' : '开始仿真'}
          </button>
        </div>
      </div>

      {/* 快捷键提示条 */}
      {showShortcutHint && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="bg-indigo-50 rounded-xl p-3 text-xs text-indigo-700 flex gap-6">
          <span>⌨ <b>R</b> = 旋转选中元件</span>
          <span>⌨ <b>Delete</b> = 删除选中元件</span>
          <span>🖱 <b>点击</b> = 选中/取消元件</span>
        </motion.div>
      )}

      <div className="grid grid-cols-12 gap-4">
        {/* 左：元件库 */}
        <div className="col-span-2 bg-white rounded-2xl border border-slate-100 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-sm">元件库</h3>
          </div>
          <div className="p-3 space-y-2">
            {palette.map((item) => (
              <motion.button
                key={item.type}
                whileHover={{ scale: 1.03, x: 2 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => addComponent(item)}
                className="w-full p-3 rounded-xl border-2 border-slate-100 hover:border-slate-300 flex flex-col items-center gap-1"
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-2xl" style={{ backgroundColor: item.color + '20' }}>
                  {item.icon}
                </div>
                <span className="text-xs font-semibold text-slate-700">{item.label}</span>
                <span className="text-[10px] text-slate-400">{item.value}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* 中：面包板画布 */}
        <div className="col-span-7 bg-slate-900 rounded-2xl overflow-hidden">
          <div className="px-4 py-2.5 border-b border-slate-700 flex items-center justify-between">
            <h3 className="font-bold text-white text-sm">面包板</h3>
            <span className="text-[10px] text-slate-400">{components.length} 个元件 · {selected ? '已选中 1 个' : '未选中'}</span>
          </div>
          <div className="h-[440px] relative">
            {/* 网格 */}
            <div className="absolute inset-0 opacity-15" style={{
              backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
              backgroundSize: '30px 30px',
            }} />
            {/* 连线 */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
              {components.length >= 2 && components.slice(0, -1).map((c, i) => {
                const next = components[i + 1];
                return (
                  <line key={i} x1={c.x} y1={c.y} x2={next.x} y2={next.y}
                    stroke={simulation.ledOn ? '#22c55e' : '#475569'} strokeWidth="0.4" strokeDasharray="1 1" />
                );
              })}
            </svg>
            {/* LED 发光 */}
            {simulation.ledOn && components.find((c) => c.type === 'led') && (
              <motion.div
                animate={{ opacity: [0.3, 0.6, 0.3], scale: [1, 1.3, 1] }}
                transition={{ repeat: Infinity, duration: 1.2 }}
                className="absolute w-32 h-32 rounded-full bg-red-400 blur-2xl pointer-events-none"
                style={{ left: `${components.find((c) => c.type === 'led')!.x}%`, top: `${components.find((c) => c.type === 'led')!.y}%`, transform: 'translate(-50%, -50%)' }}
              />
            )}
            {/* 元件 */}
            {components.map((c) => (
              <motion.div
                key={c.uid}
                initial={false}
                animate={{ left: `${c.x}%`, top: `${c.y}%`, rotate: c.rotated ? 90 : 0 }}
                onClick={() => setSelected(selected === c.uid ? null : c.uid)}
                className={`absolute -ml-8 -mt-8 w-16 h-16 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all ${
                  selected === c.uid ? 'ring-2 ring-white scale-110 z-10' : ''
                }`}
                style={{ backgroundColor: c.color + '40', border: `2px solid ${c.color}` }}
              >
                <span className="text-2xl">{c.icon}</span>
                <span className="text-[8px] text-white font-bold">{c.value}</span>
              </motion.div>
            ))}
          </div>
        </div>

        {/* 右：仿真面板 */}
        <div className="col-span-3 space-y-3">
          {/* 仿真状态 */}
          <div className={`rounded-2xl p-4 ${simulation.ok ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center gap-2 mb-1">
              <Activity className={`h-5 w-5 ${simulation.ok ? 'text-green-600' : 'text-red-500'}`} />
              <h3 className="font-bold text-slate-900 text-sm">仿真状态</h3>
            </div>
            <p className={`text-xs font-medium ${simulation.ok ? 'text-green-700' : 'text-red-600'}`}>{simulation.status}</p>
          </div>

          {/* 仿真读数 */}
          <div className="bg-white rounded-2xl border border-slate-100 p-4 space-y-3">
            <h3 className="font-bold text-slate-900 text-sm">实时读数</h3>
            {[
              { label: '电压 (V)', value: simulation.voltage, unit: 'V', color: 'text-orange-600', bg: 'bg-orange-50' },
              { label: '电流 (mA)', value: simulation.current, unit: 'mA', color: 'text-blue-600', bg: 'bg-blue-50' },
              { label: '电阻 (Ω)', value: simulation.resistance, unit: 'Ω', color: 'text-slate-700', bg: 'bg-slate-50' },
              { label: '功率 (W)', value: simulation.power, unit: 'W', color: 'text-purple-600', bg: 'bg-purple-50' },
            ].map((r) => (
              <div key={r.label} className={`rounded-xl p-3 ${r.bg} flex items-center justify-between`}>
                <span className="text-xs text-slate-600">{r.label}</span>
                <span className={`text-lg font-bold ${r.color}`}>{r.value}<span className="text-xs ml-0.5">{r.unit}</span></span>
              </div>
            ))}
          </div>

          {/* 选中元件操作 */}
          {selected && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-slate-100 p-4">
              <h3 className="font-bold text-slate-900 text-sm mb-3">选中元件</h3>
              <div className="flex gap-2">
                <button onClick={() => rotateComponent(selected)} className="flex-1 py-2 bg-blue-50 text-blue-600 rounded-lg text-xs font-semibold flex items-center justify-center gap-1">
                  <RotateCw className="h-3.5 w-3.5" /> 旋转
                </button>
                <button onClick={() => removeComponent(selected)} className="flex-1 py-2 bg-red-50 text-red-600 rounded-lg text-xs font-semibold flex items-center justify-center gap-1">
                  <Trash2 className="h-3.5 w-3.5" /> 删除
                </button>
              </div>
            </motion.div>
          )}

          {/* 公式提示 */}
          <div className="bg-indigo-50 rounded-2xl p-3 text-xs text-indigo-700">
            <p className="font-bold mb-1">📐 欧姆定律</p>
            <p>I = (V - V_LED) / R</p>
            <p className="text-[10px] mt-1 text-indigo-500">电流 = (电压 - LED压降) / 电阻</p>
          </div>
        </div>
      </div>
    </div>
  );
}
