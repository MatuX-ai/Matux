/**
 * 学习来源进度组件
 * 通用组件，展示跨机构/兴趣班的学习进度
 * 可用于学生仪表板和家长仪表板
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';

import {
  LearningSourceType,
  LearningSourceTypeLabels,
  UnifiedProgressStats,
} from '../../../models/multi-source-learning.models';

/** 学习来源项展示模型 */
export interface LearningSourceDisplayItem {
  sourceType: LearningSourceType;
  sourceName: string;
  courses: number;
  completed: number;
  avgScore: number | null;
  totalTime: number;
  progressPercentage: number;
}

@Component({
  selector: 'app-learning-source-progress',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatChipsModule,
    MatTabsModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="learning-source-progress">
      <!-- 总体统计 -->
      <div class="overall-stats" *ngIf="showOverallStats">
        <div class="stat-item">
          <mat-icon color="primary">school</mat-icon>
          <div class="stat-content">
            <span class="stat-value">{{ stats?.total_courses || 0 }}</span>
            <span class="stat-label">总课程数</span>
          </div>
        </div>
        <div class="stat-item">
          <mat-icon color="accent">check_circle</mat-icon>
          <div class="stat-content">
            <span class="stat-value">{{ stats?.completed_courses || 0 }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </div>
        <div class="stat-item">
          <mat-icon color="warn">pending</mat-icon>
          <div class="stat-content">
            <span class="stat-value">{{ stats?.in_progress_courses || 0 }}</span>
            <span class="stat-label">进行中</span>
          </div>
        </div>
        <div class="stat-item">
          <mat-icon>schedule</mat-icon>
          <div class="stat-content">
            <span class="stat-value">{{ formatTime(stats?.total_time_minutes || 0) }}</span>
            <span class="stat-label">总学习时长</span>
          </div>
        </div>
        <div class="stat-item" *ngIf="stats?.average_score !== null">
          <mat-icon>grade</mat-icon>
          <div class="stat-content">
            <span class="stat-value">{{ stats?.average_score | number: '1.1-1' }}</span>
            <span class="stat-label">平均成绩</span>
          </div>
        </div>
      </div>

      <!-- 学习来源分类展示 -->
      <div class="source-breakdown" *ngIf="sourceItems.length > 0">
        <h3 class="section-subtitle" *ngIf="showSectionTitle">
          <mat-icon>hub</mat-icon>
          学习来源分布
        </h3>

        <!-- 分类视图切换 -->
        <mat-tab-group [(selectedIndex)]="selectedTabIndex" *ngIf="showTabs">
          <mat-tab label="全部来源">
            <div class="source-grid">
              <mat-card
                *ngFor="let item of sourceItems"
                class="source-card"
                [class.source-school]="isSchoolSource(item.sourceType)"
                [class.source-interest]="item.sourceType === 'school_interest'"
                [class.source-institution]="item.sourceType === 'institution'"
                [class.source-online]="item.sourceType === 'online_platform'"
                [class.source-competition]="item.sourceType === 'competition'"
                [class.source-self]="item.sourceType === 'self_study'"
              >
                <mat-card-header>
                  <mat-card-title>
                    <mat-icon [matTooltip]="getSourceTypeLabel(item.sourceType)">
                      {{ getSourceIcon(item.sourceType) }}
                    </mat-icon>
                    {{ item.sourceName }}
                  </mat-card-title>
                  <mat-card-subtitle>
                    <mat-chip-listbox>
                      <mat-chip [color]="getStatusColor(item)" selected>
                        {{ getSourceTypeLabel(item.sourceType) }}
                      </mat-chip>
                    </mat-chip-listbox>
                  </mat-card-subtitle>
                </mat-card-header>
                <mat-card-content>
                  <div class="source-stats">
                    <div class="source-stat">
                      <span class="label">课程数</span>
                      <span class="value">{{ item.courses }}</span>
                    </div>
                    <div class="source-stat">
                      <span class="label">已完成</span>
                      <span class="value completed">{{ item.completed }}</span>
                    </div>
                    <div class="source-stat">
                      <span class="label">学习时长</span>
                      <span class="value">{{ formatTime(item.totalTime) }}</span>
                    </div>
                    <div class="source-stat" *ngIf="item.avgScore !== null">
                      <span class="label">平均分</span>
                      <span
                        class="value"
                        [class.score-high]="item.avgScore >= 90"
                        [class.score-good]="item.avgScore >= 80 && item.avgScore < 90"
                        [class.score-low]="item.avgScore < 80"
                      >
                        {{ item.avgScore | number: '1.1-1' }}
                      </span>
                    </div>
                  </div>
                  <div class="progress-section" *ngIf="item.courses > 0">
                    <div class="progress-header">
                      <span>总体进度</span>
                      <span class="progress-percent">{{ item.progressPercentage }}%</span>
                    </div>
                    <mat-progress-bar
                      [value]="item.progressPercentage"
                      [color]="getProgressColor(item.progressPercentage)"
                    >
                    </mat-progress-bar>
                  </div>
                </mat-card-content>
                <mat-card-actions *ngIf="showActions">
                  <button
                    mat-button
                    color="primary"
                    [matTooltip]="'查看' + item.sourceName + '详情'"
                  >
                    <mat-icon>visibility</mat-icon>
                    查看详情
                  </button>
                </mat-card-actions>
              </mat-card>
            </div>
          </mat-tab>

          <!-- 按类型筛选标签页 -->
          <mat-tab *ngFor="let type of sourceTypes" [label]="getSourceTypeLabel(type)">
            <ng-template matTabContent>
              <div class="source-grid">
                <mat-card
                  *ngFor="let item of getItemsByType(type)"
                  class="source-card"
                  [class]="'source-' + type"
                >
                  <mat-card-header>
                    <mat-card-title>
                      <mat-icon>{{ getSourceIcon(type) }}</mat-icon>
                      {{ item.sourceName }}
                    </mat-card-title>
                  </mat-card-header>
                  <mat-card-content>
                    <div class="source-stats">
                      <div class="source-stat">
                        <span class="label">课程数</span>
                        <span class="value">{{ item.courses }}</span>
                      </div>
                      <div class="source-stat">
                        <span class="label">已完成</span>
                        <span class="value completed">{{ item.completed }}</span>
                      </div>
                      <div class="source-stat">
                        <span class="label">学习时长</span>
                        <span class="value">{{ formatTime(item.totalTime) }}</span>
                      </div>
                    </div>
                    <div class="progress-section" *ngIf="item.courses > 0">
                      <mat-progress-bar
                        [value]="item.progressPercentage"
                        [color]="getProgressColor(item.progressPercentage)"
                      >
                      </mat-progress-bar>
                    </div>
                  </mat-card-content>
                </mat-card>
                <div class="empty-type" *ngIf="getItemsByType(type).length === 0">
                  <mat-icon>info</mat-icon>
                  <p>暂无{{ getSourceTypeLabel(type) }}学习记录</p>
                </div>
              </div>
            </ng-template>
          </mat-tab>
        </mat-tab-group>

        <!-- 简单列表视图（不带标签页） -->
        <div class="source-grid simple" *ngIf="!showTabs">
          <mat-card
            *ngFor="let item of sourceItems"
            class="source-card"
            [class]="'source-' + item.sourceType"
          >
            <mat-card-header>
              <mat-card-title>
                <mat-icon>{{ getSourceIcon(item.sourceType) }}</mat-icon>
                {{ item.sourceName }}
              </mat-card-title>
              <mat-card-subtitle>{{ getSourceTypeLabel(item.sourceType) }}</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <div class="source-stats compact">
                <div class="source-stat">
                  <span class="label">课程</span>
                  <span class="value">{{ item.completed }}/{{ item.courses }}</span>
                </div>
                <div class="source-stat" *ngIf="item.avgScore !== null">
                  <span class="label">均分</span>
                  <span class="value">{{ item.avgScore | number: '1.1-1' }}</span>
                </div>
                <div class="source-stat">
                  <span class="label">时长</span>
                  <span class="value">{{ formatTime(item.totalTime) }}</span>
                </div>
              </div>
              <mat-progress-bar
                *ngIf="item.courses > 0"
                [value]="item.progressPercentage"
                [color]="getProgressColor(item.progressPercentage)"
              >
              </mat-progress-bar>
            </mat-card-content>
          </mat-card>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" *ngIf="!stats && !loading">
        <mat-icon>school</mat-icon>
        <p>暂无学习来源记录</p>
        <span>添加学习来源后，这里将显示您的跨机构学习进度</span>
      </div>

      <!-- 加载状态 -->
      <div class="loading-state" *ngIf="loading">
        <mat-progress-spinner diameter="40" mode="indeterminate"></mat-progress-spinner>
        <p>加载学习进度中...</p>
      </div>
    </div>
  `,
  styles: [
    `
      .learning-source-progress {
        width: 100%;
      }

      /* 总体统计 */
      .overall-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        padding: 20px;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 12px;
        margin-bottom: 24px;
      }

      .stat-item {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        min-width: 120px;

        mat-icon {
          font-size: 32px;
          width: 32px;
          height: 32px;
          color: #666;
        }
      }

      .stat-content {
        display: flex;
        flex-direction: column;
      }

      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: #333;
      }

      .stat-label {
        font-size: 12px;
        color: #666;
      }

      /* 章节标题 */
      .section-subtitle {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 600;
        color: #333;
        margin-bottom: 16px;

        mat-icon {
          color: #666;
        }
      }

      /* 来源卡片网格 */
      .source-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
        padding: 16px 0;

        &.simple {
          grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        }
      }

      /* 来源卡片 */
      .source-card {
        transition:
          transform 0.2s,
          box-shadow 0.2s;

        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        mat-card-header {
          margin-bottom: 12px;
        }

        mat-card-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 16px;

          mat-icon {
            font-size: 20px;
            width: 20px;
            height: 20px;
          }
        }

        mat-card-subtitle {
          margin-top: 8px;
        }
      }

      /* 来源类型颜色 */
      .source-school {
        border-left: 4px solid #10b981;
      }

      .source-school_interest {
        border-left: 4px solid #f59e0b;
      }

      .source-institution {
        border-left: 4px solid #3b82f6;
      }

      .source-online_platform {
        border-left: 4px solid #8b5cf6;
      }

      .source-competition {
        border-left: 4px solid #ef4444;
      }

      .source-self_study {
        border-left: 4px solid #64748b;
      }

      /* 来源统计 */
      .source-stats {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 16px;

        &.compact {
          grid-template-columns: repeat(3, 1fr);
          margin-bottom: 8px;
        }
      }

      .source-stat {
        display: flex;
        flex-direction: column;

        .label {
          font-size: 12px;
          color: #666;
        }

        .value {
          font-size: 18px;
          font-weight: 600;
          color: #333;

          &.completed {
            color: #10b981;
          }

          &.score-high {
            color: #10b981;
          }

          &.score-good {
            color: #f59e0b;
          }

          &.score-low {
            color: #ef4444;
          }
        }
      }

      /* 进度部分 */
      .progress-section {
        .progress-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 13px;
          color: #666;
        }

        .progress-percent {
          font-weight: 600;
          color: #333;
        }
      }

      /* 空状态 */
      .empty-state,
      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px;
        text-align: center;
        color: #666;

        mat-icon {
          font-size: 64px;
          width: 64px;
          height: 64px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        p {
          font-size: 16px;
          margin-bottom: 8px;
        }

        span {
          font-size: 14px;
          color: #999;
        }
      }

      .empty-type {
        grid-column: 1 / -1;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 32px;
        color: #999;

        mat-icon {
          font-size: 32px;
          width: 32px;
          height: 32px;
          margin-bottom: 8px;
        }
      }

      /* 响应式 */
      @media (max-width: 768px) {
        .overall-stats {
          flex-direction: column;
        }

        .source-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class LearningSourceProgressComponent implements OnChanges {
  /** 统一进度统计数据 */
  @Input() stats: UnifiedProgressStats | null = null;

  /** 加载状态 */
  @Input() loading = false;

  /** 显示总体统计 */
  @Input() showOverallStats = true;

  /** 显示分区标签页 */
  @Input() showTabs = false;

  /** 显示操作按钮 */
  @Input() showActions = false;

  /** 显示区块标题 */
  @Input() showSectionTitle = true;

  /** 用户类型：student/parent */
  @Input() userType: 'student' | 'parent' = 'student';

  /** 解析后的学习来源项 */
  sourceItems: LearningSourceDisplayItem[] = [];

  /** 选中的标签页索引 */
  selectedTabIndex = 0;

  /** 学习来源类型列表 */
  sourceTypes: LearningSourceType[] = [
    'school_curriculum',
    'school_interest',
    'institution',
    'online_platform',
    'competition',
    'self_study',
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['stats'] && this.stats) {
      this.parseSourceBreakdown();
    }
  }

  /** 解析来源分布数据 */
  private parseSourceBreakdown(): void {
    if (!this.stats?.source_breakdown) {
      this.sourceItems = [];
      return;
    }

    this.sourceItems = this.stats.source_breakdown.map(
      (item: {
        source_type: LearningSourceType;
        source_name: string;
        courses: number;
        completed: number;
        avg_score: number | null;
        total_time: number;
      }) => ({
        sourceType: item.source_type,
        sourceName: item.source_name,
        courses: item.courses,
        completed: item.completed,
        avgScore: item.avg_score,
        totalTime: item.total_time,
        progressPercentage:
          item.courses > 0 ? Math.round((item.completed / item.courses) * 100) : 0,
      })
    );
  }

  /** 获取特定类型的项 */
  getItemsByType(type: LearningSourceType): LearningSourceDisplayItem[] {
    return this.sourceItems.filter((item) => item.sourceType === type);
  }

  /** 获取来源类型标签 */
  getSourceTypeLabel(type: LearningSourceType): string {
    return LearningSourceTypeLabels[type] || type;
  }

  /** 获取来源类型图标 */
  getSourceIcon(type: LearningSourceType): string {
    const icons: Record<LearningSourceType, string> = {
      school_curriculum: 'school',
      school_interest: 'palette',
      institution: 'business',
      self_study: 'self_improvement',
      online_platform: 'computer',
      competition: 'emoji_events',
    };
    return icons[type] || 'source';
  }

  /** 判断是否为学校来源 */
  isSchoolSource(type: LearningSourceType): boolean {
    return type === 'school_curriculum';
  }

  /** 获取状态颜色 */
  getStatusColor(item: LearningSourceDisplayItem): string {
    if (item.progressPercentage >= 80) return 'primary';
    if (item.progressPercentage >= 50) return 'accent';
    return 'warn';
  }

  /** 获取进度条颜色 */
  getProgressColor(percentage: number): 'primary' | 'accent' | 'warn' {
    if (percentage >= 80) return 'primary';
    if (percentage >= 50) return 'accent';
    return 'warn';
  }

  /** 格式化学习时长 */
  formatTime(minutes: number): string {
    if (minutes < 60) {
      return `${minutes}分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours < 24) {
      return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`;
    }
    const days = Math.floor(hours / 24);
    const remainHours = hours % 24;
    return remainHours > 0 ? `${days}天${remainHours}小时` : `${days}天`;
  }
}
