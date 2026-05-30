/**
 * 用户管理服务
 * 提供用户管理相关API调用封装，包括用户列表、详情、CRUD操作、批量操作等
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, delay } from 'rxjs/operators';

import {
  AdminUser,
  BulkOperationResponse,
  BulkUserOperation,
  PaginatedUserList,
  UserDetail,
  UserFilterOptions,
  UserListQuery,
  UserRole,
  UserStatistics,
  UserStatus,
} from '../models/user-management.models';

@Injectable({
  providedIn: 'root',
})
export class UserManagementService {
  private readonly API_BASE = '/api/v1';

  constructor(private http: HttpClient) {}

  // ==================== 用户列表查询 ====================

  /**
   * 获取用户列表（支持分页、搜索、筛选、排序）
   */
  getUserList(query: UserListQuery): Observable<PaginatedUserList> {
    let params = new HttpParams()
      .set('page', query.page.toString())
      .set('pageSize', query.pageSize.toString());

    if (query.search) {
      params = params.set('search', query.search);
    }
    if (query.userType) {
      params = params.set('userType', query.userType);
    }
    if (query.status) {
      params = params.set('status', query.status);
    }
    if (query.role) {
      params = params.set('role', query.role);
    }
    if (query.organizationId) {
      params = params.set('organizationId', query.organizationId.toString());
    }
    if (query.sortBy) {
      params = params.set('sortBy', query.sortBy);
    }
    if (query.sortOrder) {
      params = params.set('sortOrder', query.sortOrder);
    }
    if (query.createdAfter) {
      params = params.set('createdAfter', query.createdAfter.toISOString());
    }
    if (query.createdBefore) {
      params = params.set('createdBefore', query.createdBefore.toISOString());
    }

    return this.http.get<PaginatedUserList>(`${this.API_BASE}/admin/users`, { params }).pipe(
      catchError((err) => {
        console.error('获取用户列表失败，回退到模拟数据:', err);
        return this.getSimulatedUserList(query);
      })
    );
  }

  /**
   * 获取用户详情
   */
  getUserDetail(userId: string): Observable<UserDetail> {
    return this.http.get<UserDetail>(`${this.API_BASE}/admin/users/${userId}`).pipe(
      catchError((err) => {
        console.error('获取用户详情失败，回退到模拟数据:', err);
        return this.getSimulatedUserDetail(userId);
      })
    );
  }

  // ==================== 用户CRUD操作 ====================

  /**
   * 创建用户
   */
  createUser(userData: Partial<AdminUser>): Observable<AdminUser> {
    return this.http.post<AdminUser>(`${this.API_BASE}/admin/users`, userData).pipe(
      catchError((err) => {
        console.error('创建用户失败:', err);
        throw err;
      })
    );
  }

  /**
   * 更新用户
   */
  updateUser(userId: string, userData: Partial<AdminUser>): Observable<AdminUser> {
    return this.http.put<AdminUser>(`${this.API_BASE}/admin/users/${userId}`, userData).pipe(
      catchError((err) => {
        console.error('更新用户失败:', err);
        throw err;
      })
    );
  }

  /**
   * 删除用户
   */
  deleteUser(userId: string): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/admin/users/${userId}`).pipe(
      catchError((err) => {
        console.error('删除用户失败:', err);
        throw err;
      })
    );
  }

  /**
   * 更新用户状态
   */
  updateUserStatus(userId: string, status: UserStatus): Observable<AdminUser> {
    return this.http
      .patch<AdminUser>(`${this.API_BASE}/admin/users/${userId}/status`, { status })
      .pipe(
        catchError((err) => {
          console.error('更新用户状态失败:', err);
          throw err;
        })
      );
  }

  // ==================== 批量操作 ====================

  /**
   * 批量操作用户
   */
  bulkOperation(operation: BulkUserOperation): Observable<BulkOperationResponse> {
    return this.http
      .post<BulkOperationResponse>(`${this.API_BASE}/admin/users/bulk`, operation)
      .pipe(
        catchError((err) => {
          console.error('批量操作失败:', err);
          throw err;
        })
      );
  }

  /**
   * 批量导入用户
   */
  bulkImportUsers(file: File): Observable<BulkOperationResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http
      .post<BulkOperationResponse>(`${this.API_BASE}/admin/users/import`, formData)
      .pipe(
        catchError((err) => {
          console.error('批量导入失败:', err);
          throw err;
        })
      );
  }

  /**
   * 批量导出用户
   */
  exportUsers(query: UserListQuery): Observable<Blob> {
    let params = new HttpParams()
      .set('page', query.page.toString())
      .set('pageSize', query.pageSize.toString());

    if (query.search) {
      params = params.set('search', query.search);
    }
    if (query.userType) {
      params = params.set('userType', query.userType);
    }
    if (query.status) {
      params = params.set('status', query.status);
    }
    if (query.role) {
      params = params.set('role', query.role);
    }

    return this.http
      .get(`${this.API_BASE}/admin/users/export`, {
        params,
        responseType: 'blob',
      })
      .pipe(
        catchError((err) => {
          console.error('导出用户失败:', err);
          throw err;
        })
      );
  }

  // ==================== 用户统计 ====================

  /**
   * 获取用户统计信息
   */
  getUserStatistics(): Observable<UserStatistics> {
    return this.http.get<UserStatistics>(`${this.API_BASE}/admin/users/statistics`).pipe(
      catchError((err) => {
        console.error('获取用户统计失败，回退到模拟数据:', err);
        return this.getSimulatedUserStatistics();
      })
    );
  }

  /**
   * 获取用户过滤选项
   */
  getFilterOptions(): Observable<UserFilterOptions> {
    return this.http.get<UserFilterOptions>(`${this.API_BASE}/admin/users/filter-options`).pipe(
      catchError((err) => {
        console.error('获取过滤选项失败，回退到模拟数据:', err);
        return this.getSimulatedFilterOptions();
      })
    );
  }

  // ==================== 模拟数据方法（向后兼容） ====================

  /**
   * 生成模拟用户列表
   */
  private getSimulatedUserList(query: UserListQuery): Observable<PaginatedUserList> {
    const mockUsers = this.generateMockUsers(50);
    let filteredUsers = [...mockUsers];

    // 搜索过滤
    if (query.search) {
      const searchLower = query.search.toLowerCase();
      const searchTerm = query.search || '';
      filteredUsers = filteredUsers.filter(
        (user) =>
          user.email.toLowerCase().includes(searchLower) ||
          user.username.toLowerCase().includes(searchLower) ||
          user.realName?.toLowerCase().includes(searchLower) ||
          user.phone?.includes(searchTerm)
      );
    }

    // 用户类型过滤
    if (query.userType) {
      filteredUsers = filteredUsers.filter((user) => user.userType === query.userType);
    }

    // 状态过滤
    if (query.status) {
      filteredUsers = filteredUsers.filter((user) => user.status === query.status);
    }

    // 角色过滤
    if (query.role) {
      filteredUsers = filteredUsers.filter((user) => user.roles.includes(query.role as UserRole));
    }

    // 排序
    if (query.sortBy) {
      filteredUsers.sort((a, b) => {
        const aVal = a[query.sortBy as keyof AdminUser];
        const bVal = b[query.sortBy as keyof AdminUser];
        if (aVal === bVal) return 0;
        if (aVal === undefined || aVal === null) return 1;
        if (bVal === undefined || bVal === null) return -1;
        const comparison = aVal < bVal ? -1 : 1;
        return query.sortOrder === 'desc' ? -comparison : comparison;
      });
    }

    // 分页
    const total = filteredUsers.length;
    const totalPages = Math.ceil(total / query.pageSize);
    const startIndex = (query.page - 1) * query.pageSize;
    const items = filteredUsers.slice(startIndex, startIndex + query.pageSize);

    return of({
      items,
      total,
      page: query.page,
      pageSize: query.pageSize,
      totalPages,
      hasNext: query.page < totalPages,
      hasPrevious: query.page > 1,
    }).pipe(delay(300));
  }

  /**
   * 生成模拟用户详情
   */
  private getSimulatedUserDetail(userId: string): Observable<UserDetail> {
    const mockUser: AdminUser = {
      id: userId,
      email: 'user@example.com',
      username: 'user123',
      realName: '张三',
      phone: '13800138000',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + userId,
      userType: 'teacher',
      userTypeGroup: 'educator',
      status: UserStatus.ACTIVE,
      roles: [UserRole.TEACHER],
      organization: {
        id: 1,
        name: '北京市第一中学',
        type: 'school',
        role: '教师',
        joinedAt: new Date('2023-09-01'),
      },
      subscription: {
        planName: '专业版',
        status: 'active',
        startDate: new Date('2024-01-01'),
        features: ['all_courses', 'analytics', 'priority_support'],
      },
      createdAt: new Date('2023-09-01'),
      updatedAt: new Date(),
      lastLoginAt: new Date(),
      loginCount: 150,
      metadata: {},
    };

    const userDetail: UserDetail = {
      ...mockUser,
      learningStats: {
        totalCourses: 12,
        completedCourses: 8,
        totalHours: 256,
        avgScore: 92.5,
        lastActivityAt: new Date(),
      },
      organizations: [mockUser.organization!],
      permissions: ['course:read', 'course:write', 'student:read', 'student:manage'],
      devices: [
        { id: 'device1', type: 'desktop', lastUsed: new Date(), ipAddress: '192.168.1.100' },
        {
          id: 'device2',
          type: 'mobile',
          lastUsed: new Date(Date.now() - 86400000),
          ipAddress: '192.168.1.101',
        },
      ],
      recentActivities: [
        {
          id: 1,
          type: 'login',
          description: '用户登录系统',
          timestamp: new Date(),
          ipAddress: '192.168.1.100',
        },
        {
          id: 2,
          type: 'course_create',
          description: '创建新课程',
          timestamp: new Date(Date.now() - 3600000),
        },
        {
          id: 3,
          type: 'grade_update',
          description: '更新学生成绩',
          timestamp: new Date(Date.now() - 7200000),
        },
      ],
    };

    return of(userDetail).pipe(delay(200));
  }

  /**
   * 生成模拟用户统计数据
   */
  private getSimulatedUserStatistics(): Observable<UserStatistics> {
    return of({
      totalUsers: 1250,
      activeUsers: 980,
      newUsersToday: 15,
      newUsersThisWeek: 85,
      newUsersThisMonth: 320,
      usersByType: {
        teacher: 120,
        student: 850,
        parent: 180,
        org_admin: 50,
        school_admin: 30,
        education_bureau: 20,
      },
      usersByStatus: {
        [UserStatus.ACTIVE]: 980,
        [UserStatus.INACTIVE]: 150,
        [UserStatus.SUSPENDED]: 45,
        [UserStatus.PENDING]: 75,
      },
      usersByRole: {
        [UserRole.TEACHER]: 120,
        [UserRole.STUDENT]: 850,
        [UserRole.PARENT]: 180,
        [UserRole.ORG_ADMIN]: 50,
        [UserRole.SCHOOL_ADMIN]: 30,
        [UserRole.EDUCATION_BUREAU]: 20,
        [UserRole.ADMIN]: 5,
      },
      topOrganizations: [
        { id: 1, name: '北京市第一中学', userCount: 280 },
        { id: 2, name: '上海市实验中学', userCount: 245 },
        { id: 3, name: '广州市外国语学校', userCount: 198 },
      ],
      loginTrend: [
        { date: '2026-03-16', loginCount: 320, activeUsers: 280 },
        { date: '2026-03-17', loginCount: 345, activeUsers: 310 },
        { date: '2026-03-18', loginCount: 380, activeUsers: 340 },
        { date: '2026-03-19', loginCount: 365, activeUsers: 325 },
        { date: '2026-03-20', loginCount: 410, activeUsers: 370 },
        { date: '2026-03-21', loginCount: 425, activeUsers: 385 },
        { date: '2026-03-22', loginCount: 390, activeUsers: 350 },
      ],
    }).pipe(delay(300));
  }

  /**
   * 生成模拟过滤选项
   */
  private getSimulatedFilterOptions(): Observable<UserFilterOptions> {
    return of({
      userTypes: [
        { value: 'teacher', label: '教师', count: 120 },
        { value: 'student', label: '学生', count: 850 },
        { value: 'parent', label: '家长', count: 180 },
        { value: 'org_admin', label: '机构管理员', count: 50 },
        { value: 'school_admin', label: '学校管理员', count: 30 },
        { value: 'education_bureau', label: '教育局', count: 20 },
      ],
      roles: [
        { value: UserRole.TEACHER, label: '教师', count: 120 },
        { value: UserRole.STUDENT, label: '学生', count: 850 },
        { value: UserRole.PARENT, label: '家长', count: 180 },
        { value: UserRole.ORG_ADMIN, label: '机构管理员', count: 50 },
        { value: UserRole.SCHOOL_ADMIN, label: '学校管理员', count: 30 },
        { value: UserRole.EDUCATION_BUREAU, label: '教育局', count: 20 },
      ],
      statuses: [
        { value: UserStatus.ACTIVE, label: '活跃', count: 980 },
        { value: UserStatus.INACTIVE, label: '未激活', count: 150 },
        { value: UserStatus.SUSPENDED, label: '已停用', count: 45 },
        { value: UserStatus.PENDING, label: '待审核', count: 75 },
      ],
      organizations: [
        { id: 1, name: '北京市第一中学', count: 280 },
        { id: 2, name: '上海市实验中学', count: 245 },
        { id: 3, name: '广州市外国语学校', count: 198 },
      ],
      dateRanges: [
        { value: 'today', label: '今天' },
        { value: 'this_week', label: '本周' },
        { value: 'this_month', label: '本月' },
        { value: 'this_year', label: '今年' },
        { value: 'custom', label: '自定义' },
      ],
    }).pipe(delay(200));
  }

  /**
   * 生成模拟用户数据
   */
  private generateMockUsers(count: number): AdminUser[] {
    const userTypes = [
      'teacher',
      'student',
      'parent',
      'org_admin',
      'school_admin',
      'education_bureau',
    ];
    const statusValues = [
      UserStatus.ACTIVE,
      UserStatus.INACTIVE,
      UserStatus.SUSPENDED,
      UserStatus.PENDING,
    ];
    const roleMap: Record<string, UserRole[]> = {
      teacher: [UserRole.TEACHER],
      student: [UserRole.STUDENT],
      parent: [UserRole.PARENT],
      org_admin: [UserRole.ORG_ADMIN],
      school_admin: [UserRole.SCHOOL_ADMIN],
      education_bureau: [UserRole.EDUCATION_BUREAU],
    };
    const orgNames = [
      '北京市第一中学',
      '上海市实验中学',
      '广州市外国语学校',
      '深圳市外国语学校',
      '杭州市第二中学',
    ];

    return Array.from({ length: count }, (_, i) => {
      const userType = userTypes[i % userTypes.length];
      const status = statusValues[i % statusValues.length];
      const orgName = orgNames[i % orgNames.length];

      return {
        id: `user_${i + 1}`,
        email: `user${i + 1}@example.com`,
        username: `user${i + 1}`,
        realName: `用户${i + 1}`,
        phone: `138${String(i).padStart(8, '0')}`,
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=user${i + 1}`,
        userType,
        userTypeGroup: userType === 'student' ? 'learner' : 'educator',
        status,
        roles: roleMap[userType],
        organization: {
          id: (i % 5) + 1,
          name: orgName,
          type: 'school',
          role: userType === 'student' ? '学生' : '教师',
          joinedAt: new Date('2023-09-01'),
        },
        subscription: {
          planName: '专业版',
          status: 'active',
          startDate: new Date('2024-01-01'),
          features: ['all_courses', 'analytics', 'priority_support'],
        },
        createdAt: new Date('2023-09-01'),
        updatedAt: new Date(),
        lastLoginAt: new Date(),
        loginCount: Math.floor(Math.random() * 200),
        metadata: {},
      };
    });
  }
}
