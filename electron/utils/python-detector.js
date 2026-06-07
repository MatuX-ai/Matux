/**
 * MatuX Electron Python 环境检测工具
 * 
 * 提供 Python 版本检测、依赖检查等工具函数
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const {
  EXEC_SYNC_TIMEOUT,
  EXEC_SYNC_PIP_TIMEOUT,
  PYTHON_MIN_VERSION,
  CRITICAL_PYTHON_PACKAGES,
} = require('../config/constants');

/**
 * 检查 Python 版本是否满足最低要求
 * @param {string} versionStr 版本字符串，如 "3.12"
 * @returns {boolean}
 */
function isPythonVersionGteMin(versionStr) {
  const { major: MIN_MAJOR, minor: MIN_MINOR } = PYTHON_MIN_VERSION;
  const parts = versionStr.split('.');
  const major = parseInt(parts[0], 10);
  const minor = parseInt(parts[1], 10);
  return major > MIN_MAJOR || (major === MIN_MAJOR && minor >= MIN_MINOR);
}

/**
 * 搜索 Windows 上常见的 Python 安装路径
 * @returns {string[]} 找到的 python.exe 路径列表
 */
function searchPythonPaths() {
  if (process.platform !== 'win32') return [];
  const found = new Set();

  // 方法1: 使用 py --list-paths 获取所有注册的 Python 安装
  try {
    const output = execSync('py --list-paths 2>&1', {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
      shell: true,
    });
    const regex = /-[\d.]+\s+(.+?python\.exe)/gi;
    let m;
    while ((m = regex.exec(output)) !== null) {
      found.add(m[1].replace(/\s*\*$/, '').trim());
    }
  } catch { /* py 命令不可用 */ }

  // 方法2: 检查常见安装目录
  const drives = 'CDEFGHIJKLMN'.split('');
  const { major: v1, minor: v2 } = PYTHON_MIN_VERSION;
  const majorVersions = ['313', '312', '311', '310', `${v1}${v2}`];
  const pathTemplates = [];

  for (const drive of drives) {
    for (const ver of majorVersions) {
      pathTemplates.push(`${drive}:\\Python${ver}\\python.exe`);
      pathTemplates.push(`${drive}:\\Program Files\\Python${ver}\\python.exe`);
    }
  }

  const userProfile = process.env.USERPROFILE || 'C:\\Users\\Default';
  for (const ver of majorVersions) {
    pathTemplates.push(`${userProfile}\\AppData\\Local\\Programs\\Python\\Python${ver}\\python.exe`);
  }

  for (const p of pathTemplates) {
    if (fs.existsSync(p)) found.add(p);
  }

  return [...found];
}

/**
 * 检测 Python 是否可用（自动搜索 PATH + 常见安装路径）
 * @returns {{ available: boolean, version: string, path: string }}
 */
function detectPython() {
  // Phase 1: 检查 PATH 命令
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py', 'py -3']
    : ['python3', 'python'];

  for (const cmd of candidates) {
    try {
      const versionOutput = execSync(`"${cmd}" --version 2>&1`, {
        encoding: 'utf-8',
        timeout: EXEC_SYNC_TIMEOUT,
        shell: true,
      }).trim();
      const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
      if (versionMatch) {
        if (isPythonVersionGteMin(versionMatch[1])) {
          return {
            available: true,
            version: versionMatch[1],
            path: cmd,
          };
        }
        console.warn(`[WARN] Python ${versionMatch[1]} 版本过低，需要 ${PYTHON_MIN_VERSION.major}.${PYTHON_MIN_VERSION.minor}+`);
      }
    } catch {
      // 该命令不可用，尝试下一个
    }
  }

  // Phase 2: 搜索常见安装路径（仅 Windows）
  if (process.platform === 'win32') {
    const searchedPaths = searchPythonPaths();
    for (const pyPath of searchedPaths) {
      try {
        const versionOutput = execSync(`"${pyPath}" --version 2>&1`, {
          encoding: 'utf-8',
          timeout: EXEC_SYNC_TIMEOUT,
        }).trim();
        const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
        if (versionMatch && isPythonVersionGteMin(versionMatch[1])) {
          return {
            available: true,
            version: versionMatch[1],
            path: pyPath,
          };
        }
      } catch { /* 该路径不可执行，跳过 */ }
    }
  }

  return { available: false, version: '', path: '' };
}

/**
 * 检测 Python 关键依赖包是否安装
 * @param {object} pythonInfo detectPython 的返回值
 * @returns {string[]} 缺失的包名列表
 */
function checkPythonDeps(pythonInfo) {
  try {
    const output = execSync(`"${pythonInfo.path}" -m pip list --format=columns 2>&1`, {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_PIP_TIMEOUT,
      shell: true,
    });

    // 解析 pip list 输出，收集已安装的包名
    const installed = new Set();
    const lines = output.split('\n');
    for (const line of lines) {
      if (line.startsWith('---') || line.toLowerCase().startsWith('package')) continue;
      const pkgName = line.trim().split(/\s+/)[0];
      if (pkgName) installed.add(pkgName.toLowerCase());
    }

    // 检查哪些核心包缺失
    const missing = CRITICAL_PYTHON_PACKAGES.filter((pkg) => !installed.has(pkg.toLowerCase()));
    return missing;
  } catch (err) {
    console.warn('[WARN] 无法检查 Python 依赖包:', err.message);
    return []; // 无法检查时不阻塞启动
  }
}

/**
 * 获取 Python 版本信息（人类可读格式）
 * @param {string} version 版本号字符串
 * @returns {string}
 */
function formatPythonVersion(version) {
  return `Python ${version}`;
}

/**
 * 检查是否需要安装 Python
 * @param {object} pythonInfo detectPython 的返回值
 * @returns {{ needed: boolean, reason?: string }}
 */
function isPythonInstallNeeded(pythonInfo) {
  if (!pythonInfo.available) {
    return { needed: true, reason: '未检测到 Python 环境' };
  }

  // 【P0修复】使用语义化版本比较，避免 parseFloat("3.10")=3.1 的问题
  if (!isPythonVersionGteMin(pythonInfo.version)) {
    const minVersion = `${PYTHON_MIN_VERSION.major}.${PYTHON_MIN_VERSION.minor}`;
    return { needed: true, reason: `Python 版本过低 (${pythonInfo.version})，需要 ${minVersion}+` };
  }

  return { needed: false };
}

module.exports = {
  isPythonVersionGteMin,
  searchPythonPaths,
  detectPython,
  checkPythonDeps,
  formatPythonVersion,
  isPythonInstallNeeded,
};
