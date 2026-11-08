/**
 * MatuX Electron 主进程
 *
 * 负责：
 * 1. 协调各模块初始化
 * 2. 窗口管理
 * 3. IPC 安全通信桥接
 * 4. 应用生命周期管理
 *
 * 【重构】核心逻辑已抽取到独立模块：
 * - 后端管理: src/core/backend
 * - 启动流程: src/core/startup
 * - IPC 处理器: src/core/ipc/handlers
 * - 安全验证: src/core/security
 * - 窗口管理: src/ui/window-manager
 * - 托盘管理: src/ui/tray-manager
 * - 快捷键: src/core/shortcuts
 * - 自动更新: src/core/updates
 */

const {
  app,
  BrowserWindow,
  ipcMain,
  dialog,
  shell,
  protocol,
  net,
  screen,
  Menu,
} = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { pathToFileURL } = require('url');

// 【P0-静默退出】主进程持久化日志：必须尽早安装 console tee。
// 打包后应用没有可见控制台，若不落盘，uncaughtException / window-all-closed
// 等退出路径不会留下任何证据，表现为“应用凭空消失”。
const mainLogger = require('./utils/main-logger');
mainLogger.installConsoleTee();

// 【重构】配置常量
const {
  BACKEND_PORT,
  BACKEND_HOST,
  BACKEND_URL,
  HEALTH_CHECK_INTERVAL,
  MODULE_STATUS_INTERVAL,
  MODULE_STATUS_CACHE_SIZE,
  EXEC_SYNC_TIMEOUT,
  MAX_FILE_SIZE,
  HTTP_REQUEST_TIMEOUT,
  HEALTH_CHECK_DETAIL_INTERVAL,
  PORT_WAIT_INTERVAL,
  HEALTH_URL,
  HEALTH_DETAIL_URL,
  MODULES_URL,
  isDev,
  WINDOW_STATE_FILE,
  DEFAULT_WINDOW_SIZE,
  SPLASH_WINDOW_SIZE,
  SPLASH_RENDER_DELAY,
  APP_PATHS,
  APP_PROTOCOL,
  APP_PROTOCOL_PRIVILEGES,
  FRONTEND_LOAD_TIMEOUT,
  CRITICAL_PYTHON_PACKAGES,
  PYTHON_MIN_VERSION,
  ALLOWED_URL_PROTOCOLS,
  BACKEND_RESTART_DELAY,
  BACKEND_START_TIMEOUT,
  TIER1_PRELOAD_TIMEOUT,
  MAX_RESTART_ATTEMPTS,
} = require('./config/constants');

// 【重构】安全验证
const { validateExternalUrl, validateFilePath, getAllowedPaths } = require('./security');

// 【重构】后端核心模块
const backendCore = require('./src/core/backend');
const {
  detectPython,
  checkPythonDeps,
  checkPortOccupation,
  forceKillPortProcess,
  healthCheck,
  BackendManager,
} = backendCore;

// 【重构】AppState
const { AppState } = require('./core/app-state');
const appState = AppState.getInstance();

// 【重构】IPC Handlers
const {
  createBackendHandlers,
  createWindowHandlers,
  createNotificationHandlers,
  createSystemHandlers,
  createPluginHandlers,
  createFsHandlers,
  createUpdaterHandlers,
} = require('./src/core/ipc/handlers');

// 【重构】窗口状态管理
const { loadWindowState, saveWindowState } = require('./src/core/utils/window-state');

// 【重构】快捷键管理
const { registerGlobalShortcuts, unregisterGlobalShortcuts } = require('./src/core/shortcuts');

// 【重构】自动更新
const { checkForUpdates } = require('./src/core/updates');

// 【重构】应用启动器
const { AppInitializer } = require('./src/core/startup/app-initializer');

// 【重构】服务层
const { preloadTier1Modules } = require('./services');

// 【重构】UI 模块
const { SplashManager, WindowManager, TrayManager, showNotification: showTrayNotification } = require('./src/ui');

// ==================== 全局状态 ====================

let mainWindow = null;
let splashWindow = null;
let appInitializer = null;
let isStarting = false;
let isQuitting = false;

// 【P0-静默退出】退出原因：所有 app.quit()/process.exit() 调用点必须先打标，
// 这样日志里能直接看出“谁让应用退出的”，不再出现无痕消失。
let quitReason = 'running';
function markQuit(reason) {
  quitReason = reason;
  mainLogger.logEvent('QUIT-REQUEST', {
    reason,
    uptimeSec: Math.round(process.uptime()),
    stack: new Error('quit-trace').stack,
  });
}

// 主进程异常只提示一次，避免弹窗轰炸
let mainProblemDialogShown = false;
function notifyMainProcessProblem(title, detail) {
  if (mainProblemDialogShown) return;
  mainProblemDialogShown = true;
  try {
    dialog.showMessageBox({
      type: 'warning',
      title: 'MatuX 运行异常',
      message: title,
      detail: `${detail || ''}\n\n异常详情已写入日志：\n${mainLogger.getLogFile()}`,
      buttons: ['继续使用', '退出应用'],
      defaultId: 0,
      cancelId: 0,
      noLink: true,
    }).then(({ response }) => {
      mainLogger.logEvent('CRASH-DIALOG-CHOICE', { response });
      if (response === 1) {
        markQuit('user-exit-after-exception');
        app.quit();
      } else {
        // 用户选择继续：允许后续异常再次提示
        mainProblemDialogShown = false;
      }
    }).catch(() => { /* 弹窗失败不影响主流程 */ });
  } catch (_) {
    // dialog 不可用（极端场景）时仅依赖日志
  }
}

// ==================== 自定义协议注册 ====================
// 【启动优化】必须在 app.whenReady() 之前调用 protocol.registerSchemesAsPrivileged()
// 使用 app:// 协议代替 file://，避免 file:// 协议下 ES module 加载被浏览器拒绝
protocol.registerSchemesAsPrivileged([
  {
    scheme: APP_PROTOCOL,
    privileges: APP_PROTOCOL_PRIVILEGES,
  },
]);

/**
 * 自定义协议 handler：将 app:// 请求映射到本地 dist/imatuproject 目录
 * 避免 file:// 协议下 ES module 加载限制（Chromium 安全策略）
 *
 * 【修复 #1】增加 SPA fallback：Angular 使用 PathLocationStrategy，
 *   路由跳转/刷新时会请求 app://./learn 等路径，需 fallback 到 index.html
 *   参考 webpack-dev-server 的 historyApiFallback 行为
 */
