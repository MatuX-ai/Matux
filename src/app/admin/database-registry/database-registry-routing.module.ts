/**
 * 数据库注册表管理子路由配置
 *
 * 提供数据中心管理的模块列表、详细统计等子页面路由
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ModuleListComponent } from './components/module-list.component';
import { DatabaseRegistryDashboardComponent } from './database-registry-dashboard.component';

const routes: Routes = [
  {
    path: '',
    component: DatabaseRegistryDashboardComponent,
  },
  {
    path: 'modules',
    component: ModuleListComponent,
  },
  {
    path: 'stats',
    redirectTo: '',
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class DatabaseRegistryRoutingModule {}
