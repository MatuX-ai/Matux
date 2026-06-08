/**
 * 窗口控制 IPC Handlers
 * @module ipc/handlers/window-handlers
 */

const { ipcMain } = require('electron');

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
 * @returns {object} handlers 对象
 */
function createWindowHandlers(options = {}) {
  const { appState = null } = options;

  /**
   * 获取主窗口引用
   */
  function getMainWindow() {
    return appState ? appState.getMainWindow() : null;
  }

  /**
   * 注册所有窗口相关 IPC 处理器
   */
  function register() {
    // 获取窗口尺寸
    ipcMain.handle('get-window-size', () => {
      const win = getMainWindow();
      if (!win) {
        return { width: 1400, height: 900 };
      }
      const [w, h] = win.getSize();
      return { width: w, height: h };
    });

    // 窗口最小化
    ipcMain.handle('window-minimize', () => {
      getMainWindow()?.minimize();
      return { success: true };
    });

    // 窗口最大化/还原
    ipcMain.handle('window-maximize', () => {
      const win = getMainWindow();
      if (win?.isMaximized()) {
        win.unmaximize();
      } else {
        win?.maximize();
      }
      return { success: true };
    });

    // 窗口关闭
    ipcMain.handle('window-close', () => {
      getMainWindow()?.close();
      return { success: true };
    });

    // 是否最大化
    ipcMain.handle('window-is-maximized', () => {
      return {
        success: true,
        isMaximized: getMainWindow()?.isMaximized() || false
      };
    });

    // 全屏切换
    ipcMain.handle('window-toggle-fullscreen', () => {
      const win = getMainWindow();
      if (win) {
        win.setFullScreen(!win.isFullScreen());
      }
      return { success: true };
    });

    // 获取窗口位置
    ipcMain.handle('get-window-position', () => {
      const win = getMainWindow();
      if (!win) {
        return { x: 0, y: 0 };
      }
      const [x, y] = win.getPosition();
      return { x, y };
    });

    // 设置窗口位置（带参数验证）
    ipcMain.handle('set-window-position', (_event, x, y) => {
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
    ipcMain.handle('set-window-size', (_event, width, height) => {
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
