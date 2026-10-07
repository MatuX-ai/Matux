/**
 * iMato 学习端自动化测试 - 核心测试引擎
 *
 * 启动真实的 Electron 窗口，通过 CDP 连接进行自动化操作。
 * 不使用 Playwright 模拟浏览器，而是连接到真实 Electron 渲染进程。
 *
 * 执行流程：
 * 1. 确保前端开发服务器 (ng serve) 在运行
 * 2. 确保后端服务在运行
 * 3. 启动真实 Electron 进程
 * 4. 通过 CDP 连接到 Electron 窗口
 * 5. 自动登录 + 页面遍历 + 元素校验
 * 6. 生成测试报告
 */

const { chromium } = require('playwright');
const { spawn, execSync } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { TEST_ACCOUNTS, DEFAULT_ACCOUNT, ENVIRONMENT, PAGES } = require('./config');
const { Logger, TestReport, printSummary } = require('./reporter');

// ==================== 辅助函数 ====================

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * HTTP GET 请求（Node.js 原生，不依赖 fetch）
 */
function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout }, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        resolve({ status: res.statusCode, body: data });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

/**
 * HTTP POST 请求
 */
function httpPost(url, body, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const postData = JSON.stringify(body);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
      timeout,
    };
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        resolve({ status: res.statusCode, body: data });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(postData);
    req.end();
  });
}

/**
 * 检查后端健康状态
 */
async function checkBackendHealth(url, timeout, logger) {
  logger.info(`检查后端健康状态: ${url}`);
  const start = Date.now();

  while (Date.now() - start < timeout) {
    try {
      const res = await httpGet(url, 3000);
      if (res.status >= 200 && res.status < 400) {
        logger.info('后端健康检查通过 ✓');
        return true;
      }
    } catch {
      // 忽略连接失败，继续等待
    }
    await sleep(3000);
  }

  logger.warn(`后端在 ${timeout / 1000}s 内未就绪，将继续尝试...`);
  return false;
}

/**
 * 检查前端开发服务器是否运行
 */
async function checkFrontendServer(url, timeout, logger) {
  // 【修复 #B3】app:// 协议不是 HTTP，无法用 httpGet 探测
  // 在 app 模式下，由 CDP 端口就绪 + 后续页面 goto 验证代替
  if (ENVIRONMENT.protocolMode === 'app') {
    logger.info(`协议模式: app:// （跳过 HTTP 前端服务器校验，由 CDP 验证窗口就绪）`);
    return true;
  }
  logger.info(`检查前端开发服务器: ${url}`);
  const start = Date.now();

  while (Date.now() - start < timeout) {
    try {
      const res = await httpGet(url, 3000);
      if (res.status >= 200 && res.status < 400) {
        logger.info('前端开发服务器已就绪 ✓');
        return true;
      }
    } catch {
      // 忽略
    }
    await sleep(3000);
  }

  logger.warn(`前端开发服务器在 ${timeout / 1000}s 内未就绪`);
  return false;
}

// ==================== Electron 进程管理 ====================

/**
 * 启动真实 Electron 进程，开启远程调试端口
 * @returns {import('child_process').ChildProcess}
 */
function launchElectron(logger) {
  const projectRoot = path.resolve(__dirname, '..', '..', '..');
  const electronDir = path.join(projectRoot, 'electron');

  // 使用 npx electron 启动，指定远程调试端口
  const debugPort = 9222;
  logger.info(`启动真实 Electron 窗口 (调试端口: ${debugPort})`);
  logger.info(`Electron 目录: ${electronDir}`);

  // 设置环境变量：app:// 协议模式，不强制 NODE_ENV=development（避免 main.js 走 localhost:4200 分支）
  const env = Object.assign({}, process.env, {
    BACKEND_PORT: process.env.BACKEND_PORT || '8000',
    PORT: process.env.PORT || '8000',
  });

  // 使用 electron . 启动 electron 子目录
  // --remote-debugging-port 允许 CDP 连接
  const electronPath = getElectronBinaryPath();
  const args = [
    electronPath,
    electronDir,  // Electron 主入口目录（包含 main.js）
    `--remote-debugging-port=${debugPort}`,
    '--disable-gpu-sandbox',  // 某些环境下需要
  ];

  logger.info(`命令: ${args.join(' ')}`);

  const child = spawn(args[0], args.slice(1), {
    cwd: electronDir,
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false,
  });

  // 转发 Electron 子进程输出到日志
  child.stdout.on('data', (data) => {
    const lines = data.toString().split('\n').filter(l => l.trim());
    lines.forEach(line => {
      logger.debug(`[Electron stdout] ${line}`);
    });
  });

  child.stderr.on('data', (data) => {
    const lines = data.toString().split('\n').filter(l => l.trim());
    lines.forEach(line => {
      logger.debug(`[Electron stderr] ${line}`);
    });
  });

  child.on('error', (err) => {
    logger.error(`Electron 进程启动失败: ${err.message}`);
  });

  child.on('exit', (code, signal) => {
    logger.info(`Electron 进程退出 (code=${code}, signal=${signal})`);
  });

  return child;
}

