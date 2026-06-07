/**
 * 全局快捷键管理模块
 * @module shortcuts
 *
 * 负责注册和管理全局快捷键
 */

const { globalShortcut } = require('electron');

/**
 * 注册全局快捷键
 * @param {Object} options - 配置选项
 * @param {BrowserWindow|null} options.mainWindow - 主窗口引用
 * @param {Function} options.onRestartBackend - 重启后端回调
 * @param {Function} options.onShowNotification - 显示通知回调
 */
function registerGlobalShortcuts({ mainWindow, onRestartBackend, onShowNotification }) {
  // Ctrl+Shift+M → 显示/隐藏 MatuX
  const retCtrlM = globalShortcut.register('CommandOrControl+Shift+M', () => {
    if (!mainWindow || mainWindow.isDestroyed()) return;

    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  if (!retCtrlM) {
    console.warn('[WARN] 全局快捷键 Ctrl+Shift+M 注册失败（可能被占用）');
  } else {
    console.log('[INFO] 全局快捷键 Ctrl+Shift+M 已注册（显示/隐藏窗口）');
  }

  // Ctrl+K → 全局命令面板
  const retCtrlK = globalShortcut.register('CommandOrControl+K', () => {
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.isVisible()) {
      mainWindow.webContents.send('shortcut', 'command-palette');
    }
  });
  if (!retCtrlK) {
    console.warn('[WARN] 全局快捷键 Ctrl+K 注册失败（可能被占用）');
  }

  // Ctrl+N → 新建项目
  const retCtrlN = globalShortcut.register('CommandOrControl+N', () => {
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.isVisible()) {
      mainWindow.webContents.send('shortcut', 'new-project');
    }
  });
  if (!retCtrlN) {
    console.warn('[WARN] 全局快捷键 Ctrl+N 注册失败（可能被占用）');
  }

  console.log('[INFO] 快捷键 Ctrl+K（命令面板）、Ctrl+N（新建项目）注册完成');
}

/**
 * 注销所有全局快捷键
 */
function unregisterGlobalShortcuts() {
  globalShortcut.unregisterAll();
}

module.exports = {
  registerGlobalShortcuts,
  unregisterGlobalShortcuts,
};
