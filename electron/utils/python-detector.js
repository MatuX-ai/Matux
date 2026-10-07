/**
 * MatuX Electron Python 环境检测工具
 *
 * 提供 Python 版本检测、依赖检查（含 24h 缓存）等工具函数
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

// ==================== 依赖检查缓存配置（24h TTL）====================

const DEPS_CACHE_TTL_MS = 24 * 60 * 60 * 1000;  // 24h
const DEPS_CACHE_FILENAME = 'python-deps-cache.json';

/**
 * 获取依赖缓存文件路径
 * 优先写入 app.getPath('userData')，跨会话持久化
 */
function getDepsCachePath() {
  try {
    const { app } = require('electron');
    if (app.isReady && app.isReady()) {
      return path.join(app.getPath('userData'), DEPS_CACHE_FILENAME);
    }
  } catch { /* electron 未加载或非主进程 */ }
  return path.join(require('os').tmpdir(), DEPS_CACHE_FILENAME);
}

/**
 * 读取依赖检查缓存（命中条件：未过期 + Python 路径/版本未变 + 之前齐全）
 * @returns {string[]|null} 缓存的 missing 列表；未命中返回 null
 */
function loadDepsCache(pythonInfo) {
  if (!pythonInfo || !pythonInfo.path) return null;
  const cachePath = getDepsCachePath();
  if (!fs.existsSync(cachePath)) return null;
  try {
    const raw = fs.readFileSync(cachePath, 'utf-8');
    const cache = JSON.parse(raw);
    if (!cache || typeof cache !== 'object' || typeof cache.timestamp !== 'number') {
      return null;
    }
    if (Date.now() - cache.timestamp > DEPS_CACHE_TTL_MS) return null;  // TTL 检查
    if (cache.pythonPath !== pythonInfo.path) return null;              // 路径变化
    if (cache.pythonVersion !== pythonInfo.version) return null;         // 版本变化
    if (!Array.isArray(cache.missing) || cache.missing.length > 0) return null;  // 只缓存齐全结果
    return cache.missing;
  } catch (err) {
    console.warn('[WARN] 依赖缓存读取失败:', err.message);
    return null;
  }
}

/**
 * 写入依赖检查缓存（仅 missing=[] 时生效，避免污染中间状态）
 */
function saveDepsCache(pythonInfo, missing) {
  if (!Array.isArray(missing) || missing.length > 0) return;
  if (!pythonInfo || !pythonInfo.path) return;
  const cachePath = getDepsCachePath();
  try {
    const cache = {
      version: '1.0',
      timestamp: Date.now(),
      pythonPath: pythonInfo.path,
      pythonVersion: pythonInfo.version,
      missing,
    };
    fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2), 'utf-8');
    console.log(`[INFO] 依赖检查结果已缓存: ${cachePath}`);
  } catch (err) {
    console.warn('[WARN] 依赖缓存写入失败:', err.message);
  }
}

/**
 * 清除依赖检查缓存（供 IPC "重新检查依赖" 使用）
 */
function clearDepsCache() {
  try {
    const p = getDepsCachePath();
    if (fs.existsSync(p)) fs.unlinkSync(p);
  } catch (err) {
    console.warn('[WARN] 清理依赖缓存失败:', err.message);
  }
}

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

  // 【增强】Microsoft Store 安装的 Python 路径
  const localAppData = process.env.LOCALAPPDATA || `${userProfile}\\AppData\\Local`;
  pathTemplates.push(`${localAppData}\\Microsoft\\WindowsApps\\python.exe`);
  pathTemplates.push(`${localAppData}\\Microsoft\\WindowsApps\\python3.exe`);
  // Microsoft Store Python 的实际安装路径
  pathTemplates.push(`${localAppData}\\Programs\\Python\\Python312\\python.exe`);
  pathTemplates.push(`${localAppData}\\Programs\\Python\\Python311\\python.exe`);
  pathTemplates.push(`${localAppData}\\Programs\\Python\\Python310\\python.exe`);

  // 【增强】检查 PATH 环境变量中所有包含 python 的目录
  const envPath = process.env.PATH || '';
  const pathDirs = envPath.split(path.delimiter);
  for (const dir of pathDirs) {
    const pyExe = path.join(dir, 'python.exe');
    if (fs.existsSync(pyExe)) found.add(pyExe);
    const py3Exe = path.join(dir, 'python3.exe');
    if (fs.existsSync(py3Exe)) found.add(py3Exe);
  }

  // 【增强】Anaconda/Miniconda 环境
  const condaPaths = [
    `${userProfile}\\Anaconda3\\python.exe`,
    `${userProfile}\\miniconda3\\python.exe`,
    `${localAppData}\\Continuum\\anaconda3\\python.exe`,
    `${localAppData}\\Continuum\\miniconda3\\python.exe`,
  ];
  for (const p of condaPaths) {
    if (fs.existsSync(p)) found.add(p);
  }

  for (const p of pathTemplates) {
    if (fs.existsSync(p)) found.add(p);
  }

  return [...found];
}

/**
 * 验证指定路径是否为可用 Python（满足 >= PYTHON_MIN_VERSION）
 * 【NSIS 集成】被 utils/install-state.js 的 consumePendingPythonPath() 调用，
 * 也被 python-checker.js 中"手动选择"流程复用（统一验证逻辑）。
 *
 * @param {string} pythonPath - python.exe 的绝对路径
 * @returns {{ available: boolean, version: string, path: string, error?: string }}
 */
