/**
 * MatuX Electron 主进程
 *
 * 负责：
 * 1. Splash Screen 启动画面
 * 2. Python 环境检测与引导安装
 * 3. 后端服务生命周期管理（启动/重启/关闭）
 * 4. 浏览器窗口创建与管理
 * 5. IPC 安全通信桥接
 * 6. 崩溃恢复与健康检查
 */

const { app, BrowserWindow, ipcMain, dialog, shell, Tray, Menu, Notification, globalShortcut } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const fs = require('fs');

// 导入分阶段启动模块
const { createPhasedStartup, registerModuleIpcHandlers } = require('./phased-startup');

// 导入设备评估引擎
const {
  assessDevice,
  loadDeviceProfile,
  saveDeviceProfile,
  shouldReassess,
} = require('./device-profiler');

// 导入插件管理器（Phase 2）
const { PluginInstaller, registerPluginInstallerIPC } = require('./plugin-installer');
const { PluginDownloader, registerPluginDownloaderIPC } = require('./plugin-downloader');
const { PluginRegistry } = require('./plugin-registry');

// 导入 Phase 5 推荐引擎和安装包精简模块
const { PluginRecommendationEngine } = require('./plugin-recommender');
const { InstallConfigManager } = require('./install-config');
const { PluginStoreEnhancer } = require('./plugin-store-enhancer');

// ==================== 配置 ====================

const BACKEND_PORT = 8000;
const BACKEND_HOST = 'localhost';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
const BACKEND_START_TIMEOUT = 5000;  // 核心启动超时 5 秒（仅等待 Tier 0 就绪）
const TIER1_PRELOAD_TIMEOUT = 15000; // Tier 1 预加载超时 15 秒（不阻塞 UI）
const BACKEND_RESTART_DELAY = 3000;  // 崩溃后 3 秒重启
const MAX_RESTART_ATTEMPTS = 3;
const HEALTH_CHECK_INTERVAL = 10000; // 健康检查间隔 10 秒
const MODULE_STATUS_INTERVAL = 5000; // 模块状态轮询间隔 5 秒

const HEALTH_URL = `${BACKEND_URL}/health`;
const HEALTH_DETAIL_URL = `${BACKEND_URL}/api/v1/system/health-detail`;
const MODULES_URL = `${BACKEND_URL}/api/v1/system/modules`;

const isDev = process.env.NODE_ENV === 'development';

// ==================== 路径常量 ====================

const APP_PATHS = {
  backendDir: path.join(__dirname, '..', 'backend'),
  frontendIndex: path.join(__dirname, '..', 'dist', 'imatuproject', 'index.html'),
  icon: path.join(__dirname, 'build', 'icon.ico'),
  preload: path.join(__dirname, 'preload.js'),
  preloadSplash: path.join(__dirname, 'preload-splash.js'),
  splashHtml: path.join(__dirname, 'splash.html'),
};

let splashWindow = null;
let mainWindow = null;
let backendProcess = null;
let healthCheckTimer = null;
let restartAttempts = 0;
let isQuitting = false;
let isStarting = false; // 防止 startBackend 并发调用
let tray = null;
let moduleStatusCache = null;  // 缓存模块状态
let moduleStatusTimer = null;  // 模块状态轮询定时器
let backendOverallStatus = 'unknown'; // 'healthy' | 'degraded' | 'unhealthy' | 'unknown'

// 插件管理器实例（Phase 2）
let pluginInstaller = null;
let pluginDownloader = null;
let pluginRegistry = null;

// Phase 5 推荐引擎和增强组件实例
let pluginRecommender = null;
let installConfigManager = null;
let pluginStoreEnhancer = null;

// ==================== 窗口状态持久化 ====================

const WINDOW_STATE_FILE = path.join(app.getPath('userData'), 'window-state.json');

function loadWindowState() {
  try {
    if (fs.existsSync(WINDOW_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(WINDOW_STATE_FILE, 'utf-8'));
    }
  } catch (_) { /* 忽略解析错误 */ }
  return { width: 1400, height: 900 };
}

function saveWindowState() {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  try {
    const bounds = mainWindow.getBounds();
    const isMaximized = mainWindow.isMaximized();
    fs.writeFileSync(WINDOW_STATE_FILE, JSON.stringify({
      ...bounds,
      isMaximized,
    }, null, 2));
  } catch (_) { /* 忽略写入错误 */ }
}

// ==================== 工具函数 ====================

/**
 * 检查 Python 版本是否 >= 3.9（语义版本号比较，避免 parseFloat 误判）
 * @param {string} versionStr 版本字符串，如 "3.12"
 * @returns {boolean}
 */
function isPythonVersionGte39(versionStr) {
  const parts = versionStr.split('.');
  const major = parseInt(parts[0], 10);
  const minor = parseInt(parts[1], 10);
  return major > 3 || (major === 3 && minor >= 9);
}

/**
 * 向 Splash 窗口发送状态更新
 */
function sendSplashStatus(phase, text, progress, detail, modules) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('splash-status', { phase, text, progress, detail, modules });
  }
  // 同时打印到控制台
  const prefix = phase === 'error' || phase === 'backend-error' ? '[ERROR]' : '[INFO]';
  console.log(`${prefix} ${text}`);
}

/**
 * 搜索 Windows 上常见的 Python 安装路径
 * @returns {string[]} 找到的 python.exe 路径列表
 */
function searchPythonPaths() {
  if (process.platform !== 'win32') return [];
  const found = new Set();

  // 方法1: 使用 py --list-paths 获取所有注册的 Python 安装
  try {
    const output = execSync('py --list-paths 2>&1', {
      encoding: 'utf-8',
      timeout: 5000,
      shell: true,
    });
    const regex = /-[\d.]+\s+(.+?python\.exe)/gi;
    let m;
    while ((m = regex.exec(output)) !== null) {
      found.add(m[1].replace(/\s*\*$/, '').trim());
    }
  } catch { /* py 命令不可用 */ }

  // 方法2: 检查常见安装目录（覆盖 C: 到 N: 的所有盘符）
  const drives = 'CDEFGHIJKLMN'.split('');
  const majorVersions = ['312', '311', '310', '39', '313'];
  const pathTemplates = [];
  for (const drive of drives) {
    for (const ver of majorVersions) {
      pathTemplates.push(`${drive}:\\Python${ver}\\python.exe`);
      pathTemplates.push(`${drive}:\\Program Files\\Python${ver}\\python.exe`);
    }
  }

  const userProfile = process.env.USERPROFILE || 'C:\\Users\\Default';
  for (const ver of majorVersions) {
    pathTemplates.push(`${userProfile}\\AppData\\Local\\Programs\\Python\\Python${ver}\\python.exe`);
  }

  for (const p of pathTemplates) {
    if (fs.existsSync(p)) found.add(p);
  }

  return [...found];
}

/**
 * 检测 Python 是否可用（自动搜索 PATH + 常见安装路径）
 * @returns {{ available: boolean, version: string, path: string }}
 */
