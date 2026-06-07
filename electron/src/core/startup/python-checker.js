/**
 * Python 环境检测模块
 * @module python-checker
 *
 * 负责 Python 环境的检测、验证和用户引导
 */

const { dialog, shell } = require('electron');
const { execSync } = require('child_process');
const path = require('path');

const {
  detectPython,
  checkPythonDeps,
  isPythonVersionGte39,
} = require('../backend');

const {
  EXEC_SYNC_TIMEOUT,
  APP_PATHS,
} = require('../../../config/constants');

// 【重构】安全验证
const { validateExternalUrl, validateFilePath } = require('../security');

/**
 * 向 Splash 窗口发送状态更新
 * @callback SplashStatusCallback
 * @param {string} phase - 当前阶段
 * @param {string} text - 状态文本
 * @param {number} progress - 进度百分比
 * @param {string} [detail] - 详细信息
 * @param {Object} [modules] - 模块信息
 */

/**
 * 检测并验证 Python 环境
 * @param {Object} options - 配置选项
 * @param {Function} options.sendSplashStatus - 发送状态回调
 * @returns {Promise<Object>} Python 信息对象
 */
async function checkPythonEnvironment({ sendSplashStatus }) {
  sendSplashStatus('checking-python', '正在检测 Python 环境...', 5);
  let pythonInfo = detectPython();

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
      // 打开 Python 下载页面
      const pythonDownloadUrl = 'https://www.python.org/downloads/';
      const validation = validateExternalUrl(pythonDownloadUrl);
      if (validation.valid) {
        shell.openExternal(pythonDownloadUrl);
      } else {
        console.error('[ERROR] URL验证失败:', validation.error);
      }
      return null;
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
      return null;
    }
  }

  console.log(`[INFO] 检测到 Python ${pythonInfo.version} (${pythonInfo.path})`);

  // 检查 Python 关键依赖包
  sendSplashStatus('checking-deps', '正在检查 Python 依赖包...', 10);
  const missingDeps = checkPythonDeps(pythonInfo);
  
  if (missingDeps.length > 0) {
    const msg = `缺少关键依赖: ${missingDeps.join(', ')}`;
    console.error(`[ERROR] ${msg}`);
    sendSplashStatus('pip-missing', '缺少 Python 依赖包', 0, msg);

    const { response: depResponse } = await dialog.showMessageBox({
      type: 'warning',
      title: '缺少 Python 依赖包',
      message: '请先安装 Python 依赖包再启动',
      detail: `检测到以下 Python 依赖包缺失:\n\n${missingDeps.join('\n')}\n\n请在终端中执行:\ncd backend\npip install -r requirements.txt`,
      buttons: ['查看依赖文件', '暂不处理'],
      defaultId: 0,
    });

    if (depResponse === 0) {
      // 打开 requirements.txt
      const reqPath = path.join(APP_PATHS.backendDir, 'requirements.txt');
      const validation = validateFilePath(reqPath);
      if (validation.valid) {
        shell.openPath(reqPath);
      } else {
        console.error('[ERROR] 路径验证失败:', validation.error);
      }
    }
    return null;
  }

  return pythonInfo;
}

/**
 * 验证后端健康状态
 * @param {Object} options - 配置选项
 * @param {Function} options.sendSplashStatus - 发送状态回调
 * @param {Function} options.healthCheck - 健康检查函数
 * @param {Function} options.backendManager - 后端管理器实例
 * @returns {Promise<boolean>} 是否健康
 */
async function verifyBackendHealth({ sendSplashStatus, healthCheck, backendManager }) {
  sendSplashStatus('verifying-health', '正在验证后端服务...', 90);
  
  const { PORT_WAIT_INTERVAL } = require('../../../config/constants');
  let healthResult = await healthCheck();
  
  // 首次失败后短等待重试
  if (!healthResult.success) {
    console.log(`[INFO] 首次健康检查未通过，${PORT_WAIT_INTERVAL / 1000} 秒后重试...`);
    await new Promise((r) => setTimeout(r, PORT_WAIT_INTERVAL));
    healthResult = await healthCheck();
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

module.exports = {
  checkPythonEnvironment,
  verifyBackendHealth,
};
