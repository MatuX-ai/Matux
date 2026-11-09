/**
 * 每周排行榜 widget（P1-1：赛季增强版）
 *
 * 显示：
 * - 头部：赛季名 + 倒计时徽章
 * - top 5 同学，本周积分变化、排名升降
 * - 当前用户行：额外显示「距上一名还差 N EXP」+ 我行额外信息
 * - 右上角：赛季终奖按钮 → 弹出 3 档奖励卡
 *
 * @see Task 3.6 排行榜 + 桌面端游戏化P1升级 §2.1
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  inject,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Subscription, interval } from 'rxjs';

import {
  SeasonReward,
  SeasonService,
  TimeRemaining,
} from '../../../core/services/season.service';
import type { LeaderboardEntry } from '../services/student-dashboard-data.service';

@Component({
  selector: 'app-weekly-leaderboard-widget',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule],
  template: `
    <mat-card class="leaderboard-widget" aria-label="每周排行榜">
      <!-- 头部：赛季名 + 倒计时 + 终奖按钮 -->
      <div class="widget-header">
        <div class="title-group">
          <mat-icon class="title-icon">leaderboard</mat-icon>
          <h2 class="title">本周排行榜</h2>
        </div>
        <div class="header-right">
          <span class="season-tag" [attr.aria-label]="ariaSeason">
            <span class="season-emoji">{{ seasonEmoji }}</span>
            <span class="season-name">{{ seasonName }}</span>
            <span class="season-divider">·</span>
            <span class="season-remaining">剩余 {{ remainingDays }} 天</span>
          </span>
          <button
            type="button"
            class="reward-btn"
            (click)="toggleRewards()"
            [attr.aria-expanded]="showRewards"
            aria-label="查看赛季终奖"
          >
            <span class="reward-icon">🏆</span>
          </button>
        </div>
      </div>

      <!-- 终奖预览（折叠） -->
      <div class="reward-strip" *ngIf="showRewards" [@.disabled]="false">
        <div
          class="reward-card"
          *ngFor="let r of rewards; trackBy: trackByRank"
          [style.background]="'linear-gradient(135deg, ' + r.gradient[0] + ' 0%, ' + r.gradient[1] + ' 100%)'"
        >
          <div class="reward-badge">{{ r.badge }}</div>
          <div class="reward-info">
            <div class="reward-title">{{ r.title }}</div>
            <div class="reward-range">Top {{ r.rankRange }}</div>
          </div>
          <div class="reward-exp">+{{ r.exp }} EXP</div>
        </div>
      </div>

      <!-- top 5 列表 -->
      <div class="leaderboard-list">
        <div
          *ngFor="let entry of entries; trackBy: trackByUserId"
          class="lb-entry"
          [class.is-me]="entry.isCurrentUser"
          [class]="'rank-' + entry.rank"
        >
          <!-- 排名 -->
          <div class="rank-cell">
            <span class="rank-medal" *ngIf="entry.rank <= 3">
              {{ entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉' }}
            </span>
            <span class="rank-number" *ngIf="entry.rank > 3">{{ entry.rank }}</span>
          </div>

          <!-- 头像 -->
          <div class="avatar-cell">
            <div class="avatar" [class]="'rank-' + entry.rank">
              {{ entry.username.slice(0, 1) }}
            </div>
            <span *ngIf="entry.isCurrentUser" class="me-marker">👤</span>
          </div>

          <!-- 姓名 + 积分 -->
          <div class="info-cell">
            <div class="username">{{ entry.username }}</div>
            <div class="points">{{ entry.totalExp }} EXP</div>
          </div>

          <!-- 变化 -->
          <div class="change-cell">
            <div class="weekly-change">
              <mat-icon [class.up]="entry.weeklyChange > 0" [class.down]="entry.weeklyChange < 0">
                {{
                  entry.weeklyChange > 0
                    ? 'trending_up'
                    : entry.weeklyChange < 0
                      ? 'trending_down'
                      : 'trending_flat'
                }}
              </mat-icon>
              <span class="change-num">+{{ entry.weeklyChange }}</span>
            </div>
            <div
              *ngIf="entry.rankChange !== 0"
              class="rank-change"
              [class.up]="entry.rankChange > 0"
              [class.down]="entry.rankChange < 0"
            >
              {{ entry.rankChange > 0 ? '↑' : '↓'
              }}{{ entry.rankChange > 0 ? entry.rankChange : -entry.rankChange }}
            </div>
          </div>

          <!-- 当前用户：距上一名差距 -->
          <div *ngIf="entry.isCurrentUser && gapToAbove > 0" class="gap-pill">
            <span class="gap-icon">⚡</span>
            <span class="gap-text">差 {{ gapToAbove }} EXP</span>
          </div>
        </div>
      </div>
    </mat-card>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .leaderboard-widget {
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
        margin-bottom: 12px;
        gap: 8px;
      }

      .title-group {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .title-icon {
        color: var(--stem-warning, #f59e0b);
      }

      .title {
        margin: 0;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 18px;
        font-weight: 700;
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .season-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%);
        color: #92400e;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
      }

      .season-emoji {
        font-size: 13px;
      }

      .season-name {
        font-weight: 700;
      }

      .season-divider {
        color: #c2410c;
        opacity: 0.5;
      }

      .season-remaining {
        font-weight: 600;
        font-variant-numeric: tabular-nums;
      }

      .reward-btn {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 28px;
        height: 28px;
        border: none;
        border-radius: 50%;
        background: var(--matux-color-background, #f1f5f9);
        cursor: pointer;
        transition: transform 200ms ease, background 200ms ease;
      }

      .reward-btn:hover {
        background: #fef3c7;
        transform: scale(1.1);
      }

      .reward-btn:active {
        transform: scale(0.95);
      }

      .reward-btn[aria-expanded='true'] {
        background: #fef3c7;
      }

      .reward-icon {
        font-size: 16px;
      }

      .reward-strip {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 12px;
        padding: 8px;
        border-radius: 12px;
        background: var(--matux-color-background, #f1f5f9);
        animation: rewardFadeIn 280ms cubic-bezier(0.34, 1.56, 0.64, 1);
      }

      @keyframes rewardFadeIn {
        from {
          opacity: 0;
          transform: translateY(-8px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .reward-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        padding: 8px 4px;
        border-radius: 10px;
        color: #ffffff;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
      }

      .reward-badge {
        font-size: 22px;
        line-height: 1;
        filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2));
      }

      .reward-title {
        font-size: 12px;
        font-weight: 700;
        margin-top: 2px;
      }

      .reward-range {
        font-size: 10px;
        opacity: 0.9;
        font-weight: 600;
      }

      .reward-exp {
        font-size: 11px;
        font-weight: 700;
        margin-top: 2px;
        font-variant-numeric: tabular-nums;
      }

      .leaderboard-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .lb-entry {
        display: grid;
        grid-template-columns: 32px 40px 1fr auto;
        gap: 10px;
        align-items: center;
        padding: 8px 10px;
        border-radius: 10px;
        background: var(--matux-color-background, #f1f5f9);
        transition: background 200ms ease;
        position: relative;
      }

      .lb-entry.is-me {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        outline: 1px solid var(--stem-primary, #059669);
      }

      .rank-cell {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 16px;
      }

      .rank-number {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 13px;
        font-weight: 700;
      }

      .avatar-cell {
        position: relative;
      }

      .avatar {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--matux-color-background, #f1f5f9);
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 700;
      }

      .avatar.rank-1 {
        background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%);
      }
      .avatar.rank-2 {
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
      }
      .avatar.rank-3 {
        background: linear-gradient(135deg, #fed7aa 0%, #fb923c 100%);
      }

      .me-marker {
        position: absolute;
        bottom: -4px;
        right: -4px;
        font-size: 10px;
      }

      .info-cell {
        min-width: 0;
      }

      .username {
        overflow: hidden;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 600;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .lb-entry.is-me .username::after {
        content: ' (我)';
        color: var(--stem-primary, #059669);
        font-size: 10px;
      }

      .points {
        color: var(--stem-warning, #f59e0b);
        font-size: 11px;
        font-weight: 600;
      }

      .change-cell {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 2px;
      }

      .weekly-change {
        display: flex;
        align-items: center;
        gap: 2px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .weekly-change mat-icon {
        width: 12px;
        height: 12px;
        font-size: 12px;
      }

      .weekly-change mat-icon.up {
        color: var(--stem-success, #059669);
      }
      .weekly-change mat-icon.down {
        color: var(--stem-error, #ef4444);
      }

      .rank-change {
        font-size: 10px;
        font-weight: 600;
      }

      .rank-change.up {
        color: var(--stem-success, #059669);
      }
      .rank-change.down {
        color: var(--stem-error, #ef4444);
      }

      .gap-pill {
        grid-column: 1 / -1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        margin-top: 4px;
        padding: 4px 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #92400e;
        font-size: 11px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        animation: gapGlow 1.6s ease-in-out infinite;
      }

      @keyframes gapGlow {
        0%,
        100% {
          box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4);
        }
        50% {
          box-shadow: 0 0 0 4px rgba(245, 158, 11, 0);
        }
      }

      .gap-icon {
        font-size: 12px;
      }
    `,
  ],
})
export class WeeklyLeaderboardWidgetComponent implements OnInit, OnDestroy {
  @Input() entries: LeaderboardEntry[] = [];
  @Output() viewAll = new EventEmitter<void>();

  private readonly seasonService = inject(SeasonService);
  private readonly sub = new Subscription();

  /** 倒计时流（每分钟刷新） */
  remaining: TimeRemaining = this.seasonService.timeRemaining();

  showRewards = false;
  rewards: SeasonReward[] = [];

  ngOnInit(): void {
    this.rewards = this.seasonService.upcomingRewards();
    // 每 60 秒刷新倒计时
    this.sub.add(interval(60000).subscribe(() => (this.remaining = this.seasonService.timeRemaining())));
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
  }

  toggleRewards(): void {
    this.showRewards = !this.showRewards;
  }

  get seasonName(): string {
    return this.seasonService.getCurrentSeason().name;
  }

  get seasonEmoji(): string {
    const id = this.seasonService.getCurrentSeason().id;
    if (id.endsWith('q1')) return '🌸';
    if (id.endsWith('q2')) return '🌞';
    if (id.endsWith('q3')) return '🍂';
    return '❄️';
  }

  get remainingDays(): number {
    return this.remaining.days;
  }

  get ariaSeason(): string {
    const s = this.seasonService.getCurrentSeason();
    return `${s.name} 剩余 ${this.remainingDays} 天`;
  }

  /**
   * 距上一名差距（当前用户非第 1 名时计算）
   * - 找 currentUser 上一名（rank = me.rank - 1）
   * - gap = above.totalExp - me.totalExp
   */
  get gapToAbove(): number {
    const me = this.entries.find((e) => e.isCurrentUser);
    if (!me || me.rank <= 1) return 0;
    const above = this.entries.find((e) => e.rank === me.rank - 1);
    if (!above) return 0;
    return Math.max(0, above.totalExp - me.totalExp);
  }

  trackByUserId(index: number, entry: LeaderboardEntry): number {
    return entry.userId;
  }

  trackByRank(index: number, r: SeasonReward): string {
    return r.rankRange;
  }

  get weekLabel(): string {
    const now = new Date();
    const start = new Date(now);
    start.setDate(now.getDate() - now.getDay());
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    const m1 = start.getMonth() + 1;
    const d1 = start.getDate();
    const m2 = end.getMonth() + 1;
    const d2 = end.getDate();
    return `${m1}/${d1} - ${m2}/${d2}`;
  }
}
