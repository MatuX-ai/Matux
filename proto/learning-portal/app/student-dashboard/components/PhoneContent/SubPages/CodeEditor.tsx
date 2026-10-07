'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Code, Save, Play, Square, Trash2, FileCode, Check, Loader2, Terminal,
} from 'lucide-react';

interface CodeEditorProps {
  onNavigate?: (page: string) => void;
}

// ============ 文件系统 ============
interface CodeFile {
  name: string;
  code: string;
  desc: string;
}

const initialFiles: CodeFile[] = [
  {
    name: 'main.py',
    desc: 'LED 闪烁',
    code: `from machine import Pin
import time

# 初始化板载 LED（GPIO 2）
led = Pin(2, Pin.OUT)

print("LED 闪烁程序启动")
print("按 Ctrl+C 停止")

while True:
    led.value(1)
    print("LED ON")
    time.sleep(1)
    led.value(0)
    print("LED OFF")
    time.sleep(1)`,
  },
  {
    name: 'sensor.py',
    desc: '温湿度读取',
    code: `from machine import Pin, ADC
import time

# 模拟传感器读取
temp_sensor = ADC(Pin(34))
temp_sensor.atten(ADC.ATTN_11V)

print("传感器初始化完成")

for i in range(5):
    raw = temp_sensor.read()
    temp = (raw / 4095) * 3.3 * 100
    print(f"第{i+1}次读取: {temp:.1f}C")
    time.sleep(0.5)

print("采样完成")`,
  },
  {
    name: 'led.py',
    desc: '呼吸灯',
    code: `from machine import Pin, PWM
import time

# PWM 呼吸灯
pwm = PWM(Pin(2), freq=1000)

print("呼吸灯启动")

brightness = 0
direction = 1

for _ in range(3):
    for _ in range(100):
        pwm.duty(brightness)
        brightness += direction * 5
        if brightness >= 100 or brightness <= 0:
            direction *= -1
        time.sleep(0.02)
    print(f"亮度: {brightness}%")

pwm.deinit()
print("呼吸灯结束")`,
  },
];

// ============ 模拟 Python 执行器 ============
interface ExecResult {
  output: string;
  error?: string;
}

