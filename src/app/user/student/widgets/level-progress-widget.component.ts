/**
 * 等级进度 widget - 独立的等级+EXP进度条组件
 *
 * 动画填充进度条，可作为内嵌小组件在其他页面复用
 *
 * @see Task 3.2 等级系统
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Input,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import type { UserLevel } from '../services/student-dashboard-data.service';

@Component({
  selector: 'app-level-progress-widget',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatIconModule, MatProgressBarModule],
  template: `
    <div class="level-progress" [class.compact]="compact">
      <!-- 等级徽章 -->
      <div class="level-badge" [class]="'rarity-' + badgeRarity">
        <span class="level-text">Lv.{{ level.current }}</span>
      </div>

      <!-- 经验值进度条 -->
      <div class="progress-section">
        <div class="progress-header">
          <span class="level-title">{{ level.title }}</span>
          <span class="exp-text">{{ level.exp }} / {{ level.expToNext }} EXP</span>
        </div>
        <div class="progress-bar-wrap">
          <mat-progress-bar
            mode="determinate"
            [value]="level.expProgressPercent"
            color="primary"
          ></mat-progress-bar>
        </div>
        <div class="progress-footer" *ngIf="!compact">
          <span class="total-exp">总经验 {{ level.totalExp }}</span>
          <span class="to-next">
            距离下一级还需 {{ level.expToNext - level.exp }} EXP
          </span>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      :host { display: block; }

      .level-progress {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 12px 14px;
        border-radius: 14px;
        background: var(--matux-color-background, #f1f5f9);
      }

      .level-progress.compact {
        padding: 8px 10px;
      }

      .level-badge {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #10b981 100%));
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
        color: white;
        transition: transform 200ms ease;
      }

      .level-progress.compact .level-badge {
        width: 36px;
        height: 36px;
      }

      .level-badge:hover {
        transform: scale(1.05);
      }

      .level-badge.rarity-rare {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
      }

      .level-badge.rarity-epic {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4);
      }

      .level-badge.rarity-legendary {
        background: linear-gradient(135deg, #b45309 0%, #f59e0b 100%);
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.5);
        animation: legendary-pulse 2s ease-in-out infinite;
      }

      @keyframes legendary-pulse {
        0%, 100% { box-shadow: 0 4px 16px rgba(245, 158, 11, 0.5); }
        50% { box-shadow: 0 4px 24px rgba(245, 158, 11, 0.8); }
      }

      .level-text {
        font-size: 14px;
        font-weight: 700;
      }

      .level-progress.compact .level-text {
        font-size: 11px;
      }

      .progress-section {
        flex: 1;
        min-width: 0;
      }

      .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 4px;
      }

      .level-title {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 700;
      }

      .exp-text {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
      }

      .progress-bar-wrap {
        height: 8px;
      }

      .progress-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 4px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }
    `,
  ],
})
export class LevelProgressWidgetComponent {
  @Input() level!: UserLevel;
  @Input() compact = false;

  get badgeRarity(): string {
    if (this.level.current >= 16) return 'legendary';
    if (this.level.current >= 11) return 'epic';
    if (this.level.current >= 6) return 'rare';
    return 'common';
  }
}