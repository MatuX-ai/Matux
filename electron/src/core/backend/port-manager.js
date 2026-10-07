/**
 * 端口占用管理模块
 * @module backend/port-manager
 * 
 * 支持功能：
 * - 端口占用检测与进程识别
 * - 自动终止MatuX相关进程（Python/Electron/Node）
 * - 备用端口查找
 * - 交互式确认清理
 */

const { execSync, execFile } = require('child_process');
const net = require('net');
const http = require('http');

// 【P3-4修复】统一魔法数字为具名常量
const EXEC_SYNC_TIMEOUT = 5000;
const EXEC_SYNC_SHORT_TIMEOUT = 3000;

// 【启动优化 P2-6】TCP 探活超时
const TCP_PROBE_TIMEOUT_MS = 300;   // 本地端口连接超时 300ms

// 【P-优化】探活默认值（【启动优化 P0-3】从 3×2s 缩短为 2×1s）
// 复用场景：1 次成功即可命中，节省 4-6s
// 不健康场景：1 次失败后立即杀进程，不需要继续探
const HEALTH_PROBE_TIMEOUT_MS = 1000;  // 单次请求超时 1s（从 2s 缩短）
const HEALTH_PROBE_MAX_RETRIES = 2;    // 重试 2 次（从 3 次减少）
const HEALTH_PROBE_PATHS = ['/health', '/', '/docs'];

/**
 * 查找可用的备用端口
 * @param {number} preferredPort 首选端口
 * @param {number[]} backupPorts 备用端口列表
 * @returns {number|null} 可用端口或null
 */
function findAvailablePort(preferredPort, backupPorts) {
  // 先检查首选端口
  if (!checkPortOccupation(preferredPort).occupied) {
    return preferredPort;
  }
  
  // 尝试备用端口
  for (const port of backupPorts) {
    if (!checkPortOccupation(port).occupied) {
      console.log(`[INFO] 首选端口 ${preferredPort} 被占用，切换到备用端口 ${port}`);
      return port;
    }
  }
  
  return null;
}

/**
 * 【启动优化 P2-6】TCP 快速探活：检测端口是否有服务在监听
 * 优势：比 netstat 快 3-5 倍（50-100ms vs 200-500ms）
 * 限制：只能判断是否被占用，不能识别进程
 * @param {number} port 端口号
 * @param {string} host 主机（默认 127.0.0.1）
 * @returns {Promise<boolean>} 是否有服务监听
 */
function isPortListening(port, host = '127.0.0.1') {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    let resolved = false;
    const finish = (result) => {
      if (resolved) return;
      resolved = true;
      try { socket.destroy(); } catch { /* 忽略 */ }
      resolve(result);
    };
    socket.setTimeout(TCP_PROBE_TIMEOUT_MS);
    socket.once('connect', () => finish(true));   // 连上 = 被占用
    socket.once('timeout', () => finish(false));  // 超时 = 未占用
    socket.once('error', (err) => {
      // ECONNREFUSED = 明确未占用；其他错误也当作未占用
      finish(err.code === 'ECONNREFUSED' ? false : false);
    });
    try {
      socket.connect(port, host);
    } catch {
      finish(false);
    }
  });
}

/**
 * 【启动优化 P2-6】异步并行执行 netstat + PowerShell，取最快结果
 * 原因：原串行方案最坏需 10s（netstat 失败 + PS 启动 5s）
 * 并行后取最快：最快 200ms（一个成功）
 * @param {number} port 端口号
 * @returns {Promise<number|null>} PID 或 null
 */
