/**
 * 每日任务 widget - 游戏化核心
 *
 * 5 个每日任务，含稀有度、完成态、奖励积分
 * 点击完成任务后触发 +EXP 飞升动画
 *
 * @see Task 3.4 每日任务系统
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  QueryList,
  ViewChildren,
  inject,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { OfflineBonusService } from '../../../core/services/offline-bonus.service';
import { FeedbackFlyService } from '../../../core/services/feedback-fly.service';
import { SparkleBurstComponent } from '../../../shared/components/sparkle-burst/sparkle-burst.component';
import type { DailyTask } from '../services/student-dashboard-data.service';

@Component({
  selector: 'app-daily-tasks-widget',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    SparkleBurstComponent,
  ],
  template: `
    <mat-card class="tasks-widget" aria-label="每日任务">
      <div class="widget-header">
        <div class="title-group">
          <mat-icon class="title-icon">today</mat-icon>
          <h2 class="title">每日任务</h2>
          <span *ngIf="offlineBonusActive" class="bonus-chip" aria-label="离线 2 倍经验">
            ⚡ 2x
          </span>
        </div>
        <div class="progress-info">
          <span class="progress-text">{{ completedCount }} / {{ tasks.length }}</span>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
      </div>

      <div class="progress-bar-wrap">
        <mat-progress-bar
          mode="determinate"
          [value]="progressPercent"
          color="primary"
        ></mat-progress-bar>
      </div>

      <div class="tasks-list">
        <div
          *ngFor="let task of tasks; trackBy: trackByTaskId; let i = index"
          #taskItem
          class="task-item"
          [class.completed]="task.completed"
          [class.bursting]="burstingTaskId === task.id"
          [class]="'rarity-' + task.rarity"
          (click)="onTaskClick(task, taskItem)"
        >
          <!-- 左侧稀有度色条 -->
          <div class="rarity-bar"></div>

          <!-- 图标 + 内容 -->
          <div class="task-content">
            <div class="task-header">
              <mat-icon class="task-icon">{{ task.icon }}</mat-icon>
              <span class="task-title">{{ task.title }}</span>
              <span class="task-reward" *ngIf="!task.completed">
                +{{ offlineBonusActive ? offlineBonus.applyMultiplier(task.rewardExp) : task.rewardExp }} EXP
              </span>
            </div>
            <p class="task-desc">{{ task.description }}</p>
            <!-- 进度（针对 streak 类任务） -->
            <div *ngIf="task.progress && !task.completed" class="task-progress">
              <mat-progress-bar
                mode="determinate"
                [value]="(task.progress.current / task.progress.total) * 100"
              ></mat-progress-bar>
              <span class="progress-label">
                {{ task.progress.current }} / {{ task.progress.total }}
              </span>
            </div>
          </div>

          <!-- 完成 checkbox -->
          <div class="task-action">
            <div #checkboxEl class="checkbox" [class.checked]="task.completed">
              <mat-icon *ngIf="task.completed">check</mat-icon>
            </div>
          </div>

          <!-- 完成态：划过线 -->
          <div *ngIf="task.completed" class="completed-line"></div>
        </div>
      </div>

      <!-- 全部完成提示 + 长尾粒子 -->
      <div *ngIf="allCompleted" class="all-done-banner">
        <mat-icon>celebration</mat-icon>
        <span>太棒了！今天的任务全部完成 🎉</span>
      </div>

      <!-- P0-1 共享粒子层 -->
      <app-sparkle-burst
        [active]="burstActive"
        [x]="burstX"
        [y]="burstY"
        [count]="12"
        [color]="'#fbbf24'"
        [durationMs]="600"
      ></app-sparkle-burst>
    </mat-card>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .tasks-widget {
        padding: 20px;
        border: none !important;
        border-radius: var(--dash-card-radius, 20px);
        background: var(--stem-bg-surface, #ffffff);
        box-shadow: var(--stem-shadow-sm, 0 1px 3px rgba(5, 150, 105, 0.08));
      }

      .widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }

      .title-group {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .title-icon {
        color: var(--stem-primary, #059669);
      }

      .title {
        margin: 0;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 18px;
        font-weight: 700;
      }

      .bonus-chip {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        padding: 2px 8px;
        border-radius: 999px;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.5px;
        animation: bonus-chip-pulse 1.6s ease-in-out infinite;
      }

      @keyframes bonus-chip-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.08); }
      }

      .progress-info {
        display: flex;
        align-items: baseline;
        gap: 6px;
      }

      .progress-text {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 14px;
        font-weight: 700;
      }

      .progress-percent {
        color: var(--stem-success, #059669);
        font-size: 12px;
      }

      .progress-bar-wrap {
        margin-bottom: 12px;
        height: 4px;
      }

      .tasks-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .task-item {
        position: relative;
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 10px 12px;
        border-radius: 12px;
        background: var(--matux-color-background, #f1f5f9);
        cursor: pointer;
        transition:
          transform 200ms ease,
          box-shadow 200ms ease,
          background 200ms ease;
      }

      .task-item.bursting {
        animation: task-burst 600ms cubic-bezier(0.34, 1.56, 0.64, 1);
      }

      @keyframes task-burst {
        0% {
          transform: scale(1) rotate(0);
        }
        30% {
          transform: scale(1.05) rotate(2deg);
          background: rgb(251 191 36 / 18%);
        }
        60% {
          transform: scale(0.98) rotate(-1deg);
        }
        100% {
          transform: scale(1) rotate(0);
        }
      }

      @media (prefers-reduced-motion: reduce) {
        .task-item.bursting {
          animation: none;
          background: rgb(251 191 36 / 25%);
          transition: background 200ms ease;
        }
      }

      .task-item:hover:not(.completed) {
        transform: translateX(2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
      }

      .task-item.completed {
        opacity: 0.55;
        cursor: default;
      }

      .task-item.completed .task-title {
        text-decoration: line-through;
      }

      .rarity-bar {
        flex-shrink: 0;
        align-self: stretch;
        width: 4px;
        border-radius: 2px;
        background: var(--stem-rarity-common, var(--matux-color-text-disabled, #94a3b8));
      }

      .task-item.rarity-common .rarity-bar {
        background: var(--matux-color-text-disabled, #94a3b8);
      }
      .task-item.rarity-rare .rarity-bar {
        background: var(--matux-color-primary, #3b82f6);
        box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
      }
      .task-item.rarity-epic .rarity-bar {
        background: var(--stem-rarity-epic, #a855f7);
        box-shadow: 0 0 8px rgba(168, 85, 247, 0.5);
        animation: rarity-pulse 3s ease-in-out infinite;
      }
      .task-item.rarity-legendary .rarity-bar {
        background: linear-gradient(180deg, #f59e0b 0%, #fbbf24 100%);
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
        animation: rarity-pulse 2s ease-in-out infinite;
      }

      @keyframes rarity-pulse {
        0%,
        100% {
          box-shadow: 0 0 6px rgba(168, 85, 247, 0.4);
        }
        50% {
          box-shadow: 0 0 14px rgba(168, 85, 247, 0.7);
        }
      }

      .task-content {
        flex: 1;
        min-width: 0;
      }

      .task-header {
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .task-icon {
        flex-shrink: 0;
        width: 16px;
        height: 16px;
        color: var(--stem-primary, #059669);
        font-size: 16px;
      }

      .task-title {
        flex: 1;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 600;
      }

      .task-reward {
        padding: 2px 8px;
        border-radius: 10px;
        background: var(--stem-gradient-points, linear-gradient(180deg, #f59e0b 0%, #fbbf24 100%));
        color: white;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
      }

      .task-desc {
        margin: 4px 0 0 22px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
      }

      .task-progress {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 6px 0 0 22px;
      }

      .task-progress mat-progress-bar {
        flex: 1;
      }

      .progress-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
        white-space: nowrap;
      }

      .task-action {
        flex-shrink: 0;
      }

      .checkbox {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 24px;
        height: 24px;
        border: 2px solid var(--matux-color-divider, #e2e8f0);
        border-radius: 50%;
        background: white;
        transition: all 200ms ease;
      }

      .checkbox.checked {
        background: var(--stem-gradient-points, linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%));
        border-color: var(--stem-warning, #f59e0b);
        color: white;
      }

      .checkbox mat-icon {
        color: white;
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .all-done-banner {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-top: 8px;
        padding: 8px 12px;
        border-radius: 10px;
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #0ea5e9 100%));
        color: white;
        font-size: 12px;
        font-weight: 700;
        animation: all-done-glow 2s ease-in-out infinite;
      }

      @keyframes all-done-glow {
        0%,
        100% {
          box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
        }
        50% {
          box-shadow: 0 4px 16px rgba(5, 150, 105, 0.5);
        }
      }
    `,
  ],
})
export class DailyTasksWidgetComponent implements OnDestroy {
  @Input() tasks: DailyTask[] = [];
  @Output() taskCompleted = new EventEmitter<DailyTask>();

  private readonly flyService = inject(FeedbackFlyService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  /** P1-2 离线倍率状态 */
  offlineBonusActive = false;
  readonly offlineBonus = inject(OfflineBonusService);
  private offlineBonusSub = this.offlineBonus.isOffline$.subscribe((off) => {
    if (this.offlineBonusActive !== off) {
      this.offlineBonusActive = off;
      this.cdr.markForCheck();
    }
  });

  /** 触发粒子爆裂的位置（页面坐标） */
  burstActive = false;
  burstX = 0;
  burstY = 0;
  /** 当前正在播放 burst 动效的任务 id */
  burstingTaskId: string | null = null;

  @ViewChildren('checkboxEl') checkboxRefs!: QueryList<ElementRef<HTMLDivElement>>;

  get completedCount(): number {
    return this.tasks.filter((t) => t.completed).length;
  }

  get progressPercent(): number {
    if (this.tasks.length === 0) return 0;
    return Math.round((this.completedCount / this.tasks.length) * 100);
  }

  get allCompleted(): boolean {
    return this.tasks.length > 0 && this.completedCount === this.tasks.length;
  }

  onTaskClick(task: DailyTask, taskItemEl?: HTMLElement): void {
    if (task.completed) return;

    // 1) 视觉 burst：粒子 + 卡片缩放回弹
    const checkboxEl = this.findCheckboxEl(task.id);
    const target = checkboxEl ?? taskItemEl;
    if (target) {
      const rect = target.getBoundingClientRect();
      this.burstX = rect.left + rect.width / 2;
      this.burstY = rect.top + rect.height / 2;
      this.burstActive = false;
      this.cdr.markForCheck();
      // 强制下一帧重置 + 激活，确保 sparkle-burst 重播
      setTimeout(() => {
        this.burstActive = true;
        this.burstingTaskId = task.id;
        this.cdr.markForCheck();
        setTimeout(() => {
          this.burstActive = false;
          this.burstingTaskId = null;
          this.cdr.markForCheck();
        }, 700);
      }, 16);
    }

    // 2) flyNumber：从源元素飞到状态栏 EXP 锚点（P1-2 应用离线倍率）
    if (target) {
      const expTarget = document.getElementById('exp-target');
      const finalExp = this.offlineBonus.applyMultiplier(task.rewardExp);
      const color = this.offlineBonus.isCurrentlyOffline() ? '#f59e0b' : '#fbbf24';
      this.flyService
        .flyNumber(target, expTarget ?? target, `+${finalExp}`, color)
        .pipe(takeUntil(this.destroy$))
        .subscribe();
      // 离线时累积离线 EXP（供 banner 显示「累计 EXP 待同步」）
      if (this.offlineBonus.isCurrentlyOffline()) {
        this.offlineBonus.accumulateOfflineExp(finalExp);
      }
    }

    // 3) 业务回调
    this.taskCompleted.emit(task);
  }

  private findCheckboxEl(taskId: string): HTMLElement | null {
    // 通过任务列表索引反查；fallback 到 taskItem 引用
    const idx = this.tasks.findIndex((t) => t.id === taskId);
    if (idx < 0) return null;
    const ref = this.checkboxRefs?.toArray()[idx];
    return ref?.nativeElement ?? null;
  }

  trackByTaskId(index: number, task: DailyTask): string {
    return task.id;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.offlineBonusSub?.unsubscribe();
  }
}
