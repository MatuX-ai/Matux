/**
 * IPC Handlers 统一导出
 * @module ipc/handlers
 *
 * 按功能分组的后端 IPC 处理器模块
 *
 * 设计原则:
 * 1. 所有 IPC 注册走 safeHandle 防止重复注册 (历史告警: backend:activate-module 等)
 * 2. 注册表基于 Set 跟踪 channel, 避免 ipcMain.handle 抛出
 * 3. 重复注册时输出警告而非抛出, 防止阻塞启动
 */

const { ipcMain } = require('electron');

// safeHandle 已抽到 ipc-utils.js，避免与具体 handler 形成循环依赖
const { safeHandle, getRegisteredChannels, _resetRegisteredChannels } = require('./ipc-utils');

const { createBackendHandlers } = require('./backend-handlers');
const { createWindowHandlers } = require('./window-handlers');
const { createNotificationHandlers } = require('./notification-handlers');
const { createSystemHandlers } = require('./system-handlers');
const { createPluginHandlers } = require('./plugin-handlers');
const { createFsHandlers } = require('./fs-handlers');
const { createUpdaterHandlers } = require('./updater-handlers');

module.exports = {
  // 安全注册工具
  safeHandle,
  getRegisteredChannels,
  _resetRegisteredChannels,

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

  // 自动更新
  createUpdaterHandlers,
};