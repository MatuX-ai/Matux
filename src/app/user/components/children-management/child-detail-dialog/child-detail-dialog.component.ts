/**
 * 孩子详情对话框组件
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

import { ChildProfile } from '../../../services/children-management.service';

export interface ChildDetailDialogData {
  child: ChildProfile;
}

@Component({
  selector: 'app-child-detail-dialog',
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
  templateUrl: './child-detail-dialog.component.html',
  styleUrls: ['./child-detail-dialog.component.scss'],
})
export class ChildDetailDialogComponent {
  isLoading = false;
  selectedTab = 0;

  constructor(
    public dialogRef: MatDialogRef<ChildDetailDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ChildDetailDialogData
  ) {}

  get child(): ChildProfile {
    return this.data.child;
  }

  /**
   * 关闭对话框
   */
  close(): void {
    this.dialogRef.close();
  }

  /**
   * 查看学习报告
   */
  viewLearningReports(): void {
    this.dialogRef.close('view-reports');
  }
}
