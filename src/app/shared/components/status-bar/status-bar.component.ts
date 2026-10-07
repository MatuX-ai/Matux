/* eslint-disable @typescript-eslint/explicit-function-return-type */
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
import { filter, map, pairwise } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import { ModuleStatusService, TierGroupStatus } from '../../../core/services/module-status.service';

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
  // 【P0 修复】三态后端状态：unknown 区分 healthy/unhealthy，
  //   避免初次加载时（fetchHealth 还没回来）被误判为「后端未启动」。
  backendStatus: 'unknown' | 'healthy' | 'unhealthy' = 'unknown';
  backendVersion = 'Python 3.12';
  appVersion = 'v1.0.0';
  currentUser: string = '';

  /** 便捷派生属性：模板里 isBackendRunning 仍然可读，但语义仅在 healthy 时为 true */
  get isBackendRunning(): boolean {
    return this.backendStatus === 'healthy';
  }

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

    // 【P0 修复】主动触发一次健康检查，让状态尽快从「检测中」跳到「运行中」。
    //   避免用户在路由切换时看到长时间的「后端检测中…」占位。
    this.moduleStatusService.fetchHealth();

    // 获取当前用户
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      if (user) {
        this.currentUser = (user as AppUser).nickname ?? user.username ?? '同学';
      }
    });

    // 订阅模块状态
    // 【P0 修复】跳过 BehaviorSubject 的初始 false（未检测时），
    //   只有当 healthy$ 有过一次“状态变化”才更新 UI，避免初次订阅被
    //   初始默认值 false 误判为「后端未启动」。
    this.moduleStatusService.healthy$
      .pipe(
        pairwise(),
        filter(([prev, curr]) => prev !== curr),
        map(([, curr]) => curr),
        takeUntil(this.destroy$)
      )
      .subscribe((healthy) => {
        // 【P0 修复】保留三态映射：healthy → 'healthy' / false → 'unhealthy'。
        this.backendStatus = healthy ? 'healthy' : 'unhealthy';
      });

    this.moduleStatusService.tierGroups$.pipe(takeUntil(this.destroy$)).subscribe((groups) => {
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
   * 【P0 修复】unknown → 「检测中…」；unhealthy → 「后端未启动」；healthy → 模块摘要 / 运行中
   */
  getBackendStatusText(): string {
    if (this.backendStatus === 'unknown') return '后端检测中…';
    if (this.backendStatus === 'unhealthy') return '后端未启动';
    if (this.moduleSummaryText) return this.moduleSummaryText;
    return `${this.backendVersion} 运行中`;
  }

  /**
   * 获取后端状态颜色类
   * 【P0 修复】unknown → status-checking（中性灰），区别于 healthy / unhealthy
   */
  getBackendStatusClass(): string {
    if (this.backendStatus === 'unknown') return 'status-checking';
    return this.backendStatus === 'healthy' ? 'status-running' : 'status-stopped';
  }

  /**
   * 【P0 修复】后端状态图标 — 三态
   */
  backendIcon(): string {
    if (this.backendStatus === 'unknown') return 'sync';
    if (this.backendStatus === 'healthy') return 'check_circle';
    return 'error';
  }

  /**
   * 【P0 修复】后端状态 tooltip — 三态
   */
  backendTooltip(): string {
    if (this.backendStatus === 'unknown') return '后端状态检测中…';
    if (this.backendStatus === 'healthy') return 'Python 后端运行正常';
    return '后端未启动，点击重试';
  }

  /**
   * 【P3-4 修复】手动重新检查后端连接 — 用户点击“后端未启动”区域时调用
   * 原逻辑仅靠 ModuleStatusService 的 30s 间隔轮询，路由切换时会引入状态闪烁。
   * 这里提供手动重试入口，让 UI 能立即重新触发 fetchHealth。
   */
  onRefreshBackend(): void {
    this.moduleStatusService.fetchHealth();
  }
}
