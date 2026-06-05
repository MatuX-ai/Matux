/**
 * 用户中心主组件
 *
 * 统一用户中心入口，根据用户类型动态渲染不同内容
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../core/models/auth.models';
import { AuthService } from '../core/services/auth.service';

import { UserFooterComponent } from './components/user-footer/user-footer.component';
import { UserNavbarComponent } from './components/user-navbar/user-navbar.component';
import { UserSidebarComponent } from './components/user-sidebar/user-sidebar.component';
import { UserSubNavComponent } from './components/user-sub-nav/user-sub-nav.component';
// 家长仪表板已解耦至 OpenMTEduInst 项目
import { SidebarService } from './services/sidebar.service';
import { UserCenterService } from './services/user-center.service';
import { StudentDashboardComponent } from './student/student-dashboard.component';

@Component({
  selector: 'app-user-center',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatSidenavModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatListModule,
    MatMenuModule,
    UserSidebarComponent,
    UserFooterComponent,
    UserNavbarComponent,
    UserSubNavComponent,
    StudentDashboardComponent,
    // ParentDashboardComponent 已移除
  ],
  template: `
    <div class="user-center-container" [class.desktop-layout]="!isMobile">
      <!-- 全局导航栏 -->
      <app-user-navbar></app-user-navbar>

      <!-- 桌面端侧边栏（持久可见） -->
      <app-user-sidebar
        *ngIf="!isMobile"
        [opened]="true"
        [isMobile]="false"
        class="desktop-sidebar"
      ></app-user-sidebar>

      <!-- 水平子导航 -->
      <app-user-sub-nav></app-user-sub-nav>

      <!-- 移动端遮罩 -->
      <div class="overlay" [class.show]="isMobile && sidebarOpen" (click)="closeSidebar()"></div>

      <!-- 移动端侧边栏 -->
      <app-user-sidebar
        *ngIf="isMobile"
        [opened]="sidebarOpen"
        [isMobile]="true"
        (menuClick)="handleMenuClick()"
        class="mobile-sidebar"
      ></app-user-sidebar>

      <!-- 主内容区 -->
      <div class="main-content" [class.with-sidebar]="!isMobile">
        <main class="content-area">
          <app-student-dashboard></app-student-dashboard>
          <app-user-footer></app-user-footer>
        </main>
      </div>
    </div>
  `,
  styles: [
    `
      .user-center-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        position: relative;
      }

      /* 桌面端 Grid 布局：侧边栏 + 内容区 */
      .user-center-container.desktop-layout {
        display: grid;
        grid-template-columns: 260px 1fr;
        grid-template-rows: 64px auto 1fr;
        min-height: 100vh;
      }

      .user-center-container.desktop-layout app-user-navbar {
        grid-column: 1 / -1;
        grid-row: 1;
      }

      .user-center-container.desktop-layout .desktop-sidebar {
        grid-column: 1;
        grid-row: 2 / -1;
        z-index: 100;
      }

      .user-center-container.desktop-layout app-user-sub-nav {
        grid-column: 2;
        grid-row: 2;
      }

      .user-center-container.desktop-layout .main-content {
        grid-column: 2;
        grid-row: 3;
      }

      app-user-navbar {
        flex-shrink: 0;
      }

      .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .content-area {
        flex: 1;
        padding: 24px;
        overflow-y: auto;
        background-color: var(--color-background);
        min-height: 0;
        display: flex;
        flex-direction: column;
      }

      .content-area app-user-footer {
        flex-shrink: 0;
        margin-top: auto;
      }

      .overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 998;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
      }

      .overlay.show {
        opacity: 1;
        visibility: visible;
      }

      /* 移动端侧边栏 */
      .mobile-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        z-index: 999;
      }

      .redirect-notice {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        color: var(--color-text-secondary);
      }

      .redirect-notice mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 16px;
      }

      .redirect-notice p {
        font-size: 16px;
      }

      @media (max-width: 767px) {
        .user-center-container.desktop-layout {
          display: flex;
          flex-direction: column;
        }

        .content-area {
          padding: 16px;
        }
      }
    `,
  ],
})
export class UserCenterComponent implements OnInit, OnDestroy {
  sidebarOpen = true;
  isMobile = false;
  currentUser: User | null = null;
  userType: string | undefined;

  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private userCenterService: UserCenterService,
    private sidebarService: SidebarService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // 检查屏幕宽度
    this.checkScreenWidth();
    window.addEventListener('resize', () => this.checkScreenWidth());

    // 订阅侧边栏状态
    this.sidebarService.sidebarOpen$.pipe(takeUntil(this.destroy$)).subscribe((isOpen) => {
      this.sidebarOpen = isOpen;
    });

    // 订阅当前用户信息（只在这里处理跳转，避免重复）
    this.userCenterService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      this.userType = user?.userType;
    });

    // 如果没有用户信息，尝试获取（但不处理跳转，等待订阅触发）
    if (!this.currentUser) {
      this.currentUser = this.userCenterService.getCurrentUser();
      this.userType = this.currentUser?.userType;
    }
  }

  /**
   * 根据用户类型处理重定向（已解耦至 OpenMTEduInst 项目，功能已移除）
   */
  // private handleUserTypeRedirect(userType?: string): void {
  //   // 已解耦至 OpenMTEduInst 项目
  // }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', () => this.checkScreenWidth());
  }

  /**
   * 检查屏幕宽度，判断是否为移动端
   */
  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
    if (this.isMobile) {
      this.sidebarOpen = false; // 移动端默认关闭侧边栏
    }
  }

  /**
   * 切换侧边栏状态
   */
  toggleSidebar(): void {
    this.sidebarService.toggleSidebar();
  }

  /**
   * 关闭侧边栏（移动端点击菜单后）
   */
  closeSidebar(): void {
    if (this.isMobile) {
      this.sidebarService.closeSidebar();
    }
  }

  /**
   * 处理菜单点击事件
   */
  handleMenuClick(): void {
    this.closeSidebar();
  }

  /**
   * 登出
   */
  logout(): void {
    this.userCenterService.logout();
  }
}
