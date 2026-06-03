/**
 * 我的课程页面
 *
 * PRD 6.6 关键页面线框 - "我的课程"
 * 展示：已选课程列表、学习进度、课程分类筛选
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import { CourseEnrollmentService } from '../../../core/services/course-enrollment.service';
import { UnifiedCourseService } from '../../../core/services/unified-course.service';
import type { UnifiedCourse, CourseEnrollment } from '../../../../shared/models/course.models';
import type { User } from '../../../core/models/auth.models';

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
      <mat-tab-group [(selectedIndex)]="activeTab" (selectedIndexChange)="onTabChange($event)" class="filter-tabs">
        <mat-tab label="全部 ({{ enrolledCourses.length }})"></mat-tab>
        <mat-tab label="学习中 ({{ getCoursesByStatus('active').length }})"></mat-tab>
        <mat-tab label="已完成 ({{ getCoursesByStatus('completed').length }})"></mat-tab>
      </mat-tab-group>

      <!-- 课程列表 -->
      <div class="course-grid">
        <div *ngFor="let item of filteredCourses" class="course-card-wrapper">
          <mat-card class="course-card" [class.completed]="item.enrollment.status === 'completed'">
            <mat-card-content>
              <div class="course-header">
                <div class="course-icon" [class]="'icon-' + item.course.category">
                  {{ categoryIcon[item.course.category] ?? '📘' }}
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
                  <span class="progress-value" [class.complete]="item.enrollment.status === 'completed'">
                    {{ item.enrollment.status === 'completed' ? '已完成' : Math.round(item.enrollment.progress_percentage) + '%' }}
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
                  <span *ngIf="item.enrollment.score != null" class="tag score-tag"
                    [class.high-score]="(item.enrollment.score ?? 0) >= 80">
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
        <p>你目前还没有{{ activeTab === 0 ? '选课' : activeTab === 1 ? '在学' : '已完成' }}的课程</p>
        <button mat-raised-button color="primary" routerLink="/content-store">去选课</button>
      </div>

      <!-- 加载中 -->
      <div class="loading-state" *ngIf="loading">
        <mat-icon>hourglass_empty</mat-icon>
        <p>正在加载你的课程...</p>
      </div>
    </div>
  `,
  styles: [`
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
    .course-card-wrapper { display: flex; }

    .course-card {
      width: 100%;
      border-radius: 16px;
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .course-card:hover {
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      transform: translateY(-2px);
    }
    .course-card.completed { opacity: 0.8; }

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
    .course-info { flex: 1; min-width: 0; }
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
    .progress-value.complete { color: #22c55e; }

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

    .empty-state, .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 80px 24px;
      color: #94a3b8;
      text-align: center;
    }
    .empty-state mat-icon, .loading-state mat-icon {
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
  `],
})
export class MyCoursesComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  enrolledCourses: EnrolledCourse[] = [];
  filteredCourses: EnrolledCourse[] = [];
  activeTab = 0;
  loading = true;

  currentUser: User | null = null;

  readonly Math = Math;

  readonly categoryIcon: Record<string, string> = {
    programming: '💻', science: '🔬', math: '📐',
    art: '🎨', music: '🎵', language: '🌍',
    general: '📚',
  };

  constructor(
    private courseEnrollmentService: CourseEnrollmentService,
    private unifiedCourseService: UnifiedCourseService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      if (user?.id) {
        this.loadCourses(Number(user.id));
      }
    });
  }

  private loadCourses(userId: number): void {
    this.loading = true;
    this.courseEnrollmentService.getUserEnrollments(userId).pipe(
      takeUntil(this.destroy$),
    ).subscribe((response) => {
      const enrollments = response.items;
      if (enrollments.length === 0) {
        this.enrolledCourses = [];
        this.applyFilter();
        this.loading = false;
        this.cdr.markForCheck();
        return;
      }

      const courseIds = enrollments.map((e) => e.course_id);
      this.unifiedCourseService.getCoursesBatch(courseIds).pipe(
        takeUntil(this.destroy$),
      ).subscribe((courses) => {
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
      beginner: '入门', intermediate: '进阶', advanced: '高级',
    };
    return map[d] ?? d;
  }

  sourceTypeLabel(t: string): string {
    const map: Record<string, string> = {
      school_curriculum: '校本课程', school_interest: '校内兴趣班',
      institution: '培训机构', self_study: '自学',
      online_platform: '在线平台', competition: '竞赛',
    };
    return map[t] ?? t;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
