/**
 * Admin 营销数据看板子路由配置
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { MarketingDashboardComponent } from './marketing-dashboard.component';

const routes: Routes = [
  {
    path: '',
    component: MarketingDashboardComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AdminMarketingRoutingModule {}
