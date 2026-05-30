/**
 * 学习报告组件（家长）
 * 功能：
 * - 显示孩子的学习报告列表
 * - 查看报告详情
 * - 学习趋势分析（图表）
 * - 报告筛选和导出
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatOptionModule } from '@angular/material/core';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  ChildProfile,
  ChildrenManagementService,
} from '../../services/children-management.service';
import {
  LearningReport,
  LearningReportsService,
  LearningTrend,
  ReportFilter,
} from '../../services/learning-reports.service';

import { ReportDetailDialogComponent } from './report-detail-dialog/report-detail-dialog.component';

@Component({
  selector: 'app-learning-reports',
  standalone: true,
  providers: [provideNativeDateAdapter()],
  imports: [
    CommonModule,
    FormsModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatOptionModule,
    MatDatepickerModule,
    MatInputModule,
    MatFormFieldModule,
    MatDialogModule,
    MatTabsModule,
    MatDividerModule,
    MatChipsModule,
    MatMenuModule,
    MatTooltipModule,
  ],
  templateUrl: './learning-reports.component.html',
  styleUrls: ['./learning-reports.component.scss'],
})
export class LearningReportsComponent implements OnInit, OnDestroy {
  // 数据
  children: ChildProfile[] = [];
  reportsList: LearningReport[] = [];
  learningTrendData: LearningTrend | null = null;

  // UI状态
  isLoading = false;
  loadingError: string | null = null;
  selectedTab = 0; // 0: 报告列表, 1: 趋势分析

  // 筛选器
  filter: ReportFilter = {
    childId: null,
    sourceType: null,
    startDate: null,
    endDate: null,
  };

  // 私有属性
  private destroy$ = new Subject<void>();

  constructor(
    private learningReportsService: LearningReportsService,
    private childrenManagementService: ChildrenManagementService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    // 检查URL参数中是否有childId（从孩子管理页面跳转过来）
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe((params) => {
      if (params['childId']) {
        this.filter.childId = params['childId'];
      }
    });

    this.loadChildren();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载孩子列表
   */
  loadChildren(): void {
    this.childrenManagementService
      .getChildren()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (children) => {
          this.children = children;

          // 如果URL中有childId但不在孩子列表中，清除筛选
          if (this.filter.childId && !children.find((c) => c.id === this.filter.childId)) {
            this.filter.childId = null;
          }

          // 加载报告
          this.loadReports();
        },
        error: (error) => {
          console.error('加载孩子列表失败:', error);
          this.loadingError = error.message || '加载失败，请稍后重试';
        },
      });
  }

  /**
   * 加载报告列表
   */
  loadReports(): void {
    this.isLoading = true;
    this.loadingError = null;

    const params: any = {
      childId: this.filter.childId || undefined,
      reportType: this.filter.sourceType ? this.filter.sourceType : undefined,
    };

    this.learningReportsService
      .getReports(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.reportsList = response.data;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('加载报告失败:', error);
          this.loadingError = error.message || '加载失败，请稍后重试';
          this.isLoading = false;
        },
      });
  }

  /**
   * 加载学习趋势
   */
  loadLearningTrend(): void {
    if (!this.filter.childId) {
      this.snackBar.open('请先选择孩子', '关闭', { duration: 3000 });
      return;
    }

    this.isLoading = true;

    this.learningReportsService
      .getLearningTrend(this.filter.childId, 30)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (trend) => {
          this.learningTrendData = trend;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('加载学习趋势失败:', error);
          this.snackBar.open('加载趋势失败，请稍后重试', '关闭', { duration: 3000 });
          this.isLoading = false;
        },
      });
  }

  /**
   * 筛选器变更
   */
  onFilterChange(): void {
    if (this.selectedTab === 0) {
      this.loadReports();
    } else {
      this.loadLearningTrend();
    }
  }

  /**
   * 重置筛选器
   */
  resetFilter(): void {
    this.filter = {
      childId: null,
      sourceType: null,
      startDate: null,
      endDate: null,
    };
    this.onFilterChange();
  }

  /**
   * 查看报告详情
   */
  viewReportDetail(report: LearningReport): void {
    const dialogRef = this.dialog.open(ReportDetailDialogComponent, {
      width: '800px',
      data: { report },
    });

    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe((result) => {
        if (result === 'refresh') {
          this.loadReports();
        }
      });
  }

  /**
   * 导出报告
   */
  exportReport(reportId: string, format: 'pdf' | 'excel'): void {
    this.snackBar.open(`正在导出${format.toUpperCase()}格式报告...`, '关闭', { duration: 2000 });

    this.learningReportsService
      .exportReport(reportId, format)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob: Blob) => {
          // 创建下载链接
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `report.${format === 'excel' ? 'xlsx' : 'pdf'}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);

          this.snackBar.open('导出成功', '关闭', { duration: 3000 });
        },
        error: (error: Error) => {
          console.error('导出失败:', error);
          this.snackBar.open('导出失败，请稍后重试', '关闭', { duration: 3000 });
        },
      });
  }

  /**
   * 批量导出
   */
  batchExport(): void {
    this.snackBar.open('批量导出功能即将开放', '关闭', { duration: 3000 });
  }

  /**
   * 分享报告
   */
  shareReport(report: LearningReport): void {
    // 复制分享链接
    const shareUrl = `${window.location.origin}/user/learning-reports/${report.id}`;

    if (navigator.clipboard) {
      navigator.clipboard
        .writeText(shareUrl)
        .then(() => {
          this.snackBar.open('分享链接已复制到剪贴板', '关闭', { duration: 3000 });
        })
        .catch(() => {
          this.snackBar.open('复制失败', '关闭', { duration: 3000 });
        });
    } else {
      this.snackBar.open('您的浏览器不支持复制功能', '关闭', { duration: 3000 });
    }
  }

  /**
   * 重试加载
   */
  retry(): void {
    if (this.selectedTab === 0) {
      this.loadReports();
    } else {
      this.loadLearningTrend();
    }
  }

  /**
   * 获取来源类型标签
   */
  getSourceTypeLabel(sourceType: string): string {
    const labels: { [key: string]: string } = {
      school_curriculum: '校本课程',
      school_interest: '兴趣班',
      org_course: '机构课程',
      personal: '个人学习',
    };
    return labels[sourceType] || sourceType;
  }

  /**
   * 获取来源类型颜色
   */
  getSourceTypeColor(sourceType: string): string {
    const colors: Record<string, string> = {
      school_curriculum: 'primary',
      school_interest: 'accent',
      org_course: 'warn',
      personal: 'basic',
    };
    return colors[sourceType] || 'basic';
  }
}
