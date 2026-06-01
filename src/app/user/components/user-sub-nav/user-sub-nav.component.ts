/**
 * 用户中心子导航组件（水平导航条）
 *
 * 位于头部导航条下方，提供用户中心的主要导航功能
 */

import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';
import { UserCenterMenuItem, UserCenterService } from '../../services/user-center.service';

@Component({
  selector: 'app-user-sub-nav',
  standalone: true,
  imports: [CommonModule, RouterModule, MatTabsModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="sub-nav-container">
      <nav class="sub-nav">
        <!-- 用户信息区域 -->
        <div class="user-info-section" *ngIf="currentUser">
          <div class="user-avatar-small">
            <img [src]="currentUser.avatar || 'assets/icons/user.svg'" alt="用户头像" />
          </div>
          <div class="user-details-small">
            <span class="username">{{ currentUser.username || '用户' }}</span>
            <span class="user-type-badge">{{ getUserTypeLabel() }}</span>
          </div>
        </div>

        <!-- 导航链接 -->
        <div class="nav-links">
          <a
            *ngFor="let item of menuItems"
            class="nav-link"
            [routerLink]="item.route"
            routerLinkActive="active"
            [matTooltip]="item.label"
          >
            <mat-icon class="nav-icon">{{ item.icon }}</mat-icon>
            <span class="nav-label">{{ item.label }}</span>
          </a>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions">
          <button mat-icon-button [matTooltip]="'刷新页面'" (click)="refreshPage()">
            <mat-icon>refresh</mat-icon>
          </button>
          <button mat-icon-button [matTooltip]="'返回首页'" routerLink="/dashboard">
            <mat-icon>home</mat-icon>
          </button>
          <button mat-icon-button [matTooltip]="'用户设置'" routerLink="/user/profile">
            <mat-icon>settings</mat-icon>
          </button>
        </div>
      </nav>
    </div>
  `,
  styles: [
    `
      .sub-nav-container {
        background: white;
        border-bottom: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        position: sticky;
        top: 60px; /* 头部导航条高度 */
        z-index: 999;
      }

      .sub-nav {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 24px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      /* 用户信息区域 */
      .user-info-section {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
        margin-right: 24px;
      }

      .user-avatar-small {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        overflow: hidden;
        background: #f5f5f5;
      }

      .user-avatar-small img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .user-details-small {
        display: flex;
        flex-direction: column;
      }

      .username {
        font-size: 14px;
        font-weight: 600;
        color: #333;
        line-height: 1.2;
      }

      .user-type-badge {
        font-size: 11px;
        color: #666;
        background: #f0f0f0;
        padding: 1px 6px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 2px;
      }

      /* 导航链接 */
      .nav-links {
        flex: 1;
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding: 0 16px;
        scrollbar-width: thin;
      }

      .nav-links::-webkit-scrollbar {
        height: 4px;
      }

      .nav-links::-webkit-scrollbar-track {
        background: #f1f1f1;
      }

      .nav-links::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 2px;
      }

      .nav-link {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        color: #666;
        text-decoration: none;
        border-radius: 8px;
        transition: all 0.2s ease;
        white-space: nowrap;
        border: 1px solid transparent;
      }

      .nav-link:hover {
        background: #f5f5f5;
        color: #333;
      }

      .nav-link.active {
        background: #e3f2fd;
        color: #1976d2;
        border-color: #1976d2;
      }

      .nav-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }

      .nav-label {
        font-size: 14px;
        font-weight: 500;
      }

      /* 快捷操作 */
      .quick-actions {
        display: flex;
        gap: 8px;
        flex-shrink: 0;
        margin-left: 16px;
      }

      .quick-actions button {
        color: #666;
      }

      .quick-actions button:hover {
        color: #1976d2;
      }

      @media (max-width: 768px) {
        .sub-nav {
          padding: 0 16px;
          height: 48px;
        }

        .user-info-section {
          display: none;
        }

        .nav-links {
          padding: 0;
          gap: 4px;
        }

        .nav-link {
          padding: 8px 12px;
        }

        .nav-label {
          display: none;
        }

        .nav-icon {
          margin: 0;
        }

        .quick-actions {
          margin-left: 8px;
        }

        .quick-actions button {
          width: 32px;
          height: 32px;
        }
      }

      @media (max-width: 480px) {
        .quick-actions {
          display: none;
        }
      }
    `,
  ],
})
export class UserSubNavComponent {
  currentUser: any = null;
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
      teacher: '教师',
      parent: '家长',
    };

    return typeMap[userType] || userType;
  }

  /**
   * 刷新页面
   */
  refreshPage(): void {
    window.location.reload();
  }
}
