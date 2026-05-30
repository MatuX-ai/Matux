是/**
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
});

console.log('[Splash Preload] 启动画面预加载脚本已就绪');
