/**
 * 学员列表组件 - 展示学员列表，支持搜索、筛选和基础操作
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { Subject } from 'rxjs';

import { Gender, StudentProfile, StudentStatus } from '../../../models/student.models';
import { StudentService } from '../../../services/student.service';

@Component({
  selector: 'app-student-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule,
    MatSelectModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
  ],
  templateUrl: './student-list.component.html',
  styleUrls: ['./student-list.component.scss'],
})
export class StudentListComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // 数据
  students: StudentProfile[] = [];
  loading = false;
  error: string | null = null;

  // 表格列定义
  displayedColumns: string[] = [
    'avatar',
    'name',
    'gender',
    'grade',
    'school',
    'status',
    'remainingHours',
    'actions',
  ];

  // 筛选条件
  searchKeyword = '';
  statusFilter: StudentStatus | 'all' = 'all';
  genderFilter: Gender | 'all' = 'all';

  // 状态标签映射
  statusLabels: Record<StudentStatus, string> = {
    在读: '在读',
    休学: '休学',
    毕业: '毕业',
    退学: '退学',
    转校: '转校',
  };

  // 状态颜色映射
  statusColors: Record<StudentStatus, 'primary' | 'accent' | 'warn' | 'basic'> = {
    在读: 'primary',
    休学: 'accent',
    毕业: 'basic',
    退学: 'warn',
    转校: 'accent',
  };

  /**
   * 获取状态对应的颜色（类型安全方法）
   */
  getStatusColor(status: StudentStatus): 'primary' | 'accent' | 'warn' | 'basic' {
    return this.statusColors[status];
  }

  /**
   * 获取状态对应的标签（类型安全方法）
   */
  getStatusLabel(status: StudentStatus): string {
    return this.statusLabels[status];
  }

  constructor(private studentService: StudentService) {}

  ngOnInit(): void {
    this.loadStudents();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载学员列表
   */
  loadStudents(): void {
    this.loading = true;
    this.error = null;

    // TODO: 调用服务获取数据
    // this.studentService.getStudents().subscribe({
    //   next: (data) => {
    //     this.students = data;
    //     this.loading = false;
    //   },
    //   error: (err) => {
    //     this.error = '加载学员列表失败，请稍后重试';
    //     this.loading = false;
    //   },
    // });

    // 模拟数据
    setTimeout(() => {
      this.students = [
        {
          id: '1',
          name: '张三',
          gender: 'male',
          grade: '初三',
          school: 'XX 中学',
          status: '在读',
          totalPurchasedHours: 100,
          totalConsumedHours: 45,
          remainingHours: 55,
          enrollmentDate: '2024-09-01',
          parents: [],
          createdAt: '2024-09-01T00:00:00Z',
          updatedAt: '2024-09-01T00:00:00Z',
        },
        {
          id: '2',
          name: '李四',
          gender: 'female',
          grade: '初二',
          school: 'XX 外国语学校',
          status: '在读',
          totalPurchasedHours: 80,
          totalConsumedHours: 60,
          remainingHours: 20,
          enrollmentDate: '2024-03-01',
          parents: [],
          createdAt: '2024-03-01T00:00:00Z',
          updatedAt: '2024-03-01T00:00:00Z',
        },
      ] as StudentProfile[];
      this.loading = false;
    }, 500);
  }

  /**
   * 应用筛选
   */
  applyFilters(): void {
    // TODO: 实现筛选逻辑
    console.log('筛选条件:', {
      keyword: this.searchKeyword,
      status: this.statusFilter,
      gender: this.genderFilter,
    });
  }

  /**
   * 清空筛选
   */
  clearFilters(): void {
    this.searchKeyword = '';
    this.statusFilter = 'all';
    this.genderFilter = 'all';
    this.loadStudents();
  }

  /**
   * 新增学员
   */
  addStudent(): void {
    // TODO: 打开新增对话框
    console.log('新增学员');
  }

  /**
   * 编辑学员
   */
  editStudent(student: StudentProfile): void {
    // TODO: 打开编辑对话框
    console.log('编辑学员:', student.name);
  }

  /**
   * 查看学员详情
   */
  viewDetail(student: StudentProfile): void {
    // TODO: 导航到详情页
    console.log('查看详情:', student.name);
  }

  /**
   * 删除学员
   */
  deleteStudent(student: StudentProfile): void {
    if (confirm(`确定要删除学员"${student.name}"吗？`)) {
      // TODO: 调用删除 API
      console.log('删除学员:', student.name);
    }
  }
}
