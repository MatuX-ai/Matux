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

// ==================== 配置 ====================

const BACKEND_PORT = 8000;
const BACKEND_HOST = 'localhost';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
const BACKEND_START_TIMEOUT = 45000; // 后端启动超时 45 秒
const BACKEND_RESTART_DELAY = 3000;  // 崩溃后 3 秒重启
const MAX_RESTART_ATTEMPTS = 3;
const HEALTH_CHECK_INTERVAL = 10000; // 健康检查间隔 10 秒

const isDev = process.env.NODE_ENV === 'development';

let splashWindow = null;
let mainWindow = null;
let backendProcess = null;
let healthCheckTimer = null;
let restartAttempts = 0;
let isQuitting = false;
let tray = null;

// ==================== 工具函数 ====================

/**
 * 向 Splash 窗口发送状态更新
 */
function sendSplashStatus(phase, text, progress, detail) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('splash-status', { phase, text, progress, detail });
  }
  // 同时打印到控制台
  const prefix = phase === 'error' || phase === 'backend-error' ? '[ERROR]' : '[INFO]';
  console.log(`${prefix} ${text}`);
}

/**
 * 检测 Python 是否可用
 * @returns {{ available: boolean, version: string, path: string }}
 */
function detectPython() {
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py', 'py -3']
    : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const versionOutput = execSync(`"${cmd.split(' ')[0]}" --version 2>&1`, {
        encoding: 'utf-8',
        timeout: 5000,
        shell: true,
      }).trim();
      const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
      if (versionMatch) {
        const majorMinor = parseFloat(versionMatch[1]);
        if (majorMinor >= 3.9) {
          return {
            available: true,
            version: versionMatch[1],
            path: cmd.split(' ')[0],
          };
        }
        console.warn(`[WARN] Python ${versionMatch[1]} 版本过低，需要 3.9+`);
      }
    } catch {
      // 该命令不可用，尝试下一个
    }
  }
  return { available: false, version: '', path: '' };
}

/**
 * 获取后端脚本路径
 */
