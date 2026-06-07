/**
 * 后端进程启动/停止模块
 * @module backend/launcher
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const waitPort = require('wait-port');
const { checkPortOccupation, forceKillPortProcess } = require('./port-manager');
const { healthCheck } = require('./health');

// ==================== 配置常量 ====================

const DEFAULT_BACKEND_PORT = 8000;
const DEFAULT_BACKEND_HOST = 'localhost';
const DEFAULT_BACKEND_START_TIMEOUT = 60000;  // 核心启动超时 60 秒
const MAX_RESTART_ATTEMPTS = 3;
const BACKEND_RESTART_DELAY = 3000;  // 崩溃后 3 秒重启

// 【P3-4修复】统一魔法数字为具名常量
const EXEC_SYNC_SHORT_TIMEOUT = 3000;
const PORT_WAIT_INTERVAL = 500;      // 端口等待间隔 500ms

// ==================== 模块级状态（闭包封装） ====================

let backendProcess = null;
let restartAttempts = 0;
let isStarting = false;
let isQuitting = false;

// 回调函数（由外部设置）
let onBackendStatus = null;
let onBackendReady = null;
let onBackendError = null;

// ==================== 辅助函数 ====================

/**
 * 获取后端脚本路径
 * @param {string} backendDir 后端目录
 * @param {boolean} isDev 是否开发模式
 * @returns {{ type: string, path: string }}
 */
function getBackendScriptPath(backendDir = null, isDev = false) {
  // 获取默认后端目录
  // __dirname 是 src/core/backend/，向上三级到 electron/ 根目录，再进入 backend/
  // 注意：实际后端在 G:\iMato\backend\，不是 electron/backend/
  const bDir = backendDir || path.join(__dirname, '..', '..', '..', '..', 'backend');
  
  // 生产环境使用 PyInstaller 打包的 exe
  if (!isDev && process.platform === 'win32') {
    const exePath = path.join(bDir, 'dist', 'main_ai_edu.exe');
    try {
      const fs = require('fs');
      if (fs.existsSync(exePath)) return { type: 'exe', path: exePath, cwd: bDir };
    } catch { /* 忽略 */ }
  }
  // 开发环境使用源码
  const scriptPath = path.join(bDir, 'main_ai_edu.py');
  return { type: 'script', path: scriptPath, cwd: bDir };
}

/**
 * 等待后端服务就绪（分阶段启动 Phase 1：仅等待核心 Tier 0 就绪）
 * @param {object} options 配置选项
 * @returns {Promise<boolean>}
 */
async function waitForBackend(options = {}) {
  const {
    backendHost = DEFAULT_BACKEND_HOST,
    backendPort = DEFAULT_BACKEND_PORT,
    timeout = DEFAULT_BACKEND_START_TIMEOUT,
    onProgress = null,
  } = options;

  const backendUrl = `http://${backendHost}:${backendPort}`;
  console.log(`[INFO] 等待后端服务启动 (${backendUrl})...`);

  if (onProgress) onProgress('waiting-backend', '等待后端服务就绪...', 50);

  const startTime = Date.now();
  const maxWaitTime = timeout;

  // 动态更新进度
  const progressInterval = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(50 + (elapsed / maxWaitTime) * 40, 85);
    if (onProgress) onProgress('waiting-backend', '等待后端服务就绪', progress);
  }, PORT_WAIT_INTERVAL);

  try {
    // 等待端口开放
    await waitPort({
      host: backendHost,
      port: backendPort,
      timeout: maxWaitTime,
      output: 'silent',
    });

    console.log('[INFO] 后端端口已开放，进行健康检查...');
    if (onProgress) onProgress('waiting-backend', '后端端口已开放，正在验证...', 70);

    // 持续进行健康检查，直到成功或超时
    let elapsed = Date.now() - startTime;
    let healthCheckAttempts = 0;
    const maxHealthCheckAttempts = Math.max(1, Math.floor((maxWaitTime - elapsed) / PORT_WAIT_INTERVAL));

    while (healthCheckAttempts < maxHealthCheckAttempts && elapsed < maxWaitTime) {
      const result = await healthCheck(backendHost, backendPort);

      if (result.success) {
        clearInterval(progressInterval);
        console.log('[INFO] 后端健康检查通过！');
        if (onProgress) onProgress('backend-ready', '后端服务就绪', 90);
        restartAttempts = 0; // 重置重启计数
        isStarting = false;
        return true;
      }

      healthCheckAttempts++;
      elapsed = Date.now() - startTime;

      // 如果健康检查失败且端口被其他程序占用，立即返回错误
      if (elapsed >= maxWaitTime * 0.8) {
        const portStatus = checkPortOccupation(backendPort);
        if (portStatus.occupied && !portStatus.processName.toLowerCase().includes('python')) {
          clearInterval(progressInterval);
          console.error('[ERROR] 端口被非 Python 进程占用，无法识别为 MatuX 后端服务');
          if (onProgress) onProgress('backend-error', '端口被其他程序占用', 0,
            `端口 ${backendPort} 被 ${portStatus.processName} (PID: ${portStatus.pid}) 占用`);
          return false;
        }
      }

      // 等待后再次检查
      await new Promise((r) => setTimeout(r, PORT_WAIT_INTERVAL));
    }

    // 健康检查超时
    clearInterval(progressInterval);

    // 检查是否是端口占用问题
    const finalPortStatus = checkPortOccupation(backendPort);
    if (finalPortStatus.occupied) {
      console.error(`[ERROR] 端口 ${backendPort} 被 ${finalPortStatus.processName} (PID: ${finalPortStatus.pid}) 占用`);
      if (onProgress) onProgress('backend-error', `端口 ${backendPort} 被占用`, 0,
        `检测到端口被 ${finalPortStatus.processName} 占用`);
    } else {
      console.error('[ERROR] 后端服务健康检查超时');
      if (onProgress) onProgress('backend-timeout', '后端启动超时', 0, '健康检查未能在规定时间内通过');
    }
    return false;

  } catch (error) {
    clearInterval(progressInterval);
    console.error('[ERROR] 后端服务启动超时:', error.message);
    if (onProgress) onProgress('backend-timeout', '后端启动超时', 0, error.message);
    return false;
  }
}

