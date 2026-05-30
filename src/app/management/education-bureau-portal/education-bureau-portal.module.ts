/**
 * Education Bureau Portal Module
 * 教育局管理后台模块
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { EducationBureauDashboardComponent } from './education-bureau-dashboard.component';

const routes: Routes = [
  {
    path: 'dashboard',
    component: EducationBureauDashboardComponent,
  },
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
];

@NgModule({
  declarations: [],
  imports: [CommonModule, RouterModule.forChild(routes), EducationBureauDashboardComponent],
  exports: [],
})
export class EducationBureauPortalModule {}
