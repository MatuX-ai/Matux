/**
 * 创作中心卡 - 核心 dashboard 卡 #3
 *
 * 内容：
 * - AI 推荐项目（top 1 渐变卡 + 更多入口）
 * - 课件库入口
 * - 实战项目入口
 *
 * 视觉：天空蓝渐变 + 创意色板
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import type {
  AiRecommendation,
  DashboardSnapshot,
} from '../../services/student-dashboard-data.service';

@Component({
  selector: 'app-creation-center-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule, MatTooltipModule],
  template: `
    <mat-card
      class="core-card core-card--creation"
      [class.clickable]="true"
      tabindex="0"
      role="button"
      [attr.aria-label]="'创作中心：' + (topRec?.title || '开始你的创作')"
      (click)="onClick()"
      (keyup.enter)="onClick()"
    >
      <div class="card-icon-wrap">
        <mat-icon>auto_awesome</mat-icon>
      </div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-label">创作中心</span>
          <mat-icon class="card-arrow">arrow_forward</mat-icon>
        </div>

        <!-- AI 推荐项目预览 -->
        <div class="rec-preview" *ngIf="topRec" [style.background]="topRec.gradient">
          <mat-icon class="rec-sparkle">auto_awesome</mat-icon>
          <div class="rec-info">
            <div class="rec-title">{{ topRec.title }}</div>
            <div class="rec-desc">{{ topRec.description }}</div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="quick-entries">
          <button
            class="entry-btn"
            mat-button
            (click)="onAiCoding($event)"
            [matTooltip]="'AI 编程：' + (topRec?.title || '开始')"
          >
            <mat-icon>code</mat-icon>
            <span>AI 编程</span>
          </button>
          <button class="entry-btn" mat-button (click)="onMaterials($event)" matTooltip="课件库">
            <mat-icon>folder</mat-icon>
            <span>课件库</span>
          </button>
          <button class="entry-btn" mat-button (click)="onProjects($event)" matTooltip="实战项目">
            <mat-icon>rocket_launch</mat-icon>
            <span>实战</span>
          </button>
        </div>

        <div class="rec-counter" *ngIf="recsCount > 1">+{{ recsCount - 1 }} 个推荐项目等你探索</div>
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
          color: var(--stem-secondary, #0ea5e9);
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
        background: var(--stem-gradient-sky, linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%));
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

      .rec-preview {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.25);
      }

      .rec-sparkle {
        flex-shrink: 0;
        width: 24px;
        height: 24px;
        font-size: 24px;
      }

      .rec-info {
        flex: 1;
        min-width: 0;
      }

      .rec-title {
        margin-bottom: 2px;
        font-size: 13px;
        font-weight: 700;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .rec-desc {
        opacity: 0.9;
        font-size: 11px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .quick-entries {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        margin-top: 2px;
      }

      .entry-btn {
        display: flex !important;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        min-height: 48px !important;
        padding: 6px 4px !important;
        border-radius: 10px !important;
        background: var(--matux-color-background, #f1f5f9) !important;
        color: var(--matux-color-text-secondary, #57534e) !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        transition:
          background 200ms ease,
          color 200ms ease;
      }

      .entry-btn mat-icon {
        width: 18px;
        height: 18px;
        font-size: 18px;
      }

      .entry-btn:hover {
        background: var(--stem-secondary, #0ea5e9) !important;
        color: white !important;
      }

      .rec-counter {
        margin-top: 2px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
        text-align: center;
      }
    `,
  ],
})
export class CreationCenterCardComponent {
  @Input() snapshot: DashboardSnapshot | null = null;
  @Output() navigate = new EventEmitter<string>();

  get topRec(): AiRecommendation | null {
    const recs = this.snapshot?.aiRecommendations ?? [];
    return recs[0] ?? null;
  }

  get recsCount(): number {
    return this.snapshot?.aiRecommendations?.length ?? 0;
  }

  onClick(): void {
    this.navigate.emit('/ai-edu/coding');
  }

  onAiCoding(event: Event): void {
    event.stopPropagation();
    this.navigate.emit('/ai-edu/coding');
  }

  onMaterials(event: Event): void {
    event.stopPropagation();
    this.navigate.emit('/user/materials');
  }

  onProjects(event: Event): void {
    event.stopPropagation();
    this.navigate.emit('/student/projects');
  }
}
