/**
 * 我的课程页面
 *
 * PRD 6.6 关键页面线框 - "我的课程"
 * 展示：已选课程列表、学习进度、课程分类筛选
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { CourseEnrollment, UnifiedCourse } from '../../../../shared/models/course.models';
import type { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { CourseEnrollmentService } from '../../../core/services/course-enrollment.service';
import { UnifiedCourseService } from '../../../core/services/unified-course.service';

interface EnrolledCourse {
  course: UnifiedCourse;
  enrollment: CourseEnrollment;
}

@Component({
  selector: 'app-my-courses',
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
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="courses-container">
      <div class="page-header">
        <h1 class="page-title">我的课程</h1>
        <span class="course-count" *ngIf="enrolledCourses.length">
          共 {{ enrolledCourses.length }} 门课程
        </span>
      </div>

      <!-- 状态筛选 Tab -->
      <mat-tab-group
        [(selectedIndex)]="activeTab"
        (selectedIndexChange)="onTabChange($event)"
        class="filter-tabs"
      >
        <mat-tab label="我的课程 ({{ enrolledCourses.length }})"></mat-tab>
        <mat-tab label="学习来源"></mat-tab>
        <mat-tab label="推荐课程"></mat-tab>
      </mat-tab-group>

      <!-- Tab 1: 我的课程列表 -->
      <ng-container *ngIf="activeTab === 0">
        <div class="course-grid">
          <div *ngFor="let item of filteredCourses" class="course-card-wrapper">
            <mat-card class="course-card" [class.completed]="item.enrollment.status === 'completed'">
              <mat-card-content>
                <div class="course-header">
                  <div class="course-icon" [class]="'icon-' + item.course.category">
                    {{ getCategoryIcon(item.course.category) }}
                  </div>
                  <div class="course-info">
                    <h3 class="course-title">{{ item.course.title }}</h3>
                    <div class="course-meta">
                      <span class="meta-item">
                        <mat-icon>school</mat-icon>
                        {{ difficultyLabel(item.course.difficulty) }}
                      </span>
                      <span class="meta-item">
                        <mat-icon>access_time</mat-icon>
                        {{ item.course.duration_minutes }}分钟
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 进度条 -->
                <div class="progress-section">
                  <div class="progress-header">
                    <span class="progress-label">学习进度</span>
                    <span
                      class="progress-value"
                      [class.complete]="item.enrollment.status === 'completed'"
                    >
                      {{
                        item.enrollment.status === 'completed'
                          ? '已完成'
                          : Math.round(item.enrollment.progress_percentage) + '%'
                      }}
                    </span>
                  </div>
                  <mat-progress-bar
                    mode="determinate"
                    [value]="item.enrollment.progress_percentage"
                    [color]="item.enrollment.status === 'completed' ? 'primary' : 'accent'"
                  ></mat-progress-bar>
                </div>

                <!-- 标签和操作 -->
                <div class="course-footer">
                  <div class="course-tags">
                    <span class="tag source-tag">{{ sourceTypeLabel(item.course.source_type) }}</span>
                    <span
                      *ngIf="item.enrollment.score != null"
                      class="tag score-tag"
                      [class.high-score]="isHighScore(item.enrollment.score)"
                    >
                      得分: {{ item.enrollment.score }}
                    </span>
                  </div>
                  <button
                    mat-stroked-button
                    color="primary"
                    class="continue-btn"
                    [disabled]="item.enrollment.status === 'completed'"
                  >
                    {{ item.enrollment.status === 'completed' ? '复习' : '继续学习' }}
                  </button>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="empty-state" *ngIf="filteredCourses.length === 0 && !loading">
          <mat-icon>menu_book</mat-icon>
          <h3>还没有课程</h3>
          <p>
            你目前还没有{{ activeTab === 0 ? '选课' : activeTab === 1 ? '在学' : '已完成' }}的课程
          </p>
          <button mat-raised-button color="primary" routerLink="/content-store">去选课</button>
        </div>
      </ng-container>

      <!-- Tab 2: 学习来源 -->
      <ng-container *ngIf="activeTab === 1">
        <div class="sources-section">
          <div class="sources-intro">
            <mat-icon>hub</mat-icon>
            <p>整合来自学校、培训机构、在线平台等多个学习来源的数据，统一管理您的学习进度。</p>
          </div>
          <div class="sources-grid">
            <mat-card *ngFor="let source of learningSources" class="source-card" [class.primary]="source.is_primary">
              <mat-card-content>
                <div class="source-header">
                  <mat-icon class="source-icon">{{ getSourceIcon(source.source_type) }}</mat-icon>
                  <div class="source-info">
                    <h4 class="source-name">{{ source.name }}</h4>
                    <span class="source-type">{{ getSourceTypeLabel(source.source_type) }}</span>
                  </div>
                  <span *ngIf="source.is_primary" class="primary-badge">主来源</span>
                </div>
                <div class="source-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ source.courses || 0 }}</span>
                    <span class="stat-label">课程</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ source.completed || 0 }}</span>
                    <span class="stat-label">已完成</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ source.avg_score || '-' }}</span>
                    <span class="stat-label">平均分</span>
                  </div>
                </div>
                <div class="source-dates" *ngIf="source.start_date">
                  <mat-icon>date_range</mat-icon>
                  <span>{{ source.start_date }} ~ {{ source.end_date || '长期' }}</span>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
          <div class="empty-state" *ngIf="learningSources.length === 0 && !loadingSources">
            <mat-icon>source</mat-icon>
            <h3>暂无学习来源</h3>
            <p>绑定学校或培训机构账号后，可以统一管理多来源的学习进度。</p>
          </div>
        </div>
      </ng-container>

      <!-- Tab 3: 推荐课程 -->
      <ng-container *ngIf="activeTab === 2">
        <div class="recommendations-section">
          <div class="recommendations-intro">
            <mat-icon>auto_awesome</mat-icon>
            <p>根据您的学习历史和兴趣，为您推荐精选课程。</p>
          </div>
          <div class="course-grid">
            <mat-card *ngFor="let course of recommendedCourses" class="course-card recommendation-card">
              <mat-card-content>
                <div class="course-header">
                  <div class="course-icon" [class]="'icon-' + course.category">
                    {{ getCategoryIcon(course.category) }}
                  </div>
                  <div class="course-info">
                    <h3 class="course-title">{{ course.title }}</h3>
                    <div class="course-meta">
                      <span class="meta-item">
                        <mat-icon>school</mat-icon>
                        {{ difficultyLabel(course.difficulty) }}
                      </span>
                      <span class="meta-item">
                        <mat-icon>access_time</mat-icon>
                        {{ course.duration_minutes }}分钟
                      </span>
                    </div>
                  </div>
                </div>
                <p class="course-description">{{ course.description }}</p>
                <div class="course-footer">
                  <div class="course-tags">
                    <span class="tag tag-recommend">
                      <mat-icon>thumb_up</mat-icon>
                      为您推荐
                    </span>
                  </div>
                  <button mat-raised-button color="primary" class="enroll-btn">
                    立即报名
                  </button>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
          <div class="empty-state" *ngIf="recommendedCourses.length === 0 && !loadingRecommendations">
            <mat-icon>explore</mat-icon>
            <h3>暂无推荐课程</h3>
            <p>完成更多课程后，我们会根据您的兴趣推荐更多内容。</p>
          </div>
        </div>
      </ng-container>

      <!-- 加载中 -->
      <div class="loading-state" *ngIf="loading">
        <mat-icon>hourglass_empty</mat-icon>
        <p>正在加载你的课程...</p>
      </div>
    </div>
  `,
  styles: [
    `
      .courses-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
      }
      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .page-title {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
      }
      .course-count {
        font-size: 14px;
        color: #64748b;
      }

      .filter-tabs {
        margin-bottom: 20px;
      }

      .course-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
        gap: 16px;
      }
      .course-card-wrapper {
        display: flex;
      }

      .course-card {
        width: 100%;
        border-radius: 16px;
        transition:
          box-shadow 0.2s,
          transform 0.2s;
      }
      .course-card:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
      }
      .course-card.completed {
        opacity: 0.8;
      }

      .course-header {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }
      .course-icon {
        font-size: 32px;
        width: 56px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        flex-shrink: 0;
      }
      .course-info {
        flex: 1;
        min-width: 0;
      }
      .course-title {
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
        margin: 0 0 8px 0;
        line-height: 1.4;
      }
      .course-meta {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }
      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #64748b;
      }
      .meta-item mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .progress-section {
        margin-bottom: 14px;
      }
      .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
      }
      .progress-label {
        font-size: 13px;
        color: #64748b;
      }
      .progress-value {
        font-size: 13px;
        font-weight: 600;
        color: #3b82f6;
      }
      .progress-value.complete {
        color: #22c55e;
      }

      .course-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .course-tags {
        display: flex;
        gap: 6px;
      }
      .tag {
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 10px;
        font-weight: 500;
      }
      .source-tag {
        background: #f1f5f9;
        color: #475569;
      }
      .score-tag {
        background: #fef3c7;
        color: #92400e;
      }
      .score-tag.high-score {
        background: #dcfce7;
        color: #166534;
      }
      .continue-btn {
        font-size: 12px;
        padding: 2px 14px;
      }

      .empty-state,
      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 80px 24px;
        color: #94a3b8;
        text-align: center;
      }
      .empty-state mat-icon,
      .loading-state mat-icon {
        font-size: 56px;
        width: 56px;
        height: 56px;
        margin-bottom: 16px;
      }
      .empty-state h3 {
        font-size: 18px;
        font-weight: 600;
        color: #475569;
        margin: 0 0 8px 0;
      }
      .empty-state p {
        font-size: 14px;
        margin: 0 0 20px 0;
      }

      @media (max-width: 768px) {
        .course-grid {
          grid-template-columns: 1fr;
        }
      }

      /* ============================================= */
      /* 学习来源 Tab 样式 */
      /* ============================================= */
      .sources-section {
        padding: 8px 0;
      }

      .sources-intro {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: #f8fafc;
        border-radius: 12px;
        margin-bottom: 20px;
        color: #64748b;
      }

      .sources-intro mat-icon {
        color: #3b82f6;
        font-size: 24px;
      }

      .sources-intro p {
        margin: 0;
        font-size: 14px;
      }

      .sources-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
      }

      .source-card {
        border-radius: 16px;
        transition: box-shadow 0.2s, transform 0.2s;
      }

      .source-card:hover {
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
      }

      .source-card.primary {
        border-left: 4px solid #22c55e;
        background: linear-gradient(135deg, #f0fdf4 0%, #fff 100%);
      }

      .source-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
      }

      .source-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
        color: #3b82f6;
      }

      .source-info {
        flex: 1;
      }

      .source-name {
        margin: 0 0 4px;
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
      }

      .source-type {
        font-size: 12px;
        color: #64748b;
      }

      .primary-badge {
        padding: 2px 10px;
        background: #22c55e;
        color: white;
        font-size: 11px;
        font-weight: 600;
        border-radius: 10px;
      }

      .source-stats {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
      }

      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .stat-value {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
      }

      .stat-label {
        font-size: 11px;
        color: #64748b;
      }

      .source-dates {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #94a3b8;
      }

      .source-dates mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }

      /* ============================================= */
      /* 推荐课程 Tab 样式 */
      /* ============================================= */
      .recommendations-section {
        padding: 8px 0;
      }

      .recommendations-intro {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
        border-radius: 12px;
        margin-bottom: 20px;
        color: #3b82f6;
      }

      .recommendations-intro mat-icon {
        font-size: 24px;
      }

      .recommendations-intro p {
        margin: 0;
        font-size: 14px;
        color: #64748b;
      }

      .recommendation-card {
        border-radius: 16px;
        transition: box-shadow 0.2s, transform 0.2s;
      }

      .recommendation-card:hover {
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
      }

      .course-description {
        margin: 0 0 16px;
        font-size: 13px;
        color: #64748b;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .tag-recommend {
        display: flex;
        align-items: center;
        gap: 4px;
        background: #dbeafe;
        color: #1d4ed8;
      }

      .tag-recommend mat-icon {
        font-size: 12px;
        width: 12px;
        height: 12px;
      }

      .enroll-btn {
        font-size: 13px;
      }
    `,
  ],
})
export class MyCoursesComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  enrolledCourses: EnrolledCourse[] = [];
  filteredCourses: EnrolledCourse[] = [];
  activeTab = 0;
  loading = true;
  loadingSources = false;
  loadingRecommendations = false;

  // 学习来源数据
  learningSources: Array<{
    id: number;
    name: string;
    source_type: string;
    is_primary: boolean;
    start_date?: string;
    end_date?: string;
    courses?: number;
    completed?: number;
    avg_score?: number;
  }> = [];

  // 推荐课程数据
  recommendedCourses: UnifiedCourse[] = [];

  currentUser: User | null = null;

  readonly Math = Math;

  readonly categoryIcon: Record<string, string> = {
    programming: '💻',
    science: '🔬',
    math: '📐',
    art: '🎨',
    music: '🎵',
    language: '🌍',
    general: '📚',
  };

  constructor(
    private courseEnrollmentService: CourseEnrollmentService,
    private unifiedCourseService: UnifiedCourseService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      if (user?.id) {
        const userId = Number(user.id);
        this.loadCourses(userId);
        this.loadLearningSources(userId);
        this.loadRecommendations(userId);
      }
    });
  }

  /**
   * 加载学习来源数据
   */
  private loadLearningSources(userId: number): void {
    this.loadingSources = true;
    // TODO: 替换为实际的API调用
    // 暂时使用Mock数据
    setTimeout(() => {
      this.learningSources = [
        {
          id: 1,
          name: '校本部',
          source_type: 'school_curriculum',
          is_primary: true,
          start_date: '2025-09-01',
          end_date: '2026-07-31',
          courses: 3,
          completed: 1,
          avg_score: 88,
        },
        {
          id: 2,
          name: '创新机器人培训中心',
          source_type: 'institution',
          is_primary: false,
          start_date: '2025-10-15',
          end_date: '2026-06-30',
          courses: 2,
          completed: 0,
          avg_score: 83,
        },
        {
          id: 3,
          name: '校内兴趣班',
          source_type: 'school_interest',
          is_primary: false,
          start_date: '2025-11-01',
          end_date: '2026-05-31',
          courses: 1,
          completed: 0,
          avg_score: undefined,
        },
      ];
      this.loadingSources = false;
      this.cdr.markForCheck();
    }, 500);
  }

  /**
   * 加载推荐课程数据
   */
  private loadRecommendations(_userId: number): void {
    this.loadingRecommendations = true;
    // TODO: 替换为实际的API调用
    // 暂时使用Mock数据
    setTimeout(() => {
      this.recommendedCourses = [
        {
          id: 201,
          org_id: 1,
          title: 'ROS机器人操作系统',
          description: '学习ROS机器人操作系统的核心概念，包括节点通信、导航SLAM、机械臂控制等。',
          cover_image_url: null,
          category: 'programming',
          difficulty: 'advanced',
          duration_minutes: 2400,
          status: 'published',
          source_type: 'institution',
          teacher_name: '博士坦老师',
          tags: ['ROS', '机器人', 'SLAM'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
        {
          id: 202,
          org_id: 1,
          title: 'Python机器学习入门',
          description: '掌握Python和Scikit-Learn基础，学习监督学习和无监督学习的核心算法。',
          cover_image_url: null,
          category: 'science',
          difficulty: 'intermediate',
          duration_minutes: 1800,
          status: 'published',
          source_type: 'institution',
          teacher_name: '小M老师',
          tags: ['Python', '机器学习', 'AI'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
        {
          id: 203,
          org_id: 1,
          title: 'Arduino智能硬件开发',
          description: '从零开始学习Arduino开发板，掌握传感器、执行器的编程控制。',
          cover_image_url: null,
          category: 'programming',
          difficulty: 'beginner',
          duration_minutes: 1200,
          status: 'published',
          source_type: 'institution',
          teacher_name: '小X老师',
          tags: ['Arduino', '硬件', '物联网'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
      ];
      this.loadingRecommendations = false;
      this.cdr.markForCheck();
    }, 500);
  }

  private loadCourses(userId: number): void {
    this.loading = true;
    this.courseEnrollmentService
      .getUserEnrollments(userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((response) => {
        const enrollments = response.items;
        if (enrollments.length === 0) {
          this.enrolledCourses = [];
          this.applyFilter();
          this.loading = false;
          this.cdr.markForCheck();
          return;
        }

        const courseIds = enrollments.map((e) => e.course_id);
        this.unifiedCourseService
          .getCoursesBatch(courseIds)
          .pipe(takeUntil(this.destroy$))
          .subscribe((courses) => {
            const courseMap = new Map(courses.map((c) => [c.id, c]));
            this.enrolledCourses = enrollments
              .map((enrollment) => {
                const course = courseMap.get(enrollment.course_id);
                return course ? { course, enrollment } : null;
              })
              .filter((item): item is EnrolledCourse => item !== null);
            this.applyFilter();
            this.loading = false;
            this.cdr.markForCheck();
          });
      });
  }

  onTabChange(_index: number): void {
    this.applyFilter();
  }

  private applyFilter(): void {
    if (this.activeTab === 0) {
      this.filteredCourses = [...this.enrolledCourses];
    } else {
      const status = this.activeTab === 1 ? 'active' : 'completed';
      this.filteredCourses = this.getCoursesByStatus(status);
    }
  }

  getCoursesByStatus(status: string): EnrolledCourse[] {
    return this.enrolledCourses.filter((item) => item.enrollment.status === status);
  }

  difficultyLabel(d: string): string {
    const map: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级',
    };
    return map[d] ?? d;
  }

  sourceTypeLabel(t: string): string {
    const map: Record<string, string> = {
      school_curriculum: '校本课程',
      school_interest: '校内兴趣班',
      institution: '培训机构',
      self_study: '自学',
      online_platform: '在线平台',
      competition: '竞赛',
    };
    return map[t] ?? t;
  }

  isHighScore(score: number | null | undefined): boolean {
    return (score ?? 0) >= 80;
  }

  getCategoryIcon(category: string): string {
    return this.categoryIcon[category] || '📘';
  }

  /**
   * 获取学习来源图标
   */
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

  /**
   * 获取学习来源类型标签
   */
  getSourceTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      school_curriculum: '校本课程',
      school_interest: '校内兴趣班',
      institution: '培训机构',
      self_study: '自学',
      online_platform: '在线平台',
      competition: '竞赛',
    };
    return labels[type] || type;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
