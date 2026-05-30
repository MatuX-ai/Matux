/**
 * 用户中心模块
 *
 * 封装用户中心相关组件、服务和路由
 */

import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
// Angular Material
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule } from '@angular/router';

import { UserHeaderComponent } from './components/user-header/user-header.component';
import { UserSidebarComponent } from './components/user-sidebar/user-sidebar.component';
// 守卫
import { UserCenterGuard } from './guards/user-center.guard';
// 服务
import { UserCenterService } from './services/user-center.service';
// 组件
import { UserCenterComponent } from './user-center.component';
// 路由
import { UserRoutingModule } from './user-routing.module';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatMenuModule,
    UserRoutingModule,
    UserCenterComponent,
    UserSidebarComponent,
    UserHeaderComponent,
  ],
  providers: [UserCenterService, UserCenterGuard],
})
export class UserModule {}
