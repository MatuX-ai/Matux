/**
 * 用户中心路由配置
 *
 * 统一处理所有用户类型的路由，根据用户类型动态加载对应组件
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { UserPageLayoutComponent } from './components/user-page-layout/user-page-layout.component';
import { UserCenterGuard } from './guards/user-center.guard';
import { UserCenterComponent } from './user-center.component';

const routes: Routes = [
  // Dashboard 使用 UserCenterComponent（自带导航）
  {
    path: 'dashboard',
    component: UserCenterComponent,
    canActivate: [UserCenterGuard],
  },
  // 其他页面使用共享布局
  {
    path: '',
    component: UserPageLayoutComponent,
    canActivate: [UserCenterGuard],
    children: [
      {
        path: 'profile',
        loadComponent: () =>
          import('./components/user-profile/user-profile.component').then(
            (m) => m.UserProfileComponent
          ),
      },
      {
        path: 'token',
        loadChildren: () =>
          import('./token-dashboard/token-dashboard.module').then((m) => m.TokenDashboardModule),
      },
      {
        path: 'children',
        loadComponent: () =>
          import('./components/children-management/children-management.component').then(
            (m) => m.ChildrenManagementComponent
          ),
      },
      {
        path: 'reports',
        loadComponent: () =>
          import('./components/learning-reports/learning-reports.component').then(
            (m) => m.LearningReportsComponent
          ),
      },
      {
        path: 'achievements',
        loadComponent: () =>
          import('./components/achievements/achievements.component').then(
            (m) => m.AchievementsComponent
          ),
      },
      {
        path: 'teaching',
        loadComponent: () =>
          import('./components/teaching-management/teaching-management.component').then(
            (m) => m.TeachingManagementComponent
          ),
      },
      {
        path: 'students',
        loadComponent: () =>
          import('./components/student-management/student-management.component').then(
            (m) => m.StudentManagementComponent
          ),
      },
      // 学校管理员功能模块路由
      {
        path: 'classes',
        loadComponent: () =>
          import('./school-admin/school-admin-dashboard.component').then(
            (m) => m.SchoolAdminDashboardComponent
          ),
      },
      {
        path: 'school-courses',
        loadComponent: () =>
          import('./school-admin/school-admin-dashboard.component').then(
            (m) => m.SchoolAdminDashboardComponent
          ),
      },
      {
        path: 'quality',
        loadComponent: () =>
          import('./school-admin/school-admin-dashboard.component').then(
            (m) => m.SchoolAdminDashboardComponent
          ),
      },
      {
        path: 'teacher-workload',
        loadComponent: () =>
          import('./school-admin/school-admin-dashboard.component').then(
            (m) => m.SchoolAdminDashboardComponent
          ),
      },
      // 教育局功能模块路由
      {
        path: 'schools',
        loadComponent: () =>
          import('./education-bureau/education-bureau-dashboard.component').then(
            (m) => m.EducationBureauDashboardComponent
          ),
      },
      {
        path: 'analysis',
        loadComponent: () =>
          import('./education-bureau/education-bureau-dashboard.component').then(
            (m) => m.EducationBureauDashboardComponent
          ),
      },
      {
        path: 'reports-export',
        loadComponent: () =>
          import('./education-bureau/education-bureau-dashboard.component').then(
            (m) => m.EducationBureauDashboardComponent
          ),
      },
      // 默认重定向
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class UserRoutingModule {}
