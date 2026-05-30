/**
 * @deprecated 此类已迁移到 OpenMTEduInst 子项目。此桩文件仅用于向后兼容，避免现有组件报错。
 * 请访问 OpenMTEduInst 项目获取最新服务实现。
 * 此桩服务在迁移完成后应被移除。
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

export interface UserRecord {
  id: number;
  name: string;
  email: string;
  role: string;
}

@Injectable({
  providedIn: 'root',
})
export class UserManagementService {
  getUsers(): Observable<any[]> {
    return of([]);
  }

  getUserList(): Observable<any[]> {
    return of([]);
  }

  createUser(_user: any): Observable<any> {
    return of({});
  }

  updateUser(_id: number, _user: any): Observable<any> {
    return of({});
  }

  deleteUser(_id: number): Observable<any> {
    return of({ success: true });
  }

  batchUpdateStatus(_userIds: number[], _status: string): Observable<any> {
    return of({ success: true });
  }

  resetPassword(_userId: number): Observable<any> {
    return of({ success: true });
  }

  updateUserStatus(_userId: number, _status: string): Observable<any> {
    return of({ success: true });
  }

  exportUsersToExcel(_users: any[]): Observable<Blob> {
    return of(new Blob());
  }
}