function detectPython() {
  // Phase 1: 检查 PATH 命令
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py', 'py -3']
    : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const versionOutput = execSync(`"${cmd}" --version 2>&1`, {
        encoding: 'utf-8',
        timeout: 5000,
        shell: true,
      }).trim();
      const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
      if (versionMatch) {
        if (isPythonVersionGte39(versionMatch[1])) {
          return {
            available: true,
            version: versionMatch[1],
            path: cmd,
          };
        }
        console.warn(`[WARN] Python ${versionMatch[1]} 版本过低，需要 3.9+`);
      }
    } catch {
      // 该命令不可用，尝试下一个
    }
  }

  // Phase 2: 搜索常见安装路径（仅 Windows）
  if (process.platform === 'win32') {
    const searchedPaths = searchPythonPaths();
    for (const pyPath of searchedPaths) {
      try {
        const versionOutput = execSync(`"${pyPath}" --version 2>&1`, {
          encoding: 'utf-8',
          timeout: 5000,
        }).trim();
        const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
        if (versionMatch && isPythonVersionGte39(versionMatch[1])) {
          return {
            available: true,
            version: versionMatch[1],
            path: pyPath,
          };
        }
      } catch { /* 该路径不可执行，跳过 */ }
    }
  }

  return { available: false, version: '', path: '' };
}

/**
 * 检测 Python 关键依赖包是否安装
 * @param {object} pythonInfo detectPython 的返回值
 * @returns {string[]} 缺失的包名列表
 */
function checkPythonDeps(pythonInfo) {
  // 后端启动所必需的核心包（无此列表中的包将无法启动）
  const criticalPkgs = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 'python-jose', 'passlib', 'python-multipart'];

  try {
    const output = execSync(`"${pythonInfo.path}" -m pip list --format=columns 2>&1`, {
      encoding: 'utf-8',
      timeout: 15000,
      shell: true,
    });

    // 解析 pip list 输出，收集已安装的包名
    const installed = new Set();
    const lines = output.split('\n');
    for (const line of lines) {
      if (line.startsWith('---') || line.toLowerCase().startsWith('package')) continue;
      const pkgName = line.trim().split(/\s+/)[0];
      if (pkgName) installed.add(pkgName.toLowerCase());
    }

    // 检查哪些核心包缺失
    const missing = criticalPkgs.filter((pkg) => !installed.has(pkg.toLowerCase()));
    return missing;
  } catch (err) {
    console.warn('[WARN] 无法检查 Python 依赖包:', err.message);
    return []; // 无法检查时不阻塞启动
  }
}

/**
 * 获取后端脚本路径
 */
function getBackendScriptPath() {
  // 生产环境使用 PyInstaller 打包的 exe
  if (!isDev && process.platform === 'win32') {
    const exePath = path.join(APP_PATHS.backendDir, 'dist', 'main_ai_edu.exe');
    if (fs.existsSync(exePath)) return { type: 'exe', path: exePath };
  }
  // 开发环境使用源码
  const scriptPath = path.join(APP_PATHS.backendDir, 'main_ai_edu.py');
  return { type: 'script', path: scriptPath };
}

// ==================== 窗口管理 ====================

/**
 * 创建 Splash Screen 窗口
 */
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 520,
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
    splashWindow.show();
  });

  splashWindow.on('closed', () => {
    splashWindow = null;
  });
}

/**
 * 创建主应用窗口
 */
