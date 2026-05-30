/**
 * Electron 预加载脚本
 *
 * 在渲染进程和主进程之间建立安全桥接
 */
const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // ==================== 后端通信 ====================

  /**
   * 获取后端服务 URL
   */
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

  /**
   * 执行健康检查
   */
  healthCheck: () => ipcRenderer.invoke('health-check'),

  /**
   * 获取应用信息
   */
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // ==================== 文件系统操作 ====================

  /**
   * 读取文件内容
   */
  readFile: (filePath) => ipcRenderer.invoke('fs-read-file', filePath),

  /**
   * 写入文件内容（文本或二进制数据）
   */
  writeFile: (filePath, content) => ipcRenderer.invoke('fs-write-file', filePath, content),

  /**
   * 打开保存文件对话框
   * @param opts 可选的对话框选项（文件过滤器等）
   */
  showSaveDialog: (opts) => ipcRenderer.invoke('fs-save-dialog', opts),

  /**
   * 打开文件对话框
   */
  showOpenDialog: () => ipcRenderer.invoke('fs-open-dialog'),

  /**
   * 打开外部链接（系统默认浏览器）
   */
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // ==================== 原生功能 ====================

  /**
   * 发送原生系统通知
   */
  showNotification: (title, body, category) =>
    ipcRenderer.invoke('show-notification', title, body, category),

  /**
   * 检查应用更新
   */
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),

  // ==================== 窗口控制 ====================

  /**
   * 窗口操作
   */
  windowControl: (action) => {
    ipcRenderer.send('app-event', { type: action });
  },

  /**
   * 获取当前窗口尺寸
   */
  getWindowSize: () => ipcRenderer.invoke('get-window-size'),

  // ==================== 事件通信 ====================

  /**
   * 发送消息到主进程
   */
  send: (channel, data) => {
    const validChannels = ['to-backend', 'app-event'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },

  /**
   * 监听事件（支持自定义回调）
   */
  on: (channel, func) => {
    const validChannels = ['app-event', 'from-backend', 'window-blur', 'window-focus',
      'fullscreen-enter', 'fullscreen-leave', 'window-resize', 'open-file',
      'update-available', 'backend-disconnected', 'backend-reconnected'];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => func(...args));
    }
  },

  /**
   * 从主进程接收消息（兼容旧 API）
   */
  receive: (channel, func) => {
    const validChannels = ['from-backend', 'app-event'];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => func(...args));
    }
  },

  /**
   * 移除消息监听
   */
  removeListener: (channel, func) => {
    ipcRenderer.removeListener(channel, func);
  },

  /**
   * 移除所有消息监听
   */
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  },
});

console.log('[Preload] Electron 预加载脚本已加载');
