/**
 * 截图脚本：捕获 Electron Splash 窗口的实际渲染
 */
const { _electron: electron } = require('playwright');
const path = require('path');

(async () => {
  console.log('[Screenshot] 启动 Electron...');
  const electronApp = await electron.launch({
    args: ['.'],
    cwd: path.join(__dirname),
    env: {
      ...process.env,
      SPLASH_DEBUG: '1',
    },
  });

  // 等待第一个窗口
  const windows = electronApp.windows();
  console.log('[Screenshot] 初始窗口数:', windows.length);

  // 等待 splash 窗口
  let splashWindow = null;
  for (let i = 0; i < 10; i++) {
    await new Promise(r => setTimeout(r, 500));
    const allWindows = electronApp.windows();
    console.log(`[Screenshot] 检查窗口 (${i}): ${allWindows.length} 个`);
    for (const win of allWindows) {
      const title = await win.title().catch(() => 'unknown');
      const url = win.url();
      console.log(`  - 标题: ${title}, URL: ${url}`);
      if (url.includes('splash.html') || title.includes('启动中')) {
        splashWindow = win;
        break;
      }
    }
    if (splashWindow) break;
  }

  if (!splashWindow) {
    console.log('[Screenshot] 警告：未找到 Splash 窗口，截取第一个窗口');
    splashWindow = electronApp.windows()[0];
  }

  // 等待 DOM 加载
  await splashWindow.waitForLoadState('domcontentloaded', { timeout: 10000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2000)); // 等待动画初始化

  // 截取 Splash 窗口
  const screenshotPath = path.join(__dirname, 'splash-screenshot.png');
  await splashWindow.screenshot({ path: screenshotPath });
  console.log('[Screenshot] 已保存截图:', screenshotPath);

  // 收集控制台日志
  splashWindow.on('console', msg => {
    console.log(`[Splash-Console] ${msg.type()}: ${msg.text()}`);
  });

  // 收集页面错误
  splashWindow.on('pageerror', err => {
    console.log(`[Splash-Error] ${err.message}`);
  });

  // 获取 body 实际样式
  const bodyStyles = await splashWindow.evaluate(() => {
    const body = document.body;
    const computed = window.getComputedStyle(body);
    return {
      backgroundColor: computed.backgroundColor,
      display: computed.display,
      opacity: computed.opacity,
      width: body.offsetWidth,
      height: body.offsetHeight,
      childCount: body.children.length,
      innerHTMLLength: body.innerHTML.length,
    };
  });
  console.log('[Screenshot] Body 样式:', JSON.stringify(bodyStyles, null, 2));

  // 检查 body 的子元素
  const childInfo = await splashWindow.evaluate(() => {
    const result = [];
    for (let i = 0; i < document.body.children.length; i++) {
      const child = document.body.children[i];
      const computed = window.getComputedStyle(child);
      result.push({
        tag: child.tagName,
        class: child.className,
        id: child.id,
        display: computed.display,
        opacity: computed.opacity,
        visibility: computed.visibility,
        width: child.offsetWidth,
        height: child.offsetHeight,
      });
    }
    return result;
  });
  console.log('[Screenshot] Body 子元素:');
  childInfo.forEach((c, i) => console.log(`  [${i}]`, JSON.stringify(c)));

  // 等待 2 秒后再次截图（动画进行中）
  await new Promise(r => setTimeout(r, 2000));
  const screenshot2Path = path.join(__dirname, 'splash-screenshot-2s.png');
  await splashWindow.screenshot({ path: screenshot2Path });
  console.log('[Screenshot] 已保存第 2 张截图:', screenshot2Path);

  // 关闭
  await electronApp.close();
  console.log('[Screenshot] 完成');
})();
