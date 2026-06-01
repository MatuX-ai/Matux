/**
 * 赞助管理子路由配置
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { SponsorshipDashboardComponent } from './sponsorship-dashboard.component';

const routes: Routes = [
  {
    path: '',
    component: SponsorshipDashboardComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SponsorshipDashboardRoutingModule {}
