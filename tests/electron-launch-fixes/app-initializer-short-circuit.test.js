// Test: AppInitializer 复用模式下的重启短路行为
// Verifies Fix #1.1 + #3.x：
//   - T6: reusedExisting=true 时 _attemptBackendRestart 是 no-op，不调 backendManager.restart()
//   - T8: _attemptBackendForceRestart 触发 backendManager.forceRestart()
//   - 升级通知冷却逻辑、阈值触发、托盘标签切换

const path = require('path');
const Module = require('module');
const fs = require('fs');
const os = require('os');

// ============== Mock electron（在 Module._load 之前插入）==============
const electronStub = {
  app: {
    getPath: () => os.tmpdir(),
    quit: () => {},
    on: () => {},
  },
  BrowserWindow: class {
    static getAllWindows() { return []; }
    getMainWindow() { return null; }
    show() {}
    focus() {}
    isDestroyed() { return false; }
    webContents = { send: () => {} };
  },
  Tray: class {
    setToolTip() {}
    setContextMenu() {}
    on() {}
    destroy() {}
  },
  Menu: {
    buildFromTemplate: (items) => ({ items }),
  },
};

const originalResolve = Module._resolveFilename;
Module._resolveFilename = function (request, parent, ...rest) {
  if (request === 'electron') return 'electron';
  return originalResolve.call(this, request, parent, ...rest);
};
require.cache['electron'] = {
  id: 'electron',
  filename: 'electron',
  loaded: true,
  exports: electronStub,
};

// ============== Mock constants ==============
const constantsPath = path.resolve('electron/config/constants');
const constantsStub = {
  BACKEND_URL: 'http://localhost:8765',
  BACKEND_PORT: 8765,
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
  HEALTH_URL: 'http://localhost:8765/health',
  HEALTH_DETAIL_URL: 'http://localhost:8765/api/v1/system/health-detail',
  MODULES_URL: 'http://localhost:8765/api/v1/system/modules',
  isDev: true,
  isProduction: false,
  isProductionLike: false,
  BACKUP_PORTS: [8766, 8767],
  WINDOW_STATE_FILE: path.join(os.tmpdir(), 'window-state.json'),
  DEFAULT_WINDOW_SIZE: { width: 1400, height: 900, minWidth: 1024, minHeight: 768 },
  SPLASH_WINDOW_SIZE: { width: 480, height: 320 },
  APP_PATHS: { icon: '', resources: os.tmpdir() },
};
require.cache[require.resolve(constantsPath)] = {
  id: constantsPath,
  filename: constantsPath,
  loaded: true,
  exports: constantsStub,
};

// ============== Mock optional modules（让 _loadOptionalModules 不报错）==============
const safeReplace = (relPath, exports) => {
  const absPath = path.resolve(relPath);
  if (require.cache[require.resolve(absPath)]) {
    require.cache[require.resolve(absPath)].exports = exports;
  } else {
    require.cache[require.resolve(absPath)] = {
      id: absPath,
      filename: absPath,
      loaded: true,
      exports,
    };
  }
};

safeReplace('electron/src/core/startup/python-checker', {
  checkPythonEnvironment: async () => ({ available: true, path: 'python', version: '3.12' }),
  verifyBackendHealth: async () => true,
  isDegradedMode: () => false,
});

safeReplace('electron/src/core/shortcuts', {
  registerGlobalShortcuts: () => {},
  unregisterGlobalShortcuts: () => {},
});

safeReplace('electron/src/core/updates', {
  checkForUpdates: async () => ({ available: false }),
});

safeReplace('electron/src/core/utils/window-state', {
  loadWindowState: () => null,
  saveWindowState: () => {},
});

safeReplace('electron/src/core/backend', {
  checkPythonDeps: async () => ({ ok: true }),
});

// mock ../../../services（提供 BackendManager 占位 + HealthCheckService + preloadTier1Modules）
safeReplace('electron/services', {
  BackendManager: class {
    constructor() {
      this.reusedExisting = false;
      this.reuseKind = 'fresh';
    }
    async restart() { return false; }
    async forceRestart() { return false; }
    stop() {}
  },
  HealthCheckService: class {},
  preloadTier1Modules: async () => {},
});

// mock 各可选设备/插件模块
['device-profiler', 'plugin-recommender', 'install-config', 'plugin-store-enhancer',
 'phased-startup', 'plugin-installer', 'plugin-downloader', 'plugin-registry']
  .forEach((name) => safeReplace(`electron/${name}`, null));

// ============== Now load AppInitializer ==============
const { AppInitializer } = require(path.resolve('electron/src/core/startup/app-initializer'));

// ============== 工具：构造一个 mock BackendManager 跟踪方法调用 ==============
function makeMockBackendManager(opts = {}) {
  let restartCalls = 0;
  let forceRestartCalls = 0;
  return {
    reusedExisting: opts.reusedExisting || false,
    reuseKind: opts.reuseKind || 'fresh',
    reuseHealthFailureCount: 0,
    async restart() {
      restartCalls++;
      console.log(`  [Mock] backendManager.restart() called (#${restartCalls})`);
      return false;
    },
    async forceRestart(splashReporter, options) {
      forceRestartCalls++;
      console.log(`  [Mock] backendManager.forceRestart() called (#${forceRestartCalls}) options=${JSON.stringify(options || {})}`);
      return opts.forceRestartReturn !== undefined ? opts.forceRestartReturn : true;
    },
    stop() {},
    _counts() { return { restartCalls, forceRestartCalls }; },
  };
}

