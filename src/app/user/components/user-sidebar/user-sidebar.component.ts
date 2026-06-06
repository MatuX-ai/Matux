/**
 * 用户侧边栏组件
 *
 * 桌面端持久可见（260px），移动端覆盖层模式
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterModule } from '@angular/router';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { UserCenterMenuItem, UserCenterService } from '../../services/user-center.service';

@Component({
  selector: 'app-user-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatListModule, MatIconModule, MatCardModule],
  template: `
    <div
      class="sidebar"
      [class.desktop]="!isMobile"
      [class.mobile]="isMobile"
      [class.open]="opened"
    >
      <!-- 用户信息卡片 -->
      <div class="user-info-card" *ngIf="currentUser">
        <div class="avatar">
          <img [src]="currentUser.avatar || 'assets/icons/user.svg'" alt="用户头像" />
        </div>
        <div class="user-details">
          <h3 class="username">{{ currentUser.username || '用户' }}</h3>
          <p class="user-type">{{ getUserTypeLabel() }}</p>
        </div>
      </div>

      <!-- 导航菜单 -->
      <nav class="nav-menu">
        <a
          *ngFor="let item of menuItems"
          class="nav-item"
          [routerLink]="item.route"
          routerLinkActive="active"
          (click)="onMenuClick()"
        >
          <mat-icon class="nav-icon">{{ item.icon }}</mat-icon>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </nav>

      <!-- 底部信息 -->
      <div class="sidebar-footer" *ngIf="!isMobile">
        <span class="version">v1.0.0</span>
      </div>
    </div>
  `,
  styles: [
    `
      .sidebar {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--matux-color-surface, #ffffff);
        overflow-y: auto;
      }

      .sidebar.desktop {
        border-right: 1px solid var(--matux-color-border, #e2e8f0);
      }

      .sidebar.mobile {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        max-width: 280px;
        height: 100vh;
        z-index: 300;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
      }

      .sidebar.mobile.open {
        transform: translateX(0);
      }

      .user-info-card {
        padding: 24px;
        border-bottom: 1px solid var(--matux-color-divider, #e2e8f0);
        text-align: center;
        flex-shrink: 0;
      }

      .avatar {
        width: 64px;
        height: 64px;
        margin: 0 auto 12px;
        border-radius: 50%;
        overflow: hidden;
        background: var(--matux-color-brand-100, #f1f5f9);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .username {
        margin: 0 0 4px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--matux-color-text-primary, #0f172a);
      }

      .user-type {
        margin: 0;
        font-size: 13px;
        color: var(--matux-color-text-secondary, #475569);
      }

      .nav-menu {
        padding: 8px 0;
        flex: 1;
        overflow-y: auto;
      }

      .nav-item {
        display: flex;
        align-items: center;
        padding: 10px 20px;
        margin: 2px 8px;
        color: var(--matux-color-text-secondary, #475569);
        text-decoration: none;
        border-radius: 8px;
        transition: all 0.15s ease;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
      }

      .nav-item:hover {
        background: var(--matux-color-brand-100, #f1f5f9);
        color: var(--matux-color-text-primary, #0f172a);
      }

      .nav-item.active {
        background: var(--matux-color-secondary, #3b82f6);
        color: #ffffff;
      }

      .nav-icon {
        margin-right: 12px;
        width: 20px;
        height: 20px;
        font-size: 20px;
      }

      .nav-item.active .nav-icon {
        color: #ffffff;
      }

      .nav-label {
        white-space: nowrap;
      }

      .sidebar-footer {
        padding: 12px 20px;
        border-top: 1px solid var(--matux-color-divider, #e2e8f0);
        flex-shrink: 0;
      }

      .version {
        font-size: 12px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }
    `,
  ],
})
export class UserSidebarComponent {
  @Input() opened = false;
  @Input() isMobile = false;
  @Output() menuClick = new EventEmitter<void>();

  currentUser: User | null = null;
  menuItems: UserCenterMenuItem[] = [];

  constructor(
    private userCenterService: UserCenterService,
    private authService: AuthService
  ) {
    this.loadUserData();
  }

  private loadUserData(): void {
    this.currentUser = this.userCenterService.getCurrentUser();
    this.menuItems = this.userCenterService.getSidebarMenu();
  }

  getUserTypeLabel(): string {
    const userType = this.currentUser?.userType;
    if (!userType) return '用户';
    const typeMap: Record<string, string> = {
      student: '学生',
    };
    return typeMap[userType] || '用户';
  }

  onMenuClick(): void {
    this.menuClick.emit();
  }
}
