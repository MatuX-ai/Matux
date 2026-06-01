/**
 * AR/VR 课程播放器模块
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { ARVRCoursePlayerRoutingModule } from './arvr-course-player-routing.module';

@NgModule({
  imports: [CommonModule, ARVRCoursePlayerRoutingModule],
})
export class ARVRCoursePlayerModule {}
