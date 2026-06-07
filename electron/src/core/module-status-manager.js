/**
 * 模块状态管理器
 * 负责后端模块状态的预加载、轮询和托盘状态更新
 */

let moduleStatusTimer = null;
let moduleStatusCache = null;
let backendOverallStatus = 'unknown';

// 配置常量
const MODULE_STATUS_INTERVAL = 30000; // 30秒轮询一次
const TIER1_PRELOAD_TIMEOUT = 5000;   // 5秒超时

// 依赖注入（由 main.js 设置）
let deps = {
  mainWindow: null,
  tray: null,
  backendManager: null,
  APP_PATHS: {},
  BACKEND_PORT: 8000,
  sendSplashStatus: () => {},
  showNotification: () => {},
  checkForUpdates: () => {},
  onStatusChange: null,
};

/**
 * 设置依赖
 */
function setDependencies(newDeps) {
  deps = { ...deps, ...newDeps };
}

/**
 * 获取模块状态缓存
 */
function getModuleStatusCache() {
  return moduleStatusCache;
}

/**
 * 获取后端整体状态
 */
function getBackendOverallStatus() {
  return backendOverallStatus;
}

// ==================== 模块状态轮询 ====================

/**
 * 轮询模块状态并推送到渲染进程
 */
async function pollModuleStatus() {
  const MODULES_URL = `http://127.0.0.1:${deps.BACKEND_PORT}/api/v1/modules`;
  const HEALTH_DETAIL_URL = `http://127.0.0.1:${deps.BACKEND_PORT}/api/v1/health/detail`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), MODULE_STATUS_INTERVAL);
    const response = await fetch(HEALTH_DETAIL_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) return;

    const data = await response.json();
    const previousStatus = backendOverallStatus;
    backendOverallStatus = data.status || 'unknown';
    moduleStatusCache = data.modules || null;

    // 推送到渲染进程
    if (deps.mainWindow && !deps.mainWindow.isDestroyed()) {
      deps.mainWindow.webContents.send('backend:module-status', moduleStatusCache);
    }

    // 更新托盘状态
    updateTrayStatus();

    // 状态变化时通知前端
    if (previousStatus !== backendOverallStatus && deps.mainWindow && !deps.mainWindow.isDestroyed()) {
      deps.mainWindow.webContents.send('app-event', {
        type: 'backend-status-change',
        status: backendOverallStatus,
        previousStatus,
      });
      if (deps.onStatusChange) {
        deps.onStatusChange(backendOverallStatus, previousStatus);
      }
    }
  } catch (err) {
    // 静默失败
  }
}

/**
 * 后台预加载 Tier 1 模块（分阶段启动 Phase 2：不阻塞 UI）
 */
async function preloadTier1Modules() {
  const MODULES_URL = `http://127.0.0.1:${deps.BACKEND_PORT}/api/v1/modules`;

  // 等待 1 秒让 Tier 0 稳定
  await new Promise((r) => setTimeout(r, 1000));

  console.log('[INFO] 开始后台预加载 Tier 1 模块...');

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIER1_PRELOAD_TIMEOUT);
    const response = await fetch(MODULES_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('[WARN] 获取模块状态失败:', response.status);
      return;
    }

    const data = await response.json();
    const summary = data.summary || {};
    const modules = data.modules || [];

    console.log(
      `[INFO] 模块状态: ${summary.active}/${summary.total} 已激活, ` +
      `${summary.degraded || 0} 降级, ${summary.failed || 0} 失败`
    );

    // 发送模块进度到 Splash
    if (deps.sendSplashStatus) {
      deps.sendSplashStatus('modules', `模块加载中 (${summary.active}/${summary.total})...`,
        Math.round((summary.active / Math.max(summary.total, 1)) * 100),
        null, modules);
    }

    // 通知渲染进程模块状态
    if (deps.mainWindow && !deps.mainWindow.isDestroyed()) {
      deps.mainWindow.webContents.send('backend:module-status', data);
    }

    // 缓存初始状态
    moduleStatusCache = data;
  } catch (err) {
    console.warn('[WARN] Tier 1 预加载检查失败:', err.message);
  }
}

