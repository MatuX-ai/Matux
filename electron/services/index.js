/**
 * MatuX Electron 服务层统一导出
 * 
 * 【重构】BackendManager 已提升至 src/core/backend/，此处为向后兼容导出
 */

// 【重构】从 src/core/backend 统一导入
const backendCore = require('../src/core/backend');

// 验证导出
const validExports = ['BackendManager', 'HealthChecker', 'HealthCheckService', 'preloadTier1Modules'];

// 统一导出所有功能
const exports = {
  // 后端管理（从 src/core/backend 统一导出）
  BackendManager: backendCore.BackendManager,
  HealthChecker: backendCore.HealthChecker,
  
  // 【废弃】保留旧路径导出以维持向后兼容
  // @deprecated 请使用 src/core/backend/index.js
  getBackendManager: () => backendCore.BackendManager,
};

// 健康检查服务
const healthCheckModule = require('./health-checker');
if (healthCheckModule.HealthCheckService) {
  exports.HealthCheckService = healthCheckModule.HealthCheckService;
}
if (healthCheckModule.preloadTier1Modules) {
  exports.preloadTier1Modules = healthCheckModule.preloadTier1Modules;
}

// 文件解析服务
const fileParserModule = require('./file-parser');
exports.fileParser = fileParserModule;

// 验证必要的导出存在
if (!exports.BackendManager) {
  console.warn('[WARN] BackendManager 导出缺失，请检查 backend-manager.js');
}

module.exports = exports;