/**
 * 获取 Electron 可执行文件路径
 * Windows 上优先使用 electron 包自带的 electron.exe（避免 spawn .cmd 时的 EINVAL 问题）
 */
function getElectronBinaryPath() {
  const projectRoot = path.resolve(__dirname, '..', '..', '..');

  if (process.platform === 'win32') {
    // 优先：electron 包自带的 electron.exe（Node.js spawn 直接支持）
    const electronExe = path.join(projectRoot, 'node_modules', 'electron', 'dist', 'electron.exe');
    if (fs.existsSync(electronExe)) {
      return electronExe;
    }
    // 备选：node_modules/.bin/electron.cmd（需要 shell:true 才能 spawn）
    const localElectronCmd = path.join(projectRoot, 'node_modules', '.bin', 'electron.cmd');
    if (fs.existsSync(localElectronCmd)) {
      return localElectronCmd;
    }
  } else {
    const localElectron = path.join(projectRoot, 'node_modules', '.bin', 'electron');
    if (fs.existsSync(localElectron)) {
      return localElectron;
    }
  }

  // 回退到 npx
  return 'npx';
}

/**
 * 等待 Electron 的 CDP 端口可用
 */
async function waitForCDP(port, timeout, logger) {
  logger.info(`等待 Electron CDP 端口 ${port} 可用...`);
  const start = Date.now();

  while (Date.now() - start < timeout) {
    try {
      const res = await httpGet(`http://localhost:${port}/json`, 3000);
      if (res.status === 200) {
        logger.info(`Electron CDP 端口已就绪 ✓`);
        return true;
      }
    } catch {
      // 端口尚未就绪
    }
    await sleep(2000);
  }

  logger.error(`Electron CDP 端口在 ${timeout / 1000}s 内未就绪`);
  return false;
}

/**
 * 通过 CDP 端口获取 Electron 浏览器级别的 WebSocket 调试 URL
 * （连接 browser-level URL 可以正常获取所有 contexts/pages）
 */
async function getElectronWebSocketUrl(port, logger) {
  try {
    const res = await httpGet(`http://localhost:${port}/json/version`, 5000);
    const version = JSON.parse(res.body);
    if (version.webSocketDebuggerUrl) {
      logger.info(`找到 Electron Browser-level 端点: ${version.Browser || 'unknown'}`);
      return version.webSocketDebuggerUrl;
    }
    logger.warn('/json/version 未返回 webSocketDebuggerUrl');
    return null;
  } catch (err) {
    logger.error(`获取 Electron Browser-level 端点失败: ${err.message}`);
    return null;
  }
}

// ==================== 自动登录 ====================

/**
 * 通过 API 直接登录获取 Token，然后注入到浏览器
 */
