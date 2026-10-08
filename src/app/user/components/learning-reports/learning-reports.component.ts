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
import { PdfPrintService } from '../../../shared/services/pdf-print.service';
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
    private cdr: ChangeDetectorRef,
    private pdfPrintService: PdfPrintService
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

  /**
   * 导出当前报告为 PDF：
   * 1. 调用后端获取 Blob
   * 2. 后端不可用时回退到浏览器打印（用户可另存为 PDF）
   * 【P3-1 修复】点击「导出 PDF」如果有可见反馈（即使是提示 / 也避免沉默失败）
   */
  exportAsPdf(): void {
    const report = this.selectedReport;
    if (!report) {
      // 【P3-1 修复】原逻辑在没有选中报告时静默 return，导致用户点击后无任何反馈。
      //   现在给出明确提示，并自动 fallback 到打印整个报告页（用户可下载为 PDF）。
      this.snackBar.open(
        '当前未选中报告，已为你打开打印对话框（可“另存为 PDF”）',
        '关闭',
        { duration: 3000 }
      );
      this.printReport();
      return;
    }
    this.exporting = true;
    this.cdr.markForCheck();

    this.pdfPrintService
      .downloadPdfBlob(this.learningReportsService.exportReport(report.id, 'pdf'), {
        filename: `学习报告_${report.period}`,
        fallbackToPrint: true,
        successMessage: `✅ PDF 导出成功：学习报告_${report.period}.pdf`,
        errorMessage: '后端 PDF 导出失败，已自动切换到浏览器打印（可“另存为 PDF”）',
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (ok) => {
          this.exporting = false;
          this.cdr.markForCheck();
          // ok=false 表示后端失败，服务内部已触发回退打印，这里仅记录状态
          if (!ok) {
            // eslint-disable-next-line no-console
            console.warn('[P4-F] PDF 导出后端失败，已回退到打印');
          }
        },
        error: () => {
          // 防御性：服务内部已处理错误
          this.exporting = false;
          this.cdr.markForCheck();
        },
      });
  }

  /** 打印当前报告（用户可在打印对话框中“另存为 PDF”） */
  printReport(): void {
    if (!this.selectedReport) {
      // 无选中报告时仍可打印当前页面（也许是“报告未加载”状态下的页面）
      this.snackBar.open('未选择报告，将打印当前页面', '关闭', { duration: 2000 });
    }
    this.pdfPrintService.print({
      preparingMessage: '正在打开打印对话框…请选择“另存为 PDF”',
      successMessage: '打印任务已结束',
    });
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
