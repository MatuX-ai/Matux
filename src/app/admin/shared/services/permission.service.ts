import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

// 权限枚举
export enum Permission {
  // 用户管理权限
  VIEW_USERS = 'view_users',
  CREATE_USER = 'create_user',
  EDIT_USER = 'edit_user',
  DELETE_USER = 'delete_user',

  // 许可证管理权限
  VIEW_LICENSES = 'view_licenses',
  CREATE_LICENSE = 'create_license',
  EDIT_LICENSE = 'edit_license',
  REVOKE_LICENSE = 'revoke_license',

  // 订阅管理权限
  VIEW_SUBSCRIPTIONS = 'view_subscriptions',
  CREATE_SUBSCRIPTION = 'create_subscription',
  EDIT_SUBSCRIPTION = 'edit_subscription',
  CANCEL_SUBSCRIPTION = 'cancel_subscription',

  // 支付管理权限
  VIEW_PAYMENTS = 'view_payments',
  PROCESS_REFUND = 'process_refund',

  // AI服务权限
  VIEW_AI_USAGE = 'view_ai_usage',
  MANAGE_AI_MODELS = 'manage_ai_models',

  // 报表和导出权限
  VIEW_REPORTS = 'view_reports',
  EXPORT_DATA = 'export_data',
  EXPORT_FULL_DATA = 'export_full_data',

  // 系统管理权限
  SYSTEM_ADMIN = 'system_admin',
  MANAGE_ROLES = 'manage_roles',
  VIEW_AUDIT_LOGS = 'view_audit_logs',
}

// 角色枚举
export enum Role {
  ADMIN = 'admin',
  MANAGER = 'manager',
  ANALYST = 'analyst',
  SUPPORT = 'support',
  VIEWER = 'viewer',
}

// 用户信息接口
export interface UserInfo {
  id: string;
  username: string;
  email: string;
  roles: Role[];
  permissions: Permission[];
}

// 角色权限配置
interface RolePermissions {
  [key: string]: Permission[];
}

@Injectable({
  providedIn: 'root',
})
export class PermissionService {
  private currentUserSubject = new BehaviorSubject<UserInfo | null>(null);
  private rolePermissions: RolePermissions = {
    [Role.ADMIN]: [
      Permission.VIEW_USERS,
      Permission.CREATE_USER,
      Permission.EDIT_USER,
      Permission.DELETE_USER,
      Permission.VIEW_LICENSES,
      Permission.CREATE_LICENSE,
      Permission.EDIT_LICENSE,
      Permission.REVOKE_LICENSE,
      Permission.VIEW_SUBSCRIPTIONS,
      Permission.CREATE_SUBSCRIPTION,
      Permission.EDIT_SUBSCRIPTION,
      Permission.CANCEL_SUBSCRIPTION,
      Permission.VIEW_PAYMENTS,
      Permission.PROCESS_REFUND,
      Permission.VIEW_AI_USAGE,
      Permission.MANAGE_AI_MODELS,
      Permission.VIEW_REPORTS,
      Permission.EXPORT_DATA,
      Permission.EXPORT_FULL_DATA,
      Permission.SYSTEM_ADMIN,
      Permission.MANAGE_ROLES,
      Permission.VIEW_AUDIT_LOGS,
    ],

    [Role.MANAGER]: [
      Permission.VIEW_USERS,
      Permission.CREATE_USER,
      Permission.EDIT_USER,
      Permission.VIEW_LICENSES,
      Permission.CREATE_LICENSE,
      Permission.EDIT_LICENSE,
      Permission.VIEW_SUBSCRIPTIONS,
      Permission.CREATE_SUBSCRIPTION,
      Permission.EDIT_SUBSCRIPTION,
      Permission.VIEW_PAYMENTS,
      Permission.VIEW_AI_USAGE,
      Permission.VIEW_REPORTS,
      Permission.EXPORT_DATA,
    ],

    [Role.ANALYST]: [
      Permission.VIEW_USERS,
      Permission.VIEW_LICENSES,
      Permission.VIEW_SUBSCRIPTIONS,
      Permission.VIEW_AI_USAGE,
      Permission.VIEW_REPORTS,
      Permission.EXPORT_DATA,
    ],

    [Role.SUPPORT]: [
      Permission.VIEW_USERS,
      Permission.VIEW_LICENSES,
      Permission.VIEW_SUBSCRIPTIONS,
      Permission.VIEW_PAYMENTS,
    ],

    [Role.VIEWER]: [Permission.VIEW_USERS, Permission.VIEW_LICENSES, Permission.VIEW_SUBSCRIPTIONS],
  };

  constructor() {
    // 初始化当前用户（可以从localStorage或认证服务获取）
    this.initializeCurrentUser();
  }

  /**
   * 获取当前用户
   */
  getCurrentUser(): Observable<UserInfo | null> {
    return this.currentUserSubject.asObservable();
  }

  /**
   * 获取当前用户同步版本
   */
  getCurrentUserSync(): UserInfo | null {
    return this.currentUserSubject.value;
  }

  /**
   * 设置当前用户
   */
  setCurrentUser(userInfo: UserInfo): void {
    this.currentUserSubject.next(userInfo);
    // 保存到本地存储
    localStorage.setItem('currentUser', JSON.stringify(userInfo));
  }

