/**
 * 家长用户中心 - 家长仪表板
 *
 * 展示孩子的学习情况、成绩报告等信息
 * 集成多来源学习系统，显示按机构/兴趣班分类的孩子学习进度
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { Subject } from 'rxjs';
import { of } from 'rxjs';
import { catchError, takeUntil } from 'rxjs/operators';

import { AuthService } from '../../core/services/auth.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import {
  LearningSource,
  LearningSourceType,
  LearningSourceTypeLabels,
  UnifiedProgressStats,
} from '../../models/multi-source-learning.models';
import { LearningSourceProgressComponent } from '../../shared/components/learning-source-progress/learning-source-progress.component';
import {
  StatsCardComponent,
  StatsCardConfig,
} from '../../shared/components/stats-card/stats-card.component';

interface ChildWithSources {
  name: string;
  grade: string;
  avatar: string;
  weeklyStudyTime: number;
  averageScore: number;
  completedAssignments: number;
  totalAssignments: number;
  recentActivities: string[];
  learningSources: LearningSource[];
  progressStats: UnifiedProgressStats | null;
}

@Component({
  selector: 'app-parent-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatTableModule,
    MatChipsModule,
    MatTabsModule,
    MatProgressBarModule,
    MatExpansionModule,
    LearningSourceProgressComponent,
    StatsCardComponent,
  ],
  template: `
    <div class="parent-dashboard">
      <h1 class="page-title">家长仪表板</h1>

      <!-- 统计卡片 -->
      <div class="stats-grid">
        <app-stats-card [config]="statsConfig.childCount"></app-stats-card>
        <app-stats-card [config]="statsConfig.weeklyAssignments"></app-stats-card>
        <app-stats-card [config]="statsConfig.pendingItems"></app-stats-card>
        <app-stats-card [config]="statsConfig.tokenBalance"></app-stats-card>
      </div>

      <!-- 孩子学习情况 - 增强版：包含机构/兴趣班进度 -->
      <div class="section">
        <h2 class="section-title">
          <mat-icon>school</mat-icon>
          孩子学习情况
        </h2>

        <mat-tab-group>
          <mat-tab *ngFor="let child of children" [label]="child.name + '的学习进度'">
            <div class="child-detail">
              <!-- 孩子基本信息 -->
              <mat-card class="child-info-card">
                <mat-card-header>
                  <div mat-card-avatar class="child-avatar">
                    <img [src]="child.avatar || 'assets/icons/user.svg'" [alt]="child.name" />
                  </div>
                  <mat-card-title>{{ child.name }}</mat-card-title>
                  <mat-card-subtitle>{{ child.grade }}</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content>
                  <div class="child-stats">
                    <div class="stat-item">
                      <span class="stat-label">本周学习时长</span>
                      <span class="stat-value">{{ child.weeklyStudyTime }}小时</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">平均成绩</span>
                      <span
                        class="stat-value"
                        [class.grade-good]="child.averageScore >= 85"
                        [class.grade-average]="child.averageScore < 85"
                      >
                        {{ child.averageScore }}分
                      </span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">完成作业</span>
                      <span class="stat-value"
                        >{{ child.completedAssignments }}/{{ child.totalAssignments }}</span
                      >
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>

              <!-- 跨机构学习进度组件 -->
              <div class="source-progress-section">
                <h3 class="subsection-title">
                  <mat-icon>hub</mat-icon>
                  跨机构/兴趣班学习进度
                </h3>
                <app-learning-source-progress
                  [stats]="child.progressStats"
                  [loading]="loadingChildProgress[child.name]"
                  [showOverallStats]="true"
                  [showTabs]="true"
                  [showActions]="false"
                  [showSectionTitle]="false"
                  userType="parent"
                >
                </app-learning-source-progress>
              </div>

              <!-- 学习来源列表（折叠面板） -->
              <mat-accordion class="sources-accordion" *ngIf="child.learningSources.length > 0">
                <mat-expansion-panel>
                  <mat-expansion-panel-header>
                    <mat-panel-title>
                      <mat-icon>account_balance</mat-icon>
                      学习来源详情 ({{ child.learningSources.length }})
                    </mat-panel-title>
                  </mat-expansion-panel-header>

                  <div class="child-sources-grid">
                    <mat-card
                      *ngFor="let source of child.learningSources"
                      class="child-source-card"
                      [class]="'source-' + source.source_type"
                    >
                      <mat-card-header>
                        <mat-card-title>
                          <mat-icon>{{ getSourceIcon(source.source_type) }}</mat-icon>
                          {{ source.name }}
                        </mat-card-title>
                        <mat-card-subtitle>
                          {{ getSourceTypeLabel(source.source_type) }}
                        </mat-card-subtitle>
                      </mat-card-header>
                      <mat-card-content>
                        <div class="source-status" [class]="'status-' + source.status">
                          <mat-icon>{{ getStatusIcon(source.status) }}</mat-icon>
                          {{ getStatusLabel(source.status) }}
                        </div>
                        <div class="source-dates" *ngIf="source.start_date || source.end_date">
                          <mat-icon>date_range</mat-icon>
                          {{ source.start_date || '待开始' }} ~ {{ source.end_date || '长期' }}
                        </div>
                        <div class="source-role" *ngIf="source.role">
                          <mat-icon>person</mat-icon>
                          角色: {{ source.role }}
                        </div>
                      </mat-card-content>
                    </mat-card>
                  </div>
                </mat-expansion-panel>
              </mat-accordion>

              <!-- 最近活动 -->
              <div class="recent-activity">
                <h4>最近活动</h4>
                <p *ngFor="let activity of child.recentActivities">{{ activity }}</p>
              </div>

              <!-- 操作按钮 -->
              <div class="child-actions">
                <button mat-button>查看详情</button>
                <button mat-button color="primary">学习报告</button>
                <button mat-button color="accent">联系老师</button>
              </div>
            </div>
          </mat-tab>
        </mat-tab-group>
      </div>

      <!-- 成绩趋势 -->
      <div class="section">
        <h2 class="section-title">成绩趋势</h2>
        <mat-card>
          <mat-card-content>
            <table mat-table [dataSource]="gradeTrends" class="grade-table">
              <!-- 科目 -->
              <ng-container matColumnDef="subject">
                <th mat-header-cell *matHeaderCellDef>科目</th>
                <td mat-cell *matCellDef="let trend">{{ trend.subject }}</td>
              </ng-container>

              <!-- 小明 -->
              <ng-container matColumnDef="xiaoming">
                <th mat-header-cell *matHeaderCellDef>小明</th>
                <td mat-cell *matCellDef="let trend">
                  <span
                    [class.grade-excellent]="trend.xiaoming >= 90"
                    [class.grade-good]="trend.xiaoming >= 80 && trend.xiaoming < 90"
                    [class.grade-average]="trend.xiaoming < 80"
                  >
                    {{ trend.xiaoming }}
                  </span>
                </td>
              </ng-container>

              <!-- 小红 -->
              <ng-container matColumnDef="xiaohong">
                <th mat-header-cell *matHeaderCellDef>小红</th>
                <td mat-cell *matCellDef="let trend">
                  <span
                    [class.grade-excellent]="trend.xiaohong >= 90"
                    [class.grade-good]="trend.xiaohong >= 80 && trend.xiaohong < 90"
                    [class.grade-average]="trend.xiaohong < 80"
                  >
                    {{ trend.xiaohong }}
                  </span>
                </td>
              </ng-container>

              <!-- 趋势 -->
              <ng-container matColumnDef="trend">
                <th mat-header-cell *matHeaderCellDef>趋势</th>
                <td mat-cell *matCellDef="let trend">
                  <mat-chip
                    [color]="
                      trend.trend === '上升'
                        ? 'primary'
                        : trend.trend === '稳定'
                          ? 'accent'
                          : 'warn'
                    "
                    selected
                  >
                    {{ trend.trend }}
                  </mat-chip>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="gradeColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: gradeColumns"></tr>
            </table>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [
    `
      .parent-dashboard {
        max-width: 1200px;
        margin: 0 auto;
      }

      .page-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 24px;
        color: #333;
      }

      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
      }

      .section {
        margin-bottom: 40px;
      }

      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        color: #333;

        mat-icon {
          color: #666;
        }
      }

      .subsection-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
        color: #333;

        mat-icon {
          color: #666;
        }
      }

      .children-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 20px;
      }

      .child-detail {
        padding: 20px 0;
      }

      .child-info-card {
        margin-bottom: 24px;
      }

      .child-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        background: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .child-stats {
        margin-bottom: 20px;
      }

      .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }
      }

      .stat-label {
        font-size: 14px;
        color: #666;
      }

      .stat-value {
        font-size: 16px;
        font-weight: 600;
      }

      /* 跨机构进度区域 */
      .source-progress-section {
        margin-bottom: 24px;
        padding: 20px;
        background: #fafafa;
        border-radius: 12px;
      }

      /* 学习来源列表 */
      .sources-accordion {
        margin-bottom: 24px;
      }

      .child-sources-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        padding: 16px 0;
      }

      .child-source-card {
        transition: transform 0.2s;

        &:hover {
          transform: translateY(-2px);
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
            color: #666;
          }
        }

        mat-card-subtitle {
          font-size: 13px;
        }
      }

      .source-school_curriculum {
        border-left: 4px solid #4caf50;
      }

      .source-school_interest {
        border-left: 4px solid #ff9800;
      }

      .source-institution {
        border-left: 4px solid #2196f3;
      }

      .source-online_platform {
        border-left: 4px solid #9c27b0;
      }

      .source-competition {
        border-left: 4px solid #f44336;
      }

      .source-self_study {
        border-left: 4px solid #607d8b;
      }

      .source-status {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        margin-bottom: 8px;

        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
        }

        &.status-active {
          color: #4caf50;
        }

        &.status-inactive {
          color: #999;
        }

        &.status-completed {
          color: #2196f3;
        }

        &.status-suspended {
          color: #ff9800;
        }
      }

      .source-dates,
      .source-role {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;

        mat-icon {
          font-size: 14px;
          width: 14px;
          height: 14px;
        }
      }

      .grade-excellent {
        color: #4caf50;
      }

      .grade-good {
        color: #ff9800;
      }

      .grade-average {
        color: #f44336;
      }

      .recent-activity {
        margin-bottom: 24px;

        h4 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          color: #333;
        }

        p {
          font-size: 14px;
          color: #666;
          margin-bottom: 8px;
          padding-left: 12px;
          position: relative;

          &::before {
            content: '•';
            position: absolute;
            left: 0;
            color: #999;
          }
        }
      }

      .child-actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .grade-table {
        width: 100%;
      }

      @media (max-width: 768px) {
        .stats-grid {
          grid-template-columns: 1fr;
        }

        .children-grid {
          grid-template-columns: 1fr;
        }

        .child-sources-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class ParentDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  gradeColumns: string[] = ['subject', 'xiaoming', 'xiaohong', 'trend'];

  /** 加载状态追踪 */
  loadingChildProgress: Record<string, boolean> = {};

  // 统计卡片配置
  statsConfig: {
    childCount: StatsCardConfig;
    weeklyAssignments: StatsCardConfig;
    pendingItems: StatsCardConfig;
    tokenBalance: StatsCardConfig;
  } = {
    childCount: {
      value: 0,
      label: '孩子数量',
      icon: 'family_restroom',
      color: 'primary',
      clickable: true,
    },
    weeklyAssignments: {
      value: 18,
      label: '本周作业',
      icon: 'assignment',
      color: 'accent',
      clickable: true,
    },
    pendingItems: {
      value: 3,
      label: '待关注事项',
      icon: 'notification_important',
      color: 'warn',
      clickable: true,
    },
    tokenBalance: {
      value: 1500,
      label: 'Token余额',
      icon: 'token',
      color: 'success',
      clickable: true,
    },
  };

  children: ChildWithSources[] = [
    {
      name: '小明',
      grade: '高中一年级',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=xiaoming',
      weeklyStudyTime: 28,
      averageScore: 88,
      completedAssignments: 8,
      totalAssignments: 9,
      recentActivities: [
        '完成了"机器人基础入门"课程的第3章',
        '在"Python机器人控制"作业中获得92分',
        '参加了1次机器人编程在线测验',
      ],
      learningSources: [],
      progressStats: null,
    },
    {
      name: '小红',
      grade: '初中三年级',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=xiaohong',
      weeklyStudyTime: 24,
      averageScore: 92,
      completedAssignments: 10,
      totalAssignments: 10,
      recentActivities: [
        '完成了"AI编程入门"课程',
        '在机器人设计大赛中获得优秀奖',
        '参与了2次机器人社团活动',
      ],
      learningSources: [],
      progressStats: null,
    },
  ];

  gradeTrends = [
    { subject: '机器人基础', xiaoming: 92, xiaohong: 96, trend: '上升' },
    { subject: 'Python编程', xiaoming: 85, xiaohong: 89, trend: '稳定' },
    { subject: 'AI入门', xiaoming: 88, xiaohong: 93, trend: '上升' },
    { subject: '机械设计', xiaoming: 82, xiaohong: 90, trend: '下降' },
    { subject: 'AR/VR', xiaoming: 95, xiaohong: 88, trend: '上升' },
  ];

  // 模拟的孩子用户ID（实际应从后端获取关联的孩子列表）
  private childUserIds: Record<string, number> = {
    小明: 101,
    小红: 102,
  };

  constructor(
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService
  ) {}

  ngOnInit(): void {
    // 加载每个孩子的学习来源和进度
    this.loadChildrenData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadChildrenData(): void {
    this.children.forEach((child) => {
      const childUserId = this.childUserIds[child.name];
      if (childUserId) {
        this.loadChildSources(child.name, childUserId);
        this.loadChildProgress(child.name, childUserId);
      }
    });
  }

  private loadChildSources(childName: string, childUserId: number): void {
    this.loadingChildProgress[childName] = true;
    this.multiSourceService
      .getUserLearningSources(childUserId, { includeInactive: true })
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error(`加载 ${childName} 学习来源失败:`, err);
          // API失败时使用mock数据
          return of({ total: 3, items: this.getMockChildSources(childName) });
        })
      )
      .subscribe((response: any) => {
        const child = this.children.find((c) => c.name === childName);
        if (child) {
          child.learningSources = response.items || [];
        }
      });
  }

  private loadChildProgress(childName: string, childUserId: number): void {
    this.multiSourceService
      .getUserUnifiedProgress(childUserId)
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error(`加载 ${childName} 学习进度失败:`, err);
          // API失败时使用mock数据
          return of(this.getMockChildProgress(childName));
        })
      )
      .subscribe((stats: any) => {
        const child = this.children.find((c) => c.name === childName);
        if (child) {
          child.progressStats = stats;
        }
        this.loadingChildProgress[childName] = false;
      });
  }

  /**
   * 获取Mock孩子学习来源数据
   */
  private getMockChildSources(childName: string): LearningSource[] {
    const now = new Date().toISOString();
    return [
      {
        id: 1,
        user_id: 101,
        org_id: 1,
        name: '校本部',
        source_type: 'school_curriculum' as LearningSourceType,
        status: 'active',
        is_primary: true,
        is_active: true,
        role: 'student',
        source_detail: {},
        start_date: '2025-09-01',
        end_date: '2026-07-31',
        notes: null,
        created_at: now,
        updated_at: now,
      },
      {
        id: 2,
        user_id: 101,
        org_id: 2,
        name: '创新机器人培训中心',
        source_type: 'institution' as LearningSourceType,
        status: 'active',
        is_primary: false,
        is_active: true,
        role: 'student',
        source_detail: {},
        start_date: '2025-10-15',
        end_date: '2026-06-30',
        notes: null,
        created_at: now,
        updated_at: now,
      },
      {
        id: 3,
        user_id: 101,
        org_id: 1,
        name: '校内兴趣班',
        source_type: 'school_interest' as LearningSourceType,
        status: 'active',
        is_primary: false,
        is_active: true,
        role: 'student',
        source_detail: {},
        start_date: '2025-11-01',
        end_date: '2026-05-31',
        notes: null,
        created_at: now,
        updated_at: now,
      },
    ];
  }

  /**
   * 获取Mock孩子学习进度数据
   */
  private getMockChildProgress(childName: string): UnifiedProgressStats {
    // 根据孩子返回不同的mock数据
    if (childName === '小明') {
      return {
        total_courses: 5,
        completed_courses: 2,
        in_progress_courses: 3,
        total_time_minutes: 1250,
        average_score: 88,
        source_breakdown: [
          {
            source_type: 'school_curriculum' as LearningSourceType,
            source_name: '校本部',
            courses: 2,
            completed: 1,
            avg_score: 90,
            total_time: 600,
          },
          {
            source_type: 'school_interest' as LearningSourceType,
            source_name: '校内兴趣班',
            courses: 1,
            completed: 0,
            avg_score: null,
            total_time: 150,
          },
          {
            source_type: 'institution' as LearningSourceType,
            source_name: '创新机器人培训中心',
            courses: 2,
            completed: 1,
            avg_score: 86,
            total_time: 500,
          },
        ],
      };
    } else {
      // 小红
      return {
        total_courses: 4,
        completed_courses: 3,
        in_progress_courses: 1,
        total_time_minutes: 980,
        average_score: 92,
        source_breakdown: [
          {
            source_type: 'school_curriculum' as LearningSourceType,
            source_name: '校本部',
            courses: 2,
            completed: 2,
            avg_score: 94,
            total_time: 480,
          },
          {
            source_type: 'school_interest' as LearningSourceType,
            source_name: '校内兴趣班',
            courses: 1,
            completed: 1,
            avg_score: 90,
            total_time: 200,
          },
          {
            source_type: 'institution' as LearningSourceType,
            source_name: '创新机器人培训中心',
            courses: 1,
            completed: 0,
            avg_score: null,
            total_time: 300,
          },
        ],
      };
    }
  }

  getSourceTypeLabel(type: string): string {
    return LearningSourceTypeLabels[type as keyof typeof LearningSourceTypeLabels] || type;
  }

  getSourceIcon(type: string): string {
    const icons: Record<string, string> = {
      school_curriculum: 'school',
      school_interest: 'palette',
      institution: 'business',
      self_study: 'self_improvement',
      online_platform: 'computer',
      competition: 'emoji_events',
    };
    return icons[type] || 'source';
  }

  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      active: 'play_circle',
      inactive: 'pause_circle',
      completed: 'check_circle',
      suspended: 'warning',
    };
    return icons[status] || 'info';
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: '学习中',
      inactive: '未激活',
      completed: '已完成',
      suspended: '已暂停',
    };
    return labels[status] || status;
  }
}
