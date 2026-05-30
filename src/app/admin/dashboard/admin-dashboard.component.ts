import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';

import { DashboardOverview } from './models/dashboard.models';
import { DashboardService } from './services/dashboard.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: false,
  template: `
    <div class="admin-dashboard">
      <!-- 页面标题 -->
      <div class="dashboard-header">
        <h1>管理仪表板</h1>
        <p>欢迎回来！这里是您的系统概览</p>
      </div>

      <!-- 加载状态 -->
      <div *ngIf="isLoading" class="loading-container">
        <mat-spinner diameter="40"></mat-spinner>
        <p>正在加载仪表板数据...</p>
      </div>

      <!-- 主要内容 -->
      <div *ngIf="!isLoading" class="dashboard-content">
        <div *ngIf="dashboardData$ | async as data; else loadingData">
          <!-- 统计卡片网格 -->
          <div class="stats-grid">
            <mat-card class="stat-card">
              <mat-card-content>
                <div class="stat-icon users-icon">
                  <mat-icon>people</mat-icon>
                </div>
                <div class="stat-info">
                  <h3>{{ data.statistics.totalUsers }}</h3>
                  <p>总用户数</p>
                  <span class="stat-change positive"
                    >+{{ data.userGrowthTrend.trendPercentage | number: '1.0-1' }}%</span
                  >
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="stat-card">
              <mat-card-content>
                <div class="stat-icon licenses-icon">
                  <mat-icon>vpn_key</mat-icon>
                </div>
                <div class="stat-info">
                  <h3>{{ data.statistics.activeLicenses }}/{{ data.statistics.totalLicenses }}</h3>
                  <p>活跃许可证</p>
                  <span class="stat-change"
                    >{{
                      (data.statistics.activeLicenses / data.statistics.totalLicenses) * 100
                        | number: '1.0-1'
                    }}% 激活率</span
                  >
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="stat-card">
              <mat-card-content>
                <div class="stat-icon subscriptions-icon">
                  <mat-icon>credit_card</mat-icon>
                </div>
                <div class="stat-info">
                  <h3>
                    {{ data.statistics.activeSubscriptions }}/{{
                      data.statistics.totalSubscriptions
                    }}
                  </h3>
                  <p>活跃订阅</p>
                  <span class="stat-change positive"
                    >+{{ data.subscriptionPlanDistribution.professional }} 专业版</span
                  >
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="stat-card">
              <mat-card-content>
                <div class="stat-icon revenue-icon">
                  <mat-icon>attach_money</mat-icon>
                </div>
                <div class="stat-info">
                  <h3>¥{{ data.statistics.monthlyRevenue | number }}</h3>
                  <p>本月收入</p>
                  <span class="stat-change {{ data.revenueTrend.trendDirection }}">
                    {{ data.revenueTrend.trendDirection === 'up' ? '+' : ''
                    }}{{ data.revenueTrend.trendPercentage | number: '1.0-1' }}%
                  </span>
                </div>
              </mat-card-content>
            </mat-card>
          </div>

          <!-- 分布数据展示 -->
          <div class="distribution-section">
            <mat-card class="distribution-card">
              <mat-card-header>
                <mat-card-title>许可证状态分布</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="distribution-grid">
                  <div class="distribution-item">
                    <span class="distribution-label">活跃</span>
                    <span class="distribution-value">{{
                      data.licenseStatusDistribution.active
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill active"
                        [style.width.%]="
                          (data.licenseStatusDistribution.active / data.statistics.totalLicenses) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                  <div class="distribution-item">
                    <span class="distribution-label">已过期</span>
                    <span class="distribution-value">{{
                      data.licenseStatusDistribution.expired
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill expired"
                        [style.width.%]="
                          (data.licenseStatusDistribution.expired / data.statistics.totalLicenses) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                  <div class="distribution-item">
                    <span class="distribution-label">已撤销</span>
                    <span class="distribution-value">{{
                      data.licenseStatusDistribution.revoked
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill revoked"
                        [style.width.%]="
                          (data.licenseStatusDistribution.revoked / data.statistics.totalLicenses) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="distribution-card">
              <mat-card-header>
                <mat-card-title>订阅计划分布</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="distribution-grid">
                  <div class="distribution-item">
                    <span class="distribution-label">基础版</span>
                    <span class="distribution-value">{{
                      data.subscriptionPlanDistribution.basic
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill basic"
                        [style.width.%]="
                          (data.subscriptionPlanDistribution.basic /
                            data.statistics.totalSubscriptions) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                  <div class="distribution-item">
                    <span class="distribution-label">专业版</span>
                    <span class="distribution-value">{{
                      data.subscriptionPlanDistribution.professional
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill professional"
                        [style.width.%]="
                          (data.subscriptionPlanDistribution.professional /
                            data.statistics.totalSubscriptions) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                  <div class="distribution-item">
                    <span class="distribution-label">企业版</span>
                    <span class="distribution-value">{{
                      data.subscriptionPlanDistribution.enterprise
                    }}</span>
                    <div class="distribution-bar">
                      <div
                        class="bar-fill enterprise"
                        [style.width.%]="
                          (data.subscriptionPlanDistribution.enterprise /
                            data.statistics.totalSubscriptions) *
                          100
                        "
                      ></div>
                    </div>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </div>
      </div>

      <!-- 加载数据模板 -->
      <ng-template #loadingData>
        <div class="loading-data">
          <mat-spinner diameter="40"></mat-spinner>
          <p>正在加载数据...</p>
        </div>
      </ng-template>

      <!-- 错误状态 -->
      <div *ngIf="error" class="error-container">
        <mat-icon color="warn">error</mat-icon>
        <p>加载数据时出现错误</p>
        <button mat-raised-button color="primary" (click)="loadData()">重试</button>
      </div>
    </div>
  `,
  styles: [
    `
      .admin-dashboard {
        padding: 24px;
        max-width: 1400px;
        margin: 0 auto;
      }

      .dashboard-header {
        margin-bottom: 32px;
      }

      .dashboard-header h1 {
        margin: 0 0 8px 0;
        color: #2196f3;
        font-size: 2.5rem;
      }

      .dashboard-header p {
        margin: 0;
        color: #666;
        font-size: 1.1rem;
      }

      .loading-container,
      .error-container,
      .loading-data {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        text-align: center;
      }

      .loading-container p,
      .error-container p,
      .loading-data p {
        margin: 16px 0 0 0;
        color: #666;
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
          transform 0.2s ease,
          box-shadow 0.2s ease;
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

      .users-icon {
        background: linear-gradient(135deg, #2196f3, #1976d2);
        color: white;
      }

      .licenses-icon {
        background: linear-gradient(135deg, #4caf50, #388e3c);
        color: white;
      }

      .subscriptions-icon {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
      }

      .revenue-icon {
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

      .stat-change.down {
        color: #f44336;
      }

      .stat-change.stable {
        color: #ff9800;
      }

      .distribution-section {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 24px;
        margin-top: 32px;
      }

      .distribution-card {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .distribution-card mat-card-header {
        padding: 16px 24px 0 24px;
      }

      .distribution-card mat-card-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
      }

      .distribution-grid {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }

      .distribution-item {
        display: flex;
        align-items: center;
        gap: 16px;
      }

      .distribution-label {
        min-width: 80px;
        font-weight: 500;
        color: #333;
      }

      .distribution-value {
        min-width: 40px;
        font-weight: 600;
        color: #2196f3;
      }

      .distribution-bar {
        flex: 1;
        height: 8px;
        background-color: #eee;
        border-radius: 4px;
        overflow: hidden;
      }

      .bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
      }

      .bar-fill.active {
        background-color: #4caf50;
      }
      .bar-fill.expired {
        background-color: #ff9800;
      }
      .bar-fill.revoked {
        background-color: #f44336;
      }
      .bar-fill.basic {
        background-color: #2196f3;
      }
      .bar-fill.professional {
        background-color: #9c27b0;
      }
      .bar-fill.enterprise {
        background-color: #ff5722;
      }

      @media (max-width: 768px) {
        .admin-dashboard {
          padding: 16px;
        }

        .dashboard-header h1 {
          font-size: 2rem;
        }

        .stats-grid {
          grid-template-columns: 1fr;
        }

        .distribution-section {
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
export class AdminDashboardComponent implements OnInit {
  isLoading = true;
  error: string | null = null;
  dashboardData$!: Observable<DashboardOverview>;

  constructor(private dashboardService: DashboardService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.isLoading = true;
    this.error = null;

    this.dashboardData$ = this.dashboardService.getDashboardOverview();

    // 订阅数据
    this.dashboardData$.subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err: unknown) => {
        this.isLoading = false;
        this.error = (err as Error)?.message || '加载失败';
      },
    });
  }
}
