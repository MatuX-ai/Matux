/**
 * MatuX Electron 应用启动引导器
 * 
 * 封装应用启动流程，包括 Python 环境检测、后端启动、窗口创建等
 */

const { app, dialog, shell } = require('electron');
const path = require('path');
const {
  EXEC_SYNC_TIMEOUT,
  APP_PATHS,
  getBackendScriptPath,
} = require('../config/constants');

class AppBootstrap {
  /**
   * @param {object} options 启动选项
   * @param {object} options.splashManager 启动画面管理器
   * @param {object} options.backendManager 后端管理器
   * @param {object} options.windowManager 窗口管理器
   * @param {object} options.healthService 健康检查服务
   */
  constructor(options) {
    this.splash = options.splashManager;
    this.backend = options.backendManager;
    this.windows = options.windowManager;
    this.health = options.healthService;
    
    this.pythonInfo = null;
    this.mainWindow = null;
  }

  /**
   * 执行完整的启动流程
   */
  async boot() {
    // 1. 检测 Python 环境
    const pythonReady = await this.ensurePythonEnvironment();
    if (!pythonReady) return false;

    // 2. 检查 Python 依赖
    const depsReady = await this.ensurePythonDependencies();
    if (!depsReady) return false;

    // 3. 启动后端
    const backendStarted = await this.startBackend();
    if (!backendStarted) return false;

    // 4. 等待后端就绪
    const ready = await this.waitBackendReady();
    if (!ready) return false;

    // 5. 验证后端健康
    const healthy = await this.verifyBackendHealth();
    if (!healthy) return false;

    // 6. 创建主窗口
    await this.createMainWindow();

    // 7. 创建托盘
    this.createTray();

    // 8. 注册快捷键
    this.registerShortcuts();

    return true;
  }

  /**
   * 确保 Python 环境可用
   */
  async ensurePythonEnvironment() {
    const { detectPython, isPythonVersionGteMin } = require('../utils/python-detector');
    
    this.splash.report('checking-python', '正在检测 Python 环境...', 5);
    this.pythonInfo = detectPython();

    while (!this.pythonInfo.available) {
      this.splash.report('python-missing', '未检测到 Python 3.9+ 环境', 0);

      const { response } = await dialog.showMessageBox({
        type: 'warning',
        title: '缺少 Python 环境',
        message: 'MatuX 需要 Python 3.9 或更高版本',
        detail: '检测到您的系统未安装 Python 或版本过低。\n\n您可以选择手动指定 Python 位置，或下载安装。',
        buttons: ['下载 Python', '手动选择 Python 位置', '暂不处理'],
        defaultId: 0,
        cancelId: 2,
      });

      if (response === 0) {
        shell.openExternal('https://www.python.org/downloads/');
        return false;
      }

      if (response === 1) {
        const result = await this.selectPythonManually();
        if (result) {
          this.pythonInfo = result;
          break;
        }
      } else {
        return false;
      }
    }

    console.log(`[INFO] 检测到 Python ${this.pythonInfo.version} (${this.pythonInfo.path})`);
    return true;
  }

  /**
   * 让用户手动选择 Python
   */
  async selectPythonManually() {
    const { execSync } = require('child_process');
    const { isPythonVersionGteMin } = require('../utils/python-detector');

    const result = await dialog.showOpenDialog({
      title: '请选择 python.exe',
      defaultPath: process.env.ProgramFiles || 'C:\\',
      filters: [{ name: 'Python 可执行文件', extensions: ['exe'] }],
      properties: ['openFile'],
    });

    if (result.canceled || result.filePaths.length === 0) {
      return null;
    }

    const manualPath = result.filePaths[0];
    try {
      const versionOutput = execSync(`"${manualPath}" --version 2>&1`, {
        encoding: 'utf-8',
        timeout: EXEC_SYNC_TIMEOUT,
      }).trim();
      
      const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
      if (versionMatch && isPythonVersionGteMin(versionMatch[1])) {
        console.log(`[INFO] 用户手动指定 Python: ${manualPath} (${versionMatch[1]})`);
        return { available: true, version: versionMatch[1], path: manualPath };
      }
      
      await dialog.showMessageBox({
        type: 'error',
        title: '版本不符',
        message: `所选 Python 版本 ${versionMatch ? versionMatch[1] : '未知'} 不符合要求`,
        detail: 'MatuX 需要 Python 3.9 或更高版本。',
      });
    } catch {
      await dialog.showMessageBox({
        type: 'error',
        title: '无效的文件',
        message: '所选文件不是有效的 Python 可执行文件，请重新选择。',
      });
    }

    return null;
  }

