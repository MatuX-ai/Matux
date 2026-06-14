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

const {
  isPythonSkipped,
  markPythonSkipped,
  clearPythonSkipped,
} = require('../../../utils/install-state');

// 【重构】安全验证
const { validateExternalUrl, validateFilePath } = require('../security');

// ==================== 降级模式 Sentinel ====================

/**
 * 降级模式标记：当 Python 不可用时，checkPythonEnvironment 返回此对象
 * 而非 null，使调用方能区分"用户跳过 → 降级运行"和"真正的启动失败"
 */
const DEGRADED_MODE_RESULT = { available: false, degraded: true };

/**
 * 判断返回值是否为降级模式标记
 * @param {*} info - checkPythonEnvironment 的返回值
 * @returns {boolean}
 */
function isDegradedMode(info) {
  return info !== null && typeof info === 'object' && info.degraded === true;
}

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

  // 【P1 修复】如检测成功，主动清除可能存在的“跳过”标记（重置状态）
  if (pythonInfo.available && isPythonSkipped()) {
    clearPythonSkipped();
    console.log('[INFO] Python 环境已可用，清除之前的跳过标记');
  }

  // 如果自动检测未找到，循环弹窗让用户选择
  while (!pythonInfo.available) {
    sendSplashStatus('python-missing', '未检测到 Python 3.9+ 环境', 0);

    // 【需求】如果用户在之前的会话中已选择跳过，启动时弹窗提醒“功能受限”
    const previouslySkipped = isPythonSkipped();

    const { response } = await dialog.showMessageBox({
      type: 'warning',
      title: previouslySkipped ? 'Python 环境仍未安装' : '缺少 Python 环境',
      message: previouslySkipped
        ? '检测到您上次选择了跳过 Python 安装'
        : 'MatuX 需要 Python 3.9 或更高版本',
      detail: previouslySkipped
        ? '由于未安装 Python 环境，以下后端功能当前不可用：\n\n  · 课程内容同步与下载\n  · AI 教师寄语与学习进度保存\n  · 错题本与学习报告生成\n  · 插件商店与在线服务\n\n您可以选择现在安装、下载 Python，或继续跳过。'
        : '检测到您的系统未安装 Python 或版本过低。\n\n您可以选择手动指定 Python 位置，或下载安装。',
      buttons: ['下载 Python', '手动选择 Python 位置', '跳过'],
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
      // 【需求】下载 Python 也视为"跳过"（下次启动仍会提示），需持久化
      markPythonSkipped();
      return { ...DEGRADED_MODE_RESULT, reason: 'downloaded' };
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
            // 成功检测到 Python 后清除跳过标记
            clearPythonSkipped();
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
      // 用户选择"跳过"——持久化标记并返回降级模式标记
      const saved = markPythonSkipped();
      console.log(`[INFO] 用户选择跳过 Python 环境检测，状态已${saved ? '保存' : '保存失败'}`);
      return { ...DEGRADED_MODE_RESULT, reason: 'skipped' };
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
    return { ...DEGRADED_MODE_RESULT, reason: 'missing-deps' };
  }

  return pythonInfo;
}

/**
 * 验证后端健康状态
 * 【启动优化 P0-1】去除双重健康检查
 * - waitForReady() 内部已完成 waitPort + HealthChecker 探测，不需要重复调用 healthCheck
 * - 本函数仅负责错误处理（弹窗 + 停止后端），不再重复探测
 * @param {Object} options - 配置选项
 * @param {Function} options.sendSplashStatus - 发送状态回调
 * @param {Function} options.healthCheck - 健康检查函数（保留向后兼容，实际不再调用）
 * @param {Function} options.backendManager - 后端管理器实例
 * @param {boolean} options.alreadyVerified - waitForReady 是否已验证通过
 * @returns {Promise<boolean>} 是否健康
 */
async function verifyBackendHealth({ sendSplashStatus, healthCheck, backendManager, alreadyVerified = true }) {
  // 【启动优化 P0-1】waitForReady 已验证通过，直接返回 true，避免重复探测（节省 50-1000ms）
  if (alreadyVerified) {
    console.log('[INFO] 后端健康已由 waitForReady 验证，跳过重复检查');
    return true;
  }

  sendSplashStatus('verifying-health', '正在验证后端服务...', 90);

  // 兑底路径：仅在 waitForReady 未验证时执行（理论上不会走到这里）
  let healthResult = await healthCheck();

  // 首次失败后短等待重试
  if (!healthResult.success) {
    const { PORT_WAIT_INTERVAL } = require('../../../config/constants');
    console.log(`[INFO] 首次健康检查未通过，${PORT_WAIT_INTERVAL / 1000} 秒后重试...`);
    await new Promise((r) => setTimeout(r, PORT_WAIT_INTERVAL));
    healthResult = await healthCheck();
  }

  if (!healthResult.success) {
    const { BACKEND_PORT } = require('../../../config/constants');
    console.error(`[ERROR] 端口 ${BACKEND_PORT} 已开放但健康检查未通过`);
    sendSplashStatus('backend-error', `端口 ${BACKEND_PORT} 无法连接后端服务`, 0,
      `健康检查失败，请检查后端服务是否正常运行在端口 ${BACKEND_PORT}`);
    const { dialog } = require('electron');
    await dialog.showMessageBox({
      type: 'error',
      title: '后端连接失败',
      message: `无法连接到后端服务 (端口 ${BACKEND_PORT})`,
      detail: `检测到端口 ${BACKEND_PORT} 已开放，但无法识别为 MatuX 后端服务。\n\n请检查后端服务是否正常运行，或是否有其他程序占用了该端口。`,
    });
    backendManager?.stop();
    return false;
  }

  return true;
}

module.exports = {
  checkPythonEnvironment,
  verifyBackendHealth,
  isDegradedMode,
  DEGRADED_MODE_RESULT,
};
