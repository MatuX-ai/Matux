/**
 * 用户列表组件
 * 提供用户搜索、筛选、分页、批量操作等功能
 */

import { AfterViewInit, Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { PageEvent } from '@angular/material/paginator';
import { Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, finalize, startWith, tap } from 'rxjs/operators';

import {
  AdminUser,
  PaginatedUserList,
  UserFilterOptions,
  UserListQuery,
  UserRole,
  UserStatistics,
  UserStatus,
} from './models/user-management.models';
import { UserManagementService } from './services/user-management.service';

@Component({
  selector: 'app-user-list',
  standalone: false,
  templateUrl: './user-list.component.html',
  styleUrls: ['./user-list.component.scss'],
})
export class UserListComponent implements OnInit, AfterViewInit {
  // ==================== 表格配置 ====================
  displayedColumns: string[] = [
    'avatar',
    'username',
    'email',
    'realName',
    'userType',
    'status',
    'organization',
    'lastLoginAt',
    'actions',
  ];
  dataSource: MatTableDataSource<AdminUser> = new MatTableDataSource<AdminUser>();

  // ==================== 状态管理 ====================
  loading$ = new BehaviorSubject<boolean>(false);
  error$ = new BehaviorSubject<string | null>(null);

  // ==================== 分页配置 ====================
  pageSizeOptions: number[] = [10, 25, 50, 100];
  pageIndex = 0;
  pageSize = 25;
  totalItems = 0;

  // ==================== 统计数据 ====================
  statistics$: Observable<UserStatistics | null> = of(null);
  filterOptions$: Observable<UserFilterOptions | null> = of(null);

  // ==================== 筛选表单 ====================
  filterForm: FormGroup;
  userTypes: { value: string; label: string }[] = [];
  statuses: { value: UserStatus; label: string }[] = [];
  roles: { value: UserRole; label: string }[] = [];
  organizations: { id: number; name: string }[] = [];

  // ==================== 选中行 ====================
  selectedUsers: Set<string> = new Set();
  allSelected = false;

  // ==================== 构造函数 ====================
  constructor(
    private userService: UserManagementService,
    private fb: FormBuilder,
    private router: Router
  ) {
    this.filterForm = this.fb.group({
      search: [''],
      userType: [''],
      status: [''],
      role: [''],
      organizationId: [''],
      createdAfter: [''],
      createdBefore: [''],
    });
  }

  // ==================== 生命周期钩子 ====================
  ngOnInit(): void {
    this.loadFilterOptions();
    this.loadStatistics();
  }

  ngAfterViewInit(): void {
    // 监听筛选变化自动刷新列表
    this.filterForm.valueChanges
      .pipe(
        startWith(this.filterForm.value),
        tap(() => {
          this.pageIndex = 0;
          this.loadUserList();
        })
      )
      .subscribe();
  }

  // ==================== 数据加载 ====================

  /**
   * 加载过滤选项
   */
  loadFilterOptions(): void {
    this.filterOptions$ = this.userService.getFilterOptions().pipe(
      catchError((err) => {
        console.error('加载过滤选项失败:', err);
        return of(null);
      })
    );

    this.filterOptions$.subscribe((options) => {
      if (options) {
        this.userTypes = options.userTypes.map((t) => ({ value: t.value, label: t.label }));
        this.statuses = options.statuses.map((s) => ({ value: s.value, label: s.label }));
        this.roles = options.roles.map((r) => ({ value: r.value, label: r.label }));
        this.organizations = options.organizations.map((o) => ({ id: o.id, name: o.name }));
      }
    });
  }

  /**
   * 加载统计数据
   */
  loadStatistics(): void {
    this.statistics$ = this.userService.getUserStatistics().pipe(
      catchError((err) => {
        console.error('加载统计数据失败:', err);
        return of(null);
      })
    );
  }

  /**
   * 加载用户列表
   */
  loadUserList(): void {
    this.loading$.next(true);
    this.error$.next(null);

    const filterValue = this.filterForm.value;

    const query: UserListQuery = {
      page: this.pageIndex + 1,
      pageSize: this.pageSize,
      search: filterValue.search || undefined,
      userType: filterValue.userType || undefined,
      status: filterValue.status || undefined,
      role: filterValue.role || undefined,
      organizationId: filterValue.organizationId || undefined,
      createdAfter: filterValue.createdAfter ? new Date(filterValue.createdAfter) : undefined,
      createdBefore: filterValue.createdBefore ? new Date(filterValue.createdBefore) : undefined,
      sortBy: 'createdAt',
      sortOrder: 'desc',
    };

    this.userService
      .getUserList(query)
      .pipe(
        finalize(() => this.loading$.next(false)),
        catchError((err) => {
          this.error$.next('加载用户列表失败，请稍后重试');
          console.error('加载用户列表失败:', err);
          return of({
            items: [],
            total: 0,
            page: 1,
            pageSize: this.pageSize,
            totalPages: 0,
            hasNext: false,
            hasPrevious: false,
          } as PaginatedUserList);
        })
      )
      .subscribe((response) => {
        this.dataSource.data = response.items;
        this.totalItems = response.total;
      });
  }

  // ==================== 分页处理 ====================

  /**
   * 分页事件处理
   */
  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.loadUserList();
  }

  /**
   * 排序事件处理
   */
  onSortChange(sort: Sort): void {
    // 触发重新加载
    this.loadUserList();
  }

  // ==================== 筛选操作 ====================

  /**
   * 重置筛选
   */
  resetFilters(): void {
    this.filterForm.reset({
      search: '',
      userType: '',
      status: '',
      role: '',
      organizationId: '',
      createdAfter: '',
      createdBefore: '',
    });
    this.pageIndex = 0;
    this.loadUserList();
  }

  /**
   * 搜索提交
   */
  onSearch(): void {
    this.pageIndex = 0;
    this.loadUserList();
  }

  // ==================== 选择操作 ====================

  /**
   * 切换全选
   */
  toggleSelectAll(): void {
    if (this.allSelected) {
      this.selectedUsers.clear();
    } else {
      this.dataSource.data.forEach((user) => this.selectedUsers.add(user.id));
    }
    this.allSelected = !this.allSelected;
  }

  /**
   * 切换单选
   */
  toggleSelect(userId: string): void {
    if (this.selectedUsers.has(userId)) {
      this.selectedUsers.delete(userId);
    } else {
      this.selectedUsers.add(userId);
    }
    this.updateSelectAllState();
  }

  /**
   * 更新全选状态
   */
  private updateSelectAllState(): void {
    this.allSelected = this.selectedUsers.size === this.dataSource.data.length;
  }

  /**
   * 检查是否选中
   */
  isSelected(userId: string): boolean {
    return this.selectedUsers.has(userId);
  }

  // ==================== 批量操作 ====================

  /**
   * 批量激活
   */
  bulkActivate(): void {
    if (this.selectedUsers.size === 0) return;
    this.performBulkAction('activate', '激活');
  }

  /**
   * 批量停用
   */
  bulkDeactivate(): void {
    if (this.selectedUsers.size === 0) return;
    this.performBulkAction('deactivate', '停用');
  }

  /**
   * 批量删除
   */
  bulkDelete(): void {
    if (this.selectedUsers.size === 0) return;
    if (confirm(`确定要删除选中的 ${this.selectedUsers.size} 个用户吗？此操作不可恢复。`)) {
      this.performBulkAction('delete', '删除');
    }
  }

  /**
   * 执行批量操作
   */
  private performBulkAction(
    action: 'activate' | 'deactivate' | 'suspend' | 'delete',
    actionName: string
  ): void {
    this.loading$.next(true);

    this.userService
      .bulkOperation({
        userIds: Array.from(this.selectedUsers),
        action,
      })
      .pipe(
        finalize(() => this.loading$.next(false)),
        catchError((err) => {
          alert(`${actionName}失败: ${err.message}`);
          return of(null);
        })
      )
      .subscribe((response) => {
        if (response) {
          alert(`${actionName}成功: ${response.successCount} 个用户`);
          this.selectedUsers.clear();
          this.allSelected = false;
          this.loadUserList();
          this.loadStatistics();
        }
      });
  }

  // ==================== 路由操作 ====================

  /**
   * 查看用户详情
   */
  viewUserDetail(userId: string): void {
    this.router.navigate(['/admin/users', userId]);
  }

  /**
   * 编辑用户
   */
  editUser(userId: string, event: Event): void {
    event.stopPropagation();
    this.router.navigate(['/admin/users', userId, 'edit']);
  }

  /**
   * 删除用户
   */
  deleteUser(userId: string, event: Event): void {
    event.stopPropagation();
    if (confirm('确定要删除此用户吗？此操作不可恢复。')) {
      this.loading$.next(true);
      this.userService
        .deleteUser(userId)
        .pipe(
          finalize(() => this.loading$.next(false)),
          catchError((err) => {
            alert(`删除失败: ${err.message}`);
            return of(null);
          })
        )
        .subscribe(() => {
          alert('删除成功');
          this.loadUserList();
          this.loadStatistics();
        });
    }
  }

  // ==================== 工具方法 ====================

  /**
   * 获取用户状态颜色
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
   * 获取用户类型标签
   */
  getUserTypeLabel(userType: string): string {
    const type = this.userTypes.find((t) => t.value === userType);
    return type ? type.label : userType;
  }

  /**
   * 格式化日期
   */
  formatDate(date: Date | string | undefined): string {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
