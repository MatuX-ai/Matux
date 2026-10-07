/**
 * IPC 安全注册工具
 * @module ipc/handlers/ipc-utils
 *
 * 将 safeHandle 从 handlers/index.js 抽出，避免与其他 handler 模块
 * 形成循环依赖（历史上 backend-handlers.js 与 index.js 互相 require，
 * 导致在循环未闭合时 safeHandle 尚未挂到 module.exports 上）。
 */

const { ipcMain } = require('electron');

// 注册表 - 跟踪已注册的 channel, 防止重复注册
const registeredChannels = new Set();

/**
 * 安全注册 IPC handler
 * 若 channel 已被注册, 输出警告并跳过, 防止重复注册引发 Electron 告警
 *
 * @param {string} channel - IPC 通道名
 * @param {Function} handler - 处理函数
 * @returns {boolean} 是否成功注册
 */
function safeHandle(channel, handler) {
  if (registeredChannels.has(channel)) {
    console.warn(`[IPC][WARN] 重复注册检测: ${channel} (已跳过)`);
    return false;
  }
  registeredChannels.add(channel);
  ipcMain.handle(channel, handler);
  return true;
}

/**
 * 重置注册表 (仅用于测试场景)
 */
function _resetRegisteredChannels() {
  registeredChannels.clear();
}

/**
 * 获取已注册 channel 列表 (用于调试)
 */
function getRegisteredChannels() {
  return Array.from(registeredChannels);
}

module.exports = {
  safeHandle,
  getRegisteredChannels,
  _resetRegisteredChannels,
};
