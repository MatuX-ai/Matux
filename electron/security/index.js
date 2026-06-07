/**
 * MatuX Electron 安全验证模块
 *
 * 统一管理路径验证、URL 白名单等安全检查
 *
 * 【重构】现在转发到 src/core/security/，保留向后兼容
 */

const path = require('path');
const { app } = require('electron');
const { APP_PATHS } = require('../config/constants');

// 【重构】使用新模块
const securityCore = require('../src/core/security');

/**
 * 验证URL是否在白名单内
 * @param {string} url 要验证的URL
 * @returns {{ valid: boolean, error?: string }}
 */
function validateExternalUrl(url) {
  // 【重构】使用新的 url-whitelist 模块
  return securityCore.validateExternalUrl(url);
}

/**
 * 获取允许访问的根目录列表
 */
function getAllowedPaths() {
  const userData = app.getPath('userData');
  const backendDir = APP_PATHS.backendDir;
  return [
    userData,
    backendDir,
    path.join(userData, 'plugins'),
    path.join(userData, 'projects'),
    path.join(userData, 'downloads'),
  ];
}

/**
 * 验证路径是否在允许访问的目录内（防止路径穿越攻击）
 * @param {string} targetPath 要验证的路径
 * @returns {{ valid: boolean, error?: string }}
 */
function validateFilePath(targetPath) {
  // 【重构】使用新的 path-validator 模块
  const result = securityCore.validateFilePath(targetPath);

  // 如果新模块验证通过，还需要检查是否在允许的根目录内
  if (result.valid) {
    const normalizedPath = path.normalize(targetPath);
    const allowedRoots = getAllowedPaths();
    const isAllowed = allowedRoots.some(root => {
      const normalizedRoot = path.normalize(root);
      return normalizedPath.startsWith(normalizedRoot) || normalizedPath === normalizedRoot;
    });

    if (!isAllowed) {
      return { valid: false, error: '路径超出允许访问范围' };
    }
  }

  return result;
}

module.exports = {
  validateExternalUrl,
  validateFilePath,
  getAllowedPaths,
};
