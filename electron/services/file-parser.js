/**
 * iMato 文件解析服务
 *
 * 支持的文件类型：
 * - .imato   - 课程包
 * - .imblockly - Blockly 可视化编程项目
 * - .imcircuit - 电路仿真项目
 *
 * @module services/file-parser
 */

const fs = require('fs');
const path = require('path');

/** 允许的文件扩展名 */
const ALLOWED_EXTENSIONS = ['.imato', '.imblockly', '.imcircuit'];

/** 最大文件大小 (10MB) */
const MAX_FILE_SIZE = 10 * 1024 * 1024;

/**
 * 验证文件名是否安全
 * @param {string} fileName - 文件名
 * @returns {boolean}
 */
function isValidFileName(fileName) {
  if (!fileName || typeof fileName !== 'string') return false;

  const ext = path.extname(fileName).toLowerCase();
  return ALLOWED_EXTENSIONS.includes(ext);
}

/**
 * 获取文件类型
 * @param {string} filePath - 文件路径
 * @returns {'course' | 'blockly' | 'circuit' | null}
 */
function getFileType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case '.imato':
      return 'course';
    case '.imblockly':
      return 'blockly';
    case '.imcircuit':
      return 'circuit';
    default:
      return null;
  }
}

/**
 * 安全读取文件
 * @param {string} filePath - 文件路径
 * @returns {{ success: boolean, content?: any, raw?: string, fileType?: string, error?: string }}
 */
function safeReadFile(filePath) {
  try {
    // 路径规范化
    const normalizedPath = path.normalize(filePath);

    // 防止路径遍历攻击
    if (normalizedPath.includes('..') || normalizedPath.includes('~')) {
      return { success: false, error: '非法路径字符' };
    }

    // 检查文件是否存在
    if (!fs.existsSync(normalizedPath)) {
      return { success: false, error: '文件不存在' };
    }

    // 获取文件信息
    const stats = fs.statSync(normalizedPath);

    // 检查文件大小
    if (stats.size > MAX_FILE_SIZE) {
      return {
        success: false,
        error: `文件过大 (${(stats.size / 1024 / 1024).toFixed(2)}MB)，最大支持 ${MAX_FILE_SIZE / 1024 / 1024}MB`,
      };
    }

    // 读取文件内容
    const raw = fs.readFileSync(normalizedPath, 'utf8');

    // 获取文件类型
    const fileType = getFileType(normalizedPath);

    // 解析 JSON
    let content = null;
    try {
      content = JSON.parse(raw);
    } catch (parseError) {
      return {
        success: false,
        error: `JSON 解析失败: ${parseError.message}`,
      };
    }

    // 验证 JSON 结构
    const validation = validateFileContent(content, fileType);
    if (!validation.valid) {
      return {
        success: false,
        error: validation.error,
      };
    }

    return {
      success: true,
      content,
      raw,
      fileType,
    };
  } catch (err) {
    return {
      success: false,
      error: `读取文件失败: ${err.message}`,
    };
  }
}

/**
 * 验证文件内容结构
 * @param {any} content - 解析后的 JSON 内容
 * @param {string} fileType - 文件类型
 * @returns {{ valid: boolean, error?: string }}
 */
function validateFileContent(content, fileType) {
  if (!content || typeof content !== 'object') {
    return { valid: false, error: '文件内容必须是对象' };
  }

  // 验证通用字段
  if (!content.version) {
    return { valid: false, error: '缺少 version 字段' };
  }

  if (!content.type) {
    return { valid: false, error: '缺少 type 字段' };
  }

  // 验证类型匹配
  const typeMap = {
    course: 'blockly-project|python-project|circuit-project',
    blockly: 'blockly-project',
    circuit: 'circuit-project',
  };

  if (fileType && typeMap[fileType]) {
    const pattern = new RegExp(`^(${typeMap[fileType]})$`);
    if (!pattern.test(content.type)) {
      return {
        valid: false,
        error: `文件类型不匹配: 期望 ${typeMap[fileType]}，实际 ${content.type}`,
      };
    }
  }

  // 验证必需字段
  if (!content.data) {
    return { valid: false, error: '缺少 data 字段' };
  }

  if (!content.metadata) {
    return { valid: false, error: '缺少 metadata 字段' };
  }

  return { valid: true };
}

/**
 * 创建新项目文件
 * @param {string} type - 项目类型
 * @param {object} data - 项目数据
 * @returns {string} JSON 字符串
 */
function createProjectFile(type, data) {
  const project = {
    version: '1.0',
    type,
    data,
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: 'iMato User',
    },
  };
  return JSON.stringify(project, null, 2);
}

/**
 * 保存项目文件
 * @param {string} filePath - 文件路径
 * @param {object} data - 项目数据
 * @returns {{ success: boolean, error?: string }}
 */
function saveProjectFile(filePath, data) {
  try {
    const content = createProjectFile(data.type || 'blockly-project', data);
    fs.writeFileSync(filePath, content, 'utf8');
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

module.exports = {
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE,
  isValidFileName,
  getFileType,
  safeReadFile,
  validateFileContent,
  createProjectFile,
  saveProjectFile,
};
