/* eslint-disable @typescript-eslint/prefer-optional-chain */
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
import { BehaviorSubject } from 'rxjs';

/** .imato 课程包数据结构（与 file-parser.js createProjectFile 输出对齐） */
export interface ImatoCoursePackage {
  /** 课程包格式版本 */
  version: string;
  /** 课程包类型 */
  type: string;
  /** 课程包内容数据 */
  data: {
    title: string;
    description?: string;
    modules: ImatoModule[];
    [key: string]: unknown;
  };
  /** 课程包元数据 */
  metadata: {
    createdAt: string;
    updatedAt?: string;
    author?: string;
    /** 预计学习时长（分钟） */
    estimatedDuration?: number;
    /** 适用年级 */
    gradeLevel?: string;
    /** 标签 */
    tags?: string[];
  };
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

  private recentFilesSubject = new BehaviorSubject<
    { path: string; title: string; openedAt: string }[]
  >([]);
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
    const win = window as unknown as {
      electronAPI?: {
        on: (
          event: string,
          handler: (data: {
            filePath: string;
            content: string | Record<string, unknown>;
            fileType?: string;
          }) => void
        ) => void;
      };
    };
    if (typeof window !== 'undefined' && win.electronAPI?.on) {
      win.electronAPI.on('open-file', (data) => {
        this.handleOpenFile(data.filePath, data.content);
      });
    }
  }

  /** 解析并处理打开的 .imato 文件 */
  private handleOpenFile(filePath: string, content: string | Record<string, unknown>): void {
    try {
      // 主进程可能发送已解析的 JSON 对象或原始字符串
      const parsed: ImatoCoursePackage =
        typeof content === 'string'
          ? (JSON.parse(content) as ImatoCoursePackage)
          : (content as unknown as ImatoCoursePackage);

      if (!this.validatePackage(parsed)) {
        console.warn('[ImatoFileService] 课程包验证失败:', filePath);
        return;
      }
      this.currentPackageSubject.next(parsed);
      this.addToRecentFiles(filePath, parsed.data.title);
    } catch (err) {
      console.error('[ImatoFileService] 解析文件失败:', filePath, err);
    }
  }

  /** 校验课程包格式（与 file-parser.js validateFileContent 对齐） */
  private validatePackage(pkg: ImatoCoursePackage): boolean {
    return !!(
      pkg.version &&
      pkg.type &&
      pkg.data &&
      typeof pkg.data === 'object' &&
      pkg.data.title &&
      Array.isArray(pkg.data.modules) &&
      pkg.data.modules.length > 0 &&
      pkg.data.modules.every((m) => m.id && m.title && m.content) &&
      pkg.metadata &&
      pkg.metadata.createdAt
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
    } catch {
      /* 存储失败忽略 */
    }
  }

  private loadRecentFiles(): void {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const parsed = JSON.parse(data) as { path: string; title: string; openedAt: string }[];
        this.recentFilesSubject.next(parsed);
      }
    } catch {
      /* 加载失败忽略 */
    }
  }
}
