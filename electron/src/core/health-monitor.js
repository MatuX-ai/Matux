/**
 * MatuX Electron 健康监控模块
 *
 * 负责后端健康检查和模块状态轮询
 *
 * @module core/health-monitor
 */

const http = require('http');

/**
 * 创建健康监控器
 * @param {object} options 配置选项
 * @param {function} options.getMainWindow 获取主窗口的函数
 * @param {function} options.getBackendUrl 获取后端 URL 的函数
 * @param {object} options.config 配置对象
 * @returns {object} HealthMonitor 实例
 */
function createHealthMonitor(options = {}) {
  const {
    getMainWindow = () => null,
    getBackendUrl = () => 'http://localhost:8000',
    config = {},
  } = options;

  const {
    HEALTH_CHECK_INTERVAL = 30000,
    MODULE_STATUS_INTERVAL = 10000,
    HTTP_REQUEST_TIMEOUT = 5000,
    HEALTH_CHECK_DETAIL_INTERVAL = 5000,
  } = config;

  let healthCheckTimer = null;
  let moduleStatusTimer = null;
  let backendOverallStatus = 'unknown';
  let moduleStatusCache = null;
  let isQuitting = false;

  // 回调函数
  let onStatusChange = null;
  let onModuleStatusChange = null;
  let onBackendDisconnected = null;

  /**
   * 获取主窗口
   */
  function getMainWin() {
    return getMainWindow();
  }

  /**
   * 发送消息到主窗口
   */
  function sendToRenderer(channel, data) {
    const mainWin = getMainWin();
    if (mainWin && !mainWin.isDestroyed()) {
      mainWin.webContents.send(channel, data);
    }
  }

  /**
   * 健康检查
   */
  async function healthCheck() {
    const url = getBackendUrl();
    const healthUrl = `${url}/health`;

    return new Promise((resolve) => {
      try {
        const req = http.get(healthUrl, { timeout: HTTP_REQUEST_TIMEOUT }, (res) => {
          let data = '';
          res.on('data', (chunk) => {
            data += chunk;
          });
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              resolve({ success: true, data: json });
            } catch {
              resolve({ success: true });
            }
          });
        });

        req.on('error', (err) => {
          resolve({ success: false, error: err.message });
        });

        req.on('timeout', () => {
          req.destroy();
          resolve({ success: false, error: '请求超时' });
        });
      } catch (err) {
        resolve({ success: false, error: err.message });
      }
    });
  }

  /**
   * 获取模块状态详情
   */
  async function pollModuleStatus() {
    const url = getBackendUrl();
    const healthDetailUrl = `${url}/health/detail`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_DETAIL_INTERVAL);

      const response = await fetch(healthDetailUrl, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!response.ok) return;

      const data = await response.json();
      const previousStatus = backendOverallStatus;
      backendOverallStatus = data.status || 'unknown';
      moduleStatusCache = data.modules || null;

      // 推送到渲染进程
      sendToRenderer('backend:module-status', moduleStatusCache);

      // 回调通知
      if (onModuleStatusChange) {
        onModuleStatusChange(backendOverallStatus, moduleStatusCache);
      }

      // 状态变化时通知前端
      if (previousStatus !== backendOverallStatus) {
        sendToRenderer('app-event', {
          type: 'backend-status-change',
          status: backendOverallStatus,
          previousStatus,
        });

        if (onStatusChange) {
          onStatusChange(backendOverallStatus, previousStatus);
        }
      }
    } catch (err) {
      // 忽略轮询错误
    }
  }

  /**
   * 启动健康检查
   */
  function startHealthCheck() {
    if (healthCheckTimer) clearInterval(healthCheckTimer);

    healthCheckTimer = setInterval(async () => {
      const result = await healthCheck();
      if (!result.success && !isQuitting) {
        console.warn('[WARN] 健康检查失败，后端可能已崩溃');
        sendToRenderer('app-event', { type: 'backend-disconnected' });

        if (onBackendDisconnected) {
          onBackendDisconnected(result.error);
        }
      }
    }, HEALTH_CHECK_INTERVAL);
  }

  /**
   * 停止健康检查
   */
  function stopHealthCheck() {
    if (healthCheckTimer) {
      clearInterval(healthCheckTimer);
      healthCheckTimer = null;
    }
  }

  /**
   * 启动模块状态轮询
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

  /**
   * 停止所有监控
   */
  function stopAll() {
    stopHealthCheck();
    stopModuleStatusPolling();
  }

  /**
   * 设置退出状态
   */
  function setQuitting(value) {
    isQuitting = value;
  }

  /**
   * 获取后端整体状态
   */
  function getOverallStatus() {
    return backendOverallStatus;
  }

  /**
   * 获取模块状态缓存
   */
  function getModuleStatusCache() {
    return moduleStatusCache;
  }

  /**
   * 获取模块摘要
   */
  function getModuleSummary() {
    if (!moduleStatusCache || !moduleStatusCache.summary) {
      return null;
    }
    return moduleStatusCache.summary;
  }

  /**
   * 设置回调函数
   */
  function setCallbacks(callbacks = {}) {
    if (callbacks.onStatusChange) onStatusChange = callbacks.onStatusChange;
    if (callbacks.onModuleStatusChange) onModuleStatusChange = callbacks.onModuleStatusChange;
    if (callbacks.onBackendDisconnected) onBackendDisconnected = callbacks.onBackendDisconnected;
  }

  return {
    // 生命周期
    healthCheck,
    startHealthCheck,
    stopHealthCheck,
    startModuleStatusPolling,
    stopModuleStatusPolling,
    stopAll,
    setQuitting,

    // 状态查询
    getOverallStatus,
    getModuleStatusCache,
    getModuleSummary,

    // 回调设置
    setCallbacks,
  };
}

module.exports = { createHealthMonitor };