  /**
   * 确保 Python 依赖已安装
   */
  async ensurePythonDependencies() {
    const { checkPythonDeps } = require('../utils/python-detector');
    
    this.splash.report('checking-deps', '正在检查 Python 依赖包...', 10);
    const missingDeps = checkPythonDeps(this.pythonInfo);

    if (missingDeps.length > 0) {
      const msg = `缺少关键依赖: ${missingDeps.join(', ')}`;
      console.error(`[ERROR] ${msg}`);
      this.splash.report('pip-missing', '缺少 Python 依赖包', 0, msg);

      const { response } = await dialog.showMessageBox({
        type: 'warning',
        title: '缺少 Python 依赖包',
        message: '请先安装 Python 依赖包再启动',
        detail: `检测到以下 Python 依赖包缺失:\n\n${missingDeps.join('\n')}\n\n请在终端中执行:\ncd backend\npip install -r requirements.txt`,
        buttons: ['查看依赖文件', '暂不处理'],
        defaultId: 0,
      });

      if (response === 0) {
        shell.openPath(path.join(APP_PATHS.backendDir, 'requirements.txt'));
      }
      return false;
    }

    return true;
  }

  /**
   * 启动后端
   */
  async startBackend() {
    const started = await this.backend.start((phase, text, progress, detail) => {
      this.splash.report(phase, text, progress, detail);
    });

    if (!started) {
      this.splash.report('backend-error', '后端启动失败，请检查安装', 0);
      return false;
    }

    return true;
  }

  /**
   * 等待后端就绪
   */
  async waitBackendReady() {
    this.splash.report('waiting-backend', '等待后端服务就绪...', 50);
    
    const ready = await this.backend.waitForReady();
    
    if (!ready) {
      console.error('[ERROR] 后端服务启动失败');
      return false;
    }

    this.splash.report('backend-ready', '后端服务就绪 ✓', 90);
    return true;
  }

  /**
   * 验证后端健康
   */
  async verifyBackendHealth() {
    this.splash.report('verifying-health', '正在验证后端服务...', 90);
    
    const { HealthChecker } = require('./backend-manager');
    const { BACKEND_HOST, BACKEND_PORT } = require('../config/constants');
    const healthChecker = new HealthChecker(BACKEND_HOST, BACKEND_PORT);
    
    let result = await healthChecker.check();
    
    // 首次失败后短等待重试
    if (!result.success) {
      console.log('[INFO] 首次健康检查未通过，1 秒后重试...');
      await new Promise((r) => setTimeout(r, 1000));
      result = await healthChecker.check();
    }

    if (!result.success) {
      console.error('[ERROR] 端口已开放但健康检查未通过');
      this.splash.report('backend-error', '端口 8000 被占用，无法连接后端服务', 0,
        '健康检查失败，请检查是否有其他程序占用了 8000 端口');
      
      await dialog.showMessageBox({
        type: 'error',
        title: '端口冲突',
        message: '端口 8000 已被其他程序占用',
        detail: '检测到端口 8000 已开放，但无法识别为 MatuX 后端服务。',
      });
      
      this.backend.stop();
      return false;
    }

    return true;
  }

  /**
   * 创建主窗口
   */
  async createMainWindow() {
    this.splash.report('loading-app', '正在加载应用...', 95);
    
    const splashWindow = this.splash.getWindow();
    this.mainWindow = this.windows.createMain(splashWindow);
    
    // 关闭启动画面
    this.splash.close();
    
    return this.mainWindow;
  }

  /**
   * 创建托盘
   */
  createTray() {
    // 托盘创建逻辑需要后端状态回调
    // 暂时返回 null，由外部调用者创建
    return null;
  }

  /**
   * 注册快捷键
   */
  registerShortcuts() {
    // 快捷键注册由 global-shortcuts 模块处理
  }

  /**
   * 获取主窗口
   */
  getMainWindow() {
    return this.mainWindow;
  }

  /**
   * 获取 Python 信息
   */
  getPythonInfo() {
    return this.pythonInfo;
  }
}

module.exports = { AppBootstrap };
