/**
 * 用户组/班级相关数据模型
 *
 * MatuX 仅有学生角色。
 * 教师/家长/机构/学校等类型已解耦至 OpenMTEduInst 项目。
 */

// 用户类型枚举（MatuX 仅有学生角色）
export enum UserType {
  STUDENT = 'student', // 学生
}

// 用户类型分组
export enum UserTypeGroup {
  PERSONAL = 'personal', // 个人用户
}

// 组/班级类型
export enum GroupType {
  CLASS = 'class', // 班级
}

// 组成员角色
export enum GroupMemberRole {
  MEMBER = 'member', // 普通成员
  STUDENT = 'student', // 学生
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
