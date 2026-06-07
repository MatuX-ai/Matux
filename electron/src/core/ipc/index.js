/**
 * IPC 路由分发器
 * @module core/ipc
 *
 * 统一管理所有 IPC 通信，提供模块化的 handler 注册
 */

const {
  createBackendHandlers,
  createWindowHandlers,
  createNotificationHandlers,
  createSystemHandlers,
} = require('./handlers');

/**
 * 创建 IPC 路由配置
 * @param {object} deps 依赖注入
 * @param {object} deps.app Electron app 实例
 * @param {object} deps.appState AppState 实例
 * @param {object} deps.backendManager BackendManager 实例
 * @param {function} deps.showNotification 通知显示函数
 * @param {boolean} deps.isDev 是否开发模式
 * @returns {object} IPC 路由对象
 */
function createIpcRouter(deps) {
  const {
    app = null,
    appState = null,
    backendManager = null,
    showNotification = null,
    isDev = false,
  } = deps;

  // 创建各个 handler
  const backendHandlers = createBackendHandlers({ backendManager, appState });
  const windowHandlers = createWindowHandlers({ appState });
  const notificationHandlers = createNotificationHandlers({ appState, showNotification });
  const systemHandlers = createSystemHandlers({ app, isDev });

  /**
   * 注册所有 IPC 处理器
   */
  function registerAll() {
    backendHandlers.register();
    windowHandlers.register();
    notificationHandlers.register();
    systemHandlers.register();
  }

  return {
    registerAll,
    // 单独暴露各模块注册方法（供外部调用）
    registerBackendHandlers: backendHandlers.register,
    registerWindowHandlers: windowHandlers.register,
    registerNotificationHandlers: notificationHandlers.register,
    registerSystemHandlers: systemHandlers.register,
  };
}

module.exports = {
  createIpcRouter,
};
