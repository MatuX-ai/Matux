/**
 * Playwright E2E 测试配置
 * 
 * 配置 Electron 应用的端到端测试环境
 */

const path = require('path');

module.exports = {
  // 测试目录
  testDir: path.join(__dirname),
  
  // 测试超时时间 (毫秒)
  timeout: 60000,
  
  // 预期失败测试
  expect: {
    timeout: 10000,
  },
  
  // 失败重试次数
  retries: process.env.CI ? 2 : 0,
  
  // 并行测试数量
  workers: process.env.CI ? 2 : 1,
  
  // 报告器配置
  reporter: [
    ['html', { 
      outputFolder: path.join(__dirname, '..', 'test-results', 'html'),
      open: 'never',
    }],
    ['json', { 
      outputFile: path.join(__dirname, '..', 'test-results', 'results.json'),
    }],
    ['list'],
  ],
  
  // 全局设置/清理
  globalSetup: path.join(__dirname, 'global-setup.js'),
  globalTeardown: path.join(__dirname, 'global-teardown.js'),
  
  // 项目配置
  projects: [
    {
      name: 'chromium',
      use: {
        browserName: 'chromium',
        viewport: { width: 1280, height: 720 },
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        trace: 'on-first-retry',
      },
    },
  ],
  
  // 默认配置
  use: {
    baseURL: 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    navigationTimeout: 30000,
  },
  
  // 输出目录
  outputDir: path.join(__dirname, '..', 'test-results'),
  
  fullyParallel: false,
};
