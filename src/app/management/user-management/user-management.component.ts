import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UserDetail, UserRole, UserStatus } from '@app/models/user.models';
import { UserManagementService } from '@app/services/user-management.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface UserDisplay extends UserDetail {
  statusColor: 'primary' | 'accent' | 'warn';
  statusLabel: string;
  roleLabel: string;
}

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatIconModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatDialogModule,
    MatSnackBarModule,
  ],
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss'],
})
export class UserManagementComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  users: UserDisplay[] = [];
  filteredUsers: UserDisplay[] = [];
  isLoading = true;

  // 筛选条件
  filterStatus: UserStatus | 'all' = 'all';
  filterRole: UserRole | 'all' = 'all';
  searchText = '';

  // 表格列定义
  displayedColumns: string[] = [
    'select',
    'name',
    'email',
    'role',
    'status',
    'licenses',
    'lastActive',
    'actions',
  ];

  // 批量操作
  selectedUserIds: number[] = [];
  isAllSelected = false;

  // 统计信息
  stats = {
    total: 0,
    active: 0,
    inactive: 0,
    admins: 0,
  };

  constructor(
    private userService: UserManagementService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadUsers(): void {
    this.isLoading = true;
    this.userService
      .getUserList()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data: UserDetail[]) => {
          this.users = data.map((user: UserDetail) => ({
            ...user,
            statusColor: this.getStatusColor(user.status),
            statusLabel: this.getStatusLabel(user.status),
            roleLabel: this.getRoleLabel(user.role),
          }));

          this.updateStats();
          this.applyFilters();
          this.isLoading = false;
        },
        error: (error: unknown) => {
          console.error('加载用户列表失败:', error);
          this.snackBar.open('加载用户列表失败，请稍后重试', '关闭', { duration: 3000 });
          this.isLoading = false;
        },
      });
  }

  private getStatusColor(status: UserStatus): 'primary' | 'accent' | 'warn' {
    switch (status) {
      case 'active':
        return 'primary';
      case 'pending':
        return 'accent';
      case 'suspended':
      case 'inactive':
        return 'warn';
      default:
        return 'primary';
    }
  }

  private getStatusLabel(status: UserStatus): string {
    const labels: Record<UserStatus, string> = {
      active: '活跃',
      pending: '待激活',
      suspended: '已停用',
      inactive: '未激活',
    };
    return labels[status];
  }

  private getRoleLabel(role: UserRole): string {
    const labels: Record<UserRole, string> = {
      admin: '管理员',
      teacher: '教师',
      student: '学生',
      parent: '家长',
    };
    return labels[role] || role;
  }

  getRoleColor(role: UserRole): 'primary' | 'accent' | 'warn' {
    switch (role) {
      case 'admin':
        return 'primary';
      case 'teacher':
        return 'accent';
      case 'student':
        return 'warn';
      default:
        return 'primary';
    }
  }

  private updateStats(): void {
    this.stats.total = this.users.length;
    this.stats.active = this.users.filter((u) => u.status === 'active').length;
    this.stats.inactive = this.users.filter(
      (u) => u.status === 'inactive' || u.status === 'suspended'
    ).length;
    this.stats.admins = this.users.filter((u) => u.role === 'admin').length;
  }

  applyFilters(): void {
    this.filteredUsers = this.users.filter((user) => {
      const matchStatus = this.filterStatus === 'all' || user.status === this.filterStatus;
      const matchRole = this.filterRole === 'all' || user.role === this.filterRole;
      const matchSearch =
        !this.searchText ||
        user.name.toLowerCase().includes(this.searchText.toLowerCase()) ||
        user.email.toLowerCase().includes(this.searchText.toLowerCase());

      return matchStatus && matchRole && matchSearch;
    });
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  /** 批量选择 */
  togglePageSelection(): void {
    if (this.isAllSelected) {
      this.selectedUserIds = [];
    } else {
      this.selectedUserIds = this.filteredUsers.map((u) => u.id);
    }
  }

  toggleUserSelection(userId: number): void {
    const index = this.selectedUserIds.indexOf(userId);
    if (index > -1) {
      this.selectedUserIds.splice(index, 1);
    } else {
      this.selectedUserIds.push(userId);
    }
    this.isAllSelected = this.selectedUserIds.length === this.filteredUsers.length;
  }

  /** 批量操作 */
  batchAssignLicense(): void {
    if (this.selectedUserIds.length === 0) {
      this.snackBar.open('请先选择用户', '关闭', { duration: 2000 });
      return;
    }

    this.snackBar.open(`为 ${this.selectedUserIds.length} 个用户分配许可证`, '关闭', {
      duration: 2000,
    });
    // TODO: 打开许可证分配对话框
  }

  batchActivate(): void {
    if (this.selectedUserIds.length === 0) {
      this.snackBar.open('请先选择用户', '关闭', { duration: 2000 });
      return;
    }

    if (!confirm(`确定要激活选中的 ${this.selectedUserIds.length} 个用户吗？`)) {
      return;
    }

    this.userService
      .batchUpdateStatus(this.selectedUserIds, 'active')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('批量激活成功', '关闭', { duration: 2000 });
          this.loadUsers();
        },
        error: (error: unknown) => {
          console.error('批量激活失败:', error);
          this.snackBar.open('批量激活失败', '关闭', { duration: 3000 });
        },
      });
  }

  batchSuspend(): void {
    if (this.selectedUserIds.length === 0) {
      this.snackBar.open('请先选择用户', '关闭', { duration: 2000 });
      return;
    }

    if (!confirm(`确定要停用选中的 ${this.selectedUserIds.length} 个用户吗？`)) {
      return;
    }

    this.userService
      .batchUpdateStatus(this.selectedUserIds, 'suspended')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('批量停用成功', '关闭', { duration: 2000 });
          this.loadUsers();
        },
        error: (error: unknown) => {
          console.error('批量停用失败:', error);
          this.snackBar.open('批量停用失败', '关闭', { duration: 3000 });
        },
      });
  }

  /** 单个用户操作 */
  viewUserDetails(user: UserDisplay): void {
    this.snackBar.open(`查看用户详情：${user.name}`, '关闭', { duration: 2000 });
    // TODO: 打开详情对话框
  }

  editUser(user: UserDisplay): void {
    this.snackBar.open(`编辑用户：${user.name}`, '关闭', { duration: 2000 });
    // TODO: 打开编辑对话框
  }

  resetPassword(user: UserDisplay): void {
    if (!confirm(`确定要重置用户 ${user.name} 的密码吗？`)) {
      return;
    }

    this.userService
      .resetPassword(user.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (tempPassword: string) => {
          this.snackBar.open(`密码已重置，临时密码：${tempPassword}`, '关闭', { duration: 5000 });
        },
        error: (error: unknown) => {
          console.error('重置密码失败:', error);
          this.snackBar.open('重置密码失败', '关闭', { duration: 3000 });
        },
      });
  }

  suspendUser(user: UserDisplay): void {
    if (!confirm(`确定要停用用户 ${user.name} 吗？`)) {
      return;
    }

    this.userService
      .updateUserStatus(user.id, 'suspended')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('用户已停用', '关闭', { duration: 2000 });
          this.loadUsers();
        },
        error: (error: unknown) => {
          console.error('停用用户失败:', error);
          this.snackBar.open('停用用户失败', '关闭', { duration: 3000 });
        },
      });
  }

  /** 导入导出 */
  exportUsers(): void {
    this.userService.exportUsersToExcel(this.filteredUsers).subscribe({
      next: () => {
        this.snackBar.open('导出成功', '关闭', { duration: 2000 });
      },
      error: (error: unknown) => {
        console.error('导出失败:', error);
        this.snackBar.open('导出失败', '关闭', { duration: 3000 });
      },
    });
  }

  importUsers(): void {
    this.snackBar.open('请选择 Excel 文件', '关闭', { duration: 2000 });
    // TODO: 打开文件选择器
  }

  createUser(): void {
    this.snackBar.open('添加用户功能开发中...', '关闭', { duration: 2000 });
    // TODO: 打开创建用户对话框
  }
}
