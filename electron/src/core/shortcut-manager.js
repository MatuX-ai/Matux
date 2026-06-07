/**
 * MatuX Electron 全局快捷键管理器
 *
 * 负责注册和管理全局快捷键
 *
 * @module core/shortcut-manager
 */

const { globalShortcut } = require('electron');

/**
 * 创建快捷键管理器
 * @param {object} options 配置选项
 * @param {function} options.getMainWindow 获取主窗口的函数
 * @returns {object} ShortcutManager 实例
 */
function createShortcutManager(options = {}) {
  const { getMainWindow = () => null } = options;

  /**
   * 获取主窗口
   */
  function getMainWin() {
    return getMainWindow();
  }

  /**
   * 检查主窗口是否可用
   */
  function isMainWindowReady() {
    const win = getMainWin();
    return win && !win.isDestroyed() && win.isVisible();
  }

  /**
   * 注册所有全局快捷键
   * @returns {object} 注册结果 { success: boolean, message: string }
   */
  function registerAll() {
    const results = [];

    // Ctrl+Shift+M → 显示/隐藏 MatuX
    const retCtrlM = globalShortcut.register('CommandOrControl+Shift+M', () => {
      const mainWin = getMainWin();
      if (!mainWin || mainWin.isDestroyed()) return;

      if (mainWin.isVisible()) {
        mainWin.hide();
      } else {
        mainWin.show();
        mainWin.focus();
      }
    });

    if (!retCtrlM) {
      results.push({ shortcut: 'Ctrl+Shift+M', success: false, reason: '可能被占用' });
    } else {
      results.push({ shortcut: 'Ctrl+Shift+M', success: true });
    }

    // Ctrl+K → 全局命令面板
    const retCtrlK = globalShortcut.register('CommandOrControl+K', () => {
      if (!isMainWindowReady()) return;
      getMainWin().webContents.send('shortcut', 'command-palette');
    });

    if (!retCtrlK) {
      results.push({ shortcut: 'Ctrl+K', success: false, reason: '可能被占用' });
    } else {
      results.push({ shortcut: 'Ctrl+K', success: true });
    }

    // Ctrl+N → 新建项目
    const retCtrlN = globalShortcut.register('CommandOrControl+N', () => {
      if (!isMainWindowReady()) return;
      getMainWin().webContents.send('shortcut', 'new-project');
    });

    if (!retCtrlN) {
      results.push({ shortcut: 'Ctrl+N', success: false, reason: '可能被占用' });
    } else {
      results.push({ shortcut: 'Ctrl+N', success: true });
    }

    // 统计注册结果
    const failed = results.filter((r) => !r.success);
    if (failed.length > 0) {
      console.warn('[WARN] 部分快捷键注册失败:', failed.map((f) => f.shortcut).join(', '));
    }

    console.log('[INFO] 快捷键注册完成:', results.filter((r) => r.success).map((r) => r.shortcut).join(', '));

    return {
      success: failed.length === 0,
      results,
      failed,
    };
  }

  /**
   * 注销所有全局快捷键
   */
  function unregisterAll() {
    globalShortcut.unregisterAll();
    console.log('[INFO] 已注销所有全局快捷键');
  }

  /**
   * 检查快捷键是否已注册
   * @param {string} accelerator 快捷键字符串
   */
  function isRegistered(accelerator) {
    return globalShortcut.isRegistered(accelerator);
  }

  /**
   * 注销特定快捷键
   * @param {string} accelerator 快捷键字符串
   */
  function unregister(accelerator) {
    globalShortcut.unregister(accelerator);
  }

  /**
   * 注册单个快捷键
   * @param {string} accelerator 快捷键字符串
   * @param {function} callback 回调函数
   */
  function register(accelerator, callback) {
    return globalShortcut.register(accelerator, callback);
  }

  return {
    registerAll,
    unregisterAll,
    isRegistered,
    unregister,
    register,
  };
}

module.exports = { createShortcutManager };
