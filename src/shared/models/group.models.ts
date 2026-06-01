/**
 * 用户组/班级相关数据模型
 */

// 用户类型枚举
export enum UserType {
  STUDENT = 'student', // 学生
  PARENT = 'parent', // 家长
  TEACHER = 'teacher', // 教师
}

// 用户类型分组
export enum UserTypeGroup {
  PERSONAL = 'personal', // 个人用户
  ORGANIZATION = 'org', // 机构用户
  EDUCATION = 'edu', // 教育机构
}

// 组/班级类型
export enum GroupType {
  FAMILY = 'family', // 家庭组
  CLASS = 'class', // 班级
  ORGANIZATION = 'org', // 机构
  SCHOOL = 'school', // 学校
  DEPARTMENT = 'dept', // 教育局/部门
}

// 组成员角色
export enum GroupMemberRole {
  OWNER = 'owner', // 创建者/所有者
  ADMIN = 'admin', // 管理员
  TEACHER = 'teacher', // 教师/老师
  MEMBER = 'member', // 普通成员
  STUDENT = 'student', // 学生
  PARENT = 'parent', // 家长
}

// 用户接口扩展
export interface UserProfile {
  id: string;
  email: string;
  username?: string;
  avatar?: string;
  userType: UserType;
  userTypeGroup: UserTypeGroup;

  // 组织关联
  organizationId?: string;
  organizationName?: string;

  // 班级/组关联
  groupId?: string;
  groupName?: string;

  // 家庭关联
  parentId?: string; // 家长ID（学生关联）
  childrenIds?: string[]; // 孩子ID列表（家长关联）

  // 个人信息
  realName?: string; // 真实姓名
  phone?: string; // 电话
  grade?: string; // 年级（学生）
  schoolName?: string; // 学校名称

  // 机构信息
  orgRole?: string; // 在机构中的职位
  department?: string; // 部门

  createdAt: Date;
  updatedAt: Date;
}

// 组/班级接口
export interface Group {
  id: string;
  name: string;
  description?: string;
  type: GroupType;

  // 所属上级组织
  parentId?: string; // 上级组织ID
  ownerId: string; // 创建者ID

  // 组织信息
  organizationCode?: string; // 组织代码
  regionCode?: string; // 区域编码（教育局用）

  // 状态
  isActive: boolean;
  isVerified: boolean; // 是否审核通过

  // 统计
  memberCount: number;
  maxMembers?: number; // 最大成员数

  createdAt: Date;
  updatedAt: Date;
}

// 组成员接口
export interface GroupMember {
  id: string;
  groupId: string;
  userId: string;
  role: GroupMemberRole;

  // 关联信息
  studentId?: string; // 学生ID（家长关联）
  teacherId?: string; // 教师ID（机构）

  // 状态
  status: 'active' | 'pending' | 'invited';
  joinedAt: Date;

  // 邀请信息
  invitedBy?: string;
  inviteCode?: string;
  inviteExpiredAt?: Date;
}

// 邀请入组请求
export interface GroupInvitation {
  id: string;
  groupId: string;
  inviterId: string; // 邀请人
  inviteeEmail?: string; // 被邀请人邮箱
  inviteeId?: string; // 被邀请人ID（如果已注册）

  role: GroupMemberRole;
  message?: string;

  status: 'pending' | 'accepted' | 'rejected' | 'expired';
  createdAt: Date;
  acceptedAt?: Date;
  expiredAt: Date;
}

// 用户类型配置
export const USER_TYPE_CONFIG: Record<
  UserType,
  {
    label: string;
    group: UserTypeGroup;
    canCreateGroup: boolean;
    canInvite: boolean;
    defaultRoleInGroup: GroupMemberRole;
  }
> = {
  [UserType.STUDENT]: {
    label: '学生',
    group: UserTypeGroup.PERSONAL,
    canCreateGroup: false,
    canInvite: false,
    defaultRoleInGroup: GroupMemberRole.STUDENT,
  },
  [UserType.PARENT]: {
    label: '家长',
    group: UserTypeGroup.PERSONAL,
    canCreateGroup: true,
    canInvite: true,
    defaultRoleInGroup: GroupMemberRole.OWNER,
  },
  [UserType.TEACHER]: {
    label: '教师',
    group: UserTypeGroup.ORGANIZATION,
    canCreateGroup: true,
    canInvite: true,
    defaultRoleInGroup: GroupMemberRole.TEACHER,
  },
};

// 用户组类型配置
export const GROUP_TYPE_CONFIG: Record<
  GroupType,
  {
    label: string;
    requiresVerification: boolean;
    maxMembers: number;
  }
> = {
  [GroupType.FAMILY]: {
    label: '家庭组',
    requiresVerification: false,
    maxMembers: 10,
  },
  [GroupType.CLASS]: {
    label: '班级',
    requiresVerification: false,
    maxMembers: 60,
  },
  [GroupType.ORGANIZATION]: {
    label: '机构',
    requiresVerification: true,
    maxMembers: 1000,
  },
  [GroupType.SCHOOL]: {
    label: '学校',
    requiresVerification: true,
    maxMembers: 10000,
  },
  [GroupType.DEPARTMENT]: {
    label: '教育局/部门',
    requiresVerification: true,
    maxMembers: -1, // 无限制
  },
};
