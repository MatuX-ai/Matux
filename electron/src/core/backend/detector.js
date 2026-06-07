/**
 * Python 环境检测模块
 * @module backend/detector
 */

const { execSync } = require('child_process');
const fs = require('fs');

// 【P3-4修复】统一魔法数字为具名常量
const EXEC_SYNC_TIMEOUT = 5000;

/**
 * 检查 Python 版本是否 >= 3.9（语义版本号比较，避免 parseFloat 误判）
 * @param {string} versionStr 版本字符串，如 "3.12"
 * @returns {boolean}
 */
function isPythonVersionGte39(versionStr) {
  const parts = versionStr.split('.');
  const major = parseInt(parts[0], 10);
  const minor = parseInt(parts[1], 10);
  return major > 3 || (major === 3 && minor >= 9);
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
    const regex = /-([\d.]+)\s+(.+?python\.exe)/gi;
    let m;
    while ((m = regex.exec(output)) !== null) {
      found.add(m[2].replace(/\s*\*$/, '').trim());
    }
  } catch { /* py 命令不可用 */ }

  // 方法2: 检查常见安装目录（覆盖 C: 到 N: 的所有盘符）
  const drives = 'CDEFGHIJKLMN'.split('');
  const majorVersions = ['312', '311', '310', '39', '313'];
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
        if (isPythonVersionGte39(versionMatch[1])) {
          return {
            available: true,
            version: versionMatch[1],
            path: cmd,
          };
        }
        console.warn(`[WARN] Python ${versionMatch[1]} 版本过低，需要 3.9+`);
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
        if (versionMatch && isPythonVersionGte39(versionMatch[1])) {
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
  // 后端启动所必需的核心包（无此列表中的包将无法启动）
  const criticalPkgs = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic', 'python-jose', 'passlib', 'python-multipart'];

  try {
    const output = execSync(`"${pythonInfo.path}" -m pip list --format=columns 2>&1`, {
      encoding: 'utf-8',
      timeout: 15000,
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
    const missing = criticalPkgs.filter((pkg) => !installed.has(pkg.toLowerCase()));
    return missing;
  } catch (err) {
    console.warn('[WARN] 无法检查 Python 依赖包:', err.message);
    return []; // 无法检查时不阻塞启动
  }
}

module.exports = {
  isPythonVersionGte39,
  searchPythonPaths,
  detectPython,
  checkPythonDeps,
};
