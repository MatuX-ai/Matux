/**
 * 安装状态持久化模块
 * @module install-state
 *
 * 用于记录安装/首次启动时的用户选择（如"跳过 Python 安装"），
 * 跨会话保存到 app.getPath('userData')/install-state.json。
 *
 * 设计要点：
 * - 写入采用原子化重命名（tmp + rename），避免崩溃时损坏 JSON
 * - 读取失败一律返回默认安全值（不阻塞启动）
 * - 文件大小硬限制 64 KB（防止恶意文件炸内存）
 *
 * 【NSIS 集成】
 * 配套 NSIS 安装钩子：electron/build/installer.nsh
 * - NSIS 安装完成后弹窗，让用户选择"下载/指定路径/跳过"
 * - "指定路径"时把用户输入写到同目录下的 python-pending-path.txt（纯文本）
 * - 首次启动时由 consumePendingPythonPath() 读取并验证，
 *   通过后转写到 install-state.json 的 manualPythonPath 字段
 * - 验证失败时直接删除 pending 文件，不污染状态
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const INSTALL_STATE_FILENAME = 'install-state.json';
// NSIS 安装钩子写入的临时桥接文件（electron/build/installer.nsh）
// 文件路径：app.getPath('userData')/python-pending-path.txt
// 【格式】纯文本（一行 Windows 路径），不用 JSON 以避免反斜杠转义问题
const PENDING_PYTHON_PATH_FILENAME = 'python-pending-path.txt';
const MAX_FILE_BYTES = 64 * 1024; // 64 KB
// pending 文件单独限制：路径字符串不超过 4 KB（足够容纳任何合法 Windows 路径）
const PENDING_FILE_MAX_BYTES = 4 * 1024;

/**
 * 获取 install-state.json 路径
 * - 主进程：app.getPath('userData')
 * - 非主进程/测试：回落到临时目录
 */
function getInstallStatePath() {
  try {
    const { app } = require('electron');
    // 仅在 app 已 ready 时使用 userData（否则会抛错）
    if (app.isReady && app.isReady()) {
      return path.join(app.getPath('userData'), INSTALL_STATE_FILENAME);
    }
  } catch { /* electron 模块未加载或非主进程 */ }
  return path.join(os.tmpdir(), INSTALL_STATE_FILENAME);
}

/**
 * 读取安装状态（返回默认空对象，绝不抛错）
 * @returns {Object} 当前 install-state 对象
 */
function loadInstallState() {
  const filePath = getInstallStatePath();
  try {
    if (!fs.existsSync(filePath)) return {};
    const stat = fs.statSync(filePath);
    if (stat.size > MAX_FILE_BYTES) {
      console.warn(`[WARN] install-state.json 超过 ${MAX_FILE_BYTES} 字节，忽略`);
      return {};
    }
    const raw = fs.readFileSync(filePath, 'utf-8');
    const parsed = JSON.parse(raw);
    return (parsed && typeof parsed === 'object') ? parsed : {};
  } catch (err) {
    console.warn('[WARN] 读取 install-state.json 失败:', err.message);
    return {};
  }
}

/**
 * 原子化保存 install-state：先写 .tmp 再 rename，避免崩溃导致 JSON 损坏
 * @param {Object} state - 要保存的状态对象
 * @returns {boolean} 是否成功
 */
function saveInstallState(state) {
  if (!state || typeof state !== 'object') {
    console.warn('[WARN] saveInstallState: 入参不是对象');
    return false;
  }
  const filePath = getInstallStatePath();
  const tmpPath = `${filePath}.tmp`;
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2), 'utf-8');
    fs.renameSync(tmpPath, filePath);
    return true;
  } catch (err) {
    console.error('[ERROR] 保存 install-state.json 失败:', err.message);
    try { fs.unlinkSync(tmpPath); } catch { /* 清理失败不阻塞 */ }
    return false;
  }
}

/**
 * 是否曾跳过 Python 环境引导
 * @returns {boolean}
 */
function isPythonSkipped() {
  const state = loadInstallState();
  return state.pythonSkipped === true;
}

/**
 * 标记用户跳过了 Python 环境引导
 * @returns {boolean} 是否保存成功
 */
function markPythonSkipped() {
  const state = loadInstallState();
  state.pythonSkipped = true;
  state.skippedAt = Date.now();
  return saveInstallState(state);
}

/**
 * 清除跳过标记（用于：用户后续成功检测到 Python、或重新手动选择 Python 后清账）
 * @returns {boolean}
 */
function clearPythonSkipped() {
  const state = loadInstallState();
  if (state.pythonSkipped === undefined) return true;
  delete state.pythonSkipped;
  delete state.skippedAt;
  return saveInstallState(state);
}

