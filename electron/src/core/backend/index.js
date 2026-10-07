/**
 * 后端核心模块聚合入口
 * @module backend
 *
 * 将后端相关的 Python 检测、端口管理、健康检查、后端生命周期管理
 * 统一导出，供 main.js 和其他模块按需引用，避免散落在多处。
 *
 * - detectPython / checkPythonDeps -> utils/python-detector.js
 * - checkPortOccupation / forceKillPortProcess -> ./port-manager.js
 * - healthCheck -> ./health.js
 * - BackendManager -> services/backend-manager.js
 */

const {
  detectPython,
  validatePythonAtPath,
  checkPythonDeps,
  installPythonDeps,
  loadDepsCache,
  saveDepsCache,
  clearDepsCache,
} = require('../../../utils/python-detector');

const {
  checkPortOccupation,
  checkPortOccupationAsync,
  isPortListening,
  forceKillPortProcess,
  cleanupMatuXProcesses,
  findAvailablePort,
  probeBackendHealth,
} = require('./port-manager');

const { healthCheck, httpGet } = require('./health');

const { BackendManager, HealthChecker } = require('../../../services/backend-manager');

module.exports = {
  // Python 环境探测
  detectPython,
  validatePythonAtPath,
  checkPythonDeps,
  installPythonDeps,
  loadDepsCache,
  saveDepsCache,
  clearDepsCache,

  // 端口管理
  checkPortOccupation,
  checkPortOccupationAsync,
  isPortListening,
  forceKillPortProcess,
  cleanupMatuXProcesses,
  findAvailablePort,
  probeBackendHealth,

  // 健康检查
  healthCheck,
  httpGet,

  // 后端生命周期管理
  BackendManager,
  HealthChecker,
};
