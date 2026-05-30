/**
 * 用户管理相关数据模型
 */

// 用户列表查询参数
export interface UserListQuery {
  page: number;
  pageSize: number;
  search?: string;
  userType?: string;
  status?: UserStatus;
  role?: string;
  organizationId?: number;
  createdAfter?: Date;
  createdBefore?: Date;
  sortBy?: 'name' | 'email' | 'createdAt' | 'lastLogin';
  sortOrder?: 'asc' | 'desc';
}

// 用户状态枚举
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
}

// 用户角色枚举
export enum UserRole {
  ADMIN = 'admin',
  TEACHER = 'teacher',
  STUDENT = 'student',
  PARENT = 'parent',
  ORG_ADMIN = 'org_admin',
  SCHOOL_ADMIN = 'school_admin',
  EDUCATION_BUREAU = 'education_bureau',
}

// 扩展的用户信息接口
export interface AdminUser {
  id: string;
  email: string;
  username: string;
  realName?: string;
  phone?: string;
  avatar?: string;
  userType: string;
  userTypeGroup: string;
  status: UserStatus;
  roles: UserRole[];
  organization?: UserOrganization;
  subscription?: UserSubscription;
  createdAt: Date;
  updatedAt: Date;
  lastLoginAt?: Date;
  loginCount: number;
  metadata?: Record<string, any>;
}

// 用户组织信息
export interface UserOrganization {
  id: number;
  name: string;
  type: string;
  role: string;
  joinedAt: Date;
}

// 用户订阅信息
export interface UserSubscription {
  planName: string;
  status: string;
  startDate: Date;
  endDate?: Date;
  features: string[];
}

// 分页用户列表响应
export interface PaginatedUserList {
  items: AdminUser[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// 批量操作响应
export interface BulkOperationResponse {
  successCount: number;
  failureCount: number;
  total: number;
  errors: Array<{
    userId: string;
    error: string;
  }>;
}

// 批量操作请求
export interface BulkUserOperation {
  userIds: string[];
  action: 'activate' | 'deactivate' | 'suspend' | 'delete' | 'resetPassword' | 'assignRole';
  data?: Record<string, any>;
}

// 用户统计信息
export interface UserStatistics {
  totalUsers: number;
  activeUsers: number;
  newUsersToday: number;
  newUsersThisWeek: number;
  newUsersThisMonth: number;
  usersByType: Record<string, number>;
  usersByStatus: Record<UserStatus, number>;
  usersByRole: Record<UserRole, number>;
  topOrganizations: Array<{
    id: number;
    name: string;
    userCount: number;
  }>;
  loginTrend: Array<{
    date: string;
    loginCount: number;
    activeUsers: number;
  }>;
}

// 用户详情扩展信息
export interface UserDetail extends AdminUser {
  // 学习统计
  learningStats?: {
    totalCourses: number;
    completedCourses: number;
    totalHours: number;
    avgScore: number;
    lastActivityAt?: Date;
  };

  // 机构关联
  organizations?: UserOrganization[];

  // 权限信息
  permissions?: string[];

  // 设备信息
  devices?: Array<{
    id: string;
    type: string;
    lastUsed: Date;
    ipAddress?: string;
  }>;

  // 活动日志
  recentActivities?: Array<{
    id: number;
    type: string;
    description: string;
    timestamp: Date;
    ipAddress?: string;
    userAgent?: string;
  }>;
}

// 用户导入模板
export interface UserImportTemplate {
  fields: Array<{
    name: string;
    displayName: string;
    required: boolean;
    type: 'string' | 'email' | 'number' | 'date' | 'boolean' | 'enum';
    validation?: {
      pattern?: string;
      min?: number;
      max?: number;
      enumValues?: string[];
    };
  }>;

  exampleData: Array<Record<string, any>>;

  importRules: {
    duplicateEmailAction: 'skip' | 'update' | 'error';
    requiredFields: string[];
    autoGeneratePassword: boolean;
    sendWelcomeEmail: boolean;
  };
}

// 用户过滤选项
export interface UserFilterOptions {
  userTypes: Array<{ value: string; label: string; count: number }>;
  roles: Array<{ value: UserRole; label: string; count: number }>;
  statuses: Array<{ value: UserStatus; label: string; count: number }>;
  organizations: Array<{ id: number; name: string; count: number }>;
  dateRanges: Array<{ value: string; label: string }>;
}

// 用户操作日志
export interface UserOperationLog {
  id: number;
  userId: string;
  operatorId: string;
  operationType: string;
  details: Record<string, any>;
  timestamp: Date;
  ipAddress?: string;
}