function registerAppProtocol() {
  protocol.handle(APP_PROTOCOL, (request) => {
    try {
      const url = new URL(request.url);
      // app://./index.html → ./index.html（取 pathname 去掉前导斜杠）
      let relativePath = url.pathname;
      // Windows 路径处理：去掉开头的 /
      if (process.platform === 'win32' && relativePath.startsWith('/')) {
        relativePath = relativePath.substring(1);
      }
      // 【修复 #1】空路径默认为 index.html
      if (relativePath === '' || relativePath === '/') {
        relativePath = 'index.html';
      }

      const filePath = path.join(APP_PATHS.frontendDir, relativePath);
      // 安全检查：防止路径跳出 dist 目录
      // 【安全】必须加 path.sep，避免同名前缀目录被绕过
      // 例：'imatuproject2' 不会被 'imatuproject' 错误包含
      const resolved = path.resolve(filePath);
      const frontendRoot = path.resolve(APP_PATHS.frontendDir);
      if (resolved !== frontendRoot && !resolved.startsWith(frontendRoot + path.sep)) {
        console.warn('[Protocol] 拒绝越权访问:', resolved);
        return new Response('Forbidden', { status: 403 });
      }
      // 文件存在直接返回
      if (fs.existsSync(resolved)) {
        return net.fetch(pathToFileURL(resolved).toString());
      }
      // 【修复 #1】SPA fallback 策略：
      // 1. 有扩展名且不在白名单（API/资源）→ 返回 404
      // 2. 无扩展名或 SPA 路径 → fallback 到 index.html（Angular Router 会处理路由）
      const hasExtension = /\.[a-zA-Z0-9]+$/.test(relativePath);
      const isApiOrAsset = relativePath.startsWith('api/') ||
                           relativePath.startsWith('assets/') ||
                           relativePath.startsWith('_app/');
      // 【修复 #9】API/资源路径应当代理到真实后端，而不是 fallback 到 index.html
      //   原因：Angular environment.apiUrl = '' 使渲染进程用相对路径发起 fetch，
      //   被 base href './' 解析为 app://./api/...，需要代理到后端。
      if (isApiOrAsset) {
        const backendUrl = `${process.env.BACKEND_URL || `http://localhost:${process.env.BACKEND_PORT || 8000}`}/${relativePath}`;
        // 【加固】完整生命周期：记录 method/URL，响应后记录 status + durationMs，
        //   在失败/超时/5xx 时主动报 proxy-error 事件给前端，避免前端 fetch 永远 pending。
        const upperMethod = (request.method || 'GET').toUpperCase();
        const reqStart = Date.now();
        console.log(`[Protocol] → ${upperMethod} ${backendUrl}`);
        const notifyProxyError = (source, errMsg, status) => {
          const durationMs = Date.now() - reqStart;
          safeSendAppEvent({
            type: 'proxy-error',
            source, // 'proxy' = 代理层同步/异步异常；'backend' = 后端 5xx
            path: relativePath,
            method: upperMethod,
            backendUrl: maskBackendUrl(backendUrl),
            targetStatus: status || 0,
            durationMs,
            errorMessage: errMsg || '',
            timestamp: new Date().toISOString(),
          });
          return durationMs;
        };
        // 【修复】转发原始请求的 method、headers、body，确保 POST/PUT 等方法正确代理
        // 【P1 修复】补 duplex: 'half'：
        //   Electron 28 / Node 18 自带的 undici 在 RequestInit 带 body 时强制要求
        //   duplex: 'half'，否则同步抛 `TypeError: RequestInit: duplex option is required when sending a body.`
        //   该异常在 protocol.handle 回调中无法变成响应回传给浏览器，导致前端 fetch 永远 pending。
        //   表现为：桌面端点击登录卡在 "Validating credentials..." 永远不返回。
        //   修复后 POST/PUT/PATCH 等带 body 的请求可正常代理到后端。
        try {
          const init = {
            method: request.method,
            headers: request.headers,
          };
          // 仅在有 body 时透传 + 声明 duplex（GET/HEAD 等不允许有 body）
          if (upperMethod !== 'GET' && upperMethod !== 'HEAD') {
            if (request.body) {
              init.body = request.body;
              init.duplex = 'half';
            }
          }
          return net.fetch(backendUrl, init)
            .then((response) => {
              const durationMs = Date.now() - reqStart;
              console.log(`[Protocol] ← ${response.status} ${upperMethod} ${relativePath} (${durationMs}ms)`);
              // 【加固】后端明确 5xx：记录并报事件，调用方不必额外代码即可拿到信号
              if (response.status >= 500) {
                safeSendAppEvent({
                  type: 'proxy-error',
                  source: 'backend',
                  path: relativePath,
                  method: upperMethod,
                  backendUrl: maskBackendUrl(backendUrl),
                  targetStatus: response.status,
                  durationMs,
                  timestamp: new Date().toISOString(),
                });
              }
              return response;
            })
            .catch((fetchErr) => {
              const fetchMsg =
                (fetchErr && fetchErr.message) ||
                (typeof fetchErr === 'string' ? fetchErr : String(fetchErr));
              notifyProxyError('proxy', fetchMsg, 0);
              console.error('[Protocol] API代理 fetch 失败:', fetchMsg);
              return new Response(`Bad Gateway: ${relativePath}\n${fetchMsg}`, {
                status: 502,
                headers: { 'Content-Type': 'text/plain; charset=utf-8' },
              });
            });
        } catch (proxyErr) {
          const proxyMsg =
            (proxyErr && proxyErr.message) || (typeof proxyErr === 'string' ? proxyErr : String(proxyErr));
          console.error('[Protocol] API代理同步异常:', proxyMsg);
          notifyProxyError('proxy', proxyMsg, 0);
          return new Response(`Bad Gateway: ${relativePath}\n${proxyMsg}`, {
            status: 502,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
          });
        }
      }
      if (hasExtension) {
        // 有扩展名但不是已知 API 路径（如 .json、.ico、.map 等）→ 404
        console.warn('[Protocol] 资源不存在:', resolved);
        return new Response('Not Found: ' + relativePath, { status: 404 });
      }
      // fallback 到 index.html
      const indexPath = path.join(APP_PATHS.frontendDir, 'index.html');
      if (fs.existsSync(indexPath)) {
        console.log(`[Protocol] SPA fallback: ${relativePath} -> index.html`);
        // 【N1-fix-B】检测到 URL 形如 app://./index.html/<x>，需 302 重定向到 app://./<x>
        //   原因：Angular Router 看到 location.pathname = "/index.html/<x>" 不匹配任何路由 (NG04002)
        //   重定向后，浏览器 URL 变成 app://./<x>，Angular Router 才能正常解析 <x> 路径
        if (/^index\.html\/(.+)$/i.test(relativePath)) {
          const tail = relativePath.replace(/^index\.html\//i, '');
          // 含查询串需追加
          const target = `${APP_PROTOCOL}://./${tail}${url.search || ''}${url.hash || ''}`;
          console.log(`[Protocol] SPA redirect: ${relativePath} -> ${target}`);
          return Response.redirect(target, 302);
        }
        // 【N1-fix】重写 <base href="./"> 为 <base href="app://./">
        // 原因：当 SPA 路由 URL 为 app://./index.html/user/dashboard 时，
        //   <base href="./"> 会被解析为 app://./index.html/user/ ，
        //   导致 <script src="runtime.xxx.js"> 解析为 app://./index.html/user/runtime.xxx.js → 404
        //   改为绝对 base href "app://./" 后，子资源固定从 app://./ 解析，与当前 URL 路径无关
        try {
          const html = fs.readFileSync(indexPath, 'utf8');
          // 替换 <base href="./"> （含单/双引号）
          const rewritten = html.replace(
            /<base\s+href=(["'])\.\/?\1\s*>/i,
            `<base href=$1${APP_PROTOCOL}://./$1>`
          );
          if (rewritten !== html) {
            console.log(`[Protocol] base href rewritten to ${APP_PROTOCOL}://./`);
            return new Response(rewritten, {
              status: 200,
              headers: { 'Content-Type': 'text/html; charset=utf-8' },
            });
          }
        } catch (rewriteErr) {
          console.warn('[Protocol] base href rewrite failed, fallback to raw fetch:', rewriteErr.message);
        }
        return net.fetch(pathToFileURL(indexPath).toString());
      }
      // index.html 也不存在（构建产物损坏）→ 真正的 404
      console.error('[Protocol] index.html 不存在，dist 目录可能构建不完整');
      return new Response('Not Found: index.html missing', { status: 404 });
    } catch (err) {
      console.error('[Protocol] 处理 app:// 请求失败:', err);
      return new Response('Internal Error: ' + err.message, { status: 500 });
    }
  });
  console.log('[Main] 已注册自定义协议 handler:', APP_PROTOCOL);
}

// 窗口管理器引用（用于 macOS activate 事件）
const windowManager = {
  getMainWindow: () => mainWindow,
};

// ==================== 窗口创建 ====================

/**
 * 创建 Splash Screen 窗口
 */
function createSplashWindow() {
  // 验证 Splash preload 脚本路径
  if (!APP_PATHS.preloadSplash || !fs.existsSync(APP_PATHS.preloadSplash)) {
    console.error('[Main] Splash preload 脚本不存在:', APP_PATHS.preloadSplash);
    throw new Error(`Splash preload 脚本不存在: ${APP_PATHS.preloadSplash}`);
  }
  
  splashWindow = new BrowserWindow({
    width: SPLASH_WINDOW_SIZE.width,
    height: SPLASH_WINDOW_SIZE.height,
    frame: false,
    transparent: false,
    resizable: false,
    alwaysOnTop: true,
    center: true,
    show: false,
    backgroundColor: '#0a0e1a',
    webPreferences: {
      preload: APP_PATHS.preloadSplash,
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: APP_PATHS.icon,
  });

  splashWindow.loadFile(APP_PATHS.splashHtml);
  splashWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.show();
      // 【调试】自动打开 DevTools 查看 Splash 错误
      if (process.env.SPLASH_DEBUG === '1') {
        splashWindow.webContents.openDevTools({ mode: 'detach' });
      }
    }
  });

  // 捕获 Splash 渲染进程的控制台输出
  splashWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    const prefix = level === 0 ? '[Splash-ERROR]' : level === 1 ? '[Splash-WARN]' : '[Splash-LOG]';
    console.log(prefix, message, `(${sourceId}:${line})`);
  });

  // 捕获 Splash 渲染进程崩溃
  splashWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Splash-CRASH]', details.reason, details.exitCode);
  });
  splashWindow.on('closed', () => { splashWindow = null; });

  // 监听 Splash 进入迷你模式 → 调整窗口尺寸并贴底显示
  ipcMain.once('splash-mini-mode', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      const { screen } = require('electron');
      const display = screen.getPrimaryDisplay();
      const { width: screenWidth, height: screenHeight } = display.workAreaSize;
      // 先允许调整大小，再恢复不可调整
      splashWindow.setResizable(true);
      splashWindow.setBounds({
        x: 0,
        y: screenHeight - 44,
        width: screenWidth,
        height: 44,
      });
      splashWindow.setResizable(false);
      splashWindow.setAlwaysOnTop(true, 'floating');
      console.log('[Main] Splash 已切换为迷你横条模式');
    }
  });
}

