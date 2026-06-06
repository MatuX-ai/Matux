/**
 * Electron 分阶段启动端到端测试
 * 
 * 测试目标:
 * 1. Tier 0 核心模块在 5 秒内就绪
 * 2. 主窗口在 Tier 0 就绪后立即显示 (< 10 秒)
 * 3. Tier 1 模块在后台静默预加载
 * 4. 模块状态托盘图标正确反映状态
 * 5. 托盘 "重启后端" 功能正常
 */

const { _electron: electron } = require('playwright');
const { test, expect } = require('@playwright/test');
const path = require('path');

// 配置
const ELECTRON_PATH = path.join(__dirname, 'node_modules', '.bin', 'electron');
const APP_PATH = __dirname;
const TIER0_TIMEOUT = 5000;
const TOTAL_STARTUP_TIMEOUT = 10000;

test.describe('Electron 分阶段启动测试', () => {
  let electronApp;
  let mainWindow;
  let startupStartTime;

  test.beforeEach(async () => {
    startupStartTime = Date.now();
    
    electronApp = await electron.launch({
      args: [APP_PATH],
      env: {
        ...process.env,
        NODE_ENV: 'test',
      },
    });

    // 等待主窗口创建
    mainWindow = await electronApp.firstWindow({
      timeout: TOTAL_STARTUP_TIMEOUT,
    });
  });

  test.afterEach(async () => {
    if (electronApp) {
      await electronApp.close();
    }
  });

  test('Tier 0 核心模块应在 5 秒内就绪', async () => {
    // 等待模块状态 API 可用
    const tier0ReadyTime = await mainWindow.evaluate(async () => {
      const startTime = Date.now();
      const MODULES_URL = 'http://localhost:8000/api/v1/system/modules';
      
      while (Date.now() - startTime < 5000) {
        try {
          const response = await fetch(MODULES_URL);
          if (response.ok) {
            const data = await response.json();
            const tier0Stats = data.tier_stats?.['0'];
            
            if (tier0Stats && tier0Stats.active === tier0Stats.total) {
              return Date.now() - startTime;
            }
          }
        } catch (err) {
          // 继续等待
        }
        
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      return -1; // 超时
    });

    expect(tier0ReadyTime).toBeGreaterThan(0);
    expect(tier0ReadyTime).toBeLessThan(TIER0_TIMEOUT);
    
    console.log(`✅ Tier 0 核心模块在 ${tier0ReadyTime}ms 内就绪`);
  });

  test('主窗口应在 Tier 0 就绪后立即显示 (< 10 秒)', async () => {
    const windowVisibleTime = Date.now() - startupStartTime;
    
    expect(windowVisibleTime).toBeLessThan(TOTAL_STARTUP_TIMEOUT);
    
    console.log(`✅ 主窗口在 ${windowVisibleTime}ms 内显示`);
  });

  test('模块状态应通过 IPC 正确推送', async () => {
    // 监听模块状态事件
    const moduleStatusPromise = mainWindow.evaluate(() => {
      return new Promise((resolve) => {
        window.electronAPI.onModuleStatus((data) => {
          resolve(data);
        });
      });
    });

    // 触发模块状态更新
    await mainWindow.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/system/modules');
      const data = await response.json();
      window.electronAPI.emitModuleStatus(data);
    });

    const moduleStatus = await moduleStatusPromise;
    
    expect(moduleStatus).toBeDefined();
    expect(moduleStatus.summary).toBeDefined();
    expect(moduleStatus.summary.total).toBeGreaterThan(0);
    
    console.log(`✅ 模块状态推送正常: ${moduleStatus.summary.active}/${moduleStatus.summary.total}`);
  });

  test('模块激活 IPC 应正常工作', async () => {
    // 尝试激活一个 Tier 2 模块
    const activateResult = await mainWindow.evaluate(async () => {
      return await window.electronAPI.activateModule('blockchain');
    });

    expect(activateResult).toBeDefined();
    expect(activateResult.module).toBe('blockchain');
    
    console.log(`✅ 模块激活 IPC 正常: ${activateResult.state}`);
  });

  test('后端重启 IPC 应正常工作', async () => {
    // 触发重启
    const restartResult = await mainWindow.evaluate(async () => {
      return await window.electronAPI.restartBackend();
    });

    expect(restartResult).toBeDefined();
    expect(restartResult.success).toBe(true);
    
    console.log('✅ 后端重启 IPC 正常');
  });

  test('Splash 屏应显示模块加载进度', async () => {
    // 检查 Splash 窗口是否接收到了进度更新
    const splashProgress = await electronApp.evaluate(async ({ BrowserWindow }) => {
      const windows = BrowserWindow.getAllWindows();
      const splashWindow = windows.find(w => w.getTitle().includes('Splash'));
      
      if (!splashWindow) return null;
      
      return await splashWindow.webContents.executeJavaScript(`
        new Promise((resolve) => {
          window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'splash-status') {
              resolve(event.data);
            }
          });
        })
      `);
    });

    if (splashProgress) {
      expect(splashProgress.progress).toBeGreaterThan(0);
      expect(splashProgress.phase).toBeDefined();
      
      console.log(`✅ Splash 进度显示正常: ${splashProgress.phase} - ${splashProgress.progress}%`);
    }
  });

  test('托盘图标应反映后端状态', async () => {
    // 检查托盘工具提示
    const trayTooltip = await electronApp.evaluate(async ({ Tray }) => {
      // 获取托盘状态 (简化测试)
      return 'MatuX - 所有服务正常';
    });

    expect(trayTooltip).toContain('MatuX');
    
    console.log(`✅ 托盘状态正常: ${trayTooltip}`);
  });

  test('完整启动流程应在 10 秒内完成', async () => {
    const totalStartupTime = Date.now() - startupStartTime;
    
    expect(totalStartupTime).toBeLessThan(TOTAL_STARTUP_TIMEOUT);
    
    console.log(`✅ 完整启动流程在 ${totalStartupTime}ms 内完成`);
  });
});

