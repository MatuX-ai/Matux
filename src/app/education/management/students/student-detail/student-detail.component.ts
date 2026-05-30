/**
 * 学员详情组件 - 展示学员完整信息
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';

import { StudentProfile, StudentStatus } from '../../../models/student.models';
import { StudentService } from '../../../services/student.service';

import { StudentEditDialogComponent } from './student-edit-dialog.component';

@Component({
  selector: 'app-student-detail',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatDividerModule,
    MatProgressBarModule,
    MatDialogModule,
  ],
  templateUrl: './student-detail.component.html',
  styleUrls: ['./student-detail.component.scss'],
})
export class StudentDetailComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  student: StudentProfile | null = null;
  loading = false;
  error: string | null = null;

  // 状态标签映射
  statusLabels: Record<StudentStatus, string> = {
    在读: '在读',
    休学: '休学',
    毕业: '毕业',
    退学: '退学',
    转校: '转校',
  };

  // 状态颜色映射
  statusColors: Record<StudentStatus, string> = {
    在读: 'primary',
    休学: 'accent',
    毕业: 'basic',
    退学: 'warn',
    转校: 'accent',
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private studentService: StudentService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const studentId = this.route.snapshot.paramMap.get('id');
    if (studentId) {
      this.loadStudent(studentId);
    } else {
      this.error = '未指定学员 ID';
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载学员详情
   */
  loadStudent(studentId: string): void {
    this.loading = true;
    this.error = null;

    this.studentService.getStudentById(studentId).subscribe({
      next: (data) => {
        this.student = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('加载学员详情失败:', err);
        this.error = '加载学员详情失败';
        this.loading = false;
        this.snackBar.open('加载学员信息失败，请重试', '关闭', { duration: 3000 });
      },
    });
  }

  /**
   * 返回学员列表
   */
  goBack(): void {
    void this.router.navigate(['/education/students']);
  }

  /**
   * 编辑学员
   */
  editStudent(): void {
    if (!this.student) return;

    const dialogRef = this.dialog.open(StudentEditDialogComponent, {
      width: '800px',
      maxWidth: '95vw',
      data: {
        student: this.student,
      },
    });

    dialogRef.afterClosed().subscribe((result: StudentProfile | undefined) => {
      if (result) {
        // 更新本地数据
        this.student = result;
        this.snackBar.open('学员信息已更新', '关闭', { duration: 2000 });
      }
    });
  }

  /**
   * 计算课时使用率
   */
  getUsageRate(): number {
    if (!this.student || this.student.totalPurchasedHours === 0) {
      return 0;
    }
    return Math.round((this.student.totalConsumedHours / this.student.totalPurchasedHours) * 100);
  }
}
