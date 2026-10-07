/**
 * N1-fix.1: 调试 SPA 渲染
 *
 * 启动真实 Electron + 抓 console / pageerror / requestfailed
 * + 导航到指定路径 + 抓 page.content() + 截图
 * 输出到 g:\iMato\logs\debug-spa-render.log
 *
 * 用法：node g:\iMato\tests\electron\auto-test\debug-spa-render.js [path]
 *   path: 默认为 /user/dashboard
 */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const {
  launchElectron,
  waitForCDP,
  getElectronWebSocketUrl,
  autoLogin,
} = require('./engine');
const { TEST_ACCOUNTS, DEFAULT_ACCOUNT, ENVIRONMENT } = require('./config');

const TARGET_PATH = process.argv[2] || '/user/dashboard';
const LOG_FILE = 'g:\\iMato\\logs\\debug-spa-render.log';
const SHOT_FILE = 'g:\\iMato\\tests\\test-results\\auto-test\\screenshots\\debug-spa.png';

// 简单 logger
function ts() { return new Date().toISOString().slice(11, 23); }
function log(level, msg) {
  const line = `[${ts()}] ${level} ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

// 重新写日志（清理旧内容）
fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
fs.writeFileSync(LOG_FILE, '');

(async () => {
  let browser = null;
  let electronProcess = null;
  try {
    log('INFO', `=== Debug SPA render start, target=${TARGET_PATH} ===`);

    // 1. 启动 Electron
    log('INFO', 'Step 1: launching Electron...');
    electronProcess = launchElectron({ info: log, warn: log, error: log, debug: () => {} });
    log('INFO', `Electron PID=${electronProcess.pid}`);

    // 2. 等 CDP
    log('INFO', 'Step 2: waiting CDP port 9222...');
    const cdpReady = await waitForCDP(9222, 30000, { info: log, warn: log, error: log });
    if (!cdpReady) throw new Error('CDP port 9222 not ready');
    await new Promise(r => setTimeout(r, 2000));

    // 3. 拿 browser-level URL
    log('INFO', 'Step 3: getting browser-level WS URL...');
    const wsEndpoint = await getElectronWebSocketUrl(9222, { info: log, warn: log, error: log });
    if (!wsEndpoint) throw new Error('No browser-level WS URL');
    log('INFO', `WS endpoint: ${wsEndpoint}`);

    // 4. 连接 + 拿 page
    log('INFO', 'Step 4: connecting via CDP...');
    browser = await chromium.connectOverCDP(wsEndpoint);
    const contexts = browser.contexts();
    log('INFO', `Contexts: ${contexts.length}`);
    if (contexts.length === 0) throw new Error('No contexts');
    const context = contexts[0];
    log('INFO', `Pages in context[0]: ${context.pages().length}`);
    let page = context.pages()[0];
    if (!page) {
      // 等待 30s
      log('INFO', 'Waiting for page...');
      const start = Date.now();
      while (!page && Date.now() - start < 30000) {
        await new Promise(r => setTimeout(r, 500));
        page = context.pages()[0];
      }
      if (!page) throw new Error('No page after 30s');
    }
    log('INFO', `Got page, current URL: ${page.url()}`);

    // 5. 装事件监听
    page.on('console', (msg) => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error' || type === 'warning' || type === 'warn') {
        log(`CONSOLE-${type.toUpperCase()}`, text.substring(0, 500));
      }
    });
    page.on('pageerror', (err) => {
      log('PAGE-ERROR', `${err.name}: ${err.message}`);
    });
    page.on('requestfailed', (req) => {
      log('REQ-FAILED', `${req.method()} ${req.url()} -> ${req.failure()?.errorText}`);
    });
    page.on('response', (res) => {
      if (res.status() >= 400) {
        log('HTTP-ERROR', `${res.status()} ${res.url()}`);
      }
    });

    // 6. 注入 token
    log('INFO', 'Step 6: autoLogin (injects token)...');
    const account = TEST_ACCOUNTS.student || DEFAULT_ACCOUNT;
    const loginResult = await autoLogin(page, account, ENVIRONMENT.frontendUrl, { info: log, warn: log, error: log, debug: () => {} });
    log('INFO', `autoLogin result: ${JSON.stringify({ success: loginResult.success, redirect: loginResult.redirectUrl, error: loginResult.error })}`);

    // 7. 导航到目标路径
    const fullUrl = `${ENVIRONMENT.frontendUrl}${TARGET_PATH}`;
    log('INFO', `Step 7: navigating to ${fullUrl}...`);
    const navStart = Date.now();
    await page.goto(fullUrl, { waitUntil: 'domcontentloaded', timeout: 15000 }).catch((e) => {
      log('WARN', `goto error: ${e.message}`);
    });
    log('INFO', `goto took ${Date.now() - navStart}ms`);

    // 8. 等 SPA 渲染（直接等 8s 强等，不用 waitForFunction）
    log('INFO', 'Step 8: waiting 8s for SPA render...');
    await new Promise(r => setTimeout(r, 8000));

    // 9. 抓页面状态
    log('INFO', 'Step 9: dumping page state...');
    const state = await page.evaluate(() => {
      const root = document.querySelector('app-root');
      return {
        currentUrl: location.href,
        appRootExists: !!root,
        appRootChildren: root ? root.children.length : 0,
        appRootInnerHTMLLength: root ? root.innerHTML.length : 0,
        appRootInnerHTMLPreview: root ? root.innerHTML.substring(0, 800) : null,
        bodyChildren: document.body.children.length,
        bodyInnerHTMLLength: document.body.innerHTML.length,
        title: document.title,
        // 找 router-outlet
        routerOutletExists: !!document.querySelector('router-outlet'),
        routerOutletContent: (() => {
          const outlet = document.querySelector('router-outlet');
          if (!outlet) return null;
          return outlet.nextElementSibling ? outlet.nextElementSibling.outerHTML.substring(0, 500) : '(no sibling)';
        })(),
        // 找已渲染的 Angular 组件
        knownComponents: {
          appStudentDashboard: !!document.querySelector('app-student-dashboard'),
          appUserPageLayout: !!document.querySelector('app-user-page-layout'),
          appUserProfile: !!document.querySelector('app-user-profile'),
          appAuthLogin: !!document.querySelector('app-auth-login'),
        },
        // 错误信息
        ngErrors: (window).ng && (window).ng.getComponent ? (() => {
          try {
            const comp = (window).ng.getComponent(document.querySelector('app-root'));
            return comp ? comp.constructor.name : null;
          } catch (e) { return `err: ${e.message}`; }
        })() : 'ng not available',
      };
    });
    log('INFO', `Page state: ${JSON.stringify(state, null, 2)}`);

    // 10. 截图
    log('INFO', 'Step 10: taking screenshot...');
    fs.mkdirSync(path.dirname(SHOT_FILE), { recursive: true });
    await page.screenshot({ path: SHOT_FILE, fullPage: false });
    const stat = fs.statSync(SHOT_FILE);
    log('INFO', `Screenshot saved: ${SHOT_FILE} (${stat.size} bytes)`);

    log('INFO', '=== Debug SPA render done ===');
  } catch (err) {
    log('FATAL', `${err.message}\n${err.stack}`);
  } finally {
    if (browser) await browser.close().catch(() => {});
    if (electronProcess && !electronProcess.killed) {
      try {
        require('child_process').execSync(`taskkill /pid ${electronProcess.pid} /T /F`, { stdio: 'ignore' });
      } catch {}
    }
  }
  process.exit(0);
})();
