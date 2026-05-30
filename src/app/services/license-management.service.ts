/**
 * @deprecated 此类已迁移到 OpenMTEduInst 子项目。此桩文件仅用于向后兼容，避免现有组件报错。
 * 请访问 OpenMTEduInst 项目获取最新服务实现。
 * 此桩服务在迁移完成后应被移除。
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

export interface LicensePackage {
  id: number;
  name: string;
  price: number;
  isRecommended?: boolean;
}

export interface LicenseInfo {
  id: number;
  name: string;
  status: string;
  expiresAt: string;
}

@Injectable({
  providedIn: 'root',
})
export class LicenseManagementService {
  getLicensePackages(): Observable<any[]> {
    return of([]);
  }

  getLicenses(): Observable<any[]> {
    return of([]);
  }

  getTokenPackages(): Observable<any[]> {
    return of([]);
  }

  getTokenBalance(): Observable<any> {
    return of(0);
  }

  getLicenseList(): Observable<any[]> {
    return of([]);
  }

  assignLicense(_licenseId: number, _userIds: number[], _role?: string): Observable<any> {
    return of({ success: true });
  }

  revokeLicense(_id: number): Observable<any> {
    return of({ success: true });
  }

  exportLicensesToExcel(_licenses: any[]): Observable<Blob> {
    return of(new Blob());
  }
}
