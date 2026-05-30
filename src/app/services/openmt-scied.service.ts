/**
 * @deprecated 此类已迁移到 OpenMTSciEd 子项目。此桩文件仅用于向后兼容，避免现有组件报错。
 * 请访问 OpenMTSciEd 项目获取最新服务实现。
 * 此桩服务在迁移完成后应被移除。
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

export interface Tutorial {
  id: number;
  title: string;
  description: string;
  subject: string;
}

export interface HardwareProject {
  id: number;
  title: string;
  name: string;
  status: string;
  difficulty_level: string;
}

export interface HardwareProjectListResponse {
  items: HardwareProject[];
  total: number;
}

@Injectable({
  providedIn: 'root',
})
export class OpenMtSciEdService {
  getTutorials(_page?: number, _size?: number): Observable<any> {
    return of({ items: [], total: 0 });
  }

  getHardwareProjects(_page?: number, _size?: number): Observable<any> {
    return of({ items: [], total: 0 });
  }
}
