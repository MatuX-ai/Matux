/**
 * 插件商店服务
 * 
 * 功能:
 * 1. 获取插件列表
 * 2. 搜索插件
 * 3. 获取插件详情
 * 4. 检查兼容性
 * 5. 安装/卸载插件
 * 6. 启用/禁用插件
 * 7. 下载进度跟踪
 * 8. 安装进度跟踪
 */

import { Injectable, NgZone } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject, from, interval } from 'rxjs';
import { map, switchMap, takeWhile, catchError } from 'rxjs/operators';

// ==================== 类型定义 ====================

export interface PluginAuthor {
  name: string;
  email?: string;
  url?: string;
  organization?: string;
}

export interface PluginListItem {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  icon?: string;
  categories: string[];
  state: string;
  enabled: boolean;
  compatible?: boolean;
}

export interface PluginDetail {
  id: string;
  name: string;
  version: string;
  description: string;
  author: PluginAuthor;
  license: string;
  categories: string[];
  keywords: string[];
  icon?: string;
  state: string;
  enabled: boolean;
  installed_at?: string;
  loaded_at?: string;
  device_compatibility: any;
  permissions: string[];
  settings: any;
  error?: string;
}

export interface CompatibilityCheckResult {
  compatible: boolean;
  device_class: string;
  device_score: number;
  required_tiers: string[];
  compatible_tiers: string[];
  warnings: string[];
  errors: string[];
}

export interface PluginSearchResult {
  total: number;
  plugins: PluginListItem[];
  query: string;
  filters: any;
}

export interface PluginStats {
  total_installed: number;
  total_enabled: number;
  total_disabled: number;
  total_loaded: number;
  total_errors: number;
  categories: { [key: string]: number };
}

export interface DownloadProgress {
  pluginId: string;
  version: string;
  status: string;
  progress: number;
  downloadedBytes: number;
  totalBytes: number;
  speed: number;
  eta: number;
  message: string;
}

export interface InstallProgress {
  pluginId: string;
  status: string;
  progress: number;
  message: string;
  error?: string;
}

// ==================== 服务类 ====================

@Injectable({
  providedIn: 'root',
})
export class PluginStoreService {
  private baseUrl = '/api/v1/plugins';
  
  // 进度跟踪
  private downloadProgressMap = new Map<string, BehaviorSubject<DownloadProgress | null>>();
  private installProgressMap = new Map<string, BehaviorSubject<InstallProgress | null>>();
  
  constructor(
    private http: HttpClient,
    private ngZone: NgZone,
  ) {}
  
  // ==================== 插件列表 ====================
  
  /**
   * 获取插件列表
   */
  getPlugins(options?: {
    state?: string;
    category?: string;
    compatibleOnly?: boolean;
  }): Observable<PluginListItem[]> {
    let params = new HttpParams();
    
    if (options?.state) {
      params = params.set('state', options.state);
    }
    if (options?.category) {
      params = params.set('category', options.category);
    }
    if (options?.compatibleOnly) {
      params = params.set('compatible_only', 'true');
    }
    
    return this.http.get<PluginListItem[]>(this.baseUrl, { params });
  }
  
  /**
   * 获取插件详情
   */
  getPluginDetail(pluginId: string): Observable<PluginDetail> {
    return this.http.get<PluginDetail>(`${this.baseUrl}/${pluginId}`);
  }
  
  /**
   * 搜索插件
   */
  searchPlugins(query: string, options?: {
    category?: string;
    tier?: string;
  }): Observable<PluginSearchResult> {
    let params = new HttpParams().set('q', query);
    
    if (options?.category) {
      params = params.set('category', options.category);
    }
    if (options?.tier) {
      params = params.set('tier', options.tier);
    }
    
    return this.http.get<PluginSearchResult>(`${this.baseUrl}/search`, { params });
  }
  
  /**
   * 获取插件统计信息
   */
  getPluginStats(): Observable<PluginStats> {
    return this.http.get<PluginStats>(`${this.baseUrl}/stats`);
  }
  
  // ==================== 兼容性检查 ====================
  
  /**
   * 检查插件兼容性
   */
  checkCompatibility(pluginId: string): Observable<CompatibilityCheckResult> {
    return this.http.get<CompatibilityCheckResult>(`${this.baseUrl}/${pluginId}/compatibility`);
  }
  
  // ==================== 插件操作 ====================
  
  /**
   * 安装插件（通过 Electron IPC）
   */
  async installPlugin(pluginId: string, version?: string): Promise<any> {
    if (!window.pluginAPI) {
      throw new Error('Plugin API 不可用（非 Electron 环境）');
    }
    
    // 创建进度跟踪
    const progressSubject = new BehaviorSubject<InstallProgress | null>(null);
    this.installProgressMap.set(pluginId, progressSubject);
    
    try {
      // 监听安装进度
      const removeListener = window.pluginAPI.onInstallProgress((data: any) => {
        if (data.pluginId === pluginId) {
          this.ngZone.run(() => {
            progressSubject.next({
              pluginId: data.pluginId,
              status: data.status,
              progress: data.progress,
              message: data.message,
              error: data.error,
            });
            
            // 完成后清理
            if (data.status === 'completed' || data.status === 'failed') {
              setTimeout(() => {
                this.installProgressMap.delete(pluginId);
              }, 5000);
            }
          });
        }
      });
      
      // 调用 Electron IPC
      const result = await window.pluginAPI.installPlugin(pluginId, version);
      
      return result;
    } catch (err) {
      this.installProgressMap.delete(pluginId);
      throw err;
    }
  }
  
