import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';

import { OfflineStorageStats } from '../../../core/models/offline.models';
import {
  NetworkMonitorService,
  NetworkQuality,
  NetworkStatus,
} from '../../../core/services/network-monitor.service';
import { OfflineStorageService } from '../../../core/services/offline-storage.service';

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
  /** 订阅集合 */
  private subscriptions: Subscription[] = [];

  constructor(
    private networkMonitor: NetworkMonitorService,
    private offlineStorage: OfflineStorageService
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
        return '#f44336'; // 红色
      case NetworkQuality.SLOW_2G:
        return '#ff9800'; // 橙色
      case NetworkQuality.SLOW_3G:
        return '#ffc107'; // 黄色
      case NetworkQuality.FAST_4G:
        return '#4caf50'; // 绿色
      case NetworkQuality.FAST_WIFI:
        return '#2196f3'; // 蓝色
      default:
        return '#9e9e9e'; // 灰色
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
   * 手动刷新网络状态
   */
  refreshNetworkStatus(): void {
    this.networkMonitor.checkNetworkStatus();
  }

  /**
   * 清理过期缓存
   */
  cleanupCache(): void {
    this.offlineStorage
      .cleanupExpiredCache()
      .then(() => {})
      .catch(() => {});
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
    };
    return typeNames[key] || key;
  }
}
