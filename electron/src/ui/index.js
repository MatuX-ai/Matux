/**
 * MatuX Electron UI 模块统一导出
 *
 * @module ui
 */

// 通知系统
const { createNotificationManager, showAppNotification } = require('./notification');

// 启动画面
const { createSplashManager } = require('./splash-manager');

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

  // 系统托盘
  createTrayManager,
  showNotification,

  // 窗口管理
  createWindowManager,
  loadWindowState,
  saveWindowState,
};
