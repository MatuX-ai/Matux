import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';

import {
  NetworkMonitorService,
  NetworkQuality,
} from '../../../core/services/network-monitor.service';

@Component({
  selector: 'app-network-status-indicator',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatTooltipModule],
  templateUrl: './network-status-indicator.component.html',
  styleUrls: ['./network-status-indicator.component.scss'],
})
export class NetworkStatusIndicatorComponent implements OnInit, OnDestroy {
  /** 当前网络状态 */
  networkStatus: any;
  /** 订阅集合 */
  private subscriptions: Subscription[] = [];

  constructor(private networkMonitor: NetworkMonitorService) {}

  ngOnInit(): void {
    this.initializeIndicator();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }

  /**
   * 初始化指示器
   */
  private initializeIndicator(): void {
    // 订阅网络状态变化
    this.subscriptions.push(
      this.networkMonitor.networkStatus$.subscribe((status) => {
        this.networkStatus = status;
      })
    );
  }

  /**
   * 获取网络状态图标
   */
  getStatusIcon(): string {
    if (!this.networkStatus?.isOnline) {
      return 'cloud_off';
    }

    switch (this.networkStatus?.quality) {
      case NetworkQuality.SLOW_2G:
        return 'signal_cellular_alt_1_bar';
      case NetworkQuality.SLOW_3G:
        return 'signal_cellular_alt_2_bar';
      case NetworkQuality.FAST_4G:
        return 'signal_cellular_alt';
      case NetworkQuality.FAST_WIFI:
        return 'wifi';
      default:
        return 'cloud';
    }
  }

  /**
   * 获取网络状态颜色
   */
  getStatusColor(): string {
    if (!this.networkStatus?.isOnline) {
      return 'offline';
    }

    switch (this.networkStatus?.quality) {
      case NetworkQuality.SLOW_2G:
        return 'very-slow';
      case NetworkQuality.SLOW_3G:
        return 'slow';
      case NetworkQuality.FAST_4G:
        return 'good';
      case NetworkQuality.FAST_WIFI:
        return 'excellent';
      default:
        return 'unknown';
    }
  }

  /**
   * 获取状态描述文本
   */
  getStatusText(): string {
    if (!this.networkStatus?.isOnline) {
      return '离线模式';
    }

    return this.networkMonitor.getQualityDescription(this.networkStatus.quality);
  }

  /**
   * 获取详细状态信息
   */
  getDetailedStatus(): string {
    if (!this.networkStatus) return '状态未知';

    const parts: string[] = [];

    if (this.networkStatus.isOnline) {
      parts.push('在线');
      parts.push(this.networkMonitor.getQualityDescription(this.networkStatus.quality));

      if (this.networkStatus.rtt) {
        parts.push(`延迟: ${this.networkStatus.rtt}ms`);
      }

      if (this.networkStatus.downlink) {
        parts.push(`速度: ${this.networkStatus.downlink}Mbps`);
      }
    } else {
      parts.push('离线');
    }

    return parts.join(' • ');
  }

  /**
   * 刷新网络状态
   */
  refreshStatus(): void {
    this.networkMonitor.checkNetworkStatus();
  }

  /**
   * 检查是否为低质量网络
   */
  isLowQualityNetwork(): boolean {
    return this.networkMonitor.isLowQualityNetwork();
  }
}
