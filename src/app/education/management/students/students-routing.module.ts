/**
 * 学员管理路由配置
 */

import { Routes } from '@angular/router';

import { StudentDetailComponent } from './student-detail/student-detail.component';
import { StudentListComponent } from './student-list/student-list.component';

export const studentRoutes: Routes = [
  {
    path: '',
    component: StudentListComponent,
    title: '学员列表',
  },
  {
    path: ':id',
    component: StudentDetailComponent,
    title: '学员详情',
  },
];
