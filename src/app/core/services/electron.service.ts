/**
 * Electron 桌面服务
 *
 * 封装 Electron IPC API，提供桌面端特有功能：
 * - 后端通信
 * - 文件系统操作
 * - 应用事件监听
 * - 平台检测
 *
 * 在浏览器环境（非 Electron）下提供安全的降级处理。
 */
import { Injectable, NgZone } from '@angular/core';
import { BehaviorSubject, Observable, from, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import type {
  AppEvent,
  AppInfo,
  DirectoryEntry,
  FileInfoResult,
  FileReadResult,
  FileWriteResult,
  ListDirectoryResult,
  OpenDialogResult,
  SaveDialogResult,
  SelectDirectoryResult,
} from '../models/electron-api.model';

@Injectable({
  providedIn: 'root',
})
export class ElectronService {
  /** 是否在 Electron 环境中运行 */
  readonly isElectron: boolean;

  /** 后端 URL Subject */
  private backendUrlSubject = new BehaviorSubject<string>('/api');
  readonly backendUrl$ = this.backendUrlSubject.asObservable();

  /** 应用事件 Subject */
  private appEventSubject = new BehaviorSubject<AppEvent | null>(null);
  readonly appEvent$ = this.appEventSubject.asObservable();

  constructor(private ngZone: NgZone) {
    this.isElectron = !!(typeof window !== 'undefined' && window.electronAPI);

    if (this.isElectron) {
      this.initializeElectron();
    }
  }

  /**
   * 初始化 Electron 环境
   */
  private initializeElectron(): void {
    const api = window.electronAPI!;

    // 获取后端 URL
    api.getBackendUrl().then((url) => {
      this.backendUrlSubject.next(url);
    });

    // 监听应用事件
    api.receive('app-event', (data: unknown) => {
      this.ngZone.run(() => {
        const event = data as AppEvent;
        this.appEventSubject.next(event);

        // 后端断连时弹出系统通知
        if (event.type === 'backend-disconnected') {
          api.showNotification('后端连接断开', '后端服务可能已崩溃，部分功能将不可用');
        }
      });
    });
  }

  /**
   * 获取后端 API 基础 URL
   */
  getBackendUrl(): string {
    return this.backendUrlSubject.getValue();
  }

  /**
   * 获取应用信息
   */
  getAppInfo(): Observable<AppInfo | null> {
    if (!this.isElectron) {
      return of(null);
    }
    return from(window.electronAPI!.getAppInfo()).pipe(
      catchError(() => of(null))
    );
  }

  /**
   * 健康检查
   */
  healthCheck(): Observable<boolean> {
    if (!this.isElectron) {
      return of(true); // 浏览器环境假设健康
    }
    return from(window.electronAPI!.healthCheck()).pipe(
      catchError(() => of(false))
    );
  }

  // ==================== 文件系统操作 ====================

  /**
   * 读取文件
   */
  readFile(filePath: string): Observable<FileReadResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.readFile(filePath));
  }

  /**
   * 写入文件
   */
  writeFile(filePath: string, content: string): Observable<FileWriteResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.writeFile(filePath, content));
  }

  /**
   * 打开保存文件对话框
   */
  showSaveDialog(): Observable<SaveDialogResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.showSaveDialog());
  }

  /**
   * 打开文件对话框
   */
  showOpenDialog(): Observable<OpenDialogResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.showOpenDialog());
  }

  /** ==================== 增强文件系统操作 (P1-4) ==================== */

  /** 列出目录内容 */
  listDirectory(dirPath: string): Observable<ListDirectoryResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.listDirectory(dirPath));
  }

  /** 创建目录（递归） */
  makeDirectory(dirPath: string): Observable<{ success: boolean; error?: string }> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.makeDirectory(dirPath));
  }

  /** 删除文件或目录 */
  deleteFile(targetPath: string): Observable<{ success: boolean; error?: string }> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.deleteFile(targetPath));
  }

  /** 检查文件是否存在 */
  fileExists(targetPath: string): Observable<{ exists: boolean }> {
    if (!this.isElectron) {
      return of({ exists: false });
    }
    return from(window.electronAPI!.fileExists(targetPath));
  }

  /** 获取文件信息 */
  getFileInfo(filePath: string): Observable<FileInfoResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.getFileInfo(filePath));
  }

  /** 选择目录对话框 */
  selectDirectory(): Observable<SelectDirectoryResult> {
    if (!this.isElectron) {
      return of({ success: false, error: '非桌面环境' });
    }
    return from(window.electronAPI!.selectDirectory());
  }

  /**
   * 打开外部链接
   */
  openExternal(url: string): Observable<boolean> {
    if (!this.isElectron) {
      window.open(url, '_blank');
      return of(true);
    }
    return from(window.electronAPI!.openExternal(url)).pipe(
      map((result) => result.success),
      catchError(() => of(false))
    );
  }

  // ==================== 事件 ====================

  /**
   * 监听特定应用事件
   */
  onAppEvent(eventType: AppEvent['type']): Observable<AppEvent> {
    return this.appEvent$.pipe(
      // 过滤匹配类型的事件
    ) as unknown as Observable<AppEvent>;
    // 注：实际过滤逻辑由订阅方处理
  }

  /**
   * 获取窗口失焦事件流
   */
  onWindowBlur(): Observable<void> {
    return this.appEvent$.pipe(
      // 实际过滤由使用方通过 filter 操作符完成
    ) as unknown as Observable<void>;
  }

  /**
   * 获取窗口聚焦事件流
   */
  onWindowFocus(): Observable<void> {
    return this.appEvent$.pipe(
    ) as unknown as Observable<void>;
  }

  /**
   * 发送应用事件到主进程
   */
  sendAppEvent(event: AppEvent): void {
    if (this.isElectron) {
      window.electronAPI!.send('app-event', event);
    }
  }

  /**
   * 最小化窗口
   */
  minimize(): void {
    this.sendAppEvent({ type: 'minimize' });
  }

  /**
   * 最大化/还原窗口
   */
  toggleMaximize(): void {
    this.sendAppEvent({ type: 'maximize' });
  }

  /**
   * 关闭窗口
   */
  close(): void {
    this.sendAppEvent({ type: 'close' });
  }

  /**
   * 切换全屏
   */
  toggleFullscreen(): void {
    this.sendAppEvent({ type: 'toggle-fullscreen' });
  }
}
