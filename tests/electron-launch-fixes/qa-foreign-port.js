// QA 脚本：手动启动 Python 占 8000，验证 app-initializer 不再循环
//
// 用法：
//   1. 先手动启 Python 占 8000：python -m http.server 8000
//   2. 然后跑：node tests/electron-launch-fixes/qa-foreign-port.js
//
// 验证目标：
//   - checkPortOccupation 探测出外部进程（PID）
//   - BackendManager 启动时 classifyPortHolder 标记为 foreign
//   - reuseKind === 'foreign'
//   - reusedExisting === true
//   - 重复调用 restart() 不会触发 forceKill（验证短路）

const path = require('path');
const realPortManager = require(path.resolve('electron/src/core/backend/port-manager'));
const realSession = require(path.resolve('electron/utils/backend-session'));

// 实际 BackendManager（不 mock 端口管理器，确保真实探测）
// 需要 mock 掉 spawn / health-check 等副作用
const portManagerPath = path.resolve('electron/src/core/backend/port-manager');
const constantsPath = path.resolve('electron/config/constants');
const detectorPath = path.resolve('electron/utils/python-detector');
const healthPath = path.resolve('electron/src/core/backend/health');

// constants.js 在裸 node 下访问 electron.app.getPath 会抛错；
// 这里提供一个运行时替身让 constants.js 能加载。
require.cache[require.resolve(constantsPath)] = {
  id: constantsPath,
  filename: constantsPath,
  loaded: true,
  exports: {
    BACKEND_URL: 'http://localhost:8000',
    BACKEND_PORT: 8000,
    BACKEND_HOST: 'localhost',
    BACKEND_START_TIMEOUT: 5000,
    BACKEND_RESTART_DELAY: 100,
    MAX_RESTART_ATTEMPTS: 3,
    HEALTH_CHECK_INTERVAL: 10000,
    HEALTH_CHECK_DETAIL_INTERVAL: 5000,
    MODULE_STATUS_INTERVAL: 5000,
    SPLASH_RENDER_DELAY: 0,
    HTTP_REQUEST_TIMEOUT: 3000,
    PORT_WAIT_INTERVAL: 500,
    EXEC_SYNC_TIMEOUT: 5000,
    EXEC_SYNC_SHORT_TIMEOUT: 3000,
    EXEC_SYNC_PIP_TIMEOUT: 15000,
    TIER1_PRELOAD_TIMEOUT: 5000,
    MAX_FILE_SIZE: 1024 * 1024,
    HEALTH_URL: 'http://localhost:8000/health',
    HEALTH_DETAIL_URL: 'http://localhost:8000/api/v1/system/health-detail',
    MODULES_URL: 'http://localhost:8000/api/v1/system/modules',
    isDev: true,
    isProduction: false,
    isProductionLike: false,
    BACKUP_PORTS: [8001, 8002, 8003, 8080, 3001],
    WINDOW_STATE_FILE: path.join(require('os').tmpdir(), 'window-state.json'),
    DEFAULT_WINDOW_SIZE: { width: 1400, height: 900, minWidth: 1024, minHeight: 768 },
    SPLASH_WINDOW_SIZE: { width: 480, height: 320 },
    APP_PATHS: { icon: '', resources: require('os').tmpdir() },
  },
};

// 接管 detector，避免真实 spawn
require.cache[require.resolve(detectorPath)] = {
  id: detectorPath,
  filename: detectorPath,
  loaded: true,
  exports: {
    detectPython: () => ({ available: true, path: 'python', version: '3.12' }),
  },
};

// 接管 health，避免真实 HTTP 请求
require.cache[require.resolve(healthPath)] = {
  id: healthPath,
  filename: healthPath,
  loaded: true,
  exports: {
    httpGet: async () => ({ success: true, body: '{"status":"healthy"}' }),
    healthCheck: async () => ({ success: true }),
  },
};

const { BackendManager } = require(path.resolve('electron/services/backend-manager'));