function simulatePython(code: string): ExecResult {
  const lines = code.split('\n');
  const output: string[] = [];
  let variables: Record<string, unknown> = {};

  // 简单的行解析执行器
  let whileLoopCount = 0;
  let i = 0;

  const execLine = (line: string): boolean => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return true; // 空行/注释

    // import 语句 - 静默处理
    if (trimmed.startsWith('from ') || trimmed.startsWith('import ')) return true;

    // print() 语句
    const printMatch = trimmed.match(/^print\((.*)\)$/);
    if (printMatch) {
      const arg = printMatch[1];
      // 处理 f-string
      const fstrMatch = arg.match(/^f["'](.*)["']$/);
      if (fstrMatch) {
        let str = fstrMatch[1];
        // 替换 {expr} 格式化
        str = str.replace(/\{([^}]+)\}/g, (_, expr) => {
          return evalExpr(expr, variables);
        });
        output.push(str);
      } else if (arg.startsWith('"') || arg.startsWith("'")) {
        // 纯字符串
        output.push(arg.replace(/^["']|["']$/g, ''));
      } else {
        // 表达式
        output.push(evalExpr(arg, variables));
      }
      return true;
    }

    // 变量赋值
    const assignMatch = trimmed.match(/^(\w+)\s*=\s*(.+)$/);
    if (assignMatch) {
      const [, name, expr] = assignMatch;
      variables[name] = evalExpr(expr, variables);
      return true;
    }

    // led.value(x) / pwm.duty(x)
    const methodMatch = trimmed.match(/^(\w+)\.(\w+)\((.*)\)$/);
    if (methodMatch) {
      const [, obj, method, args] = methodMatch;
      if (method === 'value') {
        const val = evalExpr(args, variables);
        output.push(`${obj} = ${val}`);
      } else if (method === 'duty') {
        // 静默处理
      } else if (method === 'deinit') {
        output.push(`${obj} 已释放`);
      }
      return true;
    }

    // time.sleep(x)
    const sleepMatch = trimmed.match(/^time\.sleep\((.+)\)$/);
    if (sleepMatch) {
      // 静默处理（实际由流式输出的延迟模拟）
      return true;
    }

    // while True:
    if (trimmed.startsWith('while ')) {
      return true; // 循环头，由外层处理
    }

    // for _ in range(n):
    const forMatch = trimmed.match(/^for\s+(\w+)\s+in\s+range\((.+)\):$/);
    if (forMatch) {
      return true; // 循环头，由外层处理
    }

    // pwm = PWM(Pin(2), freq=1000)
    if (trimmed.match(/^\w+\s*=\s*(PWM|Pin|ADC)\(/)) {
      return true; // 硬件初始化，静默
    }

    // 其他未识别的行 - 静默跳过
    return true;
  };

  // 简单表达式求值
  const evalExpr = (expr: string, vars: Record<string, unknown>): string => {
    expr = expr.trim();

    // 变量引用
    if (expr in vars) {
      const v = vars[expr];
      return typeof v === 'number' ? String(v) : String(v);
    }

    // f-string 内的表达式（简化）
    // 数值表达式
    if (/^[\d\s+\-*/.()]+$/.test(expr)) {
      try {
        const result = Function(`"use strict"; return (${expr})`)();
        return String(result);
      } catch {
        return expr;
      }
    }

    // 字符串
    if (expr.startsWith('"') || expr.startsWith("'")) {
      return expr.replace(/^["']|["']$/g, '');
    }

    // format 表达式: {temp:.1f}C
    const fmtMatch = expr.match(/^(\w+):(\.\d+)f$/);
    if (fmtMatch) {
      const [, name, fmt] = fmtMatch;
      const v = Number(vars[name] || 0);
      const digits = parseInt(fmt.match(/\.(\d+)/)?.[1] || '1');
      return v.toFixed(digits);
    }

    // 算术: raw / 4095 * 3.3 * 100
    const arithMatch = expr.match(/^(\w+)\s*\/\s*(\d+)\s*\*\s*([\d.]+)\s*\*\s*(\d+)$/);
    if (arithMatch) {
      const [, varName, divisor, mult1, mult2] = arithMatch;
      const v = Number(vars[varName] || 2048);
      const result = (v / parseInt(divisor)) * parseFloat(mult1) * parseInt(mult2);
      return String(result);
    }

    // i+1 形式
    const addMatch = expr.match(/^(\w+)\s*\+\s*(\d+)$/);
    if (addMatch) {
      const v = Number(vars[addMatch[1]] || 0);
      return String(v + parseInt(addMatch[2]));
    }

    return expr;
  };

  // 执行代码（简化版 - 处理 while 和 for 循环）
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // while True: 循环
    if (trimmed.match(/^while\s+True\s*:/)) {
      const loopBody: string[] = [];
      let j = i + 1;
      while (j < lines.length && (lines[j].startsWith('    ') || lines[j].trim() === '')) {
        loopBody.push(lines[j]);
        j++;
      }
      // 限制循环 5 轮
      while (whileLoopCount < 5) {
        for (const bodyLine of loopBody) {
          execLine(bodyLine);
        }
        whileLoopCount++;
      }
      if (whileLoopCount >= 5) {
        output.push('... (循环已运行 5 轮，自动停止)');
      }
      i = j;
      continue;
    }

    // for _ in range(n): 循环
    const forMatch = trimmed.match(/^for\s+(\w+)\s+in\s+range\((.+)\):$/);
    if (forMatch) {
      const [, varName, rangeExpr] = forMatch;
      const rangeVal = parseInt(evalExpr(rangeExpr.trim(), variables));
      const loopBody: string[] = [];
      let j = i + 1;
      while (j < lines.length && (lines[j].startsWith('    ') || lines[j].trim() === '')) {
        loopBody.push(lines[j]);
        j++;
      }
      for (let k = 0; k < rangeVal; k++) {
        variables[varName] = k;
        for (const bodyLine of loopBody) {
          execLine(bodyLine);
        }
      }
      i = j;
      continue;
    }

    execLine(line);
    i++;
  }

  return { output: output.join('\n') };
}

// ============ 语法高亮 ============
function highlightCode(code: string): string {
  // 转义 HTML
  let html = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // 注释
  html = html.replace(/(#[^\n]*)/g, '<span style="color:#6b7280">$1</span>');
  // 字符串（f-string 和普通）
  html = html.replace(/(f?["'][^"'\n]*["'])/g, '<span style="color:#fbbf24">$1</span>');
  // 关键字
  const keywords = ['from', 'import', 'while', 'for', 'in', 'range', 'True', 'False', 'None', 'if', 'else', 'elif', 'def', 'class', 'return', 'break', 'continue'];
  for (const kw of keywords) {
    html = html.replace(new RegExp(`\\b${kw}\\b`, 'g'), `<span style="color:#c084fc">${kw}</span>`);
  }
  // 函数调用
  html = html.replace(/(\w+)(\()/g, '<span style="color:#60a5fa">$1</span>$2');
  // 数字
  html = html.replace(/\b(\d+\.?\d*)\b/g, '<span style="color:#34d399">$1</span>');

  return html;
}

// ============ 主组件 ============
export default function CodeEditor({ onNavigate }: CodeEditorProps) {
  const [files, setFiles] = useState<CodeFile[]>(initialFiles);
  const [activeFile, setActiveFile] = useState(0);
  const [code, setCode] = useState(initialFiles[0].code);
  const [consoleOutput, setConsoleOutput] = useState<string[]>(['> MicroPython v1.24.0 on ESP32', '> Ready.']);
  const [isRunning, setIsRunning] = useState(false);
  const [saved, setSaved] = useState(false);
  const [dirty, setDirty] = useState(false);
  const stopRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const consoleRef = useRef<HTMLDivElement>(null);

  // 自动滚动控制台
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleOutput]);

  // 切换文件
  const switchFile = (idx: number) => {
    if (dirty) {
      // 保存当前文件内容
      setFiles(prev => prev.map((f, i) => i === activeFile ? { ...f, code } : f));
    }
    setActiveFile(idx);
    setCode(files[idx].code);
    setDirty(false);
  };

  // 编辑代码
  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCode(e.target.value);
    setDirty(true);
    setSaved(false);
  };

  // Tab 键支持
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      setCode(newCode);
      setDirty(true);
      // 恢复光标位置
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4;
        }
      }, 0);
    }
  };

  // 保存文件
  const handleSave = () => {
    setFiles(prev => prev.map((f, i) => i === activeFile ? { ...f, code } : f));
    setDirty(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // 运行代码
  const handleRun = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    stopRef.current = false;
    setConsoleOutput(['> 运行 ' + files[activeFile].name + ' ...']);

    // 模拟执行
    const result = simulatePython(code);
    const lines = result.output.split('\n').filter(l => l.trim());

    // 流式输出
    for (let i = 0; i < lines.length; i++) {
      if (stopRef.current) {
        setConsoleOutput(prev => [...prev, '> 程序已停止']);
        break;
      }
      await new Promise(r => setTimeout(r, 300));
      setConsoleOutput(prev => [...prev, lines[i]]);
    }

    if (!stopRef.current) {
      setConsoleOutput(prev => [...prev, '> 程序执行完毕']);
    }
    setIsRunning(false);
  }, [code, files, activeFile, isRunning]);

  // 停止运行
  const handleStop = () => {
    stopRef.current = true;
    setIsRunning(false);
  };

  // 清屏
  const handleClear = () => {
    setConsoleOutput([]);
  };

  // 行号
  const lineCount = code.split('\n').length;
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
      {/* ============ 工具栏 ============ */}
      <div className="flex items-center justify-between bg-slate-800 px-3 py-2 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-green-400" />
          <span className="text-xs font-mono text-slate-300">MicroPython REPL</span>
        </div>
        <div className="flex items-center gap-1.5">
          {/* 保存 */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={handleSave}
            disabled={saved || !dirty}
            className={`p-1.5 rounded-lg transition-colors ${
              saved ? 'bg-green-900 text-green-400' : dirty ? 'hover:bg-slate-700 text-slate-300' : 'text-slate-600'
            }`}
            title="保存"
          >
            {saved ? <Check className="h-4 w-4" /> : <Save className="h-4 w-4" />}
          </motion.button>

          {/* 运行/停止 */}
          {!isRunning ? (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={handleRun}
              className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1 text-white transition-colors"
            >
              <Play className="h-3 w-3" /> 运行
            </motion.button>
          ) : (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={handleStop}
              className="bg-red-600 hover:bg-red-500 px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1 text-white transition-colors"
            >
              <Square className="h-3 w-3" /> 停止
            </motion.button>
          )}
        </div>
      </div>

      {/* ============ 文件标签 ============ */}
      <div className="flex bg-slate-800 border-b border-slate-700 overflow-x-auto">
        {files.map((file, idx) => (
          <button
            key={file.name}
            onClick={() => switchFile(idx)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-mono border-r border-slate-700 transition-colors whitespace-nowrap ${
              idx === activeFile
                ? 'bg-slate-900 text-white border-t-2 border-t-green-500'
                : 'text-slate-400 hover:bg-slate-700/50'
            }`}
          >
            <FileCode className="h-3 w-3" />
            {file.name}
            {idx === activeFile && dirty && <span className="text-orange-400">●</span>}
          </button>
        ))}
      </div>

      {/* ============ 编辑器区域 ============ */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* 行号 */}
        <div className="bg-slate-800/50 text-slate-600 text-xs font-mono py-3 px-2 select-none text-right overflow-hidden">
          <pre>{lineNumbers}</pre>
        </div>

        {/* 代码编辑区（textarea + 高亮层） */}
        <div className="flex-1 relative overflow-auto">
          {/* 高亮显示层 */}
          <pre
            className="absolute inset-0 p-3 text-xs font-mono pointer-events-none whitespace-pre-wrap break-words"
            dangerouslySetInnerHTML={{ __html: highlightCode(code) + '\n' }}
          />
          {/* 透明 textarea */}
          <textarea
            ref={textareaRef}
            value={code}
            onChange={handleCodeChange}
            onKeyDown={handleKeyDown}
            spellCheck={false}
            className="absolute inset-0 p-3 text-xs font-mono bg-transparent text-transparent caret-white resize-none outline-none whitespace-pre-wrap break-words"
            style={{ caretColor: 'white' }}
          />
        </div>
      </div>

      {/* ============ 控制台 ============ */}
      <div className="h-40 bg-black border-t border-slate-700 flex flex-col">
        <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Terminal className="h-3 w-3 text-green-400" />
            <span className="text-[10px] text-slate-500 font-mono">Console Output</span>
            {isRunning && (
              <Loader2 className="h-3 w-3 text-green-400 animate-spin" />
            )}
          </div>
          <button
            onClick={handleClear}
            disabled={isRunning}
            className="text-slate-500 hover:text-slate-300 disabled:opacity-30 transition-colors"
            title="清屏"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
        <div ref={consoleRef} className="flex-1 overflow-y-auto p-3 text-xs font-mono space-y-0.5">
          {consoleOutput.map((line, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className={`whitespace-pre-wrap break-all ${
                line.startsWith('>') ? 'text-slate-500' : 'text-green-400'
              }`}
            >
              {line}
            </motion.div>
          ))}
          {isRunning && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              className="inline-block w-2 h-3 bg-green-400"
            />
          )}
        </div>
      </div>

      {/* ============ 状态栏 ============ */}
      <div className="flex items-center justify-between px-3 py-1 bg-slate-800 border-t border-slate-700 text-[10px] font-mono">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Code className="h-2.5 w-2.5" />
            {files[activeFile].name}
          </span>
          <span>{files[activeFile].desc}</span>
          {dirty && <span className="text-orange-400">未保存</span>}
          {saved && <span className="text-green-400">已保存</span>}
        </div>
        <div className="text-slate-600">
          ESP32 · UTF-8 · Python 3
        </div>
      </div>
    </div>
  );
}