/**
 * 创建主应用窗口
 */
function createMainWindow(windowManager) {
  // 验证 preload 脚本路径
  if (!APP_PATHS.preload || !fs.existsSync(APP_PATHS.preload)) {
    console.error('[Main] Preload 脚本不存在:', APP_PATHS.preload);
    throw new Error(`Preload 脚本不存在: ${APP_PATHS.preload}`);
  }
  
  const savedState = loadWindowState();
  
  // 验证保存的窗口状态有效性
  // 【修复 #5】除类型与正值校验外，还需校验 x/y 是否在任意显示器可见区域内
  // 防止用户上次使用外接显示器，状态文件中保存的坐标超出当前主屏范围，
  // 导致窗口创建后不可见（用户感觉是“白屏”）
  const validateWindowState = (state) => {
    if (!state || typeof state !== 'object') return {};
    // 【安全】使用 Object.create(null) 创建无原型对象，防止原型链污染
    const result = Object.create(null);
    if (typeof state.width === 'number' && state.width > 0) result.width = state.width;
    if (typeof state.height === 'number' && state.height > 0) result.height = state.height;
    if (typeof state.x === 'number' && state.x >= 0) result.x = state.x;
    if (typeof state.y === 'number' && state.y >= 0) result.y = state.y;
    if (typeof state.isMaximized === 'boolean') result.isMaximized = state.isMaximized;

    // 校验 x/y 是否在主显示器的 workArea 内（至少 100x100 像素可见）
    // 【修复】严格限定主显示器，避免窗口被还原到副屏导致用户看不到
    if (typeof result.x === 'number' && typeof result.y === 'number' &&
        typeof result.width === 'number' && typeof result.height === 'number') {
      try {
        const primary = screen.getPrimaryDisplay();
        const wa = primary.workArea;
        const visibleW = Math.min(result.x + result.width, wa.x + wa.width) - Math.max(result.x, wa.x);
        const visibleH = Math.min(result.y + result.height, wa.y + wa.height) - Math.max(result.y, wa.y);
        const isOnPrimary = visibleW >= 100 && visibleH >= 100;
        if (!isOnPrimary) {
          console.warn(`[Main] 保存的窗口坐标 (${result.x}, ${result.y}) 不在主显示器内，使用主屏居中`);
          delete result.x;
          delete result.y;
        }
      } catch (e) {
        // screen 模块不可用时保守处理：保留 x/y（不破坏向后兼容）
        console.warn('[Main] 校验窗口坐标失败:', e.message);
      }
    }
    return result;
  };
  
  const validatedState = validateWindowState(savedState);

  mainWindow = new BrowserWindow({
    width: validatedState.width || DEFAULT_WINDOW_SIZE.width,
    height: validatedState.height || DEFAULT_WINDOW_SIZE.height,
    minWidth: 1024,
    minHeight: 768,
    x: validatedState.x,
    y: validatedState.y,
    show: false,
    // 【修复 #7】主窗口深色背景色，避免 Angular 渲染前瞬间显示 Electron 默认白色背景
    backgroundColor: '#0a0e1a',
    webPreferences: {
      preload: APP_PATHS.preload,
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: APP_PATHS.icon,
    // 【无边框窗口 P3】桌面端自定义标题栏
    // - Windows/Linux: frame:false 彻底去掉原生标题栏与边框，拖拽区由渲染进程
    //   的 -webkit-app-region: drag 提供，窗口控制按钮走 window:* IPC
    // - macOS: 保留原生 traffic lights（frame:true + hiddenInset），无边框会让
    //   窗口失去关闭入口；渲染进程会自动隐藏自定义按钮组
    // - 不设 transparent:true: Windows 下透明窗口会丢失 DWM 阴影，拖动时残影
    frame: process.platform === 'darwin',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'hidden',
    // Windows 11: 圆角 + 阴影由 DWM 处理；thickFrame 保持默认 true，
    // 无边框下仍可从四边/四角拖拽调整窗口大小
    ...(process.platform === 'win32' ? { roundedCorners: true, hasShadow: true } : {}),
    title: 'MatuX',
  });

  // 恢复最大化状态
  if (validatedState.isMaximized) mainWindow.maximize();

  // 加载前端应用
  if (isDev) {
    mainWindow.loadURL('http://localhost:4200');
    // 【安全】仅在开发模式下打开DevTools
    if (isDev && process.env.NODE_ENV !== 'production') {
      mainWindow.webContents.openDevTools();
    }
  } else {
    // 【启动优化】使用自定义协议 app:// 代替 file://
    // 避免 file:// 协议下 ES module 加载被 Chromium 拒绝（CORS 安全策略）
    // 优点：与 Web 部署同源、Service Worker 可用、支持 fetch / XHR
    const frontendUrl = `${APP_PROTOCOL}://./index.html`;
    console.log('[Main] Loading frontend from:', frontendUrl);

    // 前端加载状态标志
    let frontendReady = false;
    let loadTimedOut = false;  // 【修复 #4】超时标志位，防止重试与超时竟态
    let loadAttempts = 0;
    const maxAttempts = 3;
    const retryDelay = 2000;

    // 【加载保护】30 秒超时：如 did-finish-load 未触发，显示错误页
    const loadTimeoutTimer = setTimeout(() => {
      if (!frontendReady && mainWindow && !mainWindow.isDestroyed()) {
        loadTimedOut = true;  // 【修复 #4】设置超时标志，后续重试需检查
        console.error('[Main] 前端加载超时 (' + (FRONTEND_LOAD_TIMEOUT / 1000) + 's)，显示错误页');
        const errorHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>MatuX - 加载失败</title><style>
          body{font-family:-apple-system,sans-serif;background:#0a0e1a;color:#e2e8f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;text-align:center}
          .error-box{max-width:500px;padding:32px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:12px}
          h1{color:#ef4444;margin-bottom:16px}
          p{color:#94a3b8;margin-bottom:24px;line-height:1.6}
          button{padding:8px 24px;background:#3b82f6;color:white;border:none;border-radius:6px;cursor:pointer}
          button:hover{background:#2563eb}
        </style></head><body><div class="error-box">
          <h1>⚠️ 前端加载超时</h1>
          <p>前端页面在 ${FRONTEND_LOAD_TIMEOUT / 1000} 秒内未能完成加载。</p>
          <p>可能原因：<br>- dist/imatuproject 目录构建不完整<br>- 资源文件缺失或损坏<br>- 自定义协议注册失败</p>
          <button onclick="location.reload()">重新加载</button>
        </div></body></html>`;
        mainWindow.webContents.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHtml)}`);
      }
    }, FRONTEND_LOAD_TIMEOUT);

    // 【加载完成事件】监听 did-finish-load 后设置 frontendReady
    mainWindow.webContents.once('did-finish-load', () => {
      console.log('[Main] ✅ Frontend finished loading');
      frontendReady = true;
      clearTimeout(loadTimeoutTimer);
    });

    const attemptLoad = () => {
      // 【修复 #4】提前检查：已就绪或超时则不重试，避免竟态
      if (frontendReady || loadTimedOut) {
        return;
      }
      loadAttempts++;
      mainWindow.loadURL(frontendUrl)
        .then(() => {
          console.log('[Main] Frontend loadURL resolved (attempt ' + loadAttempts + ')');
        })
        .catch((err) => {
          // 【修复 #4】错误发生后再次检查标志位
          if (loadTimedOut || frontendReady) return;

          console.error(`[Main] Failed to load frontend (attempt ${loadAttempts}/${maxAttempts}):`, err.message);

          if (loadAttempts < maxAttempts) {
            // 尝试重新加载
            console.log(`[Main] Retrying in ${retryDelay}ms...`);
            setTimeout(attemptLoad, retryDelay);
          } else {
            // 达到最大重试次数，发送错误事件
            console.error('[Main] Max load attempts reached, frontend unavailable');
            clearTimeout(loadTimeoutTimer);
            if (mainWindow && !mainWindow.isDestroyed()) {
              mainWindow.webContents.send('app-event', {
                type: 'frontend-load-error',
                error: '前端资源加载失败',
                detail: err.message,
                recoverable: false
              });
            }
          }
        });
    };

    attemptLoad();
  }

  // 监听页面加载错误
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[Main] Page failed to load:', errorCode, errorDescription);
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', {
        type: 'page-load-failed',
        errorCode,
        errorDescription
      });
    }
  });

  mainWindow.webContents.on('crashed', (event, killed) => {
    console.error('[Main] Renderer process crashed! killed:', killed);
    mainLogger.logEvent('RENDERER-CRASHED', { killed });
    // 尝试通知用户并提供恢复选项
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('app-event', {
        type: 'renderer-crashed',
        killed
      });
    }
    // 如果未被 kill，尝试恢复
    if (!killed) {
      console.log('[Main] 尝试恢复渲染进程...');
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.reload();
        }
      }, 1000);
    }
  });

  // 主窗口就绪后显示，并通知 Splash 切换为迷你横条模式
  // Splash 不再在此处关闭，而是在后端完全就绪后才淡出
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // 前端样式已就绪，但不要立即切换迷你模式
    // 【修复】只有后端完全就绪时才切换 mini-mode，让用户看到完整启动动画
    if (splashWindow && !splashWindow.isDestroyed()) {
      sendSplashStatus('frontend-ready', 'Frontend loaded, backend loading...', 50);
    }
  });

  // 【P0-静默退出】渲染进程消失留痕（Chromium 新版事件，含 OOM / 被杀原因）
  mainWindow.webContents.on('render-process-gone', (event, details) => {
    mainLogger.logEvent('RENDER-PROCESS-GONE', details);
    mainLogger.writeCrashReport(
      'render-process-gone',
      new Error(`renderer gone: ${details && details.reason}`),
      details
    );
  });

  // 窗口事件绑定
  mainWindow.on('closed', () => { mainLogger.logEvent('MAIN-WINDOW-CLOSED', { isQuitting, quitReason }); mainWindow = null; });

  mainWindow.on('blur', () => mainWindow.webContents.send('app-event', { type: 'window-blur' }));
  mainWindow.on('focus', () => mainWindow.webContents.send('app-event', { type: 'window-focus' }));
  mainWindow.on('enter-full-screen', () => mainWindow.webContents.send('app-event', { type: 'fullscreen-enter' }));
  mainWindow.on('leave-full-screen', () => mainWindow.webContents.send('app-event', { type: 'fullscreen-leave' }));

  // 【无边框窗口 P3】最大化状态广播：渲染进程据此切换 □ / ❐ 图标
  const broadcastMaximizeState = () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('window:maximize-change', mainWindow.isMaximized());
    }
  };
  mainWindow.on('maximize', broadcastMaximizeState);
  mainWindow.on('unmaximize', broadcastMaximizeState);

  // 【无边框窗口 P3】菜单移除后 F11 全屏快捷键兜底（原本由默认菜单 role 提供）
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.key !== 'F11') return;
    mainLogger.logEvent('F11-KEY', { type: input.type, control: input.control, alt: input.alt, shift: input.shift });
    if (input.type !== 'keyDown') return;
    event.preventDefault();
    if (mainWindow && !mainWindow.isDestroyed()) {
      const nextFullscreen = !mainWindow.isFullScreen();
      mainWindow.setFullScreen(nextFullscreen);
      mainLogger.logEvent('F11-TOGGLE', { fullscreen: nextFullscreen });
    }
  });

  // 窗口大小变化（节流）
  let resizeTimeout = null;
  mainWindow.on('resize', () => {
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        const [w, h] = mainWindow.getSize();
        mainWindow.webContents.send('app-event', { type: 'window-resize', width: w, height: h });
        saveWindowState(mainWindow);
      }
    }, 200);
  });

  // 窗口移动（防抖）
  let moveTimeout = null;
  mainWindow.on('move', () => {
    if (moveTimeout) clearTimeout(moveTimeout);
    moveTimeout = setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        saveWindowState(mainWindow);
      }
    }, 500);
  });

  // 最小化到托盘
  mainWindow.on('close', (event) => {
    // 清理定时器
    if (resizeTimeout) {
      clearTimeout(resizeTimeout);
      resizeTimeout = null;
    }
    if (moveTimeout) {
      clearTimeout(moveTimeout);
      moveTimeout = null;
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
    if (!isQuitting && appInitializer?.tray) {
      event.preventDefault();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.hide();
      }
      return;
    }
    // 【P0-静默退出】托盘不可用时（创建失败/尚未创建），直接关窗口会走到
    //   window-all-closed → app.quit()，用户感知为“应用凭空消失”。
    //   这里改为显式确认：取消 → 最小化，确认 → 标记退出原因后放行。
    if (!isQuitting) {
      let choice = null;
      try {
        choice = dialog.showMessageBoxSync(mainWindow, {
          type: 'question',
          title: 'MatuX',
          message: '确定要退出 MatuX 吗？',
          detail: '当前系统托盘不可用，关闭窗口将直接退出应用。',
          buttons: ['最小化到任务栏', '退出应用'],
          defaultId: 0,
          cancelId: 0,
          noLink: true,
        });
      } catch (_) {
        choice = null;
      }
      mainLogger.logEvent('CLOSE-CONFIRM', { choice, tray: false });
      if (choice !== 1) {
        event.preventDefault();
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.minimize();
        }
      } else {
        markQuit('user-confirm-quit-no-tray');
      }
    }
  });

  return mainWindow;
}

