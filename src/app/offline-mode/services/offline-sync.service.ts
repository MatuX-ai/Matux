/**
 * 离线同步服务
 *
 * 基于 PRD F-12 离线模式增强设计，提供：
 * - 离线操作队列管理（带优先级）
 * - 网络恢复后自动同步
 * - 批量提交（减少请求次数）
 * - 同步冲突解决
 * - 同步状态追踪与历史记录
 * - 指数退避重试
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

/** 冲突解决策略 */
export type ConflictStrategy = 'last_write_wins' | 'local_wins' | 'remote_wins' | 'manual';

/** 队列优先级 */
export type SyncPriority = 'high' | 'normal' | 'low';

/** 同步状态 */
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';

/** 同步报告 */
export interface SyncReport {
  totalOperations: number;
  syncedCount: number;
  failedCount: number;
  skippedCount: number;
  conflictCount: number;
  startedAt: string;
  completedAt: string | null;
  errors: SyncError[];
  batchInfo?: { totalBatches: number; completedBatches: number };
}

/** 同步错误 */
export interface SyncError {
  operationId: string;
  error: string;
  errorType: 'network' | 'server' | 'conflict' | 'timeout' | 'unknown';
  retryCount: number;
  timestamp: string;
}

/** 同步历史记录 */
export interface SyncHistoryEntry {
  id: string;
  timestamp: string;
  totalOperations: number;
  syncedCount: number;
  failedCount: number;
  duration: number;
  status: 'success' | 'partial' | 'failure';
}

/** 带优先级的队列操作 */
interface PrioritizedOperation extends OfflineOperation {
  priority: SyncPriority;
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

  /** 同步历史 */
  private syncHistorySubject = new BehaviorSubject<SyncHistoryEntry[]>([]);
  public syncHistory$ = this.syncHistorySubject.asObservable();

  /** 是否正在同步 */
  private isSyncing = false;

  /** 自动同步定时器 */
  private autoSyncInterval: ReturnType<typeof setInterval> | null = null;

  /** 指数退避基础间隔（毫秒） */
  private readonly BACKOFF_BASE_MS = 1000;
  /** 最大退避间隔（30秒） */
  private readonly BACKOFF_MAX_MS = 30000;

  /** 同步历史存储键 */
  private readonly HISTORY_STORAGE_KEY = 'sync_history';

