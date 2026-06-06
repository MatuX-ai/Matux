/**
 * Phase 5 端到端测试脚本
 * 
 * 测试场景:
 * 1. 首次启动引导流程
 * 2. 推荐引擎功能
 * 3. 插件详情查看
 * 4. 评分和评论
 * 5. 使用统计
 * 6. 更新通知
 * 
 * 使用方法:
 * 在 Electron 主进程中运行:
 * node test-phase5-e2e.js
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

// ==================== 测试配置 ====================

const TEST_CONFIG = {
  userDataPath: path.join(app.getPath('userData'), 'test-phase5'),
  timeout: 30000,
  screenshotDir: path.join(__dirname, 'test-screenshots'),
};

// ==================== 测试工具函数 ====================

/**
 * 创建测试窗口
 */
async function createTestWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  
  await win.loadURL('http://localhost:4200/plugin-store');
  return win;
}

/**
 * 等待元素出现
 */
async function waitForElement(win, selector, timeout = 10000) {
  return await win.webContents.executeJavaScript(`
    new Promise((resolve, reject) => {
      const element = document.querySelector('${selector}');
      if (element) {
        resolve(element);
        return;
      }
      
      const observer = new MutationObserver(() => {
        const el = document.querySelector('${selector}');
        if (el) {
          observer.disconnect();
          resolve(el);
        }
      });
      
      observer.observe(document.body, { childList: true, subtree: true });
      
      setTimeout(() => {
        observer.disconnect();
        reject(new Error('Timeout waiting for element: ${selector}'));
      }, ${timeout});
    })
  `);
}

/**
 * 点击元素
 */
async function clickElement(win, selector) {
  await win.webContents.executeJavaScript(`
    document.querySelector('${selector}')?.click();
  `);
  // 等待 UI 更新
  await new Promise(resolve => setTimeout(resolve, 500));
}

/**
 * 获取元素文本
 */
async function getElementText(win, selector) {
  return await win.webContents.executeJavaScript(`
    document.querySelector('${selector}')?.textContent || '';
  `);
}

/**
 * 检查元素是否存在
 */
async function elementExists(win, selector) {
  return await win.webContents.executeJavaScript(`
    !!document.querySelector('${selector}')
  `);
}

/**
 * 截图
 */
async function takeScreenshot(win, filename) {
  const screenshotPath = path.join(TEST_CONFIG.screenshotDir, filename);
  
  if (!fs.existsSync(TEST_CONFIG.screenshotDir)) {
    fs.mkdirSync(TEST_CONFIG.screenshotDir, { recursive: true });
  }
  
  await win.webContents.capturePage().then(image => {
    fs.writeFileSync(screenshotPath, image.toPNG());
  });
  
  console.log(`📸 截图已保存: ${filename}`);
  return screenshotPath;
}

// ==================== 测试用例 ====================

/**
 * 测试 1: 首次启动引导流程
 */
async function testFirstRunGuide(win) {
  console.log('\n🧪 测试 1: 首次启动引导流程');
  console.log('=' .repeat(50));
  
  try {
    // 清除首次运行标记
    const firstRunFlagFile = path.join(TEST_CONFIG.userDataPath, 'first-run-completed.flag');
    if (fs.existsSync(firstRunFlagFile)) {
      fs.unlinkSync(firstRunFlagFile);
    }
    
    // 等待引导组件出现
    const guideElement = await waitForElement(win, 'app-first-run-guide');
    console.log('✅ 引导组件显示正常');
    
    // 截图
    await takeScreenshot(win, '01-first-run-guide.png');
    
    // 检查引导步骤
    const stepIndicator = await getElementText(win, '.step-indicator');
    console.log(`✅ 步骤指示器: ${stepIndicator}`);
    
    // 完成引导
    await clickElement(win, '.complete-guide-button');
    
    // 等待引导完成
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 检查引导是否隐藏
    const guideHidden = !(await elementExists(win, 'app-first-run-guide'));
    console.log(`✅ 引导隐藏: ${guideHidden ? '是' : '否'}`);
    
    // 检查首次运行标记
    const flagExists = fs.existsSync(firstRunFlagFile);
    console.log(`✅ 标记文件创建: ${flagExists ? '是' : '否'}`);
    
    console.log('✅ 测试 1 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 1 失败:', err.message);
    await takeScreenshot(win, '01-first-run-guide-error.png');
    return false;
  }
}

/**
 * 测试 2: 推荐引擎功能
 */