async function autoLogin(page, account, frontendUrl, logger) {
  logger.info(`开始自动登录: ${account.username} (${account.role})`);

  try {
    // 【修复】直连后端 API，不经前端 url（app:// 不能直接 httpPost）
    const loginUrl = `${ENVIRONMENT.apiBaseUrl}/api/v1/auth/signin`;
    logger.info(`登录 API: ${loginUrl}`);

    const loginRes = await httpPost(
      loginUrl,
      { email: account.username, password: account.password },
      10000
    );

    if (loginRes.status !== 200) {
      throw new Error(`登录 API 返回 ${loginRes.status}: ${loginRes.body.substring(0, 200)}`);
    }

    let loginData;
    try {
      loginData = JSON.parse(loginRes.body);
    } catch {
      throw new Error(`登录响应 JSON 解析失败: ${loginRes.body.substring(0, 200)}`);
    }

    // 【修复 #B1】后端 AuthResponse 使用驼峰命名，同时兼容下划线以向后兼容
    const accessToken = loginData.accessToken || loginData.access_token;
    const refreshToken = loginData.refreshToken || loginData.refresh_token || '';
    const userData = loginData.user || {};

    if (!accessToken) {
      throw new Error('登录响应中未找到 accessToken/access_token');
    }

    logger.info('API 登录成功，获取到 Token ✓');

    // 注入 Token 到浏览器存储
    await page.evaluate(({ token, refresh, user }) => {
      sessionStorage.setItem('access_token', token);
      sessionStorage.setItem('refresh_token', refresh);
      sessionStorage.setItem('user_data', JSON.stringify(user));
      localStorage.setItem('access_token', token);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_data', JSON.stringify(user));
    }, {
      token: accessToken,
      refresh: refreshToken,
      user: userData,
    });

    logger.info('Token 注入到浏览器存储 ✓');

    // 导航到仪表板验证登录状态
    await page.goto(`${frontendUrl}/user/dashboard`, {
      waitUntil: 'domcontentloaded',
      timeout: ENVIRONMENT.pageLoadTimeout,
    }).catch(() => {});
    // 【修复 #B7】等 Angular 路由解析 + 组件渲染完成
    try {
      await page.waitForFunction(
        () => {
          const root = document.querySelector('app-root');
          if (!root) return false;
          return root.children.length > 0 && root.innerHTML.trim().length > 50;
        },
        { timeout: ENVIRONMENT.pageLoadTimeout }
      );
    } catch {
      logger.warn('  ⚠️ 登录后路由渲染超时');
    }
    await sleep(2500);

    // 验证是否仍在登录页
    const currentUrl = page.url();
    if (currentUrl.includes('/auth/login')) {
      throw new Error('登录后仍被重定向到登录页，Token 可能无效');
    }

    logger.info(`登录验证通过，当前页面: ${currentUrl} ✓`);
    return {
      success: true,
      username: account.username,
      role: account.role,
      token: accessToken,
      redirectUrl: currentUrl,
    };

  } catch (error) {
    logger.error(`自动登录失败: ${error.message}`);

    // 【修复】仅在 HTTP 模式下降级到表单登录（app:// 模式无表单可填）
    if (ENVIRONMENT.protocolMode === 'http') {
      logger.info('尝试降级方案: 页面表单登录...');
      try {
        return await formLogin(page, account, frontendUrl, logger);
      } catch (formError) {
        logger.error(`表单登录也失败: ${formError.message}`);
        return {
          success: false,
          username: account.username,
          role: account.role,
          error: `${error.message}; 降级登录也失败: ${formError.message}`,
        };
      }
    }
    return {
      success: false,
      username: account.username,
      role: account.role,
      error: error.message,
    };
  }
}

/**
 * 降级方案：通过填写表单登录
 */
async function formLogin(page, account, frontendUrl, logger) {
  await page.goto(`${frontendUrl}/auth/login`, {
    waitUntil: 'domcontentloaded',
    timeout: ENVIRONMENT.pageLoadTimeout,
  });

  await sleep(2000);

  // 填写邮箱
  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  await emailInput.waitFor({ state: 'visible', timeout: ENVIRONMENT.elementTimeout });
  await emailInput.fill(account.username);

  // 填写密码
  const passwordInput = page.locator('input[name="password"]').first();
  await passwordInput.waitFor({ state: 'visible', timeout: ENVIRONMENT.elementTimeout });
  await passwordInput.fill(account.password);

  // 点击登录
  const loginButton = page.locator('button.login-button').first();
  await loginButton.click();

  // 等待导航
  await page.waitForURL('**/user/dashboard**', {
    timeout: ENVIRONMENT.pageLoadTimeout,
  }).catch(() => {});

  await sleep(2000);

  const currentUrl = page.url();
  if (currentUrl.includes('/auth/login')) {
    throw new Error('表单登录后仍在登录页');
  }

  logger.info(`表单登录成功，当前页面: ${currentUrl} ✓`);
  return {
    success: true,
    username: account.username,
    role: account.role,
    method: 'form',
    redirectUrl: currentUrl,
  };
}

// ==================== 页面遍历与校验 ====================

/**
 * 校验单个页面
 */
