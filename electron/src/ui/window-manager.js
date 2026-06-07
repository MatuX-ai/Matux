/**
 * MatuX Electron 窗口管理器
 *
 * 负责主窗口和子窗口的创建、状态管理
 *
 * @module ui/window-manager
 */

const { BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');
const {
  DEFAULT_WINDOW_SIZE,
  APP_PATHS,
  isDev,
  WINDOW_STATE_FILE,
} = require('../../config/constants');

/**
 * 加载窗口状态
 */
function loadWindowState() {
  try {
    if (fs.existsSync(WINDOW_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(WINDOW_STATE_FILE, 'utf-8'));
    }
  } catch (_) { /* 忽略解析错误 */ }
  return { ...DEFAULT_WINDOW_SIZE };
}

/**
 * 保存窗口状态
 */
function saveWindowState(window) {
  if (!window || window.isDestroyed()) return;
  try {
    const bounds = window.getBounds();
    const isMaximized = window.isMaximized();
    fs.writeFileSync(
      WINDOW_STATE_FILE,
      JSON.stringify({
        ...bounds,
        isMaximized,
      }, null, 2)
    );
  } catch (_) { /* 忽略写入错误 */ }
}

/**
 * 创建窗口管理器
 * @param {object} options 配置选项
 * @param {function} options.onChildWindowCreate 子窗口创建回调
 * @returns {object} WindowManager 实例
 */
function createWindowManager(options = {}) {
  const { onChildWindowCreate = null } = options;

  let mainWindow = null;
  const childWindows = new Set();

  /**
   * 创建主窗口
   * @param {BrowserWindow} splashWindow 启动画面窗口（用于关闭）
   * @returns {BrowserWindow}
   */
  function createMain(splashWindow = null) {
    const savedState = loadWindowState();
    const { width: DEF_W, height: DEF_H, minWidth: MIN_W, minHeight: MIN_H } = DEFAULT_WINDOW_SIZE;

    mainWindow = new BrowserWindow({
      width: savedState.width || DEF_W,
      height: savedState.height || DEF_H,
      minWidth: MIN_W,
      minHeight: MIN_H,
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

    // 窗口大小变化（节流保存）
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
        saveWindowState(mainWindow);
      }, 200);
    });

    // 窗口移动时保存位置（防抖）
    let moveTimeout;
    mainWindow.on('move', () => {
      clearTimeout(moveTimeout);
      moveTimeout = setTimeout(() => {
        saveWindowState(mainWindow);
      }, 500);
    });

    // 最小化到托盘而非关闭
    mainWindow.on('close', (event) => {
      saveWindowState(mainWindow);
      // 注意：托盘关闭逻辑需要在主进程处理
    });

    return mainWindow;
  }

  /**
   * 创建子窗口（数字孪生实验室弹出窗口等）
   * @param {object} opts 子窗口配置
   * @param {number} [opts.width=1280] 窗口宽度
   * @param {number} [opts.height=800] 窗口高度
   * @param {string} [opts.title='MatuX 实验窗口'] 窗口标题
   * @param {string} [opts.url=''] 加载的 URL 或路径
   */
  function createChild(opts = {}) {
    const {
      width = 1280,
      height = 800,
      title = 'MatuX 实验窗口',
      url = '',
    } = opts;

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
    if (url.startsWith('http://') || url.startsWith('https://')) {
      childWin.loadURL(url);
    } else if (url.startsWith('/') || isDev) {
      const baseUrl = isDev ? 'http://localhost:4200' : APP_PATHS.frontendIndex;
      const hashPath = url.startsWith('/') ? url : `/${url}`;
      if (isDev) {
        childWin.loadURL(`${baseUrl}#${hashPath}`);
      } else {
        childWin.loadFile(baseUrl, { hash: hashPath });
      }
    } else {
      childWin.loadFile(APP_PATHS.frontendIndex, { hash: url.startsWith('/') ? url : `/${url}` });
    }

    childWindows.add(childWin);
    childWin.on('closed', () => {
      childWindows.delete(childWin);
    });

    if (onChildWindowCreate) {
      onChildWindowCreate(childWin);
    }

    return childWin;
  }

  /**
   * 获取主窗口
   */
  function getMain() {
    return mainWindow;
  }

  /**
   * 获取所有子窗口
   */
  function getChildren() {
    return [...childWindows];
  }

  /**
   * 检查主窗口是否已销毁
   */
  function isMainDestroyed() {
    return !mainWindow || mainWindow.isDestroyed();
  }

  /**
   * 最小化主窗口
   */
  function minimize() {
    mainWindow?.minimize();
  }

  /**
   * 最大化/还原主窗口
   */
  function toggleMaximize() {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  }

  /**
   * 关闭主窗口
   */
  function close() {
    mainWindow?.close();
  }

  /**
   * 获取主窗口尺寸
   */
  function getSize() {
    if (!mainWindow || mainWindow.isDestroyed()) {
      return { width: DEFAULT_WINDOW_SIZE.width, height: DEFAULT_WINDOW_SIZE.height };
    }
    const [w, h] = mainWindow.getSize();
    return { width: w, height: h };
  }

  /**
   * 是否最大化
   */
  function isMaximized() {
    return mainWindow?.isMaximized() || false;
  }

  return {
    createMain,
    createChild,
    getMain,
    getChildren,
    isMainDestroyed,
    minimize,
    toggleMaximize,
    close,
    getSize,
    isMaximized,
  };
}

module.exports = {
  createWindowManager,
  loadWindowState,
  saveWindowState,
};
