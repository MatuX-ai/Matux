/**
 * MatuX Electron UI 模块统一导出
 *
 * @module ui
 */

// 通知系统
const { createNotificationManager, showAppNotification } = require('./notification');

// 启动画面
// 【修复 #6】同时导出 SplashManager 别名（与旧版 electron/ui/splash-manager.js 兼容）
const { createSplashManager, SplashManager } = require('./splash-manager');

// 系统托盘
const { createTrayManager, showNotification } = require('./tray-manager');

// 窗口管理
const { createWindowManager, loadWindowState, saveWindowState } = require('./window-manager');

module.exports = {
  // 通知系统
  createNotificationManager,
  showAppNotification,

  // 启动画面
  createSplashManager,
  SplashManager, // 【修复 #6】保留旧版 SplashManager 类导出名

  // 系统托盘
  createTrayManager,
  showNotification,

  // 窗口管理
  createWindowManager,
  loadWindowState,
  saveWindowState,
};
