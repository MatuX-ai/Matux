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

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { UserCenterMenuItem, UserCenterService } from '../../services/user-center.service';

@Component({
  selector: 'app-user-sub-nav',
  standalone: true,
  imports: [CommonModule, RouterModule, MatTabsModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="sub-nav-container">
      <nav class="sub-nav">
        <!-- 面包屑导航 -->
        <div class="breadcrumb">
          <a routerLink="/user/dashboard" class="breadcrumb-link">
            <mat-icon class="breadcrumb-icon">home</mat-icon>
            <span>首页</span>
          </a>
          <mat-icon class="breadcrumb-separator">chevron_right</mat-icon>
          <span class="breadcrumb-current">{{ currentPageTitle }}</span>
        </div>

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
          <button mat-icon-button [matTooltip]="'刷新'" (click)="refreshPage()">
            <mat-icon>refresh</mat-icon>
          </button>
          <button mat-icon-button [matTooltip]="'设置'" routerLink="/user/profile">
            <mat-icon>settings</mat-icon>
          </button>
        </div>
      </nav>
    </div>
  `,
  styles: [
    `
      .sub-nav-container {
        background: var(--matux-color-surface, #ffffff);
        border-bottom: 1px solid var(--matux-color-border, #e2e8f0);
        height: 48px;
      }

      .sub-nav {
        height: 100%;
        padding: 0 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .breadcrumb {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        color: var(--matux-color-text-secondary, #475569);
      }

      .breadcrumb-link {
        display: flex;
        align-items: center;
        gap: 4px;
        color: var(--matux-color-text-secondary, #475569);
        text-decoration: none;
        border-radius: 4px;
        padding: 2px 6px;
        transition: all 0.15s;
      }

      .breadcrumb-link:hover {
        background: var(--matux-color-brand-100, #f1f5f9);
        color: var(--matux-color-secondary, #3b82f6);
      }

      .breadcrumb-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      .breadcrumb-separator {
        font-size: 16px;
        width: 16px;
        height: 16px;
        color: var(--matux-color-text-disabled, #94a3b8);
      }

      .breadcrumb-current {
        font-weight: 600;
        color: var(--matux-color-text-primary, #0f172a);
        padding: 2px 6px;
      }

      .quick-actions {
        display: flex;
        gap: 4px;
        flex-shrink: 0;
      }

      .quick-actions button {
        color: var(--matux-color-text-secondary, #475569);
        width: 32px;
        height: 32px;
        line-height: 32px;
      }

      .quick-actions button:hover {
        color: var(--matux-color-secondary, #3b82f6);
        background: var(--matux-color-brand-100, #f1f5f9);
      }

      .quick-actions mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }

      @media (max-width: 767px) {
        .sub-nav {
          padding: 0 16px;
        }

        .breadcrumb-link span {
          display: none;
        }
      }
    `,
  ],
})
export class UserSubNavComponent {
  currentUser: User | null = null;
  menuItems: UserCenterMenuItem[] = [];
  currentPageTitle = '仪表板';

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

  /**
   * 获取用户类型标签
   */
  getUserTypeLabel(): string {
    const user = this.currentUser;
    if (!user?.userType) return '用户';
    const typeMap: Record<string, string> = {
      student: '学生',
      teacher: '教师',
      parent: '家长',
    };
    return typeMap[user.userType] || user.userType;
  }

  /**
   * 刷新页面
   */
  refreshPage(): void {
    window.location.reload();
  }
}
