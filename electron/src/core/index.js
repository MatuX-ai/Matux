/**
 * MatuX Electron Core 模块统一导出
 *
 * @module core
 */

// 后端管理
const backendCore = require('./backend');

// 健康监控
const { createHealthMonitor } = require('./health-monitor');

// 快捷键管理
const { createShortcutManager } = require('./shortcut-manager');

// 应用启动管理
const { createAppStartup } = require('./app-startup');

module.exports = {
  // 后端管理
  ...backendCore,

  // 健康监控
  createHealthMonitor,

  // 快捷键管理
  createShortcutManager,

  // 应用启动管理
  createAppStartup,
};
