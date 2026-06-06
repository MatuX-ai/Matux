/**
 * Electron 分阶段后端启动增强模块
 * 
 * 优化点:
 * 1. Tier 0 就绪后立即显示主窗口 (< 10 秒)
 * 2. Tier 1 后台静默预加载 (不阻塞 UI)
 * 3. Splash 屏显示真实模块进度
 * 4. 模块状态托盘图标动态更新
 */

const { ipcMain, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

// ==================== 配置 ====================

const TIER0_HEALTH_URL = 'http://localhost:8000/api/v1/system/health?tier=0';
const MODULES_URL = 'http://localhost:8000/api/v1/system/modules';
const TIER0_TIMEOUT = 5000;        // Tier 0 核心启动超时 5 秒
const TIER1_PRELOAD_TIMEOUT = 15000; // Tier 1 预加载超时 15 秒

// ==================== 分阶段启动 ====================

/**
 * 等待 Tier 0 核心模块就绪
 * 
 * @param {number} timeout - 超时时间 (毫秒)
 * @returns {Promise<boolean>} - 是否成功
 */
async function waitForTier0Ready(timeout = TIER0_TIMEOUT) {
  const startTime = Date.now();
  
  console.log('[INFO] 等待 Tier 0 核心模块就绪...');
  
  while (Date.now() - startTime < timeout) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(TIER0_HEALTH_URL, { signal: controller.signal });
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        
        // 检查 Tier 0 模块是否全部活跃
        const tier0Stats = data.tier_stats?.['0'];
        if (tier0Stats && tier0Stats.active === tier0Stats.total) {
          console.log(`[INFO] ✅ Tier 0 核心模块已就绪 (${tier0Stats.active}/${tier0Stats.total})`);
          return true;
        }
        
        // 部分就绪,继续等待
        console.log(`[INFO] Tier 0 加载中... (${tier0Stats?.active || 0}/${tier0Stats?.total || 0})`);
      }
    } catch (err) {
      // 静默失败,继续重试
    }
    
    // 等待 500ms 后重试
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  console.error('[ERROR] ❌ Tier 0 核心模块启动超时');
  return false;
}

/**
 * 后台预加载 Tier 1 模块 (不阻塞 UI)
 * 
 * @param {BrowserWindow} mainWindow - 主窗口实例
 */
async function preloadTier1InBackground(mainWindow) {
  console.log('[INFO] 📦 开始后台预加载 Tier 1 模块...');
  
  try {
    // 等待 2 秒让 Tier 0 稳定
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIER1_PRELOAD_TIMEOUT);
    
    // 调用后端预加载接口
    const response = await fetch(`${MODULES_URL}/tier/1/preload`, {
      method: 'POST',
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json' },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      console.warn('[WARN] Tier 1 预加载接口调用失败:', response.status);
      return;
    }
    
    const data = await response.json();
    const results = data.results || {};
    const successCount = Object.values(results).filter(Boolean).length;
    
    console.log(`[INFO] ✅ Tier 1 预加载完成: ${successCount}/${Object.keys(results).length} 成功`);
    
    // 通知渲染进程
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('backend:tier1-loaded', {
        success: successCount,
        total: Object.keys(results).length,
        results,
      });
    }
  } catch (err) {
    console.warn('[WARN] Tier 1 后台预加载失败:', err.message);
  }
}

/**
 * 分阶段启动后端完整流程
 * 
 * @param {Function} startBackendFn - 原始 startBackend 函数
 * @param {Function} createMainWindowFn - 创建主窗口函数
 * @param {Function} sendSplashStatusFn - 发送 Splash 状态函数
 */
function createPhasedStartup(startBackendFn, createMainWindowFn, sendSplashStatusFn) {
  return async function startBackendPhased() {
    console.log('[INFO] 🚀 开始分阶段启动后端...');
    
    // Phase 1: 启动后端进程
    sendSplashStatusFn('starting-backend', '正在启动后端服务...', 20);
    startBackendFn();
    
    // Phase 2: 等待 Tier 0 核心模块就绪 (最多 5 秒)
    sendSplashStatusFn('waiting-tier0', '等待核心模块就绪...', 40);
    const tier0Ready = await waitForTier0Ready(TIER0_TIMEOUT);
    
    if (!tier0Ready) {
      console.error('[ERROR] Tier 0 启动失败,终止启动流程');
      sendSplashStatusFn('backend-error', '核心模块启动失败', 0, 'Tier 0 模块未能在规定时间内就绪');
      return false;
    }
    
    sendSplashStatusFn('tier0-ready', '核心模块就绪 ✓', 80);
    
    // Phase 3: Tier 0 就绪后立即创建主窗口
    sendSplashStatusFn('creating-window', '正在打开主窗口...', 85);
    createMainWindowFn();
    
    // 等待主窗口就绪
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Phase 4: 后台预加载 Tier 1 (不阻塞 UI)
    const mainWindow = BrowserWindow.getAllWindows().find(w => !w.isDestroyed());
    if (mainWindow) {
      preloadTier1InBackground(mainWindow);
    }
    
    sendSplashStatusFn('ready', '准备就绪', 100);
    
    console.log('[INFO] ✅ 分阶段启动完成');
    return true;
  };
}

// ==================== IPC 处理器 ====================

/**
 * 注册模块管理 IPC 处理器
 */
function registerModuleIpcHandlers() {
  // 获取模块状态
  ipcMain.handle('backend:get-module-status', async () => {
    try {
      const response = await fetch(MODULES_URL);
      if (!response.ok) return null;
      return await response.json();
    } catch (err) {
      console.error('[ERROR] 获取模块状态失败:', err.message);
      return null;
    }
  });
  
  // 激活模块
  ipcMain.handle('backend:activate-module', async (event, moduleName) => {
    try {
      const response = await fetch(`${MODULES_URL}/${moduleName}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) {
        return { success: false, error: '激活失败' };
      }
      
      return await response.json();
    } catch (err) {
      console.error(`[ERROR] 激活模块 ${moduleName} 失败:`, err.message);
      return { success: false, error: err.message };
    }
  });
}

module.exports = {
  waitForTier0Ready,
  preloadTier1InBackground,
  createPhasedStartup,
  registerModuleIpcHandlers,
};
