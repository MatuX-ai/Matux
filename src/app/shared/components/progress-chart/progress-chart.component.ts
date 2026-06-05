/**
 * 进度图表组件 - 共享UI组件
 *
 * 用于Dashboard展示各类进度数据（学习进度、课程完成度、班级进度等）
 * Dumb组件：仅负责展示，不包含业务逻辑
 * Phase 1 共享仪表板组件
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
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

/** 进度条数据项 */
export interface ProgressItem {
  /** 唯一标识 */
  id: number | string;
  /** 标签 */
  label: string;
  /** 进度百分比 (0-100) */
  progress: number;
  /** 副标签（如学生数、课程名） */
  subtitle?: string;
  /** 颜色主题 */
  color?: 'primary' | 'accent' | 'warn' | 'success' | 'info';
  /** 额外信息 */
  extra?: string;
  /** 图标 */
  icon?: string;
  /** 是否可点击 */
  clickable?: boolean;
}

/** 进度图表配置 */
export interface ProgressChartConfig {
  /** 标题 */
  title: string;
  /** 进度项列表 */
  items: ProgressItem[];
  /** 显示模式 */
  mode?: 'bar' | 'compact' | 'list';
  /** 是否显示总体进度 */
  showOverall?: boolean;
  /** 是否显示图例 */
  showLegend?: boolean;
  /** 最大显示条数 */
  maxItems?: number;
  /** 空状态文本 */
  emptyText?: string;
}

