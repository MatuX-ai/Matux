/**
 * 用户侧边栏组件
 *
 * 显示用户信息和导航菜单
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
    <div class="sidebar" [class.mobile]="isMobile" [class.open]="opened">
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
    </div>
  `,
  styles: [
    `
      .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        max-width: 260px;
        height: 100vh;
        background: white;
        border-right: 1px solid #e0e0e0;
        z-index: 300;
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        overflow-y: auto;
      }

      .sidebar.open {
        transform: translateX(0);
      }

      .sidebar:not(.mobile) {
        transform: translateX(0);
      }

      .user-info-card {
        padding: 24px;
        border-bottom: 1px solid #e0e0e0;
        text-align: center;
      }

      .avatar {
        width: 80px;
        height: 80px;
        margin: 0 auto 16px;
        border-radius: 50%;
        overflow: hidden;
        background: #f5f5f5;
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
        font-size: 18px;
        font-weight: 600;
        color: #333;
      }

      .user-type {
        margin: 0;
        font-size: 14px;
        color: #666;
      }

      .nav-menu {
        padding: 16px 0;
      }

      .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 24px;
        color: #333;
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
      }

      .nav-item:hover {
        background: #f5f5f5;
      }

      .nav-item.active {
        background: #e3f2fd;
        color: #1976d2;
        border-left: 3px solid #1976d2;
      }

      .nav-icon {
        margin-right: 16px;
        width: 24px;
        height: 24px;
        font-size: 20px;
      }

      .nav-label {
        font-size: 16px;
      }

      @media (max-width: 767px) {
        .sidebar {
          box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
          max-width: 280px;
        }
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
    // 获取当前用户
    this.currentUser = this.userCenterService.getCurrentUser();

    // 获取菜单项
    this.menuItems = this.userCenterService.getSidebarMenu();
  }

  /**
   * 获取用户类型标签
   */
  getUserTypeLabel(): string {
    const userType = this.currentUser?.userType;
    if (!userType) return '用户';

    const typeMap: Record<string, string> = {
      student: '学生',
    };

    return typeMap[userType] || '用户';
  }

  /**
   * 处理菜单点击
   */
  onMenuClick(): void {
    this.menuClick.emit();
  }
}
