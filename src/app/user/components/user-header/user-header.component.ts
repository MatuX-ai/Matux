/**
 * 用户头部组件
 *
 * 显示顶部导航栏和操作菜单
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { UserCenterService } from '../../services/user-center.service';

@Component({
  selector: 'app-user-header',
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
    <mat-toolbar class="header-toolbar">
      <!-- 侧边栏切换按钮 -->
      <button
        mat-icon-button
        class="menu-toggle"
        (click)="toggleSidebarHandler()"
        *ngIf="isMobile || !sidebarOpen"
      >
        <mat-icon>menu</mat-icon>
      </button>

      <!-- 页面标题 -->
      <h1 class="page-title">{{ getPageTitle() }}</h1>

      <div class="spacer"></div>

      <!-- 用户菜单 -->
      <button mat-icon-button [matMenuTriggerFor]="userMenu">
        <mat-icon>account_circle</mat-icon>
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
    </mat-toolbar>
  `,
  styles: [
    `
      .header-toolbar {
        background: var(--color-surface);
        color: var(--color-text-primary);
        border-bottom: 1px solid var(--color-divider);
        height: 64px;
        padding: 0 16px;
        position: sticky;
        top: 0;
        z-index: 100;
      }

      .menu-toggle {
        margin-right: 16px;
      }

      .page-title {
        font-size: 20px;
        font-weight: 600;
        margin: 0;
      }

      .spacer {
        flex: 1;
      }

      .user-menu-header {
        padding: 16px;
        display: flex;
        align-items: center;
        background: var(--color-background);
      }

      .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        margin-right: 12px;
        background: var(--color-divider);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .user-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .user-info {
        flex: 1;
      }

      .username {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 4px;
      }

      .user-type {
        font-size: 14px;
        color: var(--color-text-secondary);
      }

      ::ng-deep .mat-divider {
        margin: 8px 0;
      }
    `,
  ],
})
export class UserHeaderComponent {
  @Input() sidebarOpen = false;
  @Input() isMobile = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  currentUser: any = null;

  constructor(
    private userCenterService: UserCenterService,
    private authService: AuthService
  ) {
    this.loadUserData();
  }

  private loadUserData(): void {
    this.currentUser = this.userCenterService.getCurrentUser();
  }

  /**
   * 获取页面标题
   */
  getPageTitle(): string {
    // 这里可以根据当前路由动态获取标题
    return '用户中心';
  }

  /**
   * 获取用户类型标签
   */
  getUserTypeLabel(): string {
    const userType = this.currentUser?.userType;
    if (!userType) return '用户';

    const typeMap: Record<string, string> = {
      student: '学生',
      teacher: '教师',
      parent: '家长',
    };

    return typeMap[userType] || userType;
  }

  /**
   * 切换侧边栏
   */
  toggleSidebarHandler(): void {
    this.toggleSidebar.emit();
  }

  /**
   * 登出
   */
  logout(): void {
    this.userCenterService.logout();
  }
}
