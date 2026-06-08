/**
 * MatuX Electron 后端进程管理器
 * 
 * 负责后端服务的启动、停止、重启和健康检查
 * 
 * 【重构】本模块现在作为 BackendManager 类的最终实现位置
 * 底层工具函数已移至 src/core/backend/
 * 
 * 注意：为避免循环依赖，此模块直接从底层模块导入，不通过 src/core/backend/index.js
 */

const { spawn, execSync } = require('child_process');
const http = require('http');
const waitPort = require('wait-port');
const path = require('path');

// 【重构】直接从底层模块导入，避免循环依赖
const detector = require('../src/core/backend/detector');
const portManager = require('../src/core/backend/port-manager');
const health = require('../src/core/backend/health');

const {
  checkPortOccupation,
  forceKillPortProcess,
  findAvailablePort,
} = portManager;

const {
  httpGet,
  healthCheck,
} = health;

const {
  detectPython,
} = detector;

// 从 config/constants 导入配置常量（不会造成循环依赖）
const {
  BACKEND_URL,
  BACKEND_START_TIMEOUT,
  BACKEND_RESTART_DELAY,
  MAX_RESTART_ATTEMPTS,
  EXEC_SYNC_TIMEOUT,
  EXEC_SYNC_SHORT_TIMEOUT,
  isDev,
  BACKUP_PORTS,
} = require('../config/constants');

// 配置常量别名（与 src/core/backend/index.js 保持一致）
const DEFAULT_BACKEND_PORT = 8000;
const DEFAULT_BACKEND_HOST = 'localhost';

// 【重构】getBackendScriptPath 从 src/core/backend/launcher 导入（如果存在）
// 如果 launcher 不可用，使用内联实现
let getBackendScriptPath;
try {
  const launcher = require('../src/core/backend/launcher');
  getBackendScriptPath = launcher.getBackendScriptPath;
} catch {
  // 内联实现（向后兼容）
  getBackendScriptPath = function(backendDir = null, isDevMode = false) {
    const bDir = backendDir || path.join(__dirname, '..', 'backend');
    if (!isDevMode && process.platform === 'win32') {
      const exePath = path.join(bDir, 'dist', 'main_ai_edu.exe');
      if (require('fs').existsSync(exePath)) return { type: 'exe', path: exePath, cwd: bDir };
    }
    const scriptPath = path.join(bDir, 'main_ai_edu.py');
    return { type: 'script', path: scriptPath, cwd: bDir };
  };
}

class BackendManager {
  /**
   * @param {object} options 配置选项
   * @param {function} options.onReady 后端就绪回调
   * @param {function} options.onDisconnected 后端断开回调
   * @param {function} options.onReconnected 后端重连回调
   * @param {function} options.onStatusChange 状态变化回调
   * @param {function} options.onPortConflict 端口冲突回调，需要返回用户确认Promise<boolean>
   */
  constructor(options = {}) {
    this.process = null;
    this.isStarting = false;
    this.restartAttempts = 0;
    this.isQuitting = false;
    
    // 回调
    this.onReady = options.onReady || (() => {});
    this.onDisconnected = options.onDisconnected || (() => {});
    this.onReconnected = options.onReconnected || (() => {});
    this.onStatusChange = options.onStatusChange || (() => {});
    this.onPortConflict = options.onPortConflict || null; // 端口冲突交互回调
    
    // 状态
    this.overallStatus = 'unknown';
    this.currentPort = DEFAULT_BACKEND_PORT; // 当前使用的端口
  }

