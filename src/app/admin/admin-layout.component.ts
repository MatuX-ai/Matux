import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { AdminAuthService } from './auth/admin-auth.service';
import { AdminMobileNavComponent } from './shared/components/admin-mobile-nav/admin-mobile-nav.component';
import { AdminSidebarComponent } from './shared/components/admin-sidebar/admin-sidebar.component';
import { AdminUser } from './shared/models/admin-user.model';
import { PAGE_TITLE_MAP, ROUTE_PATHS } from './admin-layout.config';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [
    AdminMobileNavComponent,
    AdminSidebarComponent,
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatListModule,
    MatMenuModule,
    RouterModule,
  ],
  templateUrl: './admin-layout.component.html',
  styleUrls: ['./admin.styles.scss'],
  styles: [
    `
      .admin-layout {
        display: flex !important;
        flex-direction: column !important;
      }

      .admin-body {
        display: flex !important;
        flex-direction: row !important;
        flex: 1;
      }

      .admin-sidebar {
        flex-shrink: 0;
      }

      .admin-content {
        flex: 1;
      }
    `,
  ],
})
export class AdminLayoutComponent implements OnInit {
  currentUser: AdminUser | null = null;
  sidebarCollapsed = false;

  constructor(
    private adminAuthService: AdminAuthService,
    private router: Router,
    public route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // 从服务获取当前用户信息
    this.currentUser = this.adminAuthService.getCurrentUser();
    // 恢复侧边栏状态 - 默认展开（false）
    const savedState = localStorage.getItem('admin_sidebar_collapsed');
    this.sidebarCollapsed = savedState === 'true';
  }

  /**
   * 侧边栏折叠状态变化处理
   */
  onSidebarCollapsedChange(collapsed: boolean): void {
    this.sidebarCollapsed = collapsed;
  }

  goBack(): void {
    // 返回到 admin 仪表板首页
    void this.router.navigate([ROUTE_PATHS.DASHBOARD]);
  }

  getCurrentPageTitle(): string {
    const url = this.router.url;

    // 使用配置映射表获取页面标题
    for (const [path, title] of Object.entries(PAGE_TITLE_MAP)) {
      if (url.includes(path)) {
        return title;
      }
    }

    return '管理后台';
  }

  logout(): void {
    this.adminAuthService.logout();
    void this.router.navigate([ROUTE_PATHS.LOGIN]);
  }
}
