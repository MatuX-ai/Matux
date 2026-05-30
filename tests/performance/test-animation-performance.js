/**
 * 动效性能自动化测试脚本
 *
 * 使用说明:
 * 1. 启动应用：ng serve
 * 2. 运行测试：node tests/performance/test-animation-performance.js
 *
 * 依赖安装:
 * npm install --save-dev puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// 测试配置
const CONFIG = {
  url: 'http://localhost:4200', // 本地开发服务器地址
  testPage: '/tests/performance/animation-performance-test.html',
  outputDir: path.join(__dirname, '../../dist/performance-reports'),
  maxAnimationDuration: 1000, // 最大动画时长（ms）
  minFPS: 30, // 最低可接受帧率
};

// 确保输出目录存在
if (!fs.existsSync(CONFIG.outputDir)) {
  fs.mkdirSync(CONFIG.outputDir, { recursive: true });
}

async function runPerformanceTests() {
  console.log('🚀 开始动效性能测试...\n');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
  });

  const page = await browser.newPage();

  // 启用性能监控
  await page.setCacheEnabled(false);
  const client = await page.target().createCDPSession();
  await client.send('Performance.enable');

  const results = {
    timestamp: new Date().toISOString(),
    tests: [],
    summary: {
      total: 0,
      passed: 0,
      failed: 0,
    },
  };

  try {
    // 测试 1: Hero 区渐显动效
    console.log('📊 测试 1: Hero 区渐显动效');
    await page.goto(`${CONFIG.url}${CONFIG.testPage}`, { waitUntil: 'networkidle0' });

    // 等待所有动画完成
    await page.waitForTimeout(2000);

    // 获取动画时长
    const animationMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        let animations = [];

        // 监听 CSS 动画
        document.addEventListener('animationstart', (e) => {
          animations.push({
            name: e.animationName,
            startTime: performance.now(),
          });
        });

        // 1 秒后收集数据
        setTimeout(() => {
          const durations = animations.map(a => {
            const element = document.querySelector(`[style*="animation-name: ${a.name}"]`);
            if (element) {
              const style = getComputedStyle(element);
              return parseFloat(style.animationDuration) * 1000;
            }
            return 0;
          });

          resolve({
            totalAnimations: animations.length,
            maxDuration: Math.max(...durations),
            avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length || 0,
          });
        }, 1000);
      });
    });

    const heroTestResult = {
      name: 'Hero 区渐显动效',
      metrics: animationMetrics,
      passed: animationMetrics.maxDuration <= CONFIG.maxAnimationDuration,
      details: `最大动画时长：${animationMetrics.maxDuration.toFixed(0)}ms (标准：≤${CONFIG.maxAnimationDuration}ms)`,
    };

    results.tests.push(heroTestResult);
    console.log(`   ${heroTestResult.passed ? '✅' : '❌'} ${heroTestResult.details}\n`);

    // 测试 2: 卡片 Hover 动效性能
    console.log('📊 测试 2: 卡片 Hover 动效性能');

    const hoverMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const card = document.querySelector('.test-card');
        if (!card) {
          resolve({ error: '未找到测试卡片' });
          return;
        }

        let frameCount = 0;
        let lastTime = performance.now();
        let fpsValues = [];

        function measureFPS() {
          const now = performance.now();
          frameCount++;

          if (now - lastTime >= 500) {
            fpsValues.push(frameCount / ((now - lastTime) / 1000));
            frameCount = 0;
            lastTime = now;
          }

          if (fpsValues.length < 3) {
            requestAnimationFrame(measureFPS);
          } else {
            resolve({
              avgFPS: fpsValues.reduce((a, b) => a + b, 0) / fpsValues.length,
              minFPS: Math.min(...fpsValues),
            });
          }
        }

        // 触发 hover
        card.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        measureFPS();
      });
    });

    const hoverTestResult = {
      name: '卡片 Hover 动效',
      metrics: hoverMetrics,
      passed: hoverMetrics.avgFPS >= CONFIG.minFPS,
      details: `平均帧率：${hoverMetrics.avgFPS.toFixed(1)} fps (标准：≥${CONFIG.minFPS}fps)`,
    };

    results.tests.push(hoverTestResult);
    console.log(`   ${hoverTestResult.passed ? '✅' : '❌'} ${hoverTestResult.details}\n`);

    // 测试 3: 按钮响应时间
    console.log('📊 测试 3: 按钮响应时间');

    const buttonMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const button = document.querySelector('.btn-primary');
        if (!button) {
          resolve({ error: '未找到测试按钮' });
          return;
        }

        const startTime = performance.now();
        let transitionStarted = false;
        let transitionEnded = false;

        button.addEventListener('transitionstart', () => {
          transitionStarted = true;
        });

        button.addEventListener('transitionend', () => {
          if (transitionStarted && !transitionEnded) {
            transitionEnded = true;
            const duration = performance.now() - startTime;
            resolve({ duration });
          }
        });

        // 触发 hover
        button.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));

        // 超时处理
        setTimeout(() => {
          if (!transitionEnded) {
            resolve({ duration: performance.now() - startTime, timeout: true });
          }
        }, 2000);
      });
    });

    const buttonTestResult = {
      name: '按钮 Hover 响应',
      metrics: buttonMetrics,
      passed: buttonMetrics.duration <= 200, // 200ms 内完成过渡
      details: `响应时间：${buttonMetrics.duration.toFixed(0)}ms (标准：≤200ms)`,
    };

    results.tests.push(buttonTestResult);
    console.log(`   ${buttonTestResult.passed ? '✅' : '❌'} ${buttonTestResult.details}\n`);

    // 测试 4: 滚动渐入性能
    console.log('📊 测试 4: 滚动渐入性能');

    const scrollMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        const scrollItems = document.querySelectorAll('.scroll-item');
        if (scrollItems.length === 0) {
          resolve({ error: '未找到滚动条目' });
          return;
        }

        let animatedCount = 0;
        const startTime = performance.now();

        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              animatedCount++;

              if (animatedCount === scrollItems.length) {
                const duration = performance.now() - startTime;
                resolve({
                  totalItems: scrollItems.length,
                  animatedCount,
                  duration,
                });
              }
            }
          });
        }, { threshold: 0.1 });

        scrollItems.forEach(item => observer.observe(item));

        // 模拟滚动到底部
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });

        // 超时处理
        setTimeout(() => {
          resolve({
            totalItems: scrollItems.length,
            animatedCount,
            duration: performance.now() - startTime,
            timeout: true,
          });
        }, 3000);
      });
    });

    const scrollTestResult = {
      name: '滚动渐入动效',
      metrics: scrollMetrics,
      passed: scrollMetrics.duration <= 1000,
      details: `总耗时：${scrollMetrics.duration.toFixed(0)}ms (标准：≤1000ms, 条目数：${scrollMetrics.animatedCount}/${scrollMetrics.totalItems})`,
    };

    results.tests.push(scrollTestResult);
    console.log(`   ${scrollTestResult.passed ? '✅' : '❌'} ${scrollTestResult.details}\n`);

    // 生成汇总报告
    results.summary.total = results.tests.length;
    results.summary.passed = results.tests.filter(t => t.passed).length;
    results.summary.failed = results.summary.total - results.summary.passed;

    // 保存测试结果
    const reportPath = path.join(
      CONFIG.outputDir,
      `animation-performance-${Date.now()}.json`
    );
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));

    // 输出总结
    console.log('='.repeat(60));
    console.log('📋 测试总结');
    console.log('='.repeat(60));
    console.log(`总测试数：${results.summary.total}`);
    console.log(`✅ 通过：${results.summary.passed}`);
    console.log(`❌ 失败：${results.summary.failed}`);
    console.log(`\n详细报告已保存至：${reportPath}`);
    console.log('='.repeat(60));

    // 如果有失败的测试，退出错误码
    if (results.summary.failed > 0) {
      console.log('\n❌ 部分测试未通过，请检查优化效果！\n');
      process.exit(1);
    } else {
      console.log('\n✅ 所有测试通过！动效性能符合标准！\n');
      process.exit(0);
    }

  } catch (error) {
    console.error('测试执行失败:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// 运行测试
runPerformanceTests().catch(console.error);
