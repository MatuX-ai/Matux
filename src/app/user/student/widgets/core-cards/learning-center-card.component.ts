/**
 * 学习中心卡 - 核心 dashboard 卡 #1
 *
 * 内容：
 * - 继续学习课程（top 1 进度条 + 课程列表）
 * - 本周学习统计（时长 / 任务数 / 积分）
 * - AI 编程入口
 *
 * 视觉：探索绿渐变 + 卡片式布局
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ROUTES } from '../../../../routes.const';
import type { DashboardSnapshot, WeeklyStats } from '../../services/student-dashboard-data.service';

interface ContinueCourse {
  id: number;
  title: string;
  teacher: string;
  progress: number;
  level: string;
  duration: string;
  sourceType: string;
  sourceName: string;
}

@Component({
  selector: 'app-learning-center-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  template: `
    <mat-card
      class="core-card core-card--learning"
      [class.clickable]="true"
      tabindex="0"
      role="button"
      [attr.aria-label]="'学习中心：本周学习 ' + weeklyStats.hoursThisWeek + ' 小时'"
      (click)="onContinue()"
      (keyup.enter)="onContinue()"
    >
      <div class="card-icon-wrap">
        <mat-icon>school</mat-icon>
      </div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-label">学习中心</span>
          <mat-icon class="card-arrow">arrow_forward</mat-icon>
        </div>
        <div class="card-title-row">
          <h3 class="card-title">
            {{ topCourse?.title || '尚无进行中课程' }}
          </h3>
        </div>
        <mat-progress-bar
          *ngIf="topCourse"
          mode="determinate"
          [value]="topCourse.progress"
        ></mat-progress-bar>

        <div class="weekly-stats">
          <div class="stat-item">
            <mat-icon class="stat-icon">schedule</mat-icon>
            <div class="stat-content">
              <span class="stat-value">{{ weeklyStats.hoursThisWeek }}</span>
              <span class="stat-unit">小时</span>
              <span class="stat-trend" *ngIf="weeklyStats.weekComparison.hoursChange > 0">
                ↑ {{ weeklyStats.weekComparison.hoursChange }}
              </span>
            </div>
          </div>
          <div class="stat-item">
            <mat-icon class="stat-icon">task_alt</mat-icon>
            <div class="stat-content">
              <span class="stat-value">{{ weeklyStats.tasksCount }}</span>
              <span class="stat-unit">任务</span>
            </div>
          </div>
          <div class="stat-item">
            <mat-icon class="stat-icon">bolt</mat-icon>
            <div class="stat-content">
              <span class="stat-value">{{ weeklyStats.pointsEarned }}</span>
              <span class="stat-unit">EXP</span>
            </div>
          </div>
        </div>

        <div class="card-meta">
          <span class="meta-item" *ngIf="topCourse">
            <mat-icon>person</mat-icon>
            {{ topCourse.teacher }}
          </span>
          <span class="meta-item ai-coding" (click)="onAiCoding($event)">
            <mat-icon>code</mat-icon>
            AI 编程
          </span>
        </div>

        <!-- 【P0 修复】学习画像 / 教学建议快捷入口 -->
        <div class="card-quicklinks">
          <button
            type="button"
            class="quicklink-btn"
            (click)="onProfile($event)"
            aria-label="查看学习画像"
          >
            <mat-icon>insights</mat-icon>
            学习画像
          </button>
          <button
            type="button"
            class="quicklink-btn"
            (click)="onTeachingSuggestions($event)"
            aria-label="查看教学建议"
          >
            <mat-icon>lightbulb</mat-icon>
            教学建议
          </button>
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
          color: var(--stem-primary, #059669);
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
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #10b981 100%));
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

      .card-title {
        margin: 0;
        overflow: hidden;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 16px;
        font-weight: 700;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .weekly-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 4px;
        padding: 10px 0;
        border-radius: 12px;
        background: var(--matux-color-background, #f1f5f9);
      }

      .stat-item {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 4px;
      }

      .stat-item .stat-icon {
        width: 18px;
        height: 18px;
        color: var(--stem-primary, #059669);
        font-size: 18px;
      }

      .stat-content {
        display: flex;
        align-items: baseline;
        gap: 2px;
      }

      .stat-value {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 18px;
        font-weight: 700;
      }

      .stat-unit {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
      }

      .stat-trend {
        margin-left: 4px;
        color: var(--stem-success, #059669);
        font-size: 10px;
        font-weight: 600;
      }

      .card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 4px;
      }

      .meta-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 12px;
      }

      .meta-item mat-icon {
        width: 14px;
        height: 14px;
        font-size: 14px;
      }

      .ai-coding {
        padding: 4px 10px;
        border-radius: 12px;
        background: var(--stem-gradient-ai, linear-gradient(135deg, #059669 0%, #0ea5e9 100%));
        color: white !important;
        cursor: pointer;
        font-weight: 600;
        transition: transform 200ms ease;
      }

      .ai-coding:hover {
        transform: translateY(-1px);
      }

      .card-quicklinks {
        display: flex;
        gap: 8px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px dashed var(--matux-color-divider, #e2e8f0);
      }

      .quicklink-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        border: 1px solid var(--matux-color-divider, #e2e8f0);
        border-radius: 12px;
        background: var(--matux-color-background, #f8fafc);
        color: var(--matux-color-text-secondary, #475569);
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 200ms ease;
      }

      .quicklink-btn:hover {
        border-color: var(--stem-primary, #059669);
        background: var(--stem-primary-50, #ecfdf5);
        color: var(--stem-primary-dark, #047857);
        transform: translateY(-1px);
      }

      .quicklink-btn mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }
    `,
  ],
})
export class LearningCenterCardComponent {
  @Input() snapshot: DashboardSnapshot | null = null;
  @Output() navigate = new EventEmitter<string>();
  @Output() aiCoding = new EventEmitter<void>();

  get weeklyStats(): WeeklyStats {
    return (
      this.snapshot?.weeklyStats ?? {
        hoursThisWeek: 0,
        tasksCount: 0,
        pointsEarned: 0,
        streakDays: 0,
        weekComparison: { hoursChange: 0, tasksChange: 0, pointsChange: 0 },
      }
    );
  }

  get topCourse(): ContinueCourse | null {
    const courses = this.snapshot?.continueLearning?.courses ?? [];
    return courses[0] ?? null;
  }

  onContinue(): void {
    const course = this.topCourse;
    if (course) {
      this.navigate.emit(`/student/course/${course.id}/learn`);
    } else {
      this.navigate.emit('/user/courses');
    }
  }

  onAiCoding(event: Event): void {
    event.stopPropagation();
    this.aiCoding.emit();
  }

  /** 【P0 修复】跳转学习画像 */
  onProfile(event: Event): void {
    event.stopPropagation();
    this.navigate.emit(ROUTES.USER.LEARNING_PROFILE);
  }

  /** 【P0 修复】跳转教学建议 */
  onTeachingSuggestions(event: Event): void {
    event.stopPropagation();
    this.navigate.emit(ROUTES.USER.TEACHING_SUGGESTIONS);
  }
}
