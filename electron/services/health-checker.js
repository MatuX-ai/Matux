/**
 * MatuX Electron 健康检查服务
 * 
 * 负责周期性健康检查、模块状态轮询和状态上报
 */

const http = require('http');
const {
  BACKEND_HOST,
  BACKEND_PORT,
  HEALTH_CHECK_INTERVAL,
  MODULE_STATUS_INTERVAL,
  HEALTH_CHECK_DETAIL_INTERVAL,
  HEALTH_DETAIL_URL,
  MODULES_URL,
} = require('../config/constants');

class HealthCheckService {
  /**
   * @param {object} options 配置选项
   * @param {function} options.onBackendDown 后端断开回调
   * @param {function} options.onModuleStatusChange 模块状态变化回调
   * @param {function} options.onOverallStatusChange 整体状态变化回调
   */
  constructor(options = {}) {
    this.healthTimer = null;
    this.moduleTimer = null;
    this.isQuitting = false;
    
    // 状态缓存
    this.moduleStatusCache = null;
    this.overallStatus = 'unknown';
    this.previousStatus = 'unknown';
    
    // 回调
    this.onBackendDown = options.onBackendDown || (() => {});
    this.onModuleStatusChange = options.onModuleStatusChange || (() => {});
    this.onOverallStatusChange = options.onOverallStatusChange || (() => {});
    
    // 健康检查器（用于单次检查）
    this.healthChecker = null;
  }

  /**
   * 启动健康检查（周期性）
   */
  startHealthCheck() {
    if (this.healthTimer) return;

    console.log('[INFO] 启动健康检查...');
    
    this.healthTimer = setInterval(async () => {
      if (this.isQuitting) return;
      
      const result = await this.checkBackendHealth();
      if (!result.success) {
        console.warn('[WARN] 健康检查失败，后端可能已崩溃');
        this.onBackendDown();
      }
    }, HEALTH_CHECK_INTERVAL);
  }

  /**
   * 停止健康检查
   */
  stopHealthCheck() {
    if (this.healthTimer) {
      clearInterval(this.healthTimer);
      this.healthTimer = null;
    }
  }

  /**
   * 启动模块状态轮询
   */
  startModuleStatusPolling() {
    if (this.moduleTimer) return;

    console.log('[INFO] 启动模块状态轮询...');
    
    this.moduleTimer = setInterval(async () => {
      await this.pollModuleStatus();
    }, MODULE_STATUS_INTERVAL);
    
    // 立即执行一次
    this.pollModuleStatus();
  }

  /**
   * 停止模块状态轮询
   */
  stopModuleStatusPolling() {
    if (this.moduleTimer) {
      clearInterval(this.moduleTimer);
      this.moduleTimer = null;
    }
  }

  /**
   * 执行一次后端健康检查
   */
  async checkBackendHealth() {
    const urls = [
      `http://${BACKEND_HOST}:${BACKEND_PORT}/health`,
      `http://${BACKEND_HOST}:${BACKEND_PORT}/`,
    ];

    for (const url of urls) {
      const result = await this.httpGet(url, 5000);
      if (result.success && result.statusCode) {
        return { success: true, statusCode: result.statusCode };
      }
    }

    return { success: false };
  }

  /**
   * 轮询模块状态
   */
  async pollModuleStatus() {
    try {
      const result = await this.httpGet(HEALTH_DETAIL_URL, HEALTH_CHECK_DETAIL_INTERVAL);
      
      if (!result.success) return;

      let data;
      try {
        data = JSON.parse(result.body);
      } catch {
        return;
      }

      const previousStatus = this.overallStatus;
      this.overallStatus = data.status || 'unknown';
      this.moduleStatusCache = data.modules || null;

      // 通知状态变化
      this.onModuleStatusChange(this.moduleStatusCache);

      // 整体状态变化时通知
      if (previousStatus !== this.overallStatus) {
        this.onOverallStatusChange(this.overallStatus, previousStatus);
      }
    } catch (err) {
      // 静默失败
    }
  }

  /**
   * 获取模块状态缓存
   */
  getModuleStatusCache() {
    return this.moduleStatusCache;
  }

  /**
   * 获取当前整体状态
   */
  getOverallStatus() {
    return this.overallStatus;
  }

  /**
   * HTTP GET 请求
   */
  httpGet(url, timeout) {
    return new Promise((resolve) => {
      try {
        const urlObj = new URL(url);
        let hostname = urlObj.hostname;
        if (hostname === 'localhost') hostname = '127.0.0.1';

        const req = http.request({
          hostname,
          port: urlObj.port || 80,
          path: urlObj.pathname + urlObj.search,
          method: 'GET',
          timeout,
        }, (res) => {
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
            resolve({ success: true, statusCode: res.statusCode, body });
          });
        });

        req.on('error', (err) => resolve({ success: false, error: err.message }));
        req.on('timeout', () => { req.destroy(); resolve({ success: false, error: '超时' }); });
        req.end();
      } catch (err) {
        resolve({ success: false, error: err.message });
      }
    });
  }

  /**
   * 停止所有轮询
   */
  stop() {
    this.stopHealthCheck();
    this.stopModuleStatusPolling();
  }

  /**
   * 设置退出状态
   */
  setQuitting(quitting) {
    this.isQuitting = quitting;
    if (quitting) {
      this.stop();
    }
  }
}

/**
 * 预加载 Tier 1 模块
 */
async function preloadTier1Modules(splashReporter) {
  // 等待 1 秒让 Tier 0 稳定
  await new Promise((r) => setTimeout(r, 1000));

  console.log('[INFO] 开始后台预加载 Tier 1 模块...');

  try {
    const urlObj = new URL(MODULES_URL);
    let hostname = urlObj.hostname;
    if (hostname === 'localhost') hostname = '127.0.0.1';

    const response = await fetch(MODULES_URL);
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
    splashReporter?.('modules', `模块加载中 (${summary.active}/${summary.total})...`,
      Math.round((summary.active / Math.max(summary.total, 1)) * 100),
      null, modules);

    return { summary, modules };
  } catch (err) {
    console.warn('[WARN] Tier 1 预加载检查失败:', err.message);
    return null;
  }
}

module.exports = {
  HealthCheckService,
  preloadTier1Modules,
};
