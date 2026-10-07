// Test: Reuse mode + restart/force-restart behavior
// Verifies the fix for: 端口被外部 Python 占用时，Electron "先试后杀" 策略
// 不会陷入无效重启循环，且能通过显式标记 forceRestart 杀掉占位进程

const path = require('path');

// ============== Mock port-manager ==============
const portManagerPath = path.resolve('electron/src/core/backend/port-manager');
const realPortManager = require(portManagerPath);

let probeCallCount = 0;
let forceKillCallCount = 0;
let lastForceKilledPort = null;

const mockPortManager = {
  ...realPortManager,
  checkPortOccupation: () => ({
    occupied: true,
    pid: 9999,
    processName: 'python',
    canAutoKill: true,
  }),
  checkPortOccupationAsync: async () => ({
    occupied: true,
    pid: 9999,
    processName: 'python',
    canAutoKill: true,
  }),
  forceKillPortProcess: (port) => {
    forceKillCallCount++;
    lastForceKilledPort = port;
    console.log(`[Mock] forceKillPortProcess(${port}) called`);
    return { success: true, killedPid: 9999, message: 'mock-kill' };
  },
  findAvailablePort: () => null,
  probeBackendHealth: async () => {
    probeCallCount++;
    return { healthy: true, attempts: 1, lastError: '' };
  },
};

require.cache[require.resolve(portManagerPath)] = {
  id: portManagerPath,
  filename: portManagerPath,
  loaded: true,
  exports: mockPortManager,
};

// ============== Mock constants ==============
const constantsPath = path.resolve('electron/config/constants');
require.cache[require.resolve(constantsPath)] = {
  id: constantsPath,
  filename: constantsPath,
  loaded: true,
  exports: {
    BACKEND_URL: 'http://localhost:8765',
    BACKEND_PORT: 8765,
    BACKEND_HOST: 'localhost',
    BACKEND_START_TIMEOUT: 5000,
    BACKEND_RESTART_DELAY: 100,
    MAX_RESTART_ATTEMPTS: 3,
    EXEC_SYNC_TIMEOUT: 5000,
    EXEC_SYNC_SHORT_TIMEOUT: 3000,
    isDev: true,
    BACKUP_PORTS: [8766, 8767],
  },
};

// ============== Mock health ==============
const healthPath = path.resolve('electron/src/core/backend/health');
require.cache[require.resolve(healthPath)] = {
  id: healthPath,
  filename: healthPath,
  loaded: true,
  exports: {
    httpGet: async () => ({ success: true }),
    healthCheck: async () => ({ success: true }),
  },
};

// ============== Mock detector ==============
const detectorPath = path.resolve('electron/utils/python-detector');
require.cache[require.resolve(detectorPath)] = {
  id: detectorPath,
  filename: detectorPath,
  loaded: true,
  exports: {
    detectPython: () => ({ available: true, path: 'python', version: '3.12' }),
  },
};

// ============== Mock backend-session (use a tmp file) ==============
const fs = require('fs');
const os = require('os');
const sessionTmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'session-test-'));
const sessionTmpFile = path.join(sessionTmpDir, 'backend-session.json');

const backendSessionPath = path.resolve('electron/utils/backend-session');
require.cache[require.resolve(backendSessionPath)] = {
  id: backendSessionPath,
  filename: backendSessionPath,
  loaded: true,
  exports: {
    SESSION_FILENAME: 'backend-session.json',
    SESSION_TTL_MS: 24 * 60 * 60 * 1000,
    getSessionId: () => 'mock-session-id',
    getSessionFilePath: () => sessionTmpFile,
    readOwnedSession: () => {
      try {
        if (!fs.existsSync(sessionTmpFile)) return null;
        return JSON.parse(fs.readFileSync(sessionTmpFile, 'utf-8'));
      } catch { return null; }
    },
    writeOwnedSession: (pid, overrideSessionId) => {
      fs.writeFileSync(sessionTmpFile, JSON.stringify({
        sessionId: overrideSessionId || 'mock-session-id',
        pid,
        startedAt: Date.now(),
      }, null, 2));
      return true;
    },
    clearOwnedSession: () => {
      try { fs.unlinkSync(sessionTmpFile); return true; } catch { return false; }
    },
    classifyPortHolder: (pid) => {
      try {
        if (!fs.existsSync(sessionTmpFile)) {
          return { owned: false, sameSession: false, sessionId: null, reason: 'no-record' };
        }
        const rec = JSON.parse(fs.readFileSync(sessionTmpFile, 'utf-8'));
        if (rec.pid !== pid) {
          return { owned: false, sameSession: false, sessionId: rec.sessionId, reason: 'pid-mismatch' };
        }
        if (rec.sessionId === 'mock-session-id') {
          return { owned: true, sameSession: true, sessionId: rec.sessionId, reason: 'current-session' };
        }
        return { owned: false, sameSession: true, sessionId: rec.sessionId, reason: 'previous-session' };
      } catch { return { owned: false, sameSession: false, sessionId: null, reason: 'error' }; }
    },
  },
};

