/**
 * MatuX Electron 端口管理工具
 * 
 * 提供端口占用检测、进程清理等工具函数
 */

const { execSync } = require('child_process');
const { EXEC_SYNC_TIMEOUT } = require('../config/constants');

/**
 * 检查端口是否被占用，并识别占用进程
 * @param {number} port 端口号
 * @returns {{ occupied: boolean, pid: number | null, processName: string }}
 */
function checkPortOccupation(port) {
  if (process.platform !== 'win32') {
    return { occupied: false, pid: null, processName: '' };
  }

  // 首先尝试 netstat
  let pid = tryNetstat(port);

  // 如果 netstat 不可用，尝试 PowerShell
  if (pid === null) {
    pid = tryPowerShell(port);
  }

  if (pid === null) {
    return { occupied: false, pid: null, processName: '' };
  }

  // 获取进程名称
  const processName = getProcessName(pid);

  return { occupied: true, pid, processName };
}

/**
 * 使用 netstat 检测端口占用
 * @param {number} port 端口号
 * @returns {number | null} PID 或 null
 */
function tryNetstat(port) {
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
}

/**
 * 使用 PowerShell 检测端口占用
 * @param {number} port 端口号
 * @returns {number | null} PID 或 null
 */
function tryPowerShell(port) {
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
}

/**
 * 根据 PID 获取进程名称
 * @param {number} pid 进程 ID
 * @returns {string} 进程名称
 */
function getProcessName(pid) {
  try {
    const taskOutput = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
    });
    const match = taskOutput.match(/"([^"]+)"/);
    return match ? match[1] : 'Unknown';
  } catch {
    return 'Unknown';
  }
}

/**
 * 强制终止占用指定端口的进程
 * @param {number} port 端口号
 * @returns {{ success: boolean, killedPid: number | null, message: string }}
 */
function forceKillPortProcess(port) {
  if (process.platform !== 'win32') {
    return { success: false, killedPid: null, message: '仅支持 Windows 系统' };
  }

  const portStatus = checkPortOccupation(port);

  if (!portStatus.occupied) {
    return { success: true, killedPid: null, message: '端口未被占用' };
  }

  console.log(`[INFO] 发现端口 ${port} 被进程占用: PID ${portStatus.pid} (${portStatus.processName})`);

  // 检查是否是 MatuX 自身的 Python 进程
  if (portStatus.processName.toLowerCase().includes('python')) {
    try {
      execSync(`taskkill /pid ${portStatus.pid} /f`, {
        stdio: 'ignore',
        timeout: EXEC_SYNC_TIMEOUT,
      });
      console.log(`[INFO] 已终止占用端口 ${port} 的 Python 进程 (PID: ${portStatus.pid})`);
      return { success: true, killedPid: portStatus.pid, message: `已终止 Python 进程 (PID: ${portStatus.pid})` };
    } catch (err) {
      console.error(`[ERROR] 无法终止进程 ${portStatus.pid}:`, err.message);
      return { success: false, killedPid: portStatus.pid, message: `终止进程失败: ${err.message}` };
    }
  }

  // 其他进程，提供选项让用户决定
  return {
    success: false,
    killedPid: null,
    message: `端口被 ${portStatus.processName} (PID: ${portStatus.pid}) 占用，需要手动关闭`
  };
}

/**
 * 清理 MatuX 相关残留进程（仅开发环境）
 * @note 此函数会终止所有 Python 进程，仅在 isDev=true 时可用
 */
function cleanupMatuXProcesses() {
  const { isDev, EXEC_SYNC_SHORT_TIMEOUT } = require('../config/constants');

  if (!isDev) {
    console.debug('[DEBUG] cleanupMatuXProcesses 仅在开发环境可用');
    return;
  }

  console.log('[INFO] 正在检查 MatuX 残留进程（开发模式）...');

  if (process.platform !== 'win32') return;

  try {
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
};
