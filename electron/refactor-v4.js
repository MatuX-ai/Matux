/**
 * 重构 main.js - 集成 IPC Handlers 模块
 */

const fs = require('fs');
const path = require('path');

const inputFile = path.join(__dirname, 'main.js');
const outputFile = path.join(__dirname, 'main-refactored-v4.js');

let content = fs.readFileSync(inputFile, 'utf-8');
console.log('文件读取完成，长度:', content.length);

// 1. 添加 IPC handlers 模块导入
const importSection = `// 导入后端管理模块（由 main.js 拆分出的独立模块）
const backendManager = require('./src/core/backend');

// 导入模块状态管理器
const moduleStatusManager = require('./src/core/module-status-manager');

// 导入 IPC Handlers 模块
const { windowHandlers, fsHandlers } = require('./src/core/ipc/handlers');
`;

const importIdx = content.indexOf("// 导入后端管理模块（由 main.js 拆分出的独立模块）");
if (importIdx !== -1) {
  const endIdx = content.indexOf('\n', importIdx);
  content = content.substring(0, importIdx) + importSection + content.substring(endIdx + 1);
  console.log('[OK] 添加 IPC handlers 模块导入');
}

// 2. 删除窗口控制 IPC handlers 代码
const windowHandlersStart = '  // ===== 窗口控制 IPC（支持 frame:false 自定义标题栏）=====\n';
const windowHandlersEnd = '\n  // 检查更新\n';

const wStartIdx = content.indexOf(windowHandlersStart);
const wEndIdx = content.indexOf(windowHandlersEnd, wStartIdx);

if (wStartIdx !== -1 && wEndIdx !== -1) {
  const deleted = content.substring(wStartIdx, wEndIdx);
  const handlerCount = (deleted.match(/ipcMain\.handle\(/g) || []).length;
  content = content.substring(0, wStartIdx) + content.substring(wEndIdx);
  console.log(`[OK] 删除窗口控制 IPC handlers (${handlerCount}个)`);
}

// 3. 删除文件系统 IPC handlers 代码
const fsHandlersToDelete = [
  'fs-read-file',
  'fs-write-file',
  'fs-save-dialog',
  'get-window-size',
  'fs-open-dialog',
  'fs-list-dir',
  'fs-make-dir',
  'fs-delete-file',
  'fs-file-exists',
  'fs-get-file-info',
  'fs-select-directory',
];

for (const handler of fsHandlersToDelete) {
  const regex = new RegExp(`\\n  ipcMain\\.handle\\('${handler}',[\\s\\S]*?\\}\\);`, 'g');
  const before = content.length;
  content = content.replace(regex, '');
  if (content.length !== before) {
    console.log(`[OK] 删除 fs handler: ${handler}`);
  }
}

// 4. 删除 app-event 中的窗口控制部分
const appEventWindowCode = `
    switch (data.type) {
      case 'minimize':
        mainWindow?.minimize();
        break;
      case 'maximize':
        if (mainWindow?.isMaximized()) {
          mainWindow.unmaximize();
        } else {
          mainWindow?.maximize();
        }
        break;
      case 'close':
        mainWindow?.close();
        break;
      case 'toggle-fullscreen':
        mainWindow?.setFullScreen(!mainWindow?.isFullScreen());
        break;
      case 'open-new-window':
        // 多窗口弹出（数字孪生实验室等）
        createChildWindow(data);
        break;
      default:
        break;
    }
`;
content = content.replace(appEventWindowCode, `
    // 窗口控制已移至 windowHandlers
    createChildWindow(data);
`);
console.log('[OK] 简化 app-event 处理');

// 5. 在 registerIpcHandlers 中添加调用
const registerCallSection = `
  // 注册窗口控制 handlers
  windowHandlers.setDependencies({ mainWindow });
  windowHandlers.registerWindowHandlers(ipcMain);

  // 注册文件系统 handlers
  fsHandlers.setDependencies({ mainWindow, validateFilePath, dialog });
  fsHandlers.registerFsHandlers(ipcMain);
`;

const backendHandlersIdx = content.indexOf("ipcMain.handle('backend:url'");
if (backendHandlersIdx !== -1) {
  content = content.substring(0, backendHandlersIdx) + registerCallSection + content.substring(backendHandlersIdx);
  console.log('[OK] 添加 IPC handlers 注册调用');
}

// 6. 更新头部注释
const newHeader = `/**
 * MatuX Electron 主进程
 * 
 * 【架构说明】
 * - 后端管理功能已抽取至 ./src/core/backend/ 模块
 * - 模块状态管理已抽取至 ./src/core/module-status-manager.js
 * - IPC Handlers 已抽取至 ./src/core/ipc/handlers/ 模块
 *
 * 负责：
 * 1. Splash Screen 启动画面
 * 2. Python 环境检测与引导安装
 * 3. 后端服务生命周期管理（启动/重启/关闭）
 * 4. 浏览器窗口创建与管理
 * 5. IPC 安全通信桥接
 * 6. 崩溃恢复与健康检查
 */`;

content = content.replace(/\/\*\*[\s\S]*?^\s*\*\/\s*\n/, newHeader + '\n\n');
console.log('[OK] 更新头部注释');

// 写入输出文件
fs.writeFileSync(outputFile, content, 'utf-8');
console.log('\n========================================');
console.log('[完成] 重构完成！');
console.log('========================================');
console.log('输出文件:', outputFile);
console.log('\n下一步: 运行 node --check 验证语法');