// ==================== 核心函数 ====================

/**
 * 启动 Python 后端服务
 * @param {object} options 配置选项
 * @returns {boolean} 是否成功启动
 */
function startBackend(options = {}) {
  const {
    pythonInfo,
    backendDir,
    isDev = false,
    backendPort = DEFAULT_BACKEND_PORT,
    onStatus = null,
  } = options;

  if (backendProcess) {
    console.log('[INFO] 后端已在运行中');
    return false;
  }
  if (isStarting) {
    console.log('[INFO] 后端正在启动中，跳过重复请求');
    return false;
  }
  isStarting = true;

  // 检查并清理占用端口的进程
  const portStatus = checkPortOccupation(backendPort);
  if (portStatus.occupied) {
    console.log(`[WARN] 端口 ${backendPort} 已被占用: ${portStatus.processName} (PID: ${portStatus.pid})`);
    if (onStatus) onStatus('clearing-port', '正在清理占用端口的进程...', 15);

    const killResult = forceKillPortProcess(backendPort);
    if (!killResult.success) {
      // 如果无法自动清理，返回错误
      if (onStatus) onStatus('port-conflict', `端口 ${backendPort} 被 ${portStatus.processName} 占用`, 0);
      isStarting = false;
      return false;
    }

    // 等待端口释放
    console.log('[INFO] 等待端口释放...');
    if (onStatus) onStatus('waiting-port', '等待端口释放...', 18);
    let waitCount = 0;
    while (checkPortOccupation(backendPort).occupied && waitCount < 10) {
      require('timers').setTimeout(() => { }, 500);
      waitCount++;
    }
  }

  if (!pythonInfo || !pythonInfo.available) {
    if (onStatus) onStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);
    isStarting = false;
    return false;
  }

  const backendInfo = getBackendScriptPath(backendDir, isDev);
  console.log(`[INFO] Python: ${pythonInfo.path} (${pythonInfo.version})`);
  console.log(`[INFO] 后端入口: ${backendInfo.path} (${backendInfo.type})`);

  if (onStatus) onStatus('starting-backend', '正在启动后端服务...', 20);

  if (backendInfo.type === 'exe') {
    // 生产环境：直接运行 PyInstaller 打包的 exe
    backendProcess = spawn(backendInfo.path, [], {
      cwd: backendDir,
      env: { ...process.env, PORT: backendPort.toString() },
      windowsHide: true,
    });
  } else {
    // 开发环境：运行 Python 脚本
    backendProcess = spawn(pythonInfo.path, [backendInfo.path], {
      cwd: backendDir,
      env: { ...process.env, PORT: backendPort.toString() },
      windowsHide: !isDev,
      shell: true,  // Windows 上需要 shell 才能识别 python 命令
    });
  }

  backendProcess.stdout.on('data', (data) => {
    const msg = data.toString().trim();
    if (msg) console.log(`[后端] ${msg}`);
  });

  backendProcess.stderr.on('data', (data) => {
    const msg = data.toString().trim();
    if (msg) console.error(`[后端错误] ${msg}`);
  });

  backendProcess.on('error', (err) => {
    console.error(`[ERROR] 后端进程启动失败: ${err.message}`);
    if (onStatus) onStatus('backend-error', '后端进程启动失败', 0, err.message);
    if (onBackendError) onBackendError(err.message);
    backendProcess = null;
    isStarting = false;
  });

  backendProcess.on('close', (code, signal) => {
    console.log(`[INFO] 后端服务已退出 (code: ${code}, signal: ${signal})`);
    isStarting = false;

    if (!isQuitting && restartAttempts < MAX_RESTART_ATTEMPTS) {
      restartAttempts++;
      console.log(`[INFO] ${BACKEND_RESTART_DELAY / 1000} 秒后尝试重启后端 (${restartAttempts}/${MAX_RESTART_ATTEMPTS})`);
      if (onStatus) onStatus('starting-backend', `后端异常退出，正在重启 (${restartAttempts}/${MAX_RESTART_ATTEMPTS})...`, 30);

      setTimeout(async () => {
        const started = startBackend(options);
        if (started) {
          const ready = await waitForBackend({
            backendHost: DEFAULT_BACKEND_HOST,
            backendPort,
            onProgress: onStatus,
          });
          if (ready && onBackendReady) {
            onBackendReady();
          }
        }
      }, BACKEND_RESTART_DELAY);
    } else if (!isQuitting) {
      if (onStatus) onStatus('backend-error', '后端多次启动失败，请检查日志', 0,
        `已尝试 ${MAX_RESTART_ATTEMPTS} 次，后端无法启动`);
      if (onBackendError) onBackendError(`后端多次启动失败，已尝试 ${MAX_RESTART_ATTEMPTS} 次`);
    }
  });

  return true;
}

