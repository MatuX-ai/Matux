/**
 * Electron 预加载脚本
 *
 * 在渲染进程和主进程之间建立安全桥接
 */
const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // ==================== 后端通信 ====================

  /**
   * 获取后端服务 URL
   */
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

  /**
   * 执行健康检查
   */
  healthCheck: () => ipcRenderer.invoke('health-check'),

  /**
   * 获取应用信息
   */
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // ==================== 文件系统操作 ====================

  /**
   * 读取文件内容
   */
  readFile: (filePath) => ipcRenderer.invoke('fs-read-file', filePath),

  /**
   * 写入文件内容（文本或二进制数据）
   */
  writeFile: (filePath, content) => ipcRenderer.invoke('fs-write-file', filePath, content),

  /**
   * 打开保存文件对话框
   * @param opts 可选的对话框选项（文件过滤器等）
   */
  showSaveDialog: (opts) => ipcRenderer.invoke('fs-save-dialog', opts),

  /**
   * 打开文件对话框
   */
  showOpenDialog: () => ipcRenderer.invoke('fs-open-dialog'),

  /**
   * 列出目录内容
   * @param dirPath 目录路径
   * @returns {{ success: boolean, files?: Array, error?: string }}
   */
  listDirectory: (dirPath) => ipcRenderer.invoke('fs-list-dir', dirPath),

  /**
   * 创建目录（递归）
   * @param dirPath 目录路径
   */
  makeDirectory: (dirPath) => ipcRenderer.invoke('fs-make-dir', dirPath),

  /**
   * 删除文件或空目录
   * @param targetPath 文件或目录路径
   */
  deleteFile: (targetPath) => ipcRenderer.invoke('fs-delete-file', targetPath),

  /**
   * 检查文件或目录是否存在
   * @param targetPath 目标路径
   */
  fileExists: (targetPath) => ipcRenderer.invoke('fs-file-exists', targetPath),

  /**
   * 获取文件信息（大小、修改时间等）
   * @param filePath 文件路径
   */
  getFileInfo: (filePath) => ipcRenderer.invoke('fs-get-file-info', filePath),

  /**
   * 选择文件夹对话框
   */
  selectDirectory: () => ipcRenderer.invoke('fs-select-directory'),

  /**
   * 打开外部链接（系统默认浏览器）
   */
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // ==================== 原生功能 ====================

  /**
   * 发送原生系统通知
   */
  showNotification: (title, body, category) =>
    ipcRenderer.invoke('show-notification', title, body, category),

  /**
   * 检查应用更新
   */
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),

  // ==================== 模块状态管理 ====================

  /**
   * 获取模块状态（缓存）
   */
  getModuleStatus: () => ipcRenderer.invoke('backend:module-status'),

  /**
   * 请求激活指定模块
   * @param {string} moduleName 模块名称
   */
  activateModule: (moduleName) => ipcRenderer.invoke('backend:activate-module', moduleName),

  /**
   * 重启后端服务
   */
  restartBackend: () => ipcRenderer.invoke('backend:restart'),

  // ==================== 窗口控制 ====================

  /**
   * 窗口操作
   */
  windowControl: (action) => {
    ipcRenderer.send('app-event', { type: action });
  },

  /**
   * 获取当前窗口尺寸
   */
  getWindowSize: () => ipcRenderer.invoke('get-window-size'),

  // ==================== 事件通信 ====================

  /**
   * 发送消息到主进程
   */
  send: (channel, data) => {
    const validChannels = ['to-backend', 'app-event'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  },

  /**
   * 监听事件（支持自定义回调）
   */
  on: (channel, func) => {
    const validChannels = ['app-event', 'from-backend', 'window-blur', 'window-focus',
      'fullscreen-enter', 'fullscreen-leave', 'window-resize', 'open-file',
      'update-available', 'backend-disconnected', 'backend-reconnected',
      'backend:module-status', 'backend-status-change'];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => func(...args));
    }
  },

  /**
   * 从主进程接收消息（兼容旧 API）
   */
  receive: (channel, func) => {
    const validChannels = ['from-backend', 'app-event'];
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => func(...args));
    }
  },

  /**
   * 移除消息监听
   */
  removeListener: (channel, func) => {
    ipcRenderer.removeListener(channel, func);
  },

  /**
   * 移除所有消息监听
   */
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  },

  // ==================== 窗口控制（frame:false 自定义标题栏） ====================
  minimizeWindow: () => ipcRenderer.invoke('window-minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window-maximize'),
  closeWindow: () => ipcRenderer.invoke('window-close'),
  isWindowMaximized: () => ipcRenderer.invoke('window-is-maximized'),

  /** 监听最大化状态变化 */
  onMaximizeChange: (callback) => {
    ipcRenderer.on('app-event', (_event, data) => {
      if (data.type === 'window-resize') callback(data);
    });
  },

  /** 监听快捷键事件 */
  onShortcut: (callback) => {
    ipcRenderer.on('shortcut', (_event, action) => callback(action));
  },
});

