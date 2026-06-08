/**
 * E2E 测试运行脚本
 * 
 * 运行说明:
 * 1. 先安装 Playwright: npx playwright install
 * 2. 确保后端和前端服务正在运行
 * 3. 运行测试: node scripts/run-e2e-tests.js
 */

const { spawn } = require('child_process');
const path = require('path');

const TEST_COMMAND = 'npx';
const TEST_ARGS = ['playwright', 'test'];
const CONFIG_PATH = path.join(__dirname, '..', 'tests', 'playwright.config.js');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: path.join(__dirname, '..'),
      stdio: 'inherit',
      shell: true,
      ...options,
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(code);
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

async function checkServices() {
  log('\n📡 检查服务状态...', 'cyan');
  
  const http = require('http');
  
  const services = [
    { name: '后端服务', url: 'http://localhost:8000/health' },
    { name: '前端服务', url: 'http://localhost:4200' },
  ];
  
  for (const service of services) {
    try {
      await new Promise((resolve, reject) => {
        http.get(service.url, (res) => {
          if (res.statusCode >= 200 && res.statusCode < 400) {
            log(`✅ ${service.name} 运行正常`, 'green');
            resolve();
          } else {
            reject(new Error(`Status: ${res.statusCode}`));
          }
        }).on('error', reject);
      }).catch(() => {
        log(`⚠️  ${service.name} 不可用，请先启动服务`, 'yellow');
      });
    } catch (e) {
      log(`⚠️  ${service.name} 不可用: ${e.message}`, 'yellow');
    }
  }
}

async function main() {
  log('\n🧪 iMato E2E 测试运行器', 'cyan');
  log('='.repeat(50), 'cyan');
  
  // 检查服务
  await checkServices();
  
  // 运行测试
  log('\n🚀 开始运行 E2E 测试...', 'cyan');
  log(`📁 配置文件: ${CONFIG_PATH}\n`, 'reset');
  
  try {
    await runCommand(TEST_COMMAND, [...TEST_ARGS, '--config', CONFIG_PATH, ...process.argv.slice(2)]);
    log('\n✅ 所有 E2E 测试通过!', 'green');
  } catch (error) {
    log(`\n❌ 测试失败: ${error.message}`, 'red');
    process.exit(1);
  }
}

main();
