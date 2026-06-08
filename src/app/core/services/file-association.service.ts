/**
 * 文件关联服务
 *
 * 监听主进程发送的文件打开事件
 * 支持: .imato (课程包), .imblockly (Blockly项目), .imcircuit (电路项目)
 */

import { Injectable, NgZone } from '@angular/core';
import { Subject, Observable } from 'rxjs';

/** 文件类型 */
export type FileType = 'course' | 'blockly' | 'circuit';

/** 文件打开事件 */
export interface FileOpenEvent {
  type: 'open-file';
  filePath: string;
  content: any;
  fileType: FileType;
}

/** 文件验证结果 */
export interface FileValidationResult {
  valid: boolean;
  error?: string;
  content?: any;
  fileType?: FileType;
  version?: string;
}

@Injectable({
  providedIn: 'root',
})
export class FileAssociationService {
  /** 文件类型到路由的映射 */
  private readonly FILE_TYPE_ROUTES: Record<FileType, string> = {
    course: '/course',
    blockly: '/ai-edu/coding',
    circuit: '/ar-lab',
  };

  /** 接收到的文件事件流 */
  private fileOpenSubject = new Subject<FileOpenEvent>();
  readonly fileOpen$: Observable<FileOpenEvent> = this.fileOpenSubject.asObservable();

  constructor(private ngZone: NgZone) {
    this.initFileEventListener();
  }

  /**
   * 初始化文件事件监听
   */
  private initFileEventListener(): void {
    // 检查是否在 Electron 环境中
    if (!this.isElectronEnvironment()) {
      console.warn('[FileAssociation] 非 Electron 环境，跳过文件关联监听');
      return;
    }

    // 从 window 获取 Electron API
    const electronAPI = (window as any).electronAPI;
    if (!electronAPI?.on) {
      console.warn('[FileAssociation] Electron API 不可用');
      return;
    }

    // 监听主进程发送的文件事件
    electronAPI.on('app-event', (event: any, data: FileOpenEvent) => {
      if (data?.type === 'open-file') {
        console.log('[FileAssociation] 收到文件打开事件:', data);
        this.ngZone.run(() => {
          this.fileOpenSubject.next(data);
        });
      }
    });

    console.log('[FileAssociation] 文件关联监听已初始化');
  }

  /**
   * 检查是否为 Electron 环境
   */
  private isElectronEnvironment(): boolean {
    return typeof window !== 'undefined' && !!(window as any).electronAPI;
  }

  /**
   * 验证文件内容
   */
  validateFile(event: FileOpenEvent): FileValidationResult {
    const { content, fileType } = event;

    if (!content) {
      return { valid: false, error: '文件内容为空' };
    }

    // 验证版本
    if (!content.version) {
      return { valid: false, error: '缺少 version 字段' };
    }

    // 验证类型
    if (!content.type) {
      return { valid: false, error: '缺少 type 字段' };
    }

    // 验证数据
    if (!content.data) {
      return { valid: false, error: '缺少 data 字段' };
    }

    return {
      valid: true,
      content: content.data,
      fileType,
      version: content.version,
    };
  }

  /**
   * 获取文件类型对应的路由
   */
  getRouteForFileType(fileType: FileType): string {
    return this.FILE_TYPE_ROUTES[fileType] || '/';
  }

  /**
   * 获取文件类型标签
   */
  getFileTypeLabel(fileType: FileType): string {
    const labels: Record<FileType, string> = {
      course: '课程包',
      blockly: 'Blockly 项目',
      circuit: '电路项目',
    };
    return labels[fileType] || '未知类型';
  }

  /**
   * 处理文件打开事件
   * 返回导航路由和文件数据
   */
  handleFileOpen(event: FileOpenEvent): { route: string; data: any } | null {
    const validation = this.validateFile(event);
    if (!validation.valid) {
      console.error('[FileAssociation] 文件验证失败:', validation.error);
      return null;
    }

    const route = this.getRouteForFileType(event.fileType);
    return {
      route,
      data: {
        ...validation.content,
        _meta: {
          filePath: event.filePath,
          fileType: event.fileType,
          version: validation.version,
        },
      },
    };
  }
}