  /**
   * 卸载插件（通过 Electron IPC）
   */
  async uninstallPlugin(pluginId: string, keepData: boolean = true): Promise<any> {
    if (!window.pluginAPI) {
      throw new Error('Plugin API 不可用（非 Electron 环境）');
    }
    
    return await window.pluginAPI.uninstallPlugin(pluginId, keepData);
  }
  
  /**
   * 启用/禁用插件
   */
  togglePlugin(pluginId: string, enabled: boolean): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle`, {
      plugin_id: pluginId,
      enabled,
    });
  }
  
  /**
   * 更新插件
   */
  async updatePlugin(pluginId: string, version?: string): Promise<any> {
    if (!window.pluginAPI) {
      throw new Error('Plugin API 不可用（非 Electron 环境）');
    }
    
    return await this.http.post(`${this.baseUrl}/update`, {
      plugin_id: pluginId,
      version,
    }).toPromise();
  }
  
  /**
   * 重新加载插件（开发模式）
   */
  reloadPlugins(): Observable<any> {
    return this.http.post(`${this.baseUrl}/reload`, {});
  }
  
  // ==================== 下载管理 ====================
  
  /**
   * 下载插件
   */
  async downloadPlugin(pluginId: string, version: string, url: string): Promise<any> {
    if (!window.pluginAPI) {
      throw new Error('Plugin API 不可用（非 Electron 环境）');
    }
    
    // 创建进度跟踪
    const progressSubject = new BehaviorSubject<DownloadProgress | null>(null);
    this.downloadProgressMap.set(`${pluginId}@${version}`, progressSubject);
    
    try {
      // 监听下载进度
      const removeListener = window.pluginAPI.onInstallProgress((data: any) => {
        if (data.type === 'progress' && data.pluginId === pluginId) {
          this.ngZone.run(() => {
            progressSubject.next({
              pluginId: data.pluginId,
              version: data.version,
              status: data.status,
              progress: data.progress,
              downloadedBytes: data.downloadedBytes,
              totalBytes: data.totalBytes,
              speed: data.speed,
              eta: data.eta,
              message: data.message,
            });
          });
        }
      });
      
      // 调用 Electron IPC
      const result = await window.pluginAPI.downloadPlugin(pluginId, version, url);
      
      return result;
    } catch (err) {
      this.downloadProgressMap.delete(`${pluginId}@${version}`);
      throw err;
    }
  }
  
  /**
   * 取消下载
   */
  async cancelDownload(pluginId: string, version: string): Promise<void> {
    if (!window.pluginAPI) {
      return;
    }
    
    await window.pluginAPI.cancelDownload(pluginId, version);
    this.downloadProgressMap.delete(`${pluginId}@${version}`);
  }
  
  /**
   * 暂停下载
   */
  async pauseDownload(pluginId: string, version: string): Promise<void> {
    if (!window.pluginAPI) {
      return;
    }
    
    await window.pluginAPI.pauseDownload(pluginId, version);
  }
  
  /**
   * 恢复下载
   */
  async resumeDownload(pluginId: string, version: string): Promise<void> {
    if (!window.pluginAPI) {
      return;
    }
    
    await window.pluginAPI.resumeDownload(pluginId, version);
  }
  
  // ==================== 进度观察器 ====================
  
  /**
   * 获取下载进度 Observable
   */
  getDownloadProgress(pluginId: string, version: string): Observable<DownloadProgress | null> {
    const key = `${pluginId}@${version}`;
    
    if (!this.downloadProgressMap.has(key)) {
      this.downloadProgressMap.set(key, new BehaviorSubject<DownloadProgress | null>(null));
    }
    
    return this.downloadProgressMap.get(key)!.asObservable();
  }
  
  /**
   * 获取安装进度 Observable
   */
  getInstallProgress(pluginId: string): Observable<InstallProgress | null> {
    if (!this.installProgressMap.has(pluginId)) {
      this.installProgressMap.set(pluginId, new BehaviorSubject<InstallProgress | null>(null));
    }
    
    return this.installProgressMap.get(pluginId)!.asObservable();
  }
  
  // ==================== 工具方法 ====================
  
  /**
   * 格式化字节大小
   */
  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  /**
   * 格式化时间（秒）
   */
  formatTime(seconds: number): string {
    if (seconds < 60) return `${Math.ceil(seconds)}秒`;
    if (seconds < 3600) return `${Math.ceil(seconds / 60)}分钟`;
    return `${Math.ceil(seconds / 3600)}小时`;
  }
  
  /**
   * 获取分类标签文本
   */
  getCategoryLabel(category: string): string {
    const labels: { [key: string]: string } = {
      'ai-assistant': 'AI 助手',
      'ar-vr-lab': 'AR/VR 实验室',
      'coding-tools': '编程工具',
      'data-analysis': '数据分析',
      'education': '教育',
      'gamification': '游戏化',
      'hardware': '硬件',
      'ml-training': '机器学习',
      'visualization': '可视化',
      'productivity': '效率工具',
      'other': '其他',
    };
    
    return labels[category] || category;
  }
  
  /**
   * 获取状态标签文本
   */
  getStateLabel(state: string): string {
    const labels: { [key: string]: string } = {
      'installed': '已安装',
      'loaded': '已加载',
      'enabled': '已启用',
      'disabled': '已禁用',
      'error': '错误',
    };
    
    return labels[state] || state;
  }
  
  /**
   * 获取状态颜色
   */
  getStateColor(state: string): string {
    const colors: { [key: string]: string } = {
      'installed': '#2196F3',
      'loaded': '#4CAF50',
      'enabled': '#4CAF50',
      'disabled': '#9E9E9E',
      'error': '#F44336',
    };
    
    return colors[state] || '#9E9E9E';
  }
}
