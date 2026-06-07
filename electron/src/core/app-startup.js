/**
 * MatuX Electron 应用启动管理器
 *
 * 负责应用启动流程的编排和管理
 *
 * @module core/app-startup
 */

const { dialog, shell, app } = require('electron');
const { execSync } = require('child_process');
const path = require('path');

/**
 * 创建应用启动管理器
 * @param {object} options 配置选项
 * @returns {object} AppStartup 实例
 */
function createAppStartup(options = {}) {
  const {
    // 依赖注入
    appState = null,
    backendManager = null,
    healthMonitor = null,
    shortcutManager = null,
    trayManager = null,
    mainWindow = null,

    // 配置
    config = {},
    validateExternalUrl = () => ({ valid: true }),
    validateFilePath = () => ({ valid: true }),
    sendSplashStatus = () => {},

    // Python 环境检测
    detectPython = () => ({ available: false }),
    checkPythonDeps = () => [],

    // 后端 URL
    getBackendUrl = () => 'http://localhost:8000',
    getHealthCheck = () => async () => ({ success: false }),

    // 常量
    EXEC_SYNC_TIMEOUT = 10000,
    BACKEND_RESTART_DELAY = 3000,
    MAX_RESTART_ATTEMPTS = 3,
  } = options;

  // 状态
  let isStarting = false;
  let pythonInfo = null;

  /**
   * 检查 Python 版本是否满足要求
   */
  function isPythonVersionGte39(version) {
    const parts = version.split('.');
    const major = parseInt(parts[0], 10);
    const minor = parseInt(parts[1], 10);
    return major > 3 || (major === 3 && minor >= 9);
  }

  /**
   * 检测 Python 环境
   * @returns {Promise<boolean>} 是否成功检测到 Python
   */
  async function detectPythonEnvironment() {
    sendSplashStatus('checking-python', '正在检测 Python 环境...', 5);
    pythonInfo = detectPython();

    // 如果自动检测未找到，循环弹窗让用户选择
    while (!pythonInfo.available) {
      sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);

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
        // 下载 Python
        const pythonDownloadUrl = 'https://www.python.org/downloads/';
        const validation = validateExternalUrl(pythonDownloadUrl);
        if (validation.valid) {
          shell.openExternal(pythonDownloadUrl);
        } else {
          console.error('[ERROR] URL验证失败:', validation.error);
        }
        return false;
      }

      if (response === 1) {
        // 用户手动指定 Python 位置
        const result = await dialog.showOpenDialog({
          title: '请选择 python.exe',
          defaultPath: process.env.ProgramFiles || 'C:\\',
          filters: [{ name: 'Python 可执行文件', extensions: ['exe'] }],
          properties: ['openFile'],
        });

        if (!result.canceled && result.filePaths.length > 0) {
          const manualPath = result.filePaths[0];
          try {
            const versionOutput = execSync(`"${manualPath}" --version 2>&1`, {
              encoding: 'utf-8',
              timeout: EXEC_SYNC_TIMEOUT,
            }).trim();
            const versionMatch = versionOutput.match(/Python\s+(\d+\.\d+)/);
            if (versionMatch && isPythonVersionGte39(versionMatch[1])) {
              console.log(`[INFO] 用户手动指定 Python: ${manualPath} (${versionMatch[1]})`);
              pythonInfo = { available: true, version: versionMatch[1], path: manualPath };
              break;
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
        }
        // 用户取消文件选择，继续循环重新弹窗
      } else {
        // 暂不处理
        return false;
      }
    }

    console.log(`[INFO] 检测到 Python ${pythonInfo.version} (${pythonInfo.path})`);
    return true;
  }

  /**
   * 检查 Python 依赖包
   * @returns {Promise<boolean>} 是否所有依赖都满足
   */
  async function checkDependencies() {
    sendSplashStatus('checking-deps', '正在检查 Python 依赖包...', 10);
    const missingDeps = checkPythonDeps(pythonInfo);

    if (missingDeps.length > 0) {
      const msg = `缺少关键依赖: ${missingDeps.join(', ')}`;
      console.error(`[ERROR] ${msg}`);
      sendSplashStatus('pip-missing', '缺少 Python 依赖包', 0, msg);

      const { response } = await dialog.showMessageBox({
        type: 'warning',
        title: '缺少 Python 依赖包',
        message: '请先安装 Python 依赖包再启动',
        detail: `检测到以下 Python 依赖包缺失:\n\n${missingDeps.join('\n')}\n\n请在终端中执行:\ncd backend\npip install -r requirements.txt`,
        buttons: ['查看依赖文件', '暂不处理'],
        defaultId: 0,
      });

      if (response === 0) {
        const reqPath = path.join(config.backendDir || '', 'requirements.txt');
        const validation = validateFilePath(reqPath);
        if (validation.valid) {
          shell.openPath(reqPath);
        } else {
          console.error('[ERROR] 路径验证失败:', validation.error);
        }
      }
      return false;
    }

    return true;
  }

  /**
   * 启动后端服务
   * @returns {Promise<boolean>} 是否成功启动
   */
  async function startBackendService() {
    if (!backendManager) {
      console.error('[ERROR] 后端管理器未初始化');
      return false;
    }

    const started = await backendManager.start(sendSplashStatus);
    if (!started) {
      sendSplashStatus('backend-error', '后端启动失败，请检查安装', 0);
      return false;
    }

    // 等待后端就绪
    const ready = await backendManager.waitForReady({
      backendHost: config.BACKEND_HOST || 'localhost',
      backendPort: config.BACKEND_PORT || 8000,
      onProgress: sendSplashStatus,
    });

    if (!ready) {
      console.error('[ERROR] 后端服务启动失败');
      return false;
    }

    // 确认后端健康
    sendSplashStatus('verifying-health', '正在验证后端服务...', 90);
    let healthResult = await getHealthCheck()();

    // 首次失败后短等待重试
    if (!healthResult.success) {
      console.log(`[INFO] 首次健康检查未通过，${config.PORT_WAIT_INTERVAL / 1000 || 2} 秒后重试...`);
      await new Promise((r) => setTimeout(r, (config.PORT_WAIT_INTERVAL || 2000)));
      healthResult = await getHealthCheck()();
    }

    if (!healthResult.success) {
      console.error('[ERROR] 端口已开放但健康检查未通过，端口可能被其他程序占用');
      sendSplashStatus('backend-error', '端口 8000 被占用，无法连接后端服务', 0,
        '健康检查失败，请检查是否有其他程序占用了 8000 端口');

      await dialog.showMessageBox({
        type: 'error',
        title: '端口冲突',
        message: '端口 8000 已被其他程序占用',
        detail: '检测到端口 8000 已开放，但无法识别为 MatuX 后端服务。\n\n请检查是否有其他程序（如 nginx、其他 MatuX 实例）占用了该端口。',
      });

      backendManager?.stop();
      return false;
    }

    return true;
  }

  /**
   * 执行完整的启动流程
   * @returns {Promise<object>} 启动结果
   */
  async function startup() {
    if (isStarting) {
      console.log('[INFO] 应用正在启动中，跳过重复请求');
      return { success: false, reason: 'already_starting' };
    }

    isStarting = true;
    const result = {
      success: false,
      pythonAvailable: false,
      depsSatisfied: false,
      backendReady: false,
    };

    try {
      // 1. 检测 Python 环境
      result.pythonAvailable = await detectPythonEnvironment();
      if (!result.pythonAvailable) {
        isStarting = false;
        return result;
      }

      // 2. 检查依赖
      result.depsSatisfied = await checkDependencies();
      if (!result.depsSatisfied) {
        isStarting = false;
        return result;
      }

      // 3. 启动后端服务
      result.backendReady = await startBackendService();
      if (!result.backendReady) {
        isStarting = false;
        return result;
      }

      // 4. 启动健康检查
      if (healthMonitor) {
        healthMonitor.startHealthCheck();
        healthMonitor.startModuleStatusPolling();
      }

      // 5. 初始化 UI
      if (trayManager) {
        trayManager.create();
      }

      // 6. 注册快捷键
      if (shortcutManager) {
        shortcutManager.registerAll();
      }

      result.success = true;
    } catch (err) {
      console.error('[ERROR] 启动过程出错:', err.message);
      sendSplashStatus('error', `启动失败: ${err.message}`, 0);
    }

    isStarting = false;
    return result;
  }

  /**
   * 获取 Python 信息
   */
  function getPythonInfo() {
    return pythonInfo;
  }

  /**
   * 检查是否正在启动
   */
  function isAppStarting() {
    return isStarting;
  }

  return {
    startup,
    detectPythonEnvironment,
    checkDependencies,
    startBackendService,
    getPythonInfo,
    isAppStarting,
  };
}

module.exports = { createAppStartup };
