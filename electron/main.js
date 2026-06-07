/**
 * MatuX Electron 主进程
 *
 * 负责：
 * 1. 协调各模块初始化
 * 2. 窗口管理
 * 3. IPC 安全通信桥接
 * 4. 应用生命周期管理
 *
 * 【重构】核心逻辑已抽取到独立模块：
 * - 后端管理: src/core/backend
 * - 启动流程: src/core/startup
 * - IPC 处理器: src/core/ipc/handlers
 * - 安全验证: src/core/security
 * - 窗口管理: src/ui/window-manager
 * - 托盘管理: src/ui/tray-manager
 * - 快捷键: src/core/shortcuts
 * - 自动更新: src/core/updates
 */

const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');

// 【重构】配置常量
const {
  BACKEND_PORT,
  BACKEND_HOST,
  BACKEND_URL,
  HEALTH_CHECK_INTERVAL,
  MODULE_STATUS_INTERVAL,
  MODULE_STATUS_CACHE_SIZE,
  EXEC_SYNC_TIMEOUT,
  MAX_FILE_SIZE,
  HTTP_REQUEST_TIMEOUT,
  HEALTH_CHECK_DETAIL_INTERVAL,
  PORT_WAIT_INTERVAL,
  HEALTH_URL,
  HEALTH_DETAIL_URL,
  MODULES_URL,
  isDev,
  WINDOW_STATE_FILE,
  DEFAULT_WINDOW_SIZE,
  SPLASH_WINDOW_SIZE,
  SPLASH_RENDER_DELAY,
  APP_PATHS,
  CRITICAL_PYTHON_PACKAGES,
  PYTHON_MIN_VERSION,
  ALLOWED_URL_PROTOCOLS,
  BACKEND_RESTART_DELAY,
  BACKEND_START_TIMEOUT,
  TIER1_PRELOAD_TIMEOUT,
  MAX_RESTART_ATTEMPTS,
} = require('./config/constants');

// 【重构】安全验证
const { validateExternalUrl, validateFilePath, getAllowedPaths } = require('./security');

// 【重构】后端核心模块
const backendCore = require('./src/core/backend');
const {
  detectPython,
  checkPythonDeps,
  checkPortOccupation,
  forceKillPortProcess,
  healthCheck,
  BackendManager,
} = backendCore;

// 【重构】AppState
const { AppState } = require('./core/app-state');
const appState = AppState.getInstance();

// 【重构】IPC Handlers
const {
  createBackendHandlers,
  createWindowHandlers,
  createNotificationHandlers,
  createSystemHandlers,
  createPluginHandlers,
  createFsHandlers,
} = require('./src/core/ipc/handlers');

// 【重构】窗口状态管理
const { loadWindowState, saveWindowState } = require('./src/core/utils/window-state');

// 【重构】快捷键管理
const { registerGlobalShortcuts, unregisterGlobalShortcuts } = require('./src/core/shortcuts');

// 【重构】自动更新
const { checkForUpdates } = require('./src/core/updates');

// 【重构】应用启动器
const { AppInitializer } = require('./src/core/startup/app-initializer');

// 【重构】服务层
const { preloadTier1Modules } = require('./services');

// 【重构】UI 模块
const { SplashManager, WindowManager, TrayManager, showNotification: showTrayNotification } = require('./src/ui');

// ==================== 全局状态 ====================

let mainWindow = null;
let splashWindow = null;
let appInitializer = null;
let isStarting = false;
let isQuitting = false;

// ==================== 窗口创建 ====================

/**
 * 创建 Splash Screen 窗口
 */
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: SPLASH_WINDOW_SIZE.width,
    height: SPLASH_WINDOW_SIZE.height,
    frame: false,
    transparent: false,
    resizable: false,
    alwaysOnTop: true,
    center: true,
    show: false,
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: APP_PATHS.preloadSplash,
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: APP_PATHS.icon,
  });

  splashWindow.loadFile(APP_PATHS.splashHtml);
  splashWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.show();
    }
  });
  splashWindow.on('closed', () => { splashWindow = null; });
}

/**
 * 创建主应用窗口
 */
