/**
 * E2E 测试执行指南
 * 
 * 本文件说明了如何运行 MatuX 桌面端 E2E 测试
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// 检查 Playwright 是否安装
function checkPlaywrightInstalled() {
  try {
    execSync('npx playwright --version', { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

// 安装 Playwright
function installPlaywright() {
  console.log('📦 安装 Playwright...');
  execSync('npx playwright install chromium', { stdio: 'inherit' });
  console.log('✅ Playwright 安装完成');
}

// 运行测试
function runTests() {
  const testFile = process.argv[2] || '';
  const testDir = path.join(__dirname, '..', 'tests');
  
  let args = ['playwright', 'test'];
  
  if (testFile) {
    args.push(path.join(testDir, testFile));
  } else {
    args.push(path.join(testDir, 'electron'));
  }
  
  console.log(`\n🧪 运行测试: ${args.join(' ')}\n`);
  execSync('npx playwright test --config tests/playwright.config.js', { stdio: 'inherit' });
}

// 主函数
function main() {
  console.log('🔧 E2E 测试准备...\n');
  
  // 检查 Playwright
  if (!checkPlaywrightInstalled()) {
    installPlaywright();
  }
  
  // 运行测试
  runTests();
}

main();
