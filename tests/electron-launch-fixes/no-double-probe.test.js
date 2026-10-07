// Test: When reusing existing backend, no double-probe should occur
// Verifies Fix #5

const path = require('path');

// Mock port-manager module BEFORE backend-manager requires it
const portManagerPath = path.resolve('electron/src/core/backend/port-manager');
let probeCallCount = 0;
const realPortManager = require(portManagerPath);
const originalProbe = realPortManager.probeBackendHealth;

const mockPortManager = {
  ...realPortManager,
  checkPortOccupation: () => ({
    occupied: true,
    pid: 9999,
    processName: 'python',
    canAutoKill: true,
  }),
  forceKillPortProcess: () => ({ success: true }),
  findAvailablePort: () => null,
  probeBackendHealth: async function(port, options) {
    probeCallCount++;
    console.log(`[Mock] probeBackendHealth called (call #${probeCallCount})`);
    return { healthy: true, attempts: 1, lastError: '' };
  },
};

// Inject mock into require cache BEFORE backend-manager loads
require.cache[require.resolve(portManagerPath)] = {
  id: portManagerPath,
  filename: portManagerPath,
  loaded: true,
  exports: mockPortManager,
};

// Mock constants module
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
    BACKEND_RESTART_DELAY: 1000,
    MAX_RESTART_ATTEMPTS: 3,
    EXEC_SYNC_TIMEOUT: 5000,
    EXEC_SYNC_SHORT_TIMEOUT: 3000,
    isDev: true,
    BACKUP_PORTS: [8766, 8767],
  },
};

// Mock health module
const healthPath = path.resolve('electron/src/core/backend/health');
let healthCheckCallCount = 0;
const realHealth = require(healthPath);
require.cache[require.resolve(healthPath)] = {
  id: healthPath,
  filename: healthPath,
  loaded: true,
  exports: {
    ...realHealth,
    healthCheck: async function() {
      healthCheckCallCount++;
      console.log(`[Mock] healthCheck called (call #${healthCheckCallCount})`);
      return { success: true };
    },
  },
};

// Mock detector
const detectorPath = path.resolve('electron/src/core/backend/detector');
require.cache[require.resolve(detectorPath)] = {
  id: detectorPath,
  filename: detectorPath,
  loaded: true,
  exports: {
    detectPython: () => ({ available: true, path: 'python', version: '3.12' }),
  },
};

// Now load BackendManager
const { BackendManager } = require(path.resolve('electron/services/backend-manager'));

(async () => {
  let pass = 0;
  let fail = 0;
  function assert(condition, msg) {
    if (condition) { pass++; console.log(`  PASS: ${msg}`); }
    else { fail++; console.log(`  FAIL: ${msg}`); }
  }

  console.log('\n=== Test: Reuse scenario - no double-probe ===');

  const bm = new BackendManager({
    onReady: () => {
      console.log(`[Test] onReady called`);
    },
  });
  bm.currentPort = 8765;

  console.log('[Test] Starting BackendManager...');
  await bm.start(() => {}); // empty splash reporter

  // Wait a moment for callbacks
  await new Promise(r => setTimeout(r, 500));

  console.log(`\n[Test] probeCallCount: ${probeCallCount}`);
  console.log(`[Test] healthCheckCallCount: ${healthCheckCallCount}`);
  console.log(`[Test] bm.reusedExisting: ${bm.reusedExisting}`);

  assert(bm.reusedExisting === true, 'reusedExisting flag is true');
  assert(probeCallCount === 1, `probeBackendHealth called exactly once (was ${probeCallCount})`);
  assert(healthCheckCallCount === 0, `healthCheck NOT called in reuse path (was ${healthCheckCallCount})`);

  console.log(`\n=== Summary: ${pass} passed, ${fail} failed ===`);
  process.exit(fail === 0 ? 0 : 1);
})();