function createMainWindow() {
  const savedState = loadWindowState();

  mainWindow = new BrowserWindow({
    width: savedState.width || 1400,
    height: savedState.height || 900,
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
  if (savedState.isMaximized) {
    mainWindow.maximize();
  }

  // 加载前端应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:4200');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(APP_PATHS.frontendIndex);
  }

  // 主窗口就绪后关闭 Splash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 窗口失焦检测（防作弊用）
  mainWindow.on('blur', () => {
    mainWindow.webContents.send('app-event', { type: 'window-blur' });
  });

  mainWindow.on('focus', () => {
    mainWindow.webContents.send('app-event', { type: 'window-focus' });
  });

  // 全屏状态变化
  mainWindow.on('enter-full-screen', () => {
    mainWindow.webContents.send('app-event', { type: 'fullscreen-enter' });
  });

  mainWindow.on('leave-full-screen', () => {
    mainWindow.webContents.send('app-event', { type: 'fullscreen-leave' });
  });

  // 窗口大小变化（节流发送）
  let resizeTimeout;
  mainWindow.on('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      const [w, h] = mainWindow.getSize();
      mainWindow.webContents.send('app-event', {
        type: 'window-resize',
        width: w,
        height: h,
      });
      saveWindowState();
    }, 200);
  });

  // 窗口移动时保存位置（防抖）
  let moveTimeout;
  mainWindow.on('move', () => {
    clearTimeout(moveTimeout);
    moveTimeout = setTimeout(() => { saveWindowState(); }, 500);
  });

  // 最小化到托盘而非关闭
  mainWindow.on('close', (event) => {
    saveWindowState();
    if (!isQuitting && tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

// ==================== 子窗口管理 ====================

/** 子窗口集合 */
const childWindows = new Set();

/**
 * 创建子窗口（数字孪生实验室弹出窗口等）
 * PRD F-09 桌面端适配：多窗口模式
 */
function createChildWindow(options) {
  const width = options.width || 1280;
  const height = options.height || 800;
  const title = options.title || 'MatuX 实验窗口';
  const url = options.url || '';

  const childWin = new BrowserWindow({
    width,
    height,
    minWidth: 800,
    minHeight: 600,
    parent: mainWindow,
    webPreferences: {
      preload: APP_PATHS.preload,
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: APP_PATHS.icon,
    title,
  });

  // 加载页面
  // 绝对 URL（http/https）直接加载
  if (url.startsWith('http://') || url.startsWith('https://')) {
    childWin.loadURL(url);
  } else if (url.startsWith('/') || isDev) {
    // 相对路径或开发环境：通过 dev server 或 hash 加载
    const baseUrl = isDev ? 'http://localhost:4200' : APP_PATHS.frontendIndex;
    const hashPath = url.startsWith('/') ? url : `/${url}`;
    if (isDev) {
      childWin.loadURL(`${baseUrl}#${hashPath}`);
    } else {
      // 生产环境使用 loadFile 的 hash 参数（兼容 Windows file:// 格式）
      childWin.loadFile(baseUrl, { hash: hashPath });
    }
  } else {
    // 默认情况：用 loadFile 携带 hash（兼容 Windows file:// 格式）
    childWin.loadFile(APP_PATHS.frontendIndex, { hash: url.startsWith('/') ? url : `/${url}` });
  }

  childWindows.add(childWin);
  childWin.on('closed', () => {
    childWindows.delete(childWin);
  });
}

// ==================== 系统托盘 ====================

/**
 * 创建系统托盘
 */
function createTray() {
  const iconPath = APP_PATHS.icon;
  // 如果图标不存在，使用默认图标
  const trayIcon = fs.existsSync(iconPath) ? iconPath : undefined;

  if (!trayIcon) {
    console.warn('[WARN] 托盘图标不存在，跳过创建系统托盘');
    return;
  }

  tray = new Tray(trayIcon);
  tray.setToolTip('MatuX - AI 编程学习平台');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    { type: 'separator' },
    {
      label: '⚪ 状态未知',
      enabled: false,
    },
    { type: 'separator' },
    {
      label: '重启后端',
      click: () => {
        restartBackend();
      },
    },
    {
      label: '学习提醒',
      click: () => {
        showNotification('学习提醒', '该继续今天的学习啦！坚持就是胜利 💪');
      },
    },
    { type: 'separator' },
    {
      label: '检查更新',
      click: () => {
        checkForUpdates();
      },
    },
    { type: 'separator' },
    {
      label: '退出 MatuX',
      click: () => {
        isQuitting = true;
        gracefulShutdown();
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  // 双击托盘图标显示主窗口
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// ==================== 原生通知 ====================

/**
 * 显示系统原生通知
 * @param {string} title 通知标题
 * @param {string} body 通知内容
 * @param {string} [category] 通知类别 (learning/achievement/update)
 */
function showNotification(title, body, category = 'learning') {
  if (!Notification.isSupported()) {
    console.log('[INFO] 系统不支持原生通知');
    return;
  }

  const notification = new Notification({
    title,
    body,
    icon: APP_PATHS.icon,
    silent: false,
  });

  notification.on('click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  notification.show();
  console.log(`[NOTIFICATION] [${category}] ${title}: ${body}`);
}

// ==================== 全局快捷键 ====================

/**
 * 注册全局快捷键
 */
function registerGlobalShortcuts() {
  // Ctrl+Shift+M → 显示/隐藏 MatuX
  const ret = globalShortcut.register('CommandOrControl+Shift+M', () => {
    if (!mainWindow) return;

    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  if (!ret) {
    console.warn('[WARN] 全局快捷键 Ctrl+Shift+M 注册失败（可能被占用）');
  } else {
    console.log('[INFO] 全局快捷键 Ctrl+Shift+M 已注册（显示/隐藏窗口）');
  }

  // Ctrl+K → 全局命令面板
  globalShortcut.register('CommandOrControl+K', () => {
    if (mainWindow && mainWindow.isVisible()) {
      mainWindow.webContents.send('shortcut', 'command-palette');
    }
  });

  // Ctrl+N → 新建项目
  globalShortcut.register('CommandOrControl+N', () => {
    if (mainWindow && mainWindow.isVisible()) {
      mainWindow.webContents.send('shortcut', 'new-project');
    }
  });

  console.log('[INFO] 快捷键 Ctrl+K（命令面板）、Ctrl+N（新建项目）已注册');
}

/**
 * 注销所有全局快捷键
 */
function unregisterGlobalShortcuts() {
  globalShortcut.unregisterAll();
}

// ==================== 自动更新 ====================

/**
 * 检查应用更新
 * 使用 electron-updater（需要在 electron/package.json 中添加依赖）
 */
async function checkForUpdates() {
  try {
    // 动态导入 electron-updater（可选依赖）
    const { autoUpdater } = require('electron-updater');

    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;

    // 发现新版本
    autoUpdater.on('update-available', (info) => {
      console.log('[UPDATE] 发现新版本:', info.version);
      showNotification('发现新版本', `v${info.version} 可用，点击更新`, 'update');

      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('app-event', {
          type: 'update-available',
          version: info.version,
          releaseNotes: info.releaseNotes,
        });
      }

      // 提示用户下载
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '发现新版本',
        message: `MatuX v${info.version} 已发布`,
        detail: '是否立即下载更新？',
        buttons: ['下载更新', '稍后提醒'],
        defaultId: 0,
      }).then(({ response }) => {
        if (response === 0) {
          autoUpdater.downloadUpdate();
        }
      });
    });

    // 下载进度
    autoUpdater.on('download-progress', (progress) => {
      console.log(`[UPDATE] 下载进度: ${progress.percent.toFixed(1)}%`);
    });

    // 下载完成
    autoUpdater.on('update-downloaded', () => {
      console.log('[UPDATE] 更新下载完成');
      showNotification('更新就绪', '新版本已下载，重启后生效', 'update');

      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: '更新就绪',
        message: '新版本已下载完成',
        detail: '需要重启应用以完成安装。',
        buttons: ['立即重启', '稍后'],
        defaultId: 0,
      }).then(({ response }) => {
        if (response === 0) {
          isQuitting = true;
          autoUpdater.quitAndInstall();
        }
      });
    });

    autoUpdater.on('error', (err) => {
      console.error('[UPDATE] 更新检查失败:', err.message);
    });

    await autoUpdater.checkForUpdates();
  } catch (err) {
    // electron-updater 未安装
    console.warn('[WARN] electron-updater 未安装，跳过自动更新检查');
    console.warn('[WARN] 安装方式: cd electron && npm install electron-updater');
  }
}

// ==================== 文件关联 ====================

/**
 * 处理 .imato 文件关联打开
 * 当用户双击 .imato 文件时，Electron 会通过 open-file 事件接收
 */
function setupFileAssociation() {
  // macOS: 通过 open-file 事件
  app.on('open-file', (event, filePath) => {
    event.preventDefault();
    if (!filePath.endsWith('.imato')) return;

    console.log('[INFO] 通过文件关联打开:', filePath);

    if (mainWindow) {
      mainWindow.show();
      // 通知渲染进程打开文件
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        mainWindow.webContents.send('app-event', {
          type: 'open-file',
          filePath,
          content,
        });
      } catch (err) {
        console.error('[ERROR] 读取文件失败:', err.message);
      }
    }
  });

  // Windows: 通过命令行参数
  const filePath = process.argv.find((arg) => arg.endsWith('.imato'));
  if (filePath && fs.existsSync(filePath)) {
    console.log('[INFO] 通过命令行参数打开文件:', filePath);
    // 延迟到主窗口创建后发送
    app.once('main-window-ready', () => {
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        mainWindow.webContents.send('app-event', {
          type: 'open-file',
          filePath,
          content,
        });
      } catch (err) {
        console.error('[ERROR] 读取文件失败:', err.message);
      }
    });
  }
}

// ==================== 后端管理 ====================

/**
 * 启动 Python 后端服务
 */
function startBackend() {
  if (backendProcess) {
    console.log('[INFO] 后端已在运行中');
    return;
  }
  if (isStarting) {
    console.log('[INFO] 后端正在启动中，跳过重复请求');
    return;
  }
  isStarting = true;

  const pythonInfo = detectPython();
  if (!pythonInfo.available) {
    sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);
    isStarting = false;
    return;
  }

  const backendInfo = getBackendScriptPath();
  console.log(`[INFO] Python: ${pythonInfo.path} (${pythonInfo.version})`);
  console.log(`[INFO] 后端入口: ${backendInfo.path} (${backendInfo.type})`);

  sendSplashStatus('starting-backend', '正在启动后端服务...', 20);

  if (backendInfo.type === 'exe') {
    // 生产环境：直接运行 PyInstaller 打包的 exe
    backendProcess = spawn(backendInfo.path, [], {
      cwd: APP_PATHS.backendDir,
      env: { ...process.env, PORT: BACKEND_PORT.toString() },
      windowsHide: true,
    });
  } else {
    // 开发环境：运行 Python 脚本
    backendProcess = spawn(pythonInfo.path, [backendInfo.path], {
      cwd: APP_PATHS.backendDir,
      env: { ...process.env, PORT: BACKEND_PORT.toString() },
      windowsHide: !isDev,
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
    sendSplashStatus('backend-error', '后端进程启动失败', 0, err.message);
    backendProcess = null;
    isStarting = false;
  });

  backendProcess.on('close', (code, signal) => {
    console.log(`[INFO] 后端服务已退出 (code: ${code}, signal: ${signal})`);
    isStarting = false;

    if (!isQuitting && restartAttempts < MAX_RESTART_ATTEMPTS) {
      restartAttempts++;
      console.log(`[INFO] ${BACKEND_RESTART_DELAY / 1000} 秒后尝试重启后端 (${restartAttempts}/${MAX_RESTART_ATTEMPTS})`);
      sendSplashStatus('starting-backend', `后端异常退出，正在重启 (${restartAttempts}/${MAX_RESTART_ATTEMPTS})...`, 30);
      setTimeout(() => {
        backendProcess = null;
        startBackend();
        waitForBackend().then((ready) => {
          if (ready && mainWindow) {
            mainWindow.webContents.send('app-event', { type: 'backend-reconnected' });
          }
        });
      }, BACKEND_RESTART_DELAY);
    } else if (!isQuitting) {
      sendSplashStatus('backend-error', '后端多次启动失败，请检查日志', 0,
        `已尝试 ${MAX_RESTART_ATTEMPTS} 次，后端无法启动`);
    }

    backendProcess = null;
  });
}

/**
 * 等待后端服务就绪（分阶段启动 Phase 1：仅等待核心 Tier 0 就绪）
 */
async function waitForBackend(timeout = BACKEND_START_TIMEOUT) {
  const waitPort = require('wait-port');

  console.log(`[INFO] 等待后端服务启动 (${BACKEND_URL})...`);
  sendSplashStatus('waiting-backend', '等待后端服务就绪...', 50);

  const startTime = Date.now();

  // 动态更新进度
  const progressInterval = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(50 + (elapsed / timeout) * 40, 85);
    sendSplashStatus('waiting-backend', '等待后端服务就绪', progress);
  }, 500);

  try {
    await waitPort({
      host: BACKEND_HOST,
      port: BACKEND_PORT,
      timeout: timeout,
      output: 'silent',
    });
    clearInterval(progressInterval);
    console.log('[INFO] 后端端口已开放，验证健康状态...');
    sendSplashStatus('waiting-backend', '后端服务已就绪，正在验证...', 88);

    // 短等待让 uvicorn 完全就绪
    await new Promise((r) => setTimeout(r, 500));

    console.log('[INFO] 后端服务已就绪！');
    sendSplashStatus('backend-ready', '后端服务就绪 ✓', 90);
    restartAttempts = 0; // 重置重启计数
    isStarting = false;
    return true;
  } catch (error) {
    clearInterval(progressInterval);
    console.error('[ERROR] 后端服务启动超时:', error.message);
    sendSplashStatus('backend-timeout', '后端启动超时', 0, error.message);
    return false;
  }
}

/**
 * 健康检查
 */
async function healthCheck() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(HEALTH_URL, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    // 不仅检查状态码，还验证响应体内容（防止端口被占用时误判）
    if (!response.ok) {
      console.warn('[HEALTH] 后端健康检查返回非 200:', response.status);
      return { success: false, error: 'Backend returned non-200 status' };
    }
    const body = await response.json();
    if (body && body.status === 'ok') {
      return {
        success: true,
        status: 'ok',
        version: body.python_version || '3.11',
        uptime: body.uptime,
      };
    }
    console.warn('[HEALTH] 后端健康检查响应异常:', JSON.stringify(body));
    return { success: false, error: 'Invalid response body' };
  } catch (err) {
    console.error('[HEALTH] 健康检查失败:', err.message);
    return { success: false, error: err.message };
  }
}

