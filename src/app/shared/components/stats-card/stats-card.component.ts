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
      :host {
        display: block;
      }

      .stats-card {
        height: 100%;
        transition:
          transform 0.2s ease,
          box-shadow 0.2s ease;

        mat-card-content {
          display: flex;
          align-items: center;
          padding: 20px;
          height: 100%;
          box-sizing: border-box;
        }

        &:hover {
          &.clickable {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
        border-radius: 12px;

        mat-icon {
          font-size: 24px;
          width: 24px;
          height: 24px;
          color: white;
        }

        &.color-primary {
          background-color: #3f51b5;
        }

        &.color-accent {
          background-color: #ff4081;
        }

        &.color-warn {
          background-color: #f44336;
        }

        &.color-success {
          background-color: #4caf50;
        }

        &.color-default {
          background-color: #757575;
        }
      }

      .content {
        flex: 1;
        min-width: 0;

        .value {
          margin: 0 0 4px 0;
          font-size: 32px;
          font-weight: 700;
          color: #333;
          line-height: 1.2;
        }

        .label {
          margin: 0;
          font-size: 14px;
          color: #666;
          line-height: 1.4;
        }

        .subtitle {
          margin: 4px 0 0 0;
          font-size: 12px;
          color: #999;
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
          color: #4caf50;
        }

        .negative {
          color: #f44336;
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
