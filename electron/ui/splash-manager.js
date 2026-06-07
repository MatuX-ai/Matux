/**
 * MatuX Electron 启动画面管理器
 * 
 * 负责 Splash Screen 的创建、状态更新和显示控制
 */

const { BrowserWindow } = require('electron');
const { SPLASH_WINDOW_SIZE, APP_PATHS } = require('../config/constants');

class SplashManager {
  constructor() {
    this.window = null;
  }

  /**
   * 创建并显示启动画面
   */
  create() {
    if (this.window) {
      return this.window;
    }

    this.window = new BrowserWindow({
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

    this.window.loadFile(APP_PATHS.splashHtml);

    this.window.once('ready-to-show', () => {
      this.window.show();
    });

    this.window.on('closed', () => {
      this.window = null;
    });

    return this.window;
  }

  /**
   * 显示启动画面
   */
  show() {
    if (!this.window) {
      this.create();
    }
    if (this.window && !this.window.isVisible()) {
      this.window.show();
    }
  }

  /**
   * 关闭启动画面
   */
  close() {
    if (this.window && !this.window.isDestroyed()) {
      this.window.close();
      this.window = null;
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
  report(phase, text, progress, detail = null, modules = null) {
    if (this.window && !this.window.isDestroyed()) {
      this.window.webContents.send('splash-status', { phase, text, progress, detail, modules });
    }
    // 同时打印到控制台
    const prefix = (phase === 'error' || phase === 'backend-error') ? '[ERROR]' : '[INFO]';
    console.log(`${prefix} ${text}`);
  }

  /**
   * 获取窗口实例
   */
  getWindow() {
    return this.window;
  }

  /**
   * 检查是否已销毁
   */
  isDestroyed() {
    return !this.window || this.window.isDestroyed();
  }
}

module.exports = { SplashManager };