function createMainWindow(windowManager) {
  const savedState = loadWindowState();

  mainWindow = new BrowserWindow({
    width: savedState.width || DEFAULT_WINDOW_SIZE.width,
    height: savedState.height || DEFAULT_WINDOW_SIZE.height,
    minWidth: 1024,
    minHeight: 768,
    x: savedState.x,
    y: savedState.y,
    show: false,
    webPreferences: {
      preload: APP_PATHS.preload,
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: APP_PATHS.icon,
    titleBarStyle: 'default',
    title: 'MatuX',
  });

  // 恢复最大化状态
  if (savedState.isMaximized) mainWindow.maximize();

  // 加载前端应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:4200');
    mainWindow.webContents.openDevTools();
  } else {
    console.log('[Main] Loading frontend from:', APP_PATHS.frontendIndex);
    mainWindow.loadFile(APP_PATHS.frontendIndex).catch((err) => {
      console.error('[Main] Failed to load frontend:', err);
    });
  }

  // 监听页面加载错误
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[Main] Page failed to load:', errorCode, errorDescription);
  });

  mainWindow.webContents.on('crashed', () => {
    console.error('[Main] Renderer process crashed!');
  });

  // 主窗口就绪后关闭 Splash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
  });

  // 窗口事件绑定
  mainWindow.on('closed', () => { mainWindow = null; });

  mainWindow.on('blur', () => mainWindow.webContents.send('app-event', { type: 'window-blur' }));
  mainWindow.on('focus', () => mainWindow.webContents.send('app-event', { type: 'window-focus' }));
  mainWindow.on('enter-full-screen', () => mainWindow.webContents.send('app-event', { type: 'fullscreen-enter' }));
  mainWindow.on('leave-full-screen', () => mainWindow.webContents.send('app-event', { type: 'fullscreen-leave' }));

  // 窗口大小变化（节流）
  let resizeTimeout;
  mainWindow.on('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      const [w, h] = mainWindow.getSize();
      mainWindow.webContents.send('app-event', { type: 'window-resize', width: w, height: h });
      saveWindowState(mainWindow);
    }, 200);
  });

  // 窗口移动（防抖）
  let moveTimeout;
  mainWindow.on('move', () => {
    clearTimeout(moveTimeout);
    moveTimeout = setTimeout(() => saveWindowState(mainWindow), 500);
  });

  // 最小化到托盘
  mainWindow.on('close', (event) => {
    saveWindowState(mainWindow);
    if (!isQuitting && appInitializer?.tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  return mainWindow;
}

// ==================== 工具函数 ====================

/**
 * 向 Splash 窗口发送状态更新
 */
function sendSplashStatus(phase, text, progress, detail, modules) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('splash-status', { phase, text, progress, detail, modules });
  }
  const prefix = phase === 'error' || phase === 'backend-error' ? '[ERROR]' : '[INFO]';
  console.log(`${prefix} ${text}`);
}

/**
 * 健康检查函数
 */
