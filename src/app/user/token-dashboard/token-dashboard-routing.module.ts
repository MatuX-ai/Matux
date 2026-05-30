/**
 * Token 仪表板路由配置
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { UserTokenDashboardComponent } from './user-token-dashboard.component';

const routes: Routes = [
  {
    path: '',
    component: UserTokenDashboardComponent,
    data: {
      title: '我的 Token',
      description: '管理 Token 余额和使用记录',
    },
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TokenDashboardRoutingModule {}
