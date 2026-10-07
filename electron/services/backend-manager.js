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
const pythonDetector = require('../utils/python-detector');
const portManager = require('../src/core/backend/port-manager');
const health = require('../src/core/backend/health');
// 【复用模式修复】引入后端会话归属判定：区分 own-previous 与 foreign
const backendSession = require('../utils/backend-session');

const {
  checkPortOccupation,
  checkPortOccupationAsync,  // 【启动优化 P2-6】异步并行版本
  forceKillPortProcess,
  findAvailablePort,
  probeBackendHealth,
} = portManager;

const {
  httpGet,
  healthCheck,
} = health;

const {
  detectPython,
} = pythonDetector;

// 从 config/constants 导入配置常量（不会造成循环依赖）
const {
  BACKEND_URL,
  BACKEND_PORT,
  BACKEND_HOST,
  BACKEND_START_TIMEOUT,
  BACKEND_RESTART_DELAY,
  MAX_RESTART_ATTEMPTS,
  EXEC_SYNC_TIMEOUT,
  EXEC_SYNC_SHORT_TIMEOUT,
  isDev,
  BACKUP_PORTS,
} = require('../config/constants');

// 配置常量（从 config/constants 读取，支持环境变量覆盖）
const DEFAULT_BACKEND_PORT = BACKEND_PORT;
const DEFAULT_BACKEND_HOST = BACKEND_HOST;