/**
 * 开始模块状态轮询
 */
function startModuleStatusPolling() {
  if (moduleStatusTimer) clearInterval(moduleStatusTimer);
  moduleStatusTimer = setInterval(pollModuleStatus, MODULE_STATUS_INTERVAL);
  // 立即执行一次
  pollModuleStatus();
}

/**
 * 停止模块状态轮询
 */
function stopModuleStatusPolling() {
  if (moduleStatusTimer) {
    clearInterval(moduleStatusTimer);
    moduleStatusTimer = null;
  }
}

// ==================== 托盘状态更新 ====================

/**
 * 更新系统托盘图标和菜单（反映后端状态）
 */
function updateTrayStatus() {
  if (!deps.tray) return;

  let statusLabel = '';
  let statusEmoji = '';

  switch (backendOverallStatus) {
    case 'healthy':
      statusLabel = '所有服务正常';
      statusEmoji = '🟢';
      break;
    case 'degraded':
      statusLabel = '部分模块降级运行';
      statusEmoji = '🟡';
      break;
    case 'unhealthy':
      statusLabel = '核心服务异常';
      statusEmoji = '🔴';
      break;
    default:
      statusLabel = '状态未知';
      statusEmoji = '⚪';
  }

  deps.tray.setToolTip(`MatuX - ${statusLabel}`);

  // 构建模块摘要菜单项
  const moduleItems = [];
  if (moduleStatusCache && moduleStatusCache.summary) {
    const s = moduleStatusCache.summary;
    moduleItems.push({
      label: `模块: ${s.active}/${s.total} 活跃`,
      enabled: false,
    });
    if (s.degraded > 0) {
      moduleItems.push({ label: `${s.degraded} 个模块降级`, enabled: false });
    }
    if (s.failed > 0) {
      moduleItems.push({ label: `${s.failed} 个模块失败`, enabled: false });
    }
  }

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        if (deps.mainWindow && !deps.mainWindow.isDestroyed()) {
          deps.mainWindow.show();
          deps.mainWindow.focus();
        }
      },
    },
    { type: 'separator' },
    {
      label: `${statusEmoji} ${statusLabel}`,
      enabled: false,
    },
    ...moduleItems,
    { type: 'separator' },
    {
      label: '重启后端',
      click: () => {
        if (deps.backendManager) {
          deps.backendManager.restartBackend({
            backendDir: deps.APP_PATHS.backendDir,
            backendPort: deps.BACKEND_PORT,
          });
        }
      },
    },
    {
      label: '学习提醒',
      click: () => {
        if (deps.showNotification) {
          deps.showNotification('学习提醒', '该继续今天的学习啦！坚持就是胜利 💪');
        }
      },
    },
    { type: 'separator' },
    {
      label: '检查更新',
      click: () => {
        if (deps.checkForUpdates) {
          deps.checkForUpdates();
        }
      },
    },
    { type: 'separator' },
    {
      label: '退出 MatuX',
      click: () => {
        app.quit();
      },
    },
  ]);

  deps.tray.setContextMenu(contextMenu);
}

// ==================== IPC Handler 注册 ====================

/**
 * 注册模块状态相关的 IPC handlers
 */
function registerModuleStatusIpcHandlers(ipcMain) {
  // 获取模块状态
  ipcMain.handle('module:get-status', () => {
    return {
      overall: backendOverallStatus,
      modules: moduleStatusCache,
    };
  });

  // 手动刷新模块状态
  ipcMain.handle('module:refresh', async () => {
    await pollModuleStatus();
    return {
      overall: backendOverallStatus,
      modules: moduleStatusCache,
    };
  });
}

module.exports = {
  // 初始化
  setDependencies,

  // 状态获取
  getModuleStatusCache,
  getBackendOverallStatus,

  // 生命周期管理
  preloadTier1Modules,
  startModuleStatusPolling,
  stopModuleStatusPolling,

  // 托盘更新
  updateTrayStatus,

  // IPC 注册
  registerModuleStatusIpcHandlers,
};
