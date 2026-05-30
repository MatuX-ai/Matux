/**
 * 教育局仪表板组件
 * 提供区域数据概览、学校数据对比、教学质量监控、资源调配建议等功能
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject, Observable } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';

import { AuthService } from '../../core/services/auth.service';
import {
  EducationBureauService,
  RegionalOverview,
} from '../../core/services/education-bureau.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import { EducationBureauMaterialDashboardComponent } from '../../shared/components/education-bureau-material-dashboard/education-bureau-material-dashboard.component';
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
  selector: 'app-education-bureau-dashboard',
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
    MatSelectModule,
    MatFormFieldModule,
    MatTooltipModule,
    StatsCardComponent,
    EducationBureauMaterialDashboardComponent,
    ProgressChartComponent,
  ],
  template: `
    <div class="dashboard-container">
      <header class="dashboard-header">
        <div class="header-content">
          <div>
            <h1>教育局管理后台</h1>
            <p class="subtitle">区域教育数据汇总与监管平台</p>
          </div>
          <div class="header-actions">
            <button mat-raised-button color="primary" (click)="exportReport('excel')">
              <mat-icon>download</mat-icon> 导出Excel
            </button>
            <button mat-raised-button (click)="exportReport('pdf')">
              <mat-icon>picture_as_pdf</mat-icon> 导出PDF
            </button>
          </div>
        </div>
      </header>

      <!-- 区域概览 -->
      <mat-card class="overview-card" *ngIf="regionOverview$ | async as overview">
        <mat-card-header>
          <mat-card-title>区域数据概览</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="stats-grid">
            <app-stats-card
              [config]="getRegionOverviewStats(overview).totalSchools"
            ></app-stats-card>
            <app-stats-card
              [config]="getRegionOverviewStats(overview).totalStudents"
            ></app-stats-card>
            <app-stats-card
              [config]="getRegionOverviewStats(overview).totalTeachers"
            ></app-stats-card>
            <app-stats-card
              [config]="getRegionOverviewStats(overview).totalClasses"
            ></app-stats-card>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 学校达标率进度 -->
      <mat-card class="progress-section" *ngIf="qualityProgressConfig$ | async as qualityConfig">
        <app-progress-chart [config]="qualityConfig"></app-progress-chart>
      </mat-card>

      <!-- 功能模块 -->
      <mat-card class="tabs-card">
        <mat-tab-group animationDuration="300ms">
          <!-- 学校数据对比 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>compare</mat-icon>
              <span>学校对比</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>学校数据对比分析</h2>
              </div>

              <table mat-table [dataSource]="schoolComparisons$" class="data-table">
                <ng-container matColumnDef="name">
                  <th mat-header-cell *matHeaderCellDef>学校名称</th>
                  <td mat-cell *matCellDef="let item">{{ item.school_name }}</td>
                </ng-container>

                <ng-container matColumnDef="studentCount">
                  <th mat-header-cell *matHeaderCellDef>学生人数</th>
                  <td mat-cell *matCellDef="let item">{{ item.total_students }}</td>
                </ng-container>

                <ng-container matColumnDef="teacherCount">
                  <th mat-header-cell *matHeaderCellDef>教师人数</th>
                  <td mat-cell *matCellDef="let item">{{ item.total_teachers }}</td>
                </ng-container>

                <ng-container matColumnDef="avgScore">
                  <th mat-header-cell *matHeaderCellDef>平均分</th>
                  <td mat-cell *matCellDef="let item">
                    <span
                      [class.score-high]="item.avg_test_score >= 85"
                      [class.score-mid]="item.avg_test_score >= 70 && item.avg_test_score < 85"
                      [class.score-low]="item.avg_test_score < 70"
                    >
                      {{ item.avg_test_score }}
                    </span>
                  </td>
                </ng-container>

                <ng-container matColumnDef="passRate">
                  <th mat-header-cell *matHeaderCellDef>及格率</th>
                  <td mat-cell *matCellDef="let item">
                    <div class="rate-cell">
                      <mat-progress-bar
                        mode="determinate"
                        [value]="item.qualification_rate"
                      ></mat-progress-bar>
                      <span>{{ item.qualification_rate }}%</span>
                    </div>
                  </td>
                </ng-container>

                <ng-container matColumnDef="excellentRate">
                  <th mat-header-cell *matHeaderCellDef>优秀率</th>
                  <td mat-cell *matCellDef="let item">
                    <div class="rate-cell">
                      <mat-progress-bar
                        mode="determinate"
                        [value]="item.excellent_rate"
                        color="accent"
                      ></mat-progress-bar>
                      <span>{{ item.excellent_rate }}%</span>
                    </div>
                  </td>
                </ng-container>

                <tr mat-header-row *matHeaderRowDef="comparisonColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: comparisonColumns"></tr>
              </table>
            </div>
          </mat-tab>

          <!-- 教学质量监控 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>monitor_heart</mat-icon>
              <span>质量监控</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>教学质量监控</h2>
              </div>

              <div class="quality-overview" *ngIf="qualityMetrics$ | async as metrics">
                <mat-card class="quality-card" *ngFor="let metric of metrics">
                  <mat-card-content>
                    <div class="quality-stat">
                      <div class="quality-value">
                        {{ metric.current_value }}{{ metric.unit === '分数' ? '' : metric.unit }}
                      </div>
                      <div class="quality-label">{{ metric.metric_name }}</div>
                      <div class="metric-status">
                        <mat-chip [color]="getMetricStatusColor(metric.status)" selected>
                          {{ getMetricStatusText(metric.status) }}
                        </mat-chip>
                        <mat-chip class="trend-chip">
                          <mat-icon>{{ getTrendIcon(metric.trend) }}</mat-icon>
                        </mat-chip>
                      </div>
                    </div>
                  </mat-card-content>
                </mat-card>
              </div>

              <div class="score-distributions" *ngIf="scoreDistributions$ | async as distributions">
                <mat-card class="distribution-card" *ngFor="let distribution of distributions">
                  <mat-card-header>
                    <mat-card-title
                      >{{ distribution.subject }} - {{ distribution.grade_level }}</mat-card-title
                    >
                    <mat-card-subtitle>
                      平均分: {{ distribution.avg_score }} | 及格率: {{ distribution.pass_rate }}% |
                      优秀率: {{ distribution.excellent_rate }}%
                    </mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <div class="distribution-chart">
                      <div
                        class="distribution-bar"
                        *ngFor="let range of distribution.score_ranges"
                        [style.flex-grow]="range.percentage"
                      >
                        <span class="bar-label">{{ range.range }}</span>
                        <div class="bar-fill" [style.height.%]="range.percentage"></div>
                        <span class="bar-value">{{ range.count }}人 ({{ range.percentage }}%)</span>
                      </div>
                    </div>
                  </mat-card-content>
                </mat-card>
              </div>
            </div>
          </mat-tab>

          <!-- 资源调配建议 -->
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>lightbulb</mat-icon>
              <span>资源建议</span>
            </ng-template>
            <div class="tab-content">
              <div class="section-header">
                <h2>AI资源调配建议</h2>
              </div>

              <div class="recommendations">
                <mat-card
                  *ngFor="let rec of resourceRecommendations$ | async"
                  class="recommendation-card"
                  [class.priority-high]="rec.priority_level === 'high'"
                  [class.priority-medium]="rec.priority_level === 'medium'"
                  [class.priority-low]="rec.priority_level === 'low'"
                >
                  <mat-card-header>
                    <mat-icon mat-card-avatar [class]="'category-' + rec.category">
                      {{ getCategoryIcon(rec.category) }}
                    </mat-icon>
                    <mat-card-title>{{ rec.title }}</mat-card-title>
                    <mat-card-subtitle>
                      <mat-chip [color]="getPriorityColor(rec.priority_level)" selected>
                        {{ getPriorityLabel(rec.priority_level) }}
                      </mat-chip>
                    </mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <p class="description">{{ rec.description }}</p>
                    <mat-divider></mat-divider>
                    <div class="recommendation-details">
                      <p><strong>建议措施：</strong>{{ rec.suggested_action }}</p>
                      <p>
                        <strong>预期影响：</strong>预计{{ rec.expected_impact.metric }}从{{
                          rec.expected_impact.current_value
                        }}提升至{{ rec.expected_impact.projected_value }}，提升幅度{{
                          rec.expected_impact.improvement
                        }}%
                      </p>
                      <p><strong>涉及学校：</strong>{{ rec.affected_schools.length }}所</p>
                    </div>
                  </mat-card-content>
                </mat-card>
              </div>
            </div>
          </mat-tab>
        </mat-tab-group>
      </mat-card>

      <!-- 课件库模块 -->
      <mat-card class="dashboard-card">
        <app-education-bureau-material-dashboard></app-education-bureau-material-dashboard>
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

        .header-content {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

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

        .header-actions {
          display: flex;
          gap: 12px;
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

        .score-high {
          color: #4caf50;
          font-weight: 500;
        }
        .score-mid {
          color: #ff9800;
          font-weight: 500;
        }
        .score-low {
          color: #f44336;
          font-weight: 500;
        }

        .rate-cell {
          display: flex;
          align-items: center;
          gap: 8px;

          mat-progress-bar {
            flex: 1;
            max-width: 100px;
          }
        }
      }

      .quality-overview {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 16px;

        .quality-card {
          .quality-stat {
            text-align: center;
            padding: 16px;

            .quality-value {
              font-size: 42px;
              font-weight: 500;
              color: #1976d2;
            }

            .quality-label {
              font-size: 14px;
              color: #666;
              margin-bottom: 12px;
            }
          }
        }

        .distribution-card {
          grid-column: span 2;

          .distribution-chart {
            display: flex;
            height: 200px;
            align-items: flex-end;
            gap: 12px;
            padding: 20px;

            .distribution-bar {
              display: flex;
              flex-direction: column;
              align-items: center;
              min-width: 60px;

              .bar-label {
                font-size: 12px;
                color: #666;
                margin-bottom: 8px;
              }

              .bar-fill {
                width: 100%;
                background: linear-gradient(180deg, #1976d2, #42a5f5);
                border-radius: 4px 4px 0 0;
                min-height: 20px;
              }

              .bar-value {
                font-size: 12px;
                color: #333;
                margin-top: 8px;
                font-weight: 500;
              }
            }
          }
        }
      }

      .problem-courses-card {
        .problem-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;

          .course-name {
            font-weight: 500;
          }

          .course-rate {
            display: flex;
            align-items: center;
            gap: 12px;

            mat-progress-bar {
              width: 150px;
            }

            .rate-value {
              font-size: 14px;
              color: #f44336;
            }
          }
        }
      }

      .recommendations {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 16px;

        .recommendation-card {
          border-left: 4px solid #ccc;

          &.priority-high {
            border-left-color: #f44336;
          }
          &.priority-medium {
            border-left-color: #ff9800;
          }
          &.priority-low {
            border-left-color: #4caf50;
          }

          mat-card-header {
            margin-bottom: 12px;

            mat-icon.avatar {
              background: #f5f5f5;
              padding: 8px;
              border-radius: 50%;

              &.type-teacher {
                color: #1976d2;
              }
              &.type-course {
                color: #9c27b0;
              }
              &.type-facility {
                color: #ff9800;
              }
            }
          }

          .description {
            font-size: 14px;
            color: #555;
            margin-bottom: 12px;
          }

          mat-divider {
            margin-bottom: 12px;
          }

          .suggestion {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            font-size: 14px;
            color: #333;

            mat-icon {
              font-size: 18px;
              width: 18px;
              height: 18px;
              color: #4caf50;
            }
          }
        }
      }

      @media (max-width: 768px) {
        .overview-card .stats-grid {
          grid-template-columns: repeat(2, 1fr);
        }

        .dashboard-header .header-content {
          flex-direction: column;
          gap: 16px;
        }

        .quality-overview .distribution-card {
          grid-column: span 1;
        }
      }
    `,
  ],
})
export class EducationBureauDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private regionId = 1;

  regionOverview$ = this.educationBureauService.getRegionalOverview(this.regionId);
  schoolComparisons$ = this.educationBureauService.getSchoolComparisons(this.regionId);
  qualityMetrics$ = this.educationBureauService.getTeachingQualityMetrics(this.regionId);
  scoreDistributions$ = this.educationBureauService.getScoreDistributions(this.regionId);
  resourceRecommendations$ = this.educationBureauService.getResourceRecommendations(this.regionId);
  qualityProgressConfig$ = this.buildQualityProgressConfig();

  comparisonColumns = [
    'name',
    'studentCount',
    'teacherCount',
    'avgScore',
    'passRate',
    'excellentRate',
  ];

  /**
   * 构建教学质量达标率进度图表配置
   */
  private buildQualityProgressConfig(): Observable<ProgressChartConfig> {
    return this.educationBureauService.getTeachingQualityMetrics(this.regionId).pipe(
      map((metrics) => {
        const items: ProgressItem[] = metrics.map((metric) => ({
          id: metric.metric_id,
          label: metric.metric_name,
          progress: Math.min(
            (metric.schools_meeting_target /
              (metric.schools_meeting_target + metric.schools_below_target)) *
              100,
            100
          ),
          subtitle: `${metric.schools_meeting_target}/${metric.schools_meeting_target + metric.schools_below_target}所学校达标`,
          color: metric.status === 'excellent'
            ? 'success'
            : metric.status === 'good'
              ? 'primary'
              : metric.status === 'fair'
                ? 'accent'
                : ('warn' as ProgressItem['color']),
          icon: metric.metric_type === 'academic'
            ? 'school'
            : metric.metric_type === 'attendance'
              ? 'event_available'
              : metric.metric_type === 'infrastructure'
                ? 'business'
                : 'gavel',
          clickable: true,
        }));

        return {
          title: '教学质量指标达标率',
          items,
          mode: 'bar',
          showOverall: true,
          showLegend: true,
          maxItems: 8,
          emptyText: '暂无质量指标数据',
        };
      })
    );
  }

  /**
   * 获取区域概览统计数据配置
   */
  getRegionOverviewStats(overview: RegionalOverview): {
    totalSchools: StatsCardConfig;
    totalStudents: StatsCardConfig;
    totalTeachers: StatsCardConfig;
    totalClasses: StatsCardConfig;
  } {
    return {
      totalSchools: {
        value: overview.total_schools,
        label: '学校数量',
        icon: 'domain',
        color: 'primary',
        clickable: true,
      },
      totalStudents: {
        value: overview.total_students,
        label: '学生总数',
        icon: 'person',
        color: 'accent',
        clickable: true,
      },
      totalTeachers: {
        value: overview.total_teachers,
        label: '教师总数',
        icon: 'supervisor_account',
        color: 'success',
        clickable: true,
      },
      totalClasses: {
        value: overview.total_classes,
        label: '班级总数',
        icon: 'class',
        color: 'warn',
        clickable: true,
      },
    };
  }

  constructor(
    private educationBureauService: EducationBureauService,
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    if (user?.id) {
      const userId = typeof user.id === 'string' ? parseInt(user.id, 10) : user.id;
      this.multiSourceService
        .getUserOrganizations(userId)
        .pipe(takeUntil(this.destroy$))
        .subscribe((response) => {
          this.regionId = response?.items?.[0]?.id || 1;
          // 重新加载数据
          this.regionOverview$ = this.educationBureauService.getRegionalOverview(this.regionId);
          this.schoolComparisons$ = this.educationBureauService.getSchoolComparisons(this.regionId);
          this.qualityMetrics$ = this.educationBureauService.getTeachingQualityMetrics(
            this.regionId
          );
          this.scoreDistributions$ = this.educationBureauService.getScoreDistributions(
            this.regionId
          );
          this.resourceRecommendations$ = this.educationBureauService.getResourceRecommendations(
            this.regionId
          );
        });
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  exportReport(format: 'excel' | 'pdf'): void {
    this.educationBureauService
      .exportReport({
        format,
        data_type: 'all',
        include_charts: true,
      })
      .subscribe((blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `教育局数据报表_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        a.click();
        window.URL.revokeObjectURL(url);
      });
  }

  getTypeIcon(type: string): string {
    const icons: Record<string, string> = {
      teacher: 'person',
      course: 'menu_book',
      facility: 'business',
    };
    return icons[type] || 'info';
  }

  getTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      teacher: '师资调配',
      course: '课程优化',
      facility: '设施改善',
    };
    return labels[type] || type;
  }

  /**
   * 获取类别图标
   */
  getCategoryIcon(category: string): string {
    const icons: Record<string, string> = {
      staffing: 'person',
      funding: 'attach_money',
      infrastructure: 'business',
      curriculum: 'menu_book',
    };
    return icons[category] || 'info';
  }

  /**
   * 获取质量指标状态颜色
   */
  getMetricStatusColor(status: string): string {
    const colors: Record<string, string> = {
      excellent: 'primary',
      good: 'accent',
      fair: 'basic',
      poor: 'warn',
      critical: 'warn',
    };
    return colors[status] || 'basic';
  }

  /**
   * 获取质量指标状态文本
   */
  getMetricStatusText(status: string): string {
    const labels: Record<string, string> = {
      excellent: '优秀',
      good: '良好',
      fair: '一般',
      poor: '较差',
      critical: '严重',
    };
    return labels[status] || status;
  }

  /**
   * 获取趋势图标
   */
  getTrendIcon(trend: string): string {
    const icons: Record<string, string> = {
      improving: 'trending_up',
      stable: 'trending_flat',
      declining: 'trending_down',
    };
    return icons[trend] || 'trending_flat';
  }

  getPriorityColor(priority: string): string {
    const colors: Record<string, string> = {
      high: 'warn',
      medium: 'accent',
      low: 'primary',
    };
    return colors[priority] || 'primary';
  }

  getPriorityLabel(priority: string): string {
    const labels: Record<string, string> = {
      high: '高优先级',
      medium: '中优先级',
      low: '低优先级',
    };
    return labels[priority] || priority;
  }
}
