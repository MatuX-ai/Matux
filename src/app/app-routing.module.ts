import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { CustomPreloadingStrategy } from './core/services/custom-preloading.strategy';

const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./minimal-dashboard.component').then((m) => m.MinimalDashboardComponent),
  },
  {
    path: 'openmt-demo',
    loadComponent: () =>
      import('./components/openmt-demo/openmt-demo.component').then((m) => m.OpenMtDemoComponent),
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.module').then((m) => m.AdminModule),
  },
  {
    path: 'ar-lab',
    loadComponent: () => import('./ar-lab/ar-lab.component').then((m) => m.ARLabComponent),
  },
  {
    path: 'offline-mode',
    loadChildren: () =>
      import('./offline-mode/offline-mode.module').then((m) => m.OfflineModeModule),
  },
  {
    path: 'ai-edu',
    loadChildren: () =>
      import('./components/ai-edu-feature.module').then((m) => m.AIEduFeatureModule),
  },
  {
    path: 'arvr-course/:id',
    loadChildren: () =>
      import('./shared/components/arvr-course-player/arvr-course-player.module').then(
        (m) => m.ARVRCoursePlayerModule
      ),
  },
  {
    path: 'digital-twin-lab',
    loadChildren: () =>
      import('./shared/components/digital-twin-lab/digital-twin-lab.module').then(
        (m) => m.DigitalTwinLabModule
      ),
  },
  {
    path: 'license-management',
    loadChildren: () =>
      import('./license-management/license-management.module').then(
        (m) => m.LicenseManagementModule
      ),
  },
  {
    path: 'content-store',
    loadChildren: () =>
      import('./shared/components/content-store/content-store.module').then(
        (m) => m.ContentStoreModule
      ),
  },
  {
    path: 'creativity-engine',
    loadChildren: () =>
      import('./creativity-engine/creativity-engine.module').then((m) => m.CreativityEngineModule),
  },
  // Auth Module - 认证模块
  {
    path: 'auth',
    loadChildren: () => import('./auth/auth-routing.module').then((m) => m.AuthRoutingModule),
  },
  // User Center Module - 用户中心
  {
    path: 'user',
    loadChildren: () => import('./user/user.module').then((m) => m.UserModule),
  },
  // Management Portals Module - 管理门户（包含机构/学校/教育局三个管理后台）
  {
    path: 'management',
    loadChildren: () =>
      import('./management/management-portals.module').then((m) => m.ManagementPortalsModule),
  },

  // Icon Debug Page
  {
    path: 'icon-debug',
    loadComponent: () =>
      import('./components/icon-debug/icon-debug.component').then((m) => m.IconDebugComponent),
  },
  // Simple Icon Test
  {
    path: 'icon-test',
    loadComponent: () =>
      import('./components/icon-simple-test/icon-simple-test.component').then(
        (m) => m.IconSimpleTestComponent
      ),
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      preloadingStrategy: CustomPreloadingStrategy,
    }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule {}
