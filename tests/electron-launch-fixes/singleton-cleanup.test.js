// Test SingletonLock cleanup logic by extracting the function and exercising it
// Run as: node test-singleton-cleanup.js

const path = require('path');
const fs = require('fs');
const os = require('os');

// Recreate the cleanup function exactly as it appears in main.js
function cleanupSingletonLockFiles(appMock) {
  if (process.platform !== 'win32') return 0;
  try {
    const userData = appMock.getPath('userData');
    const lockFiles = ['SingletonLock', 'SingletonLockSymlink', 'LOCK'];
    let cleaned = 0;
    for (const name of lockFiles) {
      const p = path.join(userData, name);
      try {
        if (fs.existsSync(p)) {
          fs.unlinkSync(p);
          cleaned++;
        }
      } catch (e) {
        // silent
      }
    }
    if (cleaned > 0) {
      console.log(`[Test] Cleaned ${cleaned} stale SingletonLock file(s): ${userData}`);
    }
    return cleaned;
  } catch (e) {
    console.warn('[Test] Cleanup failed:', e.message);
    return 0;
  }
}

let pass = 0;
let fail = 0;

function assert(condition, msg) {
  if (condition) {
    pass++;
    console.log(`  PASS: ${msg}`);
  } else {
    fail++;
    console.log(`  FAIL: ${msg}`);
  }
}

// ========== Test 1: No lock files ==========
console.log('\n=== Test 1: No stale lock files ===');
const tmpDir1 = fs.mkdtempSync(path.join(os.tmpdir(), 'singleton-test-1-'));
const mockApp1 = { getPath: () => tmpDir1 };
const cleaned1 = cleanupSingletonLockFiles(mockApp1);
assert(cleaned1 === 0, 'Returns 0 when no lock files exist');

// ========== Test 2: SingletonLock residue ==========
console.log('\n=== Test 2: SingletonLock file residue ===');
const tmpDir2 = fs.mkdtempSync(path.join(os.tmpdir(), 'singleton-test-2-'));
const lockPath = path.join(tmpDir2, 'SingletonLock');
fs.writeFileSync(lockPath, 'fake-lock-data');
const symlinkPath = path.join(tmpDir2, 'SingletonLockSymlink');
fs.writeFileSync(symlinkPath, 'fake-symlink-data');
const mockApp2 = { getPath: () => tmpDir2 };
const cleaned2 = cleanupSingletonLockFiles(mockApp2);
assert(cleaned2 === 2, 'Cleans 2 lock files');
assert(!fs.existsSync(lockPath), 'SingletonLock removed');
assert(!fs.existsSync(symlinkPath), 'SingletonLockSymlink removed');

// ========== Test 3: Mixed stale + LOCK file ==========
console.log('\n=== Test 3: Mixed lock file types ===');
const tmpDir3 = fs.mkdtempSync(path.join(os.tmpdir(), 'singleton-test-3-'));
const lockPath3 = path.join(tmpDir3, 'SingletonLock');
fs.writeFileSync(lockPath3, 'fake');
const otherFile = path.join(tmpDir3, 'cookies');
fs.writeFileSync(otherFile, 'untouched');
const mockApp3 = { getPath: () => tmpDir3 };
const cleaned3 = cleanupSingletonLockFiles(mockApp3);
assert(cleaned3 === 1, 'Cleans only SingletonLock, not other files');
assert(fs.existsSync(otherFile), 'Non-lock files preserved');

// ========== Test 4: Locked file (in use) ==========
console.log('\n=== Test 4: Locked file (EBUSY simulation) ===');
const tmpDir4 = fs.mkdtempSync(path.join(os.tmpdir(), 'singleton-test-4-'));
const lockedPath = path.join(tmpDir4, 'SingletonLock');
fs.writeFileSync(lockedPath, 'fake');
// Open a handle to simulate locked file (Windows-specific)
let fd;
try {
  fd = fs.openSync(lockedPath, 'r+');
  const mockApp4 = { getPath: () => tmpDir4 };
  const cleaned4 = cleanupSingletonLockFiles(mockApp4);
  // On Windows with exclusive lock, fs.unlinkSync may fail; we just verify no crash
  assert(cleaned4 === 0 || cleaned4 === 1, 'Handles locked file gracefully (no crash)');
} finally {
  if (fd !== undefined) {
    try { fs.closeSync(fd); } catch (e) {}
    try { fs.unlinkSync(lockedPath); } catch (e) {}
  }
}

// ========== Test 5: Empty userData path ==========
console.log('\n=== Test 5: Empty userData ===');
const tmpDir5 = fs.mkdtempSync(path.join(os.tmpdir(), 'singleton-test-5-'));
fs.rmdirSync(tmpDir5); // make it not exist
const mockApp5 = { getPath: () => tmpDir5 };
let crashed = false;
try {
  const cleaned5 = cleanupSingletonLockFiles(mockApp5);
  assert(cleaned5 === 0, 'Handles missing userData directory');
} catch (e) {
  crashed = true;
  console.log(`  FAIL: Crashed on missing dir: ${e.message}`);
}
assert(!crashed, 'No crash on missing userData');

// ========== Summary ==========
console.log(`\n=== Summary: ${pass} passed, ${fail} failed ===`);
process.exit(fail === 0 ? 0 : 1);