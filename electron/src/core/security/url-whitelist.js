/**
 * URL 白名单验证模块
 * @module security/url-whitelist
 *
 * 用于验证外部 URL 是否在允许的白名单内
 */

// 允许的协议
const ALLOWED_PROTOCOLS = ['http:', 'https:'];

// 默认白名单域名
const DEFAULT_WHITELIST = [
  // 官方域名
  'matuX.com',
  'matuX.cn',
  'matux.net',
  'matux.io',
  // 开发环境
  'localhost',
  '127.0.0.1',
  // Python 官方
  'python.org',
  'pypi.org',
  'pip.pypa.io',
  // 教育资源
  'edu.cn',
  'gov.cn',
];

// 危险域名黑名单
const BLOCKED_DOMAINS = [
  'localhost.phishing.com',  // 防止 localhost.phishing.com 绕过检查
  '127.0.0.1.evil.com',
];

/**
 * URL 白名单管理器
 */
class UrlWhitelist {
  constructor(options = {}) {
    this.whitelist = new Set(options.whitelist || DEFAULT_WHITELIST);
    this.blockedDomains = new Set(options.blockedDomains || BLOCKED_DOMAINS);
    this.allowAllLocal = options.allowAllLocal !== false;
    this.allowAllInternal = options.allowAllInternal !== false;
  }

  /**
   * 添加域名到白名单
   * @param {string} domain 域名
   */
  add(domain) {
    this.whitelist.add(domain.toLowerCase());
  }

  /**
   * 从白名单移除域名
   * @param {string} domain 域名
   */
  remove(domain) {
    this.whitelist.delete(domain.toLowerCase());
  }

  /**
   * 检查域名是否在黑名单中
   * @param {string} hostname 主机名
   * @returns {boolean}
   */
  isBlocked(hostname) {
    const lower = hostname.toLowerCase();
    return this.blockedDomains.has(lower);
  }

  /**
   * 检查是否是本地地址
   * @param {string} hostname 主机名
   * @returns {boolean}
   */
  isLocal(hostname) {
    const lower = hostname.toLowerCase();
    return (
      lower === 'localhost' ||
      lower === '127.0.0.1' ||
      lower === '::1' ||
      lower.startsWith('192.168.') ||
      lower.startsWith('10.') ||
      lower.startsWith('172.16.') ||
      lower.endsWith('.local')
    );
  }

  /**
   * 检查域名是否在白名单中
   * @param {string} hostname 主机名
   * @returns {boolean}
   */
  isInWhitelist(hostname) {
    const lower = hostname.toLowerCase();

    // 首先检查黑名单
    if (this.isBlocked(lower)) {
      return false;
    }

    // 检查精确匹配
    if (this.whitelist.has(lower)) {
      return true;
    }

    // 检查子域名匹配
    for (const domain of this.whitelist) {
      if (lower === domain || lower.endsWith('.' + domain)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 验证 URL
   * @param {string} url URL 字符串
   * @returns {{ valid: boolean, error?: string }}
   */
  validate(url) {
    try {
      const urlObj = new URL(url);

      // 检查协议
      if (!ALLOWED_PROTOCOLS.includes(urlObj.protocol)) {
        return {
          valid: false,
          error: `不允许的协议: ${urlObj.protocol}`,
        };
      }

      // 检查黑名单
      if (this.isBlocked(urlObj.hostname)) {
        return {
          valid: false,
          error: `域名在黑名单中: ${urlObj.hostname}`,
        };
      }

      // 检查本地地址
      if (this.isLocal(urlObj.hostname) && this.allowAllLocal) {
        return { valid: true };
      }

      // 检查白名单
      if (this.isInWhitelist(urlObj.hostname)) {
        return { valid: true };
      }

      return {
        valid: false,
        error: `域名不在白名单中: ${urlObj.hostname}`,
      };
    } catch (err) {
      return {
        valid: false,
        error: `无效的 URL: ${err.message}`,
      };
    }
  }

  /**
   * 获取白名单列表
   * @returns {string[]}
   */
  getWhitelist() {
    return [...this.whitelist];
  }
}

// 单例
let instance = null;

/**
 * 获取 URL 白名单单例
 * @param {object} options 配置选项
 * @returns {UrlWhitelist}
 */
function getUrlWhitelist(options = {}) {
  if (!instance) {
    instance = new UrlWhitelist(options);
  }
  return instance;
}

/**
 * 验证外部 URL 是否安全（快捷函数）
 * @param {string} url URL 字符串
 * @returns {{ valid: boolean, error?: string }}
 */
function validateExternalUrl(url) {
  return getUrlWhitelist().validate(url);
}

module.exports = {
  UrlWhitelist,
  getUrlWhitelist,
  validateExternalUrl,
  ALLOWED_PROTOCOLS,
  DEFAULT_WHITELIST,
  BLOCKED_DOMAINS,
};
