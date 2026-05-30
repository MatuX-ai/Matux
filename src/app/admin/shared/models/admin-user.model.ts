/**
 * 管理员用户接口定义
 */
export interface AdminUser {
  /** 用户 ID */
  id: number;

  /** 用户名 */
  username: string;

  /** 邮箱地址 */
  email: string;

  /** 角色标识 */
  role: string;

  /** 权限列表（可选） */
  permissions?: string[];

  /** 创建时间（可选） */
  created_at?: string;
}
