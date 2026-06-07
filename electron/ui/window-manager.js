/**
 * MatuX Electron 窗口管理器
 * 
 * 负责主窗口和子窗口的创建、状态管理
 */

const { BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');
const { DEFAULT_WINDOW_SIZE, APP_PATHS, isDev, WINDOW_STATE_FILE } = require('../config/constants');

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
    fs.writeFileSync(WINDOW_STATE_FILE, JSON.stringify({
      ...bounds,
      isMaximized,
    }, null, 2));
  } catch (_) { /* 忽略写入错误 */ }
}

class WindowManager {
  constructor() {
    this.mainWindow = null;
    this.childWindows = new Set();
  }

  /**
   * 创建主窗口
   * @param {BrowserWindow} splashWindow 启动画面窗口（用于关闭）
   * @returns {BrowserWindow}
   */
  createMain(splashWindow = null) {
    const savedState = loadWindowState();
    const { width: DEF_W, height: DEF_H, minWidth: MIN_W, minHeight: MIN_H } = DEFAULT_WINDOW_SIZE;

    this.mainWindow = new BrowserWindow({
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
      this.mainWindow.maximize();
    }

    // 加载前端应用
    if (isDev) {
      this.mainWindow.loadURL('http://localhost:4200');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(APP_PATHS.frontendIndex);
    }

    // 主窗口就绪后关闭 Splash
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
      }
    });

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    // 窗口失焦检测（防作弊用）
    this.mainWindow.on('blur', () => {
      this.mainWindow.webContents.send('app-event', { type: 'window-blur' });
    });

    this.mainWindow.on('focus', () => {
      this.mainWindow.webContents.send('app-event', { type: 'window-focus' });
    });

    // 全屏状态变化
    this.mainWindow.on('enter-full-screen', () => {
      this.mainWindow.webContents.send('app-event', { type: 'fullscreen-enter' });
    });

    this.mainWindow.on('leave-full-screen', () => {
      this.mainWindow.webContents.send('app-event', { type: 'fullscreen-leave' });
    });

    // 窗口大小变化（节流保存）
    let resizeTimeout;
    this.mainWindow.on('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        const [w, h] = this.mainWindow.getSize();
        this.mainWindow.webContents.send('app-event', {
          type: 'window-resize',
          width: w,
          height: h,
        });
        saveWindowState(this.mainWindow);
      }, 200);
    });

    // 窗口移动时保存位置（防抖）
    let moveTimeout;
    this.mainWindow.on('move', () => {
      clearTimeout(moveTimeout);
      moveTimeout = setTimeout(() => { saveWindowState(this.mainWindow); }, 500);
    });

    // 最小化到托盘而非关闭
    this.mainWindow.on('close', (event) => {
      saveWindowState(this.mainWindow);
      // 注意：托盘关闭逻辑需要在主进程处理
    });

    return this.mainWindow;
  }

  /**
   * 创建子窗口（数字孪生实验室弹出窗口等）
   * @param {object} options 子窗口配置
   * @param {number} [options.width=1280] 窗口宽度
   * @param {number} [options.height=800] 窗口高度
   * @param {string} [options.title='MatuX 实验窗口'] 窗口标题
   * @param {string} [options.url=''] 加载的 URL 或路径
   */
  createChild(options = {}) {
    const {
      width = 1280,
      height = 800,
      title = 'MatuX 实验窗口',
      url = '',
    } = options;

    const childWin = new BrowserWindow({
      width,
      height,
      minWidth: 800,
      minHeight: 600,
      parent: this.mainWindow,
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

    this.childWindows.add(childWin);
    childWin.on('closed', () => {
      this.childWindows.delete(childWin);
    });

    return childWin;
  }

  /**
   * 获取主窗口
   */
  getMain() {
    return this.mainWindow;
  }

  /**
   * 获取所有子窗口
   */
  getChildren() {
    return [...this.childWindows];
  }

  /**
   * 检查主窗口是否已销毁
   */
  isMainDestroyed() {
    return !this.mainWindow || this.mainWindow.isDestroyed();
  }

  /**
   * 最小化主窗口
   */
  minimize() {
    this.mainWindow?.minimize();
  }

  /**
   * 最大化/还原主窗口
   */
  toggleMaximize() {
    if (this.mainWindow?.isMaximized()) {
      this.mainWindow.unmaximize();
    } else {
      this.mainWindow?.maximize();
    }
  }

  /**
   * 关闭主窗口
   */
  close() {
    this.mainWindow?.close();
  }

  /**
   * 获取主窗口尺寸
   */
  getSize() {
    if (!this.mainWindow || this.mainWindow.isDestroyed()) {
      return { width: DEFAULT_WINDOW_SIZE.width, height: DEFAULT_WINDOW_SIZE.height };
    }
    const [w, h] = this.mainWindow.getSize();
    return { width: w, height: h };
  }

  /**
   * 是否最大化
   */
  isMaximized() {
    return this.mainWindow?.isMaximized() || false;
  }
}

module.exports = { WindowManager, loadWindowState, saveWindowState };