// 【重构】getBackendScriptPath 统一从 config/constants 导入（支持环境变量覆盖）
// launcher.js 的同款实现已被合并，避免两处并行定义
const {
  getBackendScriptPath,
} = require('../config/constants');

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
    this.reusedExisting = false;             // 【先试后杀】是否复用了现有健康实例
    // 【复用模式修复】复用类型：
    //   undefined / null  - 非复用
    //   'foreign'         - 复用外部进程（未由本应用创建），自动重启会被短路
    //   'own-previous'    - 复用上次会话遗留的本应用后端，可正常处理
    this.reuseKind = null;
    // 复用场景下健康检查连续失败计数
    this.reuseHealthFailureCount = 0;
    // 本会话 ID（用于识别 spawn 的后端是否属本会话）
    this.sessionId = backendSession.getSessionId();
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
      const portResult = await this.ensurePortAvailable(splashReporter);

      // 【先试后杀】如果复用了现有健康实例，跳过 spawn，直接进入 ready 流程
      if (portResult.reused) {
        this.isStarting = false;
        this.process = null; // 复用模式下未拥有该进程
        this.reusedExisting = true;
        // reuseKind 已在 ensurePortAvailable() 里设好
        splashReporter?.('backend-ready', '复用现有后端服务成功', 90);
        // 【修复】复用场景下不再重复探活：ensurePortAvailable 已成功探活（最多3次重试）
        // waitForReady 的 HealthChecker 会做额外轮询，与探活重复
        // 这里直接触发 ready 回调，节省 5~10秒
        console.log(`[INFO] 复用场景：跳过重复探活，直接触发 ready 回调`);
        setImmediate(() => this.onReady());
        return true;
      }

      this.reusedExisting = false;
      this.reuseKind = null;

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
      // 【复用模式修复】记录本会话拥有的后端 PID，供下次启动时识别“本会话上轮进程”
      if (this.process?.pid) {
        const written = backendSession.writeOwnedSession(this.process.pid, this.sessionId);
        if (written) {
          console.log(`[INFO] 已记录本会话后端 PID=${this.process.pid}（session=${this.sessionId.slice(0, 8)}...）`);
        } else {
          console.warn('[WARN] 后端会话归属记录写入失败，下次启动可能误判为外部进程');
        }
      }

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
   * 策略【先试后杀】：
   * 0. 端口被占用时，先 HTTP 探活，识别是否是一个健康的 MatuX 后端
   *    - 探活成功：复用现有进程，跳过 spawn（节省 10~38s 启动时间）
   * 1. 探活失败，尝试自动终止MatuX相关进程（Python/Electron/Node）
   * 2. 如果失败，尝试使用备用端口
   * 3. 如果都无法处理，弹窗询问用户
   */
  async ensurePortAvailable(splashReporter) {
    // 【启动优化 P2-6】使用异步并行版本（TCP 探活 50ms，并行 netstat/PS）
    const status = await checkPortOccupationAsync(this.currentPort);

    if (!status.occupied) {
      console.log(`[INFO] 端口 ${this.currentPort} 可用`);
      // 【修复】补充 splash 状态报告（之前仅 console.log，未通知 splash）
      splashReporter?.('port-available', `后端端口 ${this.currentPort} 可用`, 10);
      return { reused: false };
    }

    console.log(`[INFO] 端口 ${this.currentPort} 被 ${status.processName} (PID: ${status.pid}) 占用`);

    // 【先试后杀】策略0：先 HTTP 探活，判断是否已是健康的 MatuX 后端
    splashReporter?.('probing-port', `检测到端口 ${this.currentPort} 占用，探活现有服务...`, 12);
    // 【启动优化 P0-3】使用 port-manager 默认值（2×1s），不显式覆盖
    const probe = await probeBackendHealth(this.currentPort, {
      host: DEFAULT_BACKEND_HOST,
    });
    if (probe.healthy) {
      this.reusedExisting = true;
      // 【复用模式修复】根据 session 记录判定占位进程是否为本会话私有
      //   - own-previous：是本应用上会话遗留的后端（SessionID 一致但 Electron 重启了），
      //     可以安全重起后能走起状态
      //   - foreign：外部进程，需走用户确认机制
      //   - null：无有效 session 记录（首次启动 / 记录过期），为保守起见标为 foreign
      let reuseKind = null;
      const ownership = backendSession.classifyPortHolder(status.pid);
      if (ownership.reason === 'previous-session' && ownership.sameSession) {
        reuseKind = 'own-previous';
      } else if (ownership.reason === 'current-session') {
        // 当前会话 - 在 reuse 场景下仅在 start 重试时可能命中，正常不会出现
        reuseKind = 'own-previous';
      } else {
        reuseKind = 'foreign';
      }
      this.reuseKind = reuseKind;
      const reuseKindLabel = reuseKind === 'own-previous' ? '本会话上轮进程' : '外部进程';
      console.log(`[INFO] 端口 ${this.currentPort} 上的现有服务健康（第 ${probe.attempts} 次探活成功），复用现有后端（${reuseKindLabel})，跳过启动`);
      splashReporter?.(reuseKind === 'foreign' ? 'reuse-foreign' : 'backend-reused',
        `复用现有后端服务 (端口 ${this.currentPort})`,
        85,
        { pid: status.pid, processName: status.processName, reuseKind });
      return { reused: true, pid: status.pid, processName: status.processName, reuseKind };
    }
    console.log(`[INFO] 端口 ${this.currentPort} 探活失败 (${probe.lastError})，按原有流程处理`);

    // 策略1: 尝试自动终止MatuX相关进程
    if (status.canAutoKill) {
      splashReporter?.('clearing-port', `正在清理占用端口的 ${status.processName} 进程...`, 15);
      const result = forceKillPortProcess(this.currentPort);

      if (result.success) {
        // 等待端口释放
        await this.waitForPortRelease(this.currentPort);
        console.log(`[INFO] 已自动清理端口 ${this.currentPort} 的占用进程`);
        return { reused: false };
      }
    }

    // 策略2: 尝试使用备用端口
    const availablePort = findAvailablePort(this.currentPort, BACKUP_PORTS);
    if (availablePort !== null && availablePort !== this.currentPort) {
      splashReporter?.('switching-port', `正在切换到备用端口 ${availablePort}...`, 15);
      this.currentPort = availablePort;
      console.log(`[INFO] 已切换到备用端口 ${this.currentPort}`);
      return { reused: false };
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
          return { reused: false };
        }
      }
    }

    // 如果是默认端口，尝试最后一个策略：使用备用端口启动
    if (this.currentPort === DEFAULT_BACKEND_PORT) {
      const lastResortPort = BACKUP_PORTS[BACKUP_PORTS.length - 1];
      console.log(`[WARN] 端口冲突无法解决，强制使用端口 ${lastResortPort}`);
      splashReporter?.('forcing-port', `端口冲突，强制使用端口 ${lastResortPort}`, 15);
      this.currentPort = lastResortPort;
      return { reused: false };
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

    // 【修复】不使用 shell:true，避免 Electron 环境下 spawn cmd.exe ENOENT
    // 显式设置 PATH 确保 python 命令可被找到
    const envWithPort = {
      ...process.env,
      PORT: port.toString(),
      PATH: process.env.PATH || 'C:\\Windows\\system32;C:\\Windows',
    };
    return spawn(pythonInfo.path, [backendInfo.path], {
      cwd: backendInfo.cwd,
      env: envWithPort,
      windowsHide: !isDev,
    });
  }

  /**
   * 绑定进程事件
   */
  bindProcessEvents(splashReporter) {
    this.process.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) {
        console.log(`[后端] ${msg}`);
        // 【修复】将真实 stdout 转发到 splash 窗口
        this.forwardLogToSplash('stdout', msg, splashReporter);
      }
    });

    this.process.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) {
        console.error(`[后端错误] ${msg}`);
        // 【修复】将真实 stderr 转发到 splash 窗口
        this.forwardLogToSplash('stderr', msg, splashReporter);
      }
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
   * 将后端进程的真实输出转发到 splash 窗口
   * @param {'stdout'|'stderr'} stream 输出流类型
   * @param {string} msg 输出消息（可能多行）
   * @param {function} splashReporter splash 报告器
   */
  forwardLogToSplash(stream, msg, splashReporter) {
    if (!splashReporter) return;
    // 多行日志逐行转发，避免一坨文本
    const lines = msg.split(/\r?\n/).filter((l) => l.trim().length > 0);
    for (const line of lines) {
      // 限制单行长度，避免 UI 溢出
      const trimmed = line.length > 200 ? line.slice(0, 200) + '…' : line;
      splashReporter('backend-log', trimmed, null, { stream });
    }
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
      // 【修复】早期过渡消息：只发 3 条就停，避免重复同一条消息
      const fallbackMessages = [
        '正在启动后端进程...',
        '初始化运行时环境...',
        '加载应用配置...',
      ];
      let progress = 30;
      let fallbackIndex = 0;
      const progressInterval = setInterval(() => {
        if (!onProgress || fallbackIndex >= fallbackMessages.length) {
          clearInterval(progressInterval);
          return;
        }
        const msg = fallbackMessages[fallbackIndex];
        onProgress('backend-loading', msg, progress);
        fallbackIndex++;
        progress += 10;
      }, 300);

      // 等待端口开放
      await waitPort({
        host: backendHost,
        port: backendPort,
        timeout,
        output: 'silent',
      });

      progress = 70;
      onProgress?.('backend-health-check', '后端端口已开放，进行健康检查...', 70);
      console.log('[INFO] 后端端口已开放，进行健康检查...');

      // 等待健康检查通过
      const ready = await healthChecker.waitForHealthy(timeout * 0.8);

      clearInterval(progressInterval);


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
    // 【先试后杀】复用现有进程时，不归本进程拥有，不应终止
    if (this.reusedExisting || !this.process) {
      if (this.reusedExisting) {
        console.log('[INFO] 后端为复用现有进程，跳过停止（不影响用户服务）');
      }
      // 复用进程在 graceful shutdown 时不需要清理 session 记录（不归我们管）
      return;
    }

    console.log('[INFO] 正在停止后端服务...');

    // 【复用模式修复】清理本会话的归属记录（避免下次启动误判）
    backendSession.clearOwnedSession();

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
   * 【复用模式修复】如果是复用场景，被复用的进程不是本应用 spawn 的，stop() 是 no-op。
   *   原实现会调 restart() -> stop() no-op -> start() -> 仍是复用 -> 循环。重啟：复用场景下委托
   *   forceRestart()（需用户确认后由调用方触发）。
   */
  async restart(splashReporter) {
    // 【复用模式修复】复用进程要归还：复用模式需要重新选杀，要到 forceRestart
    if (this.reusedExisting) {
      console.warn('[WARN] 重启请求落在复用模式下，转发到 forceRestart（需用户确认）');
      // 如果调用方未提供 fallback，这里返回 false，避免误导静默
      if (typeof splashReporter !== 'function' || !splashReporter.__allowUnconfirmedForce) {
        console.error('[ERROR] 复用模式下 restart() 仅支持 user-confirmed forceRestart，请走 IPC 通道');
        return false;
      }
    }

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
   * 【复用模式修复】强制重启：复用场景下的唯一重启机制。
   *   1. 解除 reusedExisting 短路
   *   2. 强杀占用 currentPort 的进程
   *   3. 走正常 spawn 路径拉起新后端
   *   4. 等待 ready
   *   调用方需在调此方法前获得用户确认（避免误杀用户手动启的后端）。
   *
   * @param {function} splashReporter 启动画面报告函数
   * @param {object} options 选项
   * @param {boolean} options.skipUserConfirmation 跳过用户确认（仅在调用方已确认时传 true）
   * @returns {Promise<boolean>} 是否重启成功
   */
  async forceRestart(splashReporter, options = {}) {
    if (!options.skipUserConfirmation) {
      console.warn('[WARN] forceRestart 必须由已确认的用户/调用方触发（请传 { skipUserConfirmation: true }）');
      return false;
    }

    console.log(`[INFO] 用户强制重启后端（先杀占位 PID）...`);
    splashReporter?.('force-restart', '正在强制重启后端（清理占位进程）...', 35);

    try {
      // 1. 解除复用短路，允许正常 spawn
      this.reusedExisting = false;
      this.isStarting = false;
      this.restartAttempts = 0;

      // 2. 强杀占位进程
      const killResult = forceKillPortProcess(this.currentPort);
      if (!killResult?.success) {
        const msg = killResult?.message || `未知错误（kill PID ${this.currentPort}）`;
        throw new Error(`强杀占位进程失败: ${msg}`);
      }
      console.log(`[INFO] 已强杀占位进程 (${killResult.killedPid ?? 'unknown'})`);

      // 3. 等待端口释放
      await this.waitForPortRelease(this.currentPort, 5000);

      // 4. 检测 Python（用户点强制重启后，可能要重新检测）
      const pythonInfo = detectPython();
      if (!pythonInfo.available) {
        throw new Error('未检测到 Python 环境，无法重新拉起后端');
      }
      console.log(`[INFO] Python: ${pythonInfo.path} (${pythonInfo.version})`);

      // 5. spawn 新后端
      this.process = this.spawnBackend(pythonInfo);
      this.bindProcessEvents(splashReporter);
      console.log(`[INFO] 已重新拉起后端进程 (PID=${this.process.pid})`);

      // 6. 等待 ready
      const ready = await this.waitForReady();
      if (ready) {
        this.onReady();
      } else {
        this.onDisconnected();
      }
      return ready;
    } catch (err) {
      console.error('[ERROR] 强制重启后端失败:', err.message);
      splashReporter?.('backend-error', '强制重启后端失败', 0, err.message);
      this.process = null;
      this.isStarting = false;
      return false;
    }
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
   * 【启动优化 P0-4】默认超时 5s → 1.5s（与 src/core/backend/health.js 一致）
   */
  async check(timeout = 1500) {
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
