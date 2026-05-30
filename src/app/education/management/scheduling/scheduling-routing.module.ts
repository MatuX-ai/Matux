/**
 * 排课管理路由配置
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ScheduleCalendarComponent } from './schedule-calendar.component';

const routes: Routes = [
  {
    path: '',
    component: ScheduleCalendarComponent,
    data: {
      title: '智能排课',
      breadcrumb: '排课管理',
    },
  },
  // {
  //   path: ':id',
  //   loadChildren: () =>
  //     import('../schedule-detail/schedule-detail-routing.module').then(
  //       (m) => m.ScheduleDetailRoutingModule
  //     ),
  // },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SchedulingRoutingModule {}