function getBackendScriptPath() {
  const backendDir = path.join(__dirname, '..', 'backend');
  // 生产环境使用 PyInstaller 打包的 exe
  if (!isDev && process.platform === 'win32') {
    const exePath = path.join(backendDir, 'dist', 'main_ai_edu.exe');
    if (fs.existsSync(exePath)) return { type: 'exe', path: exePath };
  }
  // 开发环境使用源码
  const scriptPath = path.join(backendDir, 'main_ai_edu.py');
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
      preload: path.join(__dirname, 'preload-splash.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'build', 'icon.ico'),
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));

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
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'build', 'icon.ico'),
    titleBarStyle: 'default',
    title: 'MatuX',
  });

  // 加载前端应用
  const frontendPath = path.join(__dirname, '..', 'dist', 'imatuproject', 'index.html');

  if (isDev) {
    mainWindow.loadURL('http://localhost:4200');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(frontendPath);
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
    }, 200);
  });

  // 最小化到托盘而非关闭
  mainWindow.on('close', (event) => {
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
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'build', 'icon.ico'),
    title,
  });

  // 加载页面
  if (url.startsWith('http') || url.startsWith('/')) {
    const fullUrl = url.startsWith('http')
      ? url
      : (isDev ? `http://localhost:4200` : `file://${path.join(__dirname, '..', 'dist', 'imatuproject', 'index.html')}`) + (url.startsWith('/') ? `#${url}` : url);
    childWin.loadURL(fullUrl);
  } else if (isDev) {
    childWin.loadURL(`http://localhost:4200#${url}`);
  } else {
    const frontendPath = path.join(__dirname, '..', 'dist', 'imatuproject', 'index.html');
    childWin.loadFile(frontendPath, { hash: url });
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
  const iconPath = path.join(__dirname, 'build', 'icon.ico');
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
    icon: path.join(__dirname, 'build', 'icon.ico'),
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

  const pythonInfo = detectPython();
  if (!pythonInfo.available) {
    sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);
    return;
  }

  const backendInfo = getBackendScriptPath();
  console.log(`[INFO] Python: ${pythonInfo.path} (${pythonInfo.version})`);
  console.log(`[INFO] 后端入口: ${backendInfo.path} (${backendInfo.type})`);

  sendSplashStatus('starting-backend', '正在启动后端服务...', 20);

  const backendDir = path.join(__dirname, '..', 'backend');

  if (backendInfo.type === 'exe') {
    // 生产环境：直接运行 PyInstaller 打包的 exe
    backendProcess = spawn(backendInfo.path, [], {
      cwd: backendDir,
      env: { ...process.env, PORT: BACKEND_PORT.toString() },
      windowsHide: true,
    });
  } else {
    // 开发环境：运行 Python 脚本
    backendProcess = spawn(pythonInfo.path, [backendInfo.path], {
      cwd: backendDir,
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
  });

  backendProcess.on('close', (code, signal) => {
    console.log(`[INFO] 后端服务已退出 (code: ${code}, signal: ${signal})`);

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
 * 等待后端服务就绪
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
    console.log('[INFO] 后端服务已就绪！');
    sendSplashStatus('backend-ready', '后端服务就绪 ✓', 90);
    restartAttempts = 0; // 重置重启计数
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
    const response = await fetch(`${BACKEND_URL}/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * 启动周期性健康检查
 */
function startHealthCheck() {
  if (healthCheckTimer) clearInterval(healthCheckTimer);
  healthCheckTimer = setInterval(async () => {
    const healthy = await healthCheck();
    if (!healthy && !isQuitting) {
      console.warn('[WARN] 健康检查失败，后端可能已崩溃');
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('app-event', { type: 'backend-disconnected' });
      }
    }
  }, HEALTH_CHECK_INTERVAL);
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
 * 优雅关闭所有进程
 */
function gracefulShutdown() {
  isQuitting = true;

  // 注销全局快捷键
  unregisterGlobalShortcuts();

  if (healthCheckTimer) {
    clearInterval(healthCheckTimer);
    healthCheckTimer = null;
  }

  stopBackend();

  // 销毁系统托盘
  if (tray) {
    tray.destroy();
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

  // 发送原生通知
  ipcMain.handle('show-notification', async (_event, title, body, category) => {
    showNotification(title, body, category);
    return { success: true };
  });

  // 检查更新
  ipcMain.handle('check-for-updates', async () => {
    await checkForUpdates();
    return { success: true };
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
    stopBackend();
    await new Promise((r) => setTimeout(r, 1000));
    startBackend();
    const ready = await waitForBackend();
    if (ready) {
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
  const pythonInfo = detectPython();

  if (!pythonInfo.available) {
    // Python 不可用 - 显示错误并提供引导
    sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);

    // 弹出系统对话框引导安装
    const { response } = await dialog.showMessageBox({
      type: 'warning',
      title: '缺少 Python 环境',
      message: 'MatuX 需要 Python 3.9 或更高版本',
      detail: '检测到您的系统未安装 Python 或版本过低。\n\n请安装 Python 3.9+ 后重启 MatuX。',
      buttons: ['下载 Python', '稍后再说'],
      defaultId: 0,
    });

    if (response === 0) {
      shell.openExternal('https://www.python.org/downloads/');
    }
    // 不退出，让用户看到 Splash 错误信息，可以重试
    return;
  }

  console.log(`[INFO] 检测到 Python ${pythonInfo.version} (${pythonInfo.path})`);

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
    return;
  }

  // 5. 启动健康检查
  startHealthCheck();

  // 6. 创建主窗口
  sendSplashStatus('loading-app', '正在加载应用...', 95);
  createMainWindow();

  // 7. 创建系统托盘
  createTray();

  // 8. 注册全局快捷键
  registerGlobalShortcuts();

  // 9. 设置文件关联
  setupFileAssociation();

  // 10. 通知主窗口已就绪（用于文件关联）
  mainWindow.once('ready-to-show', () => {
    app.emit('main-window-ready');
  });

  // 11. 启动后检查更新（延迟 30 秒避免影响启动速度）
  setTimeout(() => {
    checkForUpdates().catch((err) => {
      console.warn('[WARN] 更新检查失败:', err.message);
    });
  }, 30000);
});

// macOS 特殊处理
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    gracefulShutdown();
    app.quit();
  }
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
};
