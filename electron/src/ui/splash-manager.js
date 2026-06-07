/**
 * MatuX Electron 启动画面管理器
 *
 * 负责 Splash Screen 的创建、状态更新和显示控制
 *
 * @module ui/splash-manager
 */

const { BrowserWindow } = require('electron');
const { SPLASH_WINDOW_SIZE, APP_PATHS } = require('../../config/constants');

/**
 * 创建启动画面管理器
 * @param {object} options 配置选项
 * @returns {object} SplashManager 实例
 */
function createSplashManager(options = {}) {
  let window = null;

  /**
   * 创建并显示启动画面
   */
  function create() {
    if (window) {
      return window;
    }

    window = new BrowserWindow({
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

    window.loadFile(APP_PATHS.splashHtml);

    window.once('ready-to-show', () => {
      window.show();
    });

    window.on('closed', () => {
      window = null;
    });

    return window;
  }

  /**
   * 显示启动画面
   */
  function show() {
    if (!window) {
      create();
    }
    if (window && !window.isVisible()) {
      window.show();
    }
  }

  /**
   * 关闭启动画面
   */
  function close() {
    if (window && !window.isDestroyed()) {
      window.close();
      window = null;
    }
  }

  /**
   * 发送状态更新到启动画面
   * @param {string} phase 阶段标识
   * @param {string} text 显示文本
   * @param {number} progress 进度 0-100
   * @param {string} [detail] 详细描述
   * @param {Array} [modules] 模块列表
   */
  function report(phase, text, progress, detail = null, modules = null) {
    if (window && !window.isDestroyed()) {
      window.webContents.send('splash-status', { phase, text, progress, detail, modules });
    }
    // 同时打印到控制台
    const prefix = (phase === 'error' || phase === 'backend-error') ? '[ERROR]' : '[INFO]';
    console.log(`${prefix} ${text}`);
  }

  /**
   * 获取窗口实例
   */
  function getWindow() {
    return window;
  }

  /**
   * 检查是否已销毁
   */
  function isDestroyed() {
    return !window || window.isDestroyed();
  }

  return {
    create,
    show,
    close,
    report,
    getWindow,
    isDestroyed,
  };
}

module.exports = { createSplashManager };