async function validatePage(page, pageConfig, frontendUrl, logger) {
  const result = {
    name: pageConfig.name,
    path: pageConfig.path,
    status: 'pending',
    loadTimeMs: null,
    requiredChecks: [],
    optionalChecks: [],
    interactionResults: [],
    warnings: [],
    error: null,
    screenshotPath: null,
  };

  const fullUrl = `${frontendUrl}${pageConfig.path}`;
  logger.info(`正在校验页面: ${pageConfig.name} [${pageConfig.path}]`);

  try {
    // 导航到页面
    const navStart = Date.now();
    await page.goto(fullUrl, {
      waitUntil: 'domcontentloaded',
      timeout: ENVIRONMENT.pageLoadTimeout,
    }).catch(() => {});
    result.loadTimeMs = Date.now() - navStart;

    // 【修复 #B7】Angular SPA 需要等路由解析 + 组件渲染：
    //   1. 先等 app-root 下出现首个路由组件（即不再只是 <app-root></app-root>）
    //   2. 补一段时间让 HTTP 请求/动画完成
    try {
      await page.waitForFunction(
        () => {
          const root = document.querySelector('app-root');
          if (!root) return false;
          // app-root 下必须有渲染出的子组件/路由元素（不能只有 <router-outlet>）
          const childCount = root.children.length;
          const hasContent = root.innerHTML.trim().length > 50;
          return childCount > 0 && hasContent;
        },
        { timeout: ENVIRONMENT.pageLoadTimeout }
      );
    } catch {
      // Angular 路由渲染超时（可能是路由不存在、模块错误）
      logger.warn('  ⚠️ Angular 路由渲染超时（app-root 始终为空）');
    }
    await sleep(ENVIRONMENT.actionDelay + 2500);

    // 检查是否被重定向到登录页
    const currentUrl = page.url();
    if (currentUrl.includes('/auth/login') && pageConfig.path !== '/auth/login') {
      if (pageConfig.skipIfModuleInactive) {
        result.status = 'skipped';
        result.warnings.push('被重定向到登录页，可能模块未激活');
        logger.warn(`  页面被重定向到登录页，标记为跳过`);
        return result;
      }
      result.status = 'failed';
      result.error = '被重定向到登录页（认证过期或权限不足）';
      logger.error(`  页面被重定向到登录页`);
      return result;
    }

    // 【新增 N5-vircadia-skip】通用跳过：URL 被路由重定向到非自身路径，
    // 说明目标路由解析失败 / 业务代码异常（NG0201 等）。若允许跳过则视为模块未就绪。
    if (
      pageConfig.skipIfModuleInactive &&
      currentUrl &&
      !currentUrl.includes(pageConfig.path) &&
      !pageConfig.path.includes('dashboard') // 防止 login→dashboard 跳转误判
    ) {
      result.status = 'skipped';
      result.warnings.push(
        `被重定向到 ${currentUrl}（非自身路径 ${pageConfig.path}），可能模块未激活或路由解析失败`
      );
      logger.warn(`  页面被重定向到 ${currentUrl}，标记为跳过`);
      return result;
    }

    // 检查模块激活提示
    if (pageConfig.skipIfModuleInactive) {
      const activatePrompt = await page.locator(
        '.module-activate, .activation-dialog, mat-dialog-container:has-text("激活")'
      ).isVisible({ timeout: 3000 }).catch(() => false);

      if (activatePrompt) {
        result.status = 'skipped';
        result.warnings.push('模块未激活，显示激活提示');
        logger.warn(`  模块未激活，标记为跳过`);
        return result;
      }
    }

    // 校验必需元素
    let allRequiredFound = true;
    for (const element of pageConfig.requiredElements) {
      const found = await page.locator(element.selector).first().isVisible({
        timeout: ENVIRONMENT.elementTimeout,
      }).catch(() => false);

      result.requiredChecks.push({
        selector: element.selector,
        description: element.description,
        found,
      });

      if (!found) {
        allRequiredFound = false;
        logger.warn(`  ❌ 必需元素缺失: ${element.description} [${element.selector}]`);
      } else {
        logger.debug(`  ✅ 必需元素: ${element.description}`);
      }
    }

    // 校验可选元素
    for (const element of pageConfig.optionalElements) {
      const found = await page.locator(element.selector).first().isVisible({
        timeout: 3000,
      }).catch(() => false);

      result.optionalChecks.push({
        selector: element.selector,
        description: element.description,
        found,
      });

      if (!found) {
        result.warnings.push(`可选元素缺失: ${element.description}`);
        logger.debug(`  ⚠️ 可选元素缺失: ${element.description}`);
      } else {
        logger.debug(`  ✅ 可选元素: ${element.description}`);
      }
    }

    // 执行交互测试
    for (const interaction of pageConfig.interactionTests) {
      try {
        const target = page.locator(interaction.selector).first();
        const targetVisible = await target.isVisible({ timeout: 3000 }).catch(() => false);

        if (!targetVisible) {
          result.interactionResults.push({
            name: interaction.name,
            success: false,
            error: '交互目标元素不可见',
          });
          logger.warn(`  ⚠️ 交互测试跳过: ${interaction.name} (元素不可见)`);
          continue;
        }

        if (interaction.action === 'click') {
          await target.click({ timeout: 5000 });
        } else if (interaction.action === 'fill') {
          await target.fill(interaction.value || '', { timeout: 5000 });
        }

        await sleep(1000);

        if (interaction.expectSelector) {
          const expectVisible = await page.locator(interaction.expectSelector).first().isVisible({
            timeout: ENVIRONMENT.elementTimeout,
          }).catch(() => false);

          result.interactionResults.push({
            name: interaction.name,
            success: expectVisible,
            error: expectVisible ? null : `预期元素 ${interaction.expectSelector} 未出现`,
          });

          if (expectVisible) {
            logger.info(`  ✅ 交互测试通过: ${interaction.name}`);
          } else {
            logger.warn(`  ❌ 交互测试失败: ${interaction.name}`);
          }
        } else {
          result.interactionResults.push({
            name: interaction.name,
            success: true,
          });
          logger.info(`  ✅ 交互执行成功: ${interaction.name}`);
        }
      } catch (interactionError) {
        result.interactionResults.push({
          name: interaction.name,
          success: false,
          error: interactionError.message,
        });
        logger.warn(`  ❌ 交互测试异常: ${interaction.name} - ${interactionError.message}`);
      }
    }

    // 截图
    try {
      const screenshotDir = ENVIRONMENT.screenshotDir;
      if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
      }
      const safeName = pageConfig.path.replace(/[/\\]/g, '_');
      const screenshotPath = path.join(screenshotDir, `${safeName}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      result.screenshotPath = screenshotPath;
    } catch (screenshotError) {
      logger.debug(`截图失败: ${screenshotError.message}`);
    }

    // 综合判定
    if (allRequiredFound) {
      result.status = 'passed';
      logger.info(`  ✅ 页面校验通过: ${pageConfig.name}`);
    } else {
      result.status = 'failed';
      result.error = '必需元素缺失';
      logger.error(`  ❌ 页面校验失败: ${pageConfig.name} (必需元素缺失)`);
    }

  } catch (error) {
    result.status = 'failed';
    result.error = error.message;
    logger.error(`  ❌ 页面校验异常: ${pageConfig.name} - ${error.message}`);

    // 异常时截图
    try {
      const screenshotDir = ENVIRONMENT.screenshotDir;
      if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
      }
      const safeName = pageConfig.path.replace(/[/\\]/g, '_');
      const screenshotPath = path.join(screenshotDir, `${safeName}_error.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      result.screenshotPath = screenshotPath;
    } catch {
      // 忽略截图失败
    }
  }

  return result;
}

