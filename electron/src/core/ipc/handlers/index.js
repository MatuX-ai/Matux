/**
 * IPC Handlers 统一导出
 * @module ipc/handlers
 *
 * 按功能分组的后端 IPC 处理器模块
 */

const { createBackendHandlers } = require('./backend-handlers');
const { createWindowHandlers } = require('./window-handlers');
const { createNotificationHandlers } = require('./notification-handlers');
const { createSystemHandlers } = require('./system-handlers');
const { createPluginHandlers } = require('./plugin-handlers');
const { createFsHandlers } = require('./fs-handlers');

module.exports = {
  // 后端管理
  createBackendHandlers,

  // 窗口控制
  createWindowHandlers,

  // 通知系统
  createNotificationHandlers,

  // 系统信息
  createSystemHandlers,

  // 插件管理
  createPluginHandlers,

  // 文件系统
  createFsHandlers,
};