/**
 * 启动周期性健康检查
 */
function startHealthCheck() {
  if (healthCheckTimer) clearInterval(healthCheckTimer);
  healthCheckTimer = setInterval(async () => {
    const result = await healthCheck();
    if (!result.success && !isQuitting) {
      console.warn('[WARN] 健康检查失败，后端可能已崩溃');
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('app-event', { type: 'backend-disconnected' });
      }
    }
  }, HEALTH_CHECK_INTERVAL);
}

/**
 * 停止健康检查
 */
function stopHealthCheck() {
  if (healthCheckTimer) {
    clearInterval(healthCheckTimer);
    healthCheckTimer = null;
  }
}

/**
 * 停止后端服务
 */
function stopBackend() {
  if (!backendProcess) return;

  console.log('[INFO] 正在停止后端服务...');

  if (process.platform === 'win32') {
    try {
      execSync(`taskkill /pid ${backendProcess.pid} /f /t`, { stdio: 'ignore' });
    } catch {
      // 进程可能已经退出
    }
  } else {
    backendProcess.kill('SIGTERM');
    // 如果 5 秒后还没退出，强制 kill
    setTimeout(() => {
      if (backendProcess) {
        try { backendProcess.kill('SIGKILL'); } catch { /* ignore */ }
      }
    }, 5000);
  }

  backendProcess = null;
}

/**
 * 重启后端服务 (Phase 4 新增)
 */
function restartBackend() {
  console.log('[INFO] 🔄 正在重启后端服务...');
  
  // 停止状态轮询
  stopModuleStatusPolling();
  stopHealthCheck();
  
  // 停止后端进程
  stopBackend();
  
  // 等待 2 秒后重启
  setTimeout(() => {
    restartAttempts = 0;
    isStarting = false;
    startBackend();
    waitForBackend().then((ready) => {
      if (ready) {
        startHealthCheck();
        startModuleStatusPolling();
        
        // 通知渲染进程
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('app-event', { type: 'backend-restarted' });
        }
      }
    });
  }, 2000);
}

// ==================== 模块状态管理 ====================

/**
 * 后台预加载 Tier 1 模块（分阶段启动 Phase 2：不阻塞 UI）
 */
async function preloadTier1Modules() {
  // 等待 1 秒让 Tier 0 稳定
  await new Promise((r) => setTimeout(r, 1000));

  console.log('[INFO] 开始后台预加载 Tier 1 模块...');

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIER1_PRELOAD_TIMEOUT);
    const response = await fetch(MODULES_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('[WARN] 获取模块状态失败:', response.status);
      return;
    }

    const data = await response.json();
    const summary = data.summary || {};
    const modules = data.modules || [];

    console.log(
      `[INFO] 模块状态: ${summary.active}/${summary.total} 已激活, ` +
      `${summary.degraded || 0} 降级, ${summary.failed || 0} 失败`
    );

    // 发送模块进度到 Splash
    sendSplashStatus('modules', `模块加载中 (${summary.active}/${summary.total})...`, 
      Math.round((summary.active / Math.max(summary.total, 1)) * 100),
      null, modules);

    // 通知渲染进程模块状态
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend:module-status', data);
    }

    // 缓存初始状态
    moduleStatusCache = data;
  } catch (err) {
    console.warn('[WARN] Tier 1 预加载检查失败:', err.message);
  }
}

/**
 * 轮询模块状态并推送到渲染进程
 */
async function pollModuleStatus() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const response = await fetch(HEALTH_DETAIL_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) return;

    const data = await response.json();
    const previousStatus = backendOverallStatus;
    backendOverallStatus = data.status || 'unknown';
    moduleStatusCache = data.modules || null;

    // 推送到渲染进程
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend:module-status', moduleStatusCache);
    }

    // 更新托盘状态
    updateTrayStatus();

    // 状态变化时通知前端
    if (previousStatus !== backendOverallStatus && mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', {
        type: 'backend-status-change',
        status: backendOverallStatus,
        previousStatus,
      });
    }
  } catch (err) {
    // 静默失败
  }
}

