/**
 * 成长轨迹展示组件
 *
 * PRD 6.6 关键页面线框 - "我的成长"
 * 展示：AI教师寄语、能力趋势、学习里程碑时间轴、统计与兴趣演变
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';

import { GrowthTrajectory, LearningMilestone } from '../../../core/models/ai-teacher.models';

@Component({
  selector: 'app-growth-trajectory',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="growth-container">
      <!-- AI 教师寄语 -->
      <mat-card class="ai-message-card">
        <mat-card-header>
          <mat-icon mat-card-avatar class="ai-avatar">smart_toy</mat-icon>
          <mat-card-title>AI 教师寄语（{{ currentMonth }}）</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <p class="ai-message-text">{{ trajectory?.aiMonthlyMessage }}</p>
        </mat-card-content>
      </mat-card>

      <!-- 能力趋势 -->
      <mat-card class="trend-card">
        <mat-card-header>
          <mat-card-title>能力趋势</mat-card-title>
          <mat-form-field class="period-select" appearance="outline">
            <mat-select [value]="6">
              <mat-option [value]="3">3个月</mat-option>
              <mat-option [value]="6">6个月</mat-option>
              <mat-option [value]="12">12个月</mat-option>
            </mat-select>
          </mat-form-field>
        </mat-card-header>
        <mat-card-content>
          <div class="trend-chart">
            <svg [attr.viewBox]="'0 0 ' + chartWidth + ' ' + chartHeight" class="trend-svg">
              <!-- 网格线和Y轴标签 -->
              <line *ngFor="let level of [0, 25, 50, 75, 100]"
                x1="40" [attr.x2]="chartWidth - 10"
                [attr.y1]="getY(level)" [attr.y2]="getY(level)"
                stroke="#f0f0f0" stroke-width="1"/>
              <text *ngFor="let level of [0, 25, 50, 75, 100]"
                x="35" [attr.y]="getY(level) + 4"
                text-anchor="end" font-size="11" fill="#94a3b8">{{ level }}%</text>

              <!-- X轴月份标签 -->
              <text *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.x]="getX(i)" [attr.y]="chartHeight - 5"
                text-anchor="middle" font-size="11" fill="#94a3b8">
                {{ point.date.slice(5) }}
              </text>

              <!-- 能力趋势线 - 编程思维 -->
              <polyline *ngIf="trajectory?.abilityTrend?.length"
                [attr.points]="getTrendLine('programmingThinking')"
                fill="none" stroke="#3b82f6" stroke-width="2.5"/>

              <!-- 能力趋势线 - STEM实验 -->
              <polyline *ngIf="trajectory?.abilityTrend?.length"
                [attr.points]="getTrendLine('stemExperiment')"
                fill="none" stroke="#22c55e" stroke-width="2.5" stroke-dasharray="6,3"/>

              <!-- 数据点 -->
              <circle *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.cx]="getX(i)" [attr.cy]="getY(point.programmingThinking)"
                r="4" fill="#3b82f6"/>
              <circle *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.cx]="getX(i)" [attr.cy]="getY(point.stemExperiment)"
                r="4" fill="#22c55e"/>

              <!-- 图例 -->
              <line x1="60" y1="15" x2="85" y2="15" stroke="#3b82f6" stroke-width="2.5"/>
              <text x="90" y="19" font-size="11" fill="#334155">编程思维</text>
              <line x1="170" y1="15" x2="195" y2="15" stroke="#22c55e" stroke-width="2.5" stroke-dasharray="6,3"/>
              <text x="200" y="19" font-size="11" fill="#334155">STEM实验</text>
            </svg>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 学习里程碑时间轴 -->
      <mat-card class="milestone-card">
        <mat-card-header>
          <mat-card-title>学习里程碑时间轴</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="timeline">
            <div *ngFor="let milestone of trajectory?.milestones ?? []; let last = last"
              class="timeline-item">
              <div class="timeline-dot">
                <mat-icon>{{ getMilestoneIcon(milestone) }}</mat-icon>
              </div>
              <div *ngIf="!last" class="timeline-line"></div>
              <div class="timeline-content">
                <span class="timeline-date">{{ milestone.achievedAt | date:'yyyy-MM-dd' }}</span>
                <span class="timeline-title">{{ milestone.title }}</span>
                <span class="timeline-desc">{{ milestone.description }}</span>
              </div>
            </div>
            <!-- 未来预测节点 -->
            <div class="timeline-item future">
              <div class="timeline-dot future-dot">
                <mat-icon>auto_awesome</mat-icon>
              </div>
              <div class="timeline-content">
                <span class="timeline-date">未来</span>
                <span class="timeline-title">🔮 AI 预测：下个月达到 Python 中阶水平</span>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 统计与兴趣演变 -->
      <div class="bottom-row">
        <mat-card class="stats-card">
          <mat-card-header>
            <mat-card-title>学习统计</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="stat-row" *ngIf="trajectory?.statistics">
              <div class="stat-entry">
                <span class="stat-num">{{ trajectory!.statistics.totalStudyHours }}</span>
                <span class="stat-unit">小时</span>
                <span class="stat-desc">总学时</span>
              </div>
              <div class="stat-entry">
                <span class="stat-num">{{ trajectory!.statistics.completedCourses }}</span>
                <span class="stat-unit">门</span>
                <span class="stat-desc">完成课程</span>
              </div>
              <div class="stat-entry">
                <span class="stat-num">{{ trajectory!.statistics.completedProjects }}</span>
                <span class="stat-unit">个</span>
                <span class="stat-desc">完成项目</span>
              </div>
              <div class="stat-entry">
                <span class="stat-num">{{ trajectory!.statistics.totalQuestions }}</span>
                <span class="stat-unit">次</span>
                <span class="stat-desc">提问次数</span>
              </div>
              <div class="stat-entry">
                <span class="stat-num">{{ questionQualityLabel }}</span>
                <span class="stat-desc">提问质量</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="interest-card">
          <mat-card-header>
            <mat-card-title>兴趣演变</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngFor="let evo of trajectory?.interestEvolution ?? []" class="interest-period">
              <span class="interest-period-label">{{ evo.period }}</span>
              <div class="interest-bars">
                <div *ngFor="let interest of evo.interests" class="interest-bar-item">
                  <span class="interest-name">{{ interest.name }}</span>
                  <div class="interest-bar-bg">
                    <div class="interest-bar-fill" [style.width.%]="interest.percentage"></div>
                  </div>
                  <span class="interest-pct">{{ interest.percentage }}%</span>
                </div>
              </div>
            </div>
            <p *ngIf="trajectory?.interestEvolution?.length" class="interest-trend">
              趋势：从游戏开发向机器人/硬件偏移
            </p>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .growth-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 16px;
    }
    .ai-message-card { }
    .ai-avatar {
      font-size: 40px; color: #3b82f6;
      background: linear-gradient(135deg, #dbeafe, #ede9fe);
      border-radius: 50%; padding: 8px;
    }
    .ai-message-text {
      font-size: 14px; line-height: 1.8; color: #334155;
      padding: 12px; background: #f8fafc; border-radius: 12px;
      border-left: 4px solid #8b5cf6;
    }
    .period-select { width: 120px; margin-left: auto; }

    .trend-card { }
    .trend-chart { display: flex; justify-content: center; }
    .trend-svg { width: 100%; max-width: 700px; height: auto; }

    .milestone-card { }
    .timeline { position: relative; padding-left: 40px; }
    .timeline-item {
      position: relative; padding-bottom: 24px;
      display: flex; align-items: flex-start;
    }
    .timeline-dot {
      position: absolute; left: -40px; width: 32px; height: 32px;
      border-radius: 50%; background: #3b82f6; color: white;
      display: flex; align-items: center; justify-content: center;
      font-size: 16px; z-index: 1;
    }
    .future-dot { background: #8b5cf6; }
    .timeline-line {
      position: absolute; left: -25px; top: 32px; bottom: 0;
      width: 2px; background: #e2e8f0;
    }
    .timeline-content {
      display: flex; flex-direction: column; gap: 2px; padding-left: 8px;
    }
    .timeline-date { font-size: 12px; color: #94a3b8; }
    .timeline-title { font-size: 14px; font-weight: 600; color: #0f172a; }
    .timeline-desc { font-size: 13px; color: #64748b; }

    .bottom-row {
      display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
    }
    .stats-card { }
    .stat-row { display: flex; flex-wrap: wrap; gap: 16px; }
    .stat-entry {
      display: flex; flex-direction: column; align-items: center; min-width: 80px;
    }
    .stat-num { font-size: 24px; font-weight: 700; color: #3b82f6; }
    .stat-unit { font-size: 12px; color: #64748b; }
    .stat-desc { font-size: 12px; color: #94a3b8; }

    .interest-card { }
    .interest-period { margin-bottom: 12px; }
    .interest-period-label {
      font-size: 13px; font-weight: 500; color: #64748b; margin-bottom: 4px; display: block;
    }
    .interest-bar-item {
      display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
    }
    .interest-name { font-size: 13px; color: #334155; width: 60px; }
    .interest-bar-bg {
      flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden;
    }
    .interest-bar-fill {
      height: 100%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); border-radius: 4px;
    }
    .interest-pct { font-size: 12px; color: #64748b; width: 35px; }
    .interest-trend {
      font-size: 13px; color: #8b5cf6; font-weight: 500; margin-top: 8px;
    }

    @media (max-width: 768px) {
      .bottom-row { grid-template-columns: 1fr; }
    }
  `],
})
export class GrowthTrajectoryComponent {
  @Input() trajectory: GrowthTrajectory | null = null;

  chartWidth = 700;
  chartHeight = 250;
  padding = { top: 30, right: 10, bottom: 30, left: 50 };

  get currentMonth(): string {
    const now = new Date();
    return `${now.getFullYear()}年${now.getMonth() + 1}月`;
  }

  get questionQualityLabel(): string {
    const trend = this.trajectory?.statistics?.questionQualityTrend;
    if (trend === 'improving') return '中→高 ↑';
    if (trend === 'declining') return '下降 ↓';
    return '稳定 →';
  }

  getY(value: number): number {
    const plotH = this.chartHeight - this.padding.top - this.padding.bottom;
    return this.padding.top + plotH * (1 - value / 100);
  }

  getX(index: number): number {
    const data = this.trajectory?.abilityTrend ?? [];
    if (data.length <= 1) return this.chartWidth / 2;
    const plotW = this.chartWidth - this.padding.left - this.padding.right;
    return this.padding.left + (plotW * index) / (data.length - 1);
  }

  getTrendLine(field: 'programmingThinking' | 'stemExperiment'): string {
    const data = this.trajectory?.abilityTrend ?? [];
    return data.map((p, i) => `${this.getX(i)},${this.getY(p[field])}`).join(' ');
  }

  getMilestoneIcon(milestone: LearningMilestone): string {
    const iconMap: Record<string, string> = {
      first_blockly: 'school',
      python_intro: 'code',
      first_independent_project: 'construction',
      first_debug: 'build',
      streak_30_days: 'local_fire_department',
      breakthrough: 'bolt',
      project_master: 'rocket_launch',
    };
    return iconMap[milestone.type] ?? 'star';
  }
}