function validatePythonAtPath(pythonPath) {
  if (!pythonPath || typeof pythonPath !== 'string') {
    return { available: false, version: '', path: pythonPath || '', error: 'empty path' };
  }
  if (!fs.existsSync(pythonPath)) {
    return { available: false, version: '', path: pythonPath, error: 'file not found' };
  }
  try {
    const versionOutput = execSync(`"${pythonPath}" --version 2>&1`, {
      encoding: 'utf-8',
      timeout: EXEC_SYNC_TIMEOUT,
    }).trim();
    const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
    if (versionMatch && isPythonVersionGteMin(versionMatch[1])) {
      return { available: true, version: versionMatch[1], path: pythonPath };
    }
    return {
      available: false,
      version: versionMatch ? versionMatch[1] : '',
      path: pythonPath,
      error: versionMatch ? `version ${versionMatch[1]} below ${PYTHON_MIN_VERSION.major}.${PYTHON_MIN_VERSION.minor}` : 'unrecognized output',
    };
  } catch (err) {
    return { available: false, version: '', path: pythonPath, error: err.message };
  }
}

/**
 * 检测 Python 是否可用（自动搜索 PATH + 常见安装路径）
 * @returns {{ available: boolean, version: string, path: string }}
 */
function detectPython() {
  // Phase 1: 检查 PATH 命令
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py']
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

  // 【增强】Phase 1b: 尝试 py -3 命令（Windows Python Launcher，需特殊处理）
  if (process.platform === 'win32') {
    try {
      const versionOutput = execSync('py -3 --version 2>&1', {
        encoding: 'utf-8',
        timeout: EXEC_SYNC_TIMEOUT,
        shell: true,
      }).trim();
      const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
      if (versionMatch && isPythonVersionGteMin(versionMatch[1])) {
        return {
          available: true,
          version: versionMatch[1],
          path: 'py -3',
        };
      }
    } catch { /* py launcher 不可用 */ }
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
 * 【启动优化 P1-5】增加 24h 缓存机制，避免每次启动都调 pip list
 * - 快速路径：缓存命中 → 返回 < 1ms
 * - 慢速路径：未命中 → 调 pip list (1-3s) → 写缓存
 * - 只缓存"全部齐全"结果，避免部分缺失场景误判
 * @param {object} pythonInfo detectPython 的返回值
 * @returns {string[]} 缺失的包名列表
 */
function checkPythonDeps(pythonInfo) {
  if (!pythonInfo || !pythonInfo.path) {
    return [];
  }

  // 【启动优化 P1-5】先检查缓存
  const cached = loadDepsCache(pythonInfo);
  if (cached !== null) {
    console.log('[INFO] Python 依赖检查命中缓存（<1ms），跳过 pip list');
    return cached;
  }

  // 缓存未命中，执行实际的 pip list
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

    // 【启动优化 P1-5】写入缓存（仅 missing=[] 时生效）
    saveDepsCache(pythonInfo, missing);

    return missing;
  } catch (err) {
    console.warn('[WARN] 无法检查 Python 依赖包:', err.message);
    return []; // 无法检查时不阻塞启动
  }
}

/**
 * 自动安装缺失的 Python 依赖包
 * @param {object} pythonInfo detectPython 的返回值
 * @param {string[]} missingDeps 缺失的包名列表
 * @param {Function} [onProgress] 进度回调 (message: string)
 * @returns {{ success: boolean, error?: string }}
 */
function installPythonDeps(pythonInfo, missingDeps, onProgress) {
  if (!pythonInfo || !pythonInfo.path || !missingDeps || missingDeps.length === 0) {
    return { success: true };
  }

  try {
    const packages = missingDeps.join(' ');
    // 【修复】优先 --user 安装（无需管理员权限），失败再尝试全局安装
    const pipCmd = `"${pythonInfo.path}" -m pip install ${packages} --user --quiet --no-warn-script-location`;

    console.log(`[INFO] 正在安装缺失依赖 (--user): ${packages}`);
    if (onProgress) onProgress(`正在安装 ${missingDeps.length} 个依赖包...`);

    execSync(pipCmd, {
      encoding: 'utf-8',
      timeout: 120000, // 2 分钟超时（下载+安装）
      shell: true,
    });

    console.log('[INFO] 依赖安装完成');
    if (onProgress) onProgress('依赖安装完成，正在验证...');

    // 安装后清除缓存并重新检查依赖
    clearDepsCache();
    const stillMissing = checkPythonDeps(pythonInfo);
    if (stillMissing.length > 0) {
      console.error(`[ERROR] 部分依赖安装失败，仍然缺失: ${stillMissing.join(', ')}`);
      return { success: false, error: `以下依赖安装失败: ${stillMissing.join(', ')}` };
    }

    console.log('[INFO] 所有依赖安装成功');
    if (onProgress) onProgress('所有依赖安装成功');
    return { success: true };
  } catch (err) {
    console.error('[ERROR] 依赖安装失败:', err.message);
    return { success: false, error: err.message };
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
  /** @deprecated Use isPythonVersionGteMin instead */
  isPythonVersionGte39: isPythonVersionGteMin,
  validatePythonAtPath,
  searchPythonPaths,
  detectPython,
  checkPythonDeps,
  installPythonDeps,
  formatPythonVersion,
  isPythonInstallNeeded,
  // 【启动优化 P1-5】导出缓存函数（供 IPC "重新检查依赖" 使用）
  loadDepsCache,
  saveDepsCache,
  clearDepsCache,
};
