/**
 * 用户管理相关的数据模型
 */

/**
 * 用户角色
 */
export type UserRole = 'admin' | 'teacher' | 'student' | 'parent';

/**
 * 用户状态
 */
export type UserStatus = 'active' | 'pending' | 'suspended' | 'inactive';

/**
 * 用户详情接口
 */
export interface UserDetail {
  /** 用户 ID */
  id: number;

  /** 姓名 */
  name: string;

  /** 邮箱 */
  email: string;

  /** 手机号 */
  phone?: string;

  /** 头像 URL */
  avatar_url?: string;

  /** 用户角色 */
  role: UserRole;

  /** 用户状态 */
  status: UserStatus;

  /** 持有的许可证数量 */
  license_count?: number;

  /** 最后活跃时间 */
  last_active_at?: string;

  /** 创建时间 */
  created_at?: string;
}

/**
 * 用户创建请求
 */
export interface CreateUserRequest {
  /** 姓名 */
  name: string;

  /** 邮箱 */
  email: string;

  /** 手机号（可选） */
  phone?: string;

  /** 角色 */
  role: UserRole;

  /** 初始密码（可选，不填则发送激活邮件） */
  password?: string;

  /** 备注（可选） */
  notes?: string;
}

/**
 * 用户更新请求
 */
export interface UpdateUserRequest {
  /** 姓名（可选） */
  name?: string;

  /** 邮箱（可选） */
  email?: string;

  /** 手机号（可选） */
  phone?: string;

  /** 角色（可选） */
  role?: UserRole;

  /** 头像 URL（可选） */
  avatar_url?: string;

  /** 备注（可选） */
  notes?: string;
}

/**
 * 批量导入用户结果
 */
export interface ImportUsersResult {
  /** 成功导入数量 */
  successCount: number;

  /** 失败数量 */
  failureCount: number;

  /** 错误详情 */
  errors: Array<{
    row: number;
    email: string;
    reason: string;
  }>;
}
