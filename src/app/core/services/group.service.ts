import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import {
  Group,
  GroupInvitation,
  GroupMember,
  GroupMemberRole,
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
}
