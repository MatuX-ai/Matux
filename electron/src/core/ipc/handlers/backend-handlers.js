/**
 * 后端管理 IPC Handlers
 * @module ipc/handlers/backend-handlers
 */

const { ipcMain } = require('electron');
// 从 backend 模块导入（无需通过 main.js）
const backendCore = require('../../backend');
const { BACKEND_URL } = require('../../../../config/constants');

/**
 * 创建后端 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.backendManager BackendManager 实例
 * @param {object} options.appState AppState 实例
 * @returns {object} handlers 对象
 */
function createBackendHandlers(options = {}) {
  const { backendManager = null, appState = null } = options;

  /**
   * 注册所有后端相关 IPC 处理器
   */
  function register() {
    // 获取后端 URL
    ipcMain.handle('get-backend-url', () => {
      return BACKEND_URL;
    });

    // 健康检查
    ipcMain.handle('health-check', async () => {
      if (backendManager && backendManager.healthChecker) {
        return await backendManager.healthChecker.check();
      }
      // fallback: 使用 backendCore 中的健康检查
      const { healthCheck } = backendCore;
      if (healthCheck) {
        const result = await healthCheck('localhost', 8000);
        return { success: result.success, status: result.status };
      }
      return { success: false, error: '健康检查器未初始化' };
    });

    // 获取模块状态
    ipcMain.handle('backend:module-status', () => {
      if (appState) {
        return {
          success: true,
          modules: appState.getModuleStatus(),
          backendStatus: appState.backendStatus,
        };
      }
      return {
        success: true,
        modules: [],
        backendStatus: 'unknown',
      };
    });

    // 重启后端
    ipcMain.handle('backend:restart', async () => {
      if (backendManager) {
        await backendManager.restart();
        return { success: true, message: '后端重启中' };
      }
      return { success: false, error: '后端管理器未初始化' };
    });
  }

  return {
    register,
  };
}

module.exports = { createBackendHandlers };
