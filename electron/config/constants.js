/**
 * MatuX Electron 配置常量
 * 
 * 统一管理所有魔法数字、超时、路径等配置
 * 避免在业务代码中散落难以维护的硬编码值
 */

const path = require('path');
const { app } = require('electron');

// ==================== 后端服务配置 ====================

// 从环境变量读取，默认为 8000
const BACKEND_PORT = parseInt(process.env.BACKEND_PORT, 10) || 8000;
const BACKEND_HOST = process.env.BACKEND_HOST || 'localhost';
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

// 备用端口列表（当默认端口被占用时尝试）
const BACKUP_PORTS = [8001, 8002, 8003, 8080, 3001];

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
// 【启动优化 P3-8】从 200ms 改为 0ms
// - Splash 窗口内部的 ready-to-show 事件会负责 show()
// - 与主窗口创建/后端启动完全独立，可并行进行
// - 设置为 0 节省 200ms
const SPLASH_RENDER_DELAY = 0;

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

const isDev = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

// 是否为生产或类生产环境（非 development 即可认为是生产级）
const isProductionLike = !isDev;

// ==================== 窗口配置 ====================

const WINDOW_STATE_FILE = path.join(app.getPath('userData'), 'window-state.json');

const DEFAULT_WINDOW_SIZE = {
  width: 1400,
  height: 900,
  minWidth: 1024,
  minHeight: 768,
};

const SPLASH_WINDOW_SIZE = {
  width: 620,
  height: 680,
};

// ==================== 路径配置 ====================

/**
 * 获取后端目录路径
 * 开发环境: __dirname = electron/config/，向上两级到项目根，再进入 backend/
 * 生产环境: backend 作为 extraResources 打包在 resources/backend/
 */
function getBackendDir() {
  if (!isDev && process.resourcesPath) {
    // 生产环境: backend 在 resources/backend/ 目录（extraResources 配置）
    return path.join(process.resourcesPath, 'backend');
  }
  // 开发环境: 从 electron/config/ 向上两级到项目根
  return path.join(__dirname, '..', '..', 'backend');
}

/**
 * 获取前端入口 HTML 路径
 * 开发环境: electron/config/  →  项目根/dist/imatuproject/index.html
 * 生产环境: 打包在 resources/dist/imatuproject/index.html （electron-builder.yml extraResources）
 *
 * 【修复 1.0.2 蓝屏】之前 __dirname 在 asar 中指向 app.asar/config/，
 *   path.join(__dirname, '..', '..', 'dist', 'imatuproject') 解析为 app.asar/dist/imatuproject，
 *   但 asar 里压根没有 dist（asar files 不支持 ../dist/xxx 这种跳出 app 根的相对路径），
 *   导致 fs.existsSync(index.html) 始终 false → 主窗口 ready-to-show 永远不触发 → 蓝屏无显示。
 */
function getFrontendIndex() {
  if (!isDev && process.resourcesPath) {
    return path.join(process.resourcesPath, 'dist', 'imatuproject', 'index.html');
  }
  // 开发环境：从 electron/config/ 向上两级到项目根
  return path.join(__dirname, '..', '..', 'dist', 'imatuproject', 'index.html');
}

/**
 * 获取前端目录路径（用于自定义协议 handler）
 */
function getFrontendDir() {
  if (!isDev && process.resourcesPath) {
    return path.join(process.resourcesPath, 'dist', 'imatuproject');
  }
  return path.join(__dirname, '..', '..', 'dist', 'imatuproject');
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
  frontendDir: getFrontendDir(),
  frontendIndex: getFrontendIndex(),
  // 【修复 #4】icon.ico 位于 electron/build/ 下，__dirname 是 electron/config/
  //   需向上跳一级才能访问 electron/build/icon.ico
  icon: path.join(__dirname, '..', 'build', 'icon.ico'),
  preload: path.join(__dirname, '..', 'preload.js'),
  preloadSplash: path.join(__dirname, '..', 'preload-splash.js'),
  splashHtml: path.join(__dirname, '..', 'splash.html'),
};

// ==================== 自定义协议配置 ====================

// 自定义协议名称（避免 file:// 协议下 ES module 加载限制）
const APP_PROTOCOL = 'app';

// 前端加载超时时间（30秒，超时后显示错误页）
const FRONTEND_LOAD_TIMEOUT = 30000;

// 注册自定义协议为 privileged（支持 fetch / CORS / ES module）
const APP_PROTOCOL_PRIVILEGES = {
  standard: true,
  secure: true,
  supportFetchAPI: true,
  corsEnabled: true,
  stream: true,
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

// 允许的 URL 协议白名单（生产环境仅允许 https）
const ALLOWED_URL_PROTOCOLS = isProductionLike
  ? ['https:']
  : ['https:', 'http:'];

// ==================== 导出 ====================

module.exports = {
  // 后端服务
  BACKEND_PORT,
  BACKEND_HOST,
  BACKEND_URL,
  BACKUP_PORTS,
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
  isProduction,
  isProductionLike,

  // 窗口
  WINDOW_STATE_FILE,
  DEFAULT_WINDOW_SIZE,
  SPLASH_WINDOW_SIZE,

  // 路径
  APP_PATHS,
  APP_PROTOCOL,
  APP_PROTOCOL_PRIVILEGES,
  FRONTEND_LOAD_TIMEOUT,
  getBackendDir,
  getFrontendIndex,
  getFrontendDir,
  getBackendScriptPath,

  // Python
  PYTHON_MIN_VERSION,
  CRITICAL_PYTHON_PACKAGES,

  // 安全
  ALLOWED_URL_PROTOCOLS,
};
