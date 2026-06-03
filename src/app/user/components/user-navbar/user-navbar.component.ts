/**
 * 学习端全局导航栏组件
 *
 * 全宽顶部导航，包含 Logo、课程、实验室等链接（学生端）
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';

import { AuthService } from '../../../core/services/auth.service';
import { SidebarService } from '../../services/sidebar.service';
import { UserCenterService } from '../../services/user-center.service';

@Component({
  selector: 'app-user-navbar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatDividerModule,
  ],
  template: `
    <header class="user-navbar">
      <div class="navbar-container">
        <!-- 移动端汉堡菜单 -->
        <button mat-icon-button class="hamburger-menu" (click)="toggleSidebar()" *ngIf="isMobile">
          <mat-icon>menu</mat-icon>
        </button>

        <!-- Logo -->
        <div class="navbar-logo" (click)="navigateTo('/user/dashboard')">
          <span class="logo-text">MatuX</span>
          <span class="logo-subtitle">学习端</span>
        </div>

        <!-- 导航菜单 - 学生端核心功能 -->
        <nav class="navbar-nav">
          <a routerLink="/ai-edu" routerLinkActive="active" class="nav-link">
            AI编程课程
          </a>
          <a routerLink="/user/dashboard" routerLinkActive="active" class="nav-link">
            学习中心
          </a>
          <a routerLink="/creativity-engine" routerLinkActive="active" class="nav-link">
            创意引擎
          </a>
          <a routerLink="/ar-lab" routerLinkActive="active" class="nav-link">
            AR 实验室
          </a>
          <a routerLink="/content-store" routerLinkActive="active" class="nav-link">
            内容商店
          </a>
          <a routerLink="/offline-mode" routerLinkActive="active" class="nav-link">
            离线模式
          </a>
        </nav>

        <!-- 用户菜单 -->
        <div class="navbar-user">
          <button mat-button [matMenuTriggerFor]="userMenu" class="user-menu-btn">
            <mat-icon>account_circle</mat-icon>
            <span class="username">{{ currentUser?.username || '用户' }}</span>
            <mat-icon>arrow_drop_down</mat-icon>
          </button>

          <mat-menu #userMenu="matMenu">
            <div class="user-menu-header" *ngIf="currentUser">
              <div class="user-avatar">
                <img [src]="currentUser.avatar || 'assets/icons/user.svg'" alt="用户头像" />
              </div>
              <div class="user-info">
                <div class="username">{{ currentUser.username || '用户' }}</div>
                <div class="user-type">{{ getUserTypeLabel() }}</div>
              </div>
            </div>

            <mat-divider></mat-divider>

            <button mat-menu-item routerLink="/user/profile">
              <mat-icon>person</mat-icon>
              <span>个人资料</span>
            </button>

            <button mat-menu-item routerLink="/user/token">
              <mat-icon>token</mat-icon>
              <span>Token管理</span>
            </button>

            <mat-divider></mat-divider>

            <button mat-menu-item (click)="logout()">
              <mat-icon>logout</mat-icon>
              <span>退出登录</span>
            </button>
          </mat-menu>
        </div>
      </div>
    </header>
  `,
  styles: [
    `
      .user-navbar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0 24px;
        height: 60px;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .navbar-container {
        max-width: 1400px;
        margin: 0 auto;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .hamburger-menu {
        color: white;
        display: none;
      }

      .navbar-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: opacity 0.2s;
      }

      .navbar-logo:hover {
        opacity: 0.9;
      }

      .logo-text {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
      }

      .logo-subtitle {
        font-size: 14px;
        opacity: 0.8;
        padding: 2px 8px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
      }

      .navbar-nav {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .nav-link {
        padding: 8px 16px;
        color: rgba(255, 255, 255, 0.85);
        text-decoration: none;
        border-radius: 8px;
        transition: all 0.2s;
        font-size: 15px;
        font-weight: 500;
      }

      .nav-link:hover {
        background: rgba(255, 255, 255, 0.15);
        color: white;
      }

      .nav-link.active {
        background: rgba(255, 255, 255, 0.25);
        color: white;
      }

      .nav-link mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }

      .navbar-user {
        display: flex;
        align-items: center;
      }

      .user-menu-btn {
        color: white;
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .username {
        margin: 0 4px;
      }

      /* 用户菜单样式 */
      .user-menu-header {
        padding: 16px;
        display: flex;
        align-items: center;
        background: #f5f5f5;
      }

      .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        margin-right: 12px;
        background: #e0e0e0;
      }

      .user-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .user-info .username {
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin: 0;
      }

      .user-info .user-type {
        font-size: 14px;
        color: #666;
      }

      @media (max-width: 768px) {
        .navbar-nav {
          display: none;
        }

        .logo-subtitle {
          display: none;
        }

        .hamburger-menu {
          display: block;
          margin-right: 8px;
        }
      }
    `,
  ],
})
export class UserNavbarComponent implements OnInit, OnDestroy {
  currentUser: any = null;
  userType: string | undefined;
  isMobile = false;

  private destroy$ = new Subject<void>();

  constructor(
    private userCenterService: UserCenterService,
    private sidebarService: SidebarService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.checkScreenWidth();
    window.addEventListener('resize', () => this.checkScreenWidth());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', () => this.checkScreenWidth());
  }

  private loadUserData(): void {
    this.currentUser = this.userCenterService.getCurrentUser();
    this.userType = this.currentUser?.userType;

    // 订阅用户变化
    this.userCenterService.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.userType = user?.userType;
    });
  }

  getUserTypeLabel(): string {
    if (!this.userType) return '用户';

    const typeMap: Record<string, string> = {
      student: '学生',
    };

    return typeMap[this.userType] || '用户';
  }

  navigateTo(path: string): void {
    this.router.navigate([path]);
  }

  logout(): void {
    this.userCenterService.logout();
  }

  /**
   * 检查屏幕宽度
   */
  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
  }

  /**
   * 切换侧边栏
   */
  toggleSidebar(): void {
    this.sidebarService.toggleSidebar();
  }
}
