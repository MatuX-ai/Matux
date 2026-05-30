import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { User } from '../models/auth.models';
import {
  Group,
  GroupInvitation,
  GroupMember,
  GroupMemberRole,
  GroupType,
  USER_TYPE_CONFIG,
  UserType,
} from '../models/group.models';

@Injectable({
  providedIn: 'root',
})
export class GroupService {
  private readonly API_BASE_URL = '/api/groups';

  // 当前用户所在组
  private currentGroupSubject = new BehaviorSubject<Group | null>(null);
  public currentGroup$ = this.currentGroupSubject.asObservable();

  // 当前用户的组成员信息
  private currentMemberSubject = new BehaviorSubject<GroupMember | null>(null);
  public currentMember$ = this.currentMemberSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * 创建组/班级
   */
  createGroup(groupData: Partial<Group>): Observable<Group> {
    return this.http.post<Group>(`${this.API_BASE_URL}`, groupData).pipe(
      tap((group) => {
        this.currentGroupSubject.next(group);
      })
    );
  }

  /**
   * 获取用户所在的所有组
   */
  getUserGroups(userId: string): Observable<Group[]> {
    return this.http.get<Group[]>(`${this.API_BASE_URL}/user/${userId}`);
  }

  /**
   * 获取组详情
   */
  getGroup(groupId: string): Observable<Group> {
    return this.http.get<Group>(`${this.API_BASE_URL}/${groupId}`);
  }

  /**
   * 获取组成员列表
   */
  getGroupMembers(groupId: string): Observable<GroupMember[]> {
    return this.http.get<GroupMember[]>(`${this.API_BASE_URL}/${groupId}/members`);
  }

  /**
   * 添加组成员
   */
  addMember(groupId: string, memberData: Partial<GroupMember>): Observable<GroupMember> {
    return this.http.post<GroupMember>(`${this.API_BASE_URL}/${groupId}/members`, memberData);
  }

  /**
   * 移除组成员
   */
  removeMember(groupId: string, memberId: string): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE_URL}/${groupId}/members/${memberId}`);
  }

  /**
   * 更新组成员角色
   */
  updateMemberRole(
    groupId: string,
    memberId: string,
    role: GroupMemberRole
  ): Observable<GroupMember> {
    return this.http.patch<GroupMember>(`${this.API_BASE_URL}/${groupId}/members/${memberId}`, {
      role,
    });
  }

  /**
   * 邀请用户加入组
   */
  inviteToGroup(
    groupId: string,
    invitation: Partial<GroupInvitation>
  ): Observable<GroupInvitation> {
    return this.http.post<GroupInvitation>(
      `${this.API_BASE_URL}/${groupId}/invitations`,
      invitation
    );
  }

  /**
   * 接受邀请
   */
  acceptInvitation(invitationId: string): Observable<GroupMember> {
    return this.http.post<GroupMember>(
      `${this.API_BASE_URL}/invitations/${invitationId}/accept`,
      {}
    );
  }

  /**
   * 拒绝邀请
   */
  rejectInvitation(invitationId: string): Observable<void> {
    return this.http.post<void>(`${this.API_BASE_URL}/invitations/${invitationId}/reject`, {});
  }

  /**
   * 获取用户的待处理邀请
   */
  getPendingInvitations(userId: string): Observable<GroupInvitation[]> {
    return this.http.get<GroupInvitation[]>(`${this.API_BASE_URL}/invitations/user/${userId}`);
  }

  /**
   * 家长关联孩子
   */
  linkChild(parentId: string, childId: string): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(`${this.API_BASE_URL}/family/link-child`, {
      parentId,
      childId,
    });
  }

  /**
   * 解除孩子关联
   */
  unlinkChild(parentId: string, childId: string): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(`${this.API_BASE_URL}/family/unlink-child`, {
      parentId,
      childId,
    });
  }

  /**
   * 获取用户的孩子列表（家长）
   */
  getChildren(parentId: string): Observable<User[]> {
    return this.http.get<User[]>(`${this.API_BASE_URL}/family/${parentId}/children`);
  }

  /**
   * 获取孩子的家长列表（学生）
   */
  getParents(studentId: string): Observable<User[]> {
    return this.http.get<User[]>(`${this.API_BASE_URL}/family/${studentId}/parents`);
  }

  /**
   * 检查用户是否可以创建组
   */
  canCreateGroup(userType: UserType): boolean {
    return USER_TYPE_CONFIG[userType]?.canCreateGroup ?? false;
  }

  /**
   * 检查用户是否可以邀请他人
   */
  canInviteMembers(userType: UserType): boolean {
    return USER_TYPE_CONFIG[userType]?.canInvite ?? false;
  }

  /**
   * 获取用户类型的默认组角色
   */
  getDefaultRole(userType: UserType): GroupMemberRole {
    return USER_TYPE_CONFIG[userType]?.defaultRoleInGroup ?? GroupMemberRole.MEMBER;
  }

  /**
   * 获取用户类型配置
   */
  getUserTypeConfig(userType: UserType) {
    return USER_TYPE_CONFIG[userType];
  }

  /**
   * 获取组类型配置
   */
  getGroupTypeConfig(groupType: GroupType): {
    label: string;
    requiresVerification: boolean;
    maxMembers: number;
  } {
    return {
      label: this.getGroupTypeLabel(groupType),
      requiresVerification:
        groupType === GroupType.ORGANIZATION ||
        groupType === GroupType.SCHOOL ||
        groupType === GroupType.DEPARTMENT,
      maxMembers: this.getGroupMaxMembers(groupType),
    };
  }

  private getGroupTypeLabel(type: GroupType): string {
    const labels: Record<GroupType, string> = {
      [GroupType.FAMILY]: '家庭组',
      [GroupType.CLASS]: '班级',
      [GroupType.ORGANIZATION]: '机构',
      [GroupType.SCHOOL]: '学校',
      [GroupType.DEPARTMENT]: '教育局/部门',
    };
    return labels[type];
  }

  private getGroupMaxMembers(type: GroupType): number {
    const maxMembers: Record<GroupType, number> = {
      [GroupType.FAMILY]: 10,
      [GroupType.CLASS]: 60,
      [GroupType.ORGANIZATION]: 1000,
      [GroupType.SCHOOL]: 10000,
      [GroupType.DEPARTMENT]: -1,
    };
    return maxMembers[type];
  }

  /**
   * 获取可创建的组类型列表
   */
  getAvailableGroupTypes(userType: UserType): GroupType[] {
    const userConfig = USER_TYPE_CONFIG[userType];
    if (!userConfig?.canCreateGroup) {
      return [];
    }

    switch (userType) {
      case UserType.PARENT:
        return [GroupType.FAMILY];
      case UserType.TEACHER:
        return [GroupType.CLASS];
      case UserType.ORG_ADMIN:
        return [GroupType.ORGANIZATION, GroupType.CLASS];
      case UserType.SCHOOL_ADMIN:
        return [GroupType.SCHOOL, GroupType.CLASS];
      case UserType.EDUCATION_BUREAU:
        return [GroupType.DEPARTMENT, GroupType.SCHOOL];
      default:
        return [];
    }
  }
}
