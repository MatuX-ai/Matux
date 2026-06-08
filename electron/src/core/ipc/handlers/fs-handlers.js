/**
 * 文件系统操作 IPC Handlers
 * 处理文件读写、目录操作等
 *
 * @module ipc/handlers/fs-handlers
 */

const fs = require('fs');
const path = require('path');

/**
 * 创建文件系统 IPC Handlers
 * @param {object} options 配置选项
 * @param {object} options.mainWindow 主窗口引用
 * @param {function} options.validateFilePath 文件路径验证函数
 * @param {object} options.dialog Electron dialog 模块
 * @returns {object} handlers 对象
 */
function createFsHandlers(options = {}) {
  const { mainWindow = null, validateFilePath = null, dialog = null } = options;

  const deps = {
    mainWindow,
    validateFilePath,
    dialog,
  };

  /**
   * 设置依赖
   */
  function setDependencies(newDeps) {
    Object.assign(deps, newDeps);
  }

  /**
   * 获取主窗口引用
   */
  function getMainWindow() {
    return deps.mainWindow;
  }

  /**
   * 注册文件系统 IPC handlers
   */
  function register() {
    const { ipcMain } = require('electron');

    // 读取文件
    ipcMain.handle('fs-read-file', async (_event, filePath) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(filePath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return { success: true, content };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 写入文件
    ipcMain.handle('fs-write-file', async (_event, filePath, content) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(filePath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        if (Buffer.isBuffer(content) || content instanceof ArrayBuffer) {
          fs.writeFileSync(filePath, Buffer.from(content));
        } else {
          fs.writeFileSync(filePath, content, 'utf-8');
        }
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 保存对话框
    ipcMain.handle('fs-save-dialog', async (_event, opts) => {
      if (!deps.mainWindow) return { success: false, error: '主窗口未就绪' };
      const defaultOpts = {
        title: '保存文件',
        filters: [
          { name: 'MatuX 项目文件', extensions: ['imato'] },
          { name: '所有文件', extensions: ['*'] },
        ],
      };
      const result = await deps.dialog.showSaveDialog(deps.mainWindow, opts || defaultOpts);
      return { success: !result.canceled, filePath: result.filePath };
    });

    // 打开对话框
    ipcMain.handle('fs-open-dialog', async () => {
      if (!deps.mainWindow) return { success: false, error: '主窗口未就绪' };
      const result = await deps.dialog.showOpenDialog(deps.mainWindow, {
        title: '打开项目文件',
        filters: [
          { name: 'MatuX 项目文件', extensions: ['imato'] },
          { name: '所有文件', extensions: ['*'] },
        ],
        properties: ['openFile'],
      });
      if (result.canceled || result.filePaths.length === 0) {
        return { success: false, error: '用户取消' };
      }
      const filePath = result.filePaths[0];
      try {
        const content = fs.readFileSync(filePath, 'utf-8');
        return { success: true, filePath, content };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 列出目录
    ipcMain.handle('fs-list-dir', async (_event, dirPath) => {
      // 参数验证
      if (!dirPath || typeof dirPath !== 'string') {
        return { success: false, error: '目录路径不能为空' };
      }
      
      // 路径验证
      const validation = deps.validateFilePath?.(dirPath);
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      
      try {
        if (!fs.existsSync(dirPath)) {
          return { success: false, error: '目录不存在' };
        }
        const stat = fs.statSync(dirPath);
        if (!stat.isDirectory()) {
          return { success: false, error: '路径不是目录' };
        }
        
        const entries = fs.readdirSync(dirPath, { withFileTypes: true });
        const files = entries.map((entry) => {
          const fullPath = path.join(dirPath, entry.name);
          let stat;
          try {
            stat = fs.statSync(fullPath);
          } catch {
            stat = { size: 0, mtimeMs: 0, isFile: () => false, isDirectory: () => false };
          }
          return {
            name: entry.name,
            isDirectory: entry.isDirectory(),
            isFile: entry.isFile(),
            size: stat.size,
            mtimeMs: stat.mtimeMs,
            path: fullPath,
          };
        });
        files.sort((a, b) => {
          if (a.isDirectory !== b.isDirectory) return a.isDirectory ? -1 : 1;
          return a.name.localeCompare(b.name);
        });
        return { success: true, files };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 创建目录
    ipcMain.handle('fs-make-dir', async (_event, dirPath) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(dirPath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        fs.mkdirSync(dirPath, { recursive: true });
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 删除文件或目录
    ipcMain.handle('fs-delete-file', async (_event, targetPath) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(targetPath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        if (!fs.existsSync(targetPath)) {
          return { success: false, error: '目标不存在' };
        }
        const stat = fs.statSync(targetPath);
        if (stat.isDirectory()) {
          fs.rmdirSync(targetPath);
        } else {
          fs.unlinkSync(targetPath);
        }
        return { success: true };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 检查文件存在
    ipcMain.handle('fs-file-exists', async (_event, targetPath) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(targetPath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        return { success: true, exists: fs.existsSync(targetPath) };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 获取文件信息
    ipcMain.handle('fs-get-file-info', async (_event, filePath) => {
      let validation;
      try {
        validation = deps.validateFilePath?.(filePath);
      } catch (err) {
        return { success: false, error: `路径验证失败: ${err.message}` };
      }
      if (!validation?.valid) {
        return { success: false, error: validation?.error || '路径验证失败' };
      }
      try {
        if (!fs.existsSync(filePath)) {
          return { success: false, error: '文件不存在' };
        }
        const stat = fs.statSync(filePath);
        return {
          success: true,
          info: {
            size: stat.size,
            isDirectory: stat.isDirectory(),
            isFile: stat.isFile(),
            createdMs: stat.birthtimeMs,
            modifiedMs: stat.mtimeMs,
            accessedMs: stat.atimeMs,
            extension: path.extname(filePath),
            name: path.basename(filePath),
            dir: path.dirname(filePath),
          },
        };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    // 选择文件夹对话框
    ipcMain.handle('fs-select-directory', async () => {
      if (!deps.mainWindow) return { success: false, error: '主窗口未就绪' };
      try {
        const result = await deps.dialog.showOpenDialog(deps.mainWindow, {
          title: '选择文件夹',
          properties: ['openDirectory'],
        });
        if (result.canceled || result.filePaths.length === 0) {
          return { success: false, error: '用户取消' };
        }
        return { success: true, filePath: result.filePaths[0] };
      } catch (err) {
        return { success: false, error: err.message };
      }
    });
  }

  return {
    setDependencies,
    getMainWindow,
    register,
  };
}

module.exports = {
  createFsHandlers,
};
