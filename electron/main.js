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

// 窗口管理器引用（用于 macOS activate 事件）
const windowManager = {
  getMainWindow: () => mainWindow,
};

// ==================== 窗口创建 ====================

/**
 * 创建 Splash Screen 窗口
 */
function createSplashWindow() {
  // 验证 Splash preload 脚本路径
  if (!APP_PATHS.preloadSplash || !fs.existsSync(APP_PATHS.preloadSplash)) {
    console.error('[Main] Splash preload 脚本不存在:', APP_PATHS.preloadSplash);
    throw new Error(`Splash preload 脚本不存在: ${APP_PATHS.preloadSplash}`);
  }
  
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
  // 验证 preload 脚本路径
  if (!APP_PATHS.preload || !fs.existsSync(APP_PATHS.preload)) {
    console.error('[Main] Preload 脚本不存在:', APP_PATHS.preload);
    throw new Error(`Preload 脚本不存在: ${APP_PATHS.preload}`);
  }
  
  const savedState = loadWindowState();
  
  // 验证 savedState 的有效性
  const validateWindowState = (state) => {
    if (!state || typeof state !== 'object') return {};
    // 【安全】使用 Object.create(null) 创建无原型对象，防止原型链污染
    const result = Object.create(null);
    if (typeof state.width === 'number' && state.width > 0) result.width = state.width;
    if (typeof state.height === 'number' && state.height > 0) result.height = state.height;
    if (typeof state.x === 'number' && state.x >= 0) result.x = state.x;
    if (typeof state.y === 'number' && state.y >= 0) result.y = state.y;
    if (typeof state.isMaximized === 'boolean') result.isMaximized = state.isMaximized;
    return result;
  };
  
  const validatedState = validateWindowState(savedState);

  mainWindow = new BrowserWindow({
    width: validatedState.width || DEFAULT_WINDOW_SIZE.width,
    height: validatedState.height || DEFAULT_WINDOW_SIZE.height,
    minWidth: 1024,
    minHeight: 768,
    x: validatedState.x,
    y: validatedState.y,
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
  if (validatedState.isMaximized) mainWindow.maximize();

  // 加载前端应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:4200');
    // 【安全】仅在开发模式下打开DevTools
    if (isDev && process.env.NODE_ENV !== 'production') {
      mainWindow.webContents.openDevTools();
    }
  } else {
    console.log('[Main] Loading frontend from:', APP_PATHS.frontendIndex);

    // 重试计数器
    let loadAttempts = 0;
    const maxAttempts = 3;
    const retryDelay = 2000;

    const attemptLoad = () => {
      loadAttempts++;
      mainWindow.loadFile(APP_PATHS.frontendIndex)
        .then(() => {
          console.log('[Main] Frontend loaded successfully');
        })
        .catch((err) => {
          console.error(`[Main] Failed to load frontend (attempt ${loadAttempts}/${maxAttempts}):`, err.message);

          if (loadAttempts < maxAttempts) {
            // 尝试重新加载
            console.log(`[Main] Retrying in ${retryDelay}ms...`);
            setTimeout(attemptLoad, retryDelay);
          } else {
            // 达到最大重试次数，发送错误事件
            console.error('[Main] Max load attempts reached, frontend unavailable');
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('app-event', {
                type: 'frontend-load-error',
                error: '前端资源加载失败',
                detail: err.message,
                recoverable: false
              });
            }
          }
        });
    };

    attemptLoad();
  }

  // 监听页面加载错误
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[Main] Page failed to load:', errorCode, errorDescription);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', {
        type: 'page-load-failed',
        errorCode,
        errorDescription
      });
    }
  });

  mainWindow.webContents.on('crashed', (event, killed) => {
    console.error('[Main] Renderer process crashed! killed:', killed);
    // 尝试通知用户并提供恢复选项
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', {
        type: 'renderer-crashed',
        killed
      });
    }
    // 如果未被 kill，尝试恢复
    if (!killed) {
      console.log('[Main] 尝试恢复渲染进程...');
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.reload();
        }
      }, 1000);
    }
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
  let resizeTimeout = null;
  mainWindow.on('resize', () => {
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        const [w, h] = mainWindow.getSize();
        mainWindow.webContents.send('app-event', { type: 'window-resize', width: w, height: h });
        saveWindowState(mainWindow);
      }
    }, 200);
  });

  // 窗口移动（防抖）
  let moveTimeout = null;
  mainWindow.on('move', () => {
    if (moveTimeout) clearTimeout(moveTimeout);
    moveTimeout = setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        saveWindowState(mainWindow);
      }
    }, 500);
  });

  // 最小化到托盘
  mainWindow.on('close', (event) => {
    // 清理定时器
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
      resizeTimeout = null;
    }
    if (moveTimeout) {
      clearTimeout(moveTimeout);
      moveTimeout = null;
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
    if (!isQuitting && appInitializer?.tray) {
      event.preventDefault();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.hide();
      }
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
            // 验证响应格式
            if (json && typeof json === 'object' && 'status' in json) {
              resolve({ success: true, data: json });
            } else {
              // 响应格式不正确
              console.warn('[Health] 健康检查响应格式无效:', json);
              resolve({ success: false, error: 'Invalid health check response format' });
            }
          } catch {
            // JSON 解析失败
            console.warn('[Health] 健康检查响应不是有效 JSON');
            resolve({ success: false, error: 'Invalid JSON response' });
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
  // 验证 preload 脚本路径
  const preloadPath = APP_PATHS.preload;
  if (!preloadPath || !fs.existsSync(preloadPath)) {
    console.error('[Main] 子窗口 preload 脚本不存在:', preloadPath);
    return null;
  }

  const childWindow = new BrowserWindow({
    width: data.width || 1200,
    height: data.height || 800,
    title: data.title || 'MatuX - 子窗口',  // 【修复】设置默认窗口标题
    parent: mainWindow,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,  // 启用沙箱
    },
  });

  if (data.url) {
    // 验证 URL 安全性
    const urlValidation = validateExternalUrl(data.url);
    if (!urlValidation.valid) {
      console.error('[Main] 子窗口 URL 不安全:', urlValidation.error);
      childWindow.close();
      return null;
    }
    childWindow.loadURL(data.url);
  } else if (data.html) {
    // 【安全】禁用 data:text/html 加载以防止 XSS 攻击
    // Electron 的 data:text/html 可能执行恶意脚本
    console.warn('[Main] 拒绝加载内联 HTML 内容以防止 XSS 攻击');
    childWindow.close();
    return null;
  }

  return childWindow;
}

