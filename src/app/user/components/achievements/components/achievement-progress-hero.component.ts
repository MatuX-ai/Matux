/**
 * 成就总览 Hero 组件（P2-B）
 *
 * 顶部成就博物馆主视觉：
 * - 大徽章 + 等级徽章环
 * - 解锁总数 + 完成度 + 积分
 * - 段位色 + 传说级光效
 * - 最近解锁时间线
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AchievementSetsService } from '../../../../core/services/achievement-sets.service';
import type { ExtendedAchievementBadge } from '../../../../features/achievement-integration/models/achievement.model';

@Component({
  selector: 'app-achievement-progress-hero',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatProgressBarModule, MatTooltipModule],
  template: `
    <div class="hero-wrapper" *ngIf="summary">
      <!-- 左侧：大徽章 + 进度环 -->
      <div class="hero-badge-section">
        <div class="badge-ring">
          <svg viewBox="0 0 200 200" class="ring-svg">
            <circle cx="100" cy="100" r="92" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="6" />
            <circle
              cx="100"
              cy="100"
              r="92"
              fill="none"
              stroke="url(#hero-progress-gradient)"
              stroke-width="8"
              stroke-linecap="round"
              [attr.stroke-dasharray]="circumference"
              [attr.stroke-dashoffset]="dashOffset"
              transform="rotate(-90 100 100)"
              class="progress-circle"
            />
            <defs>
              <linearGradient id="hero-progress-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#fbbf24" />
                <stop offset="50%" stop-color="#f59e0b" />
                <stop offset="100%" stop-color="#d97706" />
              </linearGradient>
            </defs>
          </svg>
          <div class="badge-center">
            <span class="hero-emoji">{{ heroEmoji }}</span>
            <span class="hero-tier" [style.background]="tierGradient">
              {{ tierLabel }}
            </span>
          </div>
        </div>
      </div>

      <!-- 右侧：统计数据 -->
      <div class="hero-stats-section">
        <div class="hero-header">
          <h2 class="hero-title">成就中心</h2>
          <p class="hero-subtitle">{{ summary.unlocked }} / {{ summary.total }} 已解锁</p>
        </div>

        <!-- 数据条 -->
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-value">{{ summary.unlockRate * 100 | number: '1.0-0' }}%</div>
            <div class="stat-label">解锁率</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary.earnedPoints }}</div>
            <div class="stat-label">已获积分</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary.byRarity['legendary']?.unlocked || 0 }}</div>
            <div class="stat-label">传说徽章</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ summary.totalPoints - summary.earnedPoints }}</div>
            <div class="stat-label">待解锁积分</div>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="progress-section">
          <div class="progress-info">
            <span class="progress-label">整体进度</span>
            <span class="progress-value">
              {{ summary.unlockRate * 100 | number: '1.0-0' }}%
            </span>
          </div>
          <mat-progress-bar
            mode="determinate"
            [value]="summary.unlockRate * 100"
            class="progress-bar"
          ></mat-progress-bar>
        </div>

        <!-- 最近解锁 -->
        <div class="recent-section" *ngIf="summary.recentUnlocks.length > 0">
          <h4 class="recent-title">🕒 最近解锁</h4>
          <div class="recent-list">
            <div
              *ngFor="let badge of summary.recentUnlocks.slice(0, 4)"
              class="recent-item"
              [class]="'rarity-' + (badge.rarity || 'common')"
            >
              <span class="recent-emoji">{{ badge.icon }}</span>
              <span class="recent-name">{{ badge.name }}</span>
              <span class="recent-date" *ngIf="badge.unlockedDate">
                {{ badge.unlockedDate | date: 'MM-dd' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./achievement-progress-hero.component.scss'],
})
export class AchievementProgressHeroComponent implements OnChanges {
  @Input() badges: ExtendedAchievementBadge[] = [];

  summary: ReturnType<AchievementSetsService['summarize']> | null = null;
  heroEmoji = '🏆';
  tierLabel = '大师';
  tierGradient = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';

  /** SVG 圆周长（用于 stroke-dasharray） */
  readonly circumference = 2 * Math.PI * 92;

  private readonly setsService = inject(AchievementSetsService);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['badges']) {
      this.rebuild();
    }
  }

  get dashOffset(): number {
    if (!this.summary) return this.circumference;
    return this.circumference * (1 - this.summary.unlockRate);
  }

  private rebuild(): void {
    this.summary = this.setsService.summarize(this.badges);
    this.updateTier();
  }

  /**
   * 根据解锁数量与传说徽章数量决定英雄段位
   */
  private updateTier(): void {
    if (!this.summary) return;

    if (this.summary.byRarity['legendary']?.unlocked > 0) {
      this.heroEmoji = '🌟';
      this.tierLabel = '传说收藏家';
      this.tierGradient = 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)';
    } else if (this.summary.byRarity['epic']?.unlocked > 0) {
      this.heroEmoji = '💎';
      this.tierLabel = '史诗猎人';
      this.tierGradient = 'linear-gradient(135deg, #a78bfa 0%, #6d28d9 100%)';
    } else if (this.summary.unlockRate >= 0.5) {
      this.heroEmoji = '🏆';
      this.tierLabel = '成就达人';
      this.tierGradient = 'linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)';
    } else if (this.summary.unlockRate >= 0.2) {
      this.heroEmoji = '⭐';
      this.tierLabel = '成就新秀';
      this.tierGradient = 'linear-gradient(135deg, #34d399 0%, #10b981 100%)';
    } else {
      this.heroEmoji = '🌱';
      this.tierLabel = '启程者';
      this.tierGradient = 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)';
    }
  }
}