/**
 * 路径安全验证模块
 * @module security/path-validator
 *
 * 用于验证文件路径安全，防止路径穿越攻击
 */

const path = require('path');
const fs = require('fs');

// 默认允许的基础路径
const DEFAULT_ALLOWED_BASES = [
  process.env.APPDATA || '',
  process.env.LOCALAPPDATA || '',
  process.env.HOME || '',
  process.env.USERPROFILE || '',
];

// 危险路径模式
const DANGEROUS_PATTERNS = [
  /\.\./g,           // 路径穿越
  /^\//,             // 绝对 Unix 路径
  /^[A-Za-z]:\\/,    // Windows 绝对路径（需要检查）
  /%00/g,            // 空字节注入
  /\x00/g,           // 空字节
  /[\r\n]/g,         // 换行符注入
];

/**
 * 路径验证器
 */
class PathValidator {
  constructor(options = {}) {
    this.allowedBases = options.allowedBases || DEFAULT_ALLOWED_BASES;
    this.allowExternal = options.allowExternal !== undefined ? options.allowExternal : false;
    this.allowSymlinks = options.allowSymlinks || false;
    this.maxPathLength = options.maxPathLength || 260;  // Windows MAX_PATH
  }

  /**
   * 添加允许的基础路径
   * @param {string} basePath 基础路径
   */
  addAllowedBase(basePath) {
    if (basePath && fs.existsSync(basePath)) {
      const normalized = path.normalize(basePath);
      if (!this.allowedBases.includes(normalized)) {
        this.allowedBases.push(normalized);
      }
    }
  }

  /**
   * 检查路径是否包含危险模式
   * @param {string} filePath 文件路径
   * @returns {{ safe: boolean, reason?: string }}
   */
  checkDangerousPatterns(filePath) {
    for (const pattern of DANGEROUS_PATTERNS) {
      if (pattern.test(filePath)) {
        return {
          safe: false,
          reason: `路径包含危险模式: ${pattern.toString()}`,
        };
      }
    }
    return { safe: true };
  }

  /**
   * 检查路径长度
   * @param {string} filePath 文件路径
   * @returns {{ safe: boolean, reason?: string }}
   */
  checkPathLength(filePath) {
    if (filePath.length > this.maxPathLength) {
      return {
        safe: false,
        reason: `路径长度超过限制: ${filePath.length} > ${this.maxPathLength}`,
      };
    }
    return { safe: true };
  }

  /**
   * 检查是否是符号链接
   * @param {string} filePath 文件路径
   * @returns {boolean}
   */
  isSymlink(filePath) {
    try {
      const stats = fs.lstatSync(filePath);
      return stats.isSymbolicLink();
    } catch {
      return false;
    }
  }

  /**
   * 检查路径是否在允许的基础路径下
   * @param {string} filePath 文件路径
   * @returns {boolean}
   */
  isUnderAllowedBase(filePath) {
    const normalized = path.normalize(filePath);

    for (const base of this.allowedBases) {
      if (!base) continue;
      const normalizedBase = path.normalize(base);
      if (normalized.startsWith(normalizedBase) || normalized.startsWith(normalizedBase + path.sep)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 解析相对路径为绝对路径
   * @param {string} filePath 输入路径
   * @param {string} basePath 基础路径（可选）
   * @returns {string}
   */
  resolvePath(filePath, basePath = process.cwd()) {
    // 处理相对路径
    if (!path.isAbsolute(filePath)) {
      return path.resolve(basePath, filePath);
    }
    return path.normalize(filePath);
  }

  /**
   * 验证路径安全性
   * @param {string} filePath 文件路径
   * @param {object} options 验证选项
   * @returns {{ valid: boolean, error?: string, resolvedPath?: string }}
   */
  validate(filePath, options = {}) {
    const {
      checkSymlinks = !this.allowSymlinks,
      checkBase = true,
      checkPatterns = true,
      checkLength = true,
      basePath = process.cwd(),
    } = options;

    if (!filePath || typeof filePath !== 'string') {
      return {
        valid: false,
        error: '无效的路径：路径不能为空',
      };
    }

    // 检查危险模式
    if (checkPatterns) {
      const patternCheck = this.checkDangerousPatterns(filePath);
      if (!patternCheck.safe) {
        return {
          valid: false,
          error: patternCheck.reason,
        };
      }
    }

    // 检查路径长度
    if (checkLength) {
      const lengthCheck = this.checkPathLength(filePath);
      if (!lengthCheck.safe) {
        return {
          valid: false,
          error: lengthCheck.reason,
        };
      }
    }

    // 解析路径
    const resolvedPath = this.resolvePath(filePath, basePath);

    // 检查符号链接
    if (checkSymlinks && this.isSymlink(resolvedPath)) {
      // 如果允许符号链接，需要追踪到真实路径
      if (!this.allowSymlinks) {
        return {
          valid: false,
          error: '不允许使用符号链接',
          resolvedPath,
        };
      }
    }

    // 检查基础路径
    if (checkBase && !this.allowExternal) {
      if (!this.isUnderAllowedBase(resolvedPath)) {
        return {
          valid: false,
          error: `路径不在允许的基础目录内: ${resolvedPath}`,
          resolvedPath,
        };
      }
    }

    return {
      valid: true,
      resolvedPath,
    };
  }

  /**
   * 验证文件读取操作
   * @param {string} filePath 文件路径
   * @returns {{ valid: boolean, error?: string }}
   */
  validateRead(filePath) {
    const result = this.validate(filePath);
    if (!result.valid) return result;

    // 检查文件是否存在
    if (!fs.existsSync(result.resolvedPath)) {
      return {
        valid: false,
        error: '文件不存在',
      };
    }

    // 检查是否可读
    try {
      fs.accessSync(result.resolvedPath, fs.constants.R_OK);
    } catch {
      return {
        valid: false,
        error: '文件不可读',
      };
    }

    return result;
  }

  /**
   * 验证文件写入操作
   * @param {string} filePath 文件路径
   * @returns {{ valid: boolean, error?: string }}
   */
  validateWrite(filePath) {
    const result = this.validate(filePath, { checkBase: true });
    if (!result.valid) return result;

    // 检查目录是否存在
    const dir = path.dirname(result.resolvedPath);
    if (!fs.existsSync(dir)) {
      return {
        valid: false,
        error: '父目录不存在',
      };
    }

    // 检查目录是否可写
    try {
      fs.accessSync(dir, fs.constants.W_OK);
    } catch {
      return {
        valid: false,
        error: '目录不可写',
      };
    }

    return result;
  }

  /**
   * 获取允许的基础路径列表
   * @returns {string[]}
   */
  getAllowedBases() {
    return [...this.allowedBases];
  }
}

// 单例
let instance = null;

/**
 * 获取路径验证器单例
 * @param {object} options 配置选项
 * @returns {PathValidator}
 */
function getPathValidator(options = {}) {
  if (!instance) {
    instance = new PathValidator(options);
  }
  return instance;
}

/**
 * 验证文件路径安全（快捷函数）
 * @param {string} filePath 文件路径
 * @param {object} options 验证选项
 * @returns {{ valid: boolean, error?: string }}
 */
function validateFilePath(filePath, options = {}) {
  return getPathValidator().validate(filePath, options);
}

module.exports = {
  PathValidator,
  getPathValidator,
  validateFilePath,
  DEFAULT_ALLOWED_BASES,
  DANGEROUS_PATTERNS,
};
