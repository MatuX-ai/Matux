/**
 * 用户中心页面布局组件
 *
 * 包含全局导航栏、侧边栏、底部导航，所有子页面共享这个布局
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { SidebarService } from '../../services/sidebar.service';
import { UserCenterService } from '../../services/user-center.service';
import { UserFooterComponent } from '../user-footer/user-footer.component';
import { UserNavbarComponent } from '../user-navbar/user-navbar.component';
import { UserSidebarComponent } from '../user-sidebar/user-sidebar.component';
import { UserSubNavComponent } from '../user-sub-nav/user-sub-nav.component';

@Component({
  selector: 'app-user-page-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    UserNavbarComponent,
    UserSidebarComponent,
    UserFooterComponent,
    UserSubNavComponent,
  ],
  template: `
    <div class="user-page-layout">
      <!-- 全局导航栏 -->
      <app-user-navbar></app-user-navbar>

      <!-- 水平子导航（头部导航条下方） -->
      <app-user-sub-nav></app-user-sub-nav>

      <!-- 移动端遮罩（保留用于移动端侧边栏） -->
      <div class="overlay" [class.show]="isMobile && sidebarOpen" (click)="closeSidebar()"></div>

      <!-- 移动端侧边栏（仅移动端显示） -->
      <app-user-sidebar
        [opened]="sidebarOpen"
        [isMobile]="isMobile"
        (menuClick)="handleMenuClick()"
        class="mobile-sidebar-only"
      ></app-user-sidebar>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 页面内容 -->
        <main class="content-area">
          <router-outlet></router-outlet>

          <!-- 底部导航 -->
          <app-user-footer></app-user-footer>
        </main>
      </div>
    </div>
  `,
  styles: [
    `
      .user-page-layout {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        position: relative;
      }

      app-user-navbar {
        flex-shrink: 0;
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

      .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      .content-area {
        flex: 1;
        padding: 24px;
        overflow-y: auto;
        background-color: #f5f5f5;
        min-height: 0;
        display: flex;
        flex-direction: column;
      }

      .content-area app-user-footer {
        flex-shrink: 0;
        margin-top: auto;
      }

      /* 移动端侧边栏样式 */
      .mobile-sidebar-only {
        display: none;
      }

      @media (max-width: 768px) {
        .mobile-sidebar-only {
          display: block;
        }

        .content-area {
          padding: 16px;
        }
      }
    `,
  ],
})
export class UserPageLayoutComponent implements OnInit, OnDestroy {
  sidebarOpen = true;
  isMobile = false;
  userType: string | undefined;

  private destroy$ = new Subject<void>();

  constructor(
    private userCenterService: UserCenterService,
    private sidebarService: SidebarService
  ) {}

  ngOnInit(): void {
    this.checkScreenWidth();
    window.addEventListener('resize', () => this.checkScreenWidth());

    // 订阅侧边栏状态
    this.sidebarService.sidebarOpen$.pipe(takeUntil(this.destroy$)).subscribe((isOpen) => {
      this.sidebarOpen = isOpen;
    });

    this.userCenterService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.userType = user?.userType;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', () => this.checkScreenWidth());
  }

  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
    if (this.isMobile) {
      this.sidebarOpen = false;
    }
  }

  toggleSidebar(): void {
    this.sidebarService.toggleSidebar();
  }

  closeSidebar(): void {
    if (this.isMobile) {
      this.sidebarService.closeSidebar();
    }
  }

  handleMenuClick(): void {
    this.closeSidebar();
  }
}
