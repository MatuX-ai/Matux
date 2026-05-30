import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { RouterModule } from '@angular/router';

import { AdminAuthService } from '../../../auth/admin-auth.service';
import { MenuItem } from '../admin-sidebar/admin-sidebar.config';
import { AdminSidebarService } from '../admin-sidebar/admin-sidebar.service';

@Component({
  selector: 'app-admin-mobile-nav',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatListModule,
    MatMenuModule,
  ],
  template: `
    <div class="admin-mobile-nav" *ngIf="isMobile$ | async">
      <!-- 顶部栏 -->
      <header class="mobile-header">
        <button mat-icon-button (click)="toggleMenu()" class="menu-toggle">
          <mat-icon>{{ isMenuOpen ? 'close' : 'menu' }}</mat-icon>
        </button>

        <div class="logo">
          <h2>管理后台</h2>
        </div>

        <button mat-icon-button [matMenuTriggerFor]="userMenu" class="user-menu-btn">
          <mat-icon>account_circle</mat-icon>
        </button>

        <mat-menu #userMenu="matMenu">
          <button mat-menu-item (click)="logout()">
            <mat-icon>exit_to_app</mat-icon>
            <span>退出登录</span>
          </button>
        </mat-menu>
      </header>

      <!-- 遮罩层 -->
      <div class="overlay" [class.visible]="isMenuOpen" (click)="closeMenu()"></div>

      <!-- 侧边菜单 -->
      <div class="mobile-sidebar" [class.open]="isMenuOpen">
        <div class="sidebar-content">
          <!-- 用户信息卡片 -->
          <div class="user-info">
            <mat-icon class="user-avatar">account_circle</mat-icon>
            <div class="user-details">
              <h3>{{ currentUser?.username || '管理员' }}</h3>
              <p>{{ currentUser?.email || 'admin@example.com' }}</p>
            </div>
          </div>

          <!-- 菜单列表 -->
          <nav class="mobile-menu">
            <div *ngFor="let group of menuGroups" class="menu-group">
              <div class="group-title">{{ group.title }}</div>
              <a
                mat-list-item
                *ngFor="let item of group.items"
                [routerLink]="item.route"
                routerLinkActive="active"
                (click)="onMenuItemClick()"
                class="menu-item"
              >
                <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
                <span matListItemTitle>{{ item.title }}</span>
              </a>
            </div>
          </nav>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .admin-mobile-nav {
        display: none;
      }

      @media (max-width: 767px) {
        .admin-mobile-nav {
          display: block;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 300;
        }
      }

      .mobile-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        height: 56px;
        background: #2196f3;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }

      .logo h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 500;
      }

      .menu-toggle {
        color: white;
      }

      .user-menu-btn {
        color: white;
      }

      .overlay {
        position: fixed;
        top: 56px;
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

      .mobile-sidebar {
        position: fixed;
        top: 56px;
        left: 0;
        bottom: 0;
        width: 100%;
        max-width: 280px;
        background: white;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        z-index: 500;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
      }

      .mobile-sidebar.open {
        transform: translateX(0);
      }

      .sidebar-content {
        height: calc(100vh - 56px);
        display: flex;
        flex-direction: column;
        overflow-y: auto;
      }

      .user-info {
        display: flex;
        align-items: center;
        padding: 24px 16px;
        border-bottom: 1px solid #e0e0e0;
        gap: 16px;
      }

      .user-avatar {
        width: 48px;
        height: 48px;
        font-size: 48px;
        color: #2196f3;
      }

      .user-details h3 {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 500;
      }

      .user-details p {
        margin: 0;
        font-size: 14px;
        color: #666;
      }

      .mobile-menu {
        flex: 1;
        padding: 16px 0;
      }

      .menu-group {
        margin-bottom: 24px;
      }

      .group-title {
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 600;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .menu-item {
        height: 48px;
        border-left: 3px solid transparent;
      }

      .menu-item:hover {
        background-color: #f5f5f5;
      }

      .menu-item.active {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
        color: #2196f3;
      }

      .menu-item mat-icon {
        color: #666;
      }

      .menu-item.active mat-icon {
        color: #2196f3;
      }
    `,
  ],
})
export class AdminMobileNavComponent implements OnInit {
  isMenuOpen = false;
  currentUser: { username?: string; email?: string } | null = null;
  menuGroups: { title: string; items: MenuItem[] }[] = [];
  isMobile$ = this.breakpointObserver.observe([Breakpoints.Handset]);

  constructor(
    private breakpointObserver: BreakpointObserver,
    private adminAuthService: AdminAuthService,
    private sidebarService: AdminSidebarService
  ) {}

  ngOnInit(): void {
    this.currentUser = this.adminAuthService.getCurrentUser();
    this.loadMenu();
  }

  toggleMenu(): void {
    this.isMenuOpen = !this.isMenuOpen;
  }

  closeMenu(): void {
    this.isMenuOpen = false;
  }

  onMenuItemClick(): void {
    this.closeMenu();
  }

  logout(): void {
    this.adminAuthService.logout();
    // 延迟跳转以确保登出完成
    setTimeout(() => {
      window.location.href = '/admin/login';
    }, 100);
  }

  private loadMenu(): void {
    // 获取所有可访问的菜单项（这里暂时不过滤权限）
    const allItems = this.sidebarService.getAllMenuItems().map((item) => item.id);
    this.menuGroups = this.sidebarService.getFilteredMenuGroups(allItems);
  }
}
