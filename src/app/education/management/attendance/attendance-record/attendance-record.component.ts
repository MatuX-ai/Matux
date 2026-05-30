/**
 * 签到记录列表组件 - 管理员/教师查看
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';

interface AttendanceRecord {
  id: string;
  studentName: string;
  courseName: string;
  checkinTime: Date;
  status: 'success' | 'late' | 'absent';
  deductedHours: number;
}

@Component({
  selector: 'app-attendance-record',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  template: `
    <div class="attendance-record-container">
      <mat-card>
        <mat-card-header>
          <mat-card-title>签到记录</mat-card-title>
        </mat-card-header>

        <mat-card-content>
          <!-- 加载状态 -->
          <div *ngIf="loading" class="loading-state">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
          </div>

          <!-- 数据表格 -->
          <div *ngIf="!loading" class="table-container">
            <table mat-table [dataSource]="records" matSort>
              <ng-container matColumnDef="studentName">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>学生姓名</th>
                <td mat-cell *matCellDef="let record">{{ record.studentName }}</td>
              </ng-container>

              <ng-container matColumnDef="courseName">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>课程名称</th>
                <td mat-cell *matCellDef="let record">{{ record.courseName }}</td>
              </ng-container>

              <ng-container matColumnDef="checkinTime">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>签到时间</th>
                <td mat-cell *matCellDef="let record">
                  {{ record.checkinTime | date: 'yyyy-MM-dd HH:mm' }}
                </td>
              </ng-container>

              <ng-container matColumnDef="status">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>状态</th>
                <td mat-cell *matCellDef="let record">
                  <mat-chip-set>
                    <mat-chip [color]="getStatusColor(record.status)">
                      {{ getStatusLabel(record.status) }}
                    </mat-chip>
                  </mat-chip-set>
                </td>
              </ng-container>

              <ng-container matColumnDef="deductedHours">
                <th mat-header-cell *matHeaderCellDef mat-sort-header>扣减课时</th>
                <td mat-cell *matCellDef="let record">{{ record.deductedHours }}</td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
            </table>

            <mat-paginator [pageSizeOptions]="[10, 20, 50]" showFirstLastButtons></mat-paginator>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .attendance-record-container {
        padding: 20px;
      }

      .loading-state {
        padding: 40px 0;
      }

      .table-container {
        overflow-x: auto;
      }

      table {
        width: 100%;
      }
    `,
  ],
})
export class AttendanceRecordComponent implements OnInit {
  loading = false;
  records: AttendanceRecord[] = [];
  displayedColumns: string[] = [
    'studentName',
    'courseName',
    'checkinTime',
    'status',
    'deductedHours',
  ];

  ngOnInit(): void {
    this.loadRecords();
  }

  loadRecords(): void {
    this.loading = true;

    // TODO: 调用后端 API
    setTimeout(() => {
      this.records = [
        {
          id: '1',
          studentName: '张三',
          courseName: '数学课',
          checkinTime: new Date(),
          status: 'success',
          deductedHours: 2,
        },
      ];
      this.loading = false;
    }, 1000);
  }

  getStatusColor(status: string): 'primary' | 'accent' | 'warn' {
    switch (status) {
      case 'success':
        return 'primary';
      case 'late':
        return 'accent';
      case 'absent':
        return 'warn';
      default:
        return 'primary';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'success':
        return '正常';
      case 'late':
        return '迟到';
      case 'absent':
        return '缺勤';
      default:
        return status;
    }
  }
}
