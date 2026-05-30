/**
 * 学校管理员仪表板组件
 * 提供年级班级管理、校本课程管理、教师工作量统计、学生成长档案等功能
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { ActivatedRoute } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';

import { AuthService } from '../../core/services/auth.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import {
  GradeClass,
  SchoolAdminService,
  SchoolCourse,
  SchoolOverview,
  StudentGrowthRecord,
  TeacherWorkload,
} from '../../core/services/school-admin.service';
import {
  ProgressChartComponent,
  ProgressChartConfig,
  ProgressItem,
} from '../../shared/components/progress-chart/progress-chart.component';
import {
  StatsCardComponent,
  StatsCardConfig,
} from '../../shared/components/stats-card/stats-card.component';

@Component({
  selector: 'app-school-admin-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatTabsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressBarModule,
    MatDividerModule,
    StatsCardComponent,
    ProgressChartComponent,
  ],
  template: `
    <div class="dashboard-container">
      <header class="dashboard-header">
        <h1>学校管理</h1>
        <p class="subtitle">管理年级班级、课程、教师工作量及学生成长档案</p>
      </header>

      <!-- 学校概览 -->
      <mat-card class="overview-card" *ngIf="schoolOverview$ | async as overview">
        <mat-card-header>
          <mat-card-title>学校概览</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="stats-grid">
            <app-stats-card [config]="getOverviewStats(overview).totalGrades"></app-stats-card>
            <app-stats-card [config]="getOverviewStats(overview).totalClasses"></app-stats-card>
            <app-stats-card [config]="getOverviewStats(overview).totalStudents"></app-stats-card>
            <app-stats-card [config]="getOverviewStats(overview).totalTeachers"></app-stats-card>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 班级进度总览 -->
      <mat-card class="progress-section" *ngIf="classProgressConfig$ | async as classProgressConfig">
        <app-progress-chart [config]="classProgressConfig"></app-progress-chart>
      </mat-card>

      <!-- 课程报名进度 -->
      <mat-card class="progress-section" *ngIf="courseProgressConfig$ | async as courseProgressConfig">
        <app-progress-chart [config]="courseProgressConfig"></app-progress-chart>
      </mat-card>

      <!-- 功能模块 -->
      <mat-card class="tabs-card">
        <mat-tab-group [(selectedIndex)]="selectedTabIndex" animationDuration="300ms">
          <!-- 年级班级管理 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>groups</mat-icon>
              <span>年级班级</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>年级班级管理</h2>
                <button mat-raised-button color="primary"><mat-icon>add</mat-icon> 新增班级</button>
              </div>

              <table mat-table [dataSource]="gradeClasses$" class="data-table">
                <ng-container matColumnDef="name">
                  <th mat-header-cell *matHeaderCellDef>班级名称</th>
                  <td mat-cell *matCellDef="let item">{{ item.name }}</td>
                </ng-container>

                <ng-container matColumnDef="grade">
                  <th mat-header-cell *matHeaderCellDef>年级</th>
                  <td mat-cell *matCellDef="let item">{{ item.grade }}年级</td>
                </ng-container>

                <ng-container matColumnDef="studentCount">
                  <th mat-header-cell *matHeaderCellDef>学生数</th>
                  <td mat-cell *matCellDef="let item">{{ item.student_count }}</td>
                </ng-container>

                <ng-container matColumnDef="teacherCount">
                  <th mat-header-cell *matHeaderCellDef>教师数</th>
                  <td mat-cell *matCellDef="let item">{{ item.teacher_count }}</td>
                </ng-container>

                <ng-container matColumnDef="homeroomTeacher">
                  <th mat-header-cell *matHeaderCellDef>班主任</th>
                  <td mat-cell *matCellDef="let item">
                    {{ item.homeroom_teacher_name || '未分配' }}
                  </td>
                </ng-container>

                <tr mat-header-row *matHeaderRowDef="gradeClassColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: gradeClassColumns"></tr>
              </table>
            </div>
          </mat-tab>

          <!-- 校本课程管理 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>menu_book</mat-icon>
              <span>校本课程</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>校本课程管理</h2>
                <button mat-raised-button color="primary"><mat-icon>add</mat-icon> 新增课程</button>
              </div>

              <div class="courses-grid">
                <mat-card *ngFor="let course of schoolCourses$ | async" class="course-card">
                  <mat-card-header>
                    <mat-card-title>{{ course.name }}</mat-card-title>
                    <mat-chip
                      [color]="course.type === 'school_curriculum' ? 'primary' : 'accent'"
                      selected
                    >
                      {{ course.type === 'school_curriculum' ? '校本课程' : '兴趣班' }}
                    </mat-chip>
                  </mat-card-header>
                  <mat-card-content>
                    <p><strong>分类：</strong>{{ course.category }}</p>
                    <p><strong>授课教师：</strong>{{ course.teacher_name }}</p>
                    <p><strong>报名学生：</strong>{{ course.enrolled_students }}人</p>
                    <p><strong>上课时间：</strong>{{ course.schedule }}</p>
                    <p>
                      <strong>课程类型：</strong
                      >{{ course.type === 'school_curriculum' ? '校本课程' : '兴趣班' }}
                    </p>
                    <p><strong>课程状态：</strong>{{ getCourseStatusText(course.status) }}</p>
                  </mat-card-content>
                </mat-card>
              </div>
            </div>
          </mat-tab>

          <!-- 教师工作量统计 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>assessment</mat-icon>
              <span>教师工作量</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>教师工作量统计</h2>
              </div>

              <table mat-table [dataSource]="teacherWorkloads$" class="data-table">
                <ng-container matColumnDef="name">
                  <th mat-header-cell *matHeaderCellDef>教师姓名</th>
                  <td mat-cell *matCellDef="let item">{{ item.name }}</td>
                </ng-container>

                <ng-container matColumnDef="department">
                  <th mat-header-cell *matHeaderCellDef>所属部门</th>
                  <td mat-cell *matCellDef="let item">{{ item.department }}</td>
                </ng-container>

                <ng-container matColumnDef="courses">
                  <th mat-header-cell *matHeaderCellDef>授课数量</th>
                  <td mat-cell *matCellDef="let item">{{ item.courses_count }}</td>
                </ng-container>

                <ng-container matColumnDef="classes">
                  <th mat-header-cell *matHeaderCellDef>授课班级</th>
                  <td mat-cell *matCellDef="let item">{{ item.classes_count }}</td>
                </ng-container>

                <ng-container matColumnDef="totalHours">
                  <th mat-header-cell *matHeaderCellDef>总课时</th>
                  <td mat-cell *matCellDef="let item">{{ item.total_hours }}</td>
                </ng-container>

                <ng-container matColumnDef="students">
                  <th mat-header-cell *matHeaderCellDef>学生人数</th>
                  <td mat-cell *matCellDef="let item">{{ item.students_count }}</td>
                </ng-container>

                <tr mat-header-row *matHeaderRowDef="workloadColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: workloadColumns"></tr>
              </table>
            </div>
          </mat-tab>

          <!-- 学生成长档案 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>history_edu</mat-icon>
              <span>学生成长档案</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>学生成长档案</h2>
              </div>

              <div class="growth-records">
                <mat-card *ngFor="let record of studentGrowthRecords$ | async" class="growth-card">
                  <mat-card-header>
                    <mat-card-title>{{ record.name }}</mat-card-title>
                    <mat-card-subtitle
                      >{{ record.grade }} - {{ record.class_name }}</mat-card-subtitle
                    >
                  </mat-card-header>
                  <mat-card-content>
                    <mat-divider></mat-divider>
                    <div class="growth-stats">
                      <div class="growth-item">
                        <span class="label">学期</span>
                        <span class="value">{{ record.term }}</span>
                      </div>
                      <div class="growth-item">
                        <span class="label">选课数</span>
                        <span class="value">{{ record.courses_taken }}</span>
                      </div>
                      <div class="growth-item">
                        <span class="label">平均分</span>
                        <span class="value">{{
                          record.avg_score > 0 ? record.avg_score : '待评定'
                        }}</span>
                      </div>
                      <div class="growth-item">
                        <span class="label">出勤率</span>
                        <span class="value">{{
                          record.attendance_rate > 0 ? record.attendance_rate + '%' : '待统计'
                        }}</span>
                      </div>
                      <div class="growth-item">
                        <span class="label">操行分</span>
                        <span class="value">{{ record.conduct_score || '待评定' }}</span>
                      </div>
                      <div class="growth-item">
                        <span class="label">课外活动</span>
                        <span class="value">{{ record.extracurricular_count }}项</span>
                      </div>
                    </div>
                    <div class="achievements" *ngIf="record.achievements.length">
                      <strong>获得荣誉：</strong>
                      <mat-chip-listbox>
                        <mat-chip
                          *ngFor="let achievement of record.achievements"
                          [color]="getAchievementColor(achievement.type)"
                          selected
                        >
                          {{ achievement.name }}
                        </mat-chip>
                      </mat-chip-listbox>
                    </div>
                  </mat-card-content>
                </mat-card>
              </div>
            </div>
          </mat-tab>
        </mat-tab-group>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .dashboard-container {
        padding: 24px;
        max-width: 1400px;
        margin: 0 auto;
      }

      .dashboard-header {
        margin-bottom: 24px;

        h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 500;
          color: #333;
        }

        .subtitle {
          margin: 8px 0 0;
          color: #666;
          font-size: 14px;
        }
      }

      .overview-card {
        margin-bottom: 24px;

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          padding: 16px 0;
        }
      }

      .progress-section {
        margin-bottom: 24px;
      }

      .tabs-card {
        .tab-content {
          padding: 24px;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;

          h2 {
            margin: 0;
            font-size: 20px;
            font-weight: 500;
          }
        }
      }

      .data-table {
        width: 100%;
      }

      .courses-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;

        .course-card {
          mat-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
          }

          mat-card-title {
            font-size: 18px;
            margin: 0;
          }

          p {
            margin: 8px 0;
            font-size: 14px;
            color: #555;
          }
        }
      }

      .growth-records {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;

        .growth-card {
          mat-card-header {
            margin-bottom: 12px;
          }

          mat-card-title {
            font-size: 18px;
          }

          mat-card-subtitle {
            font-size: 14px;
          }

          mat-divider {
            margin-bottom: 16px;
          }

          .growth-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;

            .growth-item {
              display: flex;
              flex-direction: column;

              .label {
                font-size: 12px;
                color: #888;
              }

              .value {
                font-size: 16px;
                font-weight: 500;
                color: #333;
              }
            }
          }

          .achievements {
            margin-top: 16px;

            strong {
              font-size: 14px;
              color: #555;
            }
          }
        }
      }

      @media (max-width: 768px) {
        .overview-card .stats-grid {
          grid-template-columns: repeat(2, 1fr);
        }

        .dashboard-container {
          padding: 16px;
        }
      }
    `,
  ],
})
export class SchoolAdminDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private schoolId = 1;

  schoolOverview$!: Observable<SchoolOverview>;
  gradeClasses$!: Observable<GradeClass[]>;
  schoolCourses$!: Observable<SchoolCourse[]>;
  teacherWorkloads$!: Observable<TeacherWorkload[]>;
  studentGrowthRecords$!: Observable<StudentGrowthRecord[]>;
  classProgressConfig$!: Observable<ProgressChartConfig>;
  courseProgressConfig$!: Observable<ProgressChartConfig>;

  selectedTabIndex = 0;
  gradeClassColumns = ['name', 'grade', 'studentCount', 'teacherCount', 'homeroomTeacher'];
  workloadColumns = ['name', 'department', 'courses', 'classes', 'totalHours', 'students'];

  /**
   * 获取概览统计数据配置
   */
  getOverviewStats(overview: SchoolOverview): {
    totalGrades: StatsCardConfig;
    totalClasses: StatsCardConfig;
    totalStudents: StatsCardConfig;
    totalTeachers: StatsCardConfig;
  } {
    return {
      totalGrades: {
        value: overview.total_grades,
        label: '年级数',
        icon: 'school',
        color: 'primary',
        clickable: true,
      },
      totalClasses: {
        value: overview.total_classes,
        label: '班级数',
        icon: 'class',
        color: 'accent',
        clickable: true,
      },
      totalStudents: {
        value: overview.total_students,
        label: '学生数',
        icon: 'person',
        color: 'success',
        clickable: true,
      },
      totalTeachers: {
        value: overview.total_teachers,
        label: '教师数',
        icon: 'supervisor_account',
        color: 'warn',
        clickable: true,
      },
    };
  }

  constructor(
    private schoolAdminService: SchoolAdminService,
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // 监听路由路径切换Tab
    this.route.url.pipe(takeUntil(this.destroy$)).subscribe((url) => {
      const path = url[0]?.path;
      // 根据路由路径设置默认Tab
      switch (path) {
        case 'school-courses':
          this.selectedTabIndex = 1;
          break;
        case 'quality':
        case 'teacher-workload':
          this.selectedTabIndex = 2;
          break;
        case 'student-growth':
          this.selectedTabIndex = 3;
          break;
        default:
          this.selectedTabIndex = 0;
      }
    });

    // 初始化默认数据
    this.schoolOverview$ = this.schoolAdminService.getSchoolOverview(this.schoolId);
    this.loadData(this.schoolId);

    const user = this.authService.getCurrentUser();
    if (user?.id) {
      const userId = typeof user.id === 'string' ? parseInt(user.id, 10) : user.id;
      this.multiSourceService
        .getUserOrganizations(userId)
        .pipe(takeUntil(this.destroy$))
        .subscribe((response) => {
          this.schoolId = response?.items?.[0]?.id || 1;
          this.loadData(this.schoolId);
          this.schoolOverview$ = this.schoolAdminService.getSchoolOverview(this.schoolId);
        });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(schoolId: number): void {
    this.gradeClasses$ = this.schoolAdminService.getGradeClasses(schoolId);
    this.schoolCourses$ = this.schoolAdminService.getSchoolCourses(schoolId);
    this.teacherWorkloads$ = this.schoolAdminService.getTeacherWorkloads(schoolId);
    this.studentGrowthRecords$ = this.schoolAdminService.getStudentGrowthRecords(schoolId);
    this.classProgressConfig$ = this.buildClassProgressConfig(schoolId);
    this.courseProgressConfig$ = this.buildCourseProgressConfig(schoolId);
  }

  /**
   * 构建班级进度图表配置
   */
  private buildClassProgressConfig(schoolId: number): Observable<ProgressChartConfig> {
    return this.schoolAdminService.getGradeClasses(schoolId).pipe(
      map((classes) => {
        const items: ProgressItem[] = classes.map((cls, index) => ({
          id: cls.id,
          label: cls.name,
          progress: Math.min((cls.student_count / cls.capacity) * 100, 100),
          subtitle: `${cls.student_count}/${cls.capacity}人`,
          color: cls.student_count >= cls.capacity
            ? 'warn'
            : cls.student_count >= cls.capacity * 0.8
              ? 'accent'
              : ('primary' as ProgressItem['color']),
          icon: 'group',
          clickable: true,
        }));

        return {
          title: '班级满员率',
          items,
          mode: 'bar',
          showOverall: true,
          showLegend: true,
          maxItems: 8,
          emptyText: '暂无班级数据',
        };
      })
    );
  }

  /**
   * 构建课程报名进度图表配置
   */
  private buildCourseProgressConfig(schoolId: number): Observable<ProgressChartConfig> {
    return this.schoolAdminService.getSchoolCourses(schoolId).pipe(
      map((courses) => {
        const items: ProgressItem[] = courses.map((course, index) => ({
          id: course.id,
          label: course.name,
          progress: Math.min((course.enrolled_students / course.capacity) * 100, 100),
          subtitle: `${course.enrolled_students}/${course.capacity}人`,
          extra: course.type === 'school_curriculum' ? '校本课程' : '兴趣班',
          color: course.status === 'completed'
            ? 'success'
            : course.enrolled_students >= course.capacity
              ? 'warn'
              : course.type === 'school_curriculum'
                ? ('primary' as ProgressItem['color'])
                : ('accent' as ProgressItem['color']),
          icon: 'menu_book',
          clickable: true,
        }));

        return {
          title: '课程报名进度',
          items,
          mode: 'bar',
          showOverall: true,
          showLegend: true,
          maxItems: 8,
          emptyText: '暂无课程数据',
        };
      })
    );
  }

  /**
   * 获取课程状态文本
   */
  getCourseStatusText(status: string): string {
    const statusText: Record<string, string> = {
      draft: '草稿',
      published: '已发布',
      ongoing: '进行中',
      completed: '已完成',
      archived: '已归档',
    };
    return statusText[status] || status;
  }

  /**
   * 获取成就类型颜色
   */
  getAchievementColor(type: string): string {
    const colorMap: Record<string, string> = {
      academic: 'primary',
      sports: 'accent',
      arts: 'warn',
      leadership: 'success',
      service: 'basic',
    };
    return colorMap[type] || 'basic';
  }

  /**
   * 获取班级状态颜色
   */
  getClassStatusColor(status: string): string {
    const statusColors: Record<string, string> = {
      active: 'primary',
      graduated: 'accent',
      disbanded: 'warn',
      inactive: 'basic',
    };
    return statusColors[status] || 'basic';
  }

  /**
   * 获取班级状态文本
   */
  getClassStatusText(status: string): string {
    const statusText: Record<string, string> = {
      active: '活跃',
      graduated: '已毕业',
      disbanded: '已解散',
      inactive: '非活跃',
    };
    return statusText[status] || status;
  }

  /**
   * 新增班级
   */
  addNewClass(): void {
    // TODO: 实现新增班级对话框
    console.log('打开新增班级对话框');
  }

  /**
   * 新增课程
   */
  addNewCourse(): void {
    // TODO: 实现新增课程对话框
    console.log('打开新增课程对话框');
  }

  /**
   * 查看班级详情
   */
  viewClassDetails(classItem: GradeClass): void {
    // TODO: 实现查看班级详情功能
    console.log('查看班级详情:', classItem);
  }

  /**
   * 查看课程详情
   */
  viewCourseDetails(course: SchoolCourse): void {
    // TODO: 实现查看课程详情功能
    console.log('查看课程详情:', course);
  }

  /**
   * 查看教师详情
   */
  viewTeacherDetails(teacher: TeacherWorkload): void {
    // TODO: 实现查看教师详情功能
    console.log('查看教师详情:', teacher);
  }

  /**
   * 查看学生成长详情
   */
  viewStudentGrowthDetails(record: StudentGrowthRecord): void {
    // TODO: 实现查看学生成长详情功能
    console.log('查看学生成长详情:', record);
  }

  /**
   * 刷新所有数据
   */
  refreshAllData(): void {
    this.loadData(this.schoolId);
    this.schoolOverview$ = this.schoolAdminService.getSchoolOverview(this.schoolId);
  }

  /**
   * 导出学校报表
   */
  exportSchoolReport(): void {
    // TODO: 实现导出学校报表功能
    console.log('导出学校报表');
  }
}
