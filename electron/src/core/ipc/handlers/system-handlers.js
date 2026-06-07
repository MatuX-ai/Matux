/**
 * 系统相关 IPC Handlers
 * @module ipc/handlers/system-handlers
 */

const { ipcMain } = require('electron');

/**
 * 创建系统 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.app Electron app 实例
 * @param {boolean} options.isDev 是否开发模式
 * @returns {object} handlers 对象
 */
function createSystemHandlers(options = {}) {
  const { app = null, isDev = false } = options;

  /**
   * 注册所有系统相关 IPC 处理器
   */
  function register() {
    // 获取应用信息
    ipcMain.handle('get-app-info', () => {
      if (!app) {
        return {
          version: 'unknown',
          name: 'MatuX',
          platform: process.platform,
          arch: process.arch,
          isDev,
        };
      }
      return {
        version: app.getVersion(),
        name: app.getName(),
        platform: process.platform,
        arch: process.arch,
        isDev,
      };
    });

    // 检查更新
    ipcMain.handle('check-for-updates', async () => {
      // 更新检查逻辑由主文件处理，此处仅返回成功
      return { success: true };
    });

    // 获取应用路径
    ipcMain.handle('get-app-path', (_event, name) => {
      if (app) {
        try {
          return { success: true, path: app.getPath(name) };
        } catch {
          return { success: false, error: '无效的路径名称' };
        }
      }
      return { success: false, error: '应用实例未初始化' };
    });

    // 获取进程信息
    ipcMain.handle('get-process-info', () => {
      return {
        success: true,
        pid: process.pid,
        platform: process.platform,
        arch: process.arch,
        version: process.version,
        memory: process.memoryUsage(),
      };
    });

    // 获取环境变量
    ipcMain.handle('get-env', (_event, key) => {
      if (key) {
        return { success: true, value: process.env[key] };
      }
      return { success: false, error: '未指定键名' };
    });

    // 获取当前工作目录
    ipcMain.handle('get-cwd', () => {
      return { success: true, path: process.cwd() };
    });
  }

  return {
    register,
  };
}

module.exports = { createSystemHandlers };
