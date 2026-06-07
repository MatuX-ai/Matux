/**
 * 应用生命周期管理模块
 * @module lifecycle
 *
 * 统一管理 Electron 应用的启动、运行和退出阶段
 */

const { app, BrowserWindow, globalShortcut } = require('electron');

// 生命周期状态
const LIFECYCLE_STATE = {
  NOT_STARTED: 'not_started',
  INITIALIZING: 'initializing',
  READY: 'ready',
  QUITTING: 'quitting',
  QUIT: 'quit',
};

/**
 * 创建生命周期管理器
 * @param {object} options 配置选项
 * @param {function} options.onBeforeReady 应用就绪前回调
 * @param {function} options.onReady 应用就绪回调
 * @param {function} options.onActivate 应用激活回调
 * @param {function} options.onBeforeQuit 应用退出前回调
 * @param {function} options.onQuit 应用退出回调
 * @param {function} options.onWindowAllClosed 所有窗口关闭回调
 * @returns {object} 生命周期管理器
 */
function createLifecycleManager(options = {}) {
  const {
    onBeforeReady = null,
    onReady = null,
    onActivate = null,
    onBeforeQuit = null,
    onQuit = null,
    onWindowAllClosed = null,
  } = options;

  let currentState = LIFECYCLE_STATE.NOT_STARTED;
  const registeredHooks = {
    beforeReady: [],
    ready: [],
    activate: [],
    beforeQuit: [],
    quit: [],
    windowAllClosed: [],
  };

  /**
   * 获取当前状态
   * @returns {string} 当前生命周期状态
   */
  function getState() {
    return currentState;
  }

  /**
   * 检查是否处于特定状态
   * @param {string} state 状态名
   * @returns {boolean}
   */
  function isState(state) {
    return currentState === state;
  }

  /**
   * 注册生命周期钩子
   * @param {string} phase 生命周期阶段
   * @param {function} callback 回调函数
   */
  function registerHook(phase, callback) {
    if (registeredHooks[phase]) {
      registeredHooks[phase].push(callback);
    }
  }

  /**
   * 触发生命周期钩子
   * @param {string} phase 生命周期阶段
   * @param {...any} args 传递给回调的参数
   */
  async function triggerHook(phase, ...args) {
    const hooks = registeredHooks[phase] || [];
    for (const hook of hooks) {
      try {
        await hook(...args);
      } catch (err) {
        console.error(`[LIFECYCLE] Hook error in ${phase}:`, err.message);
      }
    }
  }

  /**
   * 初始化生命周期监听
   * @param {object} deps 依赖对象
   * @param {function} deps.createMainWindow 创建主窗口的函数
   * @param {function} deps.gracefulShutdown 优雅关闭函数
   */
  function initialize(deps = {}) {
    const { createMainWindow = null, gracefulShutdown = null } = deps;

    // 应用就绪前
    app.on('will-finish-launching', async () => {
      currentState = LIFECYCLE_STATE.INITIALIZING;
      console.log('[LIFECYCLE] will-finish-launching');

      if (onBeforeReady) {
        try {
          await onBeforeReady();
        } catch (err) {
          console.error('[LIFECYCLE] onBeforeReady error:', err.message);
        }
      }

      await triggerHook('beforeReady');
    });

    // 应用就绪
    app.on('ready', async () => {
      currentState = LIFECYCLE_STATE.READY;
      console.log('[LIFECYCLE] ready');

      if (onReady) {
        try {
          await onReady();
        } catch (err) {
          console.error('[LIFECYCLE] onReady error:', err.message);
        }
      }

      await triggerHook('ready');
    });

    // macOS: 应用激活
    app.on('activate', async () => {
      console.log('[LIFECYCLE] activate');

      if (onActivate) {
        try {
          await onActivate();
        } catch (err) {
          console.error('[LIFECYCLE] onActivate error:', err.message);
        }
      }

      // 如果没有窗口，创建主窗口
      if (BrowserWindow.getAllWindows().length === 0) {
        if (createMainWindow) {
          createMainWindow();
        }
      }

      await triggerHook('activate');
    });

    // 所有窗口关闭
    app.on('window-all-closed', async () => {
      console.log('[LIFECYCLE] window-all-closed');

      if (onWindowAllClosed) {
        try {
          await onWindowAllClosed();
        } catch (err) {
          console.error('[LIFECYCLE] onWindowAllClosed error:', err.message);
        }
      }

      await triggerHook('windowAllClosed');

      // 非 macOS 系统，关闭窗口后退出应用
      if (process.platform !== 'darwin') {
        if (gracefulShutdown) {
          gracefulShutdown();
        }
        app.quit();
      }
    });

    // 退出前
    app.on('before-quit', async (event) => {
      console.log('[LIFECYCLE] before-quit');
      currentState = LIFECYCLE_STATE.QUITTING;

      if (onBeforeQuit) {
        try {
          // 阻止默认退出，给回调执行时间
          event.preventDefault();
          await onBeforeQuit();
          event.preventDefault(); // 再阻止一次，确保清理完成
        } catch (err) {
          console.error('[LIFECYCLE] onBeforeQuit error:', err.message);
        }
      }

      await triggerHook('beforeQuit');
    });

    // 应用退出
    app.on('will-quit', async () => {
      console.log('[LIFECYCLE] will-quit');
      currentState = LIFECYCLE_STATE.QUIT;

      // 注销所有全局快捷键
      globalShortcut.unregisterAll();

      if (onQuit) {
        try {
          await onQuit();
        } catch (err) {
          console.error('[LIFECYCLE] onQuit error:', err.message);
        }
      }

      await triggerHook('quit');
    });
  }

  return {
    getState,
    isState,
    registerHook,
    triggerHook,
    initialize,
    LIFECYCLE_STATE,
  };
}

/**
 * 创建应用就绪事件处理器
 * @param {function} mainLogic 主逻辑函数（异步）
 * @returns {Promise<void>}
 */
async function whenReady(mainLogic) {
  if (app.isReady()) {
    await mainLogic();
  } else {
    await new Promise((resolve) => {
      app.whenReady().then(async () => {
        await mainLogic();
        resolve();
      });
    });
  }
}

/**
 * 阻止应用退出（用于清理未完成时）
 * @param {function} cleanupLogic 清理逻辑
 * @param {number} timeoutMs 超时时间（毫秒）
 * @returns {function} 返回一个函数，调用后允许退出
 */
function preventQuitUntil(cleanupLogic, timeoutMs = 10000) {
  let allowQuit = false;
  let preventTimeout = null;

  const preventQuit = (event) => {
    if (allowQuit) return;

    event.preventDefault();
    console.log('[LIFECYCLE] 阻止退出，正在清理...');

    // 设置超时
    preventTimeout = setTimeout(() => {
      console.log('[LIFECYCLE] 清理超时，强制退出');
      allowQuit = true;
      app.quit();
    }, timeoutMs);

    // 执行清理
    cleanupLogic()
      .then(() => {
        clearTimeout(preventTimeout);
        console.log('[LIFECYCLE] 清理完成，允许退出');
        allowQuit = true;
        app.quit();
      })
      .catch((err) => {
        clearTimeout(preventTimeout);
        console.error('[LIFECYCLE] 清理失败:', err.message);
        allowQuit = true;
        app.quit();
      });
  };

  app.on('before-quit', preventQuit);

  // 返回允许退出的函数
  return () => {
    app.removeListener('before-quit', preventQuit);
    clearTimeout(preventTimeout);
    allowQuit = true;
  };
}

module.exports = {
  createLifecycleManager,
  whenReady,
  preventQuitUntil,
  LIFECYCLE_STATE,
};
