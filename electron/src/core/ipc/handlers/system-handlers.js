/**
 * 系统相关 IPC Handlers
 * @module ipc/handlers/system-handlers
 */

const { ipcMain } = require('electron');

// 允许通过 IPC 读取的环境变量白名单（禁止读取敏感信息）
const ALLOWED_ENV_KEYS = [
  'NODE_ENV',
  'BACKEND_PORT',
  'BACKEND_HOST',
  'ELECTRON_DISABLE_SANDBOX',
  'ELECTRON_NO_ASAR',
  'ELECTRON_RUN_AS_NODE',
  // 可安全暴露给渲染进程的变量
];

/**
 * 检查环境变量是否允许读取
 * @param {string} key 环境变量名
 * @returns {boolean}
 */
function isEnvKeyAllowed(key) {
  if (!key || typeof key !== 'string') return false;
  
  // 禁止以下前缀的环境变量
  const forbiddenPrefixes = [
    'SECRET', 'PASSWORD', 'PASSWD', 'KEY', 'TOKEN', 'API',
    'AUTH', 'CREDENTIAL', 'PRIVATE', 'DATABASE', 'DB_',
    'MYSQL', 'POSTGRES', 'MONGODB', 'REDIS',
  ];
  
  const upperKey = key.toUpperCase();
  if (forbiddenPrefixes.some((prefix) => upperKey.startsWith(prefix))) {
    return false;
  }
  
  return ALLOWED_ENV_KEYS.includes(key) || ALLOWED_ENV_KEYS.includes(upperKey);
}

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

    // 获取环境变量（带白名单限制）
    ipcMain.handle('get-env', (_event, key) => {
      if (!key || typeof key !== 'string') {
        return { success: false, error: '未指定键名' };
      }
      
      if (!isEnvKeyAllowed(key)) {
        return { success: false, error: '该环境变量不允许访问' };
      }
      
      const value = process.env[key];
      return { success: true, value: value ?? null };
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

module.exports = { createSystemHandlers, isEnvKeyAllowed, ALLOWED_ENV_KEYS };