  constructor(
    @Inject(PLATFORM_ID) private platformId: object,
    private networkMonitor: NetworkMonitorService,
    private offlineStorage: OfflineStorageService,
  ) {
    if (isPlatformBrowser(platformId)) {
      this.initializeAutoSync();
      this.loadSyncHistory();
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
          void this.syncAll();
        }
        this.syncStatusSubject.next(status.isOnline ? 'idle' : 'offline');
      });

      // 定时同步（带指数退避）
      this.autoSyncInterval = setInterval(() => {
        if (!this.networkMonitor.isOffline() && !this.isSyncing) {
          void this.syncAll();
        }
      }, config.syncInterval);
    }
  }

  // ==================== 批量同步操作 ====================

  /** 同步所有待处理操作（按优先级分批处理） */
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

    const startedAt = new Date().toISOString();
    const report: SyncReport = {
      totalOperations: 0,
      syncedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      conflictCount: 0,
      startedAt,
      completedAt: null,
      errors: [],
    };

    try {
      const operations = await this.loadPrioritizedOperations();
      report.totalOperations = operations.length;
      this.pendingCountSubject.next(operations.length);

      if (operations.length === 0) {
        report.completedAt = new Date().toISOString();
        this.syncReportSubject.next(report);
        return report;
      }

      // 按优先级分批处理
      const config = this.offlineStorage.getSyncConfig();
      const batches = this.createBatches(operations, config.batchSize);
      report.batchInfo = { totalBatches: batches.length, completedBatches: 0 };

      let completedCount = 0;
      for (const batch of batches) {
        // 检查网络质量
        if (!this.isNetworkGoodEnough(config)) {
          report.skippedCount += batch.length;
          continue;
        }

        const result = await this.processBatch(batch, config);

        report.syncedCount += result.synced;
        report.failedCount += result.failed;
        report.conflictCount += result.conflicts;
        report.errors.push(...result.errors);

        completedCount += batch.length;
        const progress = Math.round((completedCount / operations.length) * 100);
        this.syncProgressSubject.next(progress);

        if (report.batchInfo) {
          report.batchInfo.completedBatches++;
        }
      }
    } catch {
      this.syncStatusSubject.next('error');
    } finally {
      report.completedAt = new Date().toISOString();
      this.syncReportSubject.next(report);
      this.isSyncing = false;
      this.syncStatusSubject.next('idle');
      this.syncProgressSubject.next(100);

      const remaining = await this.offlineStorage.getPendingOperations();
      this.pendingCountSubject.next(remaining.length);

      // 记录同步历史
      this.recordSyncHistory(report);
    }

    return report;
  }

  /** 按优先级排序加载操作 */
  private async loadPrioritizedOperations(): Promise<PrioritizedOperation[]> {
    const operations = await this.offlineStorage.getPendingOperations();
    const priorityOrder: Record<SyncPriority, number> = { high: 0, normal: 1, low: 2 };

    const prioritized = operations.map((op) => ({
      ...op,
      priority: this.detectPriority(op),
    }));

    prioritized.sort((a, b) => {
      const pDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (pDiff !== 0) return pDiff;
      // 同优先级按创建时间排序（旧的优先）
      return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    });

    return prioritized;
  }

  /** 检测操作优先级 */
  private detectPriority(operation: OfflineOperation): SyncPriority {
    // 用户进度和测验提交为高优先级
    if (operation.tableName === 'progress' || operation.tableName === 'exam_attempt') {
      return 'high';
    }
    // 课程内容为普通优先级
    if (operation.tableName === 'courses' || operation.tableName === 'courseData') {
      return 'normal';
    }
    return 'low';
  }

  /** 将操作分批 */
  private createBatches(operations: PrioritizedOperation[], batchSize: number): PrioritizedOperation[][] {
    const batches: PrioritizedOperation[][] = [];
    for (let i = 0; i < operations.length; i += batchSize) {
      batches.push(operations.slice(i, i + batchSize));
    }
    return batches;
  }

  /** 批量处理一组操作 */
  private async processBatch(
    batch: PrioritizedOperation[],
    config: OfflineSyncConfig,
  ): Promise<{ synced: number; failed: number; conflicts: number; errors: SyncError[] }> {
    const result = { synced: 0, failed: 0, conflicts: 0, errors: [] as SyncError[] };

    if (batch.length === 1) {
      // 单个操作直接处理
      try {
        await this.syncOperation(batch[0]);
        result.synced = 1;
        await this.offlineStorage.updateOperationStatus(batch[0].id, OfflineOperationStatus.COMPLETED);
      } catch (error) {
        result.failed = 1;
        result.errors.push(this.createSyncError(batch[0], error));
        await this.handleOperationError(batch[0], error, config);
      }
      return result;
    }

    // 批量提交（多条记录一次请求）
    try {
      const batchResult = await this.batchSyncOperations(batch);
      for (let i = 0; i < batch.length; i++) {
        const op = batch[i];
        if (batchResult.successful.includes(i)) {
          result.synced++;
          await this.offlineStorage.updateOperationStatus(op.id, OfflineOperationStatus.COMPLETED);
        } else if (batchResult.conflicts.includes(i)) {
          result.conflicts++;
          result.errors.push({
            operationId: op.id,
            error: '数据冲突',
            errorType: 'conflict',
            retryCount: op.retryCount,
            timestamp: new Date().toISOString(),
          });
          await this.offlineStorage.updateOperationStatus(op.id, OfflineOperationStatus.FAILED, '数据冲突');
        } else {
          result.failed++;
          result.errors.push({
            operationId: op.id,
            error: batchResult.error?.message ?? '批量同步失败',
            errorType: 'server',
            retryCount: op.retryCount,
            timestamp: new Date().toISOString(),
          });
          await this.handleOperationError(op, batchResult.error, config);
        }
      }
    } catch (error) {
      // 整个批量请求失败，逐个处理
      for (const op of batch) {
        try {
          await this.syncOperation(op);
          result.synced++;
          await this.offlineStorage.updateOperationStatus(op.id, OfflineOperationStatus.COMPLETED);
        } catch (singleError) {
          result.failed++;
          result.errors.push(this.createSyncError(op, singleError));
          await this.handleOperationError(op, singleError, config);
        }
      }
    }

    return result;
  }

  /** 批量同步多个操作（一次 HTTP 请求） */
  private async batchSyncOperations(
    batch: PrioritizedOperation[],
  ): Promise<{
    successful: number[];
    conflicts: number[];
    error: Error | null;
  }> {
    const payload = batch.map((op) => ({
      table: op.tableName,
      recordId: op.recordId,
      type: op.type,
      data: op.data,
      timestamp: op.createdAt,
      retryCount: op.retryCount,
    }));

    const response = await fetch('/api/v1/sync/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operations: payload }),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`批量同步失败: ${response.status} ${errorText}`);
    }

    const result = await response.json() as {
      results: { index: number; status: 'success' | 'conflict' | 'failed'; error?: string }[];
    };

    const successful: number[] = [];
    const conflicts: number[] = [];

    for (const r of result.results) {
      if (r.status === 'success') successful.push(r.index);
      else if (r.status === 'conflict') conflicts.push(r.index);
    }

    return { successful, conflicts, error: null };
  }

  /** 同步单个操作 */
  private async syncOperation(operation: OfflineOperation): Promise<void> {
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

  /** 处理操作错误（含指数退避） */
  private async handleOperationError(
    operation: PrioritizedOperation,
    error: unknown,
    config: OfflineSyncConfig,
  ): Promise<void> {
    const nextRetry = operation.retryCount + 1;

    if (nextRetry < config.maxRetryAttempts) {
      // 指数退避
      const delay = Math.min(
        this.BACKOFF_BASE_MS * Math.pow(2, operation.retryCount),
        this.BACKOFF_MAX_MS,
      );

      await this.offlineStorage.updateOperationStatus(
        operation.id,
        OfflineOperationStatus.PENDING,
        error instanceof Error ? error.message : String(error),
      );

      // 更新下次重试时间
      const op = await this.offlineStorage.getData<OfflineOperation>(
        'syncQueue' as any,
        operation.id,
      );
      if (op) {
        (op as any).nextRetryAt = new Date(Date.now() + delay).toISOString();
        (op as any).retryCount = nextRetry;
        await this.offlineStorage.setData('syncQueue' as any, op);
      }
    } else {
      await this.offlineStorage.updateOperationStatus(
        operation.id,
        OfflineOperationStatus.FAILED,
        error instanceof Error ? error.message : String(error),
      );
    }
  }

  // ==================== 网络质量检查 ====================

  private isNetworkGoodEnough(config: OfflineSyncConfig): boolean {
    if (config.minimumNetworkQuality === 'any') return true;
    if (config.minimumNetworkQuality === 'wifi') return this.networkMonitor.isHighQualityNetwork();

    const status = this.networkMonitor.getCurrentStatus();
    const qualityOrder = ['slow-2g', 'slow-3g', 'fast-4g', 'fast-wifi'];
    const minIndex = qualityOrder.indexOf(config.minimumNetworkQuality);
    const currentIndex = qualityOrder.indexOf(status.quality);

    return currentIndex >= minIndex;
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

  /** 批量添加操作到队列 */
  async enqueueOperations(
    operations: { tableName: string; type: OfflineOperationType; recordId: string; data: Record<string, unknown> }[],
  ): Promise<string[]> {
    const ids: string[] = [];
    for (const op of operations) {
      const id = await this.offlineStorage.addOperation({
        ...op,
        status: OfflineOperationStatus.PENDING,
      });
      ids.push(id);
    }

    const pending = await this.offlineStorage.getPendingOperations();
    this.pendingCountSubject.next(pending.length);

    return ids;
  }

  /** 获取当前队列统计 */
  async getQueueStats(): Promise<{
    total: number;
    pending: number;
    highPriority: number;
    estimatedTimeMs: number;
  }> {
    const operations = await this.loadPrioritizedOperations();
    const highPriority = operations.filter((op) => op.priority === 'high').length;

    // 估算同步时间（每个操作约500ms）
    const config = this.offlineStorage.getSyncConfig();
    const batches = Math.ceil(operations.length / config.batchSize);
    const estimatedTimeMs = operations.length * 300; // 粗略估计

    return {
      total: operations.length,
      pending: operations.length,
      highPriority,
      estimatedTimeMs,
    };
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

  // ==================== 同步历史 ====================

  private async loadSyncHistory(): Promise<void> {
    try {
      const historyJson = localStorage.getItem(this.HISTORY_STORAGE_KEY);
      if (historyJson) {
        const history: SyncHistoryEntry[] = JSON.parse(historyJson);
        this.syncHistorySubject.next(history.slice(-20)); // 保留最近20条
      }
    } catch {
      // 忽略加载失败
    }
  }

  private async recordSyncHistory(report: SyncReport): Promise<void> {
    const duration = report.completedAt
      ? new Date(report.completedAt).getTime() - new Date(report.startedAt).getTime()
      : 0;

    const entry: SyncHistoryEntry = {
      id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
      timestamp: report.startedAt,
      totalOperations: report.totalOperations,
      syncedCount: report.syncedCount,
      failedCount: report.failedCount,
      duration,
      status:
        report.failedCount === 0 && report.totalOperations > 0
          ? 'success'
          : report.syncedCount > 0
            ? 'partial'
            : 'failure',
    };

    const current = this.syncHistorySubject.value;
    const updated = [entry, ...current].slice(0, 20);
    this.syncHistorySubject.next(updated);

    try {
      localStorage.setItem(this.HISTORY_STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // 忽略存储失败
    }
  }

  /** 清除同步历史 */
  clearHistory(): void {
    this.syncHistorySubject.next([]);
    try {
      localStorage.removeItem(this.HISTORY_STORAGE_KEY);
    } catch {
      // 忽略
    }
  }

  // ==================== 辅助方法 ====================

  private createEmptyReport(): SyncReport {
    return {
      totalOperations: 0,
      syncedCount: 0,
      failedCount: 0,
      skippedCount: 0,
      conflictCount: 0,
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
      errors: [],
    };
  }

  private createSyncError(operation: OfflineOperation, error: unknown): SyncError {
    return {
      operationId: operation.id,
      error: error instanceof Error ? error.message : String(error),
      errorType: this.categorizeError(error),
      retryCount: operation.retryCount,
      timestamp: new Date().toISOString(),
    };
  }

  /** 错误分类 */
  private categorizeError(error: unknown): SyncError['errorType'] {
    if (error instanceof TypeError || error instanceof DOMException) {
      return 'network';
    }
    if (typeof error === 'object' && error !== null && 'status' in error) {
      const status = (error as { status: number }).status;
      if (status === 409) return 'conflict';
      if (status >= 500) return 'server';
    }
    const msg = error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();
    if (msg.includes('network') || msg.includes('fetch') || msg.includes('abort')) return 'network';
    if (msg.includes('timeout') || msg.includes('time out')) return 'timeout';
    if (msg.includes('conflict')) return 'conflict';
    if (msg.includes('500') || msg.includes('server')) return 'server';
    return 'unknown';
  }

  /** 清理自动同步 */
  destroy(): void {
    if (this.autoSyncInterval) {
      clearInterval(this.autoSyncInterval);
      this.autoSyncInterval = null;
    }
  }
}
