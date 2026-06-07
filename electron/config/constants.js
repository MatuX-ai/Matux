/**
 * MatuX Electron 配置常量
 * 
 * 统一管理所有魔法数字、超时、路径等配置
 * 避免在业务代码中散落难以维护的硬编码值
 */

const path = require('path');
const { app } = require('electron');

// ==================== 后端服务配置 ====================

const BACKEND_PORT = 8000;
const BACKEND_HOST = 'localhost';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

// ==================== 超时配置（毫秒）====================

// 核心启动超时 60 秒（覆盖冷启动 Phase 1 + 初始健康检查）
const BACKEND_START_TIMEOUT = 60000;

// Tier 1 预加载超时 30 秒（不阻塞 UI）
const TIER1_PRELOAD_TIMEOUT = 30000;

// 后端崩溃后重启延迟
const BACKEND_RESTART_DELAY = 3000;

// 最大重启尝试次数
const MAX_RESTART_ATTEMPTS = 3;

// 健康检查间隔
const HEALTH_CHECK_INTERVAL = 10000;

// 模块状态轮询间隔
const MODULE_STATUS_INTERVAL = 5000;

// ==================== execSync 超时配置 ====================

// execSync 标准超时 5 秒
const EXEC_SYNC_TIMEOUT = 5000;

// execSync 短超时 3 秒
const EXEC_SYNC_SHORT_TIMEOUT = 3000;

// execSync pip 命令超时 15 秒
const EXEC_SYNC_PIP_TIMEOUT = 15000;

// ==================== 文件读取配置 ====================

// .imato 文件最大读取大小（1MB）
const MAX_FILE_SIZE = 1 * 1024 * 1024;

// Splash 画面渲染等待时间
const SPLASH_RENDER_DELAY = 200;

// ==================== HTTP 请求配置 ====================

// HTTP 请求超时 5 秒
const HTTP_REQUEST_TIMEOUT = 5000;

// 健康检查详情请求超时 5 秒
const HEALTH_CHECK_DETAIL_INTERVAL = 5000;

// 端口等待间隔 500ms
const PORT_WAIT_INTERVAL = 500;

// ==================== 健康检查端点 ====================

const HEALTH_URL = `${BACKEND_URL}/health`;
const HEALTH_DETAIL_URL = `${BACKEND_URL}/api/v1/system/health-detail`;
const MODULES_URL = `${BACKEND_URL}/api/v1/system/modules`;

// ==================== 环境检测 ====================

const isDev = (process.env.NODE_ENV || '').trim() === 'development';

// ==================== 窗口配置 ====================

const WINDOW_STATE_FILE = path.join(app.getPath('userData'), 'window-state.json');

const DEFAULT_WINDOW_SIZE = {
  width: 1400,
  height: 900,
  minWidth: 1024,
  minHeight: 768,
};

const SPLASH_WINDOW_SIZE = {
  width: 480,
  height: 520,
};

// ==================== 路径配置 ====================

/**
 * 获取后端目录路径
 */
function getBackendDir() {
  return path.join(__dirname, '..', 'backend');
}

/**
 * 获取前端入口 HTML 路径
 */
function getFrontendIndex() {
  // 前端构建输出在项目根目录的 dist/imatuproject
  return path.join(__dirname, '..', '..', 'dist', 'imatuproject', 'index.html');
}

/**
 * 获取后端脚本路径
 */
function getBackendScriptPath() {
  // 生产环境使用 PyInstaller 打包的 exe
  if (!isDev && process.platform === 'win32') {
    const exePath = path.join(getBackendDir(), 'dist', 'main_ai_edu.exe');
    const fs = require('fs');
    if (fs.existsSync(exePath)) {
      return { type: 'exe', path: exePath, cwd: getBackendDir() };
    }
  }
  // 开发环境使用源码
  const scriptPath = path.join(getBackendDir(), 'main_ai_edu.py');
  return { type: 'script', path: scriptPath, cwd: getBackendDir() };
}

// ==================== 资源路径配置 ====================

const APP_PATHS = {
  backendDir: getBackendDir(),
  frontendIndex: getFrontendIndex(),
  icon: path.join(__dirname, 'build', 'icon.ico'),
  preload: path.join(__dirname, '..', 'preload.js'),
  preloadSplash: path.join(__dirname, '..', 'preload-splash.js'),
  splashHtml: path.join(__dirname, '..', 'splash.html'),
};

// ==================== Python 环境配置 ====================

// Python 最低版本要求
const PYTHON_MIN_VERSION = { major: 3, minor: 9 };

// 后端必需的核心依赖包（无此列表中的包将无法启动）
const CRITICAL_PYTHON_PACKAGES = [
  'fastapi',
  'uvicorn',
  'sqlalchemy',
  'pydantic',
  'python-jose',
  'passlib',
  'python-multipart',
];

// ==================== 安全配置 ====================

// 允许的 URL 协议白名单
const ALLOWED_URL_PROTOCOLS = ['https:', 'http:'];

// ==================== 导出 ====================

module.exports = {
  // 后端服务
  BACKEND_PORT,
  BACKEND_HOST,
  BACKEND_URL,
  BACKEND_START_TIMEOUT,
  TIER1_PRELOAD_TIMEOUT,
  BACKEND_RESTART_DELAY,
  MAX_RESTART_ATTEMPTS,
  HEALTH_CHECK_INTERVAL,
  MODULE_STATUS_INTERVAL,

  // execSync 超时
  EXEC_SYNC_TIMEOUT,
  EXEC_SYNC_SHORT_TIMEOUT,
  EXEC_SYNC_PIP_TIMEOUT,

  // 文件读取
  MAX_FILE_SIZE,
  SPLASH_RENDER_DELAY,

  // HTTP 请求
  HTTP_REQUEST_TIMEOUT,
  HEALTH_CHECK_DETAIL_INTERVAL,
  PORT_WAIT_INTERVAL,

  // 健康检查端点
  HEALTH_URL,
  HEALTH_DETAIL_URL,
  MODULES_URL,

  // 环境
  isDev,

  // 窗口
  WINDOW_STATE_FILE,
  DEFAULT_WINDOW_SIZE,
  SPLASH_WINDOW_SIZE,

  // 路径
  APP_PATHS,
  getBackendDir,
  getFrontendIndex,
  getBackendScriptPath,

  // Python
  PYTHON_MIN_VERSION,
  CRITICAL_PYTHON_PACKAGES,

  // 安全
  ALLOWED_URL_PROTOCOLS,
};
