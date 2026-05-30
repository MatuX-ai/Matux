/**
 * 教师用户中心 - 教学仪表板
 *
 * 展示教师的教学管理、学生管理等信息
 * 集成多来源学习系统，显示跨机构教学进度和学生学情
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { Router } from '@angular/router';
import { Observable, of, Subject } from 'rxjs';
import { catchError, map, retry, switchMap, takeUntil } from 'rxjs/operators';

import { User } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import {
  DashboardActivity,
  MultiSourceTeacherData,
  StudentAssignment,
  TeacherCourse,
  TeacherDashboardResponse,
  TeacherStats,
  TeacherStudent,
} from '../../core/services/teacher.service';
import { TeacherService } from '../../core/services/teacher.service';
import { CourseStatus, UnifiedCourse, LearningSourceType } from '../../models/unified-course.models';
import { TeacherMaterialDashboardComponent } from '../../shared/components/teacher-material-dashboard/teacher-material-dashboard.component';
import { UnifiedCourseCardComponent } from '../../shared/components/unified-course-card/unified-course-card.component';

interface OrganizationWithId {
  id?: number | string;
}

@Component({
  selector: 'app-teacher-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatTableModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatBadgeModule,
    TeacherMaterialDashboardComponent,
    UnifiedCourseCardComponent,
  ],
  template: `
    <div class="teacher-dashboard">
      <h1 class="page-title">教学仪表板</h1>

      <!-- 加载状态 -->
      <div *ngIf="isLoading" class="loading-container">
        <mat-spinner diameter="40"></mat-spinner>
        <p>加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div *ngIf="error" class="error-container">
        <mat-icon color="warn">error</mat-icon>
        <p>{{ error }}</p>
        <button mat-raised-button color="primary" (click)="loadTeacherData()">重新加载</button>
      </div>

      <!-- 部分数据加载失败提示 -->
      <div *ngIf="!isLoading && !error && hasAnyError()" class="partial-error">
        <div class="error-summary">
          <mat-icon>warning</mat-icon>
          <div>
            <p class="error-title">部分数据加载失败</p>
            <p class="error-subtitle">以下功能可能无法正常使用</p>
          </div>
        </div>
        <div class="error-details">
          <div *ngFor="let errorMsg of getErrorSummary()" class="error-item">
            <span>{{ errorMsg }}</span>
            <button mat-button class="retry-button" (click)="loadTeacherData()">重试</button>
          </div>
        </div>
      </div>

      <!-- 数据内容 -->
      <ng-container *ngIf="!isLoading && !error">
        <!-- 统计卡片 -->
        <div class="stats-grid" *ngIf="teacherStats$ | async as stats">
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon">
                <mat-icon color="primary">class</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ formatNumber(stats.classCount) }}</h3>
                <p>授课班级</p>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon">
                <mat-icon color="accent">people</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ formatNumber(stats.studentCount) }}</h3>
                <p>学生总数</p>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon">
                <mat-icon color="warn">assignment</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ formatNumber(stats.pendingAssignments) }}</h3>
                <p>待批改作业</p>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon">
                <mat-icon color="primary">token</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ formatNumber(stats.tokenBalance) }}</h3>
                <p>Token余额</p>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- 统一课程快速入口 -->
        <div class="section">
          <div class="section-header">
            <h2 class="section-title">我的课程</h2>
            <div class="header-actions">
              <button mat-raised-button color="accent" (click)="navigateToCourseManagement()">
                <mat-icon>manage_courses</mat-icon>
                课程管理
              </button>
              <button mat-raised-button color="primary" (click)="navigateToCreateCourse()">
                <mat-icon>add</mat-icon>
                创建课程
              </button>
            </div>
          </div>

          <!-- 使用统一课程卡片组件展示教师课程 -->
          <div class="course-grid" *ngIf="unifiedCourses$ | async as courses">
            <ng-container *ngIf="courses.length > 0; else noUnifiedCourses">
              <app-unified-course-card
                *ngFor="let course of courses"
                [config]="{
                  course: this.convertToUnifiedCourse(course),
                  showEnrollButton: false,
                  showProgress: true,
                  enrollmentProgress: getCourseProgress(course.id),
                  orgName: getOrgName(course.organizationId),
                  compact: false,
                }"
                (detail)="onCourseDetail(course.id)"
              >
              </app-unified-course-card>
            </ng-container>
            <ng-template #noUnifiedCourses>
              <div class="empty-state">
                <mat-icon>school</mat-icon>
                <p>暂无课程数据</p>
                <button mat-raised-button color="primary" (click)="navigateToCreateCourse()">
                  创建第一个课程
                </button>
              </div>
            </ng-template>
          </div>
        </div>

        <!-- 近期课程 -->
        <div class="section">
          <div class="section-header">
            <h2 class="section-title">近期课程</h2>
            <button mat-raised-button color="primary">
              <mat-icon>add</mat-icon>
              创建课程
            </button>
          </div>

          <div class="course-grid" *ngIf="recentCourses$ | async as courses">
            <ng-container *ngIf="courses.length > 0; else noCourses">
              <mat-card class="course-card" *ngFor="let course of courses">
                <mat-card-header>
                  <mat-card-title>{{ course.name }}</mat-card-title>
                  <mat-card-subtitle
                    >{{ course.organizationName }} ·
                    {{ course.studentCount }} 学生</mat-card-subtitle
                  >
                </mat-card-header>
                <mat-card-content>
                  <div class="course-stats">
                    <span><mat-icon>calendar_today</mat-icon> {{ course.schedule }}</span>
                    <span
                      ><mat-icon>assignment_turned_in</mat-icon>
                      {{ course.assignmentCount }} 作业</span
                    >
                  </div>
                </mat-card-content>
                <mat-card-actions>
                  <button mat-button>管理课程</button>
                  <button mat-button color="primary">查看学生</button>
                </mat-card-actions>
              </mat-card>
            </ng-container>
            <ng-template #noCourses>
              <div class="empty-state">
                <mat-icon>school</mat-icon>
                <p>暂无课程数据</p>
              </div>
            </ng-template>
          </div>
        </div>

        <!-- 跨机构教学进度展示（暂时禁用，需要适配MultiSourceTeacherData格式） -->
        <!--
      <div class="section">
        <h2 class="section-title">跨机构教学进度</h2>
        <mat-card>
          <mat-card-content>
            <app-learning-source-progress
              [stats]="multiSourceData$ | async"
              [loading]="progressLoading"
              [showOverallStats]="true"
              [showTabs]="true"
              [showSectionTitle]="false"
              userType="teacher">
            </app-learning-source-progress>
          </mat-card-content>
        </mat-card>
      </div>
      -->

        <!-- 学生表现 -->
        <div class="section">
          <h2 class="section-title">学生表现</h2>
          <mat-card>
            <mat-card-content>
              <table
                mat-table
                [dataSource]="students"
                class="performance-table"
                *ngIf="studentPerformance$ | async as students"
              >
                <ng-container *ngIf="students.length > 0; else noStudents">
                  <!-- 学生姓名 -->
                  <ng-container matColumnDef="studentName">
                    <th mat-header-cell *matHeaderCellDef>学生姓名</th>
                    <td mat-cell *matCellDef="let student">{{ student.studentName }}</td>
                  </ng-container>

                  <!-- 班级 -->
                  <ng-container matColumnDef="className">
                    <th mat-header-cell *matHeaderCellDef>班级</th>
                    <td mat-cell *matCellDef="let student">{{ student.className }}</td>
                  </ng-container>

                  <!-- 学习进度 -->
                  <ng-container matColumnDef="progress">
                    <th mat-header-cell *matHeaderCellDef>学习进度</th>
                    <td mat-cell *matCellDef="let student">
                      <div class="progress-display">
                        <span class="progress-percentage">{{ student.progress }}%</span>
                        <mat-progress-bar
                          class="progress-bar"
                          mode="determinate"
                          [value]="student.progress"
                          [color]="
                            student.progress >= 90
                              ? 'primary'
                              : student.progress >= 80
                                ? 'accent'
                                : 'warn'
                          "
                        >
                        </mat-progress-bar>
                      </div>
                    </td>
                  </ng-container>

                  <!-- 状态 -->
                  <ng-container matColumnDef="status">
                    <th mat-header-cell *matHeaderCellDef>状态</th>
                    <td mat-cell *matCellDef="let student">
                      <mat-chip
                        [color]="
                          getStatusFromProgress(student.progress) === '优秀'
                            ? 'primary'
                            : getStatusFromProgress(student.progress) === '良好'
                              ? 'accent'
                              : 'warn'
                        "
                        selected
                      >
                        {{ getStatusFromProgress(student.progress) }}
                      </mat-chip>
                    </td>
                  </ng-container>

                  <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
                  <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
                </ng-container>
                <ng-template #noStudents>
                  <div class="empty-state">
                    <mat-icon>people</mat-icon>
                    <p>暂无学生数据</p>
                  </div>
                </ng-template>
              </table>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- 课件库模块 -->
        <div class="section">
          <app-teacher-material-dashboard></app-teacher-material-dashboard>
        </div>
      </ng-container>
    </div>
  `,
  styles: [
    `
      .teacher-dashboard {
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

      .stat-card {
        mat-card-content {
          display: flex;
          align-items: center;
          padding: 20px;
        }
      }

      .stat-icon {
        margin-right: 20px;

        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
        }
      }

      .stat-info {
        h3 {
          margin: 0 0 4px 0;
          font-size: 32px;
          font-weight: 700;
          color: #333;
        }

        p {
          margin: 0;
          font-size: 14px;
          color: #666;
        }
      }

      .section {
        margin-bottom: 40px;
      }

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 12px;
      }

      .header-actions {
        display: flex;
        gap: 12px;
      }

      .section-title {
        font-size: 24px;
        font-weight: 600;
        margin: 0;
        color: #333;
      }

      .course-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
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
        }
      }

      .course-stats {
        display: flex;
        flex-direction: column;
        gap: 8px;

        span {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #666;
        }

        mat-icon {
          font-size: 20px;
          width: 20px;
          height: 20px;
        }
      }

      .performance-table {
        width: 100%;
      }

      .grade-excellent {
        color: #4caf50;
        font-weight: 600;
      }

      .grade-good {
        color: #ff9800;
        font-weight: 600;
      }

      .grade-average {
        color: #f44336;
        font-weight: 600;
      }

      .loading-container,
      .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;

        mat-spinner {
          margin-bottom: 16px;
        }

        p {
          color: #666;
          margin-bottom: 16px;
        }
      }

      .error-container {
        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
          color: #f44336;
          margin-bottom: 16px;
        }
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        grid-column: 1 / -1;
        color: #999;

        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
          margin-bottom: 12px;
        }

        p {
          margin: 0;
          font-size: 14px;
        }
      }

      @media (max-width: 768px) {
        .stats-grid {
          grid-template-columns: 1fr;
        }

        .course-grid {
          grid-template-columns: 1fr;
        }

        .section-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 12px;
        }

        .header-actions {
          flex-direction: column;
          width: 100%;
        }

        .header-actions .mat-raised-button {
          width: 100%;
        }
      }

      /* 进度显示样式 */
      .progress-display {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 120px;
      }

      .progress-percentage {
        font-size: 14px;
        font-weight: 600;
        min-width: 40px;
        text-align: right;
      }

      .progress-bar {
        flex-grow: 1;
        min-width: 60px;
        height: 8px;
        border-radius: 4px;
      }

      /* 部分错误状态提示 */
      .partial-error {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 20px;

        .error-summary {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 8px;

          mat-icon {
            color: #ff9800;
            font-size: 20px;
            width: 20px;
            height: 20px;
            flex-shrink: 0;
          }

          .error-title {
            font-weight: 600;
            color: #856404;
            margin: 0 0 4px 0;
            font-size: 14px;
          }
        }

        .error-details {
          margin-left: 32px;

          .error-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 4px;
            font-size: 13px;
            color: #666;

            .retry-button {
              font-size: 12px;
              padding: 2px 8px;
              min-height: 24px;
            }
          }
        }
      }
    `,
  ],
})
export class TeacherDashboardComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = ['name', 'className', 'progress', 'status', 'lastActivity'];

  // Observable数据流 - 使用TeacherService提供的类型安全数据
  dashboardData$: Observable<TeacherDashboardResponse | null> | null = null;
  multiSourceData$: Observable<MultiSourceTeacherData | null> | null = null;

  // 独立的Observable流（兼容性）
  teacherStats$: Observable<TeacherStats> | null = null;
  recentCourses$: Observable<TeacherCourse[]> | null = null;
  studentPerformance$: Observable<TeacherStudent[]> | null = null;
  pendingAssignments$: Observable<StudentAssignment[]> | null = null;
  recentActivities$: Observable<DashboardActivity[]> | null = null;

  // 统一课程数据流
  unifiedCourses$: Observable<TeacherCourse[]> | null = null;

  // 机构名称映射
  orgNameMap: Map<number, string> = new Map();

  // 加载状态
  progressLoading = false;
  isLoading = true;
  error: string | null = null;

  // 细粒度错误状态
  private errorState = {
    teacherStats: false,
    courses: false,
    students: false,
    assignments: false,
    activities: false,
    multiSource: false,
  };

  // 数据可用性状态
  dataAvailability = {
    hasTeacherStats: false,
    hasCourses: false,
    hasStudents: false,
    hasAssignments: false,
    hasActivities: false,
    hasMultiSourceData: false,
  };

  // 当前用户的组织ID（用于真实API调用）
  private currentOrgId: number | null = null;

  // 订阅管理
  private destroy$ = new Subject<void>();

  // 构造函数注入服务
  constructor(
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService,
    private teacherService: TeacherService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadTeacherData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载教师数据
   * 使用 TeacherService 获取真实数据，替换原有 mock 数据实现
   */
  loadTeacherData(): void {
    this.isLoading = true;
    this.error = null;

    this.authService.currentUser$
      .pipe(
        takeUntil(this.destroy$),
        switchMap((user: User | null) => this.loadUserAndOrganizations(user)),
        switchMap((data) => this.loadDashboardData(data)),
        catchError((err) => {
          console.error('加载教师数据失败:', err);
          this.error = '加载数据失败，请刷新页面重试';
          this.isLoading = false;
          return of(null);
        })
      )
      .subscribe();
  }

  /**
   * 加载用户和组织信息
   */
  private loadUserAndOrganizations(
    user: User | null
  ): Observable<{ userId: number; organizations: OrganizationWithId[] } | null> {
    if (!user?.id) {
      this.isLoading = false;
      return of(null);
    }

    const userId = typeof user.id === 'string' ? parseInt(user.id, 10) : user.id;

    // 先获取组织关联以确定 orgId
    return this.teacherService.getTeacherOrganizations(userId).pipe(
      map((organizations) => ({ userId, organizations })),
      catchError((err) => {
        console.warn('获取组织关联失败，继续使用 userId 加载:', err);
        return of({ userId, organizations: [] });
      })
    );
  }

  /**
   * 加载 Dashboard 数据
   */
  private loadDashboardData(
    data: { userId: number; organizations: OrganizationWithId[] } | null
  ): Observable<{ userId: number; organizations: OrganizationWithId[] } | null> {
    if (!data?.userId) {
      this.isLoading = false;
      return of(null);
    }

    const userId = data.userId;
    const organizations = data.organizations;

    // 尝试使用第一个组织的 ID 作为 orgId（用于真实 API 调用）
    const orgId =
      organizations.length > 0 && organizations[0].id
        ? typeof organizations[0].id === 'string'
          ? parseInt(organizations[0].id, 10)
          : organizations[0].id
        : undefined;
    this.currentOrgId = orgId ?? null;

    // 加载各个数据模块
    this.loadDashboardDataStream(userId, orgId);
    this.loadIndependentStreams(userId, orgId);
    this.loadMultiSourceProgress(userId);

    this.isLoading = false;
    return of(data);
  }

  /**
   * 加载 Dashboard 主数据流
   */
  private loadDashboardDataStream(userId: number, orgId?: number): void {
    this.dashboardData$ = this.teacherService.getTeacherDashboard(userId, orgId).pipe(
      takeUntil(this.destroy$),
      retry(2), // 最多重试 2 次
      map((dashboard) => {
        this.errorState.teacherStats = false;
        this.errorState.courses = false;
        this.errorState.students = false;
        this.dataAvailability.hasTeacherStats = !!dashboard?.stats;
        this.dataAvailability.hasCourses = (dashboard?.recentCourses?.length || 0) > 0;
        this.dataAvailability.hasStudents = (dashboard?.recentStudents?.length || 0) > 0;
        return dashboard;
      }),
      catchError((err) => {
        console.error('获取 Dashboard 数据失败（重试后）:', err);
        this.errorState.teacherStats = true;
        this.errorState.courses = true;
        this.errorState.students = true;
        return of(null);
      })
    );

    // 分解 Dashboard 数据为独立的 Observable 流（向后兼容）
    if (this.dashboardData$) {
      this.extractDashboardStreams();
    }
  }

  /**
   * 从 Dashboard 数据中提取各个 Observable 流
   */
  private extractDashboardStreams(): void {
    if (!this.dashboardData$) return;

    this.teacherStats$ = this.dashboardData$.pipe(
      map(
        (dashboard) =>
          dashboard?.stats ?? {
            classCount: 0,
            studentCount: 0,
            pendingAssignments: 0,
            tokenBalance: 0,
            activeCourses: 0,
            completedLessons: 0,
            totalLessons: 0,
            averageProgress: 0,
          }
      )
    );

    this.recentCourses$ = this.dashboardData$.pipe(
      map((dashboard) => dashboard?.recentCourses ?? [])
    );

    this.studentPerformance$ = this.dashboardData$.pipe(
      map((dashboard) => dashboard?.recentStudents ?? [])
    );
  }

  /**
   * 加载独立的数据流（作业和活动）
   */
  private loadIndependentStreams(userId: number, orgId?: number): void {
    this.loadPendingAssignments(userId, orgId);
    this.loadRecentActivities(userId, orgId);
  }

  /**
   * 加载待批改作业
   */
  private loadPendingAssignments(userId: number, orgId?: number): void {
    this.pendingAssignments$ = this.teacherService.getPendingAssignments(userId, orgId).pipe(
      takeUntil(this.destroy$),
      map((assignments) => {
        this.errorState.assignments = false;
        this.dataAvailability.hasAssignments = assignments.length > 0;
        return assignments;
      }),
      catchError((err) => {
        console.warn('获取待批改作业失败:', err);
        this.errorState.assignments = true;
        return of([]);
      })
    );
  }

  /**
   * 加载近期活动
   */
  private loadRecentActivities(userId: number, orgId?: number): void {
    this.recentActivities$ = this.teacherService.getRecentActivities(userId, orgId).pipe(
      takeUntil(this.destroy$),
      map((activities) => {
        this.errorState.activities = false;
        this.dataAvailability.hasActivities = activities.length > 0;
        return activities;
      }),
      catchError((err) => {
        console.warn('获取近期活动失败:', err);
        this.errorState.activities = true;
        return of([]);
      })
    );
  }

  /**
   * 加载跨机构教学进度统计
   */
  private loadMultiSourceProgress(userId: number): void {
    this.progressLoading = true;
    this.multiSourceData$ = this.teacherService.getUnifiedProgress(userId).pipe(
      takeUntil(this.destroy$),
      map((multiSourceData: MultiSourceTeacherData | null) => {
        this.progressLoading = false;
        return multiSourceData;
      }),
      catchError((err) => {
        console.error('获取跨机构进度失败:', err);
        this.progressLoading = false;
        return of(null);
      })
    );
  }

  // getStudentPerformance 方法已被移除，使用 TeacherService.getTeacherStudents 替代

  /**
   * 根据成绩获取状态
   */
  private getStatusFromGrade(grade: number): string {
    if (grade >= 90) return '优秀';
    if (grade >= 80) return '良好';
    if (grade >= 60) return '一般';
    return '需关注';
  }

  /**
   * 根据成绩获取状态（针对TeacherStudent接口）
   */
  getStatusFromProgress(progress: number): string {
    if (progress >= 90) return '优秀';
    if (progress >= 80) return '良好';
    if (progress >= 60) return '一般';
    return '需关注';
  }

  /**
   * 检查是否有任何数据加载错误
   */
  hasAnyError(): boolean {
    return Object.values(this.errorState).some((isError) => isError);
  }

  /**
   * 获取错误摘要信息
   */
  getErrorSummary(): string[] {
    const errors: string[] = [];

    if (this.errorState.teacherStats) {
      errors.push('统计数据加载失败');
    }
    if (this.errorState.courses) {
      errors.push('课程列表加载失败');
    }
    if (this.errorState.students) {
      errors.push('学生列表加载失败');
    }
    if (this.errorState.assignments) {
      errors.push('待批改作业加载失败');
    }
    if (this.errorState.activities) {
      errors.push('活动记录加载失败');
    }
    if (this.errorState.multiSource) {
      errors.push('跨机构数据加载失败');
    }

    return errors;
  }

  /**
   * 格式化数字
   */
  formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return '0';
    return value.toLocaleString('zh-CN');
  }

  /**
   * 重试加载特定数据部分
   */
  retryLoadData(dataType: keyof typeof this.errorState): void {
    this.errorState[dataType] = false;

    // 这里可以实现针对特定数据类型的重试逻辑
    // 目前简化为重新加载整个页面
    if (this.hasAnyError()) {
      this.loadTeacherData();
    }
  }

  // 获取课程进度
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getCourseProgress(_courseId: number): number {
    return 0; // 默认返回 0，实际应从服务获取
  }

  // 获取机构名称
  getOrgName(orgId: number): string {
    return this.orgNameMap.get(orgId) ?? '未知机构';
  }

  // 转换 TeacherCourse 为 UnifiedCourse(临时方案)
  convertToUnifiedCourse(course: TeacherCourse): UnifiedCourse {
    return {
      // 基础标识
      id: course.id,
      course_code: `C${course.id}`,
      org_id: course.organizationId || 0,
      scenario_type: 'school_curriculum' as const,

      // 元数据
      title: course.name,
      subtitle: undefined,
      description: '',
      cover_image_url: '',
      promo_video_url: '',

      // 分类信息
      category: 'other' as const,
      tags: [],
      level: 'intermediate' as const,
      subject: undefined,
      difficulty: 'intermediate' as const,
      duration_minutes: 0,

      // 课程详情
      learning_objectives: [],
      prerequisites: undefined,
      target_audience: undefined,

      // 时间和容量
      total_lessons: course.totalLessons ?? 0,
      estimated_duration_hours: 0,
      delivery_method: 'self_paced' as const,
      max_students: undefined,
      current_enrollments: course.studentCount,

      // 价格信息
      is_free: true,
      price: undefined,
      currency: undefined,

      // 进度安排
      enrollment_start_date: undefined,
      enrollment_end_date: undefined,
      course_start_date: course.startDate ?? undefined,
      course_end_date: course.endDate ?? undefined,
      schedule_pattern: undefined,

      // 教师信息
      primary_teacher_id: course.id,
      assistant_teacher_ids: undefined,
      teacher_name: null,
      source_type: 'school_curriculum' as LearningSourceType,

      // 课程资源
      materials: undefined,
      external_resources: undefined,

      // 评价和统计
      average_rating: 0,
      total_reviews: 0,
      completion_rate: undefined,
      enrollment_rate: undefined,

      // 状态和权限
      status: this.convertStatus(course.status),
      visibility: 'private' as const,
      is_featured: false,

      // AI 课程特有字段
      ai_generated: false,
      ai_model_version: undefined,
      ai_confidence_score: undefined,
      dynamic_content: false,

      // 元数据
      created_by: course.id,
      updated_by: course.id,
      created_at: course.startDate ?? new Date().toISOString(),
      updated_at: course.endDate ?? new Date().toISOString(),
      published_at: undefined,
    } as UnifiedCourse;
  }

  /**
   * 将教师课程状态映射到统一课程状态
   */
  private convertStatus(status: TeacherCourse['status']): CourseStatus {
    const statusMap: Record<TeacherCourse['status'], string> = {
      active: 'published',
      paused: 'published',
      completed: 'completed',
      draft: 'draft',
    };
    return (statusMap[status] || 'draft') as CourseStatus;
  }

  // 课程详情导航
  onCourseDetail(courseId: number): void {
    void this.router.navigate(['/teacher/course', courseId]);
  }

  // 导航到创建课程
  navigateToCreateCourse(): void {
    void this.router.navigate(['/teacher/courses']);
  }

  // 导航到课程管理
  navigateToCourseManagement(): void {
    void this.router.navigate(['/teacher/courses']);
  }
}
