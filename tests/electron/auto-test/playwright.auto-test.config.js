/**
 * iMato 学习端自动化测试 - Playwright 专用配置
 *
 * 用于 npx playwright test 命令
 * 也支持 headed/debug 模式运行
 */

const path = require('path');

module.exports = {
  testDir: path.join(__dirname),

  // 单个测试文件
  testMatch: 'auto-test.spec.js',

  timeout: 300000, // 5分钟总超时

  expect: {
    timeout: 15000,
  },

  retries: 0,

  workers: 1,

  fullyParallel: false,

  reporter: [
    ['list'],
    ['html', {
      outputFolder: path.join(__dirname, '..', '..', 'test-results', 'auto-test', 'playwright-html'),
      open: 'never',
    }],
    ['json', {
      outputFile: path.join(__dirname, '..', '..', 'test-results', 'auto-test', 'playwright-results.json'),
    }],
  ],

  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:4200',
    viewport: { width: 1400, height: 900 },
    ignoreHTTPSErrors: true,
    navigationTimeout: 30000,
    actionTimeout: 10000,
    screenshot: 'on',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    locale: 'zh-CN',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        channel: 'chromium',
      },
    },
  ],

  outputDir: path.join(__dirname, '..', '..', 'test-results', 'auto-test'),
};
