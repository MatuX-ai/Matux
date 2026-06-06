/**
 * AR/VR 课程播放器子路由配置
 * 懒加载 ARVRCoursePlayerComponent
 */

import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ARVRCoursePlayerComponent } from './arvr-course-player.component';

const routes: Routes = [
  {
    path: '',
    component: ARVRCoursePlayerComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ARVRCoursePlayerRoutingModule {}
