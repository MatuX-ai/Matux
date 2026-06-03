/**
 * 学生用户中心 - 学习仪表板
 *
 * 展示学生的学习进度、课程、成绩等信息
 * 集成多来源学习系统，显示跨机构/兴趣班的学习进度
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { forkJoin, Observable, of, Subject } from 'rxjs';
import { catchError, filter, map, switchMap, takeUntil } from 'rxjs/operators';

import type { User } from '../../core/models/auth.models';
import {
  AiEduWebSocketService,
  type ProgressUpdateData,
} from '../../core/services/ai-edu-websocket.service';
import { AuthService } from '../../core/services/auth.service';
import { CourseEnrollmentService } from '../../core/services/course-enrollment.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import { UnifiedCourseService } from '../../core/services/unified-course.service';
import type {
  LearningSource,
  LearningSourceType,
  UnifiedProgressStats,
} from '../../models/multi-source-learning.models';
import { LearningSourceTypeLabels } from '../../models/multi-source-learning.models';
import type { CourseEnrollment, UnifiedCourse } from '../../models/unified-course.models';
import { LearningCalendarHeatmapComponent, type CalendarHeatmapConfig, type DailyLearningRecord } from '../../shared/components/learning-calendar-heatmap/learning-calendar-heatmap.component';
import { LearningSourceProgressComponent } from '../../shared/components/learning-source-progress/learning-source-progress.component';
import {
  StatsCardComponent,
  type StatsCardConfig,
} from '../../shared/components/stats-card/stats-card.component';
import { StudentMaterialDashboardComponent } from '../../shared/components/student-material-dashboard/student-material-dashboard.component';
import { UnifiedCourseCardComponent } from '../../shared/components/unified-course-card/unified-course-card.component';
import { DashboardLayoutService } from '../../core/services/dashboard-layout.service';
import { DashboardLayoutDialogComponent } from '../../shared/components/dashboard-layout-dialog/dashboard-layout-dialog.component';

interface RecentCourse {
  title: string;
  teacher: string;
  progress: number;
  duration: string;
  level: string;
  sourceType?: string;
  sourceName?: string;
}

interface RecommendedCourse {
  title: string;
  teacher: string;
  description: string;
  duration: string;
  level: string;
}

interface AchievementBadge {
  id: string;
  name: string;
  icon: string;
  description: string;
  unlocked: boolean;
  unlockedDate?: string;
}

@Component({
  selector: 'app-student-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatChipsModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatDialogModule,
    LearningSourceProgressComponent,
    LearningCalendarHeatmapComponent,
    StatsCardComponent,
    StudentMaterialDashboardComponent,
    UnifiedCourseCardComponent,
    DashboardLayoutDialogComponent,
  ],
  template: `
    <div class="student-dashboard">
      <div class="page-header">
        <h1 class="page-title">学习仪表板</h1>
        <button mat-stroked-button (click)="openLayoutDialog()" matTooltip="自定义仪表盘布局">
          <mat-icon>dashboard_customize</mat-icon>
          布局
        </button>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-grid" *ngIf="layout.isVisible('stats')">
        <app-stats-card [config]="statsConfig.inProgressCourses"></app-stats-card>
        <app-stats-card [config]="statsConfig.achievements"></app-stats-card>
        <app-stats-card [config]="statsConfig.learningPoints"></app-stats-card>
        <app-stats-card [config]="statsConfig.tokenBalance"></app-stats-card>
      </div>

      <!-- 我的学习来源（原跨机构学习进度） -->
      <div class="section" *ngIf="layout.isVisible('learning_sources')">
        <h2 class="section-title">
          <mat-icon>hub</mat-icon>
          我的学习来源
        </h2>

        <app-learning-source-progress
          [stats]="progressStats"
          [loading]="loadingProgress"
          [showOverallStats]="true"
          [showTabs]="true"
          [showSectionTitle]="false"
          userType="student"
        >
        </app-learning-source-progress>
      </div>

      <!-- 学习来源概览 -->
      <div class="section" *ngIf="layout.isVisible('source_details') && learningSources.length > 0">
        <h2 class="section-title">
          <mat-icon>account_balance</mat-icon>
          学习来源详情
        </h2>
        <div class="sources-grid">
          <mat-card
            *ngFor="let source of learningSources"
            [class.primary-source]="source.is_primary"
          >
            <mat-card-content>
              <div class="source-header">
                <mat-icon [matTooltip]="getSourceTypeLabel(source.source_type)">
                  {{ getSourceIcon(source.source_type) }}
                </mat-icon>
                <span class="source-name">{{ source.name }}</span>
                <mat-chip *ngIf="source.is_primary" color="primary" selected>主来源</mat-chip>
              </div>
              <div class="source-meta">
                <span class="source-type">{{ getSourceTypeLabel(source.source_type) }}</span>
                <span class="source-status" [class]="'status-' + source.status">
                  {{ getStatusLabel(source.status) }}
                </span>
              </div>
              <div class="source-dates" *ngIf="source.start_date || source.end_date">
                <mat-icon>date_range</mat-icon>
                <span>{{ source.start_date || '待开始' }} ~ {{ source.end_date || '长期' }}</span>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      </div>

      <!-- 学习日历热力图 + 成就墙 双栏 -->
      <div class="dual-column-section" *ngIf="layout.isVisible('heatmap') || layout.isVisible('achievements')">
        <!-- 学习日历热力图 -->
        <div class="section section-heatmap" *ngIf="layout.isVisible('heatmap')">
          <app-learning-calendar-heatmap [config]="heatmapConfig"></app-learning-calendar-heatmap>
        </div>

        <!-- 成就墙 -->
        <div class="section section-achievements" *ngIf="layout.isVisible('achievements')">
          <div class="achievements-card">
            <h2 class="section-title">
              <mat-icon>emoji_events</mat-icon>
              成就墙
            </h2>
            <div class="achievements-grid">
              <div
                *ngFor="let badge of achievementBadges"
                class="achievement-badge"
                [class.locked]="!badge.unlocked"
                [matTooltip]="badge.name + (badge.unlocked ? ' - ' + badge.description : ' - 未解锁')"
              >
                <span class="badge-icon">{{ badge.icon }}</span>
                <span class="badge-name">{{ badge.name }}</span>
              </div>
            </div>
            <div class="achievements-summary">
              <span>已解锁 {{ unlockedAchievementsCount }}/{{ achievementBadges.length }}</span>
              <mat-progress-bar
                mode="determinate"
                [value]="achievementProgress"
              ></mat-progress-bar>
            </div>
          </div>
        </div>
      </div>

      <!-- 正在学习的课程（使用统一课程卡片） -->
      <div class="section" *ngIf="layout.isVisible('enrolled_courses')">
        <h2 class="section-title">正在学习</h2>
        <div class="course-grid" *ngIf="enrolledCourses$ | async as enrolledCourses">
          <ng-container *ngIf="enrolledCourses.length > 0; else noEnrolledCourses">
            <app-unified-course-card
              *ngFor="let item of enrolledCourses"
              [config]="{
                course: item.course,
                showEnrollButton: false,
                showProgress: true,
                enrollmentStatus: 'enrolled',
                enrollmentProgress: item.progress || 0,
                orgName: getOrgName(item.course.org_id),
              }"
              (detail)="onContinueLearning(item.course.id)"
            >
            </app-unified-course-card>
          </ng-container>
          <ng-template #noEnrolledCourses>
            <div class="empty-state">
              <mat-icon>menu_book</mat-icon>
              <p>暂无正在学习的课程</p>
              <button mat-raised-button color="primary" (click)="navigateToCourseLibrary()">
                浏览课程库
              </button>
            </div>
          </ng-template>
        </div>
      </div>

      <!-- 推荐课程（使用统一课程卡片） -->
      <div class="section" *ngIf="layout.isVisible('recommended_courses')">
        <div class="section-header">
          <h2 class="section-title">推荐课程</h2>
          <button mat-button color="primary" (click)="navigateToCourseLibrary()">
            查看更多
            <mat-icon>arrow_forward</mat-icon>
          </button>
        </div>
        <div class="course-grid" *ngIf="recommendedCourses$ | async as recommendedCourses">
          <ng-container *ngIf="recommendedCourses.length > 0; else noRecommendedCourses">
            <app-unified-course-card
              *ngFor="let course of recommendedCourses"
              [config]="{
                course: course,
                showEnrollButton: true,
                showProgress: false,
                enrollmentStatus: 'not_enrolled',
                orgName: getOrgName(course.org_id),
                compact: false,
              }"
              (enroll)="onEnrollCourse(course.id)"
              (detail)="onViewCourseDetail(course.id)"
            >
            </app-unified-course-card>
          </ng-container>
          <ng-template #noRecommendedCourses>
            <div class="empty-state">
              <mat-icon>explore</mat-icon>
              <p>暂无推荐课程</p>
            </div>
          </ng-template>
        </div>
      </div>

      <!-- 课件库模块 -->
      <div class="section" *ngIf="layout.isVisible('materials')">
        <app-student-material-dashboard></app-student-material-dashboard>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        --dash-max-width: 1400px;
        --dash-padding: 32px;
        --stats-card-min: 260px;
        --course-card-min: 320px;
        --source-card-min: 300px;
        --section-gap: 48px;
      }

      .student-dashboard {
        max-width: var(--dash-max-width);
        margin: 0 auto;
        padding: 0 var(--dash-padding);
      }

      .page-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
      }

      .page-title {
        font-size: 28px;
        font-weight: 700;
        color: #333;
        margin: 0;
      }

      /* ===== 统计卡片网格 ===== */
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(var(--stats-card-min), 1fr));
        gap: 20px;
        margin-bottom: var(--section-gap);
      }

      /* ===== 区块 ===== */
      .section {
        margin-bottom: var(--section-gap);
      }

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
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

      .section-header .section-title {
        margin-bottom: 0;
      }

      /* ===== 课程网格 ===== */
      .course-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(var(--course-card-min), 1fr));
        gap: 20px;
      }

      .course-card {
        mat-card-header {
          margin-bottom: 12px;
        }

        mat-card-title {
          font-size: 18px;
          font-weight: 600;
        }

        mat-card-subtitle {
          font-size: 14px;
          color: #666;
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
      }

      .source-chip {
        font-size: 11px;
        min-height: 24px;
        padding: 0 8px;

        mat-icon {
          font-size: 14px;
          width: 14px;
          height: 14px;
          margin-right: 4px;
        }
      }

      .progress-info {
        margin-bottom: 12px;

        span {
          display: block;
          margin-bottom: 8px;
          font-size: 14px;
          color: #666;
        }
      }

      .course-description {
        font-size: 14px;
        line-height: 1.6;
        color: #666;
        margin-bottom: 12px;
      }

      .course-meta {
        display: flex;
        gap: 16px;
        font-size: 13px;
        color: #999;

        span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        mat-icon {
          font-size: 16px;
          width: 16px;
          height: 16px;
        }
      }

      /* ===== 学习来源卡片网格 ===== */
      .sources-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(var(--source-card-min), 1fr));
        gap: 16px;
      }

      /* ===== 双栏布局（热力图+成就墙） ===== */
      .dual-column-section {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 20px;
        margin-bottom: var(--section-gap);
      }

      .section-heatmap, .section-achievements {
        margin-bottom: 0;
      }

      .achievements-card {
        background: #fff;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
      }

      .achievements-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 16px;
      }

      .achievement-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px 8px;
        border-radius: 12px;
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%);
        border: 1px solid #d0e3ff;
        cursor: default;
        transition: transform 0.2s, box-shadow 0.2s;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }

        &.locked {
          background: #f5f5f5;
          border-color: #e0e0e0;
          opacity: 0.5;
          filter: grayscale(0.8);
        }
      }

      .badge-icon {
        font-size: 28px;
        line-height: 1;
      }

      .badge-name {
        font-size: 11px;
        font-weight: 600;
        color: #333;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
      }

      .achievements-summary {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 13px;
        color: #666;
      }

      .source-chip-card {
        transition:
          transform 0.2s,
          box-shadow 0.2s;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        &.primary-source {
          border-left: 4px solid #4caf50;
          background: linear-gradient(135deg, #f1f8e9 0%, #ffffff 100%);
        }

        mat-card-content {
          padding: 16px;
        }
      }

      .source-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;

        mat-icon {
          color: #666;
        }

        .source-name {
          font-size: 16px;
          font-weight: 600;
          color: #333;
          flex: 1;
        }
      }

      .source-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .source-type {
          font-size: 13px;
          color: #666;
        }

        .source-status {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 10px;

          &.status-active {
            background: #e8f5e9;
            color: #4caf50;
          }

          &.status-inactive {
            background: #f5f5f5;
            color: #999;
          }

          &.status-completed {
            background: #e3f2fd;
            color: #2196f3;
          }
        }
      }

      .source-dates {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #999;

        mat-icon {
          font-size: 14px;
          width: 14px;
          height: 14px;
        }
      }

      /* ===== 空状态 ===== */
      .empty-state {
        grid-column: 1 / -1;
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
          margin-bottom: 16px;
        }
      }

      /* ===== 响应式：移动端 ===== */
      @media (max-width: 768px) {
        :host {
          --dash-padding: 16px;
          --stats-card-min: 1fr;
          --course-card-min: 1fr;
          --source-card-min: 1fr;
          --section-gap: 32px;
        }

        .page-title {
          font-size: 22px;
        }

        .section-title {
          font-size: 18px;
        }

        .dual-column-section {
          grid-template-columns: 1fr;
        }

        .achievements-grid {
          grid-template-columns: repeat(4, 1fr);
        }
      }

      /* ===== 响应式：大屏桌面（≥ 1600px）===== */
      @media (min-width: 1600px) {
        :host {
          --dash-max-width: 100%;
          --dash-padding: 48px;
          --stats-card-min: 280px;
          --course-card-min: 360px;
          --source-card-min: 320px;
        }

        .stats-grid {
          grid-template-columns: repeat(4, 1fr);
        }

        .course-grid {
          grid-template-columns: repeat(3, 1fr);
        }
      }

      /* ===== 响应式：超宽屏（≥ 2000px）===== */
      @media (min-width: 2000px) {
        :host {
          --stats-card-min: 300px;
          --course-card-min: 380px;
          --source-card-min: 340px;
        }

        .course-grid {
          grid-template-columns: repeat(4, 1fr);
        }
      }
    `,
  ],
})
export class StudentDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  currentUser: User | null = null;
  progressStats: UnifiedProgressStats | null = null;
  learningSources: LearningSource[] = [];
  loadingProgress = false;
  loadingSources = false;

  // 统计卡片配置
  statsConfig: {
    inProgressCourses: StatsCardConfig;
    achievements: StatsCardConfig;
    learningPoints: StatsCardConfig;
    tokenBalance: StatsCardConfig;
  } = {
    inProgressCourses: {
      value: 0,
      label: '正在学习',
      icon: 'menu_book',
      color: 'primary',
      clickable: true,
    },
    achievements: {
      value: 8,
      label: '获得成就',
      icon: 'emoji_events',
      color: 'accent',
      clickable: true,
    },
    learningPoints: {
      value: 2450,
      label: '学习积分',
      icon: 'stars',
      color: 'warn',
      clickable: true,
    },
    tokenBalance: {
      value: 500,
      label: 'Token 余额',
      icon: 'token',
      color: 'success',
      clickable: true,
    },
  };

  recentCourses: RecentCourse[] = [
    {
      title: '机器人基础入门',
      teacher: '小M老师',
      progress: 75,
      duration: '20小时',
      level: '初级',
      sourceType: 'school_curriculum',
      sourceName: '校本部',
    },
    {
      title: 'AI 编程与机器学习',
      teacher: '阿博特老师',
      progress: 45,
      duration: '30 小时',
      level: '中级',
      sourceType: 'institution',
      sourceName: '创新机器人培训中心',
    },
    {
      title: 'Python 机器人控制',
      teacher: '小 X 老师',
      progress: 90,
      duration: '15 小时',
      level: '初级',
      sourceType: 'school_interest',
      sourceName: '校内兴趣班',
    },
  ];

  recommendedCourses: RecommendedCourse[] = [
    {
      title: 'ROS机器人操作系统',
      teacher: '博士坦老师',
      description: '学习 ROS 机器人操作系统的核心概念，包括节点通信、导航 SLAM、机械臂控制等。',
      duration: '40 小时',
      level: '高级',
    },
    {
      title: '深度学习与计算机视觉',
      teacher: '小 M 老师',
      description: '掌握深度学习算法在计算机视觉中的应用，实现目标检测、人脸识别等 AI 功能。',
      duration: '35 小时',
      level: '中级',
    },
  ];

  // 添加缺失的属性
  enrolledCourses$!: Observable<
    Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>
  >;
  recommendedCourses$!: Observable<UnifiedCourse[]>;
  orgNameMap: Map<number, string> = new Map();
  loadingEnrolledCourses = false;

  /** 学习日历热力图配置 */
  heatmapConfig: CalendarHeatmapConfig = {
    year: new Date().getFullYear(),
    data: [],
    loading: true,
  };

  /** 成就徽章列表 */
  achievementBadges: AchievementBadge[] = [
    { id: 'first-lesson', name: '初入编程', icon: '🎓', description: '完成第一个课程', unlocked: true, unlockedDate: '2026-01-15' },
    { id: 'first-code', name: '代码新手', icon: '💻', description: '编写第一行代码', unlocked: true, unlockedDate: '2026-01-20' },
    { id: 'python-start', name: 'Python入门', icon: '🐍', description: '完成 Python 基础课程', unlocked: true, unlockedDate: '2026-02-20' },
    { id: 'streak-7', name: '坚持7天', icon: '🔥', description: '连续学习7天', unlocked: true, unlockedDate: '2026-03-01' },
    { id: 'quiz-master', name: '测验达人', icon: '📝', description: '5次测验获得满分', unlocked: true, unlockedDate: '2026-03-15' },
    { id: 'blockly-pro', name: '积木高手', icon: '🧩', description: '完成10个Blockly关卡', unlocked: true, unlockedDate: '2026-04-01' },
    { id: 'first-debug', name: 'Bug猎手', icon: '🔧', description: '独立修复3个错误', unlocked: true, unlockedDate: '2026-04-05' },
    { id: 'streak-30', name: '30天坚持', icon: '🏆', description: '连续学习30天', unlocked: true, unlockedDate: '2026-04-28' },
    { id: 'circuit-master', name: '电路大师', icon: '⚡', description: '完成所有电路实验', unlocked: false },
    { id: 'ai-pioneer', name: 'AI先锋', icon: '🤖', description: '完成AI编程课程', unlocked: false },
    { id: 'project-10', name: '项目达人', icon: '🚀', description: '完成10个项目', unlocked: false },
    { id: 'streak-100', name: '百日传说', icon: '💎', description: '连续学习100天', unlocked: false },
  ];

  get unlockedAchievementsCount(): number {
    return this.achievementBadges.filter((b) => b.unlocked).length;
  }

  get achievementProgress(): number {
    return this.achievementBadges.length > 0
      ? Math.round((this.unlockedAchievementsCount / this.achievementBadges.length) * 100)
      : 0;
  }

  constructor(
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService,
    private unifiedCourseService: UnifiedCourseService,
    private courseEnrollmentService: CourseEnrollmentService,
    private wsService: AiEduWebSocketService,
    private cdr: ChangeDetectorRef,
    private router: Router,
    public layout: DashboardLayoutService,
    private dialog: MatDialog,
  ) {}

  ngOnInit(): void {
    this.loadCurrentUser();
  }

  /** 打开仪表盘布局设置对话框 */
  openLayoutDialog(): void {
    this.dialog.open(DashboardLayoutDialogComponent, {
      width: '480px',
      maxWidth: '90vw',
    });
  }

  private loadCurrentUser(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      if (user?.id) {
        const userId = Number(user.id);
        if (!isNaN(userId) && userId > 0) {
          this.loadProgressStats(userId);
          this.loadLearningSources(userId);
          this.loadUnifiedCourses(userId);
          this.connectWebSocket(userId);
        } else {
          this.loadMockData();
        }
      }
    });
  }

  /**
   * 建立 WebSocket 连接，实现数据自动刷新
   */
  private connectWebSocket(userId: number): void {
    const baseUrl = window.location.origin.includes('localhost')
      ? 'http://localhost:8000'
      : window.location.origin;
    const orgId = (this.currentUser as unknown as { org_id?: number })?.org_id ?? 1;

    this.wsService.connect(userId, orgId, baseUrl);

    // 监听进度更新，自动刷新仪表板数据
    this.wsService
      .onProgressUpdate()
      .pipe(takeUntil(this.destroy$))
      .subscribe((update: ProgressUpdateData) => {
        console.log('[Dashboard] 收到进度更新:', update);
        // 刷新学习进度统计
        this.loadProgressStats(userId);
        this.cdr.markForCheck();
      });

    // 监听连接状态
    this.wsService.connectionStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe((status) => {
        if (status === 'connected') {
          console.log('[Dashboard] WebSocket 已连接，实时数据已启用');
        }
      });
  }

  /**
   * 加载统一课程数据
   */
  private loadUnifiedCourses(userId: number): void {
    // 加载已报名课程
    this.enrolledCourses$ = this.courseEnrollmentService
      .getUserEnrollments(userId, {
        page: 1,
        page_size: 10,
      })
      .pipe(
        takeUntil(this.destroy$),
        switchMap((enrollments) => {
          const courseIds = enrollments.items.map((e) => e.course_id);
          if (courseIds.length === 0) {
            return of([]);
          }

          // 获取课程详情
          return forkJoin(
            courseIds.map((courseId) => this.unifiedCourseService.getCourse(courseId))
          ).pipe(
            map((courses) =>
              enrollments.items.map((enrollment, index) => ({
                course: courses[index],
                progress: enrollment.progress_percentage || 0,
                enrollment,
              }))
            )
          );
        }),
        catchError((error) => {
          console.error('获取已报名课程失败:', error);
          return of([]);
        })
      );

    // 加载推荐课程
    this.recommendedCourses$ = this.unifiedCourseService.getRecommendedCourses(userId, 8).pipe(
      takeUntil(this.destroy$),
      catchError((error) => {
        console.error('获取推荐课程失败:', error);
        return this.unifiedCourseService.getNewestCourses(8);
      })
    );

    // 加载组织名称映射
    this.loadOrgNames();
  }

  /**
   * 加载组织名称映射
   */
  private loadOrgNames(): void {
    // 简化实现：实际应从组织服务获取
    this.orgNameMap.set(1, '校本部');
    this.orgNameMap.set(2, '创新机器人培训中心');
    this.orgNameMap.set(3, '在线学习平台');
  }

  /**
   * 获取组织名称
   */
  getOrgName(orgId: number): string {
    return this.orgNameMap.get(orgId) ?? `机构 ${orgId}`;
  }

  /**
   * 继续学习
   */
  onContinueLearning(courseId: number): void {
    void this.router.navigate(['/student/course', courseId, 'learn']);
  }

  /**
   * 报名课程
   */
  onEnrollCourse(courseId: number): void {
    if (!this.currentUser?.id) return;

    const userId = Number(this.currentUser.id);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const userOrgId = (this.currentUser as unknown as { org_id: number })?.org_id;
    const orgId = userOrgId && userOrgId !== null ? Number(userOrgId) : 1;

    this.courseEnrollmentService
      .enrollInCourse(courseId, userId, orgId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          // 刷新已报名课程列表
          this.loadUnifiedCourses(userId);
        },
        error: (error) => {
          console.error('报名失败:', error);
        },
      });
  }

  /**
   * 查看课程详情
   */
  onViewCourseDetail(courseId: number): void {
    void this.router.navigate(['/student/course', courseId]);
  }

  /**
   * 导航到课程库
   */
  navigateToCourseLibrary(): void {
    void this.router.navigate(['/student/courses']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.wsService.disconnect();
  }

  private loadProgressStats(userId: number): void {
    this.loadingProgress = true;
    this.multiSourceService
      .getUserUnifiedProgress(userId)
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error('加载学习进度失败:', err);
          // API失败时使用mock数据
          return of(this.getMockProgressStats());
        })
      )
      .subscribe((stats) => {
        this.progressStats = stats;
        this.loadingProgress = false;
        // 更新统计卡片数据
        this.updateStatsConfig(stats);
      });

    // 加载学习日历数据
    this.loadCalendarHeatmap(userId);
  }

  /**
   * 加载学习日历热力图数据
   */
  private loadCalendarHeatmap(_userId: number): void {
    // TODO: 调用后端 API 获取真实学习日历数据
    // 目前使用 mock 数据
    this.heatmapConfig = {
      year: new Date().getFullYear(),
      data: this.getMockCalendarData(),
      loading: false,
    };
  }

  /**
   * 生成 Mock 日历数据
   */
  private getMockCalendarData(): DailyLearningRecord[] {
    const records: DailyLearningRecord[] = [];
    const year = new Date().getFullYear();
    const today = new Date();

    for (let d = new Date(year, 0, 1); d <= today; d.setDate(d.getDate() + 1)) {
      const dayOfWeek = d.getDay();
      // 周末学习概率低，工作日概率高
      const shouldStudy = dayOfWeek === 0 || dayOfWeek === 6
        ? Math.random() > 0.6
        : Math.random() > 0.2;

      if (shouldStudy) {
        records.push({
          date: `${year}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`,
          minutes: Math.floor(Math.random() * 180) + 15,
          courses: Math.floor(Math.random() * 3) + 1,
          quizzes: Math.random() > 0.8 ? 1 : 0,
          score: Math.random() > 0.5 ? Math.floor(Math.random() * 30) + 70 : undefined,
        });
      }
    }

    return records;
  }

  /**
   * 更新统计卡片配置
   */
  private updateStatsConfig(stats: UnifiedProgressStats): void {
    if (stats) {
      this.statsConfig.inProgressCourses = {
        ...this.statsConfig.inProgressCourses,
        value: stats.in_progress_courses || 0,
      };
    }
  }

  private loadLearningSources(userId: number): void {
    this.loadingSources = true;
    this.multiSourceService
      .getUserLearningSources(userId, { includeInactive: true })
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error('加载学习来源失败:', err);
          // API失败时使用mock数据
          return of({ total: 3, items: this.getMockLearningSources() });
        })
      )
      .subscribe((response) => {
        this.learningSources = response.items || [];
        this.loadingSources = false;
      });
  }

  /**
   * 获取Mock学习进度数据
   */
  private getMockProgressStats(): UnifiedProgressStats {
    return {
      total_courses: 5,
      completed_courses: 2,
      in_progress_courses: 3,
      total_time_minutes: 1250,
      average_score: 85.5,
      source_breakdown: [
        {
          source_type: 'school_curriculum' as LearningSourceType,
          source_name: '校本部',
          courses: 2,
          completed: 1,
          avg_score: 88,
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
          avg_score: 83,
          total_time: 500,
        },
      ],
    };
  }

  /**
   * 获取 Mock 学习来源数据
   */
  private getMockLearningSources(): LearningSource[] {
    return [
      this.createMockLearningSource(
        1,
        1,
        '校本部',
        'school_curriculum',
        true,
        '2025-09-01',
        '2026-07-31'
      ),
      this.createMockLearningSource(
        2,
        2,
        '创新机器人培训中心',
        'institution',
        false,
        '2025-10-15',
        '2026-06-30'
      ),
      this.createMockLearningSource(
        3,
        1,
        '校内兴趣班',
        'school_interest',
        false,
        '2025-11-01',
        '2026-05-31'
      ),
    ];
  }

  /**
   * 创建单个 Mock 学习来源
   */
  private createMockLearningSource(
    id: number,
    userId: number,
    name: string,
    sourceType: LearningSourceType,
    isPrimary: boolean,
    startDate: string,
    endDate: string
  ): LearningSource {
    const now = new Date().toISOString();
    return {
      id,
      user_id: userId,
      org_id: id === 2 ? 2 : 1,
      name,
      source_type: sourceType,
      status: 'active',
      is_primary: isPrimary,
      is_active: true,
      role: 'student',
      source_detail: {},
      start_date: startDate,
      end_date: endDate,
      notes: null,
      created_at: now,
      updated_at: now,
    };
  }

  /**
   * 加载Mock数据（用于模拟账号）
   */
  private loadMockData(): void {
    this.progressStats = this.getMockProgressStats();
    this.learningSources = this.getMockLearningSources();
    this.loadingProgress = false;
    this.loadingSources = false;
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

  getSourceIconByName(type: string): string {
    return this.getSourceIcon(type);
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
