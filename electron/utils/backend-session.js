/**
 * 后端会话归属管理
 *
 * 目的：识别端口 8000 上的进程是否由本 Electron 会话启动。
 *   - ownPrevious：上一会话遗留的 MatuX 后端（session 一致但 Electron 重启了），可放心接管或替换
 *   - foreign：外部进程（用户手动启动 / 别的程序），需走"用户确认"路径
 *
 * 设计：
 *   - 文件位置：app.getPath('userData')/backend-session.json
 *   - 内容：{ sessionId, pid, startedAt }
 *   - sessionId：每次 Electron 启动生成新的 UUID
 *   - PID：spawn 成功后写入
 *   - 写入：写临时文件 + rename 原子替换（防并发损坏）
 *   - 失效：超过 24h 的记录视为过期（防止幽灵文件干扰判定）
 *
 * @module backend-session
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const SESSION_FILENAME = 'backend-session.json';
const SESSION_TTL_MS = 24 * 60 * 60 * 1000; // 24 小时

let _cachedSessionId = null;

/**
 * 生成/获取本次 Electron 启动的 sessionId
 * 进程内首次访问时生成 UUID，后续复用同一值
 * @returns {string}
 */
function getSessionId() {
  if (_cachedSessionId) return _cachedSessionId;
  try {
    const { randomUUID } = require('crypto');
    _cachedSessionId = randomUUID();
  } catch {
    // crypto 不可用时的兜底（极端环境）
    _cachedSessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }
  return _cachedSessionId;
}

/**
 * 获取 session 文件的绝对路径
 * 优先 userData，回退到系统临时目录
 */
function getSessionFilePath() {
  try {
    const { app } = require('electron');
    if (app && app.isReady && app.isReady() && typeof app.getPath === 'function') {
      return path.join(app.getPath('userData'), SESSION_FILENAME);
    }
  } catch { /* electron 未就绪或非主进程 */ }
  return path.join(os.tmpdir(), `imatuproject-${SESSION_FILENAME}`);
}

/**
 * 读取当前持久化的 session 记录
 * 过期或损坏返回 null
 * @returns {{ sessionId: string, pid: number, startedAt: number } | null}
 */
function readOwnedSession() {
  const filePath = getSessionFilePath();
  try {
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, 'utf-8');
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    if (typeof parsed.sessionId !== 'string') return null;
    if (typeof parsed.pid !== 'number') return null;
    if (typeof parsed.startedAt !== 'number') return null;
    if (Date.now() - parsed.startedAt > SESSION_TTL_MS) return null;
    return parsed;
  } catch (err) {
    console.warn('[WARN] session 记录读取失败:', err.message);
    return null;
  }
}

/**
 * 写入 session 记录（原子 rename）
 * @param {number} pid 后端进程 PID
 * @param {string} [overrideSessionId] 可选：覆盖 sessionId（默认用 getSessionId）
 */
function writeOwnedSession(pid, overrideSessionId) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  const sessionId = overrideSessionId || getSessionId();
  const filePath = getSessionFilePath();
  const dir = path.dirname(filePath);
  const tmpPath = path.join(dir, `${SESSION_FILENAME}.tmp.${process.pid}`);
  const payload = JSON.stringify({
    sessionId,
    pid,
    startedAt: Date.now(),
  }, null, 2);

  try {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(tmpPath, payload, 'utf-8');
    fs.renameSync(tmpPath, filePath); // 原子替换
    return true;
  } catch (err) {
    console.warn('[WARN] session 记录写入失败:', err.message);
    // 清理临时文件
    try { if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath); } catch { /* ignore */ }
    return false;
  }
}

/**
 * 清除 session 记录（Electron 正常退出时调用）
 */
function clearOwnedSession() {
  const filePath = getSessionFilePath();
  try {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    return true;
  } catch (err) {
    console.warn('[WARN] session 记录清理失败:', err.message);
    return false;
  }
}

/**
 * 判定指定 PID 是否由本会话（或曾经会话）拥有
 *   - sameSession=true：sessionId 完全匹配，可能是上一会话遗留
 *   - sameSession=false：sessionId 不匹配，是外部进程
 * @param {number} pid
 * @returns {{ owned: boolean, sameSession: boolean, sessionId: string|null, reason: string }}
 */
function classifyPortHolder(pid) {
  const record = readOwnedSession();
  if (!record) {
    return { owned: false, sameSession: false, sessionId: null, reason: 'no-record' };
  }
  if (record.pid !== pid) {
    return {
      owned: false,
      sameSession: false,
      sessionId: record.sessionId,
      reason: 'pid-mismatch',
    };
  }
  // PID 匹配，进一步看 sessionId
  const currentSessionId = getSessionId();
  if (record.sessionId === currentSessionId) {
    return {
      owned: true,
      sameSession: true,
      sessionId: record.sessionId,
      reason: 'current-session',
    };
  }
  return {
    owned: false,
    sameSession: true, // 同一 session 残留（同 workspace 同 pid）
    sessionId: record.sessionId,
    reason: 'previous-session',
  };
}

module.exports = {
  getSessionId,
  getSessionFilePath,
  readOwnedSession,
  writeOwnedSession,
  clearOwnedSession,
  classifyPortHolder,
  SESSION_FILENAME,
  SESSION_TTL_MS,
};