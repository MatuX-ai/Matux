/**
 * 底部状态栏组件
 *
 * 显示应用状态信息：
 * - 在线/离线状态
 * - Python 后端运行状态
 * - 模块 Tier 分组状态（核心/AI/扩展/实验）
 * - 应用版本号
 *
 * 符合 PRD 第 6.5 节页面布局规范（28px 高度状态栏）
 */

import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject, takeUntil } from 'rxjs';

import { AuthService } from '../../../core/services/auth.service';
import {
  ModuleStatusService,
  TierGroupStatus,
} from '../../../core/services/module-status.service';

/** 用户信息接口 */
interface AppUser {
  nickname?: string;
  username?: string;
}

@Component({
  selector: 'app-status-bar',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  templateUrl: './status-bar.component.html',
  styleUrls: ['./status-bar.component.scss'],
})
export class StatusBarComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private moduleStatusService = inject(ModuleStatusService);
  private destroy$ = new Subject<void>();

  // 基础状态
  isOnline = navigator.onLine;
  isBackendRunning = false;
  backendVersion = 'Python 3.12';
  appVersion = 'v1.0.0';
  currentUser: string = '';

  // 模块状态（懒加载架构）
  tierGroups: TierGroupStatus[] = [];
  moduleSummaryText = '';

  // 在线/离线事件处理器引用（便于移除）
  private onlineHandler = () => (this.isOnline = true);
  private offlineHandler = () => (this.isOnline = false);

  ngOnInit(): void {
    // 监听网络状态
    window.addEventListener('online', this.onlineHandler);
    window.addEventListener('offline', this.offlineHandler);

    // 获取当前用户
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      if (user) {
        this.currentUser = (user as AppUser).nickname ?? user.username ?? '同学';
      }
    });

    // 订阅模块状态
    this.moduleStatusService.healthy$
      .pipe(takeUntil(this.destroy$))
      .subscribe((healthy) => {
        this.isBackendRunning = healthy;
      });

    this.moduleStatusService.tierGroups$
      .pipe(takeUntil(this.destroy$))
      .subscribe((groups) => {
        this.tierGroups = groups;
        this.updateSummaryText();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('online', this.onlineHandler);
    window.removeEventListener('offline', this.offlineHandler);
  }

  /**
   * 更新摘要文本
   */
  private updateSummaryText(): void {
    if (this.tierGroups.length === 0) {
      this.moduleSummaryText = '';
      return;
    }
    const totalActive = this.tierGroups.reduce((s, g) => s + g.active, 0);
    const totalAll = this.tierGroups.reduce((s, g) => s + g.total, 0);
    this.moduleSummaryText = `${totalActive}/${totalAll} 模块`;
  }

  /**
   * 获取 Tier 分组 tooltip
   */
  getTierTooltip(group: TierGroupStatus): string {
    return `${group.label}模块: ${group.active}/${group.total} 已激活`;
  }

  /**
   * 获取 Tier 分组图标
   */
  getTierIcon(group: TierGroupStatus): string {
    if (group.active === group.total && group.total > 0) return 'check_circle';
    if (group.active > 0) return 'pending';
    return 'radio_button_unchecked';
  }

  /**
   * 获取在线状态文本
   */
  getOnlineStatusText(): string {
    return this.isOnline ? '在线' : '离线';
  }

  /**
   * 获取在线状态图标
   */
  getOnlineStatusIcon(): string {
    return this.isOnline ? 'cloud_done' : 'cloud_off';
  }

  /**
   * 获取在线状态颜色类
   */
  getOnlineStatusClass(): string {
    return this.isOnline ? 'status-online' : 'status-offline';
  }

  /**
   * 获取后端状态文本
   */
  getBackendStatusText(): string {
    if (!this.isBackendRunning) return '后端未启动';
    if (this.moduleSummaryText) return this.moduleSummaryText;
    return `${this.backendVersion} 运行中`;
  }

  /**
   * 获取后端状态颜色类
   */
  getBackendStatusClass(): string {
    return this.isBackendRunning ? 'status-running' : 'status-stopped';
  }
}