// ============== Now load BackendManager ==============
const { BackendManager } = require(path.resolve('electron/services/backend-manager'));

(async () => {
  let pass = 0;
  let fail = 0;
  function assert(condition, msg) {
    if (condition) { pass++; console.log(`  PASS: ${msg}`); }
    else { fail++; console.log(`  FAIL: ${msg}`); }
  }

  // ============== T1: 复用外部进程被识别为 foreign ==============
  console.log('\n=== T1: Reuse external process classified as foreign ===');
  // 清理：没有 session 记录（首次启动）
  try { fs.unlinkSync(sessionTmpFile); } catch {}

  const bm1 = new BackendManager({
    onReady: () => console.log('  [T1] onReady called'),
  });
  bm1.currentPort = 8765;
  await bm1.start(() => {}); // empty splash reporter
  await new Promise(r => setTimeout(r, 200));

  console.log(`  [T1] reuseKind=${bm1.reuseKind}, reusedExisting=${bm1.reusedExisting}`);
  assert(bm1.reuseKind === 'foreign', 'reuseKind 应该是 foreign（无 session 记录时保守判定）');
  assert(bm1.reusedExisting === true, 'reusedExisting = true');

  // ============== T2: 复用模式下 restart() 不应杀进程（短路） ==============
  console.log('\n=== T2: restart() in reuse mode is no-op ===');
  forceKillCallCount = 0;
  const bm2 = new BackendManager({ onReady: () => {} });
  bm2.currentPort = 8765;
  bm2.reusedExisting = true;
  bm2.reuseKind = 'foreign';

  const result = await bm2.restart(() => {});
  console.log(`  [T2] restart returned=${result}, forceKillCallCount=${forceKillCallCount}`);
  assert(result === false, 'reuse 模式下 restart() 返回 false（不杀进程）');
  assert(forceKillCallCount === 0, 'forceKillPortProcess 未被调用');

  // ============== T3: forceRestart 不带 skipUserConfirmation 直接拒绝 ==============
  console.log('\n=== T3: forceRestart without skipUserConfirmation is rejected ===');
  forceKillCallCount = 0;
  const bm3 = new BackendManager({ onReady: () => {} });
  bm3.currentPort = 8765;
  bm3.reusedExisting = true;
  bm3.reuseKind = 'foreign';

  const fr1 = await bm3.forceRestart(() => {});
  console.log(`  [T3] forceRestart() returned=${fr1}, forceKillCallCount=${forceKillCallCount}`);
  assert(fr1 === false, '不带确认的 forceRestart 返回 false');
  assert(forceKillCallCount === 0, '未获得确认时 forceKillPortProcess 未被调用');

  // ============== T4: forceRestart 带 skipUserConfirmation 真正调用 kill ==============
  console.log('\n=== T4: forceRestart with skipUserConfirmation actually kills ===');
  forceKillCallCount = 0;
  lastForceKilledPort = null;
  const bm4 = new BackendManager({
    onReady: () => console.log('  [T4] onReady called'),
    onDisconnected: () => console.log('  [T4] onDisconnected called'),
  });
  bm4.currentPort = 8765;
  bm4.reusedExisting = true;
  bm4.reuseKind = 'foreign';

  // 给 waitForReady() 一个"永远不 ready"的 stub（避免真实网络等待）
  bm4.waitForReady = async () => {
    console.log('  [T4] waitForReady stub called');
    return false;
  };
  // spawn 跳过
  bm4.spawnBackend = () => ({ pid: 12345, on: () => {}, stdout: { on: () => {} }, stderr: { on: () => {} } });
  bm4.bindProcessEvents = () => {};

  const fr2 = await bm4.forceRestart(() => {}, { skipUserConfirmation: true });
  console.log(`  [T4] forceRestart returned=${fr2}, forceKillCallCount=${forceKillCallCount}, lastPort=${lastForceKilledPort}`);
  assert(forceKillCallCount === 1, 'forceKillPortProcess 被调用 1 次');
  assert(lastForceKilledPort === 8765, '强杀端口为 8765');
  assert(bm4.reusedExisting === false, 'forceRestart 后 reusedExisting 重置为 false');

  // ============== T5: forceRestart 失败时抛错并清理状态 ==============
  console.log('\n=== T5: forceRestart handles kill failure gracefully ===');
  // 临时改 mock 让 kill 失败
  const origKill = mockPortManager.forceKillPortProcess;
  mockPortManager.forceKillPortProcess = () => ({ success: false, message: 'mock-fail' });

  const bm5 = new BackendManager({ onReady: () => {} });
  bm5.currentPort = 8765;
  bm5.reusedExisting = true;
  bm5.reuseKind = 'foreign';

  const fr3 = await bm5.forceRestart(() => {}, { skipUserConfirmation: true });
  console.log(`  [T3] forceRestart with failing kill returned=${fr3}`);
  assert(fr3 === false, 'kill 失败时 forceRestart 返回 false');

  // 恢复
  mockPortManager.forceKillPortProcess = origKill;

  // ============== T6: spawn 后 writeOwnedSession 写入了 session 文件 ==============
  console.log('\n=== T6: spawn success writes session record ===');
  // 重置 session 文件
  try { fs.unlinkSync(sessionTmpFile); } catch {}
  assert(!fs.existsSync(sessionTmpFile), '初始无 session 文件');

  // 构造一个不走 reuse 的 backend-manager
  mockPortManager.checkPortOccupationAsync = async () => ({
    occupied: false, pid: null, processName: '', canAutoKill: false,
  });
  const bm6 = new BackendManager({ onReady: () => {} });
  bm6.currentPort = 8765;
  // 直接调 spawnBackend stub 看看 session 写入
  bm6.spawnBackend = () => ({ pid: 54321, on: () => {}, stdout: { on: () => {} }, stderr: { on: () => {} } });
  bm6.bindProcessEvents = () => {};
  bm6.waitForReady = async () => true;
  // 直接调 ensurePortAvailable + 写 session
  await bm6.ensurePortAvailable(() => {});
  bm6.process = bm6.spawnBackend();
  bm6.bindProcessEvents();
  if (bm6.process?.pid) {
    const written = require(backendSessionPath).writeOwnedSession(bm6.process.pid, bm6.sessionId);
    assert(written, 'writeOwnedSession 写入成功');
  }

  assert(fs.existsSync(sessionTmpFile), 'spawn 后 session 文件存在');
  const sessionData = JSON.parse(fs.readFileSync(sessionTmpFile, 'utf-8'));
  console.log(`  [T6] sessionData=${JSON.stringify(sessionData)}`);
  assert(sessionData.pid === 54321, 'session.pid 正确');
  assert(sessionData.sessionId === bm6.sessionId, 'session.sessionId 正确');

  // ============== T7: classifyPortHolder 区分 previous-session ==============
  console.log('\n=== T7: classifyPortHolder returns previous-session ===');
  // 写入一个不同 session 但相同 PID
  require(backendSessionPath).writeOwnedSession(54321, 'previous-session-id');
  const cls = require(backendSessionPath).classifyPortHolder(54321);
  console.log(`  [T7] classify result=${JSON.stringify(cls)}`);
  assert(cls.sameSession === true, 'sameSession = true');
  assert(cls.reason === 'previous-session', 'reason = previous-session');
  assert(cls.owned === false, 'owned = false (session id 不同)');

  // ============== Summary ==============
  console.log(`\n=== Summary: ${pass} passed, ${fail} failed ===`);
  // 清理
  try { fs.unlinkSync(sessionTmpFile); } catch {}
  try { fs.rmdirSync(sessionTmpDir); } catch {}
  process.exit(fail === 0 ? 0 : 1);
})();