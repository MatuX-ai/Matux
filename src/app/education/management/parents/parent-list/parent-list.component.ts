/**
 * 家长列表组件 - 独立管理所有家长信息
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { Subject } from 'rxjs';

import { RelationshipType } from '../../../models/student.models';
import { StudentService } from '../../../services/student.service';

interface ParentWithStudent {
  id?: string;
  name: string;
  relationshipType: RelationshipType;
  phone: string;
  email?: string;
  wechat?: string;
  qq?: string;
  address?: string;
  isPrimary?: boolean;
  notes?: string;
  studentName?: string;
  studentId?: string;
}

@Component({
  selector: 'app-parent-list',
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
    MatDialogModule,
  ],
  templateUrl: './parent-list.component.html',
  styleUrls: ['./parent-list.component.scss'],
})
export class ParentListComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // 数据
  parents: ParentWithStudent[] = [];
  loading = false;
  error: string | null = null;

  // 表格列定义
  displayedColumns: string[] = [
    'name',
    'relationshipType',
    'phone',
    'email',
    'wechat',
    'studentName',
    'isPrimary',
    'actions',
  ];

  // 筛选条件
  searchKeyword = '';
  relationshipFilter: RelationshipType | 'all' = 'all';

  /**
   * 获取关系类型标签 (类型安全方法)
   */
  getRelationshipLabel(type: RelationshipType): string {
    // RelationshipType 本身就是中文字符串，直接返回
    return type;
  }

  constructor(
    private studentService: StudentService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.loadParents();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载家长列表
   */
  loadParents(): void {
    this.loading = true;
    this.error = null;

    // TODO: 调用 API 获取所有家长信息
    // 目前从学员数据中提取
    setTimeout(() => {
      // 模拟数据
      this.parents = [
        {
          id: 'parent_001',
          studentId: 'student_001',
          studentName: '张三',
          name: '张父',
          relationshipType: 'father' as RelationshipType,
          phone: '13900139000',
          email: 'zhang@example.com',
          wechat: 'zhang_father',
          qq: '123456789',
          address: '',
          isPrimary: true,
          notes: '主要联系人',
        },
        {
          id: 'parent_002',
          studentId: 'student_001',
          studentName: '张三',
          name: '李母',
          relationshipType: 'mother' as RelationshipType,
          phone: '13700137000',
          email: 'li@example.com',
          wechat: 'li_mother',
          qq: '987654321',
          address: '',
          isPrimary: false,
          notes: '',
        },
      ] as unknown as ParentWithStudent[];
      this.loading = false;
    }, 500);
  }

  /**
   * 应用筛选
   */
  applyFilters(): void {
    // TODO: 实现筛选逻辑
  }

  /**
   * 清空筛选
   */
  clearFilters(): void {
    this.searchKeyword = '';
    this.relationshipFilter = 'all';
    this.loadParents();
  }

  /**
   * 新增家长
   */
  addParent(): void {
    // TODO: 实现家长表单对话框组件
  }

  /**
   * 编辑家长
   */
  editParent(_parent: ParentWithStudent): void {
    // TODO: 实现家长表单对话框组件
  }

  /**
   * 删除家长
   */
  deleteParent(parent: ParentWithStudent): void {
    if (confirm(`确定要删除"${parent.name}"的家长信息吗？`)) {
      // TODO: 调用删除 API
      this.loadParents();
    }
  }

  /**
   * 查看关联学员
   */
  viewStudent(_studentId: string): void {
    // TODO: 导航到学员详情页
  }
}
