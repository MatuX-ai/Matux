import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AchievementDisplayComponent } from './components/achievement-display/achievement-display.component';
import { AchievementGalleryComponent } from './components/achievement-gallery/achievement-gallery.component';
import { AchievementProgressComponent } from './components/achievement-progress/achievement-progress.component';
import { AchievementReviewComponent } from './components/achievement-review/achievement-review.component';
import { AchievementUploadComponent } from './components/achievement-upload/achievement-upload.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'gallery',
    pathMatch: 'full',
  },
  {
    path: 'gallery',
    component: AchievementGalleryComponent,
    data: { title: '学习成果' },
  },
  {
    path: 'upload',
    component: AchievementUploadComponent,
    data: { title: '上传成果' },
  },
  {
    path: 'review/:id',
    component: AchievementReviewComponent,
    data: { title: '审核成果' },
  },
  {
    path: 'progress/:userId',
    component: AchievementProgressComponent,
    data: { title: '学习进度' },
  },
  {
    path: 'view/:id',
    component: AchievementDisplayComponent,
    data: { title: '成果详情' },
  },
  {
    path: 'module/:moduleId',
    component: AchievementGalleryComponent,
    data: { title: '模块成果' },
  },
  {
    path: 'lesson/:lessonId',
    component: AchievementGalleryComponent,
    data: { title: '课程成果' },
  },
  {
    path: 'user/:userId',
    component: AchievementGalleryComponent,
    data: { title: '我的成果' },
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AchievementIntegrationRoutingModule {}