/**
 * 停止后端服务
 * @note 增加优雅退出机制，避免 SIGKILL 直接杀死导致数据丢失
 */
function stopBackend() {
  if (!backendProcess) return;

  console.log('[INFO] 正在停止后端服务...');

  // 【P1-2修复】增加优雅退出等待时间，避免直接 SIGKILL 导致数据丢失
  if (process.platform === 'win32') {
    // Windows: 先尝试正常终止，给进程 3 秒优雅退出的时间
    try {
      const pid = parseInt(backendProcess.pid, 10);
      if (!isNaN(pid) && pid > 0) {
        // 先发送 SIGTERM 等效信号
        execSync(`taskkill /pid ${pid} /t`, { stdio: 'ignore', timeout: EXEC_SYNC_SHORT_TIMEOUT });
      }
    } catch {
      // 进程可能已经退出或权限不足
    }

    // 等待 3 秒让进程优雅退出
    const waitStart = Date.now();
    while (backendProcess && Date.now() - waitStart < 3000) {
      require('timers').setTimeout(() => { }, 100);
    }

    // 3 秒后仍未退出，强制终止
    if (backendProcess) {
      try {
        const pid = parseInt(backendProcess.pid, 10);
        if (!isNaN(pid) && pid > 0) {
          execSync(`taskkill /pid ${pid} /f /t`, { stdio: 'ignore' });
        }
      } catch {
        // 进程可能已经退出
      }
    }
  } else {
    // Unix/Linux/macOS: 使用信号机制
    backendProcess.kill('SIGTERM');

    // 等待 3 秒让进程优雅退出（增加等待时间避免数据丢失）
    setTimeout(() => {
      if (backendProcess) {
        try {
          backendProcess.kill('SIGKILL'); // 强制杀死
        } catch {
          // 进程可能已经退出
        }
      }
    }, 3000);
  }

  backendProcess = null;
}

/**
 * 重启后端服务
 * @param {object} options 重启选项
 * @returns {Promise<boolean>} 是否成功重启
 */
async function restartBackend(options = {}) {
  console.log('[INFO] 用户请求重启后端...');

  // 停止后端进程
  stopBackend();

  // 等待 2 秒后重启
  await new Promise((r) => setTimeout(r, 2000));

  restartAttempts = 0;
  isStarting = false;

  const started = startBackend(options);
  if (!started) return false;

  const ready = await waitForBackend({
    onProgress: options.onStatus,
  });

  return ready;
}

/**
 * 设置回调函数
 * @param {string} name 回调名称
 * @param {Function} fn 回调函数
 */
function setCallback(name, fn) {
  switch (name) {
    case 'onBackendStatus':
      onBackendStatus = fn;
      break;
    case 'onBackendReady':
      onBackendReady = fn;
      break;
    case 'onBackendError':
      onBackendError = fn;
      break;
  }
}

/**
 * 设置退出状态
 * @param {boolean} quitting 是否正在退出
 */
function setQuitting(quitting) {
  isQuitting = quitting;
}

// ==================== 状态访问器 ====================

/**
 * 获取后端进程对象
 * @returns {object|null}
 */
function getBackendProcess() {
  return backendProcess;
}

/**
 * 检查后端是否正在启动
 * @returns {boolean}
 */
function isBackendStarting() {
  return isStarting;
}

/**
 * 检查后端是否正在退出
 * @returns {boolean}
 */
function isBackendQuitting() {
  return isQuitting;
}

/**
 * 获取当前重启次数
 * @returns {number}
 */
function getRestartAttempts() {
  return restartAttempts;
}

// ==================== 导出 ====================

module.exports = {
  // 核心函数
  startBackend,
  stopBackend,
  waitForBackend,
  restartBackend,

  // 辅助函数
  getBackendScriptPath,

  // 回调设置
  setCallback,

  // 状态访问器
  getBackendProcess,
  isBackendStarting,
  isBackendQuitting,
  getRestartAttempts,
  setQuitting,

  // 配置常量（供外部使用）
  DEFAULT_BACKEND_PORT,
  DEFAULT_BACKEND_HOST,
  DEFAULT_BACKEND_START_TIMEOUT,
  MAX_RESTART_ATTEMPTS,
  BACKEND_RESTART_DELAY,
};
