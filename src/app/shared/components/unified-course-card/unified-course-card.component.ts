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
      .course-card {
        margin-bottom: 16px;
      }
      .course-card.compact {
        max-width: 320px;
      }
      .description {
        color: #666;
        font-size: 14px;
        line-height: 1.5;
      }
      .meta {
        margin: 12px 0;
      }
      mat-progress-bar {
        margin-top: 8px;
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
