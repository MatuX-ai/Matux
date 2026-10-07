/**
 * iMato 学习端自动化测试 - Playwright Test 格式
 *
 * 通过 CDP 连接真实 Electron 窗口进行自动化测试
 * 也可通过 run.js 独立运行（推荐，日志更详细）
 */

const { test, expect } = require('@playwright/test');
const { runTests } = require('./engine');
const { ENVIRONMENT } = require('./config');

test.describe('iMato 学习端自动化全页面测试 (真实 Electron 窗口)', () => {

  test('学生账号 - 真实 Electron 窗口全页面遍历', async ({}, testInfo) => {
    testInfo.setTimeout(300000); // 5 分钟

    const report = await runTests({
      accountKey: 'student',
      headed: true,
    });

    const data = report.toJSON();

    expect(data.login?.success, '登录应成功').toBeTruthy();
    expect(data.summary.total, '应至少测试 1 个页面').toBeGreaterThan(0);

    testInfo.attach('测试摘要', {
      body: JSON.stringify(data.summary, null, 2),
      contentType: 'application/json',
    });

    const { jsonPath, htmlPath } = report.save(ENVIRONMENT.reportDir);
    testInfo.attach('完整报告 (JSON)', { path: jsonPath, contentType: 'application/json' });
    testInfo.attach('完整报告 (HTML)', { path: htmlPath, contentType: 'text/html' });

    const corePages = data.pages.filter(p =>
      p.path.startsWith('/user/') || p.path === '/auth/login'
    );
    const coreFailed = corePages.filter(p => p.status === 'failed');

    if (coreFailed.length > 0) {
      const failedNames = coreFailed.map(p => p.name).join(', ');
      throw new Error(`核心页面校验失败: ${failedNames}`);
    }
  });

  test('教师账号 - 真实 Electron 窗口全页面遍历', async ({}, testInfo) => {
    testInfo.setTimeout(300000);

    const report = await runTests({
      accountKey: 'teacher',
      headed: true,
    });

    const data = report.toJSON();
    expect(data.login?.success, '教师账号登录应成功').toBeTruthy();

    const { jsonPath } = report.save(ENVIRONMENT.reportDir);
    testInfo.attach('教师测试报告 (JSON)', { path: jsonPath, contentType: 'application/json' });
  });

  test('管理员账号 - 真实 Electron 窗口全页面遍历', async ({}, testInfo) => {
    testInfo.setTimeout(300000);

    const report = await runTests({
      accountKey: 'admin',
      headed: true,
    });

    const data = report.toJSON();
    expect(data.login?.success, '管理员账号登录应成功').toBeTruthy();

    const { jsonPath } = report.save(ENVIRONMENT.reportDir);
    testInfo.attach('管理员测试报告 (JSON)', { path: jsonPath, contentType: 'application/json' });
  });
});
