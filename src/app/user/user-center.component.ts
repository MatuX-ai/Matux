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
import { ParentDashboardComponent } from './parent/parent-dashboard.component';
import { SidebarService } from './services/sidebar.service';
import { UserCenterService } from './services/user-center.service';
import { StudentDashboardComponent } from './student/student-dashboard.component';
import { TeacherDashboardComponent } from './teacher/teacher-dashboard.component';

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
    TeacherDashboardComponent,
    ParentDashboardComponent,
  ],
  template: `
    <div class="user-center-container">
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
          <!-- 根据用户类型显示不同的仪表板 -->
          <ng-container [ngSwitch]="userType">
            <app-student-dashboard *ngSwitchCase="'student'"></app-student-dashboard>
            <app-teacher-dashboard *ngSwitchCase="'teacher'"></app-teacher-dashboard>
            <app-parent-dashboard *ngSwitchCase="'parent'"></app-parent-dashboard>

            <!-- 管理员跳转到管理门户 -->
            <div *ngSwitchCase="'org_admin'">
              <div class="redirect-notice">
                <mat-icon>redirect</mat-icon>
                <p>正在跳转到机构管理后台...</p>
              </div>
            </div>

            <div *ngSwitchCase="'school_admin'">
              <div class="redirect-notice">
                <mat-icon>redirect</mat-icon>
                <p>正在跳转到学校管理后台...</p>
              </div>
            </div>

            <div *ngSwitchCase="'education_admin'">
              <div class="redirect-notice">
                <mat-icon>redirect</mat-icon>
                <p>正在跳转到教育局管理后台...</p>
              </div>
            </div>

            <!-- 默认显示通用内容（不激活任何路由） -->
            <div *ngSwitchDefault class="default-content">
              <p>欢迎使用 MatuX 平台</p>
            </div>
          </ng-container>

          <!-- 底部导航 -->
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
        background-color: #f5f5f5;
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

      /* 移动端侧边栏样式 */
      .mobile-sidebar-only {
        display: none;
      }

      @media (max-width: 767px) {
        .mobile-sidebar-only {
          display: block;
        }

        .content-area {
          padding: 16px;
        }
      }

      .redirect-notice {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        color: #666;
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
      // 只在有用户且是管理员时才处理跳转
      if (
        user &&
        (user.userType === 'org_admin' ||
          user.userType === 'school_admin' ||
          user.userType === 'education_admin')
      ) {
        this.handleUserTypeRedirect(user.userType);
      }
    });

    // 如果没有用户信息，尝试获取（但不处理跳转，等待订阅触发）
    if (!this.currentUser) {
      this.currentUser = this.userCenterService.getCurrentUser();
      this.userType = this.currentUser?.userType;
    }
  }

  /**
   * 根据用户类型处理重定向
   */
  private handleUserTypeRedirect(userType?: string): void {
    // 机构管理员跳转到管理门户（已解耦到 OpenMTEduInst 项目）
    // if (userType === 'org_admin') {
    //   setTimeout(() => {
    //     void this.router.navigate(['/management/organization/dashboard']);
    //   }, 1500);
    // }
    // 学校管理员跳转到管理门户
    if (userType === 'school_admin') {
      setTimeout(() => {
        void this.router.navigate(['/management/school/dashboard']);
      }, 1500);
    }
    // 教育局管理员跳转到管理门户（注意：AuthService 创建的是 education_admin）
    else if (userType === 'education_admin' || userType === 'education_bureau') {
      setTimeout(() => {
        void this.router.navigate(['/management/education-bureau/dashboard']);
      }, 1500);
    }
  }

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
