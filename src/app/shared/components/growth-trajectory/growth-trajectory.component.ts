/**
 * 成长轨迹展示组件
 *
 * PRD 6.6 关键页面线框 - "我的成长"
 * 展示：AI教师寄语、能力趋势、能力雷达图、学习热力图、学习里程碑时间轴、统计与兴趣演变
 */

import { animate, state, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NgxEchartsModule } from 'ngx-echarts';

import { GrowthTrajectory, LearningMilestone } from '../../../core/models/ai-teacher.models';

// ECharts 颜色令牌
const ECHARTS_COLORS = {
  textSecondary: '#64748b',
  divider: '#e2e8f0',
  primary: '#3b82f6',
  primaryFaded15: 'rgba(59, 130, 246, 0.15)',
  secondary: '#8b5cf6',
  secondaryFaded10: 'rgba(139, 92, 246, 0.1)',
} as const;

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
    MatTooltipModule,
    NgxEchartsModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('expandCollapse', [
      state('collapsed', style({ height: 0, opacity: 0, overflow: 'hidden' })),
      state('expanded', style({ height: '*', opacity: 1 })),
      transition('collapsed <=> expanded', animate('300ms ease-in-out')),
    ]),
  ],
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
              <line
                *ngFor="let level of [0, 25, 50, 75, 100]"
                x1="40"
                [attr.x2]="chartWidth - 10"
                [attr.y1]="getY(level)"
                [attr.y2]="getY(level)"
                [attr.stroke]="SVG_PALETTE.grid"
                stroke-width="1"
              />
              <text
                *ngFor="let level of [0, 25, 50, 75, 100]"
                x="35"
                [attr.y]="getY(level) + 4"
                text-anchor="end"
                font-size="11"
                [attr.fill]="SVG_PALETTE.axisLabel"
              >
                {{ level }}%
              </text>

              <!-- X轴月份标签 -->
              <text
                *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.x]="getX(i)"
                [attr.y]="chartHeight - 5"
                text-anchor="middle"
                font-size="11"
                [attr.fill]="SVG_PALETTE.axisLabel"
              >
                {{ point.date.slice(5) }}
              </text>

              <!-- 能力趋势线 - 编程思维 -->
              <polyline
                *ngIf="trajectory?.abilityTrend?.length"
                [attr.points]="getTrendLine('programmingThinking')"
                fill="none"
                [attr.stroke]="SVG_PALETTE.primary"
                stroke-width="2.5"
              />

              <!-- 能力趋势线 - STEM实验 -->
              <polyline
                *ngIf="trajectory?.abilityTrend?.length"
                [attr.points]="getTrendLine('stemExperiment')"
                fill="none"
                [attr.stroke]="SVG_PALETTE.success"
                stroke-width="2.5"
                stroke-dasharray="6,3"
              />

              <!-- 数据点 -->
              <circle
                *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.cx]="getX(i)"
                [attr.cy]="getY(point.programmingThinking)"
                r="4"
                [attr.fill]="SVG_PALETTE.primary"
              />
              <circle
                *ngFor="let point of trajectory?.abilityTrend ?? []; let i = index"
                [attr.cx]="getX(i)"
                [attr.cy]="getY(point.stemExperiment)"
                r="4"
                [attr.fill]="SVG_PALETTE.success"
              />

              <!-- 图例 -->
              <line x1="60" y1="15" x2="85" y2="15" [attr.stroke]="SVG_PALETTE.primary" stroke-width="2.5" />
              <text x="90" y="19" font-size="11" [attr.fill]="SVG_PALETTE.legendText">编程思维</text>
              <line
                x1="170"
                y1="15"
                x2="195"
                y2="15"
                [attr.stroke]="SVG_PALETTE.success"
                stroke-width="2.5"
                stroke-dasharray="6,3"
              />
              <text x="200" y="19" font-size="11" [attr.fill]="SVG_PALETTE.legendText">STEM实验</text>
            </svg>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 能力雷达图 + 学习热力图 双栏 -->
      <div class="charts-row">
        <!-- 能力雷达图 -->
        <mat-card class="radar-card">
          <mat-card-header>
            <mat-card-title>能力雷达</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div echarts [options]="radarOption" class="radar-chart"></div>
            <div class="radar-legend">
              <span class="legend-item current"><span class="dot current"></span> 当前</span>
              <span class="legend-item prev"><span class="dot prev"></span> 3个月前</span>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 学习热力图 -->
        <mat-card class="heatmap-card">
          <mat-card-header>
            <mat-card-title>学习热力图</mat-card-title>
            <span class="heatmap-rate">{{ heatmapStats.rate }}% 活跃</span>
          </mat-card-header>
          <mat-card-content>
            <div class="heatmap-grid">
              <div *ngFor="let week of heatmap; let w = index" class="heatmap-week">
                <div
                  *ngFor="let level of week; let d = index"
                  class="heatmap-cell"
                  [class]="getHeatmapClass(level)"
                  [matTooltip]="'第' + (w + 1) + '周 周' + ['日','一','二','三','四','五','六'][d] + ': ' + getHeatmapLabel(level)"
                ></div>
              </div>
            </div>
            <div class="heatmap-legend">
              <span class="heatmap-legend-label">少</span>
              <span class="heatmap-cell legend-l0"></span>
              <span class="heatmap-cell legend-l1"></span>
              <span class="heatmap-cell legend-l2"></span>
              <span class="heatmap-cell legend-l3"></span>
              <span class="heatmap-cell legend-l4"></span>
              <span class="heatmap-legend-label">多</span>
            </div>
            <div class="heatmap-stats">
              <div class="heatmap-stat">
                <div class="heatmap-stat-num">{{ heatmapStats.active }}</div>
                <div class="heatmap-stat-desc">活跃天数</div>
              </div>
              <div class="heatmap-stat">
                <div class="heatmap-stat-num intense">{{ heatmapIntenseWeeks }}</div>
                <div class="heatmap-stat-desc">密集学习周</div>
              </div>
              <div class="heatmap-stat">
                <div class="heatmap-stat-num rest">{{ heatmapStats.total - heatmapStats.active }}</div>
                <div class="heatmap-stat-desc">休息天数</div>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- 学习里程碑时间轴 -->
      <mat-card class="milestone-card">
        <mat-card-header>
          <mat-card-title>学习里程碑时间轴</mat-card-title>
          <span class="milestone-hint">点击展开详情</span>
        </mat-card-header>
        <mat-card-content>
          <div class="timeline">
            <ng-container *ngFor="let milestone of trajectory?.milestones ?? []; let last = last; let i = index">
              <div class="timeline-item" (click)="toggleMilestone(i)">
                <div class="timeline-dot">
                  <mat-icon>{{ getMilestoneIcon(milestone) }}</mat-icon>
                </div>
                <div *ngIf="!last" class="timeline-line"></div>
                <div class="timeline-content">
                  <span class="timeline-date">{{ milestone.achievedAt | date: 'yyyy-MM-dd' }}</span>
                  <span class="timeline-title">{{ milestone.title }}</span>
                  <span class="timeline-desc">{{ milestone.description }}</span>
                  <mat-icon class="expand-icon" [class.expanded]="expandedMilestone === i">expand_more</mat-icon>
                </div>
              </div>
              <!-- 展开详情 -->
              <div class="timeline-detail" [@expandCollapse]="expandedMilestone === i ? 'expanded' : 'collapsed'">
                <div class="timeline-detail-inner">
                  <p class="timeline-detail-desc">{{ milestone.description }}</p>
                  <div class="timeline-detail-reward" *ngIf="milestone.reward">
                    🎁 {{ milestone.reward }}
                  </div>
                </div>
              </div>
            </ng-container>
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

      <!-- 同龄对比（P1-5） -->
      <mat-card class="peer-card" *ngIf="trajectory?.peerComparison">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>group</mat-icon>
            同龄对比
          </mat-card-title>
          <span class="peer-badge">{{ trajectory!.peerComparison!.beatRate }}</span>
        </mat-card-header>
        <mat-card-content>
          <div class="peer-dimensions">
            <div *ngFor="let dim of peerDimensions" class="peer-row">
              <span class="peer-label">{{ dim.label }}</span>
              <div class="peer-bars">
                <div class="peer-bar-wrapper">
                  <div
                    class="peer-bar peer-bar-user"
                    [style.width.%]="getPeerBarWidth(dim.key, 'user')"
                    [matTooltip]="'你: ' + getUserValue(dim.key)"
                  ></div>
                </div>
                <div class="peer-bar-wrapper peer-bar-peer-wrapper">
                  <div
                    class="peer-bar peer-bar-peer"
                    [style.width.%]="getPeerBarWidth(dim.key, 'peer')"
                    [matTooltip]="'同龄平均: ' + getPeerValue(dim.key)"
                  ></div>
                </div>
              </div>
              <div class="peer-values">
                <span class="peer-user-val">{{ getUserValue(dim.key) }}</span>
                <span class="peer-peer-val">{{ getPeerValue(dim.key) }}</span>
              </div>
            </div>
          </div>
          <div class="peer-rank">
            <mat-icon>emoji_events</mat-icon>
            <span
              >综合排名：<strong>{{ trajectory!.peerComparison!.percentileRank }}%</strong></span
            >
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
  styles: [
    `
      .growth-container {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 16px;
      }
      .ai-message-card {
      }
      .ai-avatar {
        font-size: 40px;
        color: var(--matux-color-primary, #3b82f6);
        background: linear-gradient(135deg, var(--matux-color-info-50, #dbeafe), var(--matux-color-info-100, #bfdbfe));
        border-radius: 50%;
        padding: 8px;
      }
      .ai-message-text {
        font-size: 14px;
        line-height: 1.8;
        color: var(--matux-color-text-primary, #334155);
        padding: 12px;
        background: var(--matux-color-background, #f8fafc);
        border-radius: 12px;
        border-left: 4px solid var(--matux-color-primary, #3b82f6);
      }
      .period-select {
        width: 120px;
        margin-left: auto;
      }

      .trend-card {
      }
      .trend-chart {
        display: flex;
        justify-content: center;
      }
      .trend-svg {
        width: 100%;
        max-width: 700px;
        height: auto;
      }

      /* 能力雷达图 + 热力图 双栏 */
      .charts-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      .radar-card {
      }
      .radar-chart {
        width: 100%;
        height: 280px;
      }
      .radar-legend {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-top: 8px;
      }
      .legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: var(--matux-color-text-secondary, #64748b);
      }
      .legend-item .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }
      .legend-item.current .dot {
        background: #3b82f6;
      }
      .legend-item.prev .dot {
        background: #cbd5e1;
      }

      /* 学习热力图 */
      .heatmap-card {
      }
      .heatmap-rate {
        margin-left: auto;
        font-size: 12px;
        color: #22c55e;
        font-weight: 600;
      }
      .heatmap-grid {
        display: flex;
        gap: 2px;
        overflow-x: auto;
        padding-bottom: 4px;
      }
      .heatmap-week {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .heatmap-cell {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        transition: transform 0.15s ease;
      }
      .heatmap-cell:hover {
        transform: scale(1.3);
      }
      .heatmap-cell.level-0 { background: #f1f5f9; }
      .heatmap-cell.level-1 { background: #bbf7d0; }
      .heatmap-cell.level-2 { background: #4ade80; }
      .heatmap-cell.level-3 { background: #22c55e; }
      .heatmap-cell.level-4 { background: #16a34a; }
      .heatmap-cell.legend-l0 { background: #f1f5f9; }
      .heatmap-cell.legend-l1 { background: #bbf7d0; }
      .heatmap-cell.legend-l2 { background: #4ade80; }
      .heatmap-cell.legend-l3 { background: #22c55e; }
      .heatmap-cell.legend-l4 { background: #16a34a; }
      .heatmap-legend {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 8px;
        font-size: 10px;
        color: #94a3b8;
      }
      .heatmap-legend .heatmap-cell {
        width: 10px;
        height: 10px;
      }
      .heatmap-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 12px;
      }
      .heatmap-stat {
        text-align: center;
        padding: 8px;
        background: var(--matux-color-background, #f8fafc);
        border-radius: 8px;
      }
      .heatmap-stat-num {
        font-size: 18px;
        font-weight: 700;
        color: var(--matux-color-text-primary, #0f172a);
      }
      .heatmap-stat-num.intense { color: #22c55e; }
      .heatmap-stat-num.rest { color: #f97316; }
      .heatmap-stat-desc {
        font-size: 10px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }

      .milestone-card {
      }
      .milestone-hint {
        margin-left: auto;
        font-size: 12px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }
      .timeline {
        position: relative;
        padding-left: 40px;
      }
      .timeline-item {
        position: relative;
        padding-bottom: 24px;
        display: flex;
        align-items: flex-start;
        cursor: pointer;
        transition: background 0.15s ease;
        border-radius: 8px;
        padding: 8px 8px 24px 8px;
        margin: 0 -8px;
      }
      .timeline-item:hover {
        background: var(--matux-color-background, #f8fafc);
      }
      .timeline-dot {
        position: absolute;
        left: -40px;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--matux-color-primary, #3b82f6);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        z-index: 1;
      }
      .future-dot {
        background: var(--matux-color-primary, #3b82f6);
      }
      .timeline-line {
        position: absolute;
        left: -25px;
        top: 32px;
        bottom: 0;
        width: 2px;
        background: var(--matux-color-divider, #e2e8f0);
      }
      .timeline-content {
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding-left: 8px;
        flex: 1;
      }
      .expand-icon {
        position: absolute;
        right: 8px;
        top: 8px;
        font-size: 18px;
        color: var(--matux-color-text-disabled, #94a3b8);
        transition: transform 0.3s ease;
      }
      .expand-icon.expanded {
        transform: rotate(180deg);
      }
      .timeline-detail {
        margin-left: 40px;
        margin-bottom: 8px;
      }
      .timeline-detail-inner {
        background: var(--matux-color-background, #f8fafc);
        border-radius: 12px;
        padding: 12px 16px;
        border-left: 4px solid var(--matux-color-primary, #3b82f6);
      }
      .timeline-detail-desc {
        font-size: 13px;
        color: var(--matux-color-text-secondary, #64748b);
        margin: 0 0 8px;
        line-height: 1.6;
      }
      .timeline-detail-reward {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #fff7ed;
        color: #ea580c;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
      }
      .timeline-date {
        font-size: 12px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }
      .timeline-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--matux-color-text-primary, #0f172a);
      }
      .timeline-desc {
        font-size: 13px;
        color: var(--matux-color-text-secondary, #64748b);
      }

      .bottom-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      .stats-card {
      }
      .stat-row {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
      }
      .stat-entry {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 80px;
      }
      .stat-num {
        font-size: 24px;
        font-weight: 700;
        color: var(--matux-color-primary, #3b82f6);
      }
      .stat-unit {
        font-size: 12px;
        color: var(--matux-color-text-secondary, #64748b);
      }
      .stat-desc {
        font-size: 12px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }

      .interest-card {
      }
      .interest-period {
        margin-bottom: 12px;
      }
      .interest-period-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--matux-color-text-secondary, #64748b);
        margin-bottom: 4px;
        display: block;
      }
      .interest-bar-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
      }
      .interest-name {
        font-size: 13px;
        color: var(--matux-color-text-primary, #334155);
        width: 60px;
      }
      .interest-bar-bg {
        flex: 1;
        height: 8px;
        background: var(--matux-color-background, #f1f5f9);
        border-radius: 4px;
        overflow: hidden;
      }
      .interest-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--matux-color-primary-light, #60a5fa), var(--matux-color-primary, #3b82f6));
        border-radius: 4px;
      }
      .interest-pct {
        font-size: 12px;
        color: #64748b;
        width: 35px;
      }
      .interest-trend {
        font-size: 13px;
        color: #3b82f6;
        font-weight: 500;
        margin-top: 8px;
      }

      /* 同龄对比 */
      .peer-card {
      }
      .peer-card mat-card-header {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .peer-card mat-card-title {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 16px;
      }
      .peer-badge {
        margin-left: auto;
        padding: 4px 12px;
        border-radius: 12px;
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        color: #2563eb;
        font-size: 13px;
        font-weight: 600;
      }
      .peer-dimensions {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .peer-row {
        display: grid;
        grid-template-columns: 80px 1fr 60px;
        gap: 12px;
        align-items: center;
      }
      .peer-label {
        font-size: 13px;
        color: #475569;
        font-weight: 500;
      }
      .peer-bars {
        display: flex;
        flex-direction: column;
        gap: 3px;
      }
      .peer-bar-wrapper {
        height: 8px;
        background: #f1f5f9;
        border-radius: 4px;
        overflow: hidden;
      }
      .peer-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
        min-width: 2px;
      }
      .peer-bar-user {
        background: linear-gradient(90deg, var(--matux-color-primary, #3b82f6), #2563eb);
      }
      .peer-bar-peer {
        background: #cbd5e1;
      }
      .peer-bar-peer-wrapper {
        background: transparent;
      }
      .peer-values {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 3px;
      }
      .peer-user-val {
        font-size: 12px;
        font-weight: 600;
        color: #3b82f6;
      }
      .peer-peer-val {
        font-size: 11px;
        color: #94a3b8;
      }
      .peer-rank {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        color: #475569;
      }
      .peer-rank mat-icon {
        color: #f59e0b;
      }

      @media (max-width: 768px) {
        .bottom-row {
          grid-template-columns: 1fr;
        }
        .charts-row {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class GrowthTrajectoryComponent {
  @Input() trajectory: GrowthTrajectory | null = null;

  chartWidth = 700;
  chartHeight = 250;
  padding = { top: 30, right: 10, bottom: 30, left: 50 };

  // 能力雷达图配置
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  radarOption: any = {};

  // 学习热力图
  heatmap: number[][] = [];
  heatmapStats = { active: 0, total: 0, rate: 0 };
  heatmapIntenseWeeks = 0;

  // 里程碑展开状态
  expandedMilestone: number | null = null;

  /**
   * SVG 调色板常量（SVG 属性无法直接使用 CSS var，集中在此维护便于主题调整）
   * 与设计令牌对应：primary = --matux-color-primary，success = --stem-primary，
   * text-secondary = --matux-color-text-secondary，divider = --matux-color-divider
   */
  readonly SVG_PALETTE = {
    grid: '#f0f0f0',
    axisLabel: '#94a3b8',
    primary: '#3b82f6',
    success: '#22c55e',
    legendText: '#334155',
  } as const;

  constructor() {
    this.generateHeatmap();
    this.buildRadarChart();
  }

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

  // ==================== 同龄对比辅助方法 ====================

  get peerDimensions(): { key: string; label: string }[] {
    const pc = this.trajectory?.peerComparison;
    if (!pc) return [];
    return Object.entries(pc.dimensionLabels).map(([key, label]) => ({ key, label }));
  }

  getUserValue(key: string): number {
    const val = this.trajectory?.peerComparison?.userAverages[key];
    return val ?? 0;
  }

  getPeerValue(key: string): number {
    const val = this.trajectory?.peerComparison?.peerAverages[key];
    return val ?? 0;
  }

  getPeerBarWidth(key: string, type: 'user' | 'peer'): number {
    const userVal = this.getUserValue(key);
    const peerVal = this.getPeerValue(key);
    const maxVal = Math.max(userVal, peerVal, 100);
    const val = type === 'user' ? userVal : peerVal;
    return Math.max(2, (val / maxVal) * 100);
  }

  // ==================== 能力雷达图 ====================

  private buildRadarChart(): void {
    // 模拟数据：与原型一致
    const radarData = [
      { name: '编程', current: 85, prev: 55 },
      { name: '逻辑', current: 72, prev: 48 },
      { name: '硬件', current: 66, prev: 30 },
      { name: '创意', current: 78, prev: 60 },
      { name: '协作', current: 60, prev: 45 },
      { name: '表达', current: 55, prev: 40 },
    ];

    this.radarOption = {
      radar: {
        indicator: radarData.map(d => ({ name: d.name, max: 100 })),
        shape: 'circle',
        splitNumber: 4,
        name: {
          textStyle: {
            color: ECHARTS_COLORS.textSecondary,
            fontSize: 12,
          },
        },
        splitLine: {
          lineStyle: {
            color: ECHARTS_COLORS.divider,
          },
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(59, 130, 246, 0.02)', 'rgba(59, 130, 246, 0.04)'],
          },
        },
        axisLine: {
          lineStyle: {
            color: ECHARTS_COLORS.divider,
          },
        },
      },
      series: [
        {
          type: 'radar',
          symbol: 'circle',
          symbolSize: 6,
          data: [
            {
              value: radarData.map(d => d.current),
              name: '当前',
              areaStyle: {
                color: ECHARTS_COLORS.primaryFaded15,
              },
              lineStyle: {
                color: ECHARTS_COLORS.primary,
                width: 2,
              },
              itemStyle: {
                color: ECHARTS_COLORS.primary,
              },
            },
            {
              value: radarData.map(d => d.prev),
              name: '3个月前',
              areaStyle: {
                color: ECHARTS_COLORS.secondaryFaded10,
              },
              lineStyle: {
                color: '#cbd5e1',
                width: 1.5,
                type: 'dashed',
              },
              itemStyle: {
                color: '#cbd5e1',
              },
            },
          ],
        },
      ],
      tooltip: {
        trigger: 'item',
      },
      color: [ECHARTS_COLORS.primary, '#cbd5e1'],
    };
  }

  // ==================== 学习热力图 ====================

  private generateHeatmap(): void {
    const weeks = 12;
    const days = 7;
    const heatmap: number[][] = [];
    let activeCount = 0;
    let intenseWeeks = 0;

    for (let w = 0; w < weeks; w++) {
      const week: number[] = [];
      let weekHasIntense = false;
      for (let d = 0; d < days; d++) {
        const weekendBoost = (d === 0 || d === 6) ? 0.3 : 0;
        const recentBoost = w / weeks * 0.4;
        const base = 0.2 + weekendBoost + recentBoost;
        const random = Math.random();
        const level = random < base * 0.3 ? 0 :
                      random < base * 0.6 ? 1 :
                      random < base * 0.85 ? 2 :
                      random < base ? 3 : 4;
        if (level > 0) activeCount++;
        if (level === 4) weekHasIntense = true;
        week.push(level);
      }
      if (weekHasIntense) intenseWeeks++;
      heatmap.push(week);
    }

    this.heatmap = heatmap;
    this.heatmapStats = {
      active: activeCount,
      total: weeks * days,
      rate: Math.round((activeCount / (weeks * days)) * 100),
    };
    this.heatmapIntenseWeeks = intenseWeeks;
  }

  getHeatmapClass(level: number): string {
    return `level-${level}`;
  }

  getHeatmapLabel(level: number): string {
    const labels = ['无', '少', '中', '多', '密集'];
    return labels[level] ?? '无';
  }

  // ==================== 里程碑展开 ====================

  toggleMilestone(index: number): void {
    this.expandedMilestone = this.expandedMilestone === index ? null : index;
  }
}