function probePortPidParallel(port) {
  return new Promise((resolve) => {
    let resolved = false;
    const finish = (pid) => {
      if (resolved) return;
      resolved = true;
      resolve(pid);
    };

    // Promise.race：第一个成功返回（非 null）就胜出
    const tryNetstatAsync = () => new Promise((res) => {
      execFile('netstat', ['-ano'], { encoding: 'utf-8', timeout: EXEC_SYNC_TIMEOUT }, (err, stdout) => {
        if (err) return res(null);
        try {
          const lines = stdout.split('\n').filter((line) => line.includes(`:${port}`) && line.includes('LISTENING'));
          if (lines.length === 0) return res(null);
          const match = lines[0].trim().match(/LISTENING\s+(\d+)/);
          res(match ? parseInt(match[1], 10) : null);
        } catch { res(null); }
      });
    });

    const tryPowerShellAsync = () => new Promise((res) => {
      const psCmd = `Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess`;
      execFile('powershell', ['-Command', psCmd], { encoding: 'utf-8', timeout: EXEC_SYNC_TIMEOUT }, (err, stdout) => {
        if (err) return res(null);
        const pid = parseInt(stdout.trim(), 10);
        res(isNaN(pid) ? null : pid);
      });
    });

    Promise.race([tryNetstatAsync(), tryPowerShellAsync()]).then((pid) => {
      if (pid) {
        finish(pid);
      } else {
        // 两个都返回 null，再 race 一次（防止空值快返回误判）
        Promise.race([tryNetstatAsync(), tryPowerShellAsync()]).then(finish);
      }
    });
  });
}

/**
 * 检查端口是否被占用，并识别占用进程
 * 【启动优化 P2-6】增加 async 版本 checkPortOccupationAsync
 * - 先 TCP connect 探活（快速路径：~50ms）→ 端口空闲直接返回
 * - 占用时并行 netstat + PowerShell 拿 PID（慢速路径）
 * 同步 checkPortOccupation 保持不变，供启动期以外场景使用
 * @param {number} port 端口号
 * @returns {{ occupied: boolean, pid: number | null, processName: string, canAutoKill: boolean }}
 */
async function checkPortOccupationAsync(port) {
  if (process.platform !== 'win32') {
    return { occupied: false, pid: null, processName: '', canAutoKill: false };
  }

  // 快速路径：TCP 探活
  const listening = await isPortListening(port);
  if (!listening) {
    return { occupied: false, pid: null, processName: '', canAutoKill: false };
  }

  // 慢速路径：并行 netstat + PowerShell 拿 PID
  const pid = await probePortPidParallel(port);
  if (pid === null) {
    return { occupied: true, pid: null, processName: 'Unknown', canAutoKill: false };
  }

  // 获取进程名称
  let processName = '';
  try {
    const taskOutput = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
    });
    const taskMatch = taskOutput.match(/"([^"]+)"/);
    if (taskMatch) {
      processName = taskMatch[1];
    }
  } catch {
    processName = 'Unknown';
  }

  const processNameLower = processName.toLowerCase();
  const canAutoKill = processNameLower.includes('python') ||
                      processNameLower.includes('electron') ||
                      processNameLower.includes('node');

  return { occupied: true, pid, processName, canAutoKill };
}

/**
 * 检查端口是否被占用，并识别占用进程（同步版本，保持向后兼容）
 * @param {number} port 端口号
 * @returns {{ occupied: boolean, pid: number | null, processName: string, canAutoKill: boolean }}
 */
function checkPortOccupation(port) {
  if (process.platform !== 'win32') {
    // 非 Windows 系统使用 lsof（简化实现）
    return { occupied: false, pid: null, processName: '', canAutoKill: false };
  }

  // 【P3-8修复】添加 netstat fallback 方案，避免精简 Windows 系统没有 netstat
  const tryNetstat = () => {
    try {
      const output = execSync(`netstat -ano | findstr :${port}`, {
        encoding: 'utf-8',
        timeout: EXEC_SYNC_TIMEOUT,
      });

      // 查找 LISTENING 状态的连接
      const lines = output.split('\n').filter(line => line.includes('LISTENING'));
      if (lines.length === 0) {
        return null;
      }

      // 提取 PID
      const match = lines[0].trim().match(/LISTENING\s+(\d+)/);
      if (!match) {
        return null;
      }

      return parseInt(match[1], 10);
    } catch {
      return null;
    }
  };

  const tryPowerShell = () => {
    try {
      const psCmd = `Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess`;
      const output = execSync(`powershell -Command "${psCmd}"`, {
        encoding: 'utf-8',
        timeout: EXEC_SYNC_TIMEOUT,
      });
      const pid = parseInt(output.trim(), 10);
      return isNaN(pid) ? null : pid;
    } catch {
      return null;
    }
  };

  // 首先尝试 netstat
  let pid = tryNetstat();

  // 如果 netstat 不可用，尝试 PowerShell
  if (pid === null) {
    console.debug('[DEBUG] netstat 不可用，尝试 PowerShell Get-NetTCPConnection');
    pid = tryPowerShell();
  }

  if (pid === null) {
    return { occupied: false, pid: null, processName: '', canAutoKill: false };
  }

  // 获取进程名称
  let processName = '';
  try {
    const taskOutput = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
    });
    const taskMatch = taskOutput.match(/"([^"]+)"/);
    if (taskMatch) {
      processName = taskMatch[1];
    }
  } catch {
    processName = 'Unknown';
  }

  // 判断是否可以自动终止（MatuX相关进程：Python/Electron/Node）
  const processNameLower = processName.toLowerCase();
  const canAutoKill = processNameLower.includes('python') || 
                      processNameLower.includes('electron') ||
                      processNameLower.includes('node');

  return { occupied: true, pid, processName, canAutoKill };
}