// ==================== 文件关联 ====================

// 【重构】文件解析服务
const { isValidFileName, safeReadFile, getFileType } = require('./services/file-parser');

/**
 * 安全验证文件名（防止绕过检查如 test.imato.exe）
 * @deprecated 使用 services/file-parser.js 中的 isValidFileName
 */
function isValidFileName_deprecated(fileName) {
  if (!fileName || typeof fileName !== 'string') return false;
  const lastDotIndex = fileName.lastIndexOf('.');
  if (lastDotIndex === -1 || lastDotIndex === 0) return false;
  const actualExtension = fileName.substring(lastDotIndex + 1).toLowerCase();
  const dangerousExtensions = ['exe', 'bat', 'cmd', 'ps1', 'sh', 'js', 'ts', 'py', 'com', 'pif', 'msc', 'hta', 'scr', 'vbs', 'wsf', 'jar'];
  const lowerFileName = fileName.toLowerCase();
  for (const ext of dangerousExtensions) {
    if (lowerFileName.endsWith('.' + ext)) return false;
    if (lowerFileName.includes('.' + ext + '.')) return false;
  }
  const baseName = fileName.substring(0, lastDotIndex);
  if (!/^[a-zA-Z0-9_-]+$/.test(baseName)) return false;
  return true;
}

