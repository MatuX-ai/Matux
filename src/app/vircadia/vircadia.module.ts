import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';

import { VircadiaSceneViewerComponent } from '../components/vircadia-scene-viewer/vircadia-scene-viewer.component';

import { AvatarCustomizationComponent } from './pages/avatar-customization/avatar-customization.component';
import { VirtualClassroomComponent } from './pages/virtual-classroom/virtual-classroom.component';
import { VirtualLabComponent } from './pages/virtual-lab/virtual-lab.component';
import { VircadiaComponent } from './vircadia.component';

const routes: Routes = [
  {
    path: '',
    component: VircadiaComponent,
    children: [
      { path: 'classroom', component: VirtualClassroomComponent, data: { title: '虚拟教室' } },
      { path: 'lab', component: VirtualLabComponent, data: { title: '虚拟实验室' } },
      { path: 'avatar', component: AvatarCustomizationComponent, data: { title: 'Avatar 换装' } },
      { path: '', redirectTo: 'classroom', pathMatch: 'full' },
    ],
  },
];

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatTabsModule,
    MatTooltipModule,
    VircadiaSceneViewerComponent,
    VirtualClassroomComponent,
    VirtualLabComponent,
    AvatarCustomizationComponent,
    VircadiaComponent,
  ],
})
export class VircadiaModule {}
