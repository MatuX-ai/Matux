/**
 * 后端管理 IPC Handlers
 * @module ipc/handlers/backend-handlers
 */

const { ipcMain } = require('electron');
// 从 backend 模块导入（无需通过 main.js）
const backendCore = require('../../backend');
const { BACKEND_URL } = require('../../../../config/constants');
const { safeHandle } = require('./ipc-utils');

/**
 * 创建后端 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.backendManager BackendManager 实例
 * @param {object} options.appState AppState 实例
 * @returns {object} handlers 对象
 */
function createBackendHandlers(options = {}) {
  const { backendManager = null, appState = null, appInitializer = null } = options;

  /**
   * 注册所有后端相关 IPC 处理器
   */
  function register() {
    // 获取后端 URL
    safeHandle('get-backend-url', () => {
      return BACKEND_URL;
    });

    // 健康检查
    safeHandle('health-check', async () => {
      try {
        // 降级模式下直接返回降级状态
        if (appInitializer?.isRunningDegraded?.()) {
          return { success: false, degraded: true, error: 'Running in degraded mode (no Python backend)' };
        }
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
      } catch (err) {
        console.error('[ERROR] 健康检查 IPC 处理失败:', err.message);
        return { success: false, error: err.message };
      }
    });

    // 获取模块状态
    safeHandle('backend:module-status', () => {
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
    safeHandle('backend:restart', async () => {
      try {
        if (backendManager) {
          await backendManager.restart();
          return { success: true, message: '后端重启中' };
        }
        return { success: false, error: '后端管理器未初始化' };
      } catch (err) {
        console.error('[ERROR] 后端重启 IPC 处理失败:', err.message);
        return { success: false, error: err.message };
      }
    });

    // 【降级模式】查询当前是否处于降级模式
    safeHandle('backend:is-degraded', () => {
      return {
        degraded: appInitializer?.isRunningDegraded?.() ?? false,
      };
    });

    // 【降级模式】重试后端设置（退出降级模式路径）
    safeHandle('backend:retry-setup', async () => {
      try {
        if (!appInitializer) {
          return { success: false, error: 'AppInitializer 未初始化' };
        }
        if (!appInitializer.isRunningDegraded()) {
          return { success: false, error: '当前未处于降级模式' };
        }
        // 重新尝试初始化（重新检测 Python + 启动后端）
        const result = await appInitializer.initialize();
        if (result === true) {
          // 成功退出降级模式
          appInitializer.isDegraded = false;
          const { BrowserWindow } = require('electron');
          const windows = BrowserWindow.getAllWindows();
          windows.forEach((win) => {
            if (!win.isDestroyed()) {
              win.webContents.send('app-event', { type: 'backend-ready' });
            }
          });
          return { success: true, message: '后端已成功启动，已退出降级模式' };
        }
        return { success: false, error: '后端启动仍失败，请确认 Python 环境已安装' };
      } catch (err) {
        console.error('[ERROR] 降级模式重试失败:', err.message);
        return { success: false, error: err.message };
      }
    });
  }

  return {
    register,
  };
}

module.exports = { createBackendHandlers };
