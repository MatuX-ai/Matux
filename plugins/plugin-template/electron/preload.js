/**
 * 我的插件 - Electron 预加载脚本
 * 
 * 暴露安全的 API 给渲染进程。
 */

const { contextBridge, ipcRenderer } = require('electron');

// 暴露 API 给渲染进程
contextBridge.exposeInMainWorld('myPluginAPI', {
  /**
   * 执行动作 1
   */
  action1: (data) => ipcRenderer.invoke('my-plugin:action1', data),
  
  /**
   * 执行动作 2
   */
  action2: (data) => ipcRenderer.invoke('my-plugin:action2', data),
  
  /**
   * 监听事件（示例）
   */
  onEvent: (callback) => {
    const subscription = (event, data) => callback(data);
    ipcRenderer.on('my-plugin:event', subscription);
    
    // 返回取消订阅函数
    return () => {
      ipcRenderer.removeListener('my-plugin:event', subscription);
    };
  },
});

console.log('[MyPlugin] ✓ 预加载脚本执行完成');
