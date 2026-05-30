import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import {
  DashboardData,
  Sponsorship,
  SponsorshipAnalytics,
  SponsorshipDashboardService,
} from './sponsorship-dashboard.service';

// 创建赞助活动的表单数据接口
export interface CreateSponsorshipFormData {
  name: string;
  description: string;
  sponsor_amount: number;
  currency: string;
  start_date: Date;
  end_date: Date;
  exposure_types: string[];
  target_audience: string;
}

// 传递给后端的数据接口 (日期为 ISO 字符串)
export interface CreateSponsorshipPayload extends Omit<
  Sponsorship,
  | 'id'
  | 'org_id'
  | 'created_at'
  | 'updated_at'
  | 'total_exposures'
  | 'total_points_earned'
  | 'conversion_rate'
> {}

export interface DialogData {
  data?: Partial<CreateSponsorshipFormData>;
}

@Component({
  selector: 'app-sponsorship-dashboard',
  standalone: false,
  template: `
    <div class="sponsorship-dashboard">
      <!-- 页面头部 -->
      <div class="dashboard-header">
        <div class="header-content">
          <div>
            <h1>企业赞助管理仪表板</h1>
            <p>品牌曝光统计与公益积分转换平台</p>
          </div>
          <div class="header-actions">
            <button mat-raised-button color="primary" (click)="refreshData()">
              <mat-icon>refresh</mat-icon>
              刷新数据
            </button>
            <button mat-raised-button color="accent" (click)="openCreateDialog()">
              <mat-icon>add</mat-icon>
              新建赞助活动
            </button>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div *ngIf="loading" class="loading-container">
        <mat-spinner diameter="40"></mat-spinner>
        <p>正在加载仪表板数据...</p>
      </div>

      <!-- 主要内容 -->
      <div *ngIf="!loading" class="dashboard-content">
        <!-- 关键指标卡片 -->
        <div class="stats-grid">
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon sponsorship-icon">
                <mat-icon>business</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ dashboardData?.summary?.total_sponsorships || 0 }}</h3>
                <p>总赞助活动</p>
                <span class="stat-change positive">
                  活跃 {{ dashboardData?.summary?.active_sponsorships || 0 }} 个
                </span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon money-icon">
                <mat-icon>attach_money</mat-icon>
              </div>
              <div class="stat-info">
                <h3>
                  ¥{{ dashboardData?.summary?.total_sponsorship_amount || 0 | number: '1.0-0' }}
                </h3>
                <p>总赞助金额</p>
                <span class="stat-change positive">+15.2%</span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon exposure-icon">
                <mat-icon>visibility</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ dashboardData?.summary?.total_exposures || 0 | number }}</h3>
                <p>总品牌曝光</p>
                <span class="stat-change positive">
                  近期 {{ dashboardData?.summary?.recent_exposures || 0 | number }} 次
                </span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-icon points-icon">
                <mat-icon>stars</mat-icon>
              </div>
              <div class="stat-info">
                <h3>{{ dashboardData?.summary?.available_points || 0 | number }}</h3>
                <p>可用积分</p>
                <span class="stat-change positive">可转换</span>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- 图表区域 -->
        <div class="charts-section">
          <!-- 曝光趋势图 -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>品牌曝光趋势</mat-card-title>
              <mat-card-subtitle>近30天曝光量变化</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <div style="display: block; height: 300px;">
                <canvas
                  baseChart
                  [data]="exposureChartData"
                  [options]="exposureChartOptions"
                  [type]="'line'"
                >
                </canvas>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- 积分获取趋势 -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>积分获取趋势</mat-card-title>
              <mat-card-subtitle>近30天积分累计情况</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <div style="display: block; height: 300px;">
                <canvas
                  baseChart
                  [data]="pointsChartData"
                  [options]="pointsChartOptions"
                  [type]="'line'"
                >
                </canvas>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- 赞助活动分布 -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>赞助活动状态分布</mat-card-title>
              <mat-card-subtitle>各类活动占比情况</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <div style="display: block; height: 300px;">
                <canvas
                  baseChart
                  [data]="statusPieData"
                  [options]="statusPieOptions"
                  [type]="'pie'"
                >
                </canvas>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- 曝光类型分析 -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>曝光类型分析</mat-card-title>
              <mat-card-subtitle>各渠道曝光效果对比</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <div style="display: block; height: 300px;">
                <canvas
                  baseChart
                  [data]="exposureTypeData"
                  [options]="exposureTypeOptions"
                  [type]="'bar'"
                >
                </canvas>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- 最近活动和分析摘要 -->
        <div class="activities-analysis-grid">
          <!-- 最近活动 -->
          <mat-card class="activities-card">
            <mat-card-header>
              <mat-card-title>最近活动</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="activity-list">
                <div
                  class="activity-item"
                  *ngFor="let activity of dashboardData?.recent_activities || []"
                >
                  <div class="activity-icon" [ngClass]="activity.type">
                    <mat-icon *ngIf="activity.type === 'exposure'">visibility</mat-icon>
                    <mat-icon *ngIf="activity.type === 'conversion'">swap_horiz</mat-icon>
                    <mat-icon *ngIf="activity.type === 'sponsorship'">business</mat-icon>
                  </div>
                  <div class="activity-content">
                    <p class="activity-message">{{ activity.message }}</p>
                    <p class="activity-time">{{ activity.time }}</p>
                  </div>
                </div>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- 分析摘要 -->
          <mat-card class="analysis-card">
            <mat-card-header>
              <mat-card-title>数据摘要</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="analysis-summary">
                <div class="summary-item">
                  <span class="summary-label">平均转化率</span>
                  <span class="summary-value"
                    >{{ analyticsData?.summary?.average_conversion_rate || 0 }}%</span
                  >
                </div>
                <div class="summary-item">
                  <span class="summary-label">积分ROI</span>
                  <span class="summary-value positive">3.2x</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">最佳表现活动</span>
                  <span class="summary-value">{{ topPerforming[0]?.name || '暂无数据' }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">预测月曝光</span>
                  <span class="summary-value">{{ predictedExposures | number }}</span>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .sponsorship-dashboard {
        padding: 24px;
        background-color: #f5f5f5;
        min-height: 100vh;
      }

      .dashboard-header {
        background: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 24px;
      }

      .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
      }

      .header-content h1 {
        margin: 0;
        color: #333;
        font-size: 2rem;
      }

      .header-actions {
        display: flex;
        gap: 12px;
      }

      .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 64px 24px;
        text-align: center;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
      }

      .stat-card {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition:
          transform 0.2s,
          box-shadow 0.2s;
        background: white;
      }

      .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      }

      .stat-card mat-card-content {
        display: flex;
        align-items: center;
        padding: 24px;
      }

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        flex-shrink: 0;
      }

      .sponsorship-icon {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
      }
      .money-icon {
        background: linear-gradient(135deg, #4caf50, #388e3c);
        color: white;
      }
      .exposure-icon {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
      }
      .points-icon {
        background: linear-gradient(135deg, #9c27b0, #7b1fa2);
        color: white;
      }

      .stat-icon mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
      }

      .stat-info h3 {
        margin: 0 0 8px 0;
        font-size: 2rem;
        font-weight: 600;
        color: #333;
      }

      .stat-info p {
        margin: 0 0 8px 0;
        color: #666;
        font-size: 1rem;
      }

      .stat-change {
        font-size: 0.9rem;
        font-weight: 500;
      }

      .stat-change.positive {
        color: #4caf50;
      }

      .charts-section {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
        gap: 24px;
        margin-bottom: 32px;
      }

      .chart-card {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        background: white;
      }

      .chart-card mat-card-header {
        padding: 16px 24px 0 24px;
      }

      .chart-card mat-card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
      }

      .chart-card mat-card-subtitle {
        color: #666;
      }

      .activities-analysis-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
      }

      .activities-card,
      .analysis-card {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        background: white;
      }

      .activity-list {
        max-height: 300px;
        overflow-y: auto;
      }

      .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        border-bottom: 1px solid #eee;
      }

      .activity-item:last-child {
        border-bottom: none;
      }

      .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        color: white;
      }

      .activity-icon.exposure {
        background: #2196f3;
      }
      .activity-icon.conversion {
        background: #4caf50;
      }
      .activity-icon.sponsorship {
        background: #ff9800;
      }

      .activity-content {
        flex: 1;
      }

      .activity-message {
        margin: 0 0 4px 0;
        color: #333;
        font-size: 0.95rem;
      }

      .activity-time {
        margin: 0;
        color: #888;
        font-size: 0.85rem;
      }

      .analysis-summary {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .summary-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #eee;
      }

      .summary-item:last-child {
        border-bottom: none;
      }

      .summary-label {
        color: #666;
        font-weight: 500;
      }

      .summary-value {
        font-weight: 600;
        color: #333;
      }

      .summary-value.positive {
        color: #4caf50;
      }

      @media (max-width: 768px) {
        .sponsorship-dashboard {
          padding: 16px;
        }

        .header-content {
          flex-direction: column;
          align-items: flex-start;
        }

        .stats-grid {
          grid-template-columns: 1fr;
        }

        .charts-section {
          grid-template-columns: 1fr;
        }

        .activities-analysis-grid {
          grid-template-columns: 1fr;
        }

        .stat-card mat-card-content {
          flex-direction: column;
          text-align: center;
          padding: 16px;
        }

        .stat-icon {
          margin-right: 0;
          margin-bottom: 16px;
        }
      }
    `,
  ],
})
export class SponsorshipDashboardComponent implements OnInit {
  @ViewChild(BaseChartDirective) chart?: BaseChartDirective;

