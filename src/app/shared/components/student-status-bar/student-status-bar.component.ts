/**
 * 学生顶部状态栏组件 - GameStatsBar（P1-2 增强：离线 2x 角标）
 *
 * 显示学习端用户的核心游戏化指标（积分/等级/连续天数）
 * 位于 dashboard 顶部，用于快速查看个人状态
 *
 * P1-2 增强：
 * - 订阅 OfflineBonusService，离线时给 EXP 按钮加 `bonus-2x` class
 * - 显示 `2x` 角标 + 橙色边框光晕动画
 *
 * @see Task 4.4 顶部状态栏
 * @see 桌面端游戏化P1升级 §2.2
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  inject,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { OfflineBonusService } from '../../../core/services/offline-bonus.service';
import { FeedbackFlyService } from '../../../core/services/feedback-fly.service';
import { LevelTitleService } from '../../../core/services/level-title.service';
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
          [matTooltip]="
            '等级 ' + level.current + ' · ' + levelTitle + (nextHint ? ' · ' + nextHint : '')
          "
          (click)="navigateTo('/user/profile')"
        >
          <div
            class="level-badge-mini"
            [style.background]="tierGradient"
            [style.box-shadow]="'0 0 0 2px ' + tierColor"
          >
            <span class="level-num">Lv.{{ level.current }}</span>
          </div>
          <div class="metric-content">
            <span class="metric-value">{{ levelTitle }}</span>
            <span class="metric-unit" *ngIf="nextHint">{{ nextHint }}</span>
          </div>
        </button>

        <!-- 积分（P0-1 飞升接收端：#exp-target 锚点） -->
        <button
          id="exp-target"
          class="metric-item points"
          [class.pulse]="pulseActive"
          [class.bonus-2x]="bonusActive"
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
          <span class="bonus-badge" *ngIf="bonusActive" aria-label="离线 2 倍经验">2x</span>
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

      .points.pulse {
        animation: exp-pulse 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
      }

      @keyframes exp-pulse {
        0% {
          transform: scale(1);
          box-shadow: 0 0 0 0 rgb(245 158 11 / 0%);
        }
        30% {
          transform: scale(1.18);
          box-shadow: 0 0 0 6px rgb(245 158 11 / 35%);
        }
        100% {
          transform: scale(1);
          box-shadow: 0 0 0 0 rgb(245 158 11 / 0%);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .points.pulse {
          animation: none;
          box-shadow: 0 0 0 4px rgb(245 158 11 / 25%);
          transition: box-shadow 200ms ease;
        }
      }

      /* P1-2 离线 2x 加成样式 */
      .points.bonus-2x {
        outline: 2px solid var(--stem-warning, #f59e0b);
        outline-offset: 1px;
        animation: bonus-glow 1.8s ease-in-out infinite;
      }

      .bonus-badge {
        margin-left: 2px;
        padding: 1px 5px;
        border-radius: 8px;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        font-size: 9px;
        font-weight: 800;
        line-height: 1.4;
        letter-spacing: 0.5px;
      }

      @keyframes bonus-glow {
        0%,
        100% {
          box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5);
        }
        50% {
          box-shadow: 0 0 0 5px rgba(245, 158, 11, 0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .points.bonus-2x {
          animation: none;
          outline: 2px solid #f59e0b;
        }
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
export class StudentStatusBarComponent implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly flyService = inject(FeedbackFlyService);
  private readonly levelTitleService = inject(LevelTitleService);
  private readonly offlineBonus = inject(OfflineBonusService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private bonusSub: Subscription | null = null;

  @Input() snapshot: DashboardSnapshot | null = null;
  @Input() notificationCount = 0;
  @Output() navigate = new EventEmitter<string>();

  /** 飞升到达时 600ms 闪烁 */
  pulseActive = false;
  private pulseTimer: ReturnType<typeof setTimeout> | null = null;

  /** P1-2 离线 2x 加成角标状态 */
  bonusActive = false;

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

  get levelTitle(): string {
    const entry = this.levelTitleService.getTitleByLevel(this.level.current);
    return entry ? this.fallbackTitle(entry.level) : this.level.title;
  }

  get tierColor(): string {
    const entry = this.levelTitleService.getTitleByLevel(this.level.current);
    return entry ? this.levelTitleService.getTierColor(entry.tier) : '#b45309';
  }

  get tierGradient(): string {
    return `linear-gradient(135deg, ${this.tierColor} 0%, ${this.tierColor}cc 100%)`;
  }

  get nextHint(): string {
    const entry = this.levelTitleService.getTitleByLevel(this.level.current);
    if (!entry) return '';
    if (this.levelTitleService.isMaxLevel(this.level.current)) return 'MAX';
    return `${this.level.exp} / ${this.level.expToNext}`;
  }

  private fallbackTitle(level: number): string {
    const FALLBACK: Record<number, string> = {
      1: '好奇宝宝',
      2: '编程新手',
      3: '代码学徒',
      4: '循环骑士',
      5: '函数巫师',
      6: '算法工匠',
      7: '数据炼金师',
      8: '架构大师',
      9: 'AI 协作者',
      10: '元宇宙创世者',
    };
    return FALLBACK[level] ?? `Lv.${level}`;
  }

  ngOnInit(): void {
    // 订阅飞升命中事件，命中时给 EXP 按钮 600ms 脉冲动画
    this.flyService.hit$.pipe(takeUntil(this.destroy$)).subscribe((event) => {
      if (event?.target?.id === 'exp-target' || event?.target === this.expAnchorEl) {
        this.triggerPulse();
      } else if (!event?.target) {
        this.triggerPulse();
      }
    });

    // P1-2：订阅离线状态变化，更新 bonusActive
    this.bonusSub = this.offlineBonus.isOffline$.subscribe((off) => {
      if (this.bonusActive !== off) {
        this.bonusActive = off;
        this.cdr.markForCheck();
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.pulseTimer) clearTimeout(this.pulseTimer);
    this.bonusSub?.unsubscribe();
  }

  private get expAnchorEl(): HTMLElement | null {
    return document.getElementById('exp-target');
  }

  private triggerPulse(): void {
    this.pulseActive = false;
    this.cdr.markForCheck();
    setTimeout(() => {
      this.pulseActive = true;
      this.cdr.markForCheck();
      if (this.pulseTimer) clearTimeout(this.pulseTimer);
      this.pulseTimer = setTimeout(() => {
        this.pulseActive = false;
        this.cdr.markForCheck();
      }, 650);
    }, 16);
  }

  navigateTo(path: string): void {
    this.navigate.emit(path);
    void this.router.navigate([path]);
  }
}