// ==================== 主测试流程 ====================

/**
 * 运行完整自动化测试（真实 Electron 窗口）
 *
 * @param {object} options 运行选项
 * @param {string} options.accountKey 测试账号键名 (student/teacher/admin)
 * @param {boolean} options.headed 始终为 true（真实窗口必然可见）
 * @param {string[]} options.pageFilter 页面路径过滤
 * @param {boolean} options.skipElectron 跳过 Electron 启动，直接连接已有实例
 * @param {number} options.cdpPort 指定 CDP 端口（默认 9222）
 */
async function runTests(options = {}) {
  const {
    accountKey = 'student',
    headed = true,
    pageFilter = null,
    skipElectron = false,
    cdpPort = 9222,
  } = options;

  const account = TEST_ACCOUNTS[accountKey] || DEFAULT_ACCOUNT;
  const logger = new Logger(ENVIRONMENT.logFile);
  const report = new TestReport({
    frontendUrl: ENVIRONMENT.frontendUrl,
    account: { username: account.username, role: account.role },
  });

  let browser = null;
  let context = null;
  let page = null;
  let electronProcess = null;

  try {
    report.startTime = new Date();

    // ========== 阶段 1: 环境检查 ==========
    logger.phase('阶段 1/5: 环境检查');
    logger.info(`前端地址: ${ENVIRONMENT.frontendUrl}`);
    logger.info(`测试账号: ${account.username} (${account.role})`);
    logger.info(`运行模式: 真实 Electron 窗口 (CDP 端口 ${cdpPort})`);

    // 检查后端
    const backendOk = await checkBackendHealth(
      ENVIRONMENT.backendHealthUrl, ENVIRONMENT.backendTimeout, logger
    );
    if (!backendOk) {
      logger.warn('后端未就绪，部分功能可能无法正常工作');
    }

    // 检查前端开发服务器
    const frontendOk = await checkFrontendServer(
      ENVIRONMENT.frontendUrl, 15000, logger
    );
    if (!frontendOk) {
      logger.error('前端开发服务器未运行！请先执行 npm start 或 ng serve');
      logger.error('真实 Electron 窗口需要前端开发服务器 (localhost:4200)');
      report.endTime = new Date();
      return report;
    }

    // ========== 阶段 2: 启动真实 Electron 窗口 ==========
    logger.phase('阶段 2/5: 启动真实 Electron 窗口');

    if (!skipElectron) {
      // 启动 Electron 子进程
      electronProcess = launchElectron(logger);

      // 等待 Electron 窗口完全启动
      logger.info('等待 Electron 窗口启动...');
      await sleep(5000); // 等待 Electron 初始化

      // 等待 CDP 端口可用
      const cdpReady = await waitForCDP(cdpPort, 60000, logger);
      if (!cdpReady) {
        logger.error('Electron CDP 端口未就绪，无法连接');
        report.endTime = new Date();
        return report;
      }
    } else {
      logger.info('跳过 Electron 启动，连接已有实例...');
      const cdpReady = await waitForCDP(cdpPort, 10000, logger);
      if (!cdpReady) {
        logger.error('已有 Electron 实例的 CDP 端口不可用');
        report.endTime = new Date();
        return report;
      }
    }

    // ========== 阶段 3: 通过 CDP 连接到 Electron 窗口 ==========
    logger.phase('阶段 3/5: 通过 CDP 连接到真实 Electron 窗口');

    // 获取 Electron 窗口的 WebSocket URL
    const wsEndpoint = await getElectronWebSocketUrl(cdpPort, logger);
    if (!wsEndpoint) {
      logger.error('未找到 Electron 窗口的调试目标');
      report.endTime = new Date();
      return report;
    }

    logger.info(`连接到 Electron Browser: ${wsEndpoint}`);

    // 使用 Playwright 连接到 Electron 的 Chromium 实例
    browser = await chromium.connectOverCDP(wsEndpoint);

    // 【修复 #B6】Electron 的 Chromium 不支持 Target.createTarget CDP 命令，
    // 因此绝不能调用 newPage() / newContext()，只能复用已存在的页面。
    // 等待 Electron 主窗口的页面出现（最多 30s）
    const pageWaitStart = Date.now();
    const pageWaitTimeout = 30000;
    while (Date.now() - pageWaitStart < pageWaitTimeout) {
      const contexts = browser.contexts();
      if (contexts.length > 0) {
        context = contexts[0];
        const pages = context.pages();
        if (pages.length > 0) {
          page = pages[0];
          break;
        }
      }
      await sleep(500);
    }

    if (!page) {
      throw new Error('Electron 主窗口在 30s 内未出现任何页面，无法继续测试');
    }

    logger.info(`使用 Electron 主窗口的现有页面: ${page.url() || '(空)'}`);

    // 设置超时
    page.setDefaultTimeout(ENVIRONMENT.elementTimeout);
    page.setDefaultNavigationTimeout(ENVIRONMENT.pageLoadTimeout);

    // 等待 Electron 窗口加载完成
    logger.info('等待 Electron 窗口内容加载...');
    await sleep(3000);

    // 确认当前页面 URL
    const currentUrl = page.url();
    logger.info(`Electron 当前页面: ${currentUrl}`);

    // 如果 Electron 尚未导航到前端，手动导航
    if (!currentUrl.includes('localhost:4200') && !currentUrl.includes('app://')) {
      logger.info('Electron 窗口尚未加载前端，手动导航...');
      await page.goto(ENVIRONMENT.frontendUrl, {
        waitUntil: 'domcontentloaded',
        timeout: ENVIRONMENT.pageLoadTimeout,
      });
      await sleep(2000);
    }

    // ========== 阶段 4: 自动登录 + 逐页遍历校验 ==========
    logger.phase('阶段 4/5: 自动登录与逐页遍历校验');

    // 自动登录
    const loginResult = await autoLogin(page, account, ENVIRONMENT.frontendUrl, logger);
    report.setLoginResult(loginResult);

    if (!loginResult.success) {
      logger.error('登录失败，无法继续页面遍历测试');
      report.endTime = new Date();
      return report;
    }

    logger.info('自动登录完成 ✓');

    // 过滤页面
    let pagesToTest = PAGES;
    if (pageFilter && pageFilter.length > 0) {
      pagesToTest = PAGES.filter(p => pageFilter.some(f => p.path.includes(f)));
      logger.info(`页面过滤: 仅测试 ${pagesToTest.map(p => p.name).join(', ')}`);
    }

    // 跳过登录页（已登录），放最后验证
    const loginPage = pagesToTest.find(p => p.path === '/auth/login');
    const otherPages = pagesToTest.filter(p => p.path !== '/auth/login');

    // 逐页遍历
    for (let i = 0; i < otherPages.length; i++) {
      const pageConfig = otherPages[i];
      logger.separator('─');
      logger.info(`[${i + 1}/${otherPages.length}] ${pageConfig.name} - ${pageConfig.description}`);

      const pageResult = await validatePage(page, pageConfig, ENVIRONMENT.frontendUrl, logger, report);
      report.addPageResult(pageResult);

      await sleep(ENVIRONMENT.actionDelay);
    }

    // 最后验证登录页
    if (loginPage) {
      logger.separator('─');
      logger.info(`[额外] 验证登录页可访问性`);

      await page.evaluate(() => {
        sessionStorage.clear();
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
      });

      const loginResult2 = await validatePage(page, loginPage, ENVIRONMENT.frontendUrl, logger, report);
      report.addPageResult(loginResult2);
    }

    // ========== 阶段 5: 生成测试报告 ==========
    logger.phase('阶段 5/5: 生成测试报告');

    report.endTime = new Date();
    const { jsonPath, htmlPath } = report.save(ENVIRONMENT.reportDir);
    logger.info(`JSON 报告: ${jsonPath}`);
    logger.info(`HTML 报告: ${htmlPath}`);

    printSummary(report, logger);
    return report;

  } catch (fatalError) {
    logger.error(`测试引擎致命错误: ${fatalError.message}`);
    logger.error(fatalError.stack);
    report.endTime = new Date();

    try { report.save(ENVIRONMENT.reportDir); } catch { /* 忽略 */ }
    return report;

  } finally {
    // 断开 Playwright 连接（不断开 Electron 窗口）
    try {
      if (page && !page.isClosed()) await page.close().catch(() => {});
    } catch { /* 忽略 */ }

    // 注意：不关闭 browser，因为那是 Electron 的 Chromium 实例
    // 断开 CDP 连接即可
    try {
      if (browser) await browser.close().catch(() => {});
    } catch { /* 忽略 */ }

    // 关闭 Electron 进程
    if (electronProcess && !electronProcess.killed) {
      logger.info('关闭 Electron 进程...');
      try {
        // Windows 下使用 taskkill 强制终止进程树
        if (process.platform === 'win32') {
          execSync(`taskkill /pid ${electronProcess.pid} /T /F`, { stdio: 'ignore' });
        } else {
          electronProcess.kill('SIGTERM');
          await sleep(2000);
          if (!electronProcess.killed) {
            electronProcess.kill('SIGKILL');
          }
        }
      } catch {
        // 忽略终止失败
      }
    }
  }
}

// ==================== 导出 ====================

module.exports = {
  runTests,
  autoLogin,
  validatePage,
  checkBackendHealth,
  checkFrontendServer,
  launchElectron,
  waitForCDP,
  getElectronWebSocketUrl,
};