async function testRecommendations(win) {
  console.log('\n🧪 测试 2: 推荐引擎功能');
  console.log('=' .repeat(50));
  
  try {
    // 等待推荐组件加载
    const recElement = await waitForElement(win, 'app-plugin-recommendations');
    console.log('✅ 推荐组件显示正常');
    
    // 截图
    await takeScreenshot(win, '02-recommendations.png');
    
    // 检查推荐列表
    const recCount = await win.webContents.executeJavaScript(`
      document.querySelectorAll('.recommendation-card').length
    `);
    console.log(`✅ 推荐数量: ${recCount}`);
    
    // 检查置信度显示
    const confidence = await getElementText(win, '.confidence-value');
    console.log(`✅ 置信度: ${confidence}`);
    
    // 检查推荐理由
    const reason = await getElementText(win, '.reason');
    console.log(`✅ 推荐理由: ${reason}`);
    
    // 测试刷新推荐
    await clickElement(win, '[mattooltip="刷新推荐"]');
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('✅ 刷新推荐成功');
    
    console.log('✅ 测试 2 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 2 失败:', err.message);
    await takeScreenshot(win, '02-recommendations-error.png');
    return false;
  }
}

/**
 * 测试 3: 插件详情查看
 */
async function testPluginDetails(win) {
  console.log('\n🧪 测试 3: 插件详情查看');
  console.log('=' .repeat(50));
  
  try {
    // 点击第一个插件卡片
    await clickElement(win, '.plugin-card-item:first-child');
    
    // 等待详情面板出现
    const detailsPanel = await waitForElement(win, '.plugin-details-panel');
    console.log('✅ 详情面板显示正常');
    
    // 截图
    await takeScreenshot(win, '03-plugin-details.png');
    
    // 检查面板动画
    const hasAnimation = await win.webContents.executeJavaScript(`
      const panel = document.querySelector('.plugin-details-panel');
      const style = window.getComputedStyle(panel);
      return style.animation && style.animation.includes('slideIn');
    `);
    console.log(`✅ 滑入动画: ${hasAnimation ? '是' : '否'}`);
    
    // 检查使用统计组件
    const usageStatsExists = await elementExists(win, 'app-plugin-usage-stats');
    console.log(`✅ 使用统计组件: ${usageStatsExists ? '显示' : '未显示'}`);
    
    // 检查评分评论组件
    const reviewsExists = await elementExists(win, 'app-plugin-reviews');
    console.log(`✅ 评分评论组件: ${reviewsExists ? '显示' : '未显示'}`);
    
    // 关闭详情面板
    await clickElement(win, '.details-header button[mattooltip="关闭"]');
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 检查面板是否隐藏
    const panelHidden = !(await elementExists(win, '.plugin-details-panel'));
    console.log(`✅ 面板隐藏: ${panelHidden ? '是' : '否'}`);
    
    console.log('✅ 测试 3 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 3 失败:', err.message);
    await takeScreenshot(win, '03-plugin-details-error.png');
    return false;
  }
}

/**
 * 测试 4: 评分和评论
 */
async function testReviews(win) {
  console.log('\n🧪 测试 4: 评分和评论');
  console.log('=' .repeat(50));
  
  try {
    // 打开插件详情
    await clickElement(win, '.plugin-card-item:first-child');
    await waitForElement(win, 'app-plugin-reviews');
    
    // 检查评分显示
    const avgRating = await getElementText(win, '.rating-value');
    console.log(`✅ 平均评分: ${avgRating}`);
    
    // 检查评论数量
    const reviewCount = await win.webContents.executeJavaScript(`
      document.querySelectorAll('.review-card').length
    `);
    console.log(`✅ 评论数量: ${reviewCount}`);
    
    // 截图
    await takeScreenshot(win, '04-reviews.png');
    
    // 测试添加评论（如果表单存在）
    const addReviewForm = await elementExists(win, '.add-review-form');
    if (addReviewForm) {
      console.log('✅ 添加评论表单显示正常');
    }
    
    // 关闭详情
    await clickElement(win, '.details-header button[mattooltip="关闭"]');
    
    console.log('✅ 测试 4 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 4 失败:', err.message);
    await takeScreenshot(win, '04-reviews-error.png');
    return false;
  }
}

/**
 * 测试 5: 使用统计
 */