  /**
   * 启动后端服务
   * @param {function} splashReporter 启动画面报告函数
   */
  async start(splashReporter) {
    if (this.process) {
      console.log('[INFO] 后端已在运行中');
      return true;
    }
    
    if (this.isStarting) {
      console.log('[INFO] 后端正在启动中，跳过重复请求');
      return false;
    }
    
    this.isStarting = true;
    splashReporter?.('starting-backend', '正在启动后端服务...', 20);

    try {
      // 1. 端口冲突处理
      await this.ensurePortAvailable(splashReporter);

      // 2. 检测 Python 环境（使用 detector 模块）
      const pythonInfo = detectPython();
      if (!pythonInfo.available) {
        splashReporter?.('error', '未检测到 Python 3.9+ 环境', 0);
        this.isStarting = false;
        return false;
      }

      console.log(`[INFO] Python: ${pythonInfo.path} (${pythonInfo.version})`);
      splashReporter?.('starting-backend', '正在启动后端服务...', 25);

      // 3. 启动进程
      this.process = this.spawnBackend(pythonInfo);
      this.bindProcessEvents(splashReporter);
      
      return true;
    } catch (err) {
      console.error('[ERROR] 启动后端失败:', err.message);
      splashReporter?.('backend-error', '后端进程启动失败', 0, err.message);
      this.process = null;
      this.isStarting = false;
      return false;
    }
  }

  /**
   * 确保端口可用
   * 策略：
   * 1. 首先尝试自动终止MatuX相关进程（Python/Electron/Node）
   * 2. 如果失败，尝试使用备用端口
   * 3. 如果都无法处理，弹窗询问用户
   */
  async ensurePortAvailable(splashReporter) {
    const status = checkPortOccupation(this.currentPort);
    
    if (!status.occupied) {
      console.log(`[INFO] 端口 ${this.currentPort} 可用`);
      return true;
    }

    console.log(`[INFO] 端口 ${this.currentPort} 被 ${status.processName} (PID: ${status.pid}) 占用`);

    // 策略1: 尝试自动终止MatuX相关进程
    if (status.canAutoKill) {
      splashReporter?.('clearing-port', `正在清理占用端口的 ${status.processName} 进程...`, 15);
      const result = forceKillPortProcess(this.currentPort);
      
      if (result.success) {
        // 等待端口释放
        await this.waitForPortRelease(this.currentPort);
        console.log(`[INFO] 已自动清理端口 ${this.currentPort} 的占用进程`);
        return true;
      }
    }

    // 策略2: 尝试使用备用端口
    const availablePort = findAvailablePort(this.currentPort, BACKUP_PORTS);
    if (availablePort !== null && availablePort !== this.currentPort) {
      splashReporter?.('switching-port', `正在切换到备用端口 ${availablePort}...`, 15);
      this.currentPort = availablePort;
      console.log(`[INFO] 已切换到备用端口 ${this.currentPort}`);
      return true;
    }

    // 策略3: 弹窗询问用户
    if (this.onPortConflict && status.occupiedBy) {
      splashReporter?.('port-conflict', `端口 ${this.currentPort} 被 ${status.processName} 占用`, 0);
      
      const userConfirmed = await this.onPortConflict({
        port: this.currentPort,
        pid: status.pid,
        processName: status.processName,
        canAutoKill: status.canAutoKill,
      });
      
      if (userConfirmed) {
        // 用户确认后再次尝试终止
        const result = forceKillPortProcess(this.currentPort);
        if (result.success) {
          await this.waitForPortRelease(this.currentPort);
          return true;
        }
      }
    }

    // 如果是默认端口，尝试最后一个策略：使用备用端口启动
    if (this.currentPort === DEFAULT_BACKEND_PORT) {
      const lastResortPort = BACKUP_PORTS[BACKUP_PORTS.length - 1];
      console.log(`[WARN] 端口冲突无法解决，强制使用端口 ${lastResortPort}`);
      splashReporter?.('forcing-port', `端口冲突，强制使用端口 ${lastResortPort}`, 15);
      this.currentPort = lastResortPort;
      return true;
    }

    throw new Error(`端口 ${this.currentPort} 被 ${status.processName} (PID: ${status.pid}) 占用，无法启动后端`);
  }

