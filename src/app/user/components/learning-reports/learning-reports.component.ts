/**
 * 学习报告页面（学生版）
 *
 * PRD 6.6 关键页面线框 - "学习报告"
 * 展示：学习总览、课程成绩、学习行为统计、能力评估、AI推荐
 * 支持：PDF导出
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { LearningReportsService, LearningReport } from '../../services/learning-reports.service';
import type { StudentLearningProfile } from '../../../core/models/ai-teacher.models';
import type { User } from '../../../core/models/auth.models';

@Component({
  selector: 'app-learning-reports',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTabsModule,
    MatDividerModule,
    MatSnackBarModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="reports-container">
      <div class="page-header">
        <h1 class="page-title">学习报告</h1>
        <div class="header-actions">
          <span class="report-period" *ngIf="selectedReport">
            {{ selectedReport.period }}
          </span>
          <button mat-raised-button color="primary" class="export-btn"
            (click)="exportAsPdf()" [disabled]="exporting">
            <mat-icon>picture_as_pdf</mat-icon>
            {{ exporting ? '导出中...' : '导出PDF' }}
          </button>
          <button mat-stroked-button (click)="printReport()" matTooltip="打印当前报告">
            <mat-icon>print</mat-icon>
          </button>
        </div>
      </div>

      <!-- 报告切换 Tabs -->
      <mat-tab-group [(selectedIndex)]="activeTab" (selectedIndexChange)="onTabChange($event)" class="report-tabs">
        <mat-tab *ngFor="let report of reports" [label]="report.reportType === 'monthly' ? '月度报告' : '周报'">
        </mat-tab>
      </mat-tab-group>

      <ng-container *ngIf="selectedReport">
        <!-- 学习总览 -->
        <div class="overview-grid">
          <mat-card class="overview-card">
            <mat-icon class="overview-icon clock-icon">access_time</mat-icon>
            <div class="overview-content">
              <span class="overview-value">{{ selectedReport.totalStudyTime }}</span>
              <span class="overview-label">总学习时长</span>
            </div>
          </mat-card>
          <mat-card class="overview-card">
            <mat-icon class="overview-icon book-icon">menu_book</mat-icon>
            <div class="overview-content">
              <span class="overview-value">{{ selectedReport.completedCourses }}</span>
              <span class="overview-label">完成课程</span>
            </div>
          </mat-card>
          <mat-card class="overview-card">
            <mat-icon class="overview-icon score-icon">emoji_events</mat-icon>
            <div class="overview-content">
              <span class="overview-value">{{ selectedReport.averageScore }}</span>
              <span class="overview-label">平均分</span>
            </div>
          </mat-card>
          <mat-card class="overview-card">
            <mat-icon class="overview-icon streak-icon">local_fire_department</mat-icon>
            <div class="overview-content">
              <span class="overview-value">{{ selectedReport.learningStreak }}</span>
              <span class="overview-label">连续学习天数</span>
            </div>
          </mat-card>
        </div>

        <!-- 课程成绩 -->
        <mat-card class="section-card">
          <mat-card-header>
            <mat-icon mat-card-avatar>school</mat-icon>
            <mat-card-title>课程成绩</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngFor="let grade of selectedReport.courseGrades" class="grade-row">
              <div class="grade-info">
                <span class="grade-name">{{ grade.courseName }}</span>
                <span class="grade-status" [class.completed]="grade.completionStatus === 'completed'">
                  {{ grade.completionStatus === 'completed' ? '✅ 已完成' : '📖 学习中' }}
                </span>
              </div>
              <div class="grade-score-row">
                <mat-progress-bar
                  mode="determinate"
                  [value]="grade.score"
                  [color]="getScoreColor(grade.score)"
                ></mat-progress-bar>
                <span class="grade-score" [class.high]="grade.score >= 90"
                  [class.medium]="grade.score >= 75 && grade.score < 90">
                  {{ grade.score }}分
                </span>
              </div>
              <p class="grade-comment" *ngIf="grade.teacherComment">
                💬 {{ grade.teacherComment }}
              </p>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 学习行为统计 -->
        <mat-card class="section-card" *ngIf="selectedReport.behaviorStats">
          <mat-card-header>
            <mat-icon mat-card-avatar>insights</mat-icon>
            <mat-card-title>学习行为</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-value">{{ formatHours(selectedReport.behaviorStats!.totalLearningMinutes) }}</span>
                <span class="stat-label">总学习时间</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ selectedReport.behaviorStats!.avgDailyLearningMinutes }}分钟</span>
                <span class="stat-label">日均学习</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ selectedReport.behaviorStats!.learningDays }}天</span>
                <span class="stat-label">学习天数</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ selectedReport.behaviorStats!.homeworkSubmitted }}</span>
                <span class="stat-label">提交作业</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ selectedReport.behaviorStats!.questionsAsked }}</span>
                <span class="stat-label">提问次数</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ selectedReport.behaviorStats!.discussionsParticipated }}</span>
                <span class="stat-label">参与讨论</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 能力评估 -->
        <mat-card class="section-card" *ngIf="selectedReport.competencyAssessments?.length">
          <mat-card-header>
            <mat-icon mat-card-avatar>psychology</mat-icon>
            <mat-card-title>能力评估</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div *ngFor="let comp of selectedReport.competencyAssessments!" class="competency-row">
              <div class="competency-header">
                <span class="competency-name">{{ comp.dimension }}</span>
                <span class="competency-level" [class]="'level-' + comp.score">
                  {{ comp.level }}（{{ comp.score }}分）
                </span>
              </div>
              <mat-progress-bar mode="determinate" [value]="comp.score" color="primary"></mat-progress-bar>
              <p class="competency-desc" *ngIf="comp.description">{{ comp.description }}</p>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- AI 推荐 -->
        <mat-card class="section-card ai-section" *ngIf="selectedReport.aiRecommendations?.length">
          <mat-card-header>
            <mat-icon mat-card-avatar class="ai-avatar">auto_awesome</mat-icon>
            <mat-card-title>🤖 AI 教师建议</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <ul class="recommendation-list">
              <li *ngFor="let rec of selectedReport.aiRecommendations">{{ rec }}</li>
            </ul>
          </mat-card-content>
        </mat-card>
      </ng-container>

      <!-- 加载中 -->
      <div class="loading-state" *ngIf="!reports.length && !error">
        <mat-icon>hourglass_empty</mat-icon>
        <p>正在加载学习报告...</p>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" *ngIf="!reports.length && error">
        <mat-icon>description</mat-icon>
        <h3>暂无学习报告</h3>
        <p>继续学习，系统将在每月初自动生成你的学习报告</p>
      </div>
    </div>
  `,
  styles: [`
    .reports-container {
      max-width: 1000px;
      margin: 0 auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }
    .page-title {
      font-size: 28px;
      font-weight: 700;
      color: var(--color-text-primary);
      margin: 0;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .report-period {
      font-size: 14px;
      color: var(--color-text-secondary);
      background: var(--color-background);
      padding: 6px 14px;
      border-radius: 20px;
    }
    .export-btn {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .report-tabs {
      margin-bottom: 4px;
    }

    /* 学习总览 */
    .overview-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }
    .overview-card {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px;
    }
    .overview-icon {
      font-size: 36px;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
    }
    .clock-icon { background: var(--color-selected); color: var(--color-accent); }
    .book-icon { background: #dcfce7; color: var(--color-success); }
    .score-icon { background: #fef3c7; color: var(--color-warning); }
    .streak-icon { background: #fce7f3; color: var(--color-info); }
    .overview-content {
      display: flex;
      flex-direction: column;
    }
    .overview-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--color-text-primary);
      line-height: 1.2;
    }
    .overview-label {
      font-size: 13px;
      color: var(--color-text-secondary);
    }

    /* 课程成绩 */
    .section-card {
      border-radius: 16px;
    }
    .grade-row {
      padding: 12px 0;
      border-bottom: 1px solid var(--color-divider);
    }
    .grade-row:last-child { border-bottom: none; }
    .grade-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .grade-name {
      font-size: 15px;
      font-weight: 600;
      color: var(--color-text-primary);
    }
    .grade-status {
      font-size: 12px;
      color: var(--color-text-secondary);
    }
    .grade-status.completed { color: var(--color-success); }
    .grade-score-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .grade-score-row mat-progress-bar { flex: 1; height: 8px; }
    .grade-score {
      font-size: 14px;
      font-weight: 700;
      min-width: 48px;
      text-align: right;
      color: var(--color-text-secondary);
    }
    .grade-score.high { color: var(--color-success); }
    .grade-score.medium { color: var(--color-warning); }
    .grade-comment {
      font-size: 13px;
      color: var(--color-text-secondary);
      margin: 8px 0 0 0;
      padding: 8px 12px;
      background: var(--color-background);
      border-radius: 8px;
    }

    /* 统计 */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .stat-item {
      text-align: center;
      padding: 12px;
      background: #f8fafc;
      border-radius: 12px;
    }
    .stat-value {
      display: block;
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
    }
    .stat-label {
      font-size: 12px;
      color: #64748b;
    }

    /* 能力评估 */
    .competency-row {
      padding: 12px 0;
      border-bottom: 1px solid #f1f5f9;
    }
    .competency-row:last-child { border-bottom: none; }
    .competency-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .competency-name {
      font-size: 14px;
      font-weight: 600;
      color: #0f172a;
    }
    .competency-level {
      font-size: 13px;
      font-weight: 500;
    }
    .competency-desc {
      font-size: 13px;
      color: #64748b;
      margin: 8px 0 0 0;
    }

    /* AI 推荐 */
    .ai-section {
      border: 1px solid #ede9fe;
      background: linear-gradient(135deg, #faf5ff, #f5f3ff);
    }
    .ai-avatar {
      color: #8b5cf6;
    }
    .recommendation-list {
      margin: 0;
      padding-left: 20px;
    }
    .recommendation-list li {
      font-size: 14px;
      line-height: 1.8;
      color: #334155;
    }

    /* 状态 */
    .loading-state, .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 80px 24px;
      color: #94a3b8;
      text-align: center;
    }
    .loading-state mat-icon, .empty-state mat-icon {
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
      margin: 0;
    }

    @media (max-width: 768px) {
      .overview-grid {
        grid-template-columns: repeat(2, 1fr);
      }
      .stats-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    /* ===== 打印样式 ===== */
    @media print {
      .export-btn, .report-tabs, .header-actions button:not(.action-keep) {
        display: none !important;
      }
      .reports-container {
        padding: 0;
        max-width: none;
      }
      .page-title { font-size: 22px; color: var(--color-text-primary); }
      .overview-card { break-inside: avoid; }
      .section-card { break-inside: avoid; box-shadow: none !important; border: 1px solid #e2e8f0; }
      .grade-row, .competency-row { break-inside: avoid; }
      .ai-section { background: none !important; border: 1px solid #e2e8f0 !important; }
      @page { margin: 1.5cm; }
    }
  `],
})
export class LearningReportsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  reports: LearningReport[] = [];
  selectedReport: LearningReport | null = null;
  activeTab = 0;
  profile: StudentLearningProfile | null = null;
  exporting = false;
  error = false;

  currentUser: User | null = null;

  constructor(
    private learningReportsService: LearningReportsService,
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
    });
    this.aiTeacherService.profile$.pipe(takeUntil(this.destroy$)).subscribe((p) => {
      this.profile = p;
    });
    this.loadReports();
  }

  private loadReports(): void {
    this.error = false;
    // 学生视角：不传childId，获取所有可用报告
    this.learningReportsService.getReports({}).pipe(
      takeUntil(this.destroy$),
    ).subscribe({
      next: (response) => {
        this.reports = response.data;
        this.selectedReport = this.reports[0] ?? null;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = true;
        this.cdr.markForCheck();
      },
    });
  }

  onTabChange(index: number): void {
    this.selectedReport = this.reports[index] ?? null;
  }

  exportAsPdf(): void {
    if (!this.selectedReport) return;
    this.exporting = true;

    this.learningReportsService.exportReport(this.selectedReport.id, 'pdf').pipe(
      takeUntil(this.destroy$),
    ).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `学习报告_${this.selectedReport!.period}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.exporting = false;
        this.snackBar.open('✅ PDF导出成功', '关闭', { duration: 3000 });
        this.cdr.markForCheck();
      },
      error: () => {
        // 服务端导出失败，回退到客户端打印
        this.exporting = false;
        this.printReport();
        this.cdr.markForCheck();
      },
    });
  }

  /** 客户端打印/保存PDF */
  printReport(): void {
    if (!this.selectedReport) return;
    this.snackBar.open('正在打开打印对话框...', '关闭', { duration: 2000 });
    window.print();
  }

  getScoreColor(score: number): string {
    if (score >= 90) return 'primary';
    if (score >= 75) return 'accent';
    return 'warn';
  }

  formatHours(minutes: number): string {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m > 0 ? `${h}小时${m}分` : `${h}小时`;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
