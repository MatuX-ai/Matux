/**
 * Sprint 3 集成验证脚本
 * 验证 file-parser.js typeMap 修复和其他 Sprint 修改
 */
const fp = require('../../electron/services/file-parser.js');
const fs = require('fs');
const path = require('path');

let passed = 0;
let failed = 0;

function assert(name, condition) {
  if (condition) {
    console.log(`  PASS: ${name}`);
    passed++;
  } else {
    console.log(`  FAIL: ${name}`);
    failed++;
  }
}

console.log('\n=== Task 3.2: file-parser.js typeMap 验证 ===\n');

// Test: type='course' should now pass for .imato files
const r1 = fp.validateFileContent({
  version: '1.0', type: 'course',
  data: { title: 'test' }, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('type=course should be valid for .imato', r1.valid === true);

// Test: type='blockly-project' should still pass for .imato
const r2 = fp.validateFileContent({
  version: '1.0', type: 'blockly-project',
  data: { blocks: [] }, metadata: {}
}, 'course');
assert('type=blockly-project should be valid for .imato', r2.valid === true);

// Test: type='python-project' should still pass for .imato
const r3 = fp.validateFileContent({
  version: '1.0', type: 'python-project',
  data: { code: 'print("hello")' }, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('type=python-project should be valid for .imato', r3.valid === true);

// Test: type='circuit-project' should still pass for .imato
const r4 = fp.validateFileContent({
  version: '1.0', type: 'circuit-project',
  data: { components: [] }, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('type=circuit-project should be valid for .imato', r4.valid === true);

// Test: invalid type should still fail
const r5 = fp.validateFileContent({
  version: '1.0', type: 'invalid-type',
  data: { something: true }, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('type=invalid-type should be rejected for .imato', r5.valid === false);

// Test: blockly file type validation unchanged
const r6 = fp.validateFileContent({
  version: '1.0', type: 'blockly-project',
  data: { blocks: [] }, metadata: { createdAt: '2024-01-01' }
}, 'blockly');
assert('type=blockly-project should be valid for .imblockly', r6.valid === true);

// Test: circuit file type validation unchanged
const r7 = fp.validateFileContent({
  version: '1.0', type: 'circuit-project',
  data: { components: [] }, metadata: { createdAt: '2024-01-01' }
}, 'circuit');
assert('type=circuit-project should be valid for .imcircuit', r7.valid === true);

// Test: getFileType
assert('getFileType(.imato) === course', fp.getFileType('test.imato') === 'course');
assert('getFileType(.imblockly) === blockly', fp.getFileType('test.imblockly') === 'blockly');
assert('getFileType(.imcircuit) === circuit', fp.getFileType('test.imcircuit') === 'circuit');

console.log('\n=== Sprint 0-2: 文件存在性验证 ===\n');

// Verify key files exist
const files = [
  'src/app/core/services/blockly.service.ts',
  'src/app/core/services/opensciedu.service.ts',
  'src/app/core/services/opensciedu-mock.service.ts',
  'src/app/core/services/imato-file.service.ts',
  'src/app/shared/components/blockly-workspace/blockly-workspace.component.ts',
  'src/app/shared/components/blockly-workspace/blockly-workspace.component.html',
  'electron/services/auto-updater.js',
  'electron/services/file-parser.js',
  'electron/src/core/ipc/handlers/updater-handlers.js',
  'electron/main.js',
];

for (const file of files) {
  const fullPath = path.join(__dirname, '..', '..', file);
  assert(`${file} exists`, fs.existsSync(fullPath));
}

console.log('\n=== auto-updater.js 修复验证 ===\n');

const autoUpdaterContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'electron/services/auto-updater.js'), 'utf-8'
);
assert('auto-updater.js no longer requires electron-log', !autoUpdaterContent.includes("require('electron-log')"));
assert('auto-updater.js has console wrapper', autoUpdaterContent.includes('console.log'));
assert('auto-updater.js disableVersion uses flags', 
  autoUpdaterContent.includes('autoDownload = false') || autoUpdaterContent.includes('autoInstallOnAppQuit = false'));
assert('auto-updater.js no double property access', !autoUpdaterContent.includes('autoUpdater.autoUpdater'));

console.log('\n=== main.js 集成验证 ===\n');

const mainJsContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'electron/main.js'), 'utf-8'
);
assert('main.js imports createUpdaterHandlers', mainJsContent.includes('createUpdaterHandlers'));
assert('main.js has requestSingleInstanceLock', mainJsContent.includes('requestSingleInstanceLock'));
assert('main.js has second-instance handler', mainJsContent.includes('second-instance'));
assert('main.js has open-file handler', mainJsContent.includes('open-file'));

console.log('\n=== opensciedu.service.ts 清理验证 ===\n');

const opensciContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'src/app/core/services/opensciedu.service.ts'), 'utf-8'
);
assert('opensciedu.service.ts has no unused from import', !opensciContent.includes("from } from 'rxjs'") && !opensciContent.includes(', from }'));
assert('opensciedu.service.ts has no handleError dead code', !opensciContent.includes('handleError'));
assert('opensciedu.service.ts has IndexedDB cache', opensciContent.includes('IndexedDB'));
assert('opensciedu.service.ts has static mock import', opensciContent.includes("import { OpenSciEDUMockService }"));

console.log('\n' + '='.repeat(50));
console.log(`Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
console.log('='.repeat(50));

// ===== Round 2: Audit fix verification =====

console.log('\n=== Round 2: Audit fix verification ===\n');

console.log('\n--- #1: environment import removed ---');
assert('opensciedu.service.ts has no environment import', !opensciContent.includes("import { environment }"));

console.log('\n--- #2-3: cache-first fast-path ---');
assert('getCourseDetail uses cacheGet in fast-path', opensciContent.includes('cacheGet(`course_detail_${courseId}`)'));
assert('getKnowledgeGraph uses cacheGet in fast-path', opensciContent.includes("cacheGet('knowledge_graph')"));

console.log('\n--- #4: searchCourses cache comment ---');
assert('searchCourses has cache explanation comment', opensciContent.includes('搜索结果时效性强，不缓存'));

console.log('\n--- #8: auto-updater.js Notification static import ---');
assert('auto-updater.js Notification imported at top', autoUpdaterContent.includes('Notification } = require'));
assert('auto-updater.js no dynamic require in showUpdateNotification', !autoUpdaterContent.includes("const { Notification } = require('electron')"));
assert('auto-updater.js has event binding guard', autoUpdaterContent.includes('_eventsBound'));

console.log('\n--- #10: IPC duplicate guard ---');
assert('main.js has ipcHandlersRegistered guard', mainJsContent.includes('ipcHandlersRegistered'));

console.log('\n--- #11: data validation enhanced ---');
const fpContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'electron/services/file-parser.js'), 'utf-8'
);
assert('file-parser.js checks empty data object', fpContent.includes('Object.keys(content.data).length === 0'));

console.log('\n--- #12: path traversal fix ---');
assert('file-parser.js uses segment-based path check', fpContent.includes('segments.includes'));

console.log('\n--- #13: deprecated functions removed ---');
assert('main.js no deprecated functions', !mainJsContent.includes('_deprecated'));

console.log('\n--- #14: ImatoCoursePackage structure ---');
const imatoContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'src/app/core/services/imato-file.service.ts'), 'utf-8'
);
assert('ImatoCoursePackage has type field', imatoContent.includes('type: string'));
assert('ImatoCoursePackage has data field', imatoContent.includes('data: {'));
assert('validatePackage checks pkg.data.title', imatoContent.includes('pkg.data.title'));
assert('validatePackage checks pkg.data.modules', imatoContent.includes('pkg.data.modules'));

// Re-validate file-parser with empty data
const r8 = fp.validateFileContent({
  version: '1.0', type: 'course',
  data: {}, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('empty data {} is now rejected', r8.valid === false);

// Validate correct structure
const r9 = fp.validateFileContent({
  version: '1.0', type: 'course',
  data: { title: 'test', modules: [] }, metadata: { createdAt: '2024-01-01' }
}, 'course');
assert('valid course with data.title passes', r9.valid === true);

console.log('\n--- #9: preload.js updater channels ---');
const preloadContent = fs.readFileSync(
  path.join(__dirname, '..', '..', 'electron/preload.js'), 'utf-8'
);
assert('preload.js has auto-updater-status in whitelist', preloadContent.includes('auto-updater-status'));
assert('preload.js exposes checkForUpdate', preloadContent.includes('updater:check'));
assert('preload.js exposes downloadUpdate', preloadContent.includes('updater:download'));
assert('preload.js exposes installUpdate', preloadContent.includes('updater:install'));
assert('preload.js exposes getAppVersion', preloadContent.includes('updater:get-version'));

console.log('\n' + '='.repeat(50));
console.log(`Total Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
console.log('='.repeat(50));

if (failed > 0) {
  process.exit(1);
}