/**
 * 开始模块状态轮询
 */
function startModuleStatusPolling() {
  if (moduleStatusTimer) clearInterval(moduleStatusTimer);
  moduleStatusTimer = setInterval(pollModuleStatus, MODULE_STATUS_INTERVAL);
  // 立即执行一次
  pollModuleStatus();
}

/**
 * 停止模块状态轮询
 */
function stopModuleStatusPolling() {
  if (moduleStatusTimer) {
    clearInterval(moduleStatusTimer);
    moduleStatusTimer = null;
  }
}

/**
 * 更新系统托盘图标和菜单（反映后端状态）
 */
function updateTrayStatus() {
  if (!tray) return;

  let statusLabel = '';
  let statusEmoji = '';

  switch (backendOverallStatus) {
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

  tray.setToolTip(`MatuX - ${statusLabel}`);

  // 构建模块摘要菜单项
  const moduleItems = [];
  if (moduleStatusCache && moduleStatusCache.summary) {
    const s = moduleStatusCache.summary;
    moduleItems.push({
      label: `模块: ${s.active}/${s.total} 活跃`,
      enabled: false,
    });
    if (s.degraded > 0) {
      moduleItems.push({ label: `${s.degraded} 个模块降级`, enabled: false });
    }
    if (s.failed > 0) {
      moduleItems.push({ label: `${s.failed} 个模块失败`, enabled: false });
    }
  }

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      },
    },
    { type: 'separator' },
    {
      label: `${statusEmoji} ${statusLabel}`,
      enabled: false,
    },
    ...moduleItems,
    { type: 'separator' },
    {
      label: '重启后端',
      click: () => {
        restartBackend();
      },
    },
    {
      label: '学习提醒',
      click: () => {
        showNotification('学习提醒', '该继续今天的学习啦！坚持就是胜利 💪');
      },
    },
    { type: 'separator' },
    {
      label: '检查更新',
      click: () => {
        checkForUpdates();
      },
    },
    { type: 'separator' },
    {
      label: '退出 MatuX',
      click: () => {
        isQuitting = true;
        gracefulShutdown();
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
}

/**
 * 重启后端服务
 */
async function restartBackend() {
  console.log('[INFO] 🔄 用户请求重启后端...');
  
  // 停止状态轮询
  stopModuleStatusPolling();
  stopHealthCheck();
  
  // 停止后端进程
  stopBackend();
  
  // 等待 2 秒后重启
  await new Promise((r) => setTimeout(r, 2000));
  
  restartAttempts = 0;
  isStarting = false;
  
  startBackend();
  const ready = await waitForBackend();
  
  if (ready) {
    // 重启状态轮询
    startHealthCheck();
    startModuleStatusPolling();
    
    // 通知渲染进程
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', { type: 'backend-restarted' });
    }
    
    showNotification('后端已重启', '后端服务已成功重启', 'backend');
  } else {
    showNotification('后端重启失败', '请检查日志并联系管理员', 'backend');
  }
}

/**
 * 优雅关闭所有进程
 */
function gracefulShutdown() {
  if (isQuitting) return; // 防止重复调用
  isQuitting = true;

  try { unregisterGlobalShortcuts(); } catch (err) {
    console.error('[SHUTDOWN] 注销快捷键失败:', err.message);
  }

  if (healthCheckTimer) {
    clearInterval(healthCheckTimer);
    healthCheckTimer = null;
  }

  stopModuleStatusPolling();

  try { stopBackend(); } catch (err) {
    console.error('[SHUTDOWN] 停止后端失败:', err.message);
  }

  // 销毁系统托盘
  if (tray) {
    try {
      tray.destroy();
    } catch (err) {
      console.error('[SHUTDOWN] 销毁托盘失败:', err.message);
    }
    tray = null;
  }

  // 关闭所有窗口
  BrowserWindow.getAllWindows().forEach((win) => {
    if (!win.isDestroyed()) win.destroy();
  });
}

// ==================== IPC 通信 ====================

/**
 * 注册所有 IPC 处理器
 */
