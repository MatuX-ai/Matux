/**
 * Splash Screen 预加载脚本
 *
 * 为启动画面提供安全的 IPC 通信
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('splashAPI', {
  /**
   * 接收主进程状态更新
   */
  onStatusUpdate: (callback) => {
    ipcRenderer.on('splash-status', (_event, data) => callback(data));
  },

  /**
   * 向主进程发送重试请求
   */
  retry: () => {
    ipcRenderer.send('splash-retry');
  },

  /**
   * 通知主进程 Splash 已切换到迷你模式（主进程据此调整窗口尺寸并贴底）
   */
  notifyMiniMode: () => {
    ipcRenderer.send('splash-mini-mode');
  },

  /**
   * 【降级入口】用户主动点击"跳过"，主进程应立即标记为降级模式
   * - 关闭 Splash 窗口
   * - 主窗口 ready-to-show 后立即显示（即使后端未就绪）
   * - 通知前端进入前端降级模式
   */
  skip: () => {
    ipcRenderer.send('splash-skip');
  },

  /**
   * 【启动优化 P1-2】通知主进程 Splash 淡出动画已完成
   * 主进程收到后可以立即关闭窗口（无需硬等 900ms）
   */
  notifyFadeOutComplete: () => {
    ipcRenderer.send('splash-fadeout-complete');
  },

  /**
   * 【复用模式修复】用户点击“强制重启”按钮：主进程杀掉占位进程并重新拉起后端
   */
  forceRestart: () => {
    ipcRenderer.send('splash-force-restart');
  },

  /**
   * 退出应用
   */
  quit: () => {
    ipcRenderer.send('splash-quit');
  },
});

console.log('[Splash Preload] 启动画面预加载脚本已就绪');
