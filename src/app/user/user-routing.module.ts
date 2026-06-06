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
        path: 'achievements',
        loadComponent: () =>
          import('./components/achievements/achievements.component').then(
            (m) => m.AchievementsComponent
          ),
      },
      {
        path: 'courses',
        loadComponent: () =>
          import('./components/my-courses/my-courses.component').then((m) => m.MyCoursesComponent),
      },
      {
        path: 'learning-profile',
        loadComponent: () =>
          import('./components/learning-profile/learning-profile.component').then(
            (m) => m.LearningProfileComponent
          ),
      },
      {
        path: 'growth-trajectory',
        loadComponent: () =>
          import('./components/growth-trajectory/growth-trajectory.component').then(
            (m) => m.GrowthTrajectoryPageComponent
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
        path: 'teaching-suggestions',
        loadComponent: () =>
          import('./components/teaching-suggestions/teaching-suggestions.component').then(
            (m) => m.TeachingSuggestionsComponent
          ),
      },
      {
        path: 'emotional-companion',
        loadComponent: () =>
          import('./components/emotional-companion/emotional-companion.component').then(
            (m) => m.EmotionalCompanionComponent
          ),
      },
      {
        path: 'ai-teacher-settings',
        loadComponent: () =>
          import('./components/ai-teacher-settings/ai-teacher-settings.component').then(
            (m) => m.AITeacherSettingsComponent
          ),
      },
      // 教学管理/学生管理路由已解耦至 OpenMTEduInst 项目
      // 学校管理员功能模块（已解耦至 OpenMTEduInst 项目）
      // 教育局功能模块（已解耦至 OpenMTEduInst 项目）
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
