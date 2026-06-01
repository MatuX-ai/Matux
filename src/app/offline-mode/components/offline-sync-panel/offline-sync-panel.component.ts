/**
 * 离线同步状态面板组件
 *
 * 展示同步状态、待同步操作数、同步进度，提供手动同步按钮
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';

import { OfflineSyncService, SyncReport, SyncStatus } from '../../services/offline-sync.service';

@Component({
  selector: 'app-offline-sync-panel',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  template: `
    <mat-card class="sync-panel-card">
      <mat-card-header>
        <mat-icon mat-card-avatar>{{ getStatusIcon(syncService.syncStatus$ | async) }}</mat-icon>
        <mat-card-title>数据同步</mat-card-title>
        <mat-card-subtitle>{{ syncService.getSyncStatusDescription() }}</mat-card-subtitle>
      </mat-card-header>

      <mat-card-content>
        <!-- 待同步数量 -->
        @if (syncService.pendingCount$ | async; as pendingCount) {
          @if (pendingCount > 0) {
            <div class="sync-info">
              <mat-icon>pending_actions</mat-icon>
              <span>{{ pendingCount }} 个操作待同步</span>
            </div>
          }
        }

        <!-- 同步进度 -->
        <mat-progress-bar
          *ngIf="(syncService.syncStatus$ | async) === 'syncing'"
          mode="determinate"
          [value]="syncService.syncProgress$ | async">
        </mat-progress-bar>

        <!-- 同步报告 -->
        <div *ngIf="syncService.syncReport$ | async as report" class="sync-report">
          <div class="report-row" *ngIf="report.totalOperations > 0">
            <span>已同步: {{ report.syncedCount }}/{{ report.totalOperations }}</span>
            <span *ngIf="report.failedCount > 0" class="failed">失败: {{ report.failedCount }}</span>
          </div>
        </div>

        <!-- 手动同步按钮 -->
        <button mat-raised-button color="primary"
                (click)="manualSync()"
                [disabled]="(syncService.syncStatus$ | async) === 'syncing' || (syncService.syncStatus$ | async) === 'offline'">
          <mat-icon>sync</mat-icon> 立即同步
        </button>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .sync-panel-card { margin: 16px; }
    .sync-info { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #f59e0b; }
    .sync-report { margin: 12px 0; }
    .report-row { display: flex; align-items: center; gap: 16px; font-size: 14px; }
    .failed { color: #ef4444; }
  `],
})
export class OfflineSyncPanelComponent implements OnInit {
  constructor(
    public syncService: OfflineSyncService,
    private snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    // 触发初始同步检查
    void this.syncService.syncAll();
  }

  async manualSync(): Promise<void> {
    const report = await this.syncService.manualSync();
    if (report.failedCount > 0) {
      this.snackBar.open(`${report.failedCount} 个操作同步失败`, '关闭', { duration: 3000 });
    } else if (report.syncedCount > 0) {
      this.snackBar.open(`${report.syncedCount} 个操作同步成功`, '关闭', { duration: 2000 });
    } else {
      this.snackBar.open('所有数据已是最新', '关闭', { duration: 2000 });
    }
  }

  getStatusIcon(status: SyncStatus | null): string {
    switch (status) {
      case 'syncing': return 'sync';
      case 'error': return 'error_outline';
      case 'offline': return 'cloud_off';
      default: return 'cloud_done';
    }
  }
}