  /**
   * 清除当前用户
   */
  clearCurrentUser(): void {
    this.currentUserSubject.next(null);
    localStorage.removeItem('currentUser');
  }

  /**
   * 检查是否有特定权限
   */
  hasPermission(permission: Permission): boolean {
    const user = this.getCurrentUserSync();
    if (!user) return false;

    // 管理员拥有所有权限
    if (user.roles.includes(Role.ADMIN)) return true;

    // 检查直接分配的权限
    if (user.permissions.includes(permission)) return true;

    // 检查角色权限
    return user.roles.some((role) => this.rolePermissions[role]?.includes(permission));
  }

  /**
   * 检查是否有任意一个权限
   */
  hasAnyPermission(permissions: Permission[]): boolean {
    return permissions.some((permission) => this.hasPermission(permission));
  }

  /**
   * 检查是否拥有所有权限
   */
  hasAllPermissions(permissions: Permission[]): boolean {
    return permissions.every((permission) => this.hasPermission(permission));
  }

  /**
   * 检查是否有特定角色
   */
  hasRole(role: Role): boolean {
    const user = this.getCurrentUserSync();
    return user?.roles.includes(role) || false;
  }

  /**
   * 检查是否有任意一个角色
   */
  hasAnyRole(roles: Role[]): boolean {
    return roles.some((role) => this.hasRole(role));
  }

  /**
   * 获取用户的所有权限（包括角色权限和个人权限）
   */
  getAllUserPermissions(): Permission[] {
    const user = this.getCurrentUserSync();
    if (!user) return [];

    const permissions = new Set<Permission>();

    // 添加个人权限
    user.permissions.forEach((permission) => permissions.add(permission));

    // 添加角色权限
    user.roles.forEach((role) => {
      const rolePerms = this.rolePermissions[role] || [];
      rolePerms.forEach((permission) => permissions.add(permission));
    });

    return Array.from(permissions);
  }

  /**
   * 获取用户可访问的菜单项
   */
  getAccessibleMenuItems(): MenuItem[] {
    const menuItems: MenuItem[] = [
      {
        id: 'dashboard',
        title: '仪表板',
        icon: 'dashboard',
        route: '/admin/dashboard',
        requiredPermission: Permission.VIEW_REPORTS,
      },
      {
        id: 'users',
        title: '用户管理',
        icon: 'people',
        route: '/admin/users',
        requiredPermission: Permission.VIEW_USERS,
      },
      {
        id: 'licenses',
        title: '许可证管理',
        icon: 'vpn_key',
        route: '/admin/licenses',
        requiredPermission: Permission.VIEW_LICENSES,
      },
      {
        id: 'subscriptions',
        title: '订阅管理',
        icon: 'credit_card',
        route: '/admin/subscriptions',
        requiredPermission: Permission.VIEW_SUBSCRIPTIONS,
      },
      {
        id: 'payments',
        title: '支付管理',
        icon: 'payment',
        route: '/admin/payments',
        requiredPermission: Permission.VIEW_PAYMENTS,
      },
      {
        id: 'ai',
        title: 'AI服务',
        icon: 'auto_awesome',
        route: '/admin/ai',
        requiredPermission: Permission.VIEW_AI_USAGE,
      },
      {
        id: 'reports',
        title: '报表中心',
        icon: 'assessment',
        route: '/admin/reports',
        requiredPermission: Permission.VIEW_REPORTS,
      },
      {
        id: 'system',
        title: '系统管理',
        icon: 'settings',
        route: '/admin/system',
        requiredPermission: Permission.SYSTEM_ADMIN,
      },
    ];

    return menuItems.filter((item) => this.hasPermission(item.requiredPermission));
  }

  /**
   * 创建临时权限上下文（用于临时提升权限）
   */
  withTemporaryPermissions<T>(permissions: Permission[], callback: () => T): T {
    const user = this.getCurrentUserSync();
    if (!user) {
      throw new Error('无用户登录');
    }

    // 保存原始权限
    const originalPermissions = [...user.permissions];

    try {
      // 添加临时权限
      permissions.forEach((permission) => {
        if (!user.permissions.includes(permission)) {
          user.permissions.push(permission);
        }
      });

      // 更新用户信息
      this.setCurrentUser(user);

      // 执行回调
      return callback();
    } finally {
      // 恢复原始权限
      user.permissions = originalPermissions;
      this.setCurrentUser(user);
    }
  }

  /**
   * 初始化当前用户
   */
  private initializeCurrentUser(): void {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
      try {
        const userInfo: UserInfo = JSON.parse(storedUser);
        this.currentUserSubject.next(userInfo);
      } catch (error) {
        localStorage.removeItem('currentUser');
      }
    } else {
      // 设置默认管理员用户（仅用于演示）
      const defaultUser: UserInfo = {
        id: 'admin-user',
        username: 'admin',
        email: 'admin@example.com',
        roles: [Role.ADMIN],
        permissions: [],
      };
      this.setCurrentUser(defaultUser);
    }
  }
}

// 菜单项接口
export interface MenuItem {
  id: string;
  title: string;
  icon: string;
  route: string;
  requiredPermission: Permission;
}
