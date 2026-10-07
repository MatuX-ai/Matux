/**
 * 学生顶部状态栏组件 - GameStatsBar
 *
 * 显示学习端用户的核心游戏化指标（积分/等级/连续天数）
 * 位于 dashboard 顶部，用于快速查看个人状态
 *
 * @see Task 4.4 顶部状态栏
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';

import type {
  DashboardSnapshot,
  UserLevel,
} from '../../../user/student/services/student-dashboard-data.service';

@Component({
  selector: 'app-student-status-bar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="status-bar" *ngIf="snapshot" role="navigation" aria-label="学习状态栏">
      <!-- 左侧：核心指标 -->
      <div class="bar-left">
        <!-- 连续打卡 -->
        <button
          class="metric-item streak"
          mat-button
          [matTooltip]="'连续打卡 ' + streakDays + ' 天'"
          (click)="navigateTo('/user/achievements')"
        >
          <span class="metric-icon">🔥</span>
          <div class="metric-content">
            <span class="metric-value">{{ streakDays }}</span>
            <span class="metric-unit">天</span>
          </div>
        </button>

        <!-- 等级 -->
        <button
          class="metric-item level"
          mat-button
          [matTooltip]="'等级 ' + level.current + ' · ' + level.title"
          (click)="navigateTo('/user/profile')"
        >
          <div class="level-badge-mini">
            <span class="level-num">Lv.{{ level.current }}</span>
          </div>
          <div class="metric-content">
            <span class="metric-value">{{ level.title }}</span>
            <span class="metric-unit">{{ level.exp }} / {{ level.expToNext }}</span>
          </div>
        </button>

        <!-- 积分 -->
        <button
          class="metric-item points"
          mat-button
          [matTooltip]="'总积分 ' + totalPoints + ' · 本周 +' + weeklyPoints"
          (click)="navigateTo('/user/achievements')"
        >
          <mat-icon class="metric-mat-icon">bolt</mat-icon>
          <div class="metric-content">
            <span class="metric-value">{{ totalPoints }}</span>
            <span class="metric-unit">EXP</span>
          </div>
          <span class="weekly-trend" *ngIf="weeklyPoints > 0"> ↑ {{ weeklyPoints }} </span>
        </button>
      </div>

      <!-- 右侧：快捷操作 -->
      <div class="bar-right">
        <button
          class="icon-btn"
          mat-icon-button
          matTooltip="通知"
          (click)="navigateTo('/notifications')"
        >
          <mat-icon>notifications</mat-icon>
          <span class="badge" *ngIf="notificationCount > 0">{{ notificationCount }}</span>
        </button>
        <button
          class="icon-btn"
          mat-icon-button
          matTooltip="设置"
          (click)="navigateTo('/settings')"
        >
          <mat-icon>settings</mat-icon>
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: var(--stem-statusbar-height, 48px);
        padding: 0 16px;
        background: var(--stem-statusbar-bg, #ffffff);
        border-bottom: var(--stem-statusbar-border, 1px solid #e7e5e4);
        box-shadow: 0 1px 0 rgba(0, 0, 0, 0.04);
      }

      .bar-left,
      .bar-right {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .metric-item {
        display: inline-flex !important;
        align-items: center;
        gap: 6px;
        min-width: 0 !important;
        height: 36px !important;
        padding: 0 10px !important;
        border-radius: 18px !important;
        color: var(--matux-color-text-primary, #1c1917) !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        transition: background 200ms ease;
      }

      .metric-item:hover {
        background: var(--matux-color-background, #f1f5f9) !important;
      }

      .metric-icon {
        font-size: 18px;
        line-height: 1;
      }

      .metric-mat-icon {
        width: 18px !important;
        height: 18px !important;
        color: var(--stem-warning-dark, #b45309);
        font-size: 18px !important;
      }

      .metric-content {
        display: flex;
        align-items: baseline;
        gap: 2px;
      }

      .metric-value {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 14px;
        font-weight: 700;
      }

      .metric-unit {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .streak .metric-value {
        color: var(--stem-streak-fire, #ef4444);
      }

      .points .metric-value {
        color: var(--stem-warning-dark, #b45309);
      }

      .level-badge-mini {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #10b981 100%));
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.3);
        color: white;
      }

      .level-num {
        font-size: 9px;
        font-weight: 700;
      }

      .weekly-trend {
        margin-left: 2px;
        padding: 1px 5px;
        border-radius: 8px;
        background: var(--stem-success, #059669);
        color: white;
        font-size: 9px;
        font-weight: 700;
      }

      .icon-btn {
        position: relative;
        width: 36px !important;
        height: 36px !important;
        padding: 0 !important;
        color: var(--matux-color-text-secondary, #57534e) !important;
      }

      .icon-btn mat-icon {
        width: 20px;
        height: 20px;
        font-size: 20px;
      }

      .badge {
        position: absolute;
        top: 4px;
        right: 4px;
        min-width: 16px;
        height: 16px;
        padding: 0 4px;
        border-radius: 8px;
        background: var(--stem-error, #ef4444);
        color: white;
        font-size: 10px;
        font-weight: 700;
        line-height: 16px;
        text-align: center;
      }

      @media (width <= 768px) {
        .metric-unit,
        .weekly-trend {
          display: none;
        }
        .status-bar {
          padding: 0 12px;
        }
      }
    `,
  ],
})
export class StudentStatusBarComponent {
  private router = inject(Router);

  @Input() snapshot: DashboardSnapshot | null = null;
  @Input() notificationCount = 0;
  @Output() navigate = new EventEmitter<string>();

  get level(): UserLevel {
    return (
      this.snapshot?.level ?? {
        current: 1,
        title: '初学者',
        exp: 0,
        expToNext: 100,
        totalExp: 0,
        expProgressPercent: 0,
      }
    );
  }

  get streakDays(): number {
    return this.snapshot?.weeklyStats?.streakDays ?? 0;
  }

  get totalPoints(): number {
    return this.snapshot?.points?.total ?? 0;
  }

  get weeklyPoints(): number {
    return this.snapshot?.points?.weeklyEarned ?? 0;
  }

  navigateTo(path: string): void {
    this.navigate.emit(path);
    void this.router.navigate([path]);
  }
}