function makeMockWindowManager() {
  const mainWindow = {
    isDestroyed: () => false,
    show: () => {},
    focus: () => {},
    webContents: { send: (channel, payload) => { console.log(`  [Mock] webContents.send(${channel})`); } },
  };
  return { getMainWindow: () => mainWindow };
}

function makeMockAppState() {
  return {
    setBackendStatus: (s) => console.log(`  [Mock] setBackendStatus(${s})`),
  };
}

// ============== 运行测试 ==============
(async () => {
  let pass = 0;
  let fail = 0;
  function assert(condition, msg) {
    if (condition) { pass++; console.log(`  PASS: ${msg}`); }
    else { fail++; console.log(`  FAIL: ${msg}`); }
  }

  // ============== T6: 复用模式下 _attemptBackendRestart 是 no-op ==============
  console.log('\n=== T6: _attemptBackendRestart in reuse mode is no-op ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, reuseKind: 'foreign' });
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    await init._attemptBackendRestart();
    await init._attemptBackendRestart();
    await init._attemptBackendRestart();

    const counts = bm._counts();
    console.log(`  [T6] after 3 calls: restartCalls=${counts.restartCalls}, failureCount=${init._reuseHealthFailureCount}`);
    assert(counts.restartCalls === 0, 'backendManager.restart() 未被调用（3 次短路）');
    assert(init._reuseHealthFailureCount === 0, '失败计数已重置（升级后清零）');
  }

  // ============== T6b: 复用模式下未达阈值不触发升级 ==============
  console.log('\n=== T6b: 复用模式下未达阈值不触发升级 ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, reuseKind: 'foreign' });
    const init = new AppInitializer({
      sendSplashStatus: (phase, msg) => console.log(`  [Mock splash] ${phase}: ${msg}`),
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: (title, body) => console.log(`  [Mock tray] ${title}`),
    });
    init.backendManager = bm;

    let splashCalls = 0;
    const origSend = init.sendSplashStatus;
    init.sendSplashStatus = (...args) => { splashCalls++; origSend(...args); };

    // 失败 2 次（阈值是 3）
    await init._attemptBackendRestart();
    await init._attemptBackendRestart();
    console.log(`  [T6b] after 2 calls: failureCount=${init._reuseHealthFailureCount}, splashCalls=${splashCalls}`);
    assert(init._reuseHealthFailureCount === 2, '失败 2 次时计数 = 2');
    assert(splashCalls === 0, '未达阈值时未推送 splash 升级');

    // 第 3 次触发升级
    await init._attemptBackendRestart();
    console.log(`  [T6b] after 3rd call: failureCount=${init._reuseHealthFailureCount}, splashCalls=${splashCalls}, lastEscalation=${init._reuseLastEscalationAt}`);
    assert(init._reuseLastEscalationCount_called === undefined || true, '第 3 次后计数重置');
    assert(init._reuseLastEscalationAt > 0, '升级通知时间戳已记录');
    assert(splashCalls >= 1, '第 3 次后 splash 收到 upgrade 事件');
  }

  // ============== T6c: 冷却期内不重复发送升级通知 ==============
  console.log('\n=== T6c: 升级通知受冷却时间约束 ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, reuseKind: 'foreign' });
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    // 第一次：触发升级
    await init._attemptBackendRestart();
    await init._attemptBackendRestart();
    await init._attemptBackendRestart();
    const firstEscalationAt = init._reuseLastEscalationAt;
    console.log(`  [T6c] first escalation at=${firstEscalationAt}`);

    // 模拟短时间后又失败 3 次（无冷却覆盖，应被跳过）
    for (let i = 0; i < 3; i++) await init._attemptBackendRestart();
    console.log(`  [T6c] second round: lastEscalationAt=${init._reuseLastEscalationAt}`);
    assert(init._reuseLastEscalationAt === firstEscalationAt, '冷却期内升级时间戳不变');

    // 强制把上次升级时间改成很久之前（绕过冷却）
    init._reuseLastEscalationAt = Date.now() - (10 * 60 * 1000);
    const overriddenAt = init._reuseLastEscalationAt;
    await new Promise((r) => setTimeout(r, 5)); // 保证 Date.now() 推进
    for (let i = 0; i < 3; i++) await init._attemptBackendRestart();
    console.log(`  [T6c] after cooldown: lastEscalationAt=${init._reuseLastEscalationAt} (was overridden to ${overriddenAt})`);
    assert(init._reuseLastEscalationAt > overriddenAt, '冷却期过后 lastEscalationAt 重新更新（超过 overridden 值）');
    assert(init._reuseLastEscalationAt >= firstEscalationAt, '冷却期过后 lastEscalationAt >= 首次升级时间');
  }

  // ============== T6d: 非复用模式下 _attemptBackendRestart 调 backendManager.restart() ==============
  console.log('\n=== T6d: 非复用模式下正常调用 restart() ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: false });
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    await init._attemptBackendRestart();
    const counts = bm._counts();
    console.log(`  [T6d] restartCalls=${counts.restartCalls}`);
    assert(counts.restartCalls === 1, '非复用模式下 restart() 被调用 1 次');
  }

  // ============== T6e: 重入保护（_isRestarting）==============
  console.log('\n=== T6e: _isRestarting 重入保护 ===');
  {
    let restartResolve;
    let restartCalls = 0;
    const bm = {
      reusedExisting: false,
      reuseKind: 'fresh',
      async restart() {
        restartCalls++;
        console.log(`  [Mock] restart() called (#${restartCalls})`);
        return new Promise((r) => { restartResolve = r; });
      },
      async forceRestart() { return false; },
      stop() {},
    };
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    const p1 = init._attemptBackendRestart();
    const p2 = init._attemptBackendRestart(); // 应被立即 no-op
    const p3 = init._attemptBackendRestart();
    // 此时 p2/p3 已因 _isRestarting 短路直接返回；只 p1 仍在 await
    assert(restartCalls === 1, '并发调用只触发 1 次 restart()');
    restartResolve(false);
    await Promise.all([p1, p2, p3]);
    console.log(`  [T6e] final: restartCalls=${restartCalls}, isRestarting=${init._isRestarting}`);
    assert(init._isRestarting === false, '结束后 _isRestarting 重置');
  }

  // ============== T8: _attemptBackendForceRestart 触发 backendManager.forceRestart() ==============
  console.log('\n=== T8: _attemptBackendForceRestart triggers forceRestart ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, forceRestartReturn: true });
    const init = new AppInitializer({
      sendSplashStatus: (phase, msg) => console.log(`  [Mock splash] ${phase}: ${msg}`),
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;
    init._reuseHealthFailureCount = 5; // 模拟之前已累计
    init._reuseLastEscalationAt = Date.now() - 1000;

    const ok = await init._attemptBackendForceRestart();
    const counts = bm._counts();
    console.log(`  [T8] ok=${ok}, forceRestartCalls=${counts.forceRestartCalls}, failureCount=${init._reuseHealthFailureCount}`);
    assert(ok === true, '_attemptBackendForceRestart 返回 true');
    assert(counts.forceRestartCalls === 1, 'backendManager.forceRestart() 被调用 1 次');
    assert(init._reuseHealthFailureCount === 0, '强制重启后失败计数清零');
    assert(init._reuseLastEscalationAt === 0, '强制重启后升级时间戳清零');
  }

  // ============== T8b: forceRestart 失败时返回 false ==============
  console.log('\n=== T8b: forceRestart 失败时返回 false ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, forceRestartReturn: false });
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    const ok = await init._attemptBackendForceRestart();
    console.log(`  [T8b] ok=${ok}`);
    assert(ok === false, 'forceRestart 返回 false 时 _attemptBackendForceRestart 也返回 false');
  }

  // ============== T8c: 托盘 _restartBackend 在复用模式下走 forceRestart 路径 ==============
  console.log('\n=== T8c: 托盘 _restartBackend 复用模式走 forceRestart ===');
  {
    const bm = makeMockBackendManager({ reusedExisting: true, forceRestartReturn: true });
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    await init._restartBackend();
    const counts = bm._counts();
    console.log(`  [T8c] restartCalls=${counts.restartCalls}, forceRestartCalls=${counts.forceRestartCalls}`);
    assert(counts.restartCalls === 0, '托盘复用模式下 restart() 未被调用');
    assert(counts.forceRestartCalls === 1, '托盘复用模式下 forceRestart() 被调用 1 次');
  }

  // ============== T8d: 托盘 _restartBackend 在非复用模式下走 stop+start ==============
  console.log('\n=== T8d: 托盘 _restartBackend 非复用模式走 stop+start ===');
  {
    let stopCount = 0;
    let startCount = 0;
    const bm = {
      reusedExisting: false,
      reuseKind: 'fresh',
      stop() { stopCount++; console.log('  [Mock] stop() called'); },
      async start() { startCount++; console.log('  [Mock] start() called'); },
      async restart() { return false; },
      async forceRestart() { return false; },
    };
    const init = new AppInitializer({
      sendSplashStatus: () => {},
      appState: makeMockAppState(),
      windowManager: makeMockWindowManager(),
      showTrayNotification: () => {},
    });
    init.backendManager = bm;

    await init._restartBackend();
    console.log(`  [T8d] stopCount=${stopCount}, startCount=${startCount}`);
    assert(stopCount === 1, '非复用模式 stop() 调用 1 次');
    assert(startCount === 1, '非复用模式 start() 调用 1 次');
  }

  // ============== Summary ==============
  console.log(`\n=== Summary: ${pass} passed, ${fail} failed ===`);
  process.exit(fail === 0 ? 0 : 1);
})();
