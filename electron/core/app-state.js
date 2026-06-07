/**
 * MatuX Electron 应用状态管理
 * 
 * 统一管理应用生命周期中的各种状态
 */

const EventEmitter = require('events');

class AppState extends EventEmitter {
  constructor() {
    super();
    
    // Python 环境信息
    this.pythonInfo = null;
    
    // 插件管理器实例
    this.pluginInstaller = null;
    this.pluginDownloader = null;
    this.pluginRegistry = null;
    
    // Phase 5 推荐引擎
    this.pluginRecommender = null;
    this.installConfigManager = null;
    this.pluginStoreEnhancer = null;
    
    // 设备评估
    this.deviceProfiler = null;
    
    // 生命周期状态
    this._isQuitting = false;
    this._isStarting = false;
    this._restartAttempts = 0;
    
    // 模块状态缓存
    this.moduleStatusCache = null;
    this.backendOverallStatus = 'unknown';
    
    // 窗口状态
    this.mainWindow = null;
    this.tray = null;
    this.splashWindow = null;
  }

  // ==================== 生命周期状态 ====================

  get isQuitting() {
    return this._isQuitting;
  }

  set isQuitting(value) {
    this._isQuitting = value;
    this.emit('lifecycle:change', { type: 'quitting', value });
  }

  get isStarting() {
    return this._isStarting;
  }

  set isStarting(value) {
    this._isStarting = value;
    this.emit('lifecycle:change', { type: 'starting', value });
  }

  get restartAttempts() {
    return this._restartAttempts;
  }

  set restartAttempts(value) {
    this._restartAttempts = value;
    this.emit('lifecycle:change', { type: 'restartAttempts', value });
  }

  incrementRestartAttempts() {
    this._restartAttempts++;
    this.emit('lifecycle:change', { type: 'restartAttempts', value: this._restartAttempts });
  }

  resetRestartAttempts() {
    this._restartAttempts = 0;
    this.emit('lifecycle:change', { type: 'restartAttempts', value: 0 });
  }

  // ==================== 后端状态 ====================

  get backendStatus() {
    return this.backendOverallStatus;
  }

  setBackendStatus(status) {
    const previous = this.backendOverallStatus;
    this.backendOverallStatus = status;
    this.emit('backend:statusChange', { current: status, previous });
  }

  setModuleStatus(modules) {
    this.moduleStatusCache = modules;
    this.emit('backend:moduleStatus', modules);
  }

  // ==================== 窗口管理 ====================

  setMainWindow(window) {
    this.mainWindow = window;
    this.emit('window:mainChanged', window);
  }

  getMainWindow() {
    return this.mainWindow;
  }

  setTray(tray) {
    this.tray = tray;
    this.emit('window:trayChanged', tray);
  }

  getTray() {
    return this.tray;
  }

  setSplashWindow(window) {
    this.splashWindow = window;
  }

  getSplashWindow() {
    return this.splashWindow;
  }

  // ==================== 插件状态 ====================

  setPluginInstaller(installer) {
    this.pluginInstaller = installer;
  }

  getPluginInstaller() {
    return this.pluginInstaller;
  }

  setPluginDownloader(downloader) {
    this.pluginDownloader = downloader;
  }

  getPluginDownloader() {
    return this.pluginDownloader;
  }

  setPluginRegistry(registry) {
    this.pluginRegistry = registry;
  }

  getPluginRegistry() {
    return this.pluginRegistry;
  }

  // ==================== Phase 5 状态 ====================

  setPluginRecommender(recommender) {
    this.pluginRecommender = recommender;
  }

  getPluginRecommender() {
    return this.pluginRecommender;
  }

  setInstallConfigManager(manager) {
    this.installConfigManager = manager;
  }

  getInstallConfigManager() {
    return this.installConfigManager;
  }

  setPluginStoreEnhancer(enhancer) {
    this.pluginStoreEnhancer = enhancer;
  }

  getPluginStoreEnhancer() {
    return this.pluginStoreEnhancer;
  }

  // ==================== 设备评估状态 ====================

  setDeviceProfiler(profiler) {
    this.deviceProfiler = profiler;
  }

  getDeviceProfiler() {
    return this.deviceProfiler;
  }

  // ==================== 导出/导入状态 ====================

  // ==================== 状态导出 ====================

  /**
   * 获取模块状态（兼容 IPC handler）
   */
  getModuleStatus() {
    return this.moduleStatusCache;
  }

  /**
   * 导出完整状态（用于持久化）
   */
  export() {
    return {
      pythonInfo: this.pythonInfo,
      backendStatus: this.backendOverallStatus,
      moduleStatus: this.moduleStatusCache,
      restartAttempts: this._restartAttempts,
    };
  }

  /**
   * 重置所有状态
   */
  reset() {
    this.pythonInfo = null;
    this._isQuitting = false;
    this._isStarting = false;
    this._restartAttempts = 0;
    this.moduleStatusCache = null;
    this.backendOverallStatus = 'unknown';
    this.mainWindow = null;
    this.tray = null;
    this.splashWindow = null;
    
    this.emit('state:reset');
  }

  /**
   * 批量设置状态
   */
  setState(partial) {
    Object.assign(this, partial);
    this.emit('state:change', partial);
  }
}

// 单例模式
let instance = null;

AppState.getInstance = function() {
  if (!instance) {
    instance = new AppState();
  }
  return instance;
};

AppState.resetInstance = function() {
  if (instance) {
    instance.removeAllListeners();
    instance.reset();
  }
  instance = null;
};

module.exports = { AppState };