function registerIpcHandlers() {
  // 获取后端 URL
  ipcMain.handle('get-backend-url', () => BACKEND_URL);

  // 健康检查
  ipcMain.handle('health-check', async () => await healthCheck());

  // 获取应用信息
  ipcMain.handle('get-app-info', () => ({
    version: app.getVersion(),
    name: app.getName(),
    platform: process.platform,
    arch: process.arch,
    isDev,
  }));

  // 注册模块管理 IPC 处理器 (Phase 4 新增)
  registerModuleIpcHandlers();

  // 文件系统操作（安全桥接）
  ipcMain.handle('fs-read-file', async (_event, filePath) => {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return { success: true, content };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('fs-write-file', async (_event, filePath, content) => {
    try {
      // 确保父目录存在
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      // 支持 Buffer/ArrayBuffer（二进制）和字符串
      if (Buffer.isBuffer(content) || content instanceof ArrayBuffer) {
        fs.writeFileSync(filePath, Buffer.from(content));
      } else {
        fs.writeFileSync(filePath, content, 'utf-8');
      }
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('fs-save-dialog', async (_event, opts) => {
    if (!mainWindow) return { success: false, error: '主窗口未就绪' };
    const defaultOpts = {
      title: '保存文件',
      filters: [
        { name: 'MatuX 项目文件', extensions: ['imato'] },
        { name: '所有文件', extensions: ['*'] },
      ],
    };
    const result = await dialog.showSaveDialog(mainWindow, opts || defaultOpts);
    return { success: !result.canceled, filePath: result.filePath };
  });

  // 获取窗口尺寸
  ipcMain.handle('get-window-size', () => {
    if (!mainWindow) return { width: 1400, height: 900 };
    const [w, h] = mainWindow.getSize();
    return { width: w, height: h };
  });

  ipcMain.handle('fs-open-dialog', async () => {
    if (!mainWindow) return { success: false, error: '主窗口未就绪' };
    const result = await dialog.showOpenDialog(mainWindow, {
      title: '打开项目文件',
      filters: [
        { name: 'MatuX 项目文件', extensions: ['imato'] },
        { name: '所有文件', extensions: ['*'] },
      ],
      properties: ['openFile'],
    });
    if (result.canceled || result.filePaths.length === 0) {
      return { success: false, error: '用户取消' };
    }
    const filePath = result.filePaths[0];
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return { success: true, filePath, content };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 打开外部链接
  ipcMain.handle('open-external', async (_event, url) => {
    try {
      await shell.openExternal(url);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 列出目录内容
  ipcMain.handle('fs-list-dir', async (_event, dirPath) => {
    try {
      if (!fs.existsSync(dirPath)) {
        return { success: false, error: '目录不存在' };
      }
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });
      const files = entries.map((entry) => {
        const fullPath = path.join(dirPath, entry.name);
        let stat;
        try {
          stat = fs.statSync(fullPath);
        } catch {
          stat = { size: 0, mtimeMs: 0, isFile: () => false, isDirectory: () => false };
        }
        return {
          name: entry.name,
          isDirectory: entry.isDirectory(),
          isFile: entry.isFile(),
          size: stat.size,
          mtimeMs: stat.mtimeMs,
          path: fullPath,
        };
      });
      // 排序：目录在前，文件在后，各按名称排序
      files.sort((a, b) => {
        if (a.isDirectory !== b.isDirectory) return a.isDirectory ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
      return { success: true, files };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 创建目录（递归）
  ipcMain.handle('fs-make-dir', async (_event, dirPath) => {
    try {
      fs.mkdirSync(dirPath, { recursive: true });
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 删除文件或空目录
  ipcMain.handle('fs-delete-file', async (_event, targetPath) => {
    try {
      if (!fs.existsSync(targetPath)) {
        return { success: false, error: '目标不存在' };
      }
      const stat = fs.statSync(targetPath);
      if (stat.isDirectory()) {
        fs.rmdirSync(targetPath);
      } else {
        fs.unlinkSync(targetPath);
      }
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 检查文件是否存在
  ipcMain.handle('fs-file-exists', async (_event, targetPath) => {
    try {
      return { success: true, exists: fs.existsSync(targetPath) };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取文件信息
  ipcMain.handle('fs-get-file-info', async (_event, filePath) => {
    try {
      if (!fs.existsSync(filePath)) {
        return { success: false, error: '文件不存在' };
      }
      const stat = fs.statSync(filePath);
      return {
        success: true,
        info: {
          size: stat.size,
          isDirectory: stat.isDirectory(),
          isFile: stat.isFile(),
          createdMs: stat.birthtimeMs,
          modifiedMs: stat.mtimeMs,
          accessedMs: stat.atimeMs,
          extension: path.extname(filePath),
          name: path.basename(filePath),
          dir: path.dirname(filePath),
        },
      };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 选择文件夹对话框
  ipcMain.handle('fs-select-directory', async () => {
    if (!mainWindow) return { success: false, error: '主窗口未就绪' };
    try {
      const result = await dialog.showOpenDialog(mainWindow, {
        title: '选择文件夹',
        properties: ['openDirectory'],
      });
      if (result.canceled || result.filePaths.length === 0) {
        return { success: false, error: '用户取消' };
      }
      return { success: true, filePath: result.filePaths[0] };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 发送原生通知
  ipcMain.handle('show-notification', async (_event, title, body, category) => {
    showNotification(title, body, category);
    return { success: true };
  });

  // ===== 窗口控制 IPC（支持 frame:false 自定义标题栏）=====
  ipcMain.handle('window-minimize', () => {
    mainWindow?.minimize();
    return { success: true };
  });

  ipcMain.handle('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
    return { success: true };
  });

  ipcMain.handle('window-close', () => {
    mainWindow?.close();
    return { success: true };
  });

  ipcMain.handle('window-is-maximized', () => {
    return { success: true, isMaximized: mainWindow?.isMaximized() || false };
  });

  // 检查更新
  ipcMain.handle('check-for-updates', async () => {
    await checkForUpdates();
    return { success: true };
  });

  // ===== 模块状态 IPC（Phase 4 懒加载架构） =====

  /**
   * 获取模块状态缓存
   */
  ipcMain.handle('backend:module-status', () => {
    return {
      success: true,
      modules: moduleStatusCache,
      backendStatus: backendOverallStatus,
    };
  });

  /**
   * 重启后端
   */
  ipcMain.handle('backend:restart', async () => {
    restartBackend();
    return { success: true, message: '后端重启中' };
  });

  // ===== 设备评估 IPC（插件化架构 Phase 1） =====

  /**
   * 获取设备评估报告
   */
  ipcMain.handle('plugin:device-profile', async () => {
    try {
      const profile = loadDeviceProfile();
      if (profile && !shouldReassess(profile)) {
        return { success: true, profile };
      }
      // 需要重新评估
      const newProfile = await assessDevice();
      saveDeviceProfile(newProfile);
      return { success: true, profile: newProfile };
    } catch (err) {
      console.error('[ERROR] 获取设备评估报告失败:', err.message);
      return { success: false, error: err.message };
    }
  });

  /**
   * 重新评估设备
   */
  ipcMain.handle('plugin:reassess-device', async () => {
    try {
      console.log('[INFO] 用户请求重新评估设备');
      const profile = await assessDevice();
      saveDeviceProfile(profile);
      // 通知渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('plugin:status-change', {
          type: 'device-reassessed',
          profile,
        });
      }
      return { success: true, profile };
    } catch (err) {
      console.error('[ERROR] 重新评估设备失败:', err.message);
      return { success: false, error: err.message };
    }
  });

  /**
   * 评估指定插件兼容性
   */
  ipcMain.handle('plugin:assess', async (_event, pluginId) => {
    try {
      const profile = loadDeviceProfile();
      if (!profile) {
        return { success: false, error: '设备评估报告不存在，请先执行评估' };
      }
      // 返回设备信息供前端做兼容性判断
      return {
        success: true,
        deviceClass: profile.assessment?.deviceClass,
        score: profile.assessment?.score,
        hardware: profile.hardware,
        software: profile.software,
        compatibleTiers: profile.assessment?.compatiblePluginTiers || [],
        recommendedPlugins: profile.assessment?.recommendedPlugins || [],
        incompatiblePlugins: profile.assessment?.incompatiblePlugins || [],
      };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // ===== 插件管理 IPC（插件化架构 Phase 2） =====

  // 注册插件安装器 IPC
  if (pluginInstaller) {
    registerPluginInstallerIPC(pluginInstaller);
  }

  // 注册插件下载器 IPC
  if (pluginDownloader) {
    registerPluginDownloaderIPC(pluginDownloader);
  }

  // ===== Phase 5: 推荐引擎 IPC =====

  // 获取个性化推荐
  ipcMain.handle('plugin:recommendations', async (_event, options = {}) => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      const recommendations = await pluginRecommender.getRecommendations(options);
      return { success: true, data: recommendations };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 记录插件使用事件
  ipcMain.handle('plugin:record-usage', async (_event, pluginId, eventType, duration = 0, features = {}) => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      pluginRecommender.recordPluginUsage(pluginId, eventType, duration, features);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 设置插件评分
  ipcMain.handle('plugin:set-rating', async (_event, pluginId, rating, feedback = '') => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      pluginRecommender.setUserRating(pluginId, rating, feedback);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取热门插件
  ipcMain.handle('plugin:popular', async (_event, limit = 10) => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      const popular = await pluginRecommender.getPopularPlugins(limit);
      return { success: true, data: popular };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取插件详情
  ipcMain.handle('plugin:details', async (_event, pluginId) => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      const details = await pluginRecommender.getPluginDetails(pluginId);
      return { success: true, data: details };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // ===== Phase 5: 安装包精简 IPC =====

  // 获取首次运行引导步骤
  ipcMain.handle('plugin:first-run-guide', async () => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const guide = installConfigManager.getFirstRunGuide();
      return { success: true, data: guide };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 检查是否已完成首次运行
  ipcMain.handle('plugin:first-run-check', async () => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const isFirstRunCompleted = installConfigManager.isFirstRunCompleted();
      return { success: true, data: isFirstRunCompleted };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 标记首次运行完成
  ipcMain.handle('plugin:first-run-complete', async () => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      await installConfigManager.markFirstRunCompleted();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取核心模块列表
  ipcMain.handle('plugin:core-modules', async () => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const modules = installConfigManager.getCoreModules();
      return { success: true, data: modules };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取可选模块列表
  ipcMain.handle('plugin:optional-modules', async (_event, deviceClass = null) => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const modules = installConfigManager.getOptionalModules(deviceClass);
      return { success: true, data: modules };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取推荐模块
  ipcMain.handle('plugin:recommended-modules', async (_event, deviceClass) => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const modules = installConfigManager.getRecommendedModules(deviceClass);
      return { success: true, data: modules };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取安装统计
  ipcMain.handle('plugin:install-stats', async () => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      const stats = installConfigManager.getInstallStats();
      return { success: true, data: stats };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 添加已安装模块
  ipcMain.handle('plugin:installed-module', async (_event, moduleId) => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      await installConfigManager.addInstalledModule(moduleId);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 跳过模块安装
  ipcMain.handle('plugin:skip-module', async (_event, moduleId) => {
    try {
      if (!installConfigManager) {
        return { success: false, error: '安装配置管理器未初始化' };
      }
      await installConfigManager.skipModule(moduleId);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // ===== Phase 5: 插件商店增强 IPC =====

  // 添加插件评论
  ipcMain.handle('plugin:add-review', async (_event, reviewData) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const review = await pluginStoreEnhancer.addReview(reviewData);
      return { success: true, data: review };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取插件评论
  ipcMain.handle('plugin:get-reviews', async (_event, pluginId, options = {}) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const reviews = pluginStoreEnhancer.getReviews(pluginId, options);
      return { success: true, data: reviews };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取插件平均评分
  ipcMain.handle('plugin:average-rating', async (_event, pluginId) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const rating = pluginStoreEnhancer.getAverageRating(pluginId);
      return { success: true, data: rating };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 标记评论为有帮助
  ipcMain.handle('plugin:mark-helpful', async (_event, reviewId, pluginId) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const result = await pluginStoreEnhancer.markReviewHelpful(reviewId, pluginId);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 检查插件更新
  ipcMain.handle('plugin:check-updates', async (_event, installedPlugins) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      // 需要从 pluginRegistry 获取插件目录
      const pluginCatalog = pluginRegistry ? pluginRegistry.getCatalog() : [];
      const updates = await pluginStoreEnhancer.checkForUpdates(pluginCatalog, installedPlugins);
      return { success: true, data: updates };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取待处理更新通知
  ipcMain.handle('plugin:pending-notifications', async () => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const notifications = pluginStoreEnhancer.getPendingNotifications();
      return { success: true, data: notifications };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 关闭更新通知
  ipcMain.handle('plugin:dismiss-notification', async (_event, notificationId) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const result = await pluginStoreEnhancer.dismissNotification(notificationId);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 标记通知已安装
  ipcMain.handle('plugin:mark-installed', async (_event, notificationId) => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const result = await pluginStoreEnhancer.markNotificationInstalled(notificationId);
      return { success: true, data: result };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取插件使用统计
  ipcMain.handle('plugin:usage-stats', async (_event, pluginId) => {
    try {
      if (!pluginRecommender) {
        return { success: false, error: '推荐引擎未初始化' };
      }
      const usageStatsMap = pluginRecommender.usageStatsMap;
      const stats = pluginStoreEnhancer.getPluginUsageStats(pluginId, usageStatsMap);
      return { success: true, data: stats };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 获取商店统计
  ipcMain.handle('plugin:store-stats', async () => {
    try {
      if (!pluginStoreEnhancer) {
        return { success: false, error: '插件商店增强组件未初始化' };
      }
      const stats = pluginStoreEnhancer.getStoreStats();
      return { success: true, data: stats };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  // 渲染进程发送的消息
  ipcMain.on('to-backend', (_event, data) => {
    console.log('[IPC] 来自渲染进程的数据:', data);
  });

  ipcMain.on('app-event', (_event, data) => {
    console.log('[IPC] 应用事件:', data);
    if (!data || !data.type) return;

    switch (data.type) {
      case 'minimize':
        mainWindow?.minimize();
        break;
      case 'maximize':
        if (mainWindow?.isMaximized()) {
          mainWindow.unmaximize();
        } else {
          mainWindow?.maximize();
        }
        break;
      case 'close':
        mainWindow?.close();
        break;
      case 'toggle-fullscreen':
        mainWindow?.setFullScreen(!mainWindow?.isFullScreen());
        break;
      case 'open-new-window':
        // 多窗口弹出（数字孪生实验室等）
        createChildWindow(data);
        break;
      default:
        break;
    }
  });

  // Splash 重试
  ipcMain.on('splash-retry', async () => {
    console.log('[INFO] 用户请求重试启动');
    restartAttempts = 0;
    stopModuleStatusPolling();
    stopBackend();
    await new Promise((r) => setTimeout(r, 1000));
    startBackend();
    const ready = await waitForBackend();
    if (ready) {
      startModuleStatusPolling();
      preloadTier1Modules();
      sendSplashStatus('loading-app', '正在加载应用...', 95);
      if (!mainWindow || mainWindow.isDestroyed()) {
        createMainWindow();
      }
    }
  });
}

// ==================== 应用生命周期 ====================

app.whenReady().then(async () => {
  // 注册 IPC 处理器
  registerIpcHandlers();

  // 1. 创建 Splash Screen
  createSplashWindow();
  await new Promise((r) => setTimeout(r, 800)); // 等待 Splash 渲染

  // 2. 检测 Python 环境
  sendSplashStatus('checking-python', '正在检测 Python 环境...', 5);
  let pythonInfo = detectPython();

  // 如果自动检测未找到，循环弹窗让用户选择
  while (!pythonInfo.available) {
    sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);

    const { response } = await dialog.showMessageBox({
      type: 'warning',
      title: '缺少 Python 环境',
      message: 'MatuX 需要 Python 3.9 或更高版本',
      detail: '检测到您的系统未安装 Python 或版本过低。\n\n您可以选择手动指定 Python 位置，或下载安装。',
      buttons: ['下载 Python', '手动选择 Python 位置', '暂不处理'],
      defaultId: 0,
      cancelId: 2,
    });

    if (response === 0) {
      shell.openExternal('https://www.python.org/downloads/');
      return;
    }

    if (response === 1) {
      // 用户手动指定 Python 位置
      const result = await dialog.showOpenDialog({
        title: '请选择 python.exe',
        defaultPath: process.env.ProgramFiles || 'C:\\',
        filters: [{ name: 'Python 可执行文件', extensions: ['exe'] }],
        properties: ['openFile'],
      });

      if (!result.canceled && result.filePaths.length > 0) {
        const manualPath = result.filePaths[0];
        try {
          const versionOutput = execSync(`"${manualPath}" --version 2>&1`, {
            encoding: 'utf-8',
            timeout: 5000,
          }).trim();
          const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
          if (versionMatch && isPythonVersionGte39(versionMatch[1])) {
            console.log(`[INFO] 用户手动指定 Python: ${manualPath} (${versionMatch[1]})`);
            pythonInfo = { available: true, version: versionMatch[1], path: manualPath };
            break;
          }
          await dialog.showMessageBox({
            type: 'error',
            title: '版本不符',
            message: `所选 Python 版本 ${versionMatch ? versionMatch[1] : '未知'} 不符合要求`,
            detail: 'MatuX 需要 Python 3.9 或更高版本。',
          });
        } catch {
          await dialog.showMessageBox({
            type: 'error',
            title: '无效的文件',
            message: '所选文件不是有效的 Python 可执行文件，请重新选择。',
          });
        }
      }
      // 用户取消文件选择，继续循环重新弹窗
    } else {
      // 暂不处理
      return;
    }
  }

  console.log(`[INFO] 检测到 Python ${pythonInfo.version} (${pythonInfo.path})`);

  // 检查 Python 关键依赖包
  sendSplashStatus('checking-deps', '正在检查 Python 依赖包...', 10);
  const missingDeps = checkPythonDeps(pythonInfo);
  if (missingDeps.length > 0) {
    const msg = `缺少关键依赖: ${missingDeps.join(', ')}`;
    console.error(`[ERROR] ${msg}`);
    sendSplashStatus('pip-missing', '缺少 Python 依赖包', 0, msg);

    const { response: depResponse } = await dialog.showMessageBox({
      type: 'warning',
      title: '缺少 Python 依赖包',
      message: '请先安装 Python 依赖包再启动',
      detail: `检测到以下 Python 依赖包缺失:\n\n${missingDeps.join('\n')}\n\n请在终端中执行:\ncd backend\npip install -r requirements.txt`,
      buttons: ['查看依赖文件', '暂不处理'],
      defaultId: 0,
    });

    if (depResponse === 0) {
      shell.openPath(path.join(APP_PATHS.backendDir, 'requirements.txt'));
    }
    return;
  }

  // 3. 启动后端服务
  startBackend();

  // 如果 Python 检测通过但后端脚本不存在
  if (!backendProcess) {
    sendSplashStatus('backend-error', '后端启动失败，请检查安装', 0);
    return;
  }

  // 4. 等待后端就绪
  const isReady = await waitForBackend();

  if (!isReady) {
    console.error('[ERROR] 后端服务启动失败');
    isStarting = false;
    return;
  }

  // 确认后端健康（排除端口被其他程序占用的场景）
  sendSplashStatus('verifying-health', '正在验证后端服务...', 90);
  let healthResult = await healthCheck();
  // 首次失败后短等待重试（应对端口刚开但 uvicorn 未完全就绪的竞态）
  if (!healthResult.success) {
    console.log('[INFO] 首次健康检查未通过，1 秒后重试...');
    await new Promise((r) => setTimeout(r, 1000));
    healthResult = await healthCheck();
  }
  if (!healthResult.success) {
    console.error('[ERROR] 端口已开放但健康检查未通过，端口可能被其他程序占用');
    sendSplashStatus('backend-error', '端口 8000 被占用，无法连接后端服务', 0,
      '健康检查失败，请检查是否有其他程序占用了 8000 端口');
    await dialog.showMessageBox({
      type: 'error',
      title: '端口冲突',
      message: '端口 8000 已被其他程序占用',
      detail: '检测到端口 8000 已开放，但无法识别为 MatuX 后端服务。\n\n请检查是否有其他程序（如 nginx、其他 MatuX 实例）占用了该端口。',
    });
    stopBackend();
    return;
  }

  isStarting = false;

  // 5. 启动健康检查
  startHealthCheck();

  // 6. 启动模块状态轮询
  startModuleStatusPolling();

  // 7. 创建主窗口（核心就绪即显示）
  sendSplashStatus('loading-app', '正在加载应用...', 95);
  createMainWindow();

  // 8. 后台预加载 Tier 1 模块（不阻塞 UI）
  preloadTier1Modules();

  // 9. 创建设备评估（首次启动时自动评估，后续启动检查是否需要重新评估）
  sendSplashStatus('assessing-device', '正在评估设备能力...', 96);
  try {
    const existingProfile = loadDeviceProfile();
    if (!existingProfile || shouldReassess(existingProfile)) {
      const deviceProfile = await assessDevice();
      saveDeviceProfile(deviceProfile);
      console.log(`[INFO] 设备评级: ${deviceProfile.assessment.deviceClass} (${deviceProfile.assessment.score}分)`);
    } else {
      console.log(`[INFO] 使用缓存设备评级: ${existingProfile.assessment.deviceClass}`);
    }
  } catch (err) {
    console.warn('[WARN] 设备评估失败（不阻塞启动）:', err.message);
  }

  // 9.5 初始化插件管理器（Phase 2）
  try {
    console.log('[INFO] 初始化插件管理器...');
    
    // 创建插件安装器
    pluginInstaller = new PluginInstaller();
    
    // 创建插件下载器
    pluginDownloader = new PluginDownloader();
    
    // 创建并初始化插件注册表
    pluginRegistry = new PluginRegistry();
    await pluginRegistry.initialize();
    
    console.log('[INFO] ✓ 插件管理器初始化完成');
  } catch (err) {
    console.warn('[WARN] 插件管理器初始化失败（不阻塞启动）:', err.message);
  }

  // 9.6 初始化 Phase 5 推荐引擎和安装包精简模块
  try {
    console.log('[INFO] 初始化推荐引擎和安装包配置...');
    
    // 创建安装配置管理器
    installConfigManager = new InstallConfigManager();
    
    // 创建推荐引擎
    pluginRecommender = new PluginRecommendationEngine();
    
    // 创建插件商店增强组件
    pluginStoreEnhancer = new PluginStoreEnhancer();
    
    // 更新设备评估报告到推荐引擎
    if (deviceProfile) {
      pluginRecommender.updateDeviceProfile(deviceProfile);
    }
    
    console.log('[INFO] ✓ Phase 5 模块初始化完成');
  } catch (err) {
    console.warn('[WARN] Phase 5 模块初始化失败（不阻塞启动）:', err.message);
  }

  // 10. 创建系统托盘
  createTray();

  // 11. 注册全局快捷键
  registerGlobalShortcuts();

  // 12. 设置文件关联
  setupFileAssociation();

  // 13. 通知主窗口已就绪（用于文件关联）
  mainWindow.once('ready-to-show', () => {
    app.emit('main-window-ready');
  });

  // 14. 启动后检查更新（延迟 30 秒避免影响启动速度）
  setTimeout(() => {
    checkForUpdates().catch((err) => {
      console.warn('[WARN] 更新检查失败:', err.message);
    });
  }, 30000);
});

// macOS 特殊处理：关闭所有窗口时不退出应用（保持后端运行）
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // 非 macOS：关闭窗口即退出应用
    gracefulShutdown();
    app.quit();
  }
  // macOS：仅关闭窗口，后端继续运行
  // 用户通过 Cmd+Q 退出时触发 before-quit → gracefulShutdown
  // 再次点击 Dock 图标时触发 activate → createMainWindow
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

app.on('before-quit', () => {
  gracefulShutdown();
});

// 捕获未处理的异常
process.on('uncaughtException', (error) => {
  console.error('[FATAL] 未捕获的异常:', error);
  if (splashWindow && !splashWindow.isDestroyed()) {
    sendSplashStatus('backend-error', `应用错误: ${error.message}`, 0);
  }
});

// 导出用于测试
module.exports = {
  createSplashWindow,
  createMainWindow,
  startBackend,
  waitForBackend,
  healthCheck,
  gracefulShutdown,
  detectPython,
  createTray,
  registerGlobalShortcuts,
  showNotification,
  checkForUpdates,
  preloadTier1Modules,
  pollModuleStatus,
  restartBackend,
  startModuleStatusPolling,
  stopModuleStatusPolling,
  updateTrayStatus,
};
