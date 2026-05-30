/**
 * Management Portals Module
 *
 * 包含三个独立的管理门户：
 * - Organization Portal: 机构管理后台
 * - School Portal: 学校管理后台
 * - Education Bureau Portal: 教育局管理后台
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// import { OrganizationGuard } from '../guards/organization.guard';  // 已解耦到 OpenMTEduInst 项目

const routes: Routes = [
  // {
  //   path: 'organization',
  //   loadChildren: () =>
  //     import('./organization-portal/organizations.module').then((m) => m.OrganizationsModule),
  //   canActivate: [OrganizationGuard],
  // },  // 已解耦到 OpenMTEduInst 项目
  {
    path: 'school',
    loadChildren: () =>
      import('./school-portal/school-portal.module').then((m) => m.SchoolPortalModule),
  },
  {
    path: 'education-bureau',
    loadChildren: () =>
      import('./education-bureau-portal/education-bureau-portal.module').then(
        (m) => m.EducationBureauPortalModule
      ),
  },
  // {
  //   path: 'licenses',
  //   loadComponent: () =>
  //     import('../license-management/license-list.component').then((m) => m.LicenseListComponent),
  //   canActivate: [OrganizationGuard],
  // },  // 已解耦到 OpenMTEduInst 项目
  // {
  //   path: 'token-packages',
  //   loadComponent: () =>
  //     import('../components/token-package-selector/token-package-selector.component').then(
  //       (m) => m.TokenPackageSelectorComponent
  //     ),
  //   canActivate: [OrganizationGuard],
  // },  // 已解耦到 OpenMTEduInst 项目
  // {
  //   path: 'users',
  //   loadComponent: () =>
  //     import('./user-management/user-management.component').then((m) => m.UserManagementComponent),
  //   canActivate: [OrganizationGuard],
  // },  // 已解耦到 OpenMTEduInst 项目
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full',
  },
];

@NgModule({
  declarations: [],
  imports: [CommonModule, RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ManagementPortalsModule {}
