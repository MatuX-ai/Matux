/**
 * 窗口控制 IPC Handlers
 * @module ipc/handlers/window-handlers
 */

const { ipcMain } = require('electron');

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

    // 设置窗口位置
    ipcMain.handle('set-window-position', (_event, x, y) => {
      const win = getMainWindow();
      if (win) {
        win.setPosition(x, y);
      }
      return { success: true };
    });

    // 设置窗口尺寸
    ipcMain.handle('set-window-size', (_event, width, height) => {
      const win = getMainWindow();
      if (win) {
        win.setSize(width, height);
      }
      return { success: true };
    });
  }

  return {
    register,
  };
}

module.exports = { createWindowHandlers };
