/**
 * MatuX Electron 主进程持久化日志
 *
 * 【P0-静默退出】背景：
 *   打包后的应用没有可见控制台，console.* 输出无处落地。当出现
 *   uncaughtException / window-all-closed / 单实例锁失败等退出路径时，
 *   进程消失但磁盘上没有任何证据，表现为“应用静默退出”。
 *
 * 本模块职责：
 *   1. installConsoleTee() 把主进程所有 console 输出同时写入文件
 *   2. writeCrashReport() 为未捕获异常/子进程崩溃落盘 JSON 报告
 *   3. logEvent() 记录生命周期关键事件（退出请求、退出原因、心跳）
 *
 * 日志位置：<userData>/logs/main-YYYYMMDD.log（单文件 5MB 自动轮转）
 * 注意：全部使用同步写入，保证 process.exit / 崩溃前最后一条日志不丢。
 */

const fs = require('fs');
const path = require('path');
const { app } = require('electron');

const MAX_LOG_BYTES = 5 * 1024 * 1024;
const ROTATE_KEEP = 3;

let logDir = null;
let logFile = null;
let installed = false;
const originalConsole = {};

function resolveLogDir() {
  if (logDir) return logDir;
  try {
    logDir = path.join(app.getPath('userData'), 'logs');
  } catch (_) {
    // app 尚未 ready / 测试环境下退回工作目录
    logDir = path.join(process.cwd(), 'logs');
  }
  try {
    fs.mkdirSync(logDir, { recursive: true });
  } catch (_) {
    // 目录不可写时后续 append 会失败，write() 内部静默兜底
  }
  return logDir;
}

function todayStamp() {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}${mm}${dd}`;
}

function resolveLogFile() {
  if (logFile) return logFile;
  logFile = path.join(resolveLogDir(), `main-${todayStamp()}.log`);
  return logFile;
}

function rotateIfNeeded(file) {
  try {
    const st = fs.statSync(file);
    if (st.size <= MAX_LOG_BYTES) return;
    // 当前文件超限：重命名为带时间戳的历史文件，并清理最旧的
    fs.renameSync(file, file.replace(/\.log$/, `.${Date.now()}.log`));
    const dir = path.dirname(file);
    const base = path.basename(file).replace(/\.log$/, '');
    const olds = fs.readdirSync(dir)
      .filter((n) => n.startsWith(base + '.') && n.endsWith('.log'))
      .map((n) => ({ n, t: fs.statSync(path.join(dir, n)).mtimeMs }))
      .sort((a, b) => b.t - a.t);
    olds.slice(ROTATE_KEEP).forEach((o) => {
      try { fs.unlinkSync(path.join(dir, o.n)); } catch (_) { /* ignore */ }
    });
  } catch (_) {
    // 文件不存在 / 被占用：忽略
  }
}

function formatArg(arg) {
  if (typeof arg === 'string') return arg;
  if (arg instanceof Error) return `${arg.message}\n${arg.stack || ''}`;
  try {
    return JSON.stringify(arg);
  } catch (_) {
    return String(arg);
  }
}

function write(level, args) {
  const line = `[${new Date().toISOString()}] [${level}] ${args.map(formatArg).join(' ')}`;
  try {
    const file = resolveLogFile();
    rotateIfNeeded(file);
    fs.appendFileSync(file, line + '\n', 'utf8');
  } catch (_) {
    // 日志写入失败不得影响主流程
  }
  return line;
}

function log(...args) { return write('INFO', args); }
function warn(...args) { return write('WARN', args); }
function error(...args) { return write('ERROR', args); }

/**
 * 记录生命周期事件（结构化证据，便于事后 grep）
 * @param {string} tag 事件名，如 QUIT-REQUEST / WINDOW-ALL-CLOSED
 * @param {object} payload 附加数据
 */
function logEvent(tag, payload) {
  return write('EVENT', [`[${tag}]`, payload === undefined ? '' : payload]);
}

/**
 * 接管 console.*：文件留痕 + 保留原始终端输出（开发模式可读）
 */
function installConsoleTee() {
  if (installed) return;
  installed = true;

  ['log', 'info', 'warn', 'error', 'debug'].forEach((k) => {
    originalConsole[k] = typeof console[k] === 'function' ? console[k].bind(console) : () => {};
  });

  console.log = (...args) => { write('LOG', args); originalConsole.log(...args); };
  console.info = (...args) => { write('INFO', args); originalConsole.info(...args); };
  console.warn = (...args) => { write('WARN', args); originalConsole.warn(...args); };
  console.error = (...args) => { write('ERROR', args); originalConsole.error(...args); };
  console.debug = (...args) => { write('DEBUG', args); originalConsole.debug(...args); };
}

/**
 * 记录本次会话的元信息（启动时调用一次）
 */
function logSessionStart(extra = {}) {
  let version = 'unknown';
  try { version = app.getVersion(); } catch (_) { /* ignore */ }
  logEvent('SESSION-START', {
    appVersion: version,
    pid: process.pid,
    execPath: process.execPath,
    argv: process.argv,
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
    userData: (() => { try { return app.getPath('userData'); } catch (_) { return ''; } })(),
    logFile: resolveLogFile(),
    ...extra,
  });
}

/**
 * 崩溃/异常落盘：同一目录下生成 crash-<timestamp>-<kind>.json
 * @param {string} kind 类别，如 uncaughtException / unhandledRejection / render-process-gone
 * @param {Error|any} err 错误对象（可为任意值）
 * @param {object} extra 附加上下文
 * @returns {string} 报告文件路径（失败返回空串）
 */
function writeCrashReport(kind, err, extra = {}) {
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const file = path.join(resolveLogDir(), `crash-${ts}-${kind}.json`);
  let mem = {};
  try { mem = process.memoryUsage(); } catch (_) { /* ignore */ }
  const report = {
    kind,
    timestamp: new Date().toISOString(),
    pid: process.pid,
    uptimeSec: Math.round(process.uptime()),
    message: err && err.message ? err.message : String(err),
    stack: err && err.stack ? err.stack : '',
    memory: {
      rssMB: +(mem.rss / 1048576).toFixed(1),
      heapUsedMB: +(mem.heapUsed / 1048576).toFixed(1),
    },
    extra,
  };
  try {
    fs.writeFileSync(file, JSON.stringify(report, null, 2), 'utf8');
    write('ERROR', [`[CRASH-REPORT] ${file}`]);
    return file;
  } catch (e) {
    write('ERROR', ['[CRASH-REPORT] 写入失败:', e && e.message]);
    return '';
  }
}

module.exports = {
  installConsoleTee,
  logSessionStart,
  writeCrashReport,
  logEvent,
  log,
  warn,
  error,
  getLogFile: () => resolveLogFile(),
  getLogDir: () => resolveLogDir(),
};