/**
 * 强制终止占用指定端口的进程
 * @param {number} port 端口号
 * @param {object} options 选项
 * @param {boolean} options.autoKillMatuX 自动终止MatuX相关进程（Python/Electron/Node）
 * @param {function} options.onConfirmKill 询问用户是否终止的回调
 * @returns {{ success: boolean, killedPid: number | null, message: string, requiresUserConfirmation?: boolean, occupiedBy?: object }}
 */
function forceKillPortProcess(port, options = {}) {
  const {
    autoKillMatuX = true,
    onConfirmKill = null,
  } = options;

  if (process.platform !== 'win32') {
    return { success: false, killedPid: null, message: '仅支持 Windows 系统' };
  }

  const portStatus = checkPortOccupation(port);

  if (!portStatus.occupied) {
    return { success: true, killedPid: null, message: '端口未被占用' };
  }

  console.log(`[INFO] 发现端口 ${port} 被进程占用: PID ${portStatus.pid} (${portStatus.processName})`);

  // 如果可以自动终止（MatuX相关进程）
  if (portStatus.canAutoKill && autoKillMatuX) {
    try {
      execSync(`taskkill /pid ${portStatus.pid} /f`, {
        stdio: 'ignore',
        timeout: EXEC_SYNC_TIMEOUT,
      });
      console.log(`[INFO] 已自动终止占用端口 ${port} 的进程 (PID: ${portStatus.pid})`);
      return { success: true, killedPid: portStatus.pid, message: `已终止 ${portStatus.processName} 进程 (PID: ${portStatus.pid})` };
    } catch (err) {
      console.error(`[ERROR] 无法终止进程 ${portStatus.pid}:`, err.message);
    }
  }

  // 如果提供了确认回调，尝试询问用户
  if (onConfirmKill) {
    return {
      success: false,
      killedPid: null,
      message: `端口被 ${portStatus.processName} (PID: ${portStatus.pid}) 占用`,
      requiresUserConfirmation: true,
      occupiedBy: portStatus,
    };
  }

  // 其他进程，提供选项让用户决定
  return {
    success: false,
    killedPid: null,
    message: `端口被 ${portStatus.processName} (PID: ${portStatus.pid}) 占用，需要手动关闭`,
    requiresUserConfirmation: true,
    occupiedBy: portStatus,
  };
}

/**
 * 清理 MatuX 相关残留进程
 * @note 此函数标记为仅开发调试用，会终止所有 Python 进程
 *       仅在 isDev=true 时可用，生产环境不应调用
 * @param {boolean} isDev 是否开发模式
 */
