/**
 * 启动模块统一导出
 * @module startup
 */

const { AppInitializer } = require('./app-initializer');
const { checkPythonEnvironment, verifyBackendHealth } = require('./python-checker');

module.exports = {
  AppInitializer,
  checkPythonEnvironment,
  verifyBackendHealth,
};
