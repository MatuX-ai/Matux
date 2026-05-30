import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

/**
 * 离线模式路由配置
 * 定义离线模式下的页面路由
 */
const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./components/offline-dashboard/offline-dashboard.component').then(
        (m) => m.OfflineDashboardComponent
      ),
    data: {
      title: '离线仪表板',
      description: '离线状态下的学习管理面板',
    },
  },
  // 其他路由将在后续开发中添加
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class OfflineModeRoutingModule {}