/**
 * 消费 NSIS 安装钩子写入的 python-pending-path.txt
 * 【NSIS 集成】首次启动时调用一次：读取 pending 文件中的路径，
 * 保存到 install-state.json 的 manualPythonPath 字段，然后删除 pending 文件。
 *
 * 文件格式：纯文本（首行 = Windows 路径，可能含 \r\n 结束符）
 *
 * @param {Function} [validateFn] - 可选的路径验证函数（同步）：
 *   (pathStr) => { available: boolean, version: string, path: string, error?: string }
 *   若未提供或验证失败，pending 文件也会被删除（避免下次启动重复提示）
 * @returns {string|null} 验证通过的 Python 路径；无 pending 文件或验证失败返回 null
 */
function consumePendingPythonPath(validateFn) {
  let filePath;
  try {
    const { app } = require('electron');
    if (app.isReady && app.isReady()) {
      filePath = path.join(app.getPath('userData'), PENDING_PYTHON_PATH_FILENAME);
    }
  } catch { /* 非主进程或 app 未 ready */ }
  if (!filePath) {
    filePath = path.join(os.tmpdir(), PENDING_PYTHON_PATH_FILENAME);
  }

  // pending 文件不存在 → 正常情况，直接返回
  if (!fs.existsSync(filePath)) return null;

  // 读取纯文本路径（trim 处理可能的 \r\n 和首尾空白）
  let pendingPath = null;
  try {
    const stat = fs.statSync(filePath);
    if (stat.size > PENDING_FILE_MAX_BYTES) {
      console.warn(`[WARN] pending Python 路径文件超过 ${PENDING_FILE_MAX_BYTES} 字节，忽略并删除`);
      try { fs.unlinkSync(filePath); } catch { /* ignore */ }
      return null;
    }
    const raw = fs.readFileSync(filePath, 'utf-8').trim();
    if (raw && typeof raw === 'string') {
      pendingPath = raw;
    }
  } catch (err) {
    console.warn('[WARN] 读取 pending Python 路径失败:', err.message);
  }

  // 不管解析成功与否，先删除 pending 文件（一次性的桥接机制）
  try { fs.unlinkSync(filePath); } catch { /* 删除失败不阻塞 */ }

  if (!pendingPath) return null;

  // 执行验证（若提供了验证函数）
  if (typeof validateFn === 'function') {
    const result = validateFn(pendingPath);
    if (!result || !result.available) {
      console.warn(`[WARN] NSIS 写入的 Python 路径无效: ${pendingPath} (${result && result.error || 'unknown'})`);
      return null;
    }
    pendingPath = result.path || pendingPath;
  }

  // 持久化到 install-state.json
  const state = loadInstallState();
  state.manualPythonPath = pendingPath;
  state.manualPythonPathSetAt = Date.now();
  const saved = saveInstallState(state);
  if (!saved) {
    console.error('[ERROR] 保存 manualPythonPath 到 install-state.json 失败');
    return null;
  }

  console.log(`[INFO] 已消费 NSIS pending Python 路径并持久化: ${pendingPath}`);
  return pendingPath;
}

/**
 * 设置手动指定的 Python 路径（用于应用内"手动选择"流程）
 * @param {string} pythonPath - 验证通过的 python.exe 路径
 * @returns {boolean} 是否保存成功
 */
function setManualPythonPath(pythonPath) {
  if (!pythonPath || typeof pythonPath !== 'string') {
    console.warn('[WARN] setManualPythonPath: 入参不是合法字符串');
    return false;
  }
  const state = loadInstallState();
  state.manualPythonPath = pythonPath;
  state.manualPythonPathSetAt = Date.now();
  return saveInstallState(state);
}

/**
 * 获取手动指定的 Python 路径（持久化的优先路径）
 * @returns {string|null} 保存的路径；不存在返回 null
 */
function getManualPythonPath() {
  const state = loadInstallState();
  return typeof state.manualPythonPath === 'string' && state.manualPythonPath
    ? state.manualPythonPath
    : null;
}

/**
 * 清除手动指定的 Python 路径（用于"重置 Python 选择"场景）
 * @returns {boolean} 是否成功
 */
function clearManualPythonPath() {
  const state = loadInstallState();
  if (state.manualPythonPath === undefined) return true;
  delete state.manualPythonPath;
  delete state.manualPythonPathSetAt;
  return saveInstallState(state);
}

/**
 * 重置全部安装状态（用于：开发者手动清账或恢复出厂）
 */
function resetInstallState() {
  const filePath = getInstallStatePath();
  try {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    return true;
  } catch (err) {
    console.warn('[WARN] 重置 install-state.json 失败:', err.message);
    return false;
  }
}

module.exports = {
  INSTALL_STATE_FILENAME,
  PENDING_PYTHON_PATH_FILENAME,
  getInstallStatePath,
  loadInstallState,
  saveInstallState,
  isPythonSkipped,
  markPythonSkipped,
  clearPythonSkipped,
  consumePendingPythonPath,
  setManualPythonPath,
  getManualPythonPath,
  clearManualPythonPath,
  resetInstallState,
};