function cleanupMatuXProcesses(isDev = false) {
  // 仅在开发环境下可用
  if (!isDev) {
    console.debug('[DEBUG] cleanupMatuXProcesses 仅在开发环境可用');
    return;
  }

  console.log('[INFO] 正在检查 MatuX 残留进程（开发模式）...');

  if (process.platform !== 'win32') return;

  try {
    // 查找 Python 进程
    const pythonProcesses = execSync('tasklist /FI "IMAGENAME eq python*" /FO CSV /NH', {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
    });

    const lines = pythonProcesses.split('\n').filter(line => line.trim());
    let cleanedCount = 0;

    for (const line of lines) {
      const match = line.match(/"(python[^"]*)"\s+"(\d+)"/);
      if (match) {
        const [, processName, pid] = match;
        // 终止所有运行后端服务的 Python 进程
        try {
          execSync(`taskkill /pid ${pid} /f`, {
            stdio: 'ignore',
            timeout: EXEC_SYNC_SHORT_TIMEOUT,
          });
          cleanedCount++;
          console.log(`[INFO] 已清理残留进程: ${processName} (PID: ${pid})`);
        } catch {
          // 进程可能已经退出
        }
      }
    }

    if (cleanedCount > 0) {
      console.log(`[INFO] 共清理 ${cleanedCount} 个残留进程`);
    }
  } catch (err) {
    console.log('[INFO] 未发现需要清理的残留进程');
  }
}

/**
 * 对指定端口发起 HTTP 探活请求（单次）
 * @param {number} port 端口号
 * @param {string} host 主机（默认 localhost）
 * @param {number} timeoutMs 单次请求超时（毫秒）
 * @param {string[]} paths 探活路径列表
 * @returns {Promise<{alive: boolean, statusCode?: number, error?: string}>}
 */
function httpProbeOnce(port, host = 'localhost', timeoutMs = HEALTH_PROBE_TIMEOUT_MS, paths = HEALTH_PROBE_PATHS) {
  return new Promise((resolve) => {
    const hostname = host === 'localhost' ? '127.0.0.1' : host;
    let idx = 0;
    const tryNext = () => {
      if (idx >= paths.length) {
        resolve({ alive: false, error: '所有探活路径均失败' });
        return;
      }
      const path = paths[idx++];
      const req = http.request({
        hostname,
        port,
        path,
        method: 'GET',
        timeout: timeoutMs,
      }, (res) => {
        // 消费响应体后判定（2xx/3xx 视为存活）
        res.on('data', () => {});
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 400) {
            resolve({ alive: true, statusCode: res.statusCode });
          } else {
            tryNext();
          }
        });
      });
      req.on('error', () => tryNext());
      req.on('timeout', () => {
        try { req.destroy(); } catch { /* 忽略 */ }
        tryNext();
      });
      req.end();
    };
    tryNext();
  });
}

/**
 * 探活占用端口的进程，判断它是否运行着一个健康的 MatuX 后端服务
 * 【启动优化 P0-3】从 3×2s 缩短为 2×1s，共约 2.3s 探测窗口
 * - 复用场景：第 1 次成功就退出，平均 < 100ms
 * - 不健康场景：第 1 次失败就判定（反正要杀进程），最坏 ~2.3s
 * @param {number} port 端口号
 * @param {object} options 选项
 * @param {string} options.host 主机
 * @param {number} options.retries 重试次数（默认 2）
 * @param {number} options.timeoutMs 单次超时（默认 1000ms）
 * @returns {Promise<{healthy: boolean, attempts: number, lastError?: string}>}
 */
async function probeBackendHealth(port, options = {}) {
  const {
    host = 'localhost',
    retries = HEALTH_PROBE_MAX_RETRIES,
    timeoutMs = HEALTH_PROBE_TIMEOUT_MS,
  } = options;

  let lastError = '';
  for (let i = 1; i <= retries; i++) {
    const result = await httpProbeOnce(port, host, timeoutMs);
    if (result.alive) {
      return { healthy: true, attempts: i };
    }
    lastError = result.error || `HTTP ${result.statusCode}`;
    // 非最后一次重试才等待
    if (i < retries) {
      await new Promise((r) => setTimeout(r, 300));
    }
  }
  return { healthy: false, attempts: retries, lastError };
}

module.exports = {
  checkPortOccupation,
  // 【启动优化 P2-6】异步并行版本，供启动期热点路径使用
  checkPortOccupationAsync,
  isPortListening,
  forceKillPortProcess,
  cleanupMatuXProcesses,
  findAvailablePort,
  probeBackendHealth,
};
