/**
 * 社交中心卡 - 核心 dashboard 卡 #4
 *
 * 内容：
 * - 学习来源数量统计
 * - 排行榜入口（top 3 预览）
 * - 学习日历入口
 * - 用户主页跳转
 *
 * 视觉：探索绿-蓝渐变 + 社交感设计
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import type {
  DashboardSnapshot,
  LeaderboardEntry,
} from '../../services/student-dashboard-data.service';

@Component({
  selector: 'app-social-center-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule, MatTooltipModule],
  template: `
    <mat-card
      class="core-card core-card--social"
      [class.clickable]="true"
      tabindex="0"
      role="button"
      [attr.aria-label]="
        '社交中心：你排名 ' + (myRank ?? '?') + '，有 ' + sourcesCount + ' 个学习来源'
      "
      (click)="onClick()"
      (keyup.enter)="onClick()"
    >
      <div class="card-icon-wrap">
        <mat-icon>groups</mat-icon>
      </div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-label">社交中心</span>
          <mat-icon class="card-arrow">arrow_forward</mat-icon>
        </div>

        <!-- 我的排名 -->
        <div class="my-rank" *ngIf="myRankEntry">
          <div class="rank-badge" [class]="'rank-' + myRankEntry.rank">
            #{{ myRankEntry.rank }}
          </div>
          <div class="rank-info">
            <div class="rank-label">本周排名</div>
            <div class="rank-points">{{ myRankEntry.totalExp }} EXP</div>
          </div>
          <div class="rank-change" *ngIf="myRankEntry.rankChange !== 0">
            <mat-icon [class.up]="myRankEntry.rankChange > 0" [class.down]="myRankEntry.rankChange < 0">
              {{ myRankEntry.rankChange > 0 ? 'trending_up' : 'trending_down' }}
            </mat-icon>
            <span [class.up]="myRankEntry.rankChange > 0" [class.down]="myRankEntry.rankChange < 0">
              {{ myRankEntry.rankChange > 0 ? '+' : '' }}{{ myRankEntry.rankChange }}
            </span>
          </div>
        </div>

        <!-- Top 3 头像 -->
        <div class="top-avatars">
          <div
            *ngFor="let entry of topThree; let i = index"
            class="avatar-mini"
            [class]="'rank-' + entry.rank"
            [class.is-me]="entry.isCurrentUser"
            [matTooltip]="entry.username + ' · ' + entry.totalExp + ' EXP'"
          >
            <span class="avatar-medal" *ngIf="entry.rank <= 3">
              {{ entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉' }}
            </span>
            <span class="avatar-name">{{ entry.username.slice(0, 1) }}</span>
          </div>
        </div>

        <!-- 数据统计 -->
        <div class="social-stats">
          <div class="stat-mini">
            <mat-icon>hub</mat-icon>
            <span>{{ sourcesCount }}</span>
            <small>来源</small>
          </div>
          <div class="stat-mini">
            <mat-icon>calendar_month</mat-icon>
            <span>{{ streakDays }}</span>
            <small>打卡</small>
          </div>
          <div class="stat-mini">
            <mat-icon>emoji_events</mat-icon>
            <span>{{ unlockedCount }}</span>
            <small>徽章</small>
          </div>
        </div>
      </div>
    </mat-card>
  `,
  styles: [
    `
      :host { display: block; }

      .core-card {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        min-height: 200px;
        padding: 20px;
        border: none !important;
        border-radius: var(--dash-card-radius, 20px);
        background: var(--stem-bg-surface, #ffffff);
        box-shadow: var(--stem-shadow-sm, 0 1px 3px rgba(5, 150, 105, 0.08));
        cursor: pointer;
        transition: transform 200ms ease, box-shadow 200ms ease;

        &:hover, &:focus-visible {
          outline: none;
          transform: translateY(-4px);
          box-shadow: var(--stem-shadow-card-hover, 0 14px 28px rgba(5, 150, 105, 0.12));
        }

        &:hover .card-arrow, &:focus-visible .card-arrow {
          transform: translateX(4px);
          color: var(--stem-primary, #059669);
        }
      }

      .card-icon-wrap {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 56px;
        height: 56px;
        border-radius: 14px;
        background: var(--stem-gradient-ai, linear-gradient(135deg, #059669 0%, #2563eb 100%));
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        color: white;
      }

      .card-icon-wrap mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
        color: #ffffff; // 【修复 #14】mat-icon 默认 var(--icon-default) 会覆盖父级 white，显式重写
      }

      .card-body {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 8px;
        min-width: 0;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .card-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }

      .card-arrow {
        flex-shrink: 0;
        width: 20px;
        height: 20px;
        color: var(--matux-color-text-disabled, var(--matux-color-text-disabled, #94a3b8));
        font-size: 20px;
        transition: transform 200ms ease, color 200ms ease;
      }

      .my-rank {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        border-radius: 10px;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
      }

      .rank-badge {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: white;
        color: var(--stem-primary, #059669);
        font-size: 14px;
        font-weight: 700;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
      }

      .rank-badge.rank-1 { color: var(--stem-warning, #f59e0b); }
      .rank-badge.rank-2 { color: var(--matux-color-text-disabled, #94a3b8); }
      .rank-badge.rank-3 { color: var(--stem-rarity-legendary, #b45309); }

      .rank-info {
        flex: 1;
      }

      .rank-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .rank-points {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 14px;
        font-weight: 700;
      }

      .rank-change {
        display: flex;
        align-items: center;
        gap: 2px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
      }

      .rank-change mat-icon {
        width: 14px;
        height: 14px;
        font-size: 14px;
      }

      .rank-change mat-icon.up, .rank-change span.up {
        color: var(--stem-success, #059669);
      }

      .rank-change mat-icon.down, .rank-change span.down {
        color: var(--stem-error, #ef4444);
      }

      .top-avatars {
        display: flex;
        gap: 6px;
        justify-content: center;
      }

      .avatar-mini {
        position: relative;
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--matux-color-background, #f1f5f9);
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 12px;
        font-weight: 700;
      }

      .avatar-mini.rank-1 { background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%); }
      .avatar-mini.rank-2 { background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); }
      .avatar-mini.rank-3 { background: linear-gradient(135deg, #fed7aa 0%, #fb923c 100%); }

      .avatar-mini.is-me {
        box-shadow: 0 0 0 2px var(--stem-primary, #059669);
      }

      .avatar-medal {
        position: absolute;
        top: -4px;
        right: -4px;
        font-size: 12px;
      }

      .avatar-name {
        text-transform: uppercase;
      }

      .social-stats {
        display: flex;
        gap: 4px;
        margin-top: 4px;
        padding: 6px 0 0;
        border-top: 1px solid var(--matux-color-divider, #e2e8f0);
      }

      .stat-mini {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        gap: 2px;
      }

      .stat-mini mat-icon {
        color: var(--stem-secondary, #0ea5e9);
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .stat-mini span {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 14px;
        font-weight: 700;
      }

      .stat-mini small {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }
    `,
  ],
})
export class SocialCenterCardComponent {
  @Input() snapshot: DashboardSnapshot | null = null;
  @Output() navigate = new EventEmitter<string>();

  get myRankEntry(): LeaderboardEntry | null {
    const board = this.snapshot?.leaderboard ?? [];
    return board.find((e) => e.isCurrentUser) ?? null;
  }

  get myRank(): number | string {
    return this.myRankEntry?.rank ?? '?';
  }

  get sourcesCount(): number {
    return this.snapshot?.learningSources?.length ?? 0;
  }

  get streakDays(): number {
    return (this.snapshot as any)?.socialStats?.streakDays ?? 0;
  }

  get unlockedCount(): number {
    return this.snapshot?.achievements?.unlockedCount ?? 0;
  }

  get topThree(): LeaderboardEntry[] {
    return (this.snapshot?.leaderboard ?? []).slice(0, 3);
  }

  onClick(): void {
    this.navigate.emit('/social');
  }
}