/**
 * 安全读取文件内容
 * @deprecated 使用 services/file-parser.js 中的 safeReadFile
 */
function safeReadFile_deprecated(filePath) {
  try {
    const normalizedPath = path.normalize(filePath);
    if (normalizedPath.includes('..') || normalizedPath.includes('~')) {
      return { success: false, error: '非法路径字符' };
    }
    const stats = fs.statSync(normalizedPath);
    if (stats.size > MAX_FILE_SIZE) {
      return { success: false, error: `文件过大 (${(stats.size / 1024 / 1024).toFixed(2)}MB)，最大支持 ${MAX_FILE_SIZE / 1024 / 1024}MB` };
    }
    const content = fs.readFileSync(normalizedPath, 'utf-8');
    return { success: true, content };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * 设置文件关联处理
 * 支持: .imato (课程包), .imblockly (Blockly项目), .imcircuit (电路项目)
 */
function setupFileAssociation() {
  // 发送文件事件到渲染进程的辅助函数
  const sendFileEvent = (filePath, result) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      if (result.success) {
        // 发送完整的文件数据（包括解析后的 JSON 和文件类型）
        mainWindow.webContents.send('app-event', {
          type: 'open-file',
          filePath,
          content: result.content,
          fileType: result.fileType,
        });
        console.log(`[INFO] 成功打开文件: ${filePath} (类型: ${result.fileType})`);
      } else {
        console.error('[ERROR] 读取文件失败:', result.error);
      }
    }
  };

  // macOS: open-file 事件
  app.on('open-file', (event, filePath) => {
    event.preventDefault();
    const fileName = path.basename(filePath);
    if (!isValidFileName(fileName)) {
      console.warn('[WARN] 拒绝打开不安全的文件:', filePath);
      return;
    }
    console.log('[INFO] macOS 文件关联打开:', filePath);
    const result = safeReadFile(filePath);
    sendFileEvent(filePath, result);
  });

  // Windows: 命令行参数
  const associatedFile = process.argv.find((arg) => {
    if (!arg || typeof arg !== 'string') return false;
    const fileName = path.basename(arg);
    return isValidFileName(fileName);
  });
  if (associatedFile && fs.existsSync(associatedFile)) {
    console.log('[INFO] Windows 命令行打开文件:', associatedFile);
    app.once('main-window-ready', () => {
      const result = safeReadFile(associatedFile);
      sendFileEvent(associatedFile, result);
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
    // 修复命名不一致: PluginStoreEnhancer -> pluginStoreEnhancer
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

  // 3. 创建主窗口
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

// 捕获未处理异常 - 先保存状态再尝试恢复
process.on('uncaughtException', (error) => {
  console.error('[FATAL] 未捕获的异常:', error);

  // 尝试通知 Splash/UI
  if (typeof sendSplashStatus === 'function' && splashWindow && !splashWindow.isDestroyed()) {
    sendSplashStatus('backend-error', `应用错误: ${error.message}`, 0);
  }

  // 尝试保存应用状态
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
    console.log('[Main] 状态已保存');
  } catch (saveError) {
    console.error('[Main] 保存状态失败:', saveError);
  }

  // 优雅关闭后端服务
  try {
    if (appInitializer?.gracefulShutdown) {
      appInitializer.gracefulShutdown();
    }
  } catch (shutdownError) {
    console.error('[Main] 关闭后端服务失败:', shutdownError);
  }

  // 延迟退出以确保日志写入和资源清理
  setTimeout(() => {
    process.exit(1);
  }, 3000);
});

// 捕获未处理的 Promise 拒绝
process.on('unhandledRejection', (reason, promise) => {
  console.error('[FATAL] 未处理的 Promise 拒绝:', reason);

  // 尝试保存状态
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
  } catch (saveError) {
    console.error('[Main] 保存状态失败:', saveError);
  }

  // 延迟退出
  setTimeout(() => {
    process.exit(1);
  }, 3000);
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
