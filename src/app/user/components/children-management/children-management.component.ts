/**
 * 孩子管理组件（家长）
 * 功能：
 * - 显示已绑定的孩子列表
 * - 绑定新孩子（通过邀请码）
 * - 解绑孩子
 * - 查看孩子详细信息
 * - 查看孩子学习进度
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  BindApplication,
  ChildProfile,
  ChildrenManagementService,
} from '../../services/children-management.service';

import { ChildDetailDialogComponent } from './child-detail-dialog/child-detail-dialog.component';

@Component({
  selector: 'app-children-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatDialogModule,
    MatTabsModule,
    MatDividerModule,
    MatChipsModule,
    MatTooltipModule,
  ],
  templateUrl: './children-management.component.html',
  styleUrls: ['./children-management.component.scss'],
})
export class ChildrenManagementComponent implements OnInit, OnDestroy {
  // 数据
  children: ChildProfile[] = [];
  pendingRequests: BindApplication[] = [];

  // UI状态
  isLoading = false;
  loadingError: string | null = null;
  selectedTab = 0; // 0: 已绑定, 1: 绑定申请

  // 绑定新孩子
  inviteCode = '';
  isBinding = false;

  // 私有属性
  private destroy$ = new Subject<void>();

  constructor(
    private childrenManagementService: ChildrenManagementService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadChildrenData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载孩子数据
   */
  loadChildrenData(): void {
    this.isLoading = true;
    this.loadingError = null;

    this.childrenManagementService
      .getChildren()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (children) => {
          this.children = children;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('加载孩子数据失败:', error);
          this.loadingError = error.message || '加载失败，请稍后重试';
          this.isLoading = false;
        },
      });

    // 加载待处理的绑定申请
    this.loadBindingRequests();
  }

  /**
   * 加载绑定申请
   */
  loadBindingRequests(): void {
    this.childrenManagementService
      .getBindingRequests()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (requests) => {
          this.pendingRequests = requests.filter((req) => req.status === 'pending');
        },
        error: (error) => {
          console.error('加载绑定申请失败:', error);
        },
      });
  }

  /**
   * 搜索孩子
   */
  searchChild(searchTerm: string): void {
    if (!searchTerm || searchTerm.trim() === '') {
      this.loadChildrenData();
      return;
    }

    this.childrenManagementService
      .searchChildren(searchTerm)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (children) => {
          this.children = children;
        },
        error: (error) => {
          console.error('搜索失败:', error);
          this.snackBar.open('搜索失败，请稍后重试', '关闭', { duration: 3000 });
        },
      });
  }

  /**
   * 绑定新孩子（通过邀请码）
   */
  bindChildByInviteCode(): void {
    if (!this.inviteCode || this.inviteCode.trim() === '') {
      this.snackBar.open('请输入邀请码', '关闭', { duration: 3000 });
      return;
    }

    this.isBinding = true;

    this.childrenManagementService
      .bindChildByInviteCode(this.inviteCode.trim())
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (request) => {
          this.isBinding = false;
          this.inviteCode = '';

          if (request.status === 'approved') {
            this.snackBar.open('绑定成功！', '关闭', { duration: 3000 });
            this.loadChildrenData();
          } else {
            this.snackBar.open('绑定申请已发送，等待对方确认', '关闭', { duration: 3000 });
            this.loadBindingRequests();
            this.selectedTab = 1; // 切换到申请列表
          }
        },
        error: (error) => {
          console.error('绑定失败:', error);
          this.isBinding = false;
          this.snackBar.open(error.message || '绑定失败，请检查邀请码', '关闭', { duration: 3000 });
        },
      });
  }

  /**
   * 解绑孩子
   */
  unbindChild(childId: string): void {
    const child = this.children.find((c) => c.id === childId);
    if (!child) return;

    const confirmed = confirm(
      `确定要解绑孩子"${child.nickname}"吗？解绑后将无法查看该孩子的学习数据。`
    );

    if (confirmed) {
      this.childrenManagementService
        .unbindChild(childId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.snackBar.open('解绑成功', '关闭', { duration: 3000 });
            this.children = this.children.filter((c) => c.id !== childId);
          },
          error: (error) => {
            console.error('解绑失败:', error);
            this.snackBar.open('解绑失败，请稍后重试', '关闭', { duration: 3000 });
          },
        });
    }
  }

  /**
   * 查看孩子详情
   */
  viewChildDetail(child: ChildProfile): void {
    const dialogRef = this.dialog.open(ChildDetailDialogComponent, {
      width: '600px',
      data: { child },
    });

    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe((result) => {
        if (result === 'refresh') {
          this.loadChildrenData();
        }
      });
  }

  /**
   * 查看孩子学习进度
   */
  viewChildLearning(childId: string): void {
    // 导航到学习报告页面，并筛选该孩子
    this.router.navigate(['/user/learning-reports'], {
      queryParams: { childId },
    });
  }

  /**
   * 同意绑定申请
   */
  approveRequest(requestId: string): void {
    this.childrenManagementService
      .approveBindingRequest(requestId, true)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('已同意绑定申请', '关闭', { duration: 3000 });
          this.loadBindingRequests();
          this.loadChildrenData();
        },
        error: (error) => {
          console.error('同意申请失败:', error);
          this.snackBar.open('操作失败，请稍后重试', '关闭', { duration: 3000 });
        },
      });
  }

  /**
   * 拒绝绑定申请
   */
  rejectRequest(requestId: string): void {
    const confirmed = confirm('确定要拒绝该绑定申请吗？');

    if (confirmed) {
      this.childrenManagementService
        .approveBindingRequest(requestId, false)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.snackBar.open('已拒绝绑定申请', '关闭', { duration: 3000 });
            this.loadBindingRequests();
          },
          error: (error) => {
            console.error('拒绝申请失败:', error);
            this.snackBar.open('操作失败，请稍后重试', '关闭', { duration: 3000 });
          },
        });
    }
  }

  /**
   * 取消绑定申请
   */
  cancelRequest(requestId: string): void {
    const confirmed = confirm('确定要取消该绑定申请吗？');

    if (confirmed) {
      this.childrenManagementService
        .cancelBindingRequest(requestId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.snackBar.open('已取消绑定申请', '关闭', { duration: 3000 });
            this.loadBindingRequests();
          },
          error: (error) => {
            console.error('取消申请失败:', error);
            this.snackBar.open('操作失败，请稍后重试', '关闭', { duration: 3000 });
          },
        });
    }
  }

  /**
   * 重试加载
   */
  retry(): void {
    this.loadChildrenData();
  }

  /**
   * 获取绑定状态文本
   */
  getBindingStatusText(status: string): string {
    switch (status) {
      case 'pending':
        return '待确认';
      case 'approved':
        return '已绑定';
      case 'rejected':
        return '已拒绝';
      case 'cancelled':
        return '已取消';
      default:
        return '未知';
    }
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'pending':
        return 'warn';
      case 'approved':
        return 'accent';
      case 'rejected':
        return 'danger';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  }

  /**
   * 获取状态图标
   */
  getStatusIcon(status: string): string {
    switch (status) {
      case 'pending':
        return 'pending';
      case 'approved':
        return 'check_circle';
      case 'rejected':
        return 'cancel';
      case 'cancelled':
        return 'remove_circle';
      default:
        return 'help';
    }
  }
}
