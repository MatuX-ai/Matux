/**
 * 成就中心卡 - 核心 dashboard 卡 #2
 *
 * 内容：
 * - 等级徽章 + 经验值进度条
 * - 连续打卡天数（火焰图标）
 * - 徽章预览（解锁/未解锁状态，含稀有度）
 * - 跳转成就墙
 *
 * 视觉：琥珀渐变 + 金色稀有度
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import type { DashboardSnapshot, UserLevel } from '../../services/student-dashboard-data.service';
import type { ExtendedAchievementBadge } from '../../student-dashboard.mock';

@Component({
  selector: 'app-achievement-center-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule, MatProgressBarModule, MatTooltipModule],
  template: `
    <mat-card
      class="core-card core-card--achievement"
      [class.clickable]="true"
      tabindex="0"
      role="button"
      [attr.aria-label]="
        '成就中心：连续打卡 ' +
        streakDays +
        ' 天，已解锁 ' +
        unlockedCount +
        '/' +
        totalCount +
        ' 徽章'
      "
      (click)="onClick()"
      (keyup.enter)="onClick()"
    >
      <div class="card-icon-wrap">
        <mat-icon>emoji_events</mat-icon>
      </div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-label">成就中心</span>
          <mat-icon class="card-arrow">arrow_forward</mat-icon>
        </div>

        <!-- 等级 + 经验值进度条 -->
        <div class="level-row">
          <div class="level-badge" [class]="'rarity-' + 'legendary'">
            <span class="level-number">Lv.{{ level.current }}</span>
          </div>
          <div class="level-info">
            <div class="level-title">{{ level.title }}</div>
            <div class="exp-bar">
              <mat-progress-bar
                mode="determinate"
                [value]="level.expProgressPercent"
                color="accent"
              ></mat-progress-bar>
            </div>
            <div class="exp-text">{{ level.exp }} / {{ level.expToNext }} EXP</div>
          </div>
        </div>

        <!-- 连续打卡 -->
        <div class="streak-row">
          <span class="streak-icon">🔥</span>
          <span class="streak-days">{{ streakDays }}</span>
          <span class="streak-label">连续打卡</span>
          <span class="streak-meta" *ngIf="nextMilestoneDays > 0">
            再 {{ nextMilestoneDays }} 天解锁新成就
          </span>
        </div>

        <!-- 徽章预览 -->
        <div class="badges-preview">
          <div
            *ngFor="let badge of previewBadges"
            class="badge-mini"
            [class.locked]="!badge.unlocked"
            [class]="'rarity-' + badge.rarity"
            [matTooltip]="badge.name + (badge.unlocked ? ' · 已解锁' : ' · 未解锁')"
          >
            <span class="badge-icon">{{ badge.icon }}</span>
          </div>
          <div class="badge-mini badge-more" *ngIf="totalCount > previewBadges.length">
            +{{ totalCount - previewBadges.length }}
          </div>
        </div>
        <div class="progress-summary">
          已解锁 {{ unlockedCount }} / {{ totalCount }} · 完成度 {{ progressPercent }}%
        </div>
      </div>
    </mat-card>
  `,
  styles: [
    `
      :host {
        display: block;
      }

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
        transition:
          transform 200ms ease,
          box-shadow 200ms ease;

        &:hover,
        &:focus-visible {
          outline: none;
          transform: translateY(-4px);
          box-shadow: var(--stem-shadow-card-hover, 0 14px 28px rgba(5, 150, 105, 0.12));
        }

        &:hover .card-arrow,
        &:focus-visible .card-arrow {
          transform: translateX(4px);
          color: var(--stem-warning, #f59e0b);
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
        background: var(--stem-gradient-warning, linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%));
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
        color: var(--matux-color-text-disabled, #94a3b8);
        font-size: 20px;
        transition:
          transform 200ms ease,
          color 200ms ease;
      }

      .level-row {
        display: flex;
        gap: 10px;
        align-items: center;
        padding: 8px 10px;
        border-radius: 10px;
        background: var(--matux-color-background, #f1f5f9);
      }

      .level-badge {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #0ea5e9 100%));
        color: white;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.3);
      }

      .level-number {
        font-size: 12px;
        font-weight: 700;
      }

      .level-info {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
      }

      .level-title {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 700;
      }

      .exp-bar {
        height: 6px;
      }

      .exp-text {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .streak-row {
        display: flex;
        align-items: baseline;
        gap: 4px;
        margin-top: 2px;
      }

      .streak-icon {
        font-size: 20px;
      }

      .streak-days {
        color: var(--stem-rarity-legendary, #b45309);
        font-size: 22px;
        font-weight: 700;
      }

      .streak-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 12px;
      }

      .streak-meta {
        margin-left: auto;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .badges-preview {
        display: flex;
        gap: 6px;
        margin-top: 4px;
      }

      .badge-mini {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        font-size: 16px;
        transition: transform 200ms ease;
      }

      .badge-mini.rarity-rare {
        background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
      }
      .badge-mini.rarity-epic {
        background: linear-gradient(135deg, #ede9fe 0%, #c4b5fd 100%);
      }
      .badge-mini.rarity-legendary {
        background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%);
      }

      .badge-mini.badge-more {
        background: var(--matux-color-background, #f1f5f9);
        color: var(--matux-color-text-secondary, #57534e);
        font-weight: 700;
      }

      .badge-mini.locked {
        filter: grayscale(0.8);
        opacity: 0.6;
      }

      .progress-summary {
        margin-top: 2px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
        text-align: center;
      }
    `,
  ],
})
export class AchievementCenterCardComponent {
  @Input() snapshot: DashboardSnapshot | null = null;
  @Output() navigate = new EventEmitter<string>();

  get level(): UserLevel {
    return (
      this.snapshot?.level ?? {
        current: 1,
        title: '初学者',
        exp: 0,
        expToNext: 100,
        expProgressPercent: 0,
        totalExp: 0,
      }
    );
  }

  get streakDays(): number {
    return (this.snapshot as any)?.streakDays ?? 0;
  }

  get nextMilestoneDays(): number {
    const days = this.streakDays;
    const milestones = [7, 14, 30, 60, 100];
    const next = milestones.find((m) => m > days);
    return next ? next - days : 0;
  }

  get previewBadges(): ExtendedAchievementBadge[] {
    return (this.snapshot?.achievements?.badges ?? []).slice(0, 4);
  }

  get unlockedCount(): number {
    return this.snapshot?.achievements?.unlockedCount ?? 0;
  }

  get totalCount(): number {
    return this.snapshot?.achievements?.totalCount ?? 0;
  }

  get progressPercent(): number {
    return this.snapshot?.achievements?.progressPercent ?? 0;
  }

  onClick(): void {
    this.navigate.emit('/achievements');
  }
}
