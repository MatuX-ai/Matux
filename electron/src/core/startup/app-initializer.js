/**
 * 应用启动初始化模块
 * @module app-initializer
 *
 * 负责协调整个应用的启动流程
 */

const { app, BrowserWindow, Tray, Menu } = require('electron');
const fs = require('fs');
const path = require('path');

const { checkPythonEnvironment, verifyBackendHealth } = require('./python-checker');
const { BackendManager, HealthCheckService, preloadTier1Modules } = require('../../../services');
const { registerGlobalShortcuts, unregisterGlobalShortcuts } = require('../shortcuts');
const { checkForUpdates } = require('../updates');
const { loadWindowState, saveWindowState } = require('../utils/window-state');
const { checkPythonDeps } = require('../backend');

const {
  SPLASH_RENDER_DELAY,
  APP_PATHS,
  HEALTH_CHECK_INTERVAL,
  MODULE_STATUS_INTERVAL,
  isDev,
  BACKEND_HOST,
  BACKEND_PORT,
} = require('../../../config/constants');

/**
 * @typedef {Object} AppInitializerOptions
 * @property {Function} sendSplashStatus - 发送 Splash 状态回调
 * @property {Object} appState - 应用状态管理器
 * @property {Object} windowManager - 窗口管理器
 * @property {Function} showTrayNotification - 显示托盘通知回调
 */

/**
 * 应用启动器类
 */
class AppInitializer {
  constructor(options) {
    this.sendSplashStatus = options.sendSplashStatus;
    this.appState = options.appState;
    this.windowManager = options.windowManager;
    this.showTrayNotification = options.showTrayNotification;

    // 内部状态
    this.backendManager = null;
    this.healthCheckTimer = null;
    this.moduleStatusTimer = null;
    this.backendOverallStatus = 'unknown';
    this.moduleStatusCache = null;
    this.isQuitting = false;
    this.tray = null;
    this.pluginInstaller = null;
    this.pluginDownloader = null;
    this.pluginRegistry = null;
    this.phase5Initialized = false;
    this.updatesCheckScheduled = false;

    // 健康检查函数
    this._healthCheck = this._createHealthCheck();

    // 延迟加载的模块
    this.assessDevice = null;
    this.loadDeviceProfile = null;
    this.saveDeviceProfile = null;
    this.shouldReassess = null;
    this.PluginRecommendationEngine = null;
    this.InstallConfigManager = null;
    this.PluginStoreEnhancer = null;
    this.registerModuleIpcHandlers = null;

    this._loadOptionalModules();
  }

  /**
   * 加载可选模块
   */
  _loadOptionalModules() {
    // 设备评估
    try {
      const dp = require('../../../device-profiler');
      this.assessDevice = dp.assessDevice;
      this.loadDeviceProfile = dp.loadDeviceProfile;
      this.saveDeviceProfile = dp.saveDeviceProfile;
      this.shouldReassess = dp.shouldReassess;
    } catch (err) {
      console.warn('[WARN] device-profiler 模块加载失败:', err.message);
    }

    // Phase 5 模块
    try {
      this.PluginRecommendationEngine = require('../../../plugin-recommender').PluginRecommendationEngine;
    } catch (err) {
      console.warn('[WARN] plugin-recommender 模块加载失败:', err.message);
    }
    try {
      this.InstallConfigManager = require('../../../install-config').InstallConfigManager;
    } catch (err) {
      console.warn('[WARN] install-config 模块加载失败:', err.message);
    }
    try {
      this.PluginStoreEnhancer = require('../../../plugin-store-enhancer').PluginStoreEnhancer;
    } catch (err) {
      console.warn('[WARN] plugin-store-enhancer 模块加载失败:', err.message);
    }

    // 分阶段启动
    try {
      const phasedStartup = require('../../../phased-startup');
      this.registerModuleIpcHandlers = phasedStartup.registerModuleIpcHandlers;
    } catch (err) {
      console.warn('[WARN] phased-startup 模块加载失败:', err.message);
    }

    // 插件管理器
    try {
      this.PluginInstaller = require('../../../plugin-installer').PluginInstaller;
    } catch (err) {
      console.warn('[WARN] plugin-installer 模块加载失败:', err.message);
    }
    try {
      this.PluginDownloader = require('../../../plugin-downloader').PluginDownloader;
    } catch (err) {
      console.warn('[WARN] plugin-downloader 模块加载失败:', err.message);
    }
    try {
      this.PluginRegistry = require('../../../plugin-registry').PluginRegistry;
    } catch (err) {
      console.warn('[WARN] plugin-registry 模块加载失败:', err.message);
    }
  }

  /**
   * 创建健康检查函数
   */
  _createHealthCheck() {
    const { HEALTH_URL, HTTP_REQUEST_TIMEOUT } = require('../../../config/constants');
    return async () => {
      try {
        const http = require('http');
        return await new Promise((resolve) => {
          const req = http.get(HEALTH_URL, { timeout: HTTP_REQUEST_TIMEOUT }, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
              try {
                const json = JSON.parse(data);
                resolve({ success: true, data: json });
              } catch {
                resolve({ success: true });
              }
            });
          });
          req.on('error', (err) => resolve({ success: false, error: err.message }));
          req.on('timeout', () => { req.destroy(); resolve({ success: false, error: '请求超时' }); });
        });
      } catch (err) {
        return { success: false, error: err.message };
      }
    };
  }

  /**
   * 初始化后端管理器
   */
  _initBackendManager() {
    if (!this.backendManager) {
      this.backendManager = new BackendManager({
        onReady: () => {
          console.log('[INFO] 后端就绪');
        },
        onDisconnected: () => {
          console.warn('[WARN] 后端断开连接');
          this.appState.setBackendStatus('disconnected');
        },
        onReconnected: () => {
          console.log('[INFO] 后端重连成功');
          this.appState.setBackendStatus('healthy');
        },
        onStatusChange: (status) => {
          this.appState.setBackendStatus(status);
        },
      });
    }
    return this.backendManager;
  }

  /**
   * 执行完整的应用启动流程
   */
  async initialize() {
    const mainWindow = this.windowManager?.getMainWindow();

    // 1. Python 环境检测
    const pythonInfo = await checkPythonEnvironment({
      sendSplashStatus: this.sendSplashStatus,
    });

    if (!pythonInfo) {
      return false;
    }

    // 2. 启动后端
    const manager = this._initBackendManager();
    await manager.start(this.sendSplashStatus);

    // 3. 等待后端就绪
    const isReady = await manager.waitForReady({
      backendHost: BACKEND_HOST,
      backendPort: BACKEND_PORT,
      onProgress: this.sendSplashStatus,
    });

    if (!isReady) {
      console.error('[ERROR] 后端服务启动失败');
      return false;
    }

    // 4. 验证后端健康
    const healthCheck = this._healthCheck;
    const isHealthy = await verifyBackendHealth({
      sendSplashStatus: this.sendSplashStatus,
      healthCheck,
      backendManager: this.backendManager,
    });

    if (!isHealthy) {
      return false;
    }

    // 5. 启动健康检查
    this._startHealthCheck();

    // 6. 启动模块状态轮询
    this._startModuleStatusPolling();

    // 7. 初始化插件管理器
    await this._initializePlugins();

    // 8. 创建设备评估（延迟）
    setTimeout(() => this._initDeviceProfiler(), 1000);

    // 9. 初始化 Phase 5（延迟）
    setTimeout(() => this._initPhase5(), 1000);

    return true;
  }

  /**
   * 启动健康检查定时器
   */
  _startHealthCheck() {
    if (this.healthCheckTimer) clearInterval(this.healthCheckTimer);
    const healthCheckFn = this._healthCheck;
    if (!healthCheckFn) return;

    this.healthCheckTimer = setInterval(async () => {
      const result = await healthCheckFn();
      const mainWindow = this.windowManager?.getMainWindow();
      if (!result.success && !this.isQuitting) {
        console.warn('[WARN] 健康检查失败，后端可能已崩溃');
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('app-event', { type: 'backend-disconnected' });
        }
      }
    }, HEALTH_CHECK_INTERVAL);
  }

  /**
   * 启动模块状态轮询
   */
  _startModuleStatusPolling() {
    const { HEALTH_DETAIL_URL, HEALTH_CHECK_DETAIL_INTERVAL } = require('../../../config/constants');
    
    const poll = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_DETAIL_INTERVAL);
        const response = await fetch(HEALTH_DETAIL_URL, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!response.ok) return;

        const data = await response.json();
        const previousStatus = this.backendOverallStatus;
        this.backendOverallStatus = data.status || 'unknown';
        this.moduleStatusCache = data.modules || null;

        const mainWindow = this.windowManager?.getMainWindow();
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('backend:module-status', this.moduleStatusCache);
        }

        this._updateTrayStatus();

        if (previousStatus !== this.backendOverallStatus && mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('app-event', {
            type: 'backend-status-change',
            status: this.backendOverallStatus,
            previousStatus,
          });
        }
      } catch (err) {
        // 忽略轮询错误
      }
    };

    if (this.moduleStatusTimer) clearInterval(this.moduleStatusTimer);
    this.moduleStatusTimer = setInterval(poll, MODULE_STATUS_INTERVAL);
    poll();
  }

  /**
   * 更新托盘状态
   */
  _updateTrayStatus() {
    if (!this.tray) return;

    let statusLabel = '';
    let statusEmoji = '';

    switch (this.backendOverallStatus) {
      case 'healthy':
        statusLabel = '所有服务正常';
        statusEmoji = '🟢';
        break;
      case 'degraded':
        statusLabel = '部分模块降级运行';
        statusEmoji = '🟡';
        break;
      case 'unhealthy':
        statusLabel = '核心服务异常';
        statusEmoji = '🔴';
        break;
      default:
        statusLabel = '状态未知';
        statusEmoji = '⚪';
    }

    this.tray.setToolTip(`MatuX - ${statusLabel}`);

    // 构建模块摘要菜单项
    const moduleItems = [];
    if (this.moduleStatusCache?.summary) {
      const s = this.moduleStatusCache.summary;
      moduleItems.push({ label: `模块: ${s.active || 0}/${s.total || 0} 活跃`, enabled: false });
      if (s.degraded > 0) moduleItems.push({ label: `${s.degraded} 个模块降级`, enabled: false });
      if (s.failed > 0) moduleItems.push({ label: `${s.failed} 个模块失败`, enabled: false });
    }

    const mainWindow = this.windowManager?.getMainWindow();
    const menuItems = [
      {
        label: '显示主窗口',
        click: () => {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.show();
            mainWindow.focus();
          }
        },
      },
      { type: 'separator' },
      { label: `${statusEmoji} ${statusLabel}`, enabled: false },
      ...moduleItems,
      { type: 'separator' },
      { label: '重启后端', click: () => this._restartBackend() },
      { label: '学习提醒', click: () => this.showTrayNotification('学习提醒', '该继续今天的学习啦！') },
      { type: 'separator' },
      { label: '检查更新', click: () => this._checkForUpdates() },
      { type: 'separator' },
      {
        label: '退出 MatuX',
        click: () => {
          this.isQuitting = true;
          this.gracefulShutdown();
          app.quit();
        },
      },
    ];

    this.tray.setContextMenu(Menu.buildFromTemplate(menuItems));
  }

  /**
   * 创建系统托盘
   */
  createTray() {
    const iconPath = APP_PATHS.icon;
    if (!fs.existsSync(iconPath)) {
      console.warn('[WARN] 托盘图标不存在，跳过创建系统托盘');
      return;
    }

    this.tray = new Tray(iconPath);
    this.tray.setToolTip('MatuX - AI 编程学习平台');

    this._updateTrayStatus();

    this.tray.on('double-click', () => {
      const mainWindow = this.windowManager?.getMainWindow();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.show();
        mainWindow.focus();
      }
    });
  }

  /**
   * 初始化插件管理器
   */
  async _initializePlugins() {
    try {
      console.log('[INFO] 初始化插件管理器...');
      if (this.PluginInstaller) this.pluginInstaller = new this.PluginInstaller();
      if (this.PluginDownloader) this.pluginDownloader = new this.PluginDownloader();
      if (this.PluginRegistry) {
        this.pluginRegistry = new this.PluginRegistry();
        await this.pluginRegistry.initialize();
      }
      console.log('[INFO] ✓ 插件管理器初始化完成');
    } catch (err) {
      console.warn('[WARN] 插件管理器初始化失败（不阻塞启动）:', err.message);
    }
  }

  /**
   * 初始化设备评估
   */
  async _initDeviceProfiler() {
    try {
      if (!this.assessDevice || !this.loadDeviceProfile || !this.saveDeviceProfile || !this.shouldReassess) return;
      
      const existingProfile = this.loadDeviceProfile();
      if (!existingProfile || this.shouldReassess(existingProfile)) {
        const dp = await this.assessDevice();
        this.saveDeviceProfile(dp);
        console.log(`[INFO] 设备评级: ${dp.assessment.deviceClass} (${dp.assessment.score}分)`);
      } else {
        console.log(`[INFO] 使用缓存设备评级: ${existingProfile.assessment.deviceClass}`);
      }
    } catch (err) {
      console.warn('[WARN] 设备评估失败（不阻塞启动）:', err.message);
    }
  }

  /**
   * 初始化 Phase 5 模块
   */
  _initPhase5() {
    if (this.phase5Initialized) return;
    this.phase5Initialized = true;

    try {
      if (this.InstallConfigManager) new this.InstallConfigManager();
      if (this.PluginRecommendationEngine) new this.PluginRecommendationEngine();
      if (this.PluginStoreEnhancer) new this.PluginStoreEnhancer();
      console.log('[INFO] ✓ Phase 5 模块延迟初始化完成');
    } catch (err) {
      console.warn('[WARN] Phase 5 延迟初始化失败:', err.message);
    }
  }

  /**
   * 重启后端
   */
  async _restartBackend() {
    const { BACKEND_RESTART_DELAY } = require('../../../config/constants');
    if (!this.backendManager) return;
    this.backendManager.stop();
    await new Promise((r) => setTimeout(r, BACKEND_RESTART_DELAY));
    await this.backendManager.start(this.sendSplashStatus);
  }

  /**
   * 检查更新
   */
  async _checkForUpdates() {
    const mainWindow = this.windowManager?.getMainWindow();
    if (this.updatesCheckScheduled) return;
    this.updatesCheckScheduled = true;
    
    setTimeout(() => {
      checkForUpdates({ mainWindow, showNotification: this.showTrayNotification }).catch((err) => {
        console.warn('[WARN] 更新检查失败:', err.message);
      });
    }, 30000);
  }

  /**
   * 优雅关闭
   */
  gracefulShutdown() {
    if (this.isQuitting) return;
    this.isQuitting = true;

    try { unregisterGlobalShortcuts(); } catch (err) {
      console.error('[SHUTDOWN] 注销快捷键失败:', err.message);
    }

    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }

    if (this.moduleStatusTimer) {
      clearInterval(this.moduleStatusTimer);
      this.moduleStatusTimer = null;
    }

    try { this.backendManager?.stop(); } catch (err) {
      console.error('[SHUTDOWN] 停止后端失败:', err.message);
    }

    if (this.tray) {
      try { this.tray.destroy(); } catch (err) {
        console.error('[SHUTDOWN] 销毁托盘失败:', err.message);
      }
      this.tray = null;
    }

    BrowserWindow.getAllWindows().forEach((win) => {
      if (!win.isDestroyed()) win.destroy();
    });
  }

  /**
   * 获取后端管理器
   */
  getBackendManager() {
    return this.backendManager;
  }

  /**
   * 设置退出状态
   */
  setQuitting(value) {
    this.isQuitting = value;
  }
}

module.exports = {
  AppInitializer,
};
