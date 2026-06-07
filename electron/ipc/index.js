/**
 * IPC 路由分发器
 * @module ipc/router
 *
 * 统一管理所有 IPC 通信，减少主文件的复杂度
 * 
 * 【重构】现在使用 src/core/ipc/handlers/ 下的模块化 handlers
 * 此文件保留向后兼容，实际逻辑已迁移到 src/core/ipc/
 */

const { createIpcRouter } = require('../src/core/ipc');

/**
 * 创建 IPC 路由配置
 * @param {object} deps 依赖注入
 */
function createIpcRouterLegacy(deps) {
  // 转发到新的模块化实现
  const router = createIpcRouter(deps);

  return {
    registerAll: router.registerAll,
    registerBackendHandlers: router.registerBackendHandlers,
    registerWindowHandlers: router.registerWindowHandlers,
    registerNotificationHandlers: router.registerNotificationHandlers,
    registerSystemHandlers: router.registerSystemHandlers,
  };
}

// 向后兼容：保留旧的导出
module.exports = { createIpcRouter: createIpcRouterLegacy };