// ==================== 工具函数 ====================

/**
 * 安全发送 app-event 到主窗口
 * 【加固】所有主进程 → 渲染进程的发送都过这里，避免主窗口未创建 / isDestroyed / webContents 不可用导致额外异常
 * @param {object} payload
 */
function safeSendAppEvent(payload) {
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      const wc = mainWindow.webContents;
      if (wc && !wc.isCrashed() && !wc.isDestroyed()) {
        wc.send('app-event', payload);
      }
    }
  } catch (_sendErr) {
    // 静默忽略：上层不必要知道诊断包发送失败
  }
}

/**
 * 给用户/前端看的“安全” backendUrl，掼除可能的 BasicAuth 凭据
 * 例如 http://user:pass@host:8000 → http://****@host:8000
 */
function maskBackendUrl(url) {
  if (typeof url !== 'string') return '';
  try {
    return url.replace(/(:\/\/)([^:@/]+):([^@]+)@/, '$1$2:****@');
  } catch {
    return url;
  }
}

/**
 * 向 Splash 窗口发送状态更新
 *
 * @param {string} phase - 启动阶段标识
 * @param {string|null} text - 显示文本
 * @param {number|undefined} progress - 进度百分比 0-100
 * @param {string|null} detail - 错误详情
 * @param {Array|null} modules - 模块状态列表
 * @param {Object} [flags] - 额外标志位
 * @param {boolean} [flags.miniMode] - 通知 Splash 切换到迷你横条模式
 * @param {boolean} [flags.fadeOut] - 通知 Splash 淡出关闭
 */
