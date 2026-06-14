/**
 * Electron desktop API type definitions.
 *
 * Used for secure communication between Angular frontend and Electron main process.
 * Exposed via contextBridge.exposeInMainWorld in preload.js.
 */

/** 文件读取结果 */
export interface FileReadResult {
  success: boolean;
  content?: string;
  error?: string;
}

/** 文件写入结果 */
export interface FileWriteResult {
  success: boolean;
  error?: string;
}

/** 文件保存对话框结果 */
export interface SaveDialogResult {
  success: boolean;
  filePath?: string;
  error?: string;
}

/** 文件打开对话框结果 */
export interface OpenDialogResult {
  success: boolean;
  filePath?: string;
  content?: string;
  error?: string;
}

/** 目录列表结果 */
export interface DirectoryEntry {
  name: string;
  path: string;
  isDirectory: boolean;
  size?: number;
  modifiedAt?: string;
}

/** 目录列表结果 */
export interface ListDirectoryResult {
  success: boolean;
  entries?: DirectoryEntry[];
  error?: string;
}

/** 文件信息 */
export interface FileInfoResult {
  success: boolean;
  name?: string;
  path?: string;
  size?: number;
  isDirectory?: boolean;
  modifiedAt?: string;
  error?: string;
}

/** 选择目录结果 */
export interface SelectDirectoryResult {
  success: boolean;
  path?: string;
  error?: string;
}

/** 应用信息 */
export interface AppInfo {
  version: string;
  name: string;
  platform: string;
  arch: string;
  isDev: boolean;
}

/** 应用事件类型 */
export type AppEventType =
  | 'window-blur'
  | 'window-focus'
  | 'backend-disconnected'
  | 'backend-reconnected'
  | 'backend-degraded'
  | 'backend-ready'
  | 'minimize'
  | 'maximize'
  | 'close'
  | 'toggle-fullscreen'
  | 'window-resize'
  | 'open-file'
  | 'update-available'
  | 'fullscreen-enter'
  | 'fullscreen-leave';

/** 应用事件数据 */
export interface AppEvent {
  type: AppEventType;
  [key: string]: unknown;
}

export interface ElectronAPI {
  // ==================== 后端通信 ====================

  /** 获取后端服务 URL */
  getBackendUrl(): Promise<string>;

  /** 执行后端健康检查 */
  healthCheck(): Promise<boolean>;

  /** 查询当前是否处于降级模式（无 Python 后端） */
  isBackendDegraded(): Promise<{ degraded: boolean }>;

  /** 重试后端设置（退出降级模式路径） */
  retryBackendSetup(): Promise<{ success: boolean; message?: string; error?: string }>;

  /** 获取应用信息 */
  getAppInfo(): Promise<AppInfo>;

  // ==================== 文件系统操作 ====================

  /** 读取文件内容 */
  readFile(filePath: string): Promise<FileReadResult>;

  /** 写入文件内容（文本或二进制） */
  writeFile(filePath: string, content: string): Promise<FileWriteResult>;

  /** 打开保存文件对话框 */
  showSaveDialog(opts?: Record<string, unknown>): Promise<SaveDialogResult>;

  /** 打开文件对话框 */
  showOpenDialog(): Promise<OpenDialogResult>;

  /** 列出目录内容 */
  listDirectory(dirPath: string): Promise<ListDirectoryResult>;

  /** 创建目录（递归） */
  makeDirectory(dirPath: string): Promise<{ success: boolean; error?: string }>;

  /** 删除文件或目录 */
  deleteFile(targetPath: string): Promise<{ success: boolean; error?: string }>;

  /** 检查文件是否存在 */
  fileExists(targetPath: string): Promise<{ exists: boolean }>;

  /** 获取文件信息 */
  getFileInfo(filePath: string): Promise<FileInfoResult>;

  /** 选择目录对话框 */
  selectDirectory(): Promise<SelectDirectoryResult>;

  /** 打开外部链接 */
  openExternal(url: string): Promise<{ success: boolean; error?: string }>;

  // ==================== 原生功能 ====================

  /** 发送原生系统通知 */
  showNotification(title: string, body: string, category?: string): Promise<{ success: boolean }>;

  /** 检查应用更新 */
  checkForUpdates(): Promise<{ success: boolean }>;

  // ==================== 窗口控制 ====================

  /** 窗口操作（最小化/最大化/关闭/全屏等） */
  windowControl(action: AppEventType): void;

  /** 获取当前窗口尺寸 */
  getWindowSize(): Promise<{ width: number; height: number }>;

  // ==================== 事件通信 ====================

  /** 向主进程发送消息 */
  send(channel: 'to-backend' | 'app-event', data: unknown): void;

  /** 通用事件监听（支持更多频道） */
  on(channel: string, func: (...args: unknown[]) => void): void;

  /** 从主进程接收消息 */
  receive(channel: 'from-backend' | 'app-event', func: (...args: unknown[]) => void): void;

  /** 移除消息监听 */
  removeListener(channel: string, func: (...args: unknown[]) => void): void;

  /** 移除所有消息监听 */
  removeAllListeners(channel: string): void;
}

/**
 * 全局 window.electronAPI 声明扩展
 */
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    pluginAPI?: PluginAPI;
  }
}

export {};

// ==================== 插件管理 API 类型 ====================

