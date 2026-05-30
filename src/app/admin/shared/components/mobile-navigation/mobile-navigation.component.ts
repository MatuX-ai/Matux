import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule } from '@angular/router';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';

import { PermissionService } from '../../services/permission.service';

/** 菜单项接口 */
interface MenuItem {
  id: string;
  title: string;
  icon: string;
  route: string;
}

/** 菜单组接口 */
interface MenuGroup {
  title: string;
  items: MenuItem[];
}

@Component({
  selector: 'app-mobile-navigation',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatListModule, RouterModule],
  template: `
    <nav class="mobile-nav" [class.open]="isMenuOpen">
      <!-- 移动端顶部栏 -->
      <div class="mobile-top-bar">
        <button mat-icon-button (click)="toggleMenu()" class="menu-toggle">
          <mat-icon>{{ isMenuOpen ? 'close' : 'menu' }}</mat-icon>
        </button>
        <div class="logo">
          <h2>管理后台</h2>
        </div>
        <button mat-icon-button class="notification-btn">
          <mat-icon>notifications</mat-icon>
          <span class="notification-badge" *ngIf="unreadNotifications > 0">
            {{ unreadNotifications }}
          </span>
        </button>
      </div>

      <!-- 侧边菜单 -->
      <div class="side-menu" [class.open]="isMenuOpen">
        <div class="menu-content">
          <!-- 用户信息 -->
          <div class="user-profile">
            <div class="avatar">
              <mat-icon>account_circle</mat-icon>
            </div>
            <div class="user-info">
              <h3>{{ currentUser?.username || '管理员' }}</h3>
              <p>{{ currentUser?.email || 'admin@example.com' }}</p>
            </div>
          </div>

          <!-- 菜单项 -->
          <div class="menu-items">
            <div class="menu-group" *ngFor="let group of menuGroups">
              <h3 class="group-title">{{ group.title }}</h3>
              <a
                mat-list-item
                *ngFor="let item of group.items"
                [routerLink]="item.route"
                routerLinkActive="active"
                (click)="onMenuItemClick()"
                class="menu-item"
              >
                <mat-icon>{{ item.icon }}</mat-icon>
                <span>{{ item.title }}</span>
              </a>
            </div>
          </div>

          <!-- 底部操作 -->
          <div class="menu-footer">
            <button mat-button class="logout-btn" (click)="logout()">
              <mat-icon>exit_to_app</mat-icon>
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 遮罩层 -->
      <div class="overlay" [class.visible]="isMenuOpen" (click)="closeMenu()"></div>
    </nav>
  `,
  styles: [
    `
      .mobile-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 300;
      }

      .mobile-top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        height: 64px;
        background: #2196f3;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .logo h2 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 500;
      }

      .menu-toggle {
        color: white;
      }

      .notification-btn {
        position: relative;
        color: white;
      }

      .notification-badge {
        position: absolute;
        top: 4px;
        right: 4px;
        background: #f44336;
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .side-menu {
        position: fixed;
        top: 64px;
        left: 0;
        bottom: 0;
        width: 100%;
        max-width: 280px;
        background: white;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
        z-index: 500;
      }

      .side-menu.open {
        transform: translateX(0);
      }

      .menu-content {
        height: calc(100vh - 64px);
        display: flex;
        flex-direction: column;
        overflow-y: auto;
      }

      .user-profile {
        padding: 24px 16px;
        border-bottom: 1px solid #eee;
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #e3f2fd;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #2196f3;
      }

      .avatar mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
      }

      .user-info h3 {
        margin: 0 0 4px 0;
        font-size: 1rem;
        font-weight: 500;
      }

      .user-info p {
        margin: 0;
        font-size: 0.875rem;
        color: #666;
      }

      .menu-items {
        flex: 1;
        padding: 16px 0;
        overflow-y: auto;
      }

      .menu-group {
        margin-bottom: 24px;
      }

      .group-title {
        padding: 0 16px 8px 16px;
        font-size: 0.875rem;
        font-weight: 500;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .menu-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        text-decoration: none;
        color: #333;
        transition: all 0.2s ease;
        border-left: 3px solid transparent;
      }

      .menu-item:hover {
        background: #f5f5f5;
      }

      .menu-item.active {
        background: #e3f2fd;
        border-left-color: #2196f3;
        color: #2196f3;
      }

      .menu-item mat-icon {
        margin-right: 16px;
        color: #666;
      }

      .menu-item.active mat-icon {
        color: #2196f3;
      }

      .menu-footer {
        padding: 16px;
        border-top: 1px solid #eee;
      }

      .logout-btn {
        width: 100%;
        justify-content: flex-start;
        color: #f44336;
      }

      .logout-btn mat-icon {
        margin-right: 8px;
      }

      .overlay {
        position: fixed;
        top: 64px;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 400;
      }

      .overlay.visible {
        opacity: 1;
        visibility: visible;
      }

      /* 桌面端隐藏 */
      @media (min-width: 1024px) {
        .mobile-nav {
          display: none;
        }
      }

      /* 平板端优化 */
      @media (min-width: 768px) and (max-width: 1023px) {
        .side-menu {
          max-width: 320px;
        }
      }

      /* 高分辨率屏幕 */
      @media (-webkit-min-device-pixel-ratio: 2) {
        .avatar mat-icon {
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
      }

      /* 深色模式支持 */
      @media (prefers-color-scheme: dark) {
        .side-menu {
          background: #1e1e1e;
          color: #ffffff;
        }

        .user-profile {
          border-bottom-color: #333;
        }

        .menu-item {
          color: #ffffff;
        }

        .menu-item:hover {
          background: #333;
        }

        .menu-item.active {
          background: #2196f3;
          color: #ffffff;
        }

        .menu-footer {
          border-top-color: #333;
        }

        .group-title {
          color: #aaa;
        }
      }
    `,
  ],
})
export class MobileNavigationComponent implements OnInit {
  isMenuOpen = false;
  unreadNotifications = 3;
  currentUser: any = null;
  menuGroups: MenuGroup[] = [];

  isHandset$: Observable<boolean> = this.breakpointObserver
    .observe([Breakpoints.Handset, Breakpoints.Tablet])
    .pipe(
      map((result) => result.matches),
      shareReplay()
    );

  constructor(
    private breakpointObserver: BreakpointObserver,
    private permissionService: PermissionService
  ) {}

  ngOnInit(): void {
    this.currentUser = this.permissionService.getCurrentUserSync();
    this.buildMenu();
  }

  toggleMenu(): void {
    this.isMenuOpen = !this.isMenuOpen;
  }

  closeMenu(): void {
    this.isMenuOpen = false;
  }

  onMenuItemClick(): void {
    // 关闭菜单
    this.closeMenu();
  }

  logout(): void {
    // 实现登出逻辑
    this.permissionService.clearCurrentUser();
    // 跳转到登录页面
    window.location.href = '/admin/login';
  }

  private buildMenu(): void {
    const accessibleItems = this.permissionService.getAccessibleMenuItems();

    this.menuGroups = [
      {
        title: '核心功能',
        items: accessibleItems.filter((item) =>
          ['dashboard', 'users', 'licenses', 'subscriptions'].includes(item.id)
        ),
      },
      {
        title: '业务管理',
        items: accessibleItems.filter((item) => ['payments', 'ai'].includes(item.id)),
      },
      {
        title: '系统管理',
        items: accessibleItems.filter((item) => ['reports', 'system'].includes(item.id)),
      },
    ].filter((group) => group.items.length > 0);
  }
}
