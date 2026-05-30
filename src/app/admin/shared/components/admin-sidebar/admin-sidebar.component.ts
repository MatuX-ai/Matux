import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';

import { MenuItem } from './admin-sidebar.config';
import { AdminSidebarService } from './admin-sidebar.service';

@Component({
  selector: 'app-admin-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatListModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="admin-sidebar" [class.collapsed]="collapsed">
      <!-- Logo 区域 -->
      <div class="sidebar-header">
        <div class="logo-content" *ngIf="!collapsed">
          <h2 class="logo-title">管理后台</h2>
        </div>
        <button
          mat-icon-button
          class="collapse-btn"
          (click)="toggleCollapse()"
          matTooltip="{{ collapsed ? '展开' : '折叠' }}"
        >
          <mat-icon>{{ collapsed ? 'chevron_right' : 'chevron_left' }}</mat-icon>
        </button>
      </div>

      <!-- 菜单列表 -->
      <nav class="sidebar-nav">
        <mat-nav-list>
          <!-- 按分组显示菜单 -->
          <div *ngFor="let group of menuGroups" class="menu-group">
            <div class="group-title" *ngIf="!collapsed">
              {{ group.title }}
            </div>

            <a
              mat-list-item
              *ngFor="let item of group.items"
              [routerLink]="item.route"
              routerLinkActive="active"
              [matTooltip]="collapsed ? item.title : ''"
              matTooltipPosition="right"
              class="menu-item"
            >
              <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
              <span matListItemTitle *ngIf="!collapsed">{{ item.title }}</span>
            </a>
          </div>

          <!-- 未分组的菜单项 -->
          <div *ngIf="ungroupedItems.length > 0 && !hasGroups" class="menu-group">
            <a
              mat-list-item
              *ngFor="let item of ungroupedItems"
              [routerLink]="item.route"
              routerLinkActive="active"
              [matTooltip]="collapsed ? item.title : ''"
              matTooltipPosition="right"
              class="menu-item"
            >
              <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
              <span matListItemTitle *ngIf="!collapsed">{{ item.title }}</span>
            </a>
          </div>
        </mat-nav-list>
      </nav>
    </div>
  `,
  styles: [
    `
      .admin-sidebar {
        width: 256px;
        height: 100vh;
        background: white;
        border-right: 1px solid #e0e0e0;
        display: flex;
        flex-direction: column;
        transition: width 0.3s ease;
        overflow: hidden;
        flex-shrink: 0;
      }

      .admin-sidebar.collapsed {
        width: 64px;
      }

      .sidebar-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        border-bottom: 1px solid #e0e0e0;
        min-height: 64px;
      }

      .logo-content {
        flex: 1;
        text-align: center;
      }

      .logo-title {
        margin: 0;
        color: #2196f3;
        font-size: 20px;
        font-weight: 600;
        white-space: nowrap;
      }

      .collapse-btn {
        flex-shrink: 0;
        margin-left: 8px;
      }

      .sidebar-nav {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
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
        transition: all 0.2s ease;
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
        margin-right: 16px;
        color: #666;
      }

      .menu-item.active mat-icon {
        color: #2196f3;
      }

      /* 折叠状态下的样式调整 */
      .admin-sidebar.collapsed .sidebar-header {
        justify-content: center;
        padding: 16px 8px;
      }

      .admin-sidebar.collapsed .logo-title {
        display: none;
      }

      .admin-sidebar.collapsed .group-title {
        display: none;
      }

      .admin-sidebar.collapsed .menu-item {
        justify-content: center;
        padding: 12px;
      }

      .admin-sidebar.collapsed .menu-item mat-icon {
        margin-right: 0;
      }

      /* 滚动条样式 */
      .sidebar-nav::-webkit-scrollbar {
        width: 6px;
      }

      .sidebar-nav::-webkit-scrollbar-track {
        background: #f5f5f5;
      }

      .sidebar-nav::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 3px;
      }

      .sidebar-nav::-webkit-scrollbar-thumb:hover {
        background: #999;
      }

      /* 响应式适配 - 移动端 */
      @media (max-width: 767px) {
        .admin-sidebar {
          max-width: 280px;
        }

        .admin-sidebar.collapsed {
          max-width: 0;
        }
      }
    `,
  ],
})
export class AdminSidebarComponent implements OnInit {
  /** 是否可访问的菜单项 ID 列表（用于权限过滤） */
  @Input() accessibleMenuIds: string[] = [];

  /** 是否默认折叠 */
  @Input() defaultCollapsed = false;

  /** 是否使用分组显示 */
  @Input() useGroups = true;

  /** 侧边栏折叠状态变化事件 */
  @Output() collapsedChange = new EventEmitter<boolean>();

  menuGroups: { title: string; items: MenuItem[] }[] = [];
  ungroupedItems: MenuItem[] = [];
  hasGroups = true;
  collapsed = false;

  constructor(private sidebarService: AdminSidebarService) {}

  ngOnInit(): void {
    // 优先从 localStorage 恢复状态，如果没有则使用 defaultCollapsed
    const savedState = localStorage.getItem('admin_sidebar_collapsed');
    if (savedState !== null) {
      this.collapsed = savedState === 'true';
    } else {
      this.collapsed = this.defaultCollapsed;
    }

    // 发送初始状态通知父组件
    this.collapsedChange.emit(this.collapsed);

    this.loadMenu();
  }

  /**
   * 加载菜单数据
   */
  private loadMenu(): void {
    // 如果没有传入权限列表，使用所有菜单
    const accessibleIds =
      this.accessibleMenuIds.length > 0
        ? this.accessibleMenuIds
        : this.sidebarService.getAllMenuItems().map((item) => item.id);

    if (this.useGroups) {
      // 按分组加载
      this.menuGroups = this.sidebarService.getFilteredMenuGroups(accessibleIds);
      this.hasGroups = this.menuGroups.length > 0;
    } else {
      // 不分组，平铺显示
      this.ungroupedItems = this.sidebarService.getFilteredMenuItems(accessibleIds);
      this.hasGroups = false;
    }
  }

  /**
   * 切换折叠状态
   */
  toggleCollapse(): void {
    this.collapsed = !this.collapsed;
    console.log('[AdminSidebar] 切换折叠状态:', this.collapsed);

    // 发送状态变化事件
    this.collapsedChange.emit(this.collapsed);
    console.log('[AdminSidebar] 已发送 collapsedChange 事件:', this.collapsed);

    // 保存状态到 localStorage
    localStorage.setItem('admin_sidebar_collapsed', this.collapsed.toString());
  }

  /**
   * 从 localStorage 恢复折叠状态
   */
  restoreCollapseState(): void {
    const savedState = localStorage.getItem('admin_sidebar_collapsed');
    if (savedState !== null) {
      this.collapsed = savedState === 'true';
    }
  }
}
