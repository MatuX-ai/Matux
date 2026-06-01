/**
 * 离线同步服务
 *
 * 基于 PRD F-12 离线模式增强设计，提供：
 * - 离线操作队列管理
 * - 网络恢复后自动同步
 * - 同步冲突解决
 * - 同步状态追踪
 */

import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject } from 'rxjs';

import {
  OfflineOperation,
  OfflineOperationStatus,
  OfflineSyncConfig,
  OfflineOperationType,
} from '../../../shared/models/offline.models';
import { NetworkMonitorService, NetworkStatus } from '../../core/services/network-monitor.service';
import { OfflineStorageService } from '../../core/services/offline-storage.service';

/** 同步状态 */
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';

/** 同步报告 */
export interface SyncReport {
  totalOperations: number;
  syncedCount: number;
  failedCount: number;
  skippedCount: number;
  startedAt: string;
  completedAt: string | null;
  errors: SyncError[];
}

/** 同步错误 */
export interface SyncError {
  operationId: string;
  error: string;
  retryCount: number;
  timestamp: string;
}

@Injectable({
  providedIn: 'root',
})
export class OfflineSyncService {
  /** 同步状态 */
  private syncStatusSubject = new BehaviorSubject<SyncStatus>('idle');
  public syncStatus$ = this.syncStatusSubject.asObservable();

  /** 同步进度 */
  private syncProgressSubject = new BehaviorSubject<number>(0);
  public syncProgress$ = this.syncProgressSubject.asObservable();

  /** 同步报告 */
  private syncReportSubject = new BehaviorSubject<SyncReport | null>(null);
  public syncReport$ = this.syncReportSubject.asObservable();

  /** 待同步操作数 */
  private pendingCountSubject = new BehaviorSubject<number>(0);
  public pendingCount$ = this.pendingCountSubject.asObservable();

  /** 是否正在同步 */
  private isSyncing = false;

  /** 自动同步定时器 */
  private autoSyncInterval: ReturnType<typeof setInterval> | null = null;

  constructor(
    @Inject(PLATFORM_ID) private platformId: object,
    private networkMonitor: NetworkMonitorService,
    private offlineStorage: OfflineStorageService,
  ) {
    if (isPlatformBrowser(platformId)) {
      this.initializeAutoSync();
    }
  }

  // ==================== 初始化 ====================

  /** 初始化自动同步 */
  private initializeAutoSync(): void {
    const config = this.offlineStorage.getSyncConfig();

    if (config.autoSync) {
      // 监听网络状态变化
      this.networkMonitor.networkStatus$.subscribe((status: NetworkStatus) => {
        if (status.isOnline && this.syncStatusSubject.value === 'offline') {
          // 网络恢复，触发同步
          void this.syncAll();
        }
        this.syncStatusSubject.next(status.isOnline ? 'idle' : 'offline');
      });

      // 定时同步
      this.autoSyncInterval = setInterval(() => {
        if (!this.networkMonitor.isOffline() && !this.isSyncing) {
          void this.syncAll();
        }
      }, config.syncInterval);
    }
  }

  // ==================== 同步操作 ====================

  /** 同步所有待处理操作 */
  async syncAll(): Promise<SyncReport> {
    if (this.isSyncing) {
      return this.syncReportSubject.value ?? this.createEmptyReport();
    }

    if (this.networkMonitor.isOffline()) {
      this.syncStatusSubject.next('offline');
      return this.createEmptyReport();
    }

    this.isSyncing = true;
    this.syncStatusSubject.next('syncing');
    this.syncProgressSubject.next(0);

    const report: SyncReport = {
      totalOperations: 0,
      syncedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      startedAt: new Date().toISOString(),
      completedAt: null,
      errors: [],
    };

    try {
      const operations = await this.offlineStorage.getPendingOperations();
      report.totalOperations = operations.length;
      this.pendingCountSubject.next(operations.length);

      for (let i = 0; i < operations.length; i++) {
        const operation = operations[i];

        // 检查网络质量是否足够
        if (!this.networkMonitor.isHighQualityNetwork()) {
          report.skippedCount++;
          continue;
        }

        try {
          await this.syncOperation(operation);
          report.syncedCount++;
          await this.offlineStorage.updateOperationStatus(
            operation.id,
            OfflineOperationStatus.COMPLETED,
          );
        } catch (error) {
          report.failedCount++;
          report.errors.push({
            operationId: operation.id,
            error: error instanceof Error ? error.message : String(error),
            retryCount: operation.retryCount,
            timestamp: new Date().toISOString(),
          });

          // 判断是否需要重试
          const config = this.offlineStorage.getSyncConfig();
          if (operation.retryCount < config.maxRetryAttempts) {
            await this.offlineStorage.updateOperationStatus(
              operation.id,
              OfflineOperationStatus.PENDING,
              error instanceof Error ? error.message : String(error),
            );
          } else {
            await this.offlineStorage.updateOperationStatus(
              operation.id,
              OfflineOperationStatus.FAILED,
              error instanceof Error ? error.message : String(error),
            );
          }
        }

        // 更新进度
        const progress = ((i + 1) / operations.length) * 100;
        this.syncProgressSubject.next(progress);
      }
    } catch {
      this.syncStatusSubject.next('error');
    } finally {
      report.completedAt = new Date().toISOString();
      this.syncReportSubject.next(report);
      this.isSyncing = false;
      this.syncStatusSubject.next('idle');
      this.syncProgressSubject.next(100);

      // 更新待同步数量
      const remaining = await this.offlineStorage.getPendingOperations();
      this.pendingCountSubject.next(remaining.length);
    }

    return report;
  }

  /** 同步单个操作 */
  private async syncOperation(operation: OfflineOperation): Promise<void> {
    // 根据操作类型调用对应的后端 API
    const response = await fetch('/api/v1/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        table: operation.tableName,
        recordId: operation.recordId,
        type: operation.type,
        data: operation.data,
        timestamp: operation.createdAt,
      }),
    });

    if (!response.ok) {
      throw new Error(`同步失败: ${response.status} ${response.statusText}`);
    }
  }

  // ==================== 队列操作 ====================

  /** 添加离线操作到队列 */
  async enqueueOperation(
    tableName: string,
    type: OfflineOperationType,
    recordId: string,
    data: Record<string, unknown>,
  ): Promise<string> {
    const id = await this.offlineStorage.addOperation({
      tableName,
      type,
      recordId,
      data,
      status: OfflineOperationStatus.PENDING,
    });

    const pending = await this.offlineStorage.getPendingOperations();
    this.pendingCountSubject.next(pending.length);

    return id;
  }

  /** 获取同步状态描述 */
  getSyncStatusDescription(): string {
    const status = this.syncStatusSubject.value;
    const descriptions: Record<SyncStatus, string> = {
      idle: '同步就绪',
      syncing: '正在同步...',
      error: '同步出错',
      offline: '离线模式',
    };
    return descriptions[status] ?? '未知';
  }

  /** 手动触发同步 */
  async manualSync(): Promise<SyncReport> {
    return this.syncAll();
  }

  // ==================== 辅助方法 ====================

  private createEmptyReport(): SyncReport {
    return {
      totalOperations: 0,
      syncedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
      errors: [],
    };
  }

  /** 清理自动同步 */
  destroy(): void {
    if (this.autoSyncInterval) {
      clearInterval(this.autoSyncInterval);
      this.autoSyncInterval = null;
    }
  }
}