  loading = true;
  dashboardData: DashboardData | null = null;
  analyticsData: SponsorshipAnalytics | null = null;
  topPerforming: Array<{
    id: number;
    name: string;
    exposures: number;
    points_earned: number;
    conversion_rate: number;
  }> = [];

  // 图表数据
  exposureChartData: ChartData<'line'> = {
    labels: [],
    datasets: [
      {
        data: [],
        label: '日曝光量',
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.4,
      },
    ],
  };

  pointsChartData: ChartData<'line'> = {
    labels: [],
    datasets: [
      {
        data: [],
        label: '累计积分',
        borderColor: '#4CAF50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        tension: 0.4,
      },
    ],
  };

  statusPieData: ChartData<'pie'> = {
    labels: ['活跃', '已完成', '已暂停', '已取消'],
    datasets: [
      {
        data: [0, 0, 0, 0],
        backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#F44336'],
      },
    ],
  };

  exposureTypeData: ChartData<'bar'> = {
    labels: ['横幅广告', '侧边栏', '弹窗', '邮件推广', '社交媒体', '内容植入'],
    datasets: [
      {
        data: [0, 0, 0, 0, 0, 0],
        label: '曝光次数',
        backgroundColor: '#2196F3',
      },
    ],
  };

  // 图表配置
  exposureChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
      x: {
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
    },
  };

  pointsChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
      x: {
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
    },
  };

  statusPieOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
      },
    },
  };

  exposureTypeOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
      x: {
        grid: {
          color: 'rgba(0,0,0,0.1)',
        },
      },
    },
  };

  // 计算属性
  get predictedExposures(): number {
    if (!this.analyticsData?.trends?.length) return 0;
    const recentAvg =
      this.analyticsData.trends.slice(-7).reduce((sum, item) => sum + (item.exposures ?? 0), 0) / 7;
    return Math.round(recentAvg * 30);
  }

  constructor(
    private sponsorshipService: SponsorshipDashboardService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;

    // 并行获取多个数据源
    Promise.all([
      this.sponsorshipService.getDashboardData(30).toPromise(),
      this.sponsorshipService.getAnalytics().toPromise(),
    ])
      .then(([dashboardData, analyticsData]) => {
        this.dashboardData = dashboardData ?? null;
        this.analyticsData = analyticsData ?? null;
        this.topPerforming = analyticsData?.top_performing ?? [];

        this.updateChartData();
        this.loading = false;
      })
      .catch(() => {
        // 使用模拟数据
        this.dashboardData = this.sponsorshipService['getMockDashboardData']();
        this.analyticsData = this.sponsorshipService['getMockAnalyticsData']();
        this.topPerforming = this.analyticsData.top_performing ?? [];
        this.updateChartData();
        this.loading = false;
      });
  }

  updateChartData(): void {
    // 更新曝光趋势图数据
    if (this.analyticsData?.trends) {
      this.exposureChartData.labels = this.analyticsData.trends.map((item) => item.date);
      this.exposureChartData.datasets[0].data = this.analyticsData.trends.map(
        (item) => item.exposures ?? 0
      );
    }

    // 更新积分趋势图数据
    if (this.analyticsData?.trends) {
      this.pointsChartData.labels = this.analyticsData.trends.map((item) => item.date);
      this.pointsChartData.datasets[0].data = this.analyticsData.trends.map(
        (item) => item.points ?? 0
      );
    }

    // 更新状态饼图数据（模拟数据）
    this.statusPieData.datasets[0].data = [8, 3, 1, 0]; // 活跃，完成，暂停，取消

    // 更新曝光类型数据（模拟数据）
    this.exposureTypeData.datasets[0].data = [50000, 30000, 15000, 25000, 35000, 40000];

    // 触发图表更新
    if (this.chart) {
      this.chart.update();
    }
  }

  refreshData(): void {
    this.loadData();
  }

  openCreateDialog(): void {
    const dialogRef = this.dialog.open(SponsorshipCreateDialogComponent, {
      width: '600px',
      maxWidth: '90vw',
      disableClose: false,
      data: {},
    });

    dialogRef.afterClosed().subscribe((result: CreateSponsorshipPayload | undefined) => {
      if (result) {
        // 用户点击确定，提交创建请求
        this.sponsorshipService.createSponsorship(result).subscribe({
          next: (sponsorship) => {
            this.snackBar.open(`✅ 赞助活动 "${sponsorship.name}" 创建成功！`, '关闭', {
              duration: 3000,
              horizontalPosition: 'center',
              verticalPosition: 'top',
            });
            // 刷新列表
            this.loadData();
          },
          error: (error: { message?: string }) => {
            this.snackBar.open('❌ 创建失败：' + (error.message ?? '请稍后重试'), '关闭', {
              duration: 5000,
              horizontalPosition: 'center',
              verticalPosition: 'top',
            });
          },
        });
      }
    });
  }
}

