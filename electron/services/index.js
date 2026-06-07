/**
 * MatuX Electron 服务层统一导出
 * 
 * 【重构】BackendManager 已提升至 src/core/backend/，此处为向后兼容导出
 */

// 【重构】从 src/core/backend 统一导入
const backendCore = require('../src/core/backend');
const { BackendManager, HealthChecker } = backendCore;

// 健康检查服务
const { HealthCheckService, preloadTier1Modules } = require('./health-checker');

module.exports = {
  // 后端管理（从 src/core/backend 统一导出）
  BackendManager,
  HealthChecker,
  
  // 【废弃】保留旧路径导出以维持向后兼容
  // @deprecated 请使用 src/core/backend/index.js
  getBackendManager: () => BackendManager,
  
  // 健康检查服务
  HealthCheckService,
  
  // 模块预加载
  preloadTier1Modules,
};