/** 设备评估报告 */
export interface DeviceProfile {
  version: string;
  assessedAt: string;
  assessmentDurationMs: number;
  hardware: HardwareProfile;
  software: SoftwareProfile;
  assessment: DeviceAssessment;
  installedPlugins: string[];
  pluginHistory: Array<{ plugin: string; action: string; reason?: string; at: string }>;
}

export interface HardwareProfile {
  cpu: { arch: string; cores: number; model: string; benchmarkScore: number };
  memory: { totalMB: number; availableMB: number };
  gpu: {
    hasDedicatedGPU: boolean;
    gpuName: string;
    vramMB: number;
    supportsWebGL2: boolean;
    supportsWebGPU: boolean;
    supportsCUDA: boolean;
    supportsOpenCL: boolean;
  };
  storage: { totalGB: number; freeGB: number; type: 'hdd' | 'ssd' };
  peripherals: {
    hasCamera: boolean;
    hasMicrophone: boolean;
    hasUSBDevices: boolean;
    hasGamepad: boolean;
  };
  network: { type: string; bandwidthMbps: number; isMetered: boolean };
  display: {
    resolution: { width: number; height: number };
    pixelRatio: number;
    refreshRateHz: number;
  };
}

export interface SoftwareProfile {
  os: { platform: string; version: string; arch: string };
  runtime: { pythonVersion: string; pythonPath: string; nodeVersion: string };
  containers: {
    dockerInstalled: boolean;
    dockerRunning: boolean;
    dockerVersion: string;
    kubectlInstalled: boolean;
  };
  hardware_tools: {
    arduinoCliInstalled: boolean;
    platformioInstalled: boolean;
    edgeImpulseCli: boolean;
  };
  connectivity: {
    redisAvailable: boolean;
    neo4jAvailable: boolean;
    hyperledgerAvailable: boolean;
    vircadiaAvailable: boolean;
  };
}

export type DeviceClass = 'basic' | 'standard' | 'advanced' | 'professional';

export interface DeviceAssessment {
  deviceClass: DeviceClass;
  score: number;
  scores: {
    cpuScore: number;
    memoryScore: number;
    gpuScore: number;
    storageScore: number;
    networkScore: number;
    peripheralScore: number;
  };
  compatiblePluginTiers: string[];
  recommendedPlugins: string[];
  incompatiblePlugins: string[];
  warnings: string[];
}

/** 插件兼容性检查结果 */
export interface PluginCompatibilityResult {
  success: boolean;
  deviceClass?: DeviceClass;
  score?: number;
  hardware?: HardwareProfile;
  software?: SoftwareProfile;
  compatibleTiers?: string[];
  recommendedPlugins?: string[];
  incompatiblePlugins?: string[];
  error?: string;
}

/** 插件 API 接口 */
export interface PluginAPI {
  // 设备评估
  getDeviceProfile(): Promise<{ success: boolean; profile?: DeviceProfile; error?: string }>;
  reassessDevice(): Promise<{ success: boolean; profile?: DeviceProfile; error?: string }>;
  assessPlugin(pluginId: string): Promise<PluginCompatibilityResult>;

  // 插件商店 (Phase 2)
  getPluginCatalog(): Promise<unknown>;
  getRecommendedBundles(): Promise<unknown>;
  searchPlugins(query: string): Promise<unknown>;

  // 插件管理 (Phase 2)
  installPlugin(pluginId: string, version?: string): Promise<unknown>;
  uninstallPlugin(pluginId: string, keepData?: boolean): Promise<unknown>;
  updatePlugin(pluginId: string): Promise<unknown>;
  getInstalledPlugins(): Promise<unknown>;
  togglePlugin(pluginId: string, enabled: boolean): Promise<unknown>;

  // 插件下载/更新
  downloadPlugin(pluginId: string, version?: string, url?: string): Promise<unknown>;
  cancelDownload(pluginId: string, version?: string): Promise<unknown>;
  pauseDownload(pluginId: string, version?: string): Promise<unknown>;
  resumeDownload(pluginId: string, version?: string): Promise<unknown>;
  checkForUpdates(plugins: unknown): Promise<unknown>;
  getPluginUsageStats(pluginId: string): Promise<unknown>;

  // 通知/更新列表
  getPendingNotifications(): Promise<unknown>;
  markNotificationInstalled(id: string): Promise<unknown>;
  dismissNotification(id: string): Promise<unknown>;

  // 首次运行向导
  getFirstRunGuide(): Promise<unknown>;
  getRecommendedModules(deviceClass?: string): Promise<unknown>;
  getRecommendations(options?: unknown): Promise<unknown>;
  addInstalledModule(moduleId: string): Promise<unknown>;
  markFirstRunCompleted(): Promise<unknown>;

  // 插件评价
  getPluginReviews(pluginId: string, options?: unknown): Promise<unknown>;
  getPluginAverageRating(pluginId: string): Promise<unknown>;
  addPluginReview(payload: unknown): Promise<unknown>;
  markReviewHelpful(reviewId: string, pluginId: string): Promise<unknown>;

  // 事件监听
  onInstallProgress(
    callback: (data: { pluginId: string; phase: string; progress: number; message: string }) => void
  ): void;
  onPluginStatusChange(
    callback: (data: { type: string; pluginId?: string; profile?: DeviceProfile }) => void
  ): void;
  onUpdatesAvailable(
    callback: (data: {
      updates: Array<{ pluginId: string; fromVersion: string; toVersion: string }>;
    }) => void
  ): void;
}
