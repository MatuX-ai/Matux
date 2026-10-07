/**
 * 用户桌面端测试运行脚本
 *
 * 使用方法:
 * node run-user-tests.js
 * node run-user-tests.js --auth          // 仅运行认证测试
 * node run-user-tests.js --permissions   // 仅运行权限测试
 * node run-user-tests.js --data          // 仅运行数据管理测试
 */

const { spawn } = require('child_process');
const path = require('path');

const args = process.argv.slice(2);
const testType = args[0];

// 测试文件映射
const testFiles = {
  '--auth': 'test-user-desktop.spec.js',
  '--permissions': 'test-user-permissions.spec.js',
  '--data': 'test-user-data.spec.js',
  '--all': [
    'test-user-desktop.spec.js',
    'test-user-permissions.spec.js',
    'test-user-data.spec.js',
  ],
};

// 构建测试命令
let testFile;
if (testType && testFiles[testType]) {
  testFile = Array.isArray(testFiles[testType])
    ? testFiles[testType]
    : [testFiles[testType]];
} else {
  testFile = testFiles['--all'];
}

console.log('=====================================');
console.log('  用户桌面端测试');
console.log('=====================================');
console.log('测试类型:', testType || '全部');
console.log('测试文件:', testFile.join(', '));
console.log('=====================================');
console.log('');

// 构建 playwright 命令
const configFile = path.join(__dirname, 'test-user-desktop.config.js');
const testDir = __dirname;

const command = 'npx';
const testArgs = [
  'playwright',
  'test',
  ...testFile.map(f => path.join(testDir, f)),
  '--config', configFile,
  '--headed',  // 显示浏览器窗口
  '--reporter=list',
];

console.log('执行命令:', command, testArgs.join(' '));
console.log('');

// 执行测试
const testProcess = spawn(command, testArgs, {
  cwd: path.join(__dirname, '..', '..'),
  stdio: 'inherit',
  shell: true,
});

testProcess.on('exit', (code) => {
  console.log('');
  console.log('=====================================');
  console.log('  测试完成，退出码:', code);
  console.log('=====================================');
  process.exit(code);
});

testProcess.on('error', (err) => {
  console.error('测试执行失败:', err);
  process.exit(1);
});
