/**
 * MatuX Electron 安全验证模块
 *
 * 提供 URL 和文件路径的安全验证功能
 * 防止命令注入、路径遍历等安全攻击
 */

const path = require('path');

// 允许的 URL 协议
const ALLOWED_URL_PROTOCOLS = ['http:', 'https:'];

// 允许打开的外部域名白名单
const ALLOWED_EXTERNAL_DOMAINS = [
  'github.com',
  'github.io',
  'docs.github.com',
  'accounts.google.com',
  'matux.ai',
  'docs.matux.ai',
  'dicebear.com',
];

// 允许访问的基础路径
const ALLOWED_BASE_PATHS = [];

/**
 * 验证外部 URL 是否安全
 * @param {string} url 要验证的 URL
 * @returns {{ valid: boolean, error?: string }}
 */
function validateExternalUrl(url) {
  if (!url || typeof url !== 'string') {
    return { valid: false, error: 'URL 不能为空' };
  }

  try {
    const parsed = new URL(url);

    // 协议检查
    if (!ALLOWED_URL_PROTOCOLS.includes(parsed.protocol)) {
      return { valid: false, error: `不允许的协议: ${parsed.protocol}` };
    }

    // 域名白名单检查
    const hostname = parsed.hostname.toLowerCase();
    const isAllowed = ALLOWED_EXTERNAL_DOMAINS.some(
      (domain) => hostname === domain || hostname.endsWith(`.${domain}`)
    );

    if (!isAllowed) {
      // 允许 localhost 用于开发环境
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return { valid: true };
      }
      return { valid: false, error: `URL 不在白名单中: ${hostname}` };
    }

    return { valid: true };
  } catch (err) {
    return { valid: false, error: `URL 格式无效: ${err.message}` };
  }
}

/**
 * 验证文件路径是否安全
 * @param {string} filePath 要验证的文件路径
 * @param {string|string[]} [allowedBasePaths] 允许的基础路径，默认为空
 * @returns {{ valid: boolean, error?: string }}
 */
function validateFilePath(filePath, allowedBasePaths = []) {
  if (!filePath || typeof filePath !== 'string') {
    return { valid: false, error: '路径不能为空' };
  }

  // 路径遍历检查
  const normalized = path.normalize(filePath);
  if (normalized.includes('..') || normalized.includes('~')) {
    return { valid: false, error: '路径包含非法字符（禁止 .. 和 ~）' };
  }

  // 绝对路径检查
  const isAbsolute = path.isAbsolute(filePath);

  if (isAbsolute && allowedBasePaths.length > 0) {
    const normalizedPath = path.normalize(filePath);
    const isInAllowed = allowedBasePaths.some((basePath) => {
      const normalizedBase = path.normalize(basePath);
      return normalizedPath.startsWith(normalizedBase);
    });

    if (!isInAllowed) {
      return { valid: false, error: '路径不在允许的目录范围内' };
    }
  }

  // 危险扩展名检查（可选扩展）
  const dangerousExtensions = ['.exe', '.bat', '.cmd', '.ps1', '.sh', '.js', '.ts', '.py'];
  const ext = path.extname(filePath).toLowerCase();
  if (dangerousExtensions.includes(ext)) {
    return { valid: false, error: `不允许的文件类型: ${ext}` };
  }

  return { valid: true };
}

/**
 * 获取允许的基础路径列表
 * @returns {string[]}
 */
function getAllowedPaths() {
  // 可以从环境变量或配置文件读取
  return ALLOWED_BASE_PATHS;
}

/**
 * 验证 URL 是否可以用于 shell.openExternal
 * @param {string} url URL
 * @returns {boolean}
 */
function isUrlAllowedForShell(url) {
  const result = validateExternalUrl(url);
  if (!result.valid) {
    return false;
  }

  // 额外检查：禁止 file:// 协议
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'file:') {
      return false;
    }
  } catch {
    return false;
  }

  return true;
}

module.exports = {
  validateExternalUrl,
  validateFilePath,
  getAllowedPaths,
  isUrlAllowedForShell,
  ALLOWED_EXTERNAL_DOMAINS,
  ALLOWED_URL_PROTOCOLS,
};
