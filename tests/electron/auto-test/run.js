#!/usr/bin/env node

/**
 * iMato 学习端自动化测试 - 一键运行入口
 *
 * 启动真实的 Electron 窗口进行自动化测试
 *
 * 用法：
 *   node tests/electron/auto-test/run.js                         # 默认：学生账号
 *   node tests/electron/auto-test/run.js --account teacher       # 使用教师账号
 *   node tests/electron/auto-test/run.js --account admin         # 使用管理员账号
 *   node tests/electron/auto-test/run.js --pages dashboard,courses  # 仅测试指定页面
 *   node tests/electron/auto-test/run.js --cdp-port 9333         # 指定 CDP 调试端口
 *   node tests/electron/auto-test/run.js --connect               # 连接已运行的 Electron 实例
 *   node tests/electron/auto-test/run.js --no-kill               # 测试完成后不关闭 Electron
 *   node tests/electron/auto-test/run.js --help                  # 显示帮助
 *
 * 前置条件：
 *   1. 前端开发服务器已运行 (npm start / ng serve → localhost:4200)
 *   2. 后端服务已运行 (python backend/run.py → localhost:8000)
 *
 * 环境变量：
 *   FRONTEND_URL          前端地址（默认 http://localhost:4200）
 *   BACKEND_HEALTH_URL    后端健康检查地址（默认 http://localhost:8000/health）
 */

const { runTests } = require('./engine');
const { ENVIRONMENT, TEST_ACCOUNTS } = require('./config');

// ==================== 命令行参数解析 ====================

function parseArgs(argv) {
  const args = {
    accountKey: 'student',
    pageFilter: null,
    help: false,
    cdpPort: 9222,
    connect: false,    // 连接已有 Electron 实例
    noKill: false,     // 不关闭 Electron
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case '--account': {
        const key = argv[++i];
        if (key && TEST_ACCOUNTS[key]) {
          args.accountKey = key;
        } else {
          console.error(`❌ 未知账号类型: ${key}`);
          console.error(`   可选: ${Object.keys(TEST_ACCOUNTS).join(', ')}`);
          process.exit(1);
        }
        break;
      }
      case '--pages': {
        const pages = argv[++i];
        if (pages) {
          args.pageFilter = pages.split(',').map(p => p.trim());
        }
        break;
      }
      case '--cdp-port': {
        const port = parseInt(argv[++i], 10);
        if (port > 0 && port < 65536) {
          args.cdpPort = port;
        } else {
          console.error(`❌ 无效端口号`);
          process.exit(1);
        }
        break;
      }
      case '--connect':
        args.connect = true;
        break;
      case '--no-kill':
        args.noKill = true;
        break;
      case '--help':
      case '-h':
        args.help = true;
        break;
      default:
        console.error(`❌ 未知参数: ${arg}`);
        args.help = true;
        break;
    }
  }

  return args;
}

function printHelp() {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║     iMato 学习端自动化测试程序 (真实 Electron 窗口)         ║
╚══════════════════════════════════════════════════════════════╝

启动真实的 Electron 桌面应用窗口，通过 CDP 协议连接进行自动化测试。

前置条件:
  1. 后端服务: cd backend && python main_ai_edu.py (→ localhost:8000)
  2. 前端构建产物: dist/imatuproject/index.html （由 main.js app:// 协议加载）
  3. 推荐使用 scripts/run-student-e2e.ps1 一键执行

用法: node tests/electron/auto-test/run.js [选项]

选项:
  --account <type>      指定测试账号 (student | teacher | admin)
  --pages <paths>       仅测试指定页面（逗号分隔路径关键词）
  --cdp-port <port>     Electron CDP 调试端口 (默认: 9222)
  --connect             连接已运行的 Electron 实例（跳过启动）
  --no-kill             测试完成后不关闭 Electron 窗口
  --help, -h            显示此帮助信息

环境变量:
  FRONTEND_URL          前端地址 (默认: http://localhost:4200)
  BACKEND_HEALTH_URL    后端健康检查地址 (默认: http://localhost:8000/health)

示例:
  node tests/electron/auto-test/run.js                           # 学生账号，启动 Electron
  node tests/electron/auto-test/run.js --account teacher         # 教师账号
  node tests/electron/auto-test/run.js --pages dashboard,courses # 仅测试仪表板和课程
  node tests/electron/auto-test/run.js --connect                 # 连接已有 Electron 实例
  node tests/electron/auto-test/run.js --no-kill                 # 测试后保留窗口
`);
}

// ==================== 主入口 ====================

async function main() {
  const args = parseArgs(process.argv);

  if (args.help) {
    printHelp();
    process.exit(0);
  }

  console.log('');
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║     iMato 学习端自动化测试程序 v1.0                         ║');
  console.log('║     真实 Electron 窗口 + CDP 自动化校验                     ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log('');
  console.log(`  模式: ${args.connect ? '连接已有实例' : '启动新 Electron 窗口'}`);
  console.log(`  账号: ${TEST_ACCOUNTS[args.accountKey]?.username} (${TEST_ACCOUNTS[args.accountKey]?.role})`);
  console.log(`  CDP:  localhost:${args.cdpPort}`);
  console.log('');

  try {
    const report = await runTests({
      accountKey: args.accountKey,
      headed: true, // 真实 Electron 窗口始终可见
      pageFilter: args.pageFilter,
      skipElectron: args.connect,
      cdpPort: args.cdpPort,
    });

    const data = report.toJSON();

    if (!data.login || !data.login.success) {
      console.error('\n❌ 测试中止: 登录失败');
      process.exit(2);
    }

    if (data.summary.failed > 0) {
      console.error(`\n❌ 测试完成但有 ${data.summary.failed} 个页面校验失败`);
      process.exit(1);
    }

    console.log('\n✅ 所有页面校验通过！');
    process.exit(0);

  } catch (error) {
    console.error('\n❌ 测试运行致命错误:', error.message);
    console.error(error.stack);
    process.exit(3);
  }
}

main();
