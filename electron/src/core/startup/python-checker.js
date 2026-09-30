/**
 * Python 环境检测模块
 * @module python-checker
 *
 * 负责 Python 环境的检测、验证和用户引导
 */

const { dialog, shell } = require('electron');

const {
  detectPython,
  validatePythonAtPath,
  checkPythonDeps,
  installPythonDeps,
  clearDepsCache,
} = require('../backend');

const {
  APP_PATHS,
} = require('../../../config/constants');

const {
  isPythonSkipped,
  markPythonSkipped,
  clearPythonSkipped,
  // 【NSIS 集成】手动指定的 Python 路径优先级高于自动检测
  consumePendingPythonPath,
  getManualPythonPath,
  setManualPythonPath,
  clearManualPythonPath,
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

  // 【NSIS 集成】第1优先级：消费 NSIS pending 路径（一次性桥接）
  consumePendingPythonPath(validatePythonAtPath);

  // 【NSIS 集成】第2优先级：使用之前保存的手动路径
  const savedManualPath = getManualPythonPath();
  if (savedManualPath) {
    const validated = validatePythonAtPath(savedManualPath);
    if (validated.available) {
      console.log(`[INFO] 使用手动指定的 Python: ${validated.path} (${validated.version})`);
      // 跳过自动检测，直接进入后续依赖检查
      const manualInfo = { available: true, version: validated.version, path: validated.path };
      // 与自动检测路径相同的“清除跳过标记”逻辑
      if (isPythonSkipped()) clearPythonSkipped();
      return await _runDepsCheck(manualInfo, sendSplashStatus);
    }
    console.warn(`[WARN] 保存的手动 Python 路径已失效: ${savedManualPath} (${validated.error})`);
    clearManualPythonPath();
  }

  // 【原逻辑】第3优先级：自动检测（PATH + 常见安装路径）
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
        const validated = validatePythonAtPath(result.filePaths[0]);
        if (validated.available) {
          console.log(`[INFO] 用户手动指定 Python: ${validated.path} (${validated.version})`);
          pythonInfo = { available: true, version: validated.version, path: validated.path };
          // 成功检测到 Python 后清除跳过标记
          clearPythonSkipped();
          // 【NSIS 集成】持久化手动路径，后续启动可直接使用
          setManualPythonPath(validated.path);
          break;
        }
        await dialog.showMessageBox({
          type: 'error',
          title: validated.error && validated.error.startsWith('version') ? '版本不符' : '无效的文件',
          message: validated.error && validated.error.startsWith('version')
            ? `所选 Python 版本 ${validated.version || '未知'} 不符合要求`
            : '所选文件不是有效的 Python 可执行文件，请重新选择。',
          detail: validated.error && validated.error.startsWith('version')
            ? 'MatuX 需要 Python 3.9 或更高版本。'
            : `错误信息：${validated.error || '未知错误'}`,
        });
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
  return await _runDepsCheck(pythonInfo, sendSplashStatus);
}

/**
 * 【重构】统一处理 Python 依赖检查与安装逻辑
 * 自动检测路径和手动路径（NSIS 集成）都会调用这个函数。
 * @param {{ available: boolean, version: string, path: string }} pythonInfo - Python 信息
 * @param {Function} sendSplashStatus - Splash 状态回调
 * @returns {Promise<Object>} pythonInfo 或降级模式标记
 */
async function _runDepsCheck(pythonInfo, sendSplashStatus) {
  // 检查 Python 关键依赖包
  sendSplashStatus('checking-deps', '正在检查 Python 依赖包...', 10);
  const missingDeps = checkPythonDeps(pythonInfo);

  if (missingDeps.length > 0) {
    const msg = `缺少关键依赖: ${missingDeps.join(', ')}`;
    console.error(`[ERROR] ${msg}`);
    sendSplashStatus('pip-missing', '正在自动安装缺失依赖包...', 15, msg);

    // 【增强】弹窗询问用户是否自动安装
    const { response: depResponse } = await dialog.showMessageBox({
      type: 'warning',
      title: '缺少 Python 依赖包',
      message: '检测到以下 Python 依赖包缺失',
      detail: `缺失的依赖:\n\n${missingDeps.join('\n')}\n\nMatuX 可以自动为您安装这些依赖，是否继续？`,
      buttons: ['自动安装', '暂不处理'],
      defaultId: 0,
    });

    if (depResponse === 0) {
      // 用户选择自动安装
      sendSplashStatus('pip-installing', '正在安装依赖包，请稍候...', 20);
      const result = installPythonDeps(pythonInfo, missingDeps, (progressMsg) => {
        sendSplashStatus('pip-installing', progressMsg, 30);
      });

      if (result.success) {
        console.log('[INFO] Python 依赖自动安装成功');
        sendSplashStatus('pip-success', '依赖安装成功', 35);
        // 清除 deps 缓存，下次重新检查
        clearDepsCache();
      } else {
        console.error(`[ERROR] 依赖安装失败: ${result.error}`);
        sendSplashStatus('pip-failed', '依赖安装失败', 0, result.error);
        await dialog.showMessageBox({
          type: 'error',
          title: '依赖安装失败',
          message: '无法自动安装 Python 依赖包',
          detail: `错误信息: ${result.error}\n\n请尝试手动安装:\ncd backend\npip install -r requirements.txt`,
        });
        return { ...DEGRADED_MODE_RESULT, reason: 'install-failed' };
      }
    } else {
      // 用户选择暂不处理
      return { ...DEGRADED_MODE_RESULT, reason: 'missing-deps' };
    }
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
    // 【修复 P0】之前弹原生模态对话框，强制独占输入焦点，挡住 splash
    // 用户无法点击"跳过"。改为仅在 splash 显示错误状态，让用户继续操作。
    sendSplashStatus('backend-error', `端口 ${BACKEND_PORT} 无法连接后端服务`, 0,
      `健康检查失败，请检查后端服务是否正常运行在端口 ${BACKEND_PORT}（点击跳过按钮进入降级模式）`);
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
