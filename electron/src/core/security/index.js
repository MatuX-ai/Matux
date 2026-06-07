/**
 * 安全模块统一导出
 * @module security
 *
 * 提供 URL 白名单验证和路径安全验证功能
 */

const {
  UrlWhitelist,
  getUrlWhitelist,
  validateExternalUrl,
  ALLOWED_PROTOCOLS,
  DEFAULT_WHITELIST,
  BLOCKED_DOMAINS,
} = require('./url-whitelist');

const {
  PathValidator,
  getPathValidator,
  validateFilePath,
  DEFAULT_ALLOWED_BASES,
  DANGEROUS_PATTERNS,
} = require('./path-validator');

/**
 * 安全验证管理器
 * 统一管理所有安全验证功能
 */
class SecurityManager {
  constructor(options = {}) {
    this.urlWhitelist = new UrlWhitelist(options.urlWhitelist);
    this.pathValidator = new PathValidator(options.pathValidator);
  }

  /**
   * 验证外部 URL
   * @param {string} url URL 字符串
   * @returns {{ valid: boolean, error?: string }}
   */
  validateUrl(url) {
    return this.urlWhitelist.validate(url);
  }

  /**
   * 验证文件路径
   * @param {string} filePath 文件路径
   * @param {object} options 验证选项
   * @returns {{ valid: boolean, error?: string }}
   */
  validatePath(filePath, options = {}) {
    return this.pathValidator.validate(filePath, options);
  }

  /**
   * 验证文件读取
   * @param {string} filePath 文件路径
   * @returns {{ valid: boolean, error?: string }}
   */
  validateRead(filePath) {
    return this.pathValidator.validateRead(filePath);
  }

  /**
   * 验证文件写入
   * @param {string} filePath 文件路径
   * @returns {{ valid: boolean, error?: string }}
   */
  validateWrite(filePath) {
    return this.pathValidator.validateWrite(filePath);
  }

  /**
   * 添加 URL 到白名单
   * @param {string} domain 域名
   */
  addWhitelistDomain(domain) {
    this.urlWhitelist.add(domain);
  }

  /**
   * 添加允许的基础路径
   * @param {string} basePath 基础路径
   */
  addAllowedBasePath(basePath) {
    this.pathValidator.addAllowedBase(basePath);
  }
}

// 单例
let securityManager = null;

/**
 * 获取安全管理器单例
 * @param {object} options 配置选项
 * @returns {SecurityManager}
 */
function getSecurityManager(options = {}) {
  if (!securityManager) {
    securityManager = new SecurityManager(options);
  }
  return securityManager;
}

module.exports = {
  // URL 白名单
  UrlWhitelist,
  getUrlWhitelist,
  validateExternalUrl,
  ALLOWED_PROTOCOLS,
  DEFAULT_WHITELIST,
  BLOCKED_DOMAINS,

  // 路径验证
  PathValidator,
  getPathValidator,
  validateFilePath,
  DEFAULT_ALLOWED_BASES,
  DANGEROUS_PATTERNS,

  // 统一管理器
  SecurityManager,
  getSecurityManager,
};
