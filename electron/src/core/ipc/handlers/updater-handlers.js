/**
 * 自动更新 IPC Handlers
 * @module ipc/handlers/updater-handlers
 *
 * 提供渲染进程与 electron-updater 的 IPC 通信
 * 支持检查更新、下载更新、安装更新
 */

const { ipcMain } = require('electron');
const { safeHandle } = require('./ipc-utils');

/**
 * 创建自动更新 IPC 处理器
 * @param {Object} deps - 依赖注入
 * @param {Object} deps.updaterService - AutoUpdaterService 实例（可选）
 * @returns {{ register: Function }}
 */
function createUpdaterHandlers({ updaterService }) {
  return {
    register() {
      // 检查更新
      safeHandle('updater:check', async () => {
        try {
          if (!updaterService) {
            return { success: false, error: '更新服务未初始化' };
          }
          const result = await updaterService.checkForUpdates();
          return { success: true, data: result };
        } catch (err) {
          return { success: false, error: err.message };
        }
      });

      // 下载更新
      safeHandle('updater:download', async () => {
        try {
          if (!updaterService) {
            return { success: false, error: '更新服务未初始化' };
          }
          await updaterService.downloadUpdate();
          return { success: true };
        } catch (err) {
          return { success: false, error: err.message };
        }
      });

      // 安装并重启
      safeHandle('updater:install', async () => {
        try {
          if (!updaterService) {
            return { success: false, error: '更新服务未初始化' };
          }
          updaterService.quitAndInstall();
          return { success: true };
        } catch (err) {
          return { success: false, error: err.message };
        }
      });

      // 获取当前版本
      safeHandle('updater:get-version', async () => {
        try {
          if (!updaterService) {
            return { success: false, error: '更新服务未初始化' };
          }
          return { success: true, data: updaterService.getCurrentVersion() };
        } catch (err) {
          return { success: false, error: err.message };
        }
      });

      console.log('[IPC] 自动更新处理器已注册');
    },
  };
}

module.exports = { createUpdaterHandlers };
