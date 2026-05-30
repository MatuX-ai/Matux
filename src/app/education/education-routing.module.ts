/**
 * 教育培训管理系统路由配置
 */

import { Routes } from '@angular/router';

export const educationRoutes: Routes = [
  {
    path: 'scheduling',
    loadChildren: () =>
      import('./management/scheduling/scheduling-routing.module').then(
        (m) => m.SchedulingRoutingModule
      ),
  },
  {
    path: 'students',
    loadChildren: () =>
      import('./management/students/students.module').then((m) => m.StudentsModule),
  },
  // TODO: 后续实现其他子模块路由
  // {
  //   path: 'teachers',
  //   loadChildren: () => import('./management/teachers/teachers-routing.module')
  //     .then(m => m.TeachersRoutingModule)
  // },
  // {
  //   path: 'teachers',
  //   loadChildren: () => import('./management/teachers/teachers-routing.module')
  //     .then(m => m.TeachersRoutingModule)
  // },
  // {
  //   path: 'attendance',
  //   loadChildren: () => import('./management/attendance/attendance-routing.module')
  //     .then(m => m.AttendanceRoutingModule)
  // },
  // {
  //   path: 'orders',
  //   loadChildren: () => import('./management/orders/orders-routing.module')
  //     .then(m => m.OrdersRoutingModule)
  // },
  // {
  //   path: 'reports',
  //   loadChildren: () => import('./management/reports/reports-routing.module')
  //     .then(m => m.ReportsRoutingModule)
  // },
];
