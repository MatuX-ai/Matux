/**
 * 每日签到组件（P0-4）
 *
 * 三态：
 *   - idle: 摇晃的宝箱按钮（📦）
 *   - opening: 点击后 600ms 序列（盖子飞出 + 卡牌飞向 daily-tasks-widget）
 *   - done: 静态 "✓ 今日 +50 EXP 已入账 · 连续 N 天"
 *
 * 视觉锚点：放置在 welcome-section 右上角。
 *
 * @see 桌面端游戏化P0升级.md §2.4
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnInit,
  Output,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { DailyCheckinService, CheckinResult } from '../../../core/services/daily-checkin.service';
import { FeedbackFlyService } from '../../../core/services/feedback-fly.service';
import { LevelEventService } from '../../../core/services/level-event.service';
import type { DailyTask } from '../../../user/student/services/student-dashboard-data.service';

type State = 'idle' | 'opening' | 'done';

@Component({
  selector: 'app-daily-checkin',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="checkin-host" [class.is-done]="state === 'done'">
      <!-- 未签到：宝箱按钮 -->
      <button
        *ngIf="state === 'idle'"
        class="chest-btn"
        type="button"
        mat-button
        [matTooltip]="'点击领取今日奖励 +50 EXP'"
        [attr.aria-label]="'每日签到：点击领取今日奖励'"
        (click)="onCheckin()"
      >
        <span class="chest-icon" aria-hidden="true">📦</span>
        <span class="chest-label">签到</span>
      </button>

      <!-- 签到中：开启动画 -->
      <div *ngIf="state === 'opening'" class="chest-opening" aria-hidden="true">
        <span class="chest-icon opening-icon">📦</span>
        <span class="opening-text">开启中...</span>
      </div>

      <!-- 已签到：静态提示 -->
      <div
        *ngIf="state === 'done'"
        class="done-block"
        [matTooltip]="'已连续签到 ' + streakDays + ' 天'"
      >
        <span class="done-icon" aria-hidden="true">✓</span>
        <span class="done-text">
          <span class="done-primary">今日 +50 EXP 已入账</span>
          <span class="done-streak">连续 {{ streakDays }} 天</span>
        </span>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: inline-block;
      }
      .checkin-host {
        display: inline-flex;
        align-items: center;
      }
      .chest-btn {
        display: inline-flex !important;
        align-items: center;
        gap: 6px !important;
        height: 56px !important;
        padding: 0 18px !important;
        border-radius: 28px !important;
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
        color: #92400e !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        box-shadow: 0 6px 16px rgba(245, 158, 11, 0.25);
        transition:
          transform 200ms ease,
          box-shadow 200ms ease;
      }
      .chest-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 22px rgba(245, 158, 11, 0.4);
      }
      .chest-btn:active {
        transform: scale(0.96);
      }
      .chest-icon {
        font-size: 24px;
        line-height: 1;
        animation: chest-wobble 2s ease-in-out infinite;
        display: inline-block;
      }
      .chest-label {
        font-size: 14px;
      }
      @keyframes chest-wobble {
        0%, 100% { transform: rotate(-3deg); }
        50% { transform: rotate(3deg); }
      }
      .chest-opening {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        height: 56px;
        padding: 0 18px;
        border-radius: 28px;
        background: linear-gradient(135deg, #fde68a 0%, #fbbf24 100%);
        color: #92400e;
        font-weight: 700;
        font-size: 14px;
      }
      .opening-icon {
        animation: chest-open 0.6s ease-out forwards;
      }
      @keyframes chest-open {
        0% { transform: scale(1) rotate(0); }
        50% { transform: scale(1.4) rotate(20deg); }
        100% { transform: scale(0.6) rotate(45deg); opacity: 0; }
      }
      .opening-text {
        font-size: 13px;
      }
      .done-block {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 16px;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        color: #047857;
        font-size: 12px;
        line-height: 1.3;
      }
      .done-icon {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #059669;
        color: white;
        font-weight: 700;
        font-size: 13px;
      }
      .done-text {
        display: inline-flex;
        flex-direction: column;
      }
      .done-primary {
        font-weight: 700;
      }
      .done-streak {
        font-size: 10px;
        opacity: 0.85;
      }
      @media (prefers-reduced-motion: reduce) {
        .chest-icon, .opening-icon {
          animation: none !important;
        }
      }
    `,
  ],
})
export class DailyCheckinComponent implements OnInit {
  @Input() userId: string | null = null;
  @Input() candidateTasks: DailyTask[] = [];
  /** 当签到完成且有奖励卡时 emit（供 dashboard 接入飞升/追加任务） */
  @Output() checkinCompleted = new EventEmitter<CheckinResult>();

  private readonly checkinService = inject(DailyCheckinService);
  private readonly flyService = inject(FeedbackFlyService);
  private readonly levelEventService = inject(LevelEventService);
  private readonly cdr = inject(ChangeDetectorRef);

  state: State = 'idle';
  streakDays = 0;

  ngOnInit(): void {
    this.checkinService.bootstrap(this.userId, this.candidateTasks);
    this.streakDays = this.checkinService.streakDays;
    this.state = this.checkinService.isCheckedInToday() ? 'done' : 'idle';
  }

  async onCheckin(): Promise<void> {
    if (this.state !== 'idle') return;
    this.state = 'opening';
    this.cdr.markForCheck();

    // 等待 600ms 打开动画
    await new Promise((r) => setTimeout(r, 600));

    const result = this.checkinService.checkIn(this.candidateTasks);
    if (!result) {
      // 已被并发签到占用
      this.state = 'done';
      this.cdr.markForCheck();
      return;
    }

    this.streakDays = result.streak;

    // 飞升 EXP（从宝箱位置飞向状态栏）
    const chestEl = document.querySelector('.chest-opening') as HTMLElement | null;
    const expTarget = document.getElementById('exp-target');
    if (chestEl && expTarget) {
      this.flyService
        .flyNumber(chestEl, expTarget, `+${result.exp}`, '#fbbf24')
        .subscribe();
    }

    // 触发升级事件（如累计 EXP 跨级）
    const fakeUserId = this.userId;
    if (fakeUserId && result.streak) {
      // 仅示意：让 AchievementCenter 再次触发评估，逻辑仍由 LevelEventService 负责
      this.levelEventService.emitLevelUp(
        fakeUserId,
        { current: 1, title: '', exp: 0, expToNext: 0, totalExp: 0, expProgressPercent: 0 },
        { current: 1, title: '', exp: 0, expToNext: 0, totalExp: 0, expProgressPercent: 0 },
        result.exp
      );
    }

    this.state = 'done';
    this.cdr.markForCheck();
    this.checkinCompleted.emit(result);
  }
}
