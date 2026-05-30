/**
 * School Portal Module
 * 学校管理后台模块
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { SchoolAdminDashboardComponent } from './school-admin-dashboard.component';

const routes: Routes = [
  {
    path: 'dashboard',
    component: SchoolAdminDashboardComponent,
  },
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
];

@NgModule({
  declarations: [],
  imports: [CommonModule, RouterModule.forChild(routes), SchoolAdminDashboardComponent],
  exports: [],
})
export class SchoolPortalModule {}
