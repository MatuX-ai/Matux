/**
 * 通知系统 IPC Handlers
 * @module ipc/handlers/notification-handlers
 */

const { ipcMain, Notification } = require('electron');

/**
 * 创建通知 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.appState AppState 实例
 * @param {function} options.showNotification 通知显示函数
 * @returns {object} handlers 对象
 */
function createNotificationHandlers(options = {}) {
  const { appState = null, showNotification = null } = options;

  /**
   * 获取主窗口引用
   */
  function getMainWindow() {
    return appState ? appState.getMainWindow() : null;
  }

  /**
   * 注册所有通知相关 IPC 处理器
   */
  function register() {
    // 显示通知
    ipcMain.handle('show-notification', async (_event, title, body, category) => {
      if (showNotification) {
        showNotification(title, body, category, getMainWindow());
      } else {
        // Fallback: 使用 Electron 原生通知
        if (Notification.isSupported()) {
          const notification = new Notification({
            title,
            body,
          });
          notification.show();
        }
      }
      return { success: true };
    });

    // 显示错误通知
    ipcMain.handle('show-error-notification', async (_event, title, body) => {
      if (showNotification) {
        showNotification(title, body, 'error', getMainWindow());
      } else {
        if (Notification.isSupported()) {
          const notification = new Notification({
            title,
            body,
            urgency: 'critical',
          });
          notification.show();
        }
      }
      return { success: true };
    });

    // 显示成功通知
    ipcMain.handle('show-success-notification', async (_event, title, body) => {
      if (showNotification) {
        showNotification(title, body, 'success', getMainWindow());
      } else {
        if (Notification.isSupported()) {
          const notification = new Notification({
            title,
            body,
          });
          notification.show();
        }
      }
      return { success: true };
    });
  }

  return {
    register,
  };
}

module.exports = { createNotificationHandlers };
