/**
 * 我的插件 - Electron 主进程
 * 
 * 处理插件的 Electron IPC 通信。
 */

const { ipcMain } = require('electron');

/**
 * 注册 IPC 处理器
 */
function registerIPCHandlers() {
  console.log('[MyPlugin] 注册 IPC 处理器...');
  
  /**
   * 处理动作 1
   */
  ipcMain.handle('my-plugin:action1', async (event, data) => {
    try {
      console.log('[MyPlugin] 执行动作 1:', data);
      
      // 业务逻辑
      const result = {
        success: true,
        message: '动作 1 执行成功',
        data: {
          input: data,
          timestamp: Date.now(),
        },
      };
      
      return result;
    } catch (err) {
      console.error('[MyPlugin] 动作 1 失败:', err.message);
      return {
        success: false,
        error: err.message,
      };
    }
  });
  
  /**
   * 处理动作 2
   */
  ipcMain.handle('my-plugin:action2', async (event, data) => {
    try {
      console.log('[MyPlugin] 执行动作 2:', data);
      
      // 业务逻辑
      const result = {
        success: true,
        message: '动作 2 执行成功',
        data: {
          input: data,
          processed: true,
        },
      };
      
      return result;
    } catch (err) {
      console.error('[MyPlugin] 动作 2 失败:', err.message);
      return {
        success: false,
        error: err.message,
      };
    }
  });
  
  console.log('[MyPlugin] ✓ IPC 处理器注册完成');
}

/**
 * 卸载 IPC 处理器
 */
function unregisterIPCHandlers() {
  console.log('[MyPlugin] 卸载 IPC 处理器...');
  
  ipcMain.removeHandler('my-plugin:action1');
  ipcMain.removeHandler('my-plugin:action2');
  
  console.log('[MyPlugin] ✓ IPC 处理器卸载完成');
}

// 导出
module.exports = {
  registerIPCHandlers,
  unregisterIPCHandlers,
};

// 自动注册
if (require.main === module) {
  registerIPCHandlers();
}
