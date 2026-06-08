/**
 * 学习端全局导航栏组件（桌面端）
 *
 * 按照 PRD 第 6.5 节布局规范：
 * - 64px 高度深色导航栏
 * - Logo + 水平导航菜单
 * - 搜索、通知、用户菜单
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { ROUTES } from '../../../routes.const';
import { UserCenterService } from '../../services/user-center.service';

interface NavItem {
  route: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-user-navbar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatDividerModule,
    MatTooltipModule,
  ],
  template: `
    <header class="user-navbar">
      <div class="navbar-container">
        <!-- Logo -->
        <div class="navbar-logo" (click)="navigateTo(ROUTES.USER.DASHBOARD)">
          <span class="logo-icon">🧊</span>
          <span class="logo-text">MatuX</span>
        </div>

        <!-- 水平导航菜单（桌面端） -->
        <nav class="navbar-nav" *ngIf="!isMobile">
          <a
            *ngFor="let item of navItems"
            [routerLink]="item.route"
            routerLinkActive="active"
            class="nav-link"
            [matTooltip]="item.label"
          >
            <mat-icon>{{ item.icon }}</mat-icon>
            <span>{{ item.label }}</span>
          </a>
        </nav>

        <!-- 搜索和通知 -->
        <div class="navbar-actions">
          <button
            mat-icon-button
            class="action-btn"
            title="搜索 (Ctrl+K)"
            (click)="toggleSearch()"
          >
            <mat-icon>search</mat-icon>
          </button>
          <button
            mat-icon-button
            class="action-btn notification-btn"
            title="通知"
          >
            <mat-icon>notifications</mat-icon>
            <span class="notification-badge" *ngIf="unreadNotifications > 0">
              {{ unreadNotifications }}
            </span>
          </button>
        </div>

        <!-- 用户菜单 -->
        <div class="navbar-user">
          <button mat-button [matMenuTriggerFor]="userMenu" class="user-menu-btn">
            <div class="user-avatar-small">
              <mat-icon>account_circle</mat-icon>
            </div>
            <span class="username">{{ currentUser?.username || '用户' }}</span>
            <mat-icon>arrow_drop_down</mat-icon>
          </button>

          <mat-menu #userMenu="matMenu" class="user-dropdown-menu">
            <div class="user-menu-header" *ngIf="currentUser">
              <div class="user-avatar">
                <img [src]="currentUser.avatar || 'assets/icons/user.svg'" alt="用户头像" />
              </div>
              <div class="user-info">
                <div class="username">{{ currentUser.username || '用户' }}</div>
                <div class="user-type-badge">{{ getUserTypeLabel() }}</div>
              </div>
            </div>

            <mat-divider></mat-divider>

            <button mat-menu-item [routerLink]="ROUTES.USER.PROFILE">
              <mat-icon>person</mat-icon>
              <span>个人资料</span>
            </button>

            <button mat-menu-item [routerLink]="ROUTES.USER.TOKEN">
              <mat-icon>token</mat-icon>
              <span>Token管理</span>
            </button>

            <button mat-menu-item [routerLink]="ROUTES.USER.ACHIEVEMENTS">
              <mat-icon>emoji_events</mat-icon>
              <span>成就系统</span>
            </button>

            <mat-divider></mat-divider>

            <button mat-menu-item [routerLink]="ROUTES.USER.AI_TEACHER_SETTINGS">
              <mat-icon>smart_toy</mat-icon>
              <span>AI教师设置</span>
            </button>

            <mat-divider></mat-divider>

            <button mat-menu-item (click)="logout()">
              <mat-icon>logout</mat-icon>
              <span>退出登录</span>
            </button>
          </mat-menu>
        </div>

        <!-- 移动端汉堡菜单 -->
        <button
          mat-icon-button
          class="hamburger-menu"
          [matMenuTriggerFor]="mobileMenu"
          *ngIf="isMobile"
        >
          <mat-icon>menu</mat-icon>
        </button>

        <mat-menu #mobileMenu="matMenu">
          <div class="mobile-menu-header" *ngIf="currentUser">
            <span>{{ currentUser.username || '用户' }}</span>
          </div>
          <button
            mat-menu-item
            *ngFor="let item of navItems"
            [routerLink]="item.route"
          >
            <mat-icon>{{ item.icon }}</mat-icon>
            <span>{{ item.label }}</span>
          </button>
          <mat-divider></mat-divider>
          <button mat-menu-item [routerLink]="ROUTES.USER.PROFILE">
            <mat-icon>person</mat-icon>
            <span>个人资料</span>
          </button>
          <button mat-menu-item (click)="logout()">
            <mat-icon>logout</mat-icon>
            <span>退出登录</span>
          </button>
        </mat-menu>
      </div>

      <!-- 搜索面板 -->
      <div class="search-panel" *ngIf="showSearch" (click)="toggleSearch()">
        <div class="search-container" (click)="$event.stopPropagation()">
          <mat-icon class="search-icon">search</mat-icon>
          <input
            type="text"
            class="search-input"
            placeholder="搜索课程、项目、内容..."
            autofocus
            (keyup.escape)="toggleSearch()"
          />
          <span class="search-hint">按 ESC 关闭</span>
        </div>
      </div>
    </header>
  `,
  styles: [
    `
      .user-navbar {
        background: #0f172a;
        color: white;
        height: 64px;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }

      .navbar-container {
        max-width: 1400px;
        margin: 0 auto;
        height: 100%;
        padding: 0 24px;
        display: flex;
        align-items: center;
        gap: 32px;
      }

      /* Logo */
      .navbar-logo {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        transition: opacity 0.2s;
        flex-shrink: 0;
      }

      .navbar-logo:hover {
        opacity: 0.9;
      }

      .logo-icon {
        font-size: 28px;
      }

      .logo-text {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
      }

      /* 导航菜单 */
      .navbar-nav {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1;
      }

      .nav-link {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        color: rgba(255, 255, 255, 0.75);
        text-decoration: none;
        border-radius: 8px;
        transition: all 0.2s;
        font-size: 14px;
        font-weight: 500;
        white-space: nowrap;
      }

      .nav-link mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }

      .nav-link:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
      }

      .nav-link.active {
        background: rgba(255, 255, 255, 0.15);
        color: white;
      }

      /* 操作按钮 */
      .navbar-actions {
        display: flex;
        align-items: center;
        gap: 4px;
        flex-shrink: 0;
      }

      .action-btn {
        color: rgba(255, 255, 255, 0.75);
        position: relative;
      }

      .action-btn:hover {
        color: white;
        background: rgba(255, 255, 255, 0.1);
      }

      .notification-badge {
        position: absolute;
        top: 2px;
        right: 2px;
        min-width: 16px;
        height: 16px;
        padding: 0 4px;
        background: #ef4444;
        color: white;
        font-size: 10px;
        font-weight: 600;
        line-height: 16px;
        text-align: center;
        border-radius: 9999px;
      }

      /* 用户菜单 */
      .navbar-user {
        flex-shrink: 0;
      }

      .user-menu-btn {
        color: white;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 8px;
      }

      .user-menu-btn:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      .user-avatar-small {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .user-avatar-small mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }

      .username {
        font-size: 14px;
        font-weight: 500;
      }

      /* 用户下拉菜单 */
      .user-menu-header {
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        background: #f8fafc;
      }

      .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        background: #e2e8f0;
      }

      .user-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .user-info .username {
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
      }

      .user-type-badge {
        font-size: 12px;
        color: #64748b;
        background: #e2e8f0;
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 4px;
      }

      /* 汉堡菜单 */
      .hamburger-menu {
        color: white;
        display: none;
      }

      .mobile-menu-header {
        padding: 12px 16px;
        font-weight: 600;
        color: #64748b;
        border-bottom: 1px solid #e2e8f0;
      }

      /* 搜索面板 */
      .search-panel {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 64px;
        z-index: 1001;
      }

      .search-container {
        width: 100%;
        max-width: 600px;
        margin: 0 24px;
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
      }

      .search-icon {
        color: #64748b;
        font-size: 24px;
        width: 24px;
        height: 24px;
      }

      .search-input {
        flex: 1;
        border: none;
        outline: none;
        font-size: 16px;
        color: #0f172a;
      }

      .search-input::placeholder {
        color: #94a3b8;
      }

      .search-hint {
        font-size: 12px;
        color: #94a3b8;
        padding: 4px 8px;
        background: #f1f5f9;
        border-radius: 4px;
      }

      /* 响应式 */
      @media (max-width: 1024px) {
        .navbar-container {
          gap: 16px;
        }

        .nav-link span {
          display: none;
        }

        .nav-link {
          padding: 8px 12px;
        }
      }

      @media (max-width: 768px) {
        .navbar-nav {
          display: none;
        }

        .hamburger-menu {
          display: block;
        }

        .username {
          display: none;
        }

        .navbar-container {
          padding: 0 16px;
        }
      }
    `,
  ],
})
export class UserNavbarComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  userType: string | undefined;
  isMobile = false;
  unreadNotifications = 0;
  showSearch = false;

  readonly ROUTES = ROUTES;

  // 按照 PRD 第 6.5 节规范的导航菜单
  navItems: NavItem[] = [
    { route: ROUTES.USER.DASHBOARD, label: '首页', icon: 'home' },
    { route: ROUTES.USER.COURSES, label: '课程', icon: 'school' },
    { route: '/ai-edu/coding', label: 'AI 编程', icon: 'code' },
    { route: '/ar-lab', label: 'AR 实验室', icon: 'view_in_ar' },
    { route: '/creativity-engine', label: '创作', icon: 'palette' },
  ];

  private destroy$ = new Subject<void>();
  // 保存 resize handler 引用，用于正确移除监听器
  private boundCheckScreenWidth = () => this.checkScreenWidth();

  constructor(
    private userCenterService: UserCenterService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUserData();
    this.checkScreenWidth();
    window.addEventListener('resize', this.boundCheckScreenWidth);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', this.boundCheckScreenWidth);
  }

  private loadUserData(): void {
    this.currentUser = this.userCenterService.getCurrentUser();
    this.userType = this.currentUser?.userType;

    // 使用 takeUntil 确保订阅在组件销毁时自动取消
    this.userCenterService.currentUser$.pipe(
      takeUntil(this.destroy$)
    ).subscribe((user) => {
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
    void this.router.navigate([path]);
  }

  toggleSearch(): void {
    this.showSearch = !this.showSearch;
  }

  logout(): void {
    this.userCenterService.logout();
  }

  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
  }
}
