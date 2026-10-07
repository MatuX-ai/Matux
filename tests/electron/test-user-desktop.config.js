/**
 * 用户桌面端测试配置文件
 *
 * 运行方式:
 * npx playwright test --config tests/electron/test-user-desktop.config.js
 */

const path = require('path');

module.exports = {
  testDir: path.join(__dirname),

  testMatch: 'test-user-*.spec.js',

  timeout: 60000,

  expect: {
    timeout: 10000,
  },

  retries: process.env.CI ? 2 : 1,

  workers: 1,

  reporter: [
    ['html', {
      outputFolder: path.join(__dirname, '..', '..', 'test-results', 'user-desktop'),
      open: 'never',
    }],
    ['json', {
      outputFile: path.join(__dirname, '..', '..', 'test-results', 'user-desktop', 'results.json'),
    }],
    ['list'],
  ],

  use: {
    baseURL: 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'electron-chromium',
      use: {
        browserName: 'chromium',
      },
    },
  ],

  outputDir: path.join(__dirname, '..', '..', 'test-results', 'user-desktop'),
};