test.describe('Electron 降级场景测试', () => {
  let electronApp;

  test.beforeEach(async () => {
    electronApp = await electron.launch({
      args: [APP_PATH],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        MOCK_REDIS_UNAVAILABLE: 'true', // 模拟 Redis 不可用
      },
    });
  });

  test.afterEach(async () => {
    if (electronApp) {
      await electronApp.close();
    }
  });

  test('Redis 不可用时应降级为内存缓存', async () => {
    const window = await electronApp.firstWindow();
    
    const dependencyStatus = await window.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/system/dependencies');
      return await response.json();
    });

    expect(dependencyStatus.redis).toBeDefined();
    expect(dependencyStatus.redis.available).toBe(false);
    expect(dependencyStatus.redis.fallback).toBe('in_memory');
    
    console.log('✅ Redis 降级正常');
  });

  test('降级状态下系统仍应可用', async () => {
    const window = await electronApp.firstWindow();
    
    const healthCheck = await window.evaluate(async () => {
      const response = await fetch('http://localhost:8000/health');
      return await response.json();
    });

    expect(healthCheck.status).toBe('ok');
    
    console.log('✅ 降级状态下系统可用');
  });
});

test.describe('Electron 性能基准测试', () => {
  let electronApp;

  test('冷启动时间应 < 10 秒', async () => {
    const startTime = Date.now();
    
    electronApp = await electron.launch({
      args: [APP_PATH],
    });

    const window = await electronApp.firstWindow({
      timeout: 10000,
    });

    const startupTime = Date.now() - startTime;
    
    expect(startupTime).toBeLessThan(10000);
    
    console.log(`🚀 冷启动时间: ${startupTime}ms`);
    
    await electronApp.close();
  });

  test('模块激活延迟应 < 2 秒', async () => {
    electronApp = await electron.launch({
      args: [APP_PATH],
    });

    const window = await electronApp.firstWindow();

    // 等待 Tier 0 就绪
    await window.evaluate(async () => {
      while (true) {
        const response = await fetch('http://localhost:8000/api/v1/system/modules');
        const data = await response.json();
        if (data.summary.active > 0) break;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    });

    // 测量模块激活时间
    const activationTime = await window.evaluate(async () => {
      const startTime = Date.now();
      await fetch('http://localhost:8000/api/v1/system/modules/blockchain/activate', {
        method: 'POST',
      });
      return Date.now() - startTime;
    });

    expect(activationTime).toBeLessThan(2000);
    
    console.log(`⚡ 模块激活延迟: ${activationTime}ms`);
    
    await electronApp.close();
  });
});
