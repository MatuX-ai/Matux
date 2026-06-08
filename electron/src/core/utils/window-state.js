/**
 * 窗口状态持久化模块
 * @module window-state
 *
 * 负责保存和恢复窗口的位置、大小和最大化状态
 */

const fs = require('fs');
const path = require('path');
const { WINDOW_STATE_FILE, DEFAULT_WINDOW_SIZE } = require('../../../config/constants');

/**
 * 加载窗口状态
 * @returns {Object} 窗口状态对象
 */
function loadWindowState() {
  try {
    if (fs.existsSync(WINDOW_STATE_FILE)) {
      const data = fs.readFileSync(WINDOW_STATE_FILE, 'utf-8');
      try {
        const state = JSON.parse(data);
        // 验证状态数据有效性
        if (state && typeof state.width === 'number' && typeof state.height === 'number') {
          return state;
        }
      } catch (parseErr) {
        console.warn('[WARN] 窗口状态文件格式错误:', parseErr.message);
        // 删除损坏的文件
        try {
          fs.unlinkSync(WINDOW_STATE_FILE);
        } catch {
          // 忽略删除错误
        }
      }
    }
  } catch (err) {
    console.warn('[WARN] 加载窗口状态失败:', err.message);
  }
  // 返回默认值
  return {
    width: DEFAULT_WINDOW_SIZE.width,
    height: DEFAULT_WINDOW_SIZE.height,
  };
}

/**
 * 保存窗口状态
 * @param {BrowserWindow} window - Electron 窗口实例
 */
function saveWindowState(window) {
  if (!window || window.isDestroyed()) return;

  try {
    // 确保目录存在
    const dir = path.dirname(WINDOW_STATE_FILE);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const bounds = window.getBounds();
    const state = {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
      isMaximized: window.isMaximized(),
    };

    fs.writeFileSync(WINDOW_STATE_FILE, JSON.stringify(state, null, 2), 'utf-8');
  } catch (err) {
    console.warn('[WARN] 保存窗口状态失败:', err.message);
  }
}

/**
 * 获取窗口状态文件路径
 * @returns {string}
 */
function getWindowStateFile() {
  return WINDOW_STATE_FILE;
}

module.exports = {
  loadWindowState,
  saveWindowState,
  getWindowStateFile,
};