  /**
   * 等待端口释放
   */
  async waitForPortRelease(port, maxWait = 5000) {
    const start = Date.now();
    while (checkPortOccupation(port).occupied && Date.now() - start < maxWait) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  /**
   * 启动后端进程
   */
  spawnBackend(pythonInfo) {
    const backendInfo = getBackendScriptPath();
    console.log(`[INFO] 后端入口: ${backendInfo.path} (${backendInfo.type})`);
    
    // 使用当前端口（可能是备用端口）
    const port = this.currentPort || DEFAULT_BACKEND_PORT;

    if (backendInfo.type === 'exe') {
      return spawn(backendInfo.path, [], {
        cwd: backendInfo.cwd,
        env: { ...process.env, PORT: port.toString() },
        windowsHide: true,
      });
    }

    return spawn(pythonInfo.path, [backendInfo.path], {
      cwd: backendInfo.cwd,
      env: { ...process.env, PORT: port.toString() },
      windowsHide: !isDev,
      shell: true,  // Windows 上需要 shell 才能识别 python 命令
    });
  }

  /**
   * 绑定进程事件
   */
  bindProcessEvents(splashReporter) {
    this.process.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) console.log(`[后端] ${msg}`);
    });

    this.process.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) console.error(`[后端错误] ${msg}`);
    });

    this.process.on('error', (err) => {
      console.error(`[ERROR] 后端进程启动失败: ${err.message}`);
      splashReporter?.('backend-error', '后端进程启动失败', 0, err.message);
      this.process = null;
      this.isStarting = false;
    });

    this.process.on('close', (code, signal) => {
      console.log(`[INFO] 后端服务已退出 (code: ${code}, signal: ${signal})`);
      this.isStarting = false;
      
      if (!this.isQuitting && this.restartAttempts < MAX_RESTART_ATTEMPTS) {
        this.handleUnexpectedExit(splashReporter);
      } else if (!this.isQuitting) {
        splashReporter?.('backend-error', '后端多次启动失败', 0,
          `已尝试 ${MAX_RESTART_ATTEMPTS} 次，后端无法启动`);
        this.onDisconnected();
      }
    });
  }

  /**
   * 处理意外退出
   */
  handleUnexpectedExit(splashReporter) {
    this.restartAttempts++;
    console.log(`[INFO] ${BACKEND_RESTART_DELAY / 1000} 秒后尝试重启后端 (${this.restartAttempts}/${MAX_RESTART_ATTEMPTS})`);
    splashReporter?.('starting-backend', `后端异常退出，正在重启 (${this.restartAttempts}/${MAX_RESTART_ATTEMPTS})...`, 30);
    
    setTimeout(async () => {
      this.process = null;
      const started = await this.start(splashReporter);
      if (started) {
        const ready = await this.waitForReady();
        if (ready) {
          this.onReconnected();
        }
      }
    }, BACKEND_RESTART_DELAY);
  }

  /**
   * 等待后端就绪
   * @param {number|object} timeoutOrOptions 超时时间（毫秒）或选项对象
   * @param {number} timeoutOrOptions.timeout 超时时间
   * @param {string} timeoutOrOptions.backendHost 后端主机
   * @param {number} timeoutOrOptions.backendPort 后端端口
   * @param {function} timeoutOrOptions.onProgress 进度回调
   */
  async waitForReady(timeoutOrOptions = BACKEND_START_TIMEOUT) {
    // 支持对象参数和数字参数
    let timeout = BACKEND_START_TIMEOUT;
    let backendHost = DEFAULT_BACKEND_HOST;
    let backendPort = DEFAULT_BACKEND_PORT;
    let onProgress = null;

    if (typeof timeoutOrOptions === 'object' && timeoutOrOptions !== null) {
      timeout = timeoutOrOptions.timeout || BACKEND_START_TIMEOUT;
      backendHost = timeoutOrOptions.backendHost || DEFAULT_BACKEND_HOST;
      backendPort = timeoutOrOptions.backendPort || DEFAULT_BACKEND_PORT;
      onProgress = timeoutOrOptions.onProgress || null;
    } else if (typeof timeoutOrOptions === 'number') {
      timeout = timeoutOrOptions;
    }

    console.log(`[INFO] 等待后端服务启动 (http://${backendHost}:${backendPort})...`);

    const healthChecker = new HealthChecker(backendHost, backendPort);

    try {
      // 等待端口开放
      await waitPort({
        host: backendHost,
        port: backendPort,
        timeout,
        output: 'silent',
      });

      console.log('[INFO] 后端端口已开放，进行健康检查...');

      // 等待健康检查通过
      const ready = await healthChecker.waitForHealthy(timeout * 0.8);

      if (ready) {
        console.log('[INFO] 后端健康检查通过！');
        this.restartAttempts = 0;
        this.isStarting = false;
        this.onReady();
        return true;
      }

      return false;
    } catch (error) {
      console.error('[ERROR] 后端服务启动超时:', error.message);
      return false;
    }
  }

  /**
   * 停止后端服务
   */
  stop() {
    if (!this.process) return;

    console.log('[INFO] 正在停止后端服务...');

    if (process.platform === 'win32') {
      this.terminateWindows();
    } else {
      this.process.kill('SIGTERM');
      setTimeout(() => {
        if (this.process) this.process.kill('SIGKILL');
      }, 3000);
    }

    this.process = null;
  }

  /**
   * Windows 下终止进程
   */
  terminateWindows() {
    try {
      const pid = parseInt(this.process?.pid, 10);
      if (!isNaN(pid) && pid > 0) {
        execSync(`taskkill /pid ${pid} /t`, { stdio: 'ignore', timeout: EXEC_SYNC_SHORT_TIMEOUT });
      }
    } catch {
      // 进程可能已退出
    }
    
    // 异步等待进程退出，不阻塞事件循环
    setTimeout(async () => {
      // 3 秒后检查进程是否仍在运行
      if (this.process) {
        try {
          const pid = parseInt(this.process?.pid, 10);
          if (!isNaN(pid) && pid > 0) {
            execSync(`taskkill /pid ${pid} /f /t`, { stdio: 'ignore' });
          }
        } catch {
          // 进程可能已经退出
        }
      }
    }, 3000);
  }

  /**
   * 重启后端
   */
  async restart(splashReporter) {
    console.log('[INFO] 用户请求重启后端...');
    
    this.stop();
    await new Promise(r => setTimeout(r, 2000));
    
    this.restartAttempts = 0;
    this.isStarting = false;
    
    const started = await this.start(splashReporter);
    if (started) {
      const ready = await this.waitForReady();
      this.onStatusChange(ready ? 'healthy' : 'unhealthy');
      return ready;
    }
    
    return false;
  }

  /**
   * 获取运行状态
   */
  isRunning() {
    return !!this.process;
  }

  /**
   * 获取当前状态
   */
  getStatus() {
    return this.overallStatus;
  }
}