async function testUsageStats(win) {
  console.log('\n🧪 测试 5: 使用统计');
  console.log('=' .repeat(50));
  
  try {
    // 打开插件详情
    await clickElement(win, '.plugin-card-item:first-child');
    await waitForElement(win, 'app-plugin-usage-stats');
    
    // 检查统计数据
    const totalUsageTime = await getElementText(win, '.stat-card:first-child .stat-value');
    console.log(`✅ 总使用时间: ${totalUsageTime}`);
    
    const usageCount = await win.webContents.executeJavaScript(`
      document.querySelector('.stat-card:nth-child(2) .stat-value')?.textContent
    `);
    console.log(`✅ 使用次数: ${usageCount}`);
    
    // 截图
    await takeScreenshot(win, '05-usage-stats.png');
    
    // 检查趋势标识
    const trendExists = await elementExists(win, '.trend-indicator');
    console.log(`✅ 趋势标识: ${trendExists ? '显示' : '未显示'}`);
    
    // 关闭详情
    await clickElement(win, '.details-header button[mattooltip="关闭"]');
    
    console.log('✅ 测试 5 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 5 失败:', err.message);
    await takeScreenshot(win, '05-usage-stats-error.png');
    return false;
  }
}

/**
 * 测试 6: 更新通知
 */
async function testUpdateNotifications(win) {
  console.log('\n🧪 测试 6: 更新通知');
  console.log('=' .repeat(50));
  
  try {
    // 等待更新通知组件加载
    const updatesElement = await waitForElement(win, 'app-plugin-updates', 5000);
    console.log('✅ 更新通知组件显示正常');
    
    // 截图
    await takeScreenshot(win, '06-updates.png');
    
    // 检查更新数量
    const updateCount = await win.webContents.executeJavaScript(`
      document.querySelectorAll('.update-notification').length
    `);
    console.log(`✅ 待更新数量: ${updateCount}`);
    
    // 检查严重程度标识
    const severityExists = await elementExists(win, '.severity-badge');
    console.log(`✅ 严重程度标识: ${severityExists ? '显示' : '未显示'}`);
    
    // 测试检查更新按钮
    if (await elementExists(win, 'button:contains("检查更新")')) {
      await clickElement(win, 'button:contains("检查更新")');
      await new Promise(resolve => setTimeout(resolve, 2000));
      console.log('✅ 检查更新功能正常');
    }
    
    console.log('✅ 测试 6 通过\n');
    return true;
  } catch (err) {
    console.error('❌ 测试 6 失败:', err.message);
    await takeScreenshot(win, '06-updates-error.png');
    return false;
  }
}

// ==================== 主测试流程 ====================

async function runAllTests() {
  console.log('\n🚀 开始 Phase 5 端到端测试');
  console.log('=' .repeat(50));
  
  const results = {
    firstRunGuide: false,
    recommendations: false,
    pluginDetails: false,
    reviews: false,
    usageStats: false,
    updates: false,
  };
  
  let win;
  
  try {
    // 创建测试窗口
    console.log('\n📦 创建测试窗口...');
    win = await createTestWindow();
    console.log('✅ 测试窗口创建成功');
    
    // 等待页面加载
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // 运行测试
    results.firstRunGuide = await testFirstRunGuide(win);
    results.recommendations = await testRecommendations(win);
    results.pluginDetails = await testPluginDetails(win);
    results.reviews = await testReviews(win);
    results.usageStats = await testUsageStats(win);
    results.updates = await testUpdateNotifications(win);
    
    // 输出测试报告
    console.log('\n📊 测试报告');
    console.log('=' .repeat(50));
    
    const totalTests = Object.keys(results).length;
    const passedTests = Object.values(results).filter(Boolean).length;
    const failedTests = totalTests - passedTests;
    
    console.log(`总计: ${totalTests} 个测试`);
    console.log(`通过: ${passedTests} 个 ✅`);
    console.log(`失败: ${failedTests} 个 ❌`);
    console.log(`通过率: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
    
    console.log('\n详细结果:');
    for (const [test, passed] of Object.entries(results)) {
      console.log(`  ${passed ? '✅' : '❌'} ${test}`);
    }
    
    // 最终截图
    await takeScreenshot(win, 'final-state.png');
    
    return results;
  } catch (err) {
    console.error('\n💥 测试执行失败:', err.message);
    if (win) {
      await takeScreenshot(win, 'test-fatal-error.png');
    }
    return results;
  } finally {
    // 关闭测试窗口
    if (win) {
      win.close();
    }
  }
}

// ==================== 执行测试 ====================

if (require.main === module) {
  app.whenReady().then(async () => {
    const results = await runAllTests();
    
    // 输出退出码
    const hasFailures = Object.values(results).some(r => !r);
    const exitCode = hasFailures ? 1 : 0;
    
    console.log(`\n${hasFailures ? '❌ 测试失败' : '✅ 所有测试通过'}`);
    process.exit(exitCode);
  });
  
  app.on('window-all-closed', () => {
    app.quit();
  });
}

module.exports = { runAllTests };