function sendSplashStatus(phase, text, progress, detail, modules, flags) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    const miniMode = flags && flags.miniMode ? true : false;
    const fadeOut = flags && flags.fadeOut ? true : false;
    // 【新增】backend-log 不计入进度，仅传递 detail.stream 以供 splash 识别
    const payload = { phase, text, progress, detail, modules, miniMode, fadeOut };
    if (phase === 'backend-log' && detail && detail.stream) {
      payload.stream = detail.stream;
    }
    splashWindow.webContents.send('splash-status', payload);
  }
  // 后端真实日志不再重复打印到主进程 console（避免洪水）
  if (phase !== 'backend-log') {
    const prefix = phase === 'error' || phase === 'backend-error' ? '[ERROR]' : '[INFO]';
    console.log(`${prefix} ${text || phase}`);
  }
}

/**
 * 健康检查函数
 */
async function healthCheckWrapper() {
  try {
    return await new Promise((resolve) => {
      const req = http.get(HEALTH_URL, { timeout: HTTP_REQUEST_TIMEOUT }, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const json = JSON.parse(data);
            // 验证响应格式
            if (json && typeof json === 'object' && 'status' in json) {
              resolve({ success: true, data: json });
            } else {
              // 响应格式不正确
              console.warn('[Health] 健康检查响应格式无效:', json);
              resolve({ success: false, error: 'Invalid health check response format' });
            }
          } catch {
            // JSON 解析失败
            console.warn('[Health] 健康检查响应不是有效 JSON');
            resolve({ success: false, error: 'Invalid JSON response' });
          }
        });
      });
      req.on('error', (err) => resolve({ success: false, error: err.message }));
      req.on('timeout', () => { req.destroy(); resolve({ success: false, error: '请求超时' }); });
    });
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/**
 * 创建子窗口（用于数字孪生实验室等多窗口场景）
 */
function createChildWindow(data) {
  // 验证 preload 脚本路径
  const preloadPath = APP_PATHS.preload;
  if (!preloadPath || !fs.existsSync(preloadPath)) {
    console.error('[Main] 子窗口 preload 脚本不存在:', preloadPath);
    return null;
  }

  const childWindow = new BrowserWindow({
    width: data.width || 1200,
    height: data.height || 800,
    title: data.title || 'MatuX - 子窗口',  // 【修复】设置默认窗口标题
    parent: mainWindow,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,  // 启用沙箱
    },
  });

  if (data.url) {
    // 验证 URL 安全性
    const urlValidation = validateExternalUrl(data.url);
    if (!urlValidation.valid) {
      console.error('[Main] 子窗口 URL 不安全:', urlValidation.error);
      childWindow.close();
      return null;
    }
    childWindow.loadURL(data.url);
  } else if (data.html) {
    // 【安全】禁用 data:text/html 加载以防止 XSS 攻击
    // Electron 的 data:text/html 可能执行恶意脚本
    console.warn('[Main] 拒绝加载内联 HTML 内容以防止 XSS 攻击');
    childWindow.close();
    return null;
  }

  return childWindow;
}

// ==================== 文件关联 ====================

// 【重构】文件解析服务
const { isValidFileName, safeReadFile, getFileType } = require('./services/file-parser');

/**
 * 设置文件关联处理
 * 支持: .imato (课程包), .imblockly (Blockly项目), .imcircuit (电路项目)
 */
function setupFileAssociation() {
  // 发送文件事件到渲染进程的辅助函数
  const sendFileEvent = (filePath, result) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      if (result.success) {
        // 发送完整的文件数据（包括解析后的 JSON 和文件类型）
        mainWindow.webContents.send('app-event', {
          type: 'open-file',
          filePath,
          content: result.content,
          fileType: result.fileType,
        });
        console.log(`[INFO] 成功打开文件: ${filePath} (类型: ${result.fileType})`);
      } else {
        console.error('[ERROR] 读取文件失败:', result.error);
      }
    }
  };

  // macOS: open-file 事件
  app.on('open-file', (event, filePath) => {
    event.preventDefault();
    const fileName = path.basename(filePath);
    if (!isValidFileName(fileName)) {
      console.warn('[WARN] 拒绝打开不安全的文件:', filePath);
      return;
    }
    console.log('[INFO] macOS 文件关联打开:', filePath);
    const result = safeReadFile(filePath);
    sendFileEvent(filePath, result);
  });

  // Windows: 命令行参数
  const associatedFile = process.argv.find((arg) => {
    if (!arg || typeof arg !== 'string') return false;
    const fileName = path.basename(arg);
    return isValidFileName(fileName);
  });
  if (associatedFile && fs.existsSync(associatedFile)) {
    console.log('[INFO] Windows 命令行打开文件:', associatedFile);
    app.once('main-window-ready', () => {
      const result = safeReadFile(associatedFile);
      sendFileEvent(associatedFile, result);
    });
  }
}

// ==================== IPC 处理器注册 ====================

// 防止 IPC 处理器重复注册
let ipcHandlersRegistered = false;

/**
 * 注册所有 IPC 处理器
 */
function registerIpcHandlers() {
  if (ipcHandlersRegistered) {
    console.warn('[WARN] IPC 处理器已注册，跳过重复注册');
    return;
  }
  ipcHandlersRegistered = true;

  const backendHandlers = createBackendHandlers({ backendManager: appInitializer?.getBackendManager(), appState, appInitializer });
  backendHandlers.register();

  // 【无边框窗口 P3】窗口控制按钮必须能拿到真实主窗口引用：
  //   appState.setMainWindow() 在 createMainWindow 中并未被调用，仅靠 appState
  //   会拿到 null，导致 window-minimize/maximize/close 全部静默失效。
  //   这里注入主进程模块级 mainWindow 的实时读取闭包（注册时窗口尚未创建，
  //   所以必须是函数而不是值）。
  const windowHandlers = createWindowHandlers({ appState, getMainWindow: () => mainWindow });
  windowHandlers.register();

  const notificationHandlers = createNotificationHandlers({ appState, showNotification: showTrayNotification });
  notificationHandlers.register();

  const systemHandlers = createSystemHandlers({ app, isDev });
  systemHandlers.register();

  const pluginHandlers = createPluginHandlers({
    appState,
    assessDevice: appInitializer?.assessDevice,
    loadDeviceProfile: appInitializer?.loadDeviceProfile,
    saveDeviceProfile: appInitializer?.saveDeviceProfile,
    shouldReassess: appInitializer?.shouldReassess,
    pluginInstaller: appInitializer?.pluginInstaller,
    pluginDownloader: appInitializer?.pluginDownloader,
    pluginRecommender: appInitializer?.PluginRecommendationEngine,
    installConfigManager: appInitializer?.InstallConfigManager,
    // 修复命名不一致: PluginStoreEnhancer -> pluginStoreEnhancer
    pluginStoreEnhancer: appInitializer?.PluginStoreEnhancer,
    pluginRegistry: appInitializer?.pluginRegistry,
  });
  pluginHandlers.register();

  const fsHandlers = createFsHandlers({ mainWindow, validateFilePath, dialog });
  fsHandlers.register();

  // 自动更新 IPC 处理器
  let updaterService = null;
  try {
    const { AutoUpdaterService } = require('./services/auto-updater');
    updaterService = new AutoUpdaterService();
  } catch (err) {
    console.warn('[WARN] AutoUpdaterService 初始化失败，更新功能受限:', err.message);
  }
  const updaterHandlers = createUpdaterHandlers({ updaterService });
  updaterHandlers.register();
}

