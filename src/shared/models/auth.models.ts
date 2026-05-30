/**
 * 用户认证相关数据模型
 * 统一账号体系 - 支持手机号登录/注册
 */

// 基本用户信息接口
export interface User {
  id: string;
  email: string;
  username?: string;
  phone?: string; // 手机号（统一账号主登录凭证）
  avatar?: string;
  userType?: string; // 用户类型: student, parent, teacher, admin, etc.
  orgIds?: number[]; // 用户所属组织ID列表
  guardianOf?: WardInfo[]; // 家长绑定的孩子列表
  createdAt: Date;
  updatedAt: Date;
}

// 被监护人（孩子）信息
export interface WardInfo {
  student_id: number;
  student_name: string;
  student_phone?: string;
  relationship?: string;
  is_primary: boolean;
}

// 登录请求参数
export interface LoginRequest {
  email: string;
  password: string;
}

// 手机号登录请求
export interface PhoneLoginRequest {
  phone: string;
  password: string;
}

// 手机号注册请求
export interface PhoneRegisterRequest {
  phone: string;
  password: string;
  username?: string;
  role?: string; // student / parent / teacher
}

// 注册请求参数
export interface RegisterRequest {
  email: string;
  password: string;
  username?: string;
  grade?: string; // 年级信息
  userType?: string; // 用户类型: student, parent, teacher, org_admin, school_admin, education_bureau
  userTypeGroup?: string; // 用户组: personal, org, edu
  organizationName?: string; // 机构名称
  inviteCode?: string; // 邀请码
  realName?: string; // 真实姓名
  phone?: string; // 电话
}

// 认证响应
export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

// 统一认证令牌响应（匹配后端 /api/v1/unified-auth）
export interface UnifiedTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    email?: string;
    phone?: string;
    role: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at?: string;
    updated_at?: string;
  };
}

// 家长绑定学生请求
export interface BindChildRequest {
  student_phone: string;
  relationship?: string;
  is_primary?: boolean;
}

// JWT载荷
export interface JwtPayload {
  userId: string;
  email: string;
  exp: number;
  iat: number;
}

// OAuth提供商类型
export type OAuthProvider = 'github' | 'google' | 'microsoft' | 'wechat' | 'qq';

// OAuth状态管理
export interface OAuthState {
  provider: OAuthProvider;
  redirectUrl?: string;
  state: string;
}

// 微信特有配置
export interface WeChatAuthConfig {
  appId: string;
  secret?: string;
  scope?: 'snsapi_login' | 'snsapi_userinfo';
  state?: string;
}

// QQ特有配置
export interface QQAuthConfig {
  appId: string;
  secret?: string;
  scope?: string;
  state?: string;
}

// 社交媒体用户信息
export interface SocialUserInfo {
  provider: OAuthProvider;
  openid: string;
  nickname?: string;
  avatar?: string;
  gender?: string;
  unionid?: string; // 微信UnionID
  accessToken?: string;
  refreshToken?: string;
  expiresIn?: number;
}
