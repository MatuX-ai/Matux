/**
 * .imato 文件关联服务
 *
 * 处理 Electron 桌面端通过文件关联打开的 .imato 课程包文件：
 * - 监听 open-file 事件（从 preload.js 桥接）
 * - 解析 .imato 文件内容（JSON 格式课程包）
 * - 提供课程包数据供组件使用
 *
 * 关联配置见 electron/electron-builder.yml fileAssociations
 * 主进程处理见 electron/main.js open-file 事件
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/** .imato 课程包数据结构 */
export interface ImatoCoursePackage {
  /** 课程包格式版本 */
  version: string;
  /** 课程包元数据 */
  metadata: {
    title: string;
    description: string;
    author: string;
    createdAt: string;
    /** 预计学习时长（分钟） */
    estimatedDuration?: number;
    /** 适用年级 */
    gradeLevel?: string;
    /** 标签 */
    tags?: string[];
  };
  /** 课程内容模块 */
  modules: ImatoModule[];
}

/** .imato 课程模块 */
export interface ImatoModule {
  id: string;
  title: string;
  type: 'lesson' | 'quiz' | 'project' | 'reference';
  content: string;
  /** Markdown 格式内容 */
  format: 'markdown' | 'html' | 'json';
  /** 依赖模块 ID 列表 */
  prerequisites?: string[];
  /** 资源 URL 列表 */
  resources?: string[];
}

@Injectable({
  providedIn: 'root',
})
export class ImatoFileService {
  private currentPackageSubject = new BehaviorSubject<ImatoCoursePackage | null>(null);
  public currentPackage$ = this.currentPackageSubject.asObservable();

  private recentFilesSubject = new BehaviorSubject<{ path: string; title: string; openedAt: string }[]>([]);
  public recentFiles$ = this.recentFilesSubject.asObservable();

  constructor() {
    this.initFileListener();
    this.loadRecentFiles();
  }

  /** 获取当前课程包 */
  get currentPackage(): ImatoCoursePackage | null {
    return this.currentPackageSubject.value;
  }

  /** 初始化文件打开事件监听 */
  private initFileListener(): void {
    // 仅在 Electron 环境下运行
    if (typeof window !== 'undefined' && (window as any).electronAPI?.on) {
      (window as any).electronAPI.on('open-file', (data: { filePath: string; content: string }) => {
        this.handleOpenFile(data.filePath, data.content);
      });
    }
  }

  /** 解析并处理打开的 .imato 文件 */
  private handleOpenFile(filePath: string, rawContent: string): void {
    try {
      const parsed = JSON.parse(rawContent) as ImatoCoursePackage;
      if (!this.validatePackage(parsed)) {
        return;
      }
      this.currentPackageSubject.next(parsed);
      this.addToRecentFiles(filePath, parsed.metadata.title);
    } catch {
      // 解析失败忽略
    }
  }

  /** 校验课程包格式 */
  private validatePackage(pkg: ImatoCoursePackage): boolean {
    return !!(
      pkg.version &&
      pkg.metadata?.title &&
      Array.isArray(pkg.modules) &&
      pkg.modules.length > 0 &&
      pkg.modules.every((m) => m.id && m.title && m.content)
    );
  }

  /** 清除当前课程包 */
  clearPackage(): void {
    this.currentPackageSubject.next(null);
  }

  // ==================== 历史记录 ====================

  private readonly STORAGE_KEY = 'imato_recent_files';

  private addToRecentFiles(path: string, title: string): void {
    const recent = this.recentFilesSubject.value;
    // 去重：移除相同路径的旧记录
    const filtered = recent.filter((f) => f.path !== path);
    const updated = [{ path, title, openedAt: new Date().toISOString() }, ...filtered].slice(0, 20);
    this.recentFilesSubject.next(updated);
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updated));
    } catch { /* 存储失败忽略 */ }
  }

  private loadRecentFiles(): void {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const parsed = JSON.parse(data) as { path: string; title: string; openedAt: string }[];
        this.recentFilesSubject.next(parsed);
      }
    } catch { /* 加载失败忽略 */ }
  }
}