// ==================== 创建赞助活动对话框组件 ====================

@Component({
  selector: 'app-sponsorship-create-dialog',
  standalone: false,
  template: `
    <div class="create-dialog">
      <h2 mat-dialog-title>🏢 创建新的赞助活动</h2>

      <form [formGroup]="sponsorshipForm" (ngSubmit)="onSubmit()">
        <mat-dialog-content>
          <!-- 活动名称 -->
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>活动名称</mat-label>
            <input matInput formControlName="name" placeholder="例如：2026 年乡村教育支持计划" />
            <mat-error *ngIf="name?.hasError('required')">活动名称必填</mat-error>
            <mat-error *ngIf="name?.hasError('minlength')">至少 3 个字符</mat-error>
          </mat-form-field>

          <!-- 描述 -->
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>活动描述</mat-label>
            <textarea
              matInput
              formControlName="description"
              rows="4"
              placeholder="请描述活动的目标、受益群体和预期影响..."
            ></textarea>
            <mat-error *ngIf="description?.hasError('required')">活动描述必填</mat-error>
            <mat-hint align="end">{{ description?.value?.length || 0 }}/500</mat-hint>
          </mat-form-field>

          <!-- 赞助金额和货币 -->
          <div class="form-row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>赞助金额</mat-label>
              <input
                matInput
                type="number"
                formControlName="sponsor_amount"
                placeholder="10000"
                min="0"
                step="0.01"
              />
              <span matPrefix>¥&nbsp;</span>
              <mat-error *ngIf="sponsorAmount?.hasError('required')">金额必填</mat-error>
              <mat-error *ngIf="sponsorAmount?.hasError('min')">金额必须大于 0</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>货币</mat-label>
              <mat-select formControlName="currency">
                <mat-option value="CNY">人民币 (CNY)</mat-option>
                <mat-option value="USD">美元 (USD)</mat-option>
                <mat-option value="EUR">欧元 (EUR)</mat-option>
              </mat-select>
              <mat-error *ngIf="currency?.hasError('required')">请选择货币</mat-error>
            </mat-form-field>
          </div>

          <!-- 开始和结束日期 -->
          <div class="form-row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>开始日期</mat-label>
              <input matInput [matDatepicker]="startPicker" formControlName="start_date" />
              <mat-datepicker-toggle matSuffix [for]="startPicker"></mat-datepicker-toggle>
              <mat-datepicker #startPicker></mat-datepicker>
              <mat-error *ngIf="startDate?.hasError('required')">开始日期必填</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>结束日期</mat-label>
              <input matInput [matDatepicker]="endPicker" formControlName="end_date" />
              <mat-datepicker-toggle matSuffix [for]="endPicker"></mat-datepicker-toggle>
              <mat-datepicker #endPicker></mat-datepicker>
              <mat-error *ngIf="endDate?.hasError('required')">结束日期必填</mat-error>
              <mat-error *ngIf="endDate?.errors?.['endDateAfterStartDate']">
                结束日期必须在开始日期之后
              </mat-error>
            </mat-form-field>
          </div>

          <!-- 曝光类型 -->
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>品牌曝光类型</mat-label>
            <mat-select formControlName="exposure_types" multiple>
              <mat-option value="social_media">社交媒体</mat-option>
              <mat-option value="website">官方网站</mat-option>
              <mat-option value="mobile_app">移动应用</mat-option>
              <mat-option value="email">电子邮件</mat-option>
              <mat-option value="offline_event">线下活动</mat-option>
              <mat-option value="educational_content">教育内容</mat-option>
            </mat-select>
            <mat-error *ngIf="exposureTypes?.hasError('required')">
              请至少选择一种曝光类型
            </mat-error>
          </mat-form-field>

          <!-- 目标受众 -->
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>目标受众群体</mat-label>
            <mat-select formControlName="target_audience">
              <mat-option value="all">全体学生</mat-option>
              <mat-option value="primary">小学生</mat-option>
              <mat-option value="middle">初中生</mat-option>
              <mat-option value="high">高中生</mat-option>
              <mat-option value="rural">农村地区学生</mat-option>
              <mat-option value="special">特殊教育需求学生</mat-option>
            </mat-select>
            <mat-error *ngIf="targetAudience?.hasError('required')">请选择目标受众</mat-error>
          </mat-form-field>
        </mat-dialog-content>

        <mat-dialog-actions align="end">
          <button mat-button type="button" (click)="onCancel()">取消</button>
          <button
            mat-raised-button
            color="primary"
            type="submit"
            [disabled]="!sponsorshipForm.valid || submitting"
          >
            {{ submitting ? '创建中...' : '创建' }}
          </button>
        </mat-dialog-actions>
      </form>
    </div>
  `,
  styles: [
    `
      .create-dialog {
        padding: 16px;
      }

      h2[mat-dialog-title] {
        margin-bottom: 16px;
        color: #333;
      }

      .full-width {
        width: 100%;
        margin-bottom: 16px;
      }

      .form-row {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
      }

      .half-width {
        flex: 1;
      }

      mat-dialog-content {
        max-height: 70vh;
        overflow-y: auto;
      }

      mat-dialog-actions {
        padding-top: 16px;
        border-top: 1px solid #e0e0e0;
      }
    `,
  ],
})
export class SponsorshipCreateDialogComponent implements OnInit {
  sponsorshipForm!: FormGroup;
  submitting = false;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<SponsorshipCreateDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData
  ) {}

  ngOnInit(): void {
    /* eslint-disable @typescript-eslint/unbound-method */
    this.sponsorshipForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      sponsor_amount: [0, [Validators.required, Validators.min(0.01)]],
      currency: ['CNY', [Validators.required]],
      start_date: [null as Date | null, [Validators.required]],
      end_date: [null as Date | null, [Validators.required]],
      exposure_types: [[] as string[], [Validators.required, Validators.minLength(1)]],
      target_audience: ['all', [Validators.required]],
    } as const);
    /* eslint-enable @typescript-eslint/unbound-method */

    // 添加自定义验证器
    this.sponsorshipForm.addValidators([
      SponsorshipCreateDialogComponent.endDateAfterStartDateValidator,
    ]);
  }

  /**
   * 表单字段快捷访问
   */
  get name(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('name');
  }

  get description(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('description');
  }

  get sponsorAmount(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('sponsor_amount');
  }

  get currency(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('currency');
  }

  get startDate(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('start_date');
  }

  get endDate(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('end_date');
  }

  get exposureTypes(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('exposure_types');
  }

  get targetAudience(): ReturnType<typeof this.sponsorshipForm.get> {
    return this.sponsorshipForm.get('target_audience');
  }

  /**
   * 验证结束日期在开始日期之后
   */
  static endDateAfterStartDateValidator(
    this: void,
    form: AbstractControl
  ): Record<string, boolean> | null {
    const startDate = form.get('start_date')?.value as Date | null;
    const endDate = form.get('end_date')?.value as Date | null;

    if (!startDate || !endDate) {
      return null;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);

    return end > start ? null : { endDateAfterStartDate: true };
  }

  /**
   * 提交表单
   */
  onSubmit(): void {
    if (this.sponsorshipForm.valid && !this.submitting) {
      this.submitting = true;

      // 格式化表单数据为 API 所需格式
      const formValue = this.sponsorshipForm.getRawValue() as CreateSponsorshipFormData;
      const payload: CreateSponsorshipPayload = {
        name: formValue.name,
        description: formValue.description,
        sponsor_amount: formValue.sponsor_amount,
        currency: formValue.currency,
        start_date: new Date(formValue.start_date).toISOString(),
        end_date: new Date(formValue.end_date).toISOString(),
        status: 'active',
        exposure_types: formValue.exposure_types,
        target_audience: { segment: formValue.target_audience },
      };

      // 模拟 API 调用延迟（实际应该直接返回）
      setTimeout(() => {
        this.dialogRef.close(payload);
      }, 300);
    }
  }

  /**
   * 取消操作
   */
  onCancel(): void {
    this.dialogRef.close();
  }
}
