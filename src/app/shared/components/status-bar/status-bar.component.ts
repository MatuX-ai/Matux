/**
 * 底部状态栏组件
 *
 * 显示应用状态信息：
 * - 在线/离线状态
 * - Python 后端运行状态
 * - 应用版本号
 *
 * 符合 PRD 第 6.5 节页面布局规范（28px 高度状态栏）
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-status-bar',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  templateUrl: './status-bar.component.html',
  styleUrls: ['./status-bar.component.scss'],
})
export class StatusBarComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private destroy$ = new Subject<void>();

  // 状态信息
  isOnline = navigator.onLine;
  isBackendRunning = false;
  backendVersion = 'Python 3.11';
  appVersion = 'v1.0.0';
  currentUser: string = '';

  ngOnInit(): void {
    // 监听网络状态
    window.addEventListener('online', () => this.isOnline = true);
    window.addEventListener('offline', () => this.isOnline = false);

    // 获取当前用户
    this.authService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        if (user) {
          this.currentUser = (user as any).nickname || user.username || '同学';
        }
      });

    // 检查后端状态（通过 Electron IPC 或 HTTP 健康检查）
    this.checkBackendStatus();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('online', () => this.isOnline = true);
    window.removeEventListener('offline', () => this.isOnline = false);
  }

  /**
   * 检查后端运行状态
   */
  private checkBackendStatus(): void {
    // 在 Electron 环境中，通过 IPC 检查
    // 在 Web 环境中，通过 HTTP 健康检查
    if (this.isElectron()) {
      this.checkElectronBackend();
    } else {
      this.checkWebBackend();
    }
  }

  /**
   * 检测是否在 Electron 环境
   */
  private isElectron(): boolean {
    return !!(window && window.process && (window.process as any).type);
  }

  /**
   * Electron 环境下的后端检查
   */
  private checkElectronBackend(): void {
    // 通过 Electron IPC 获取后端状态
    if (typeof window !== 'undefined' && (window as any).electronAPI) {
      (window as any).electronAPI
        .healthCheck()
        .then((result: any) => {
          this.isBackendRunning = result?.success || false;
          if (result?.version) {
            this.backendVersion = `Python ${result.version}`;
          }
        })
        .catch(() => {
          this.isBackendRunning = false;
        });
    } else {
      // 如果 electronAPI 未定义，默认为运行中
      this.isBackendRunning = true;
    }
  }

  /**
   * Web 环境下的后端检查
   */
  private checkWebBackend(): void {
    // 通过 HTTP 健康检查端点
    fetch('http://localhost:8000/api/v1/health')
      .then(res => {
        if (res.ok) {
          this.isBackendRunning = true;
        }
      })
      .catch(() => {
        this.isBackendRunning = false;
      });
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
    return this.isBackendRunning ? `${this.backendVersion} 运行中` : '后端未启动';
  }

  /**
   * 获取后端状态颜色类
   */
  getBackendStatusClass(): string {
    return this.isBackendRunning ? 'status-running' : 'status-stopped';
  }
}