async function healthCheckWrapper() {
  try {
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
}

/**
 * 创建子窗口（用于数字孪生实验室等多窗口场景）
 */
function createChildWindow(data) {
  const childWindow = new BrowserWindow({
    width: data.width || 1200,
    height: data.height || 800,
    parent: mainWindow,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (data.url) {
    childWindow.loadURL(data.url);
  } else if (data.html) {
    childWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(data.html)}`);
  }

  return childWindow;
}

// ==================== 文件关联 ====================

/**
 * 安全读取文件内容
 */
function safeReadFile(filePath) {
  try {
    const stats = fs.statSync(filePath);
    if (stats.size > MAX_FILE_SIZE) {
      return { success: false, error: `文件过大 (${(stats.size / 1024 / 1024).toFixed(2)}MB)，最大支持 ${MAX_FILE_SIZE / 1024 / 1024}MB` };
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    return { success: true, content };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * 设置文件关联处理
 */
function setupFileAssociation() {
  // macOS
  app.on('open-file', (event, filePath) => {
    event.preventDefault();
    if (!filePath.endsWith('.imato')) return;
    console.log('[INFO] 通过文件关联打开:', filePath);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      const result = safeReadFile(filePath);
      if (result.success) {
        mainWindow.webContents.send('app-event', { type: 'open-file', filePath, content: result.content });
      }
    }
  });

  // Windows: 命令行参数
  const imatoFile = process.argv.find((arg) => arg.endsWith('.imato'));
  if (imatoFile && fs.existsSync(imatoFile)) {
    console.log('[INFO] 通过命令行参数打开文件:', imatoFile);
    app.once('main-window-ready', () => {
      const result = safeReadFile(imatoFile);
      if (result.success) {
        mainWindow.webContents.send('app-event', { type: 'open-file', filePath: imatoFile, content: result.content });
      }
    });
  }
}

// ==================== IPC 处理器注册 ====================

/**
 * 注册所有 IPC 处理器
 */
function registerIpcHandlers() {
  const backendHandlers = createBackendHandlers({ backendManager: appInitializer?.getBackendManager(), appState });
  backendHandlers.register();

  const windowHandlers = createWindowHandlers({ appState });
  windowHandlers.register();

  const notificationHandlers = createNotificationHandlers({ appState, showNotification: showTrayNotification });
  notificationHandlers.register();

  const systemHandlers = createSystemHandlers({ app, isDev });
  systemHandlers.register();

  const pluginHandlers = createPluginHandlers({
    appState,
    assessDevice: appInitializer?.assessDevice,
    loadDeviceProfile: appInitializer?.loadDeviceProfile,
    saveDeviceProfile: appInitializer?.saveDeviceProfile,
    shouldReassess: appInitializer?.shouldReassess,
    pluginInstaller: appInitializer?.pluginInstaller,
    pluginDownloader: appInitializer?.pluginDownloader,
    pluginRecommender: appInitializer?.PluginRecommendationEngine,
    installConfigManager: appInitializer?.InstallConfigManager,
    pluginStoreEnhancer: appInitializer?.PluginStoreEnhancer,
    pluginRegistry: appInitializer?.pluginRegistry,
  });
  pluginHandlers.register();

  const fsHandlers = createFsHandlers({ mainWindow, validateFilePath, dialog });
  fsHandlers.register();
}

// ==================== 应用生命周期 ====================

app.whenReady().then(async () => {
  // 1. 注册 IPC
  registerIpcHandlers();

  // 2. 创建 Splash
  createSplashWindow();
  await new Promise((r) => setTimeout(r, SPLASH_RENDER_DELAY));

  // 3. 创建主窗口（提前创建用于事件发送）
  const windowManager = { getMainWindow: () => mainWindow };
  createMainWindow(windowManager);

  // 4. 创建应用启动器
  appInitializer = new AppInitializer({
    sendSplashStatus,
    appState,
    windowManager,
    showTrayNotification,
  });

  // 5. 执行启动流程
  const success = await appInitializer.initialize();

  if (!success) {
    isStarting = false;
    return;
  }

  // 6. 注册快捷键
  registerGlobalShortcuts({
    mainWindow,
    onRestartBackend: () => appInitializer?._restartBackend(),
    onShowNotification: showTrayNotification,
  });

  // 7. 创建托盘
  appInitializer.createTray();

  // 8. 设置文件关联
  setupFileAssociation();

  // 9. 预加载 Tier 1 模块
  preloadTier1Modules();

  // 10. 通知主窗口就绪
  mainWindow.once('ready-to-show', () => {
    app.emit('main-window-ready');
  });

  // 11. 延迟检查更新
  setTimeout(() => {
    if (!appInitializer.updatesCheckScheduled) {
      appInitializer.updatesCheckScheduled = true;
      checkForUpdates({ mainWindow, showNotification: showTrayNotification }).catch((err) => {
        console.warn('[WARN] 更新检查失败:', err.message);
      });
    }
  }, 30000);

  isStarting = false;
});

// macOS 特殊处理
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    appInitializer?.gracefulShutdown();
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow(windowManager);
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  appInitializer?.gracefulShutdown();
});

// 捕获未处理异常
process.on('uncaughtException', (error) => {
  console.error('[FATAL] 未捕获的异常:', error);
  if (typeof sendSplashStatus === 'function' && splashWindow && !splashWindow.isDestroyed()) {
    sendSplashStatus('backend-error', `应用错误: ${error.message}`, 0);
  }
});

// ==================== 导出（用于测试） ====================
module.exports = {
  backendCore,
  createSplashWindow,
  createMainWindow,
  healthCheck: healthCheckWrapper,
  gracefulShutdown: () => appInitializer?.gracefulShutdown(),
  detectPython,
  createChildWindow,
  restartBackend: () => appInitializer?._restartBackend(),
  updateTrayStatus: () => appInitializer?._updateTrayStatus(),
};
