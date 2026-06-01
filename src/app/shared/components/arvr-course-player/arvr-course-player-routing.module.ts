/**
 * AR/VR 课程播放器子路由配置
 *
 * TODO: AR/VR 课程播放器组件尚未实现，当前路由仅作占位
 * 需要在 components 目录下创建实际的播放器组件后替换 redirectTo
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: '/content-store',
    pathMatch: 'full',
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ARVRCoursePlayerRoutingModule {}
