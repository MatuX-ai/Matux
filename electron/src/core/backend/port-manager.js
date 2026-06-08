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

const { execSync } = require('child_process');

// 【P3-4修复】统一魔法数字为具名常量
const EXEC_SYNC_TIMEOUT = 5000;
const EXEC_SYNC_SHORT_TIMEOUT = 3000;

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
 * 检查端口是否被占用，并识别占用进程
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

module.exports = {
  checkPortOccupation,
  forceKillPortProcess,
  cleanupMatuXProcesses,
  findAvailablePort,
};
