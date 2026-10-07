/**
 * 统计卡片组件 - 共享UI组件
 *
 * 用于Dashboard展示统计数据（数值+标签+图标）
 * Dumb组件：仅负责展示，不包含业务逻辑
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

export interface StatsCardConfig {
  /** 显示数值 */
  value: number | string;
  /** 标签文本 */
  label: string;
  /** 图标名称 */
  icon: string;
  /** 颜色主题 */
  color?: 'primary' | 'accent' | 'warn' | 'success';
  /** 副标题 */
  subtitle?: string;
  /** 趋势信息 */
  trend?: {
    direction: 'up' | 'down' | 'stable';
    value: string;
    positive?: boolean;
  };
  /** 是否可点击 */
  clickable?: boolean;
}

@Component({
  selector: 'app-stats-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule],
  template: `
    <mat-card class="stats-card" [class.clickable]="config.clickable" (click)="onClick()">
      <mat-card-content>
        <div class="icon-wrapper" [class]="'color-' + (config.color || 'primary')">
          <mat-icon>{{ config.icon }}</mat-icon>
        </div>
        <div class="content">
          <h3 class="value">{{ formatValue(config.value) }}</h3>
          <p class="label">{{ config.label }}</p>
          <p class="subtitle" *ngIf="config.subtitle">{{ config.subtitle }}</p>
          <div class="trend" *ngIf="config.trend">
            <mat-icon
              [class.positive]="config.trend.positive !== false"
              [class.negative]="config.trend.positive === false"
            >
              {{ getTrendIcon(config.trend.direction) }}
            </mat-icon>
            <span
              [class.positive]="config.trend.positive !== false"
              [class.negative]="config.trend.positive === false"
            >
              {{ config.trend.value }}
            </span>
          </div>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-light: #10b981;
        --stem-secondary: #0ea5e9;
        --stem-success: #059669;
        --stem-warning: #f59e0b;
        --stem-error: #ef4444;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-bg-surface: #ffffff;
        --stem-radius-lg: 20px;
        --stem-radius-md: 12px;
        --stem-shadow-sm: 0 1px 3px rgba(5, 150, 105, 0.08);
        --stem-shadow-card-hover: 0 14px 28px rgba(5, 150, 105, 0.12);
        --stem-gradient-explore: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);
      }

      :host {
        display: block;
      }

      .stats-card {
        height: 100%;
        // STEM 圆角和阴影
        border-radius: var(--stem-radius-lg, 20px);
        box-shadow: var(--stem-shadow-sm);
        background: var(--stem-bg-surface, #ffffff);
        transition:
          transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
          box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);

        mat-card-content {
          display: flex;
          align-items: center;
          padding: 20px;
          height: 100%;
          box-sizing: border-box;
        }

        &:hover {
          &.clickable {
            transform: translateY(-4px);
            box-shadow: var(--stem-shadow-card-hover);
            cursor: pointer;
          }
        }
      }

      .icon-wrapper {
        margin-right: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: var(--stem-radius-md, 12px);

        mat-icon {
          font-size: 24px;
          width: 24px;
          height: 24px;
          color: white;
        }

        // STEM 探索绿主题色
        &.color-primary {
          background: var(--stem-gradient-explore);
        }

        &.color-accent {
          background: linear-gradient(
            135deg,
            var(--stem-secondary, #0ea5e9) 0%,
            var(--stem-secondary-light, #38bdf8) 100%
          );
        }

        &.color-warn {
          background: linear-gradient(135deg, var(--stem-warning, #f59e0b) 0%, #fbbf24 100%);
        }

        &.color-success {
          background: linear-gradient(
            135deg,
            var(--stem-success, #059669) 0%,
            var(--stem-primary-light, #10b981) 100%
          );
        }

        &.color-default {
          background: #757575;
        }
      }

      .content {
        flex: 1;
        min-width: 0;

        .value {
          margin: 0 0 4px 0;
          font-size: 32px;
          font-weight: 700;
          // STEM 主题文本色
          color: var(--stem-text-primary, #1c1917);
          line-height: 1.2;
        }

        .label {
          margin: 0;
          font-size: 14px;
          color: var(--stem-text-secondary, #57534e);
          line-height: 1.4;
        }

        .subtitle {
          margin: 4px 0 0 0;
          font-size: 12px;
          color: #78716c;
          line-height: 1.4;
        }
      }

      .trend {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 8px;
        font-size: 12px;

        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
          font-weight: 600;
        }

        span {
          font-weight: 600;
        }

        .positive {
          color: var(--stem-success, #059669);
        }

        .negative {
          color: var(--stem-error, #ef4444);
        }
      }

      @media (max-width: 768px) {
        .stats-card {
          mat-card-content {
            padding: 16px;
          }
        }

        .icon-wrapper {
          width: 40px;
          height: 40px;
          margin-right: 16px;

          mat-icon {
            font-size: 20px;
            width: 20px;
            height: 20px;
          }
        }

        .content .value {
          font-size: 24px;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StatsCardComponent {
  @Input() config!: StatsCardConfig;
  @Output() clicked = new EventEmitter<void>();

  onClick(): void {
    if (this.config.clickable) {
      this.clicked.emit();
    }
  }

  formatValue(value: number | string): string {
    if (typeof value === 'number') {
      return value.toLocaleString('zh-CN');
    }
    return value;
  }

  getTrendIcon(direction: 'up' | 'down' | 'stable'): string {
    switch (direction) {
      case 'up':
        return 'trending_up';
      case 'down':
        return 'trending_down';
      case 'stable':
        return 'trending_flat';
      default:
        return 'trending_flat';
    }
  }
}
