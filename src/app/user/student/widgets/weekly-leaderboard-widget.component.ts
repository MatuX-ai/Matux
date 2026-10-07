/**
 * 每周排行榜 widget - 同班同学积分榜
 *
 * 显示 top 5 同学，本周积分变化、排名升降
 * 当前用户行高亮
 *
 * @see Task 3.6 排行榜
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

import type { LeaderboardEntry } from '../services/student-dashboard-data.service';

@Component({
  selector: 'app-weekly-leaderboard-widget',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule],
  template: `
    <mat-card class="leaderboard-widget" aria-label="每周排行榜">
      <div class="widget-header">
        <div class="title-group">
          <mat-icon class="title-icon">leaderboard</mat-icon>
          <h2 class="title">本周排行榜</h2>
        </div>
        <span class="week-tag">{{ weekLabel }}</span>
      </div>

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
                {{ entry.weeklyChange > 0 ? 'trending_up' : entry.weeklyChange < 0 ? 'trending_down' : 'trending_flat' }}
              </mat-icon>
              <span class="change-num">+{{ entry.weeklyChange }}</span>
            </div>
            <div
              *ngIf="entry.rankChange !== 0"
              class="rank-change"
              [class.up]="entry.rankChange > 0"
              [class.down]="entry.rankChange < 0"
            >
              {{ entry.rankChange > 0 ? '↑' : '↓' }}{{ entry.rankChange > 0 ? entry.rankChange : -entry.rankChange }}
            </div>
          </div>
        </div>
      </div>
    </mat-card>
  `,
  styles: [
    `
      :host { display: block; }

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

      .week-tag {
        padding: 2px 8px;
        border-radius: 10px;
        background: var(--matux-color-background, #f1f5f9);
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
        font-weight: 600;
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

      .avatar.rank-1 { background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%); }
      .avatar.rank-2 { background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); }
      .avatar.rank-3 { background: linear-gradient(135deg, #fed7aa 0%, #fb923c 100%); }

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

      .weekly-change mat-icon.up { color: var(--stem-success, #059669); }
      .weekly-change mat-icon.down { color: var(--stem-error, #ef4444); }

      .rank-change {
        font-size: 10px;
        font-weight: 600;
      }

      .rank-change.up { color: var(--stem-success, #059669); }
      .rank-change.down { color: var(--stem-error, #ef4444); }
    `,
  ],
})
export class WeeklyLeaderboardWidgetComponent {
  @Input() entries: LeaderboardEntry[] = [];
  @Output() viewAll = new EventEmitter<void>();

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

  trackByUserId(index: number, entry: LeaderboardEntry): number {
    return entry.userId;
  }
}