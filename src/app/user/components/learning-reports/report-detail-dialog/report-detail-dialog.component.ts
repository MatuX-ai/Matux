/**
 * 报告详情对话框组件
 */

import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';

import { LearningReport } from '../../../services/learning-reports.service';

export interface ReportDetailDialogData {
  report: LearningReport;
}

@Component({
  selector: 'app-report-detail-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatChipsModule,
    MatTabsModule,
    MatCardModule,
  ],
  templateUrl: './report-detail-dialog.component.html',
  styleUrls: ['./report-detail-dialog.component.scss'],
})
export class ReportDetailDialogComponent {
  isLoading = false;
  selectedTab = 0;

  constructor(
    public dialogRef: MatDialogRef<ReportDetailDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ReportDetailDialogData
  ) {}

  get report(): LearningReport {
    return this.data.report;
  }

  /**
   * 关闭对话框
   */
  close(): void {
    this.dialogRef.close();
  }

  /**
   * 获取等级标签
   */
  getGradeLevelLabel(gradeLevel: string): string {
    const labels: Record<string, string> = {
      A: '优秀',
      B: '良好',
      C: '及格',
      D: '不及格',
    };
    return labels[gradeLevel] || gradeLevel;
  }
}
