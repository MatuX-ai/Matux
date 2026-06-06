/**
 * 成就进度追踪组件
 *
 * 展示用户成就完成进度、里程碑和统计数据
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, OnDestroy, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  AchievementProgress,
  ProgressMilestone,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-progress',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  template: `
    <div class="progress-container">
      <!-- 统计概览卡片 -->
      <mat-card class="stats-card">
        <mat-card-content>
          <div class="stats-header">
            <h3>学习成就概览</h3>
            <span class="completion-badge">{{ progress.completionPercentage }}%</span>
          </div>

          <div class="main-progress">
            <mat-progress-bar
              mode="determinate"
              [value]="progress.completionPercentage"
            ></mat-progress-bar>
          </div>

          <div class="stats-row">
            <div class="stat">
              <mat-icon>emoji_events</mat-icon>
              <div class="stat-info">
                <span class="stat-value">{{ progress.totalAchievements }}</span>
                <span class="stat-label">总成就</span>
              </div>
            </div>
            <div class="stat">
              <mat-icon>stars</mat-icon>
              <div class="stat-info">
                <span class="stat-value">{{ progress.completedAchievements }}</span>
                <span class="stat-label">已完成</span>
              </div>
            </div>
            <div class="stat">
              <mat-icon>trending_up</mat-icon>
              <div class="stat-info">
                <span class="stat-value">{{ progress.averageScore }}</span>
                <span class="stat-label">平均分</span>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 里程碑列表 -->
      <div class="milestones-section">
        <h3>进度里程碑</h3>
        <div class="milestones-list" *ngIf="progress.milestones?.length; else noMilestones">
          <div
            class="milestone-item"
            *ngFor="let milestone of progress.milestones"
            [class.completed]="milestone.completed"
          >
            <div class="milestone-icon">
              <mat-icon>{{ milestone.icon }}</mat-icon>
            </div>
            <div class="milestone-content">
              <div class="milestone-header">
                <span class="milestone-title">{{ milestone.title }}</span>
                <span class="milestone-status">
                  {{ milestone.completed ? '已完成' : milestone.progress + '/' + milestone.target }}
                </span>
              </div>
              <p class="milestone-desc">{{ milestone.description }}</p>
              <mat-progress-bar
                mode="determinate"
                [value]="milestone.completed ? 100 : (milestone.progress / milestone.target) * 100"
              ></mat-progress-bar>
            </div>
          </div>
        </div>
        <ng-template #noMilestones>
          <mat-card class="empty-card">
            <mat-card-content>
              <mat-icon>flag</mat-icon>
              <p>暂无里程碑数据</p>
            </mat-card-content>
          </mat-card>
        </ng-template>
      </div>
    </div>
  `,
  styles: [
    `
      .progress-container {
        padding: 16px;
        max-width: 900px;
        margin: 0 auto;
      }

      .stats-card {
        margin-bottom: 24px;
      }

      .stats-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }

      .stats-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .completion-badge {
        font-size: 24px;
        font-weight: 700;
        color: var(--color-primary, #1976d2);
      }

      .main-progress {
        margin-bottom: 20px;
      }

      .stats-row {
        display: flex;
        justify-content: space-around;
        gap: 12px;
      }

      .stat {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .stat mat-icon {
        font-size: 24px;
        width: 24px;
        height: 24px;
        color: var(--color-primary, #1976d2);
      }

      .stat-info {
        display: flex;
        flex-direction: column;
      }

      .stat-value {
        font-size: 18px;
        font-weight: 700;
        color: var(--color-text-primary, #212121);
      }

      .stat-label {
        font-size: 12px;
        color: var(--color-text-secondary, #666);
      }

      .milestones-section {
        margin-top: 8px;
      }

      .milestones-section h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--color-text-primary, #212121);
      }

      .milestones-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .milestone-item {
        display: flex;
        gap: 16px;
        padding: 16px;
        border-radius: 12px;
        background: var(--color-surface, #fff);
        border: 1px solid var(--color-border, #e0e0e0);
        transition: transform 0.2s;
      }

      .milestone-item.completed {
        border-color: var(--color-success, #4caf50);
        background: var(--color-success-bg, #f1f8e9);
      }

      .milestone-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--color-primary-bg, #e3f2fd);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .milestone-icon mat-icon {
        color: var(--color-primary, #1976d2);
      }

      .milestone-content {
        flex: 1;
        min-width: 0;
      }

      .milestone-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
      }

      .milestone-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--color-text-primary, #212121);
      }

      .milestone-status {
        font-size: 12px;
        color: var(--color-text-secondary, #666);
      }

      .milestone-desc {
        font-size: 12px;
        color: var(--color-text-secondary, #666);
        margin: 0 0 8px;
      }

      .empty-card {
        text-align: center;
        padding: 32px;
        color: var(--color-text-secondary, #999);
      }

      .empty-card mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 12px;
      }
    `,
  ],
})
export class AchievementProgressComponent implements OnInit, OnDestroy {
  @Input() userId!: number;

  progress: AchievementProgress = {
    totalBadges: 0,
    unlockedBadges: 0,
    overallProgress: 0,
    completionPercentage: 0,
    averageScore: 0,
    totalAchievements: 0,
    completedAchievements: 0,
    categoryProgress: {} as Record<string, number>,
    recentUnlocks: [],
    milestones: [],
  };

  private destroy$ = new Subject<void>();

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadProgress();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadProgress(): void {
    if (!this.userId) {
      return;
    }

    this.achievementService
      .getUserAchievementProgress(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((progress) => {
        this.progress = progress;
      });
  }
}
