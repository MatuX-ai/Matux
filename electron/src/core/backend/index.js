/**
 * 后端管理模块 - 统一导出
 * @module backend
 *
 * 提供完整的后端服务管理功能：
 * - Python 环境检测
 * - 端口占用管理
 * - 后端进程启动/停止（BackendManager 类）
 * - 健康检查
 */

// 底层工具模块
const detector = require('./detector');
const portManager = require('./port-manager');
const health = require('./health');

// 【重构】后端管理器类（从 services 层导入）
// 这样做的好处：
// 1. 将 BackendManager 放在更规范的位置 (src/core/backend)
// 2. 保持与 services/index.js 的向后兼容
// 3. 统一后端管理的入口点
// 
// 注意：此模块与 services/backend-manager.js 存在循环依赖风险
// 为避免此问题，BackendManager 直接在 services/backend-manager.js 中实现
// 此 index.js 仅负责导出
let BackendManager = null;
let HealthChecker = null;
try {
  // 从 services/backend-manager 导入（避免循环依赖）
  const { BackendManager: BM, HealthChecker: HC } = require('../../../services/backend-manager');
  BackendManager = BM;
  HealthChecker = HC;
} catch (err) {
  console.warn('[WARN] 无法导入 BackendManager:', err.message);
}

// 统一导出所有功能
module.exports = {
  // ========== Python 环境检测 ==========
  isPythonVersionGte39: detector.isPythonVersionGte39,
  searchPythonPaths: detector.searchPythonPaths,
  detectPython: detector.detectPython,
  checkPythonDeps: detector.checkPythonDeps,

  // ========== 端口管理 ==========
  checkPortOccupation: portManager.checkPortOccupation,
  forceKillPortProcess: portManager.forceKillPortProcess,
  cleanupMatuXProcesses: portManager.cleanupMatuXProcesses,

  // ========== 健康检查 ==========
  httpGet: health.httpGet,
  healthCheck: health.healthCheck,

  // ========== 后端进程管理类 ==========
  BackendManager,
  HealthChecker,

  // ========== 配置常量 ==========
  DEFAULT_BACKEND_PORT: 8000,
  DEFAULT_BACKEND_HOST: 'localhost',
  DEFAULT_BACKEND_START_TIMEOUT: 60000,
  MAX_RESTART_ATTEMPTS: 3,
  BACKEND_RESTART_DELAY: 3000,
};
