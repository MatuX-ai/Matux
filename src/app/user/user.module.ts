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
import { MatMenuModule } from '@angular/material/menu';
import { RouterModule } from '@angular/router';

// 守卫
import { UserCenterGuard } from './guards/user-center.guard';
// 服务
import { UserCenterService } from './services/user-center.service';
// 组件
import { UserCenterComponent } from './user-center.component';
// 路由
import { UserRoutingModule } from './user-routing.module';

/**
 * @deprecated UserHeaderComponent 已废弃，请使用 UserNavbarComponent
 */
// import { UserHeaderComponent } from './components/user-header/user-header.component';

/**
 * @deprecated UserSidebarComponent 已废弃，桌面端不再使用左侧边栏布局
 */
// import { UserSidebarComponent } from './components/user-sidebar/user-sidebar.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatMenuModule,
    UserRoutingModule,
    UserCenterComponent,
  ],
  providers: [UserCenterService, UserCenterGuard],
})
export class UserModule {}
