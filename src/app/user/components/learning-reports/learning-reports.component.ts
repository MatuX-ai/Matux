/**
 * 学习报告页面（学生版）
 *
 * PRD 6.6 关键页面线框 - "学习报告"
 * 展示：学习总览、课程成绩、学习行为统计、能力评估、AI推荐
 * 支持：PDF导出
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { StudentLearningProfile } from '../../../core/models/ai-teacher.models';
import type { User } from '../../../core/models/auth.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { LearningReport, LearningReportsService } from '../../services/learning-reports.service';

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
    MatTooltipModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './learning-reports.component.html',
  styleUrls: ['./learning-reports.component.scss'],
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
    private cdr: ChangeDetectorRef
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
    this.learningReportsService
      .getReports({})
      .pipe(takeUntil(this.destroy$))
      .subscribe({
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
    const report = this.selectedReport;
    if (!report) return;
    this.exporting = true;

    this.learningReportsService
      .exportReport(report.id, 'pdf')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `学习报告_${report.period}.pdf`;
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
