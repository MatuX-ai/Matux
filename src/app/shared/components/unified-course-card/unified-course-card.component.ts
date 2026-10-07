/**
 * 统一课程卡片组件
 * 用于在课程列表中展示课程信息
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import type { UnifiedCourse } from '../../../models/unified-course.models';

export interface UnifiedCourseCardConfig {
  course: UnifiedCourse;
  showEnrollButton?: boolean;
  showProgress?: boolean;
  enrollmentStatus?: string;
  enrollmentProgress?: number;
  orgName?: string;
  compact?: boolean;
}

@Component({
  selector: 'app-unified-course-card',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressBarModule,
  ],
  template: `
    <mat-card class="course-card" [class.compact]="config?.compact">
      <mat-card-header>
        <mat-card-title>{{ config?.course?.title || '课程' }}</mat-card-title>
        <mat-card-subtitle>
          <span *ngIf="config?.course?.teacher_name">{{ config?.course?.teacher_name }}</span>
          <span *ngIf="config?.orgName"> | {{ config?.orgName }}</span>
        </mat-card-subtitle>
      </mat-card-header>
      <mat-card-content>
        <p *ngIf="config?.course?.description" class="description">
          {{ config?.course?.description }}
        </p>
        <div class="meta">
          <mat-chip-set>
            <mat-chip>{{ config?.course?.difficulty || '初级' }}</mat-chip>
            <mat-chip>{{ config?.course?.duration_minutes || 0 }}分钟</mat-chip>
          </mat-chip-set>
        </div>
        <mat-progress-bar
          *ngIf="config?.showProgress"
          mode="determinate"
          [value]="config?.enrollmentProgress ?? 0"
        >
        </mat-progress-bar>
      </mat-card-content>
      <mat-card-actions *ngIf="config?.showEnrollButton">
        <button mat-raised-button color="primary" (click)="onEnroll()">立即报名</button>
        <button mat-button (click)="onDetail()">查看详情</button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-light: #10b981;
        --stem-secondary: #0ea5e9;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-radius-lg: 20px;
        --stem-radius-md: 12px;
        --stem-shadow-sm: 0 1px 3px rgba(5, 150, 105, 0.08);
        --stem-shadow-card-hover: 0 14px 28px rgba(5, 150, 105, 0.12);
        --stem-gradient-explore: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);
      }

      .course-card {
        margin-bottom: 16px;
        // STEM 20px 圆角
        border-radius: var(--stem-radius-lg, 20px);
        // STEM 阴影
        box-shadow: var(--stem-shadow-sm);
        // STEM 悬浮效果
        transition:
          box-shadow 250ms cubic-bezier(0.4, 0, 0.2, 1),
          transform 250ms ease;

        &:hover {
          box-shadow: var(--stem-shadow-card-hover);
          transform: translateY(-2px);
        }

        // STEM 主题按钮颜色
        ::ng-deep .mat-mdc-raised-button.mat-primary {
          background: var(--stem-gradient-explore);
          border-radius: 9999px;
        }
      }

      .course-card.compact {
        max-width: 320px;
      }

      .description {
        // STEM 主题文本色
        color: var(--stem-text-secondary, #57534e);
        font-size: 14px;
        line-height: 1.6;
      }

      .meta {
        margin: 12px 0;
      }

      mat-progress-bar {
        margin-top: 8px;
        // STEM 进度条样式
        --mdc-linear-progress-active-indicator-color: var(--stem-primary, #059669);
        --mdc-linear-progress-track-color: var(--stem-primary-100, #d1fae5);
      }
    `,
  ],
})
export class UnifiedCourseCardComponent {
  @Input() config: UnifiedCourseCardConfig | null = null;
  @Output() enroll = new EventEmitter<number>();
  @Output() detail = new EventEmitter<number>();

  onEnroll(): void {
    if (this.config?.course?.id) {
      this.enroll.emit(this.config.course.id);
    }
  }

  onDetail(): void {
    if (this.config?.course?.id) {
      this.detail.emit(this.config.course.id);
    }
  }
}
