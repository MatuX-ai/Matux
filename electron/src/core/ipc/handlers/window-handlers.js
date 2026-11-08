/**
 * 窗口控制 IPC Handlers
 * @module ipc/handlers/window-handlers
 */

const { ipcMain } = require('electron');
const { safeHandle } = require('./ipc-utils');

/**
 * 验证坐标值是否有效
 * @param {any} value 要验证的值
 * @returns {number|null} 有效则返回数字，否则返回 null
 */
function validateCoordinate(value) {
  const num = Number(value);
  if (!Number.isFinite(num) || num < 0 || num > 99999) {
    return null;
  }
  return Math.round(num);
}

/**
 * 验证尺寸值是否有效
 * @param {any} value 要验证的值
 * @param {number} min 最小值
 * @param {number} max 最大值
 * @returns {number|null} 有效则返回数字，否则返回 null
 */
function validateDimension(value, min = 100, max = 9999) {
  const num = Number(value);
  if (!Number.isFinite(num) || num < min || num > max) {
    return null;
  }
  return Math.round(num);
}

/**
 * 创建窗口 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.appState AppState 实例
 * @param {Function} [options.getMainWindow] 主窗口实时读取函数（优先于 appState）
 * @returns {object} handlers 对象
 */
function createWindowHandlers(options = {}) {
  const { appState = null, getMainWindow: getMainWindowFn = null } = options;

  /**
   * 获取主窗口引用
   *
   * 【无边框窗口 P3】优先使用调用方注入的实时读取函数：
   * createWindowHandlers 在主窗口创建之前注册，appState.getMainWindow()
   * 在部分启动路径下为 null，会导致窗口控制按钮静默失效。
   */
  function getMainWindow() {
    if (typeof getMainWindowFn === 'function') {
      const win = getMainWindowFn();
      return win && !win.isDestroyed() ? win : null;
    }
    const win = appState ? appState.getMainWindow() : null;
    return win && !win.isDestroyed() ? win : null;
  }

  /**
   * 注册所有窗口相关 IPC 处理器
   */
  function register() {
    // 获取窗口尺寸
    safeHandle('get-window-size', () => {
      const win = getMainWindow();
      if (!win) {
        return { width: 1400, height: 900 };
      }
      const [w, h] = win.getSize();
      return { width: w, height: h };
    });

    // 窗口最小化
    safeHandle('window-minimize', () => {
      getMainWindow()?.minimize();
      return { success: true };
    });

    // 窗口最大化/还原
    safeHandle('window-maximize', () => {
      const win = getMainWindow();
      if (win?.isMaximized()) {
        win.unmaximize();
      } else {
        win?.maximize();
      }
      return { success: true };
    });

    // 窗口关闭
    safeHandle('window-close', () => {
      getMainWindow()?.close();
      return { success: true };
    });

    // 是否最大化
    safeHandle('window-is-maximized', () => {
      return {
        success: true,
        isMaximized: getMainWindow()?.isMaximized() || false
      };
    });

    // ==================== 无边框自定义标题栏（P3） ====================
    // 与上面短横线通道等价，命名对齐 Electron 官方 window:* 约定。
    // 渲染进程只需维护一套 windowControls API，旧通道保留向后兼容。

    safeHandle('window:minimize', () => {
      getMainWindow()?.minimize();
      return { success: true };
    });

    safeHandle('window:maximize', () => {
      const win = getMainWindow();
      if (!win) return { success: false };
      if (win.isMaximized()) {
        win.unmaximize();
      } else {
        win.maximize();
      }
      return { success: true };
    });

    safeHandle('window:close', () => {
      getMainWindow()?.close();
      return { success: true };
    });

    safeHandle('window:is-maximized', () => {
      return {
        success: true,
        isMaximized: getMainWindow()?.isMaximized() || false,
      };
    });

    // 全屏切换
    safeHandle('window-toggle-fullscreen', () => {
      const win = getMainWindow();
      if (win) {
        win.setFullScreen(!win.isFullScreen());
      }
      return { success: true };
    });

    // 获取窗口位置
    safeHandle('get-window-position', () => {
      const win = getMainWindow();
      if (!win) {
        return { x: 0, y: 0 };
      }
      const [x, y] = win.getPosition();
      return { x, y };
    });

    // 设置窗口位置（带参数验证）
    safeHandle('set-window-position', (_event, x, y) => {
      const validX = validateCoordinate(x);
      const validY = validateCoordinate(y);
      
      if (validX === null || validY === null) {
        return { success: false, error: '坐标值无效，必须是非负整数' };
      }
      
      const win = getMainWindow();
      if (win) {
        win.setPosition(validX, validY);
      }
      return { success: true };
    });

    // 设置窗口尺寸（带参数验证）
    safeHandle('set-window-size', (_event, width, height) => {
      const validWidth = validateDimension(width, 100, 9999);
      const validHeight = validateDimension(height, 100, 9999);
      
      if (validWidth === null || validHeight === null) {
        return { success: false, error: '尺寸值无效，必须在 100-9999 之间' };
      }
      
      const win = getMainWindow();
      if (win) {
        win.setSize(validWidth, validHeight);
      }
      return { success: true };
    });
  }

  return {
    register,
  };
}

module.exports = { createWindowHandlers, validateCoordinate, validateDimension };
