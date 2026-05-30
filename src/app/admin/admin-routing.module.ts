import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AdminAuthGuard } from './auth/admin.guard';
import { AdminLoginComponent } from './auth/admin-login.component';
import { AdminCourseLibraryComponent } from './course-library/admin-course-library.component';
import { AdminDashboardComponent } from './dashboard/admin-dashboard.component';
import { LicenseListComponent } from './licenses/license-list.component';
import { AdminMaterialLibraryComponent } from './material-library/admin-material-library.component';
import { PaymentListComponent } from './payments/payment-list.component';
import { UserListComponent } from './users/user-list.component';

const routes: Routes = [
  {
    path: 'login',
    component: AdminLoginComponent,
  },
  {
    path: '',
    loadComponent: () => import('./admin-layout.component').then((m) => m.AdminLayoutComponent),
    canActivate: [AdminAuthGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        component: AdminDashboardComponent,
      },
      {
        path: 'licenses',
        component: LicenseListComponent,
      },
      // {
      //   path: 'institutions',
      //   loadChildren: () =>
      //     import('./institution-management/institution-management.module').then(
      //       (m) => m.InstitutionManagementModule
      //     ),
      // },  // 已解耦到 OpenMTEduInst 项目
      {
        path: 'materials',
        // @deprecated 课件管理已解耦到 OpenMTSciEd 项目，此路由保留仅用于向后兼容
         component: AdminMaterialLibraryComponent,
       },
       {
         path: 'courses',
        // @deprecated 课件管理已解耦到 OpenMTSciEd 项目，此路由保留仅用于向后兼容
        component: AdminCourseLibraryComponent,
       },
      {
        path: 'users',
        component: UserListComponent,
      },
      {
        path: 'payments',
        component: PaymentListComponent,
      },
      {
        path: 'sponsorship',
        loadChildren: () =>
          import('./sponsorship-dashboard/sponsorship-dashboard.module').then(
            (m) => m.SponsorshipDashboardModule
          ),
      },
      // 新增：数据库注册表管理路由
      {
        path: 'database-registry',
        loadChildren: () =>
          import('./database-registry/database-registry.module').then(
            (m) => m.DatabaseRegistryModule
          ),
      },
      // 新增：营销数据看板路由
      {
        path: 'marketing',
        loadChildren: () =>
          import('./marketing/marketing.module').then((m) => m.AdminMarketingModule),
      },
      // 新增：全局 API 设置路由
      {
        path: 'api-settings',
        loadComponent: () =>
          import('./shared/components/api-settings/api-settings.component').then(
            (m) => m.ApiSettingsComponent
          ),
      },
      // API 文档路由
      {
        path: 'api-docs',
        loadComponent: () =>
          import('./api-docs/api-docs.component').then((m) => m.ApiDocsComponent),
      },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AdminRoutingModule {}