// ==================== 应用生命周期 ====================

// 清理残留的 Chromium SingletonLock 文件（防止上次异常退出后锁文件残留）
function cleanupSingletonLockFiles() {
  if (process.platform !== 'win32') return 0;
  try {
    const userData = app.getPath('userData');
    const lockFiles = ['SingletonLock', 'SingletonLockSymlink', 'LOCK'];
    let cleaned = 0;
    for (const name of lockFiles) {
      const p = path.join(userData, name);
      try {
        if (fs.existsSync(p)) {
          fs.unlinkSync(p);
          cleaned++;
        }
      } catch (e) {
        // 静默处理：文件可能被占用或权限不足
      }
    }
    if (cleaned > 0) {
      console.log(`[Main] 已清理 ${cleaned} 个残留 SingletonLock 文件: ${userData}`);
    }
    return cleaned;
  } catch (e) {
    console.warn('[Main] 清理 SingletonLock 失败:', e.message);
    return 0;
  }
}

// 单实例锁定：确保只有一个应用实例运行
// 先清理可能的残留锁文件，避免上次崩溃后无法启动
cleanupSingletonLockFiles();

let gotTheLock = app.requestSingleInstanceLock();
mainLogger.logEvent('SINGLE-INSTANCE-LOCK', { gotTheLock, pid: process.pid });

if (!gotTheLock) {
  // 首次获取失败，可能存在残留锁或锁竞争，重试一次
  console.log('[WARN] 首次 requestSingleInstanceLock 失败，清理残留锁后重试...');
  cleanupSingletonLockFiles();
  // 【修复】使用 setImmediate + setTimeout 代替 busy-wait，不占用 CPU
  // 顶层代码不能使用 await（CommonJS 不支持顶层 await）
  const retryAcquire = () => {
    gotTheLock = app.requestSingleInstanceLock();
    mainLogger.logEvent('SINGLE-INSTANCE-LOCK-RETRY', { gotTheLock });
    if (!gotTheLock) {
      console.log('[INFO] 另一个实例已在运行，退出');
      // 【P0】此路径会让“后启动的实例”静默退出，必须留痕
      markQuit('single-instance-lock-failed');
      app.quit();
      return;
    }
    console.log('[INFO] 二次重试获取单实例锁成功');
  };
  setTimeout(retryAcquire, 300);
}

// 处理第二个实例启动时传递的文件参数
app.on('second-instance', (event, commandLine) => {
    console.log('[INFO] second-instance 事件:', commandLine);
    mainLogger.logEvent('SECOND-INSTANCE', { commandLine });
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();

      // 从命令行参数提取关联文件
      const filePath = commandLine.find((arg) => {
        if (!arg || typeof arg !== 'string') return false;
        const fileName = path.basename(arg);
        return isValidFileName(fileName);
      });

      if (filePath && fs.existsSync(filePath)) {
        console.log('[INFO] second-instance 打开文件:', filePath);
        const result = safeReadFile(filePath);
        if (result.success && mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('app-event', {
            type: 'open-file',
            filePath,
            content: result.content,
            fileType: result.fileType,
          });
        }
      }
    }
  });