@Component({
  selector: 'app-progress-chart',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  template: `
    <mat-card class="progress-chart-card">
      <mat-card-header>
        <mat-card-title>{{ config.title }}</mat-card-title>
        <button
          mat-icon-button
          class="expand-btn"
          *ngIf="config.items.length > (config.maxItems || 5)"
          (click)="toggleExpand()"
          [matTooltip]="expanded ? '收起' : '展开全部'"
        >
          <mat-icon>{{ expanded ? 'expand_less' : 'expand_more' }}</mat-icon>
        </button>
      </mat-card-header>

      <mat-card-content>
        <!-- 总体进度条 -->
        <div class="overall-progress" *ngIf="config.showOverall">
          <div class="overall-header">
            <span class="overall-label">总体进度</span>
            <span class="overall-value">{{ overallProgress | number: '1.0-1' }}%</span>
          </div>
          <mat-progress-bar
            mode="determinate"
            [value]="overallProgress"
            color="primary"
          ></mat-progress-bar>
        </div>

        <!-- 空状态 -->
        <div class="empty-state" *ngIf="!displayItems.length">
          <mat-icon>inbox</mat-icon>
          <p>{{ config.emptyText || '暂无数据' }}</p>
        </div>

        <!-- 进度条列表 (bar模式) -->
        <div class="progress-list" *ngIf="config.mode !== 'compact' && config.mode !== 'list'">
          <div
            class="progress-item"
            *ngFor="let item of displayItems; trackBy: trackById"
            [class.clickable]="item.clickable"
            (click)="onItemClick(item)"
          >
            <div class="item-header">
              <div class="item-label-group">
                <mat-icon class="item-icon" *ngIf="item.icon">{{ item.icon }}</mat-icon>
                <span class="item-label">{{ item.label }}</span>
              </div>
              <span class="item-value" [class]="'color-' + (item.color || 'primary')">
                {{ item.progress | number: '1.0-1' }}%
              </span>
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="item.progress"
              [color]="item.color || 'primary'"
            ></mat-progress-bar>
            <div class="item-footer" *ngIf="item.subtitle || item.extra">
              <span class="item-subtitle" *ngIf="item.subtitle">{{ item.subtitle }}</span>
              <span class="item-extra" *ngIf="item.extra">{{ item.extra }}</span>
            </div>
          </div>
        </div>

        <!-- 紧凑模式 (compact) -->
        <div class="compact-list" *ngIf="config.mode === 'compact'">
          <div
            class="compact-item"
            *ngFor="let item of displayItems; trackBy: trackById"
            [class.clickable]="item.clickable"
            (click)="onItemClick(item)"
          >
            <div class="compact-ring" [class]="'color-' + (item.color || 'primary')">
              <svg viewBox="0 0 36 36" class="circular-chart">
                <path
                  class="circle-bg"
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  class="circle"
                  [attr.stroke-dasharray]="item.progress + ', 100'"
                  d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <text x="18" y="20.35" class="percentage">{{ item.progress | number: '1.0-0' }}%</text>
              </svg>
            </div>
            <div class="compact-info">
              <span class="compact-label">{{ item.label }}</span>
              <span class="compact-subtitle" *ngIf="item.subtitle">{{ item.subtitle }}</span>
            </div>
          </div>
        </div>

        <!-- 列表模式 (list) -->
        <div class="simple-list" *ngIf="config.mode === 'list'">
          <div
            class="list-item"
            *ngFor="let item of displayItems; trackBy: trackById"
            [class.clickable]="item.clickable"
            (click)="onItemClick(item)"
          >
            <span class="list-label">{{ item.label }}</span>
            <div class="list-progress-group">
              <mat-progress-bar
                mode="determinate"
                [value]="item.progress"
                [color]="item.color || 'primary'"
                class="list-progress-bar"
              ></mat-progress-bar>
              <span class="list-value">{{ item.progress | number: '1.0-1' }}%</span>
            </div>
          </div>
        </div>

        <!-- 图例 -->
        <div class="legend" *ngIf="config.showLegend && config.items.length > 0">
          <div class="legend-item" *ngFor="let color of legendColors">
            <span class="legend-dot" [class]="'color-' + color.key"></span>
            <span class="legend-label">{{ color.label }}</span>
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

      .progress-chart-card {
        height: 100%;

        mat-card-header {
          display: flex;
          align-items: center;
          padding: 16px 16px 0;

          mat-card-title {
            font-size: 16px;
            font-weight: 600;
            margin: 0;
          }

          .expand-btn {
            margin-left: auto;
            width: 32px;
            height: 32px;
            line-height: 32px;

            mat-icon {
              font-size: 20px;
              width: 20px;
              height: 20px;
            }
          }
        }

        mat-card-content {
          padding: 16px;
        }
      }

      /* 总体进度 */
      .overall-progress {
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid #eee;

        .overall-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .overall-label {
            font-size: 14px;
            color: #555;
            font-weight: 500;
          }

          .overall-value {
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
          }
        }
      }

      /* 空状态 */
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        color: #999;

        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
          margin-bottom: 12px;
        }

        p {
          margin: 0;
          font-size: 14px;
        }
      }

      /* Bar模式 - 进度条列表 */
      .progress-list {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .progress-item {
        cursor: default;

        &.clickable {
          cursor: pointer;
          transition: background-color 0.2s ease;
          border-radius: 8px;
          padding: 8px;
          margin: -8px;

          &:hover {
            background-color: #f5f5f5;
          }
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;

          .item-label-group {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;

            .item-icon {
              font-size: 18px;
              width: 18px;
              height: 18px;
              color: #888;
            }

            .item-label {
              font-size: 14px;
              color: #333;
              font-weight: 500;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
          }

          .item-value {
            font-size: 14px;
            font-weight: 600;
            flex-shrink: 0;
            margin-left: 12px;

            &.color-primary { color: #0f172a; }
            &.color-accent { color: #3b82f6; }
            &.color-warn { color: #ef4444; }
            &.color-success { color: #10b981; }
            &.color-info { color: #3b82f6; }
          }
        }

        .item-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 4px;

          .item-subtitle {
            font-size: 12px;
            color: #999;
          }

          .item-extra {
            font-size: 12px;
            color: #aaa;
          }
        }
      }

      /* Compact模式 - 环形图 */
      .compact-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 16px;
      }

      .compact-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        cursor: default;

        &.clickable {
          cursor: pointer;
          padding: 8px;
          border-radius: 8px;
          transition: background-color 0.2s ease;

          &:hover {
            background-color: #f5f5f5;
          }
        }

        .compact-ring {
          width: 64px;
          height: 64px;

          .circular-chart {
            display: block;
            width: 100%;
            height: 100%;

            .circle-bg {
              fill: none;
              stroke: #eee;
              stroke-width: 3.8;
            }

            .circle {
              fill: none;
              stroke-width: 3.8;
              stroke-linecap: round;
              animation: progress 1s ease-out forwards;
            }

            .percentage {
              fill: #333;
              font-size: 8px;
              text-anchor: middle;
              font-weight: 600;
            }
          }

          &.color-primary .circle { stroke: #0f172a; }
          &.color-accent .circle { stroke: #3b82f6; }
          &.color-warn .circle { stroke: #ef4444; }
          &.color-success .circle { stroke: #10b981; }
          &.color-info .circle { stroke: #3b82f6; }
        }

        .compact-info {
          text-align: center;
          min-width: 0;
          width: 100%;

          .compact-label {
            display: block;
            font-size: 13px;
            color: #333;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .compact-subtitle {
            display: block;
            font-size: 11px;
            color: #999;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }

      /* List模式 - 简单列表 */
      .simple-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .list-item {
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: default;

        &.clickable {
          cursor: pointer;
          padding: 6px 8px;
          margin: -6px -8px;
          border-radius: 6px;
          transition: background-color 0.2s ease;

          &:hover {
            background-color: #f5f5f5;
          }
        }

        .list-label {
          font-size: 14px;
          color: #333;
          min-width: 80px;
          max-width: 120px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .list-progress-group {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;

          .list-progress-bar {
            flex: 1;
            min-width: 60px;
          }

          .list-value {
            font-size: 13px;
            font-weight: 600;
            color: #555;
            min-width: 42px;
            text-align: right;
          }
        }
      }

      /* 图例 */
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid #eee;

        .legend-item {
          display: flex;
          align-items: center;
          gap: 4px;

          .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;

            &.color-primary { background-color: #0f172a; }
            &.color-accent { background-color: #3b82f6; }
            &.color-warn { background-color: #ef4444; }
            &.color-success { background-color: #10b981; }
            &.color-info { background-color: #3b82f6; }
          }

          .legend-label {
            font-size: 12px;
            color: #666;
          }
        }
      }

      /* 响应式 */
      @media (max-width: 768px) {
        .progress-chart-card {
          mat-card-header {
            padding: 12px 12px 0;
          }

          mat-card-content {
            padding: 12px;
          }
        }

        .compact-list {
          grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
          gap: 12px;
        }

        .compact-item .compact-ring {
          width: 52px;
          height: 52px;
        }

        .list-item .list-label {
          min-width: 60px;
          max-width: 90px;
        }
      }

      @keyframes progress {
        0% {
          stroke-dasharray: 0 100;
        }
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProgressChartComponent {
  @Input() config!: ProgressChartConfig;
  @Output() itemClicked = new EventEmitter<ProgressItem>();

  expanded = false;

  /** 显示的数据项（受maxItems和expanded控制） */
  get displayItems(): ProgressItem[] {
    const max = this.config.maxItems || 5;
    if (!this.expanded && this.config.items.length > max) {
      return this.config.items.slice(0, max);
    }
    return this.config.items;
  }

  /** 总体进度（所有项的平均值） */
  get overallProgress(): number {
    const items = this.config.items;
    if (!items.length) return 0;
    const total = items.reduce((sum, item) => sum + item.progress, 0);
    return total / items.length;
  }

  /** 图例颜色 */
  get legendColors(): Array<{ key: string; label: string }> {
    const seen = new Set<string>();
    const colors: Array<{ key: string; label: string }> = [];
    const colorLabels: Record<string, string> = {
      primary: '主要',
      accent: '强调',
      warn: '警告',
      success: '成功',
      info: '信息',
    };

    for (const item of this.config.items) {
      const color = item.color || 'primary';
      if (!seen.has(color)) {
        seen.add(color);
        colors.push({ key: color, label: colorLabels[color] || color });
      }
    }

    return colors;
  }

  toggleExpand(): void {
    this.expanded = !this.expanded;
  }

  onItemClick(item: ProgressItem): void {
    if (item.clickable) {
      this.itemClicked.emit(item);
    }
  }

  trackById(_index: number, item: ProgressItem): number | string {
    return item.id;
  }
}
