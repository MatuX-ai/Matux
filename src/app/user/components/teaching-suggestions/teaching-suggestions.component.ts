/**
 * 智能教学建议组件
 *
 * PRD F-08-AI.5：智能教学建议
 * 展示 DiagnosisService 的诊断结果：
 * - 总体学习健康评分
 * - 多维度得分（知识掌握、技能均衡、学习投入、学习效率、独立学习）
 * - 教学建议列表（按严重程度排序）
 * - 一键重新诊断
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import {
  DiagnosisDimension,
  DiagnosisReport,
  DiagnosisService,
  HealthRating,
} from '../../../core/services/diagnosis.service';

@Component({
  selector: 'app-teaching-suggestions',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatProgressBarModule],
  template: `
    <div class="suggestions-container">
      <div class="page-header">
        <h1 class="page-title">智能教学建议</h1>
        <button
          mat-raised-button
          color="primary"
          (click)="runDiagnosis()"
          [disabled]="isDiagnosing"
        >
          <mat-icon>refresh</mat-icon>
          {{ isDiagnosing ? '诊断中...' : '重新诊断' }}
        </button>
      </div>

      <!-- 加载状态 -->
      <div *ngIf="isDiagnosing" class="loading-section">
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
        <p>正在分析学习数据...</p>
      </div>

      <!-- 空状态 -->
      <div *ngIf="!report && !isDiagnosing" class="empty-section">
        <mat-icon class="empty-icon">psychology</mat-icon>
        <h3>暂无诊断数据</h3>
        <p>点击上方"重新诊断"按钮，AI 将分析你的学习状况并给出建议</p>
        <button mat-raised-button color="primary" (click)="runDiagnosis()">
          <mat-icon>play_arrow</mat-icon>
          开始诊断
        </button>
      </div>

      <!-- 诊断报告 -->
      <ng-container *ngIf="report && !isDiagnosing">
        <!-- 总体健康评分 -->
        <mat-card class="health-card" [class]="'health-' + healthRating">
          <mat-card-content class="health-content">
            <div class="health-score-section">
              <div
                class="health-score-ring"
                [style.--score-color]="healthColor"
                [style.--score]="report.overallHealth"
              >
                <span class="health-score-value">{{ report.overallHealth }}</span>
                <span class="health-score-label">健康分</span>
              </div>
              <div class="health-info">
                <h2>学习健康评级：{{ healthLabel }}</h2>
                <p>诊断时间：{{ report.timestamp | date: 'yyyy-MM-dd HH:mm' }}</p>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 多维度评分 -->
        <mat-card class="dimensions-card">
          <mat-card-header>
            <mat-card-title>多维度评估</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="dimensions-grid">
              <div *ngFor="let dim of dimensionList" class="dimension-item">
                <div class="dimension-header">
                  <span class="dimension-label">{{ dim.label }}</span>
                  <span class="dimension-score" [style.color]="getScoreColor(dim.score)">{{
                    dim.score
                  }}</span>
                </div>
                <mat-progress-bar
                  mode="determinate"
                  [value]="dim.score"
                  [class]="'progress-' + getScoreLevel(dim.score)"
                >
                </mat-progress-bar>
                <span class="dimension-desc">{{ dim.description }}</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 紧急问题 -->
        <mat-card *ngIf="report.criticalIssues.length > 0" class="critical-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="critical-icon">warning</mat-icon>
            <mat-card-title>需关注的问题（{{ report.criticalIssues.length }}）</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngFor="let issue of report.criticalIssues" class="suggestion-item critical">
              <div class="suggestion-header">
                <mat-icon class="severity-icon">priority_high</mat-icon>
                <strong>{{ issue.title }}</strong>
              </div>
              <p class="suggestion-desc">{{ issue.description }}</p>
              <div class="suggestion-action">
                <mat-icon>lightbulb</mat-icon>
                <span>{{ issue.suggestedAction }}</span>
              </div>
              <div class="suggestion-tags" *ngIf="issue.relatedKnowledgePoints.length">
                <span class="tag" *ngFor="let kp of issue.relatedKnowledgePoints">{{ kp }}</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 教学建议列表 -->
        <mat-card class="suggestions-card">
          <mat-card-header>
            <mat-card-title>教学建议（{{ report.suggestions.length }}）</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div
              *ngFor="let item of report.suggestions"
              class="suggestion-item"
              [class]="item.severity"
            >
              <div class="suggestion-header">
                <mat-icon class="severity-icon">
                  {{
                    item.severity === 'critical'
                      ? 'error'
                      : item.severity === 'warning'
                        ? 'warning'
                        : 'info'
                  }}
                </mat-icon>
                <strong>{{ item.title }}</strong>
                <span class="severity-badge" [class]="'badge-' + item.severity">
                  {{
                    item.severity === 'critical'
                      ? '紧急'
                      : item.severity === 'warning'
                        ? '关注'
                        : '提示'
                  }}
                </span>
              </div>
              <p class="suggestion-desc">{{ item.description }}</p>
              <div class="suggestion-action">
                <mat-icon>lightbulb</mat-icon>
                <span>{{ item.suggestedAction }}</span>
              </div>
              <div class="suggestion-tags" *ngIf="item.relatedKnowledgePoints.length">
                <span class="tag" *ngFor="let kp of item.relatedKnowledgePoints">{{ kp }}</span>
              </div>
            </div>
            <div *ngIf="report.suggestions.length === 0" class="no-suggestions">
              <mat-icon>check_circle</mat-icon>
              <span>暂无建议，学习状态良好！</span>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 趋势分析 -->
        <mat-card
          *ngIf="report.trends.improving.length > 0 || report.trends.declining.length > 0"
          class="trends-card"
        >
          <mat-card-header>
            <mat-card-title>趋势分析</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngIf="report.trends.improving.length" class="trend-row improving">
              <mat-icon class="trend-icon">trending_up</mat-icon>
              <span>进步趋势：{{ report.trends.improving.join('、') }}</span>
            </div>
            <div *ngIf="report.trends.declining.length" class="trend-row declining">
              <mat-icon class="trend-icon">trending_down</mat-icon>
              <span>下降趋势：{{ report.trends.declining.join('、') }}</span>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 诊断历史 -->
        <mat-card *ngIf="history.length > 1" class="history-card">
          <mat-card-header>
            <mat-card-title>诊断历史</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngFor="let h of history.slice(-5).reverse()" class="history-item">
              <div class="history-score" [style.color]="getScoreColor(h.overallHealth)">
                {{ h.overallHealth }}
              </div>
              <span class="history-date">{{ h.timestamp | date: 'MM/dd HH:mm' }}</span>
              <mat-progress-bar mode="determinate" [value]="h.overallHealth"></mat-progress-bar>
            </div>
          </mat-card-content>
        </mat-card>
      </ng-container>
    </div>
  `,
  styles: [
    `
      .suggestions-container {
        padding: 24px;
        max-width: 960px;
        margin: 0 auto;
      }
      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
      }
      .page-title {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: var(--color-text-primary);
      }

      /* 加载 */
      .loading-section {
        text-align: center;
        padding: 48px 16px;
        color: var(--color-text-secondary);
      }
      .empty-section {
        text-align: center;
        padding: 64px 16px;
      }
      .empty-icon {
        font-size: 64px;
        width: 64px;
        height: 64px;
        color: var(--color-text-disabled);
        margin-bottom: 16px;
      }
      .empty-section h3 {
        margin: 0 0 8px;
        color: var(--color-text-primary);
      }
      .empty-section p {
        color: var(--color-text-secondary);
        margin: 0 0 24px;
      }

      /* 健康评分卡片 */
      .health-card {
        margin-bottom: 16px;
        border-radius: 16px;
      }
      .health-card.health-excellent {
        border-left: 4px solid var(--color-success);
      }
      .health-card.health-good {
        border-left: 4px solid var(--color-accent);
      }
      .health-card.health-fair {
        border-left: 4px solid var(--color-warning);
      }
      .health-card.health-needs_attention {
        border-left: 4px solid #f97316;
      }
      .health-card.health-critical {
        border-left: 4px solid var(--color-error);
      }

      .health-content {
        padding: 24px;
      }
      .health-score-section {
        display: flex;
        align-items: center;
        gap: 24px;
      }
      .health-score-ring {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: conic-gradient(
          var(--score-color) calc(var(--score) * 1%),
          var(--color-divider) 0
        );
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        flex-shrink: 0;
      }
      .health-score-ring::before {
        content: '';
        position: absolute;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: white;
      }
      .health-score-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--score-color);
        z-index: 1;
      }
      .health-score-label {
        font-size: 11px;
        color: var(--color-text-secondary);
        z-index: 1;
      }
      .health-info h2 {
        margin: 0 0 4px;
        font-size: 18px;
      }
      .health-info p {
        margin: 0;
        color: var(--color-text-secondary);
        font-size: 13px;
      }

      /* 维度评分 */
      .dimensions-card {
        margin-bottom: 16px;
        border-radius: 16px;
      }
      .dimensions-grid {
        display: grid;
        gap: 16px;
      }
      .dimension-item {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .dimension-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .dimension-label {
        font-size: 14px;
        font-weight: 500;
        color: var(--color-text-primary);
      }
      .dimension-score {
        font-size: 16px;
        font-weight: 600;
      }
      .dimension-desc {
        font-size: 12px;
        color: var(--color-text-disabled);
      }
      ::ng-deep .progress-high .mdc-linear-progress__bar-inner {
        background-color: var(--color-success);
      }
      ::ng-deep .progress-medium .mdc-linear-progress__bar-inner {
        background-color: var(--color-warning);
      }
      ::ng-deep .progress-low .mdc-linear-progress__bar-inner {
        background-color: var(--color-error);
      }

      /* 紧急问题 */
      .critical-card {
        margin-bottom: 16px;
        border-radius: 16px;
        border: 1px solid var(--color-error-light, #fecaca);
        background: #fef2f2;
      }
      .critical-icon {
        color: var(--color-error);
      }

      /* 建议列表 */
      .suggestions-card {
        margin-bottom: 16px;
        border-radius: 16px;
      }
      .suggestion-item {
        padding: 16px;
        border-bottom: 1px solid var(--color-divider);
      }
      .suggestion-item:last-child {
        border-bottom: none;
      }
      .suggestion-item.critical {
        background: #fef2f2;
        border-radius: 8px;
        margin: 8px 0;
      }
      .suggestion-item.warning {
        background: #fffbeb;
        border-radius: 8px;
        margin: 8px 0;
      }
      .suggestion-item.info {
        border-radius: 0;
      }

      .suggestion-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }
      .severity-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }
      .critical .severity-icon {
        color: var(--color-error);
      }
      .warning .severity-icon {
        color: var(--color-warning);
      }
      .info .severity-icon {
        color: var(--color-accent);
      }

      .severity-badge {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        margin-left: auto;
      }
      .badge-critical {
        background: #fecaca;
        color: #dc2626;
      }
      .badge-warning {
        background: #fde68a;
        color: #d97706;
      }
      .badge-info {
        background: #dbeafe;
        color: #2563eb;
      }

      .suggestion-desc {
        margin: 0 0 8px 28px;
        color: #475569;
        font-size: 13px;
        line-height: 1.5;
      }
      .suggestion-action {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: 0 0 8px 28px;
        font-size: 13px;
        color: #2563eb;
      }
      .suggestion-action mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }
      .suggestion-tags {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-left: 28px;
      }
      .tag {
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 12px;
        background: #f1f5f9;
        color: #475569;
      }

      .no-suggestions {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 24px;
        color: #22c55e;
        justify-content: center;
      }

      /* 趋势 */
      .trends-card {
        margin-bottom: 16px;
        border-radius: 16px;
      }
      .trend-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        font-size: 14px;
      }
      .trend-row.improving .trend-icon {
        color: #22c55e;
      }
      .trend-row.declining .trend-icon {
        color: #ef4444;
      }

      /* 历史 */
      .history-card {
        margin-bottom: 16px;
        border-radius: 16px;
      }
      .history-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
      }
      .history-score {
        font-size: 18px;
        font-weight: 700;
        min-width: 36px;
      }
      .history-date {
        font-size: 12px;
        color: #94a3b8;
        min-width: 80px;
      }
      .history-item mat-progress-bar {
        flex: 1;
      }
    `,
  ],
})
export class TeachingSuggestionsComponent implements OnInit, OnDestroy {
  report: DiagnosisReport | null = null;
  history: DiagnosisReport[] = [];
  isDiagnosing = false;

  dimensionList: { key: DiagnosisDimension; label: string; score: number; description: string }[] =
    [];

  private userId = '';
  private destroy$ = new Subject<void>();

  constructor(
    private diagnosisService: DiagnosisService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    this.userId = user?.id ?? 'default_user';

    // 订阅诊断报告
    this.diagnosisService.report$.pipe(takeUntil(this.destroy$)).subscribe((r) => {
      if (r) {
        this.report = r;
        this.history = this.diagnosisService.getHistory();
        this.buildDimensionList(r);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get healthRating(): HealthRating {
    if (!this.report) return 'fair';
    return this.diagnosisService.getHealthRating(this.report.overallHealth);
  }

  get healthLabel(): string {
    return this.diagnosisService.getHealthRatingLabel(this.healthRating);
  }

  get healthColor(): string {
    return this.diagnosisService.getHealthRatingColor(this.healthRating);
  }

  runDiagnosis(): void {
    this.isDiagnosing = true;
    this.diagnosisService.runFullDiagnosis(this.userId).subscribe({
      complete: () => {
        this.isDiagnosing = false;
      },
      error: () => {
        this.isDiagnosing = false;
      },
    });
  }

  getScoreColor(score: number): string {
    if (score >= 70) return '#22c55e';
    if (score >= 45) return '#f59e0b';
    return '#ef4444';
  }

  getScoreLevel(score: number): string {
    if (score >= 70) return 'high';
    if (score >= 45) return 'medium';
    return 'low';
  }

  private buildDimensionList(report: DiagnosisReport): void {
    const meta: { key: DiagnosisDimension; label: string; description: string }[] = [
      { key: 'knowledge', label: '知识掌握', description: '基础知识点掌握程度' },
      { key: 'skill', label: '技能均衡', description: '各项技能发展均衡性' },
      { key: 'engagement', label: '学习投入', description: '学习专注度和持续性' },
      { key: 'efficiency', label: '学习效率', description: '单位时间学习产出' },
      { key: 'independence', label: '独立学习', description: '自主学习能力评估' },
    ];
    this.dimensionList = meta.map((m) => ({
      key: m.key,
      label: m.label,
      score: report.dimensionScores[m.key] ?? 50,
      description: m.description,
    }));
  }
}
