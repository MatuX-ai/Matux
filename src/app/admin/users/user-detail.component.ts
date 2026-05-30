/**
 * 用户详情组件
 * 显示用户详细信息、学习统计、机构关联、权限信息和活动日志
 */

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable, of } from 'rxjs';
import { catchError, finalize, tap } from 'rxjs/operators';

import { UserDetail, UserStatus } from './models/user-management.models';
import { UserManagementService } from './services/user-management.service';

@Component({
  selector: 'app-user-detail',
  standalone: false,
  templateUrl: './user-detail.component.html',
  styleUrls: ['./user-detail.component.scss'],
})
export class UserDetailComponent implements OnInit {
  // 用户详情
  userDetail$: Observable<UserDetail | null> = of(null);

  // 加载状态
  loading = false;
  error: string | null = null;

  // 活跃标签页
  activeTab = 'info';

  // 用户ID
  userId: string = '';

  // ==================== 构造函数 ====================
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private userService: UserManagementService
  ) {}

  // ==================== 生命周期钩子 ====================
  ngOnInit(): void {
    this.userId = this.route.snapshot.paramMap.get('id') || '';
    if (this.userId) {
      this.loadUserDetail();
    } else {
      this.error = '无效的用户ID';
    }
  }

  // ==================== 数据加载 ====================

  /**
   * 加载用户详情
   */
  loadUserDetail(): void {
    this.loading = true;
    this.error = null;

    this.userDetail$ = this.userService.getUserDetail(this.userId).pipe(
      tap(() => (this.loading = false)),
      catchError((err) => {
        this.error = '加载用户详情失败，请稍后重试';
        this.loading = false;
        console.error('加载用户详情失败:', err);
        return of(null);
      })
    );
  }

  // ==================== 操作方法 ====================

  /**
   * 返回用户列表
   */
  goBack(): void {
    this.router.navigate(['/admin/users']);
  }

  /**
   * 激活用户
   */
  activateUser(): void {
    this.updateUserStatus(UserStatus.ACTIVE);
  }

  /**
   * 停用用户
   */
  deactivateUser(): void {
    this.updateUserStatus(UserStatus.INACTIVE);
  }

  /**
   * 暂停用户
   */
  suspendUser(): void {
    this.updateUserStatus(UserStatus.SUSPENDED);
  }

  /**
   * 更新用户状态
   */
  private updateUserStatus(status: UserStatus): void {
    if (!confirm(`确定要将用户状态设置为 "${status}" 吗？`)) {
      return;
    }

    this.loading = true;
    this.userService
      .updateUserStatus(this.userId, status)
      .pipe(
        finalize(() => (this.loading = false)),
        catchError((err) => {
          alert(`更新状态失败: ${err.message}`);
          return of(null);
        })
      )
      .subscribe(() => {
        alert('状态更新成功');
        this.loadUserDetail();
      });
  }

  /**
   * 删除用户
   */
  deleteUser(): void {
    if (!confirm('确定要删除此用户吗？此操作不可恢复。')) {
      return;
    }

    this.loading = true;
    this.userService
      .deleteUser(this.userId)
      .pipe(
        finalize(() => (this.loading = false)),
        catchError((err) => {
          alert(`删除失败: ${err.message}`);
          return of(null);
        })
      )
      .subscribe(() => {
        alert('删除成功');
        this.router.navigate(['/admin/users']);
      });
  }

  /**
   * 编辑用户
   */
  editUser(): void {
    this.router.navigate(['/admin/users', this.userId, 'edit']);
  }

  // ==================== 工具方法 ====================

  /**
   * 格式化日期
   */
  formatDate(date: Date | string | undefined): string {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(status: UserStatus): string {
    switch (status) {
      case UserStatus.ACTIVE:
        return 'primary';
      case UserStatus.INACTIVE:
        return 'default';
      case UserStatus.SUSPENDED:
        return 'warn';
      case UserStatus.PENDING:
        return 'accent';
      default:
        return 'default';
    }
  }

  /**
   * 获取状态标签
   */
  getStatusLabel(status: UserStatus): string {
    const labels: Record<UserStatus, string> = {
      [UserStatus.ACTIVE]: '活跃',
      [UserStatus.INACTIVE]: '未激活',
      [UserStatus.SUSPENDED]: '已停用',
      [UserStatus.PENDING]: '待审核',
    };
    return labels[status] || status;
  }

  /**
   * 获取活动图标
   */
  getActivityIcon(type: string): string {
    const icons: Record<string, string> = {
      login: 'login',
      logout: 'logout',
      course_create: 'add_circle',
      course_update: 'edit',
      course_delete: 'remove_circle',
      grade_update: 'grade',
      assignment_submit: 'assignment',
      file_upload: 'cloud_upload',
      settings: 'settings',
      profile_update: 'person',
    };
    return icons[type] || 'info';
  }
}