// ==================== 插件管理 API（插件化架构 Phase 1） ====================

contextBridge.exposeInMainWorld('pluginAPI', {
  // ==================== 设备评估 ====================

  /**
   * 获取设备评估报告
   * @returns {Promise<{success: boolean, profile?: object, error?: string}>}
   */
  getDeviceProfile: () => ipcRenderer.invoke('plugin:device-profile'),

  /**
   * 重新评估设备能力
   * @returns {Promise<{success: boolean, profile?: object, error?: string}>}
   */
  reassessDevice: () => ipcRenderer.invoke('plugin:reassess-device'),

  /**
   * 评估指定插件与当前设备的兼容性
   * @param {string} pluginId 插件 ID
   */
  assessPlugin: (pluginId) => ipcRenderer.invoke('plugin:assess', pluginId),

  // ==================== 插件商店（Phase 2 实现） ====================

  /**
   * 获取可用插件列表
   */
  getPluginCatalog: () => ipcRenderer.invoke('plugin:catalog'),

  /**
   * 获取推荐套餐
   */
  getRecommendedBundles: () => ipcRenderer.invoke('plugin:recommended-bundles'),

  /**
   * 搜索插件
   * @param {string} query 搜索关键词
   */
  searchPlugins: (query) => ipcRenderer.invoke('plugin:search', query),

  // ==================== 插件管理（Phase 2 实现） ====================

  /**
   * 安装插件
   * @param {string} pluginId 插件 ID
   * @param {string} version 版本号
   */
  installPlugin: (pluginId, version) =>
    ipcRenderer.invoke('plugin:install', pluginId, version),

  /**
   * 卸载插件
   * @param {string} pluginId 插件 ID
   * @param {boolean} keepData 是否保留用户数据
   */
  uninstallPlugin: (pluginId, keepData) =>
    ipcRenderer.invoke('plugin:uninstall', pluginId, keepData),

  /**
   * 更新插件
   * @param {string} pluginId 插件 ID
   */
  updatePlugin: (pluginId) => ipcRenderer.invoke('plugin:update', pluginId),

  /**
   * 获取已安装插件列表
   */
  getInstalledPlugins: () => ipcRenderer.invoke('plugin:installed'),

  /**
   * 启用/禁用插件
   * @param {string} pluginId 插件 ID
   * @param {boolean} enabled 是否启用
   */
  togglePlugin: (pluginId, enabled) =>
    ipcRenderer.invoke('plugin:toggle', pluginId, enabled),

  // ==================== 事件监听 ====================

  /**
   * 监听插件安装进度
   * @param {Function} callback ({pluginId, phase, progress, message})
   */
  onInstallProgress: (callback) =>
    ipcRenderer.on('plugin:install-progress', (_, data) => callback(data)),

  /**
   * 监听插件状态变化
   * @param {Function} callback ({type, pluginId, ...})
   */
  onPluginStatusChange: (callback) =>
    ipcRenderer.on('plugin:status-change', (_, data) => callback(data)),

  /**
   * 监听可用更新
   * @param {Function} callback ({updates: [{pluginId, fromVersion, toVersion}]})
   */
  onUpdatesAvailable: (callback) =>
    ipcRenderer.on('plugin:updates-available', (_, data) => callback(data)),

  // ==================== Phase 5: 推荐引擎 ====================

  /**
   * 获取个性化推荐
   * @param {object} options { maxRecommendations, includeBundles, excludeInstalled }
   */
  getRecommendations: (options = {}) =>
    ipcRenderer.invoke('plugin:recommendations', options),

  /**
   * 记录插件使用事件
   * @param {string} pluginId 插件 ID
   * @param {string} eventType 事件类型
   * @param {number} duration 持续时间（秒）
   * @param {object} features 功能使用统计
   */
  recordPluginUsage: (pluginId, eventType, duration = 0, features = {}) =>
    ipcRenderer.invoke('plugin:record-usage', pluginId, eventType, duration, features),

  /**
   * 设置插件评分
   * @param {string} pluginId 插件 ID
   * @param {number} rating 评分 (1-5)
   * @param {string} feedback 反馈文本
   */
  setPluginRating: (pluginId, rating, feedback = '') =>
    ipcRenderer.invoke('plugin:set-rating', pluginId, rating, feedback),

  /**
   * 获取热门插件
   * @param {number} limit 返回数量
   */
  getPopularPlugins: (limit = 10) =>
    ipcRenderer.invoke('plugin:popular', limit),

  /**
   * 获取插件详情（含评分和统计）
   * @param {string} pluginId 插件 ID
   */
  getPluginDetails: (pluginId) =>
    ipcRenderer.invoke('plugin:details', pluginId),

  // ==================== Phase 5: 安装包精简 ====================

  /**
   * 获取首次运行引导步骤
   */
  getFirstRunGuide: () =>
    ipcRenderer.invoke('plugin:first-run-guide'),

  /**
   * 检查是否已完成首次运行
   */
  isFirstRunCompleted: () =>
    ipcRenderer.invoke('plugin:first-run-check'),

  /**
   * 标记首次运行完成
   */
  markFirstRunCompleted: () =>
    ipcRenderer.invoke('plugin:first-run-complete'),

  /**
   * 获取核心模块列表
   */
  getCoreModules: () =>
    ipcRenderer.invoke('plugin:core-modules'),

  /**
   * 获取可选模块列表
   * @param {string} deviceClass 设备等级
   */
  getOptionalModules: (deviceClass = null) =>
    ipcRenderer.invoke('plugin:optional-modules', deviceClass),

  /**
   * 获取推荐模块
   * @param {string} deviceClass 设备等级
   */
  getRecommendedModules: (deviceClass) =>
    ipcRenderer.invoke('plugin:recommended-modules', deviceClass),

  /**
   * 获取安装统计
   */
  getInstallStats: () =>
    ipcRenderer.invoke('plugin:install-stats'),

  /**
   * 添加已安装模块
   * @param {string} moduleId 模块 ID
   */
  addInstalledModule: (moduleId) =>
    ipcRenderer.invoke('plugin:installed-module', moduleId),

  /**
   * 跳过模块安装
   * @param {string} moduleId 模块 ID
   */
  skipModule: (moduleId) =>
    ipcRenderer.invoke('plugin:skip-module', moduleId),

  // ==================== Phase 5: 插件商店增强 ====================

  /**
   * 添加插件评论
   * @param {object} reviewData { pluginId, rating, title, content, pros, cons }
   */
  addPluginReview: (reviewData) =>
    ipcRenderer.invoke('plugin:add-review', reviewData),

  /**
   * 获取插件评论
   * @param {string} pluginId 插件 ID
   * @param {object} options { sortBy, sortOrder, limit, offset, minRating }
   */
  getPluginReviews: (pluginId, options = {}) =>
    ipcRenderer.invoke('plugin:get-reviews', pluginId, options),

  /**
   * 获取插件平均评分
   * @param {string} pluginId 插件 ID
   */
  getPluginAverageRating: (pluginId) =>
    ipcRenderer.invoke('plugin:average-rating', pluginId),

  /**
   * 标记评论为有帮助
   * @param {string} reviewId 评论 ID
   * @param {string} pluginId 插件 ID
   */
  markReviewHelpful: (reviewId, pluginId) =>
    ipcRenderer.invoke('plugin:mark-helpful', reviewId, pluginId),

  /**
   * 检查插件更新
   * @param {array} installedPlugins 已安装插件列表
   */
  checkForUpdates: (installedPlugins) =>
    ipcRenderer.invoke('plugin:check-updates', installedPlugins),

  /**
   * 获取待处理更新通知
   */
  getPendingNotifications: () =>
    ipcRenderer.invoke('plugin:pending-notifications'),

  /**
   * 关闭更新通知
   * @param {string} notificationId 通知 ID
   */
  dismissNotification: (notificationId) =>
    ipcRenderer.invoke('plugin:dismiss-notification', notificationId),

  /**
   * 标记通知已安装
   * @param {string} notificationId 通知 ID
   */
  markNotificationInstalled: (notificationId) =>
    ipcRenderer.invoke('plugin:mark-installed', notificationId),

  /**
   * 获取插件使用统计
   * @param {string} pluginId 插件 ID
   */
  getPluginUsageStats: (pluginId) =>
    ipcRenderer.invoke('plugin:usage-stats', pluginId),

  /**
   * 获取商店统计
   */
  getStoreStats: () =>
    ipcRenderer.invoke('plugin:store-stats'),
});

console.log('[Preload] Electron 预加载脚本已加载（含 pluginAPI）');