(async () => {
  let pass = 0;
  let fail = 0;
  function assert(condition, msg) {
    if (condition) { pass++; console.log(`  PASS: ${msg}`); }
    else { fail++; console.log(`  FAIL: ${msg}`); }
  }

  // ============== QA-1: 真实探测端口 8000 ==============
  console.log('\n=== QA-1: 真实探测端口 8000 ===');
  const port = 8000;
  const occ = await realPortManager.checkPortOccupationAsync(port);
  console.log(`  [QA-1] checkPortOccupationAsync(${port}):`, JSON.stringify(occ));
  assert(occ.occupied === true, '端口 8000 被占用（外部 Python 已起）');
  assert(typeof occ.pid === 'number' && occ.pid > 0, `占用进程 PID 有效（${occ.pid}）`);
  assert(occ.processName && occ.processName.toLowerCase().includes('python'), `进程名含 python（${occ.processName}）`);

  // ============== QA-2: 真实 BackendManager 启动应判定为 foreign ==============
  console.log('\n=== QA-2: BackendManager 启动后判定 reuseKind ===');
  // 清理 session 记录确保是首次判定
  realSession.clearOwnedSession();

  const bm = new BackendManager({
    onReady: () => console.log('  [QA-2] onReady called'),
    onDisconnected: () => console.log('  [QA-2] onDisconnected called'),
  });
  bm.currentPort = port;

  // stub waitForReady：避免真实 HTTP 等待
  bm.waitForReady = async () => false;
  // stub spawnBackend：避免真实 spawn
  bm.spawnBackend = () => null;

  await bm.start(() => {});
  await new Promise((r) => setTimeout(r, 300));

  console.log(`  [QA-2] reuseKind=${bm.reuseKind}, reusedExisting=${bm.reusedExisting}, process=${bm.process?.pid}`);
  assert(bm.reuseKind === 'foreign', `reuseKind === 'foreign'（实际=${bm.reuseKind}）`);
  assert(bm.reusedExisting === true, 'reusedExisting === true');
  assert(bm.process === null, 'process === null（复用模式不持有 process）');

  // ============== QA-3: 反复调 restart() 不触发 kill ==============
  console.log('\n=== QA-3: 复用模式下 restart() 反复调用不触发 kill ===');
  let killAttempts = 0;
  const origKill = realPortManager.forceKillPortProcess;
  realPortManager.forceKillPortProcess = (p) => {
    killAttempts++;
    console.log(`  [QA-3] forceKillPortProcess(${p}) 被调用`);
    return { success: false, message: 'should-not-be-called-in-reuse-mode' };
  };
  // 重新 require BackendManager 让其使用 mocked portManager
  // （上面 bm 已经 require 过，新 mock 在 module.exports 上覆盖即可）

  for (let i = 0; i < 5; i++) {
    const r = await bm.restart(() => {});
    console.log(`  [QA-3] restart #${i + 1} returned=${r}`);
  }
  assert(killAttempts === 0, `forceKillPortProcess 未被调用（实际=${killAttempts}，循环被打破）`);

  realPortManager.forceKillPortProcess = origKill;

  // ============== QA-4: forceRestart 必须显式确认才执行 kill ==============
  console.log('\n=== QA-4: forceRestart 必须 skipUserConfirmation=true 才生效 ===');
  let killAttempts2 = 0;
  realPortManager.forceKillPortProcess = (p) => {
    killAttempts2++;
    console.log(`  [QA-4] forceKillPortProcess(${p}) 被调用`);
    return { success: true, killedPid: occ.pid };
  };

  const frNoConfirm = await bm.forceRestart(() => {});
  console.log(`  [QA-4] forceRestart(no confirm) returned=${frNoConfirm}`);
  assert(frNoConfirm === false, '无确认时 forceRestart 直接返回 false');
  assert(killAttempts2 === 0, '无确认时未尝试 kill');

  // 注：带 skipUserConfirmation 的真实验证需要真杀外部进程，会影响后续手动 QA。
  // 此处仅校验分支判断，真实 kill 路径已由单元测试覆盖（T4/T5）。

  // ============== Summary ==============
  console.log(`\n=== QA Summary: ${pass} passed, ${fail} failed ===`);
  console.log(`(外部 Python PID ${occ.pid} 仍占用端口 8000，请手动结束: taskkill /PID ${occ.pid} /F)`);
  process.exit(fail === 0 ? 0 : 1);
})();
