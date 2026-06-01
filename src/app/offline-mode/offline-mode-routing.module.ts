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
  {
    path: 'code-execution',
    loadComponent: () =>
      import('./components/offline-code-execution/offline-code-execution.component').then(
        (m) => m.OfflineCodeExecutionComponent
      ),
    data: {
      title: '离线代码执行',
      description: '离线环境下编写和运行代码',
    },
  },
  {
    path: 'sync',
    loadComponent: () =>
      import('./components/offline-sync-panel/offline-sync-panel.component').then(
        (m) => m.OfflineSyncPanelComponent
      ),
    data: {
      title: '数据同步',
      description: '管理离线操作同步',
    },
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class OfflineModeRoutingModule {}
