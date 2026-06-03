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
  }
}

export {};