/**
 * 健康检查器
 */
class HealthChecker {
  constructor(host, port) {
    this.host = host;
    this.port = port;
  }

  /**
   * 执行一次健康检查
   */
  async check(timeout = 5000) {
    const urls = [
      `http://${this.host}:${this.port}/health`,
      `http://${this.host}:${this.port}/`,
      `http://${this.host}:${this.port}/docs`,
    ];

    for (const url of urls) {
      const result = await this.httpGet(url, timeout);
      // 支持 2xx/3xx 状态码
      if (result.success && result.statusCode && result.statusCode >= 200 && result.statusCode < 400) {
        return { success: true, status: 'ok' };
      }
    }

    return { success: false, error: '所有健康检查端点都无法访问' };
  }

  /**
   * 等待健康检查通过
   */
  async waitForHealthy(timeout = 60000) {
    const start = Date.now();
    const interval = 500;

    while (Date.now() - start < timeout) {
      const result = await this.check();
      if (result.success) return true;
      await new Promise(r => setTimeout(r, interval));
    }

    return false;
  }

  /**
   * HTTP GET 请求
   */
  httpGet(url, timeout) {
    return new Promise((resolve) => {
      try {
        const urlObj = new URL(url);
        let hostname = urlObj.hostname;
        if (hostname === 'localhost') hostname = '127.0.0.1';

        const req = http.request({
          hostname,
          port: urlObj.port || 80,
          path: urlObj.pathname,
          method: 'GET',
          timeout,
        }, (res) => {
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
            resolve({ success: true, statusCode: res.statusCode, body });
          });
        });

        req.on('error', (err) => resolve({ success: false, error: err.message }));
        req.on('timeout', () => { req.destroy(); resolve({ success: false, error: '超时' }); });
        req.end();
      } catch (err) {
        resolve({ success: false, error: err.message });
      }
    });
  }
}

module.exports = { BackendManager, HealthChecker };