app.whenReady().then(async () => {
  // 【P0-静默退出】会话启动信息 + 心跳：
  //   - SESSION-START 记录版本/参数/日志路径，定位“哪次运行”
  //   - 每 5 分钟写 HEARTBEAT（uptime + 内存），日志突然中断即为进程被杀的强证据
  mainLogger.logSessionStart();
  const heartbeatTimer = setInterval(() => {
    try {
      const mem = process.memoryUsage();
      mainLogger.logEvent('HEARTBEAT', {
        uptimeSec: Math.round(process.uptime()),
        rssMB: +(mem.rss / 1048576).toFixed(1),
        heapUsedMB: +(mem.heapUsed / 1048576).toFixed(1),
        quitReason,
        windows: BrowserWindow.getAllWindows().length,
        tray: !!appInitializer?.tray,
      });
    } catch (_) { /* 心跳失败不影响主流程 */ }
  }, 5 * 60 * 1000);
  if (typeof heartbeatTimer.unref === 'function') heartbeatTimer.unref();

  // 【无边框窗口 P3】移除 Electron 默认菜单（File/Edit/View/Window/Help）
  // 自定义标题栏已接管窗口控制；菜单移除后 F11 全屏改由 before-input-event 兜底
  try {
    Menu.setApplicationMenu(null);
    mainLogger.logEvent('MENU-CLEARED', {});
    console.log('[Main] 已移除应用默认菜单（无边框模式）');
  } catch (err) {
    console.warn('[Main] 移除默认菜单失败（非阻塞）:', err && err.message);
  }

  // 【P2-5】electron-updater 接入骨架：feedURL 未配置时静默跳过，不阻塞启动。
  // 后续配置好 update.electronjs.org / 自有服务器签名后，把 FEED_URL 填上即可启用自动更新。
  try {
    const { autoUpdater } = require('electron-updater');
    const FEED_URL = process.env.IMATO_UPDATE_FEED_URL || '';
    autoUpdater.autoDownload = false;
    autoUpdater.autoInstallOnAppQuit = true;
    if (FEED_URL) {
      autoUpdater.setFeedURL({ provider: 'generic', url: FEED_URL });
      autoUpdater.on('update-available', (info) => {
        console.log('[Updater] update available:', info && info.version);
      });
      autoUpdater.on('update-downloaded', (info) => {
        console.log('[Updater] update downloaded:', info && info.version);
      });
      autoUpdater.on('error', (err) => {
        console.warn('[Updater] error (non-blocking):', err && err.message);
      });
      autoUpdater.checkForUpdatesAndNotify().catch((e) => {
        console.warn('[Updater] check failed (non-blocking):', e && e.message);
      });
    } else {
      console.log('[Updater] FEED_URL not configured, skipping auto-update check.');
    }
  } catch (e) {
    console.warn('[Updater] electron-updater not available (non-blocking):', e && e.message);
  }
  // 0. 注册 splash 关键 IPC handler（必须在 createSplashWindow 之前注册,
  //   否则 initialize() 阻塞期间用户点击"跳过"会因无人监听被丢弃）
  ipcMain.on('splash-quit', () => {
    console.log('[Main] User requested quit from splash');
    markQuit('user-splash-quit');
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy();
    }
    app.quit();
  });

  // 【启动优化 P3】主窗口主动退出应用：用于 fast mode 登录失败后引导用户重启
  // 与 splash-quit 区别：splash 阶段 splashWindow 还在；主窗口阶段只有 mainWindow
  // 走标准 quit 流程（before-quit 事件 + 资源清理 + 进程退出）
  ipcMain.on('app-quit', () => {
    console.log('[Main] User requested quit from main window (fast mode recovery)');
    isQuitting = true;
    markQuit('user-app-quit');
    app.quit();
  });

  ipcMain.on('splash-skip', () => {
    console.log('[Main] User requested skip from splash → degraded mode');
    global.__matuxUserSkippedStartup = true;
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy();
      splashWindow = null;
    }
    const win = windowManager?.getMainWindow?.();
    if (win && !win.isDestroyed() && !win.isVisible()) {
      win.show();
    }
  });

  // 【启动优化 P3】学习优先模式：用户点"快速进入"或本地偏好自动应用
  // 复用 splash-skip 的全局标志位(__matuxUserSkippedStartup=true)让 appInitializer 立即走降级分支
  // 同时新增 __matuxFastMode 供前端 StartupModeService 区分"主动跳过"与"学习优先模式"
  ipcMain.on('splash-fast-mode', () => {
    console.log('[Main] User requested fast mode → enter immediately, backend in background');
    global.__matuxFastMode = true;
    global.__matuxUserSkippedStartup = true;
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.destroy();
      splashWindow = null;
    }
    const win = windowManager?.getMainWindow?.();
    if (win && !win.isDestroyed() && !win.isVisible()) {
      win.show();
    }
  });

  // 【启动优化 P3】前端查询启动模式（fast mode / degraded）
  // StartupModeService 在主窗口 ready-to-show 后首次调用
  ipcMain.handle('startup:get-mode', () => {
    return {
      fastMode: global.__matuxFastMode === true,
      degraded: global.__matuxUserSkippedStartup === true,
    };
  });

  // 【复用模式修复】Splash 上的“强制重启”按钮：异步执行 forceRestart（用户已点 Splash 上的弹窗按钮 = 确认）
  ipcMain.on('splash-force-restart', async () => {
    console.log('[Main] User confirmed force-restart from splash');
    if (!appInitializer?.backendManager) {
      console.error('[ERROR] appInitializer/backendManager 未就绪，无法执行 forceRestart');
      return;
    }
    try {
      // splash 点击 = 用户已确认，传入 skipUserConfirmation: true
      const ok = await appInitializer.backendManager.forceRestart(null, { skipUserConfirmation: true });
      console.log(`[Main] forceRestart 结果: ${ok ? '成功' : '失败'}`);
    } catch (err) {
      console.error('[ERROR] splash-force-restart 执行异常:', err.message);
    }
  });

  // 1. 注册自定义协议 handler（必须在创建窗口之前）
  registerAppProtocol();

  // 1. 创建应用启动器（必须在 registerIpcHandlers 之前）
  // 【修复 #2】之前顺序错误：registerIpcHandlers() 调用时 appInitializer 为 null，
  //    导致 backendHandlers 拿到的 backendManager 为 undefined，启动后所有 IPC 调用 TypeError
  appInitializer = new AppInitializer({
    sendSplashStatus,
    appState,
    windowManager,
    showTrayNotification,
  });

  // 2. 注册 IPC（此时 appInitializer 已存在）
  registerIpcHandlers();

  // 3. 创建 Splash（全屏科技感打字机动画）
  // 【启动优化 P3-8】不再硬等 SPLASH_RENDER_DELAY（200ms）——
  //   Splash 窗口内部的 ready-to-show 事件会负责 show() ，
  //   与主窗口创建完全独立，可并行进行。
  createSplashWindow();
  if (SPLASH_RENDER_DELAY > 0) {
    await new Promise((r) => setTimeout(r, SPLASH_RENDER_DELAY));
  }

  // 4. 创建主窗口（立即开始加载前端，不等待后端）
  //    mainWindow 的 ready-to-show 处理器会显示主窗口并通知 Splash 进入迷你模式
  createMainWindow(windowManager);

  // 5. 启动后端（后端初始化在后台进行，不阻塞主窗口显示）
  //    - 前端加载与后端启动并行执行
  //    - Splash 会在主窗口 ready-to-show 时自动变形为底部横条
  // 【跳过入口】如果用户在 splash 上点了"跳过"，把 await 转成"等标志"的 race,
  //   这样 initResult 会立刻得到 'degraded',主窗口立即显示。
  let initResult;
  if (global.__matuxUserSkippedStartup) {
    if (global.__matuxFastMode) {
      // 【启动优化 P3】学习优先模式：跳过同步等待，但保留后端后台启动
      // 行为：splash 立即关闭 + 主窗口立即显示 + 后端在后台异步启动
      // 与"主动跳过"区分：__matuxFastMode = true 时不放弃后端
      console.log('[Main] 检测到学习优先模式,主窗口立即显示,后端后台启动');
      initResult = 'fast-mode';
      // 启动后端但不 await（fire-and-forget），失败仅记日志
      appInitializer.initialize().then((result) => {
        console.log(`[Main] 后台后端启动完成: ${result}`);
        if (mainWindow && !mainWindow.isDestroyed()) {
          if (result === false) {
            mainWindow.webContents.send('app-event', { type: 'backend-degraded', reason: 'Fast mode 后台启动失败' });
          } else {
            mainWindow.webContents.send('app-event', { type: 'backend-ready' });
          }
        }
      }).catch((err) => {
        console.error('[Main] 学习优先模式后台启动后端失败:', err.message);
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('app-event', { type: 'backend-degraded', reason: err.message });
        }
      });
    } else {
      console.log('[Main] 检测到用户跳过启动,直接走降级模式');
      initResult = 'degraded';
    }
  } else {
    initResult = await appInitializer.initialize();
  }

  if (initResult === false) {
    console.error('[Main] 后端启动失败，进入降级模式继续运行');
    isStarting = false;
    // 【修复 P0】之前这里直接 return，导致 splash 永不关闭、主窗口不显示，
    // 用户即便点了"跳过"也没机会进入降级模式。
    // 现在即使后端启动失败，也强制走降级模式：
    //   - 显示主窗口（带降级横幅）
    //   - 通知前端 backend-degraded
    initResult = 'degraded';
    if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isVisible()) {
      mainWindow.show();
    }
  }

  const isDegraded = (initResult === 'degraded' || initResult === 'fast-mode');
  const isFastMode = (initResult === 'fast-mode');

  if (isFastMode) {
    console.log('[Main] 学习优先模式：主窗口已显示，后端在后台启动中');
  } else if (isDegraded) {
    console.log('[Main] 降级模式运行中（无 Python 后端），跳过后端启动步骤');
  }

  // 6. 后端就绪 / 降级模式 → 通知 Splash 淡出并关闭
  if (isFastMode) {
    // 【启动优化 P3】学习优先模式：通知前端进入 fast mode + 后端后台启动
    sendSplashStatus('fast-mode', '学习优先模式已启用', 100, '本地内容立即可用，后端在后台启动');
  } else if (isDegraded) {
    // 降级模式：不传 fadeOut，由 splash.html 的 degraded-mode case 自行控制淡出时机
    sendSplashStatus('degraded-mode', '前端模式运行中（无后端）', 100, 'Python 后端不可用，部分功能受限');
  } else {
    sendSplashStatus('app-ready', 'MatuX is ready!', 100, null, null, { fadeOut: true });
  }
  // 【启动优化 P1-2】不再硬等 900ms，监听 splash-fadeout-complete 事件
  // - 正常路径：Splash CSS transition (0.6s) 结束后通知 → 立即关闭（节省 300ms）
  // - 兑底路径：800ms 超时（防止 transitionend 不触发） → 避免主进程永久等待
  let fadeOutClosed = false;
  const closeSplash = () => {
    if (fadeOutClosed) return;
    fadeOutClosed = true;
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
  };
  ipcMain.once('splash-fadeout-complete', closeSplash);
  // 兑底超时：降级模式需等待更久（splash 内部延迟 1.5s + CSS transition 0.6s）
  setTimeout(closeSplash, isDegraded ? 3000 : 800);

  // splash-quit / splash-skip handler 已在 app.whenReady() 顶部注册,
  // 这样 initialize() 阻塞期间用户点击也能被及时处理

  // 7. 通知前端后端状态
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (isFastMode) {
      // 【启动优化 P3】学习优先模式：发 fast-mode 事件（不标记 degraded，让前端显示"加载中"横幅）
      mainWindow.webContents.send('app-event', {
        type: 'fast-mode-active',
        message: '学习优先模式：本地内容立即可用，后端在后台启动',
      });
    } else if (isDegraded) {
      mainWindow.webContents.send('app-event', {
        type: 'backend-degraded',
        reason: 'Python backend unavailable',
      });
    } else {
      mainWindow.webContents.send('app-event', { type: 'backend-ready' });
    }
  }

  // 8. 注册快捷键
  registerGlobalShortcuts({
    mainWindow,
    onRestartBackend: () => appInitializer?._restartBackend(),
    onShowNotification: showTrayNotification,
  });

  // 9. 创建托盘
  appInitializer.createTray();

  // 10. 设置文件关联
  setupFileAssociation();

  // 11. 预加载 Tier 1 模块
  preloadTier1Modules();

  // 12. 通知主窗口就绪
  app.emit('main-window-ready');

  // 13. 延迟检查更新
  setTimeout(() => {
    if (!appInitializer.updatesCheckScheduled) {
      appInitializer.updatesCheckScheduled = true;
      checkForUpdates({ mainWindow, showNotification: showTrayNotification }).catch((err) => {
        console.warn('[WARN] 更新检查失败:', err.message);
      });
    }
  }, 30000);

  isStarting = false;
});

