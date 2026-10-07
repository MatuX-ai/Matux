import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';

import { OfflineStorageStats } from '../../../core/models/offline.models';
import {
  NetworkMonitorService,
  NetworkQuality,
  NetworkStatus,
} from '../../../core/services/network-monitor.service';
import { OfflineStorageService } from '../../../core/services/offline-storage.service';
import { OfflineCourseStorageService } from '../../services/offline-course-storage.service';
import { OfflineProgressStorageService } from '../../services/offline-progress-storage.service';
import { OfflineSyncService, SyncStatus } from '../../services/offline-sync.service';

@Component({
  selector: 'app-offline-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatGridListModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatDividerModule,
  ],
  templateUrl: './offline-dashboard.component.html',
  styleUrls: ['./offline-dashboard.component.scss'],
})
export class OfflineDashboardComponent implements OnInit, OnDestroy {
  /** 网络状态 */
  networkStatus: NetworkStatus | null = null;
  /** 存储统计 */
  storageStats: OfflineStorageStats | null = null;
  /** 课程缓存统计 */
  courseCacheStats: { courseCount: number; resourceCount: number; totalSize: number } | null = null;
  /** 进度同步统计 */
  progressSyncStats: { synced: number; unsynced: number; conflicts: number } | null = null;
  /** 同步状态 */
  syncStatus: SyncStatus = 'idle';
  /** 同步进度 */
  syncProgress = 0;
  /** 缓存清理中 */
  isCleaningUp = false;

  /** 订阅集合 */
  private subscriptions: Subscription[] = [];

  constructor(
    private networkMonitor: NetworkMonitorService,
    private offlineStorage: OfflineStorageService,
    private courseStorage: OfflineCourseStorageService,
    private progressStorage: OfflineProgressStorageService,
    private syncService: OfflineSyncService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.initializeDashboard();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  /**
   * 初始化仪表板
   */
  private initializeDashboard(): void {
    // 订阅网络状态变化
    this.subscriptions.push(
      this.networkMonitor.networkStatus$.subscribe((status) => {
        this.networkStatus = status;
      })
    );

    // 订阅存储统计变化
    this.subscriptions.push(
      this.offlineStorage.stats$.subscribe((stats) => {
        this.storageStats = stats;
      })
    );

    // 订阅同步状态
    this.subscriptions.push(
      this.syncService.syncStatus$.subscribe((status) => {
        this.syncStatus = status;
      })
    );

    // 订阅同步进度
    this.subscriptions.push(
      this.syncService.syncProgress$.subscribe((progress) => {
        this.syncProgress = progress;
      })
    );

    // 加载扩展统计
    this.loadExtendedStats();
  }

  private async loadExtendedStats(): Promise<void> {
    this.courseCacheStats = await this.courseStorage.getCacheStats();
    this.progressSyncStats = await this.progressStorage.getSyncStats();
  }

  /**
   * 获取网络质量描述
   */
  getQualityDescription(quality: NetworkQuality | null | undefined): string {
    if (!quality) return '网络状态未知';
    return this.networkMonitor.getQualityDescription(quality);
  }

  /**
   * 获取网络质量图标
   */
  getNetworkQualityIcon(quality: NetworkQuality | null | undefined): string {
    switch (quality) {
      case NetworkQuality.OFFLINE:
        return 'cloud_off';
      case NetworkQuality.SLOW_2G:
        return 'signal_cellular_alt_1_bar';
      case NetworkQuality.SLOW_3G:
        return 'signal_cellular_alt_2_bar';
      case NetworkQuality.FAST_4G:
        return 'signal_cellular_alt';
      case NetworkQuality.FAST_WIFI:
        return 'wifi';
      default:
        return 'help_outline';
    }
  }

  /**
   * 获取网络质量颜色
   */
  getNetworkQualityColor(quality: NetworkQuality | null | undefined): string {
    switch (quality) {
      case NetworkQuality.OFFLINE:
        return '#ef4444';
      case NetworkQuality.SLOW_2G:
        return '#f59e0b';
      case NetworkQuality.SLOW_3G:
        return '#f59e0b';
      case NetworkQuality.FAST_4G:
        return '#10b981';
      case NetworkQuality.FAST_WIFI:
        return '#3b82f6';
      default:
        return '#94a3b8';
    }
  }

  /**
   * 格式化存储大小
   */
  formatStorageSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  }

  /**
   * 获取同步状态文本
   */
  getSyncStatusText(): string {
    return this.syncService.getSyncStatusDescription();
  }

  /**
   * 是否正在同步
   */
  isSyncing(): boolean {
    return this.syncStatus === 'syncing';
  }

  /**
   * 手动刷新网络状态
   */
  refreshNetworkStatus(): void {
    this.networkMonitor.checkNetworkStatus();
  }

  /**
   * 触发同步
   */
  triggerSync(): void {
    if (this.isSyncing()) {
      this.snackBar.open('同步正在进行中，请稍候', '关闭', { duration: 2000 });
      return;
    }

    this.syncService.manualSync().then(
      (report) => {
        const total = report.totalOperations;
        const synced = report.syncedCount;
        const failed = report.failedCount;
        // 【P2 修复】字段名以 SyncReport 定义为准: conflictCount
        const conflicts = report.conflictCount ?? 0;

        if (total === 0) {
          this.snackBar.open('没有需要同步的数据', '关闭', { duration: 2000 });
          return;
        }

        const summary =
          failed === 0
            ? `同步完成：${synced} 项已上传`
            : `同步部分成功：${synced} 成功，${failed} 失败`;
        const detail = conflicts > 0 ? `, ${conflicts} 个冲突` : '';
        this.snackBar
          .open(summary + detail, failed === 0 ? '关闭' : '查看', {
            duration: 4000,
          })
          .onAction()
          .subscribe(() => {
            // 用户点击"查看"时刷新扩展统计并跳转到 sync 面板
            void this.loadExtendedStats();
          });
      },
      (error: Error) => {
        console.error('[OfflineDashboard] 手动同步失败:', error);
        this.snackBar
          .open(error?.message ?? '同步失败，请稍后重试', '重试', { duration: 5000 })
          .onAction()
          .subscribe(() => {
            this.triggerSync();
          });
      }
    );
  }

  /**
   * 清理过期缓存
   */
  async cleanupCache(): Promise<void> {
    this.isCleaningUp = true;
    try {
      await this.offlineStorage.cleanupExpiredCache();
      await this.courseStorage.cleanupExpiredCourses();
      await this.loadExtendedStats();
    } finally {
      this.isCleaningUp = false;
    }
  }

  /**
   * 获取存储类型名称
   */
  getItemTypeName(key: string): string {
    const typeNames: Record<string, string> = {
      userData: '用户数据',
      courseData: '课程数据',
      taskData: '任务数据',
      settings: '设置数据',
      cache: '缓存数据',
      syncQueue: '同步队列',
      courses: '课程缓存',
      progress: '学习进度',
      assets: '资源文件',
    };
    return typeNames[key] || key;
  }

  /**
   * 获取同步进度百分比
   */
  getSyncProgressPercent(): number {
    return Math.round(this.syncProgress);
  }
}