// macOS 特殊处理
app.on('window-all-closed', () => {
  // 【P0-静默退出】全部窗口关闭是“静默退出”的三大路径之一，必须留痕
  mainLogger.logEvent('WINDOW-ALL-CLOSED', {
    platform: process.platform,
    isQuitting,
    tray: !!appInitializer?.tray,
    quitReason,
  });
  if (process.platform !== 'darwin') {
    markQuit('window-all-closed');
    appInitializer?.gracefulShutdown();
    app.quit();
  }
});

app.on('activate', () => {
  mainLogger.logEvent('APP-ACTIVATE', { windows: BrowserWindow.getAllWindows().length });
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow(windowManager);
  }
});

app.on('before-quit', () => {
  mainLogger.logEvent('BEFORE-QUIT', { quitReason, uptimeSec: Math.round(process.uptime()) });
  isQuitting = true;
  appInitializer?.gracefulShutdown();
});

app.on('will-quit', () => {
  mainLogger.logEvent('WILL-QUIT', {
    quitReason,
    uptimeSec: Math.round(process.uptime()),
  });
});

// 【P0-静默退出】子进程（GPU / Utility / Renderer）消失留痕
app.on('child-process-gone', (event, details) => {
  mainLogger.logEvent('CHILD-PROCESS-GONE', details);
});

// 【P0-静默退出】进程级兜底：无论哪条路径退出，同步写入最后一笔，
// 保证日志末尾总能看到退出码与退出原因。
process.on('exit', (code) => {
  mainLogger.logEvent('PROCESS-EXIT', {
    code,
    quitReason,
    uptimeSec: Math.round(process.uptime()),
  });
});

// 【P0-静默退出】未捕获异常：记录 + 提示 + 继续运行（不再 process.exit）。
// 原实现 3 秒后 process.exit(1) 且无任何 UI 反馈，是“静默退出”的头号疑似来源。
process.on('uncaughtException', (error) => {
  console.error('[FATAL] 未捕获的异常:', error);
  const reportFile = mainLogger.writeCrashReport('uncaughtException', error, {
    quitReason,
    isQuitting,
  });

  // 尝试通知 Splash/UI
  if (typeof sendSplashStatus === 'function' && splashWindow && !splashWindow.isDestroyed()) {
    sendSplashStatus('backend-error', `应用错误: ${error.message}`, 0);
  }

  // 尝试保存应用状态
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
    console.log('[Main] 状态已保存');
  } catch (saveError) {
    console.error('[Main] 保存状态失败:', saveError);
  }

  // 告知用户（非阻塞弹窗），避免应用“看着无响应/像消失”
  notifyMainProcessProblem(
    '应用捕获到未处理异常（已继续运行）',
    `${error.message}${reportFile ? `\n崩溃报告: ${reportFile}` : ''}`
  );
});

// 捕获未处理的 Promise 拒绝
// 【修复 #3】不再粗暴退出：业界实践是记录并继续运行
// 原因：多数 rejection 是非致命的（网络超时、第三方库内部错误等）
//       粗暴退出会导致偶发错误使得整个应用崩溃
// 策略：1. 记录详细日志 2. 通知主进程记录 3. 弹窗提示用户（可选） 4. 仅在严重错误时退出
process.on('unhandledRejection', (reason, promise) => {
  const errorMessage = reason?.message || String(reason);
  const errorStack = reason?.stack || '';

  console.error('[FATAL] 未处理的 Promise 拒绝:');
  console.error('  原因:', errorMessage);
  if (errorStack) console.error('  堆栈:', errorStack);

  // 1. 记录到状态（供问题追踪）
  try {
    if (appState && typeof appState.setState === 'function') {
      appState.setState({
        lastUnhandledRejection: {
          message: errorMessage,
          stack: errorStack,
          timestamp: new Date().toISOString(),
        },
      });
    }
  } catch (e) {
    console.error('[Main] 记录状态失败:', e);
  }

  // 2. 通知渲染进程（如果主窗口存在）
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      const wc = mainWindow.webContents;
      if (!wc.isCrashed() && !wc.isDestroyed()) {
        wc.send('app-event', {
          type: 'unhandled-rejection',
          message: errorMessage,
          timestamp: new Date().toISOString(),
          // 仅在开发模式传递完整堆栈
          stack: isDev ? errorStack : undefined,
        });
      }
    }
  } catch (sendError) {
    console.error('[Main] 发送 IPC 通知失败:', sendError);
  }

  // 3. 尝试保存状态
  try {
    if (mainWindow && !mainWindow.isDestroyed()) {
      saveWindowState(mainWindow);
    }
  } catch (saveError) {
    console.error('[Main] 保存状态失败:', saveError);
  }

  // 4. 严重错误检测：仅用于日志分级；【P0 修复】不再因 rejection 退出进程。
  //    原实现遇到 EACCES/ENOSPC/FATAL 等字样会 process.exit(1)，且退出前无 UI 提示，
  //    属于“静默退出”的另一来源。
  const isCritical = reason instanceof Error &&
    (errorMessage.includes('EACCES') ||    // 权限错误
     errorMessage.includes('ENOSPC') ||    // 磁盘空间不足
     errorMessage.includes('ERR_WORKER') || // Worker 线程崩溃
     errorMessage.includes('FATAL'));       // 标记为 FATAL

  if (isCritical) {
    mainLogger.writeCrashReport('unhandledRejection-critical', reason, { quitReason });
    console.error('[Main] 检测到严重 rejection，已记录崩溃报告，应用继续运行');
    notifyMainProcessProblem('检测到严重异步异常（已继续运行）', errorMessage);
  } else {
    console.warn('[Main] 非严重 rejection，应用继续运行');
  }
});

// ==================== 导出（用于测试） ====================
module.exports = {
  backendCore,
  createSplashWindow,
  createMainWindow,
  healthCheck: healthCheckWrapper,
  gracefulShutdown: () => appInitializer?.gracefulShutdown(),
  detectPython,
  createChildWindow,
  restartBackend: () => appInitializer?._restartBackend(),
  updateTrayStatus: () => appInitializer?._updateTrayStatus(),
};
