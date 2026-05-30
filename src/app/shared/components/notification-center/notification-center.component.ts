/**
 * Notification Center Component
 *
 * 通知中心组件，展示和管理用户通知
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Observable, Subject, takeUntil } from 'rxjs';

interface NotificationResponse {
  notifications: Notification[];
}

interface NotificationService {
  getNotifications(params: { page: number; size: number }): Observable<NotificationResponse>;
  getUnreadCount(userId: number): Observable<UnreadCount>;
  markAsRead(notificationId: number): Observable<{ success: boolean }>;
  archiveNotification(notificationId: number): Observable<{ success: boolean }>;
  markAllAsRead(): Observable<{ success: boolean }>;
  deleteNotification(notificationId: number): Observable<{ success: boolean }>;
}

interface WebSocketService {
  notifications$: Observable<{
    notificationId: number;
    title: string;
    summary: string;
    priority: string;
  }>;
  connect(): void;
  disconnect(): void;
}

// 通知相关类型和服务 (延迟加载以避免循环依赖)

// 通知相关类型和服务 (延迟加载以避免循环依赖)
interface Notification {
  id: number;
  title: string;
  content: string;
  type: string;
  priority: string;
  status: string;
  recipientId: number;
  recipientType: string;
  requiresAction?: boolean;
  actionText?: string;
  actionUrl?: string;
  createdAt: string;
  updatedAt: string;
}

interface UnreadCount {
  total: number;
  urgent: number;
  normal: number;
}

/**
 * 通知中心组件
 * @eslint-disable
 */
@Component({
  selector: 'app-notification-center',
  template: `
    <div class="notification-center">
      <!-- 头部 -->
      <div class="notification-header">
        <h2>
          <mat-icon>notifications</mat-icon>
          通知中心
        </h2>
        <div class="header-actions">
          <button
            mat-button
            color="primary"
            (click)="markAllAsRead()"
            [disabled]="unreadCount.total === 0"
          >
            <mat-icon>done_all</mat-icon>
            全部已读
          </button>
          <button mat-icon-button [matMenuTriggerFor]="menu">
            <mat-icon>more_vert</mat-icon>
          </button>
        </div>
      </div>

      <mat-menu #menu="matMenu">
        <button mat-menu-item (click)="filterByStatus('all')">
          <mat-icon>list</mat-icon>
          <span>全部通知</span>
        </button>
        <button mat-menu-item (click)="filterByStatus('unread')">
          <mat-icon>mail</mat-icon>
          <span>未读通知</span>
        </button>
        <button mat-menu-item (click)="filterByStatus('archived')">
          <mat-icon>archive</mat-icon>
          <span>已归档</span>
        </button>
      </mat-menu>

      <!-- 统计信息 -->
      <div class="notification-stats">
        <div class="stat-item">
          <div class="stat-value">{{ unreadCount.total }}</div>
          <div class="stat-label">未读通知</div>
        </div>
        <div class="stat-item urgent" *ngIf="unreadCount.urgent > 0">
          <div class="stat-value">{{ unreadCount.urgent }}</div>
          <div class="stat-label">紧急通知</div>
        </div>
      </div>

      <!-- Tab 切换 -->
      <mat-tab-group [(selectedIndex)]="activeTab" (selectedIndexChange)="onTabChange($event)">
        <mat-tab label="全部通知">
          <div class="tab-content">
            <ng-container *ngIf="!loading; else loadingTemplate">
              <ng-container *ngIf="filteredNotifications.length > 0; else emptyState">
                <div class="notification-list">
                  <div
                    *ngFor="let notification of filteredNotifications"
                    class="notification-item"
                    [class.unread]="notification.status === 'unread'"
                    [class.urgent]="notification.priority === 'urgent'"
                    [class.has-action]="notification.requiresAction"
                  >
                    <div class="notification-avatar">
                      <mat-icon [color]="getPriorityColor(notification.priority)">
                        {{ getNotificationIcon(notification.type) }}
                      </mat-icon>
                    </div>

                    <div class="notification-content">
                      <div class="notification-header-row">
                        <h4 class="notification-title">{{ notification.title }}</h4>
                        <span class="notification-time">{{
                          formatTime(notification.createdAt)
                        }}</span>
                      </div>

                      <p class="notification-text">{{ notification.content }}</p>

                      <div class="notification-footer">
                        <mat-chip [color]="getPriorityChipColor(notification.priority)" selected>
                          {{ getPriorityLabel(notification.priority) }}
                        </mat-chip>

                        <div
                          class="notification-actions"
                          *ngIf="notification.requiresAction && notification.actionUrl"
                        >
                          <a mat-button color="primary" [href]="notification.actionUrl">
                            {{ notification.actionText || '查看详情' }}
                            <mat-icon>arrow_forward</mat-icon>
                          </a>
                        </div>
                      </div>
                    </div>

                    <div class="notification-actions-right">
                      <button
                        mat-icon-button
                        [matTooltip]="notification.status === 'unread' ? '标记为已读' : '归档'"
                        (click)="toggleReadStatus(notification)"
                      >
                        <mat-icon>{{
                          notification.status === 'unread' ? 'mark_email_read' : 'archive'
                        }}</mat-icon>
                      </button>
                      <button
                        mat-icon-button
                        [matTooltip]="'删除'"
                        (click)="deleteNotification(notification)"
                      >
                        <mat-icon>delete</mat-icon>
                      </button>
                    </div>
                  </div>
                </div>
              </ng-container>

              <ng-template #emptyState>
                <div class="empty-state">
                  <mat-icon>notifications_none</mat-icon>
                  <p>暂无通知</p>
                </div>
              </ng-template>
            </ng-container>

            <ng-template #loadingTemplate>
              <div class="loading-state">
                <mat-spinner diameter="40"></mat-spinner>
                <p>正在加载通知...</p>
              </div>
            </ng-template>
          </div>
        </mat-tab>

        <mat-tab label="系统通知">
          <div class="tab-content">
            <!-- 类似全部通知的逻辑 -->
          </div>
        </mat-tab>

        <mat-tab label="预警通知">
          <div class="tab-content">
            <!-- 类似全部通知的逻辑 -->
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [
    `
      .notification-center {
        width: 100%;
        max-width: 900px;
        margin: 0 auto;
      }

      .notification-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #e0e0e0;
      }

      .notification-header h2 {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 24px;
        color: #333;
      }

      .header-actions {
        display: flex;
        gap: 8px;
      }

      .notification-stats {
        display: flex;
        gap: 24px;
        padding: 16px 0;
      }

      .stat-item {
        text-align: center;
      }

      .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: #2196f3;
      }

      .stat-item.urgent .stat-value {
        color: #f44336;
      }

      .stat-label {
        font-size: 14px;
        color: #666;
        margin-top: 4px;
      }

      .tab-content {
        min-height: 400px;
      }

      .notification-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 16px 0;
      }

      .notification-item {
        display: flex;
        gap: 16px;
        padding: 16px;
        border-radius: 8px;
        background-color: #f5f5f5;
        transition: all 0.3s ease;
        cursor: pointer;

        &:hover {
          background-color: #e8e8e8;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      }

      .notification-item.unread {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
      }

      .notification-item.urgent {
        border-left: 4px solid #f44336;
      }

      .notification-avatar {
        flex-shrink: 0;
      }

      .notification-avatar mat-icon {
        font-size: 32px;
        width: 32px;
        height: 32px;
      }

      .notification-content {
        flex: 1;
        min-width: 0;
      }

      .notification-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }

      .notification-title {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #333;
      }

      .notification-time {
        font-size: 12px;
        color: #999;
      }

      .notification-text {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: #666;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .notification-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .notification-actions {
        display: flex;
        gap: 8px;
      }

      .notification-actions-right {
        display: flex;
        gap: 4px;
      }

      .loading-state,
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        gap: 16px;
      }

      .empty-state mat-icon {
        font-size: 64px;
        width: 64px;
        height: 64px;
        color: #9e9e9e;
      }

      .empty-state p {
        margin: 0;
        color: #999;
        font-size: 16px;
      }
    `,
  ],
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatMenuModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTabsModule,
    MatTooltipModule,
  ],
})
export class NotificationCenterComponent implements OnInit, OnDestroy {
  notifications: Notification[] = [];
  filteredNotifications: Notification[] = [];
  loading = false;
  activeTab = 0;
  currentFilter: 'all' | 'unread' | 'archived' = 'all';

  unreadCount: UnreadCount = { total: 0, urgent: 0, normal: 0 };

  private destroy$ = new Subject<void>();

  constructor(
    private notificationService: NotificationService,
    private wsService: WebSocketService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadNotifications();
    this.loadUnreadCount();

    // 监听实时通知
    this.wsService.notifications$.pipe(takeUntil(this.destroy$)).subscribe((data) => {
      this.handleNewNotification(data);
    });

    // 连接 WebSocket
    this.wsService.connect();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    // 断开 WebSocket 连接，防止内存泄漏
    this.wsService.disconnect();
  }

  /**
   * 加载通知列表
   */
  loadNotifications(): void {
    this.loading = true;

    this.notificationService.getNotifications({ page: 1, size: 50 }).subscribe({
      next: (response) => {
        this.notifications = response.notifications || [];
        this.applyFilter();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.snackBar.open('加载通知失败', '关闭', { duration: 3000 });
      },
    });
  }

  /**
   * 加载未读数量
   */
  loadUnreadCount(): void {
    this.notificationService.getUnreadCount(1).subscribe({
      next: (count: UnreadCount) => {
        this.unreadCount = count;
      },
    });
  }

  /**
   * 处理新通知
   */
  handleNewNotification(data: {
    notificationId: number;
    title: string;
    summary: string;
    priority: string;
  }): void {
    const newNotification: Notification = {
      id: data.notificationId,
      title: data.title,
      content: data.summary,
      type: 'alert',
      priority: data.priority,
      status: 'unread',
      recipientId: 1,
      recipientType: 'user',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.notifications.unshift(newNotification);
    this.applyFilter();
    this.loadUnreadCount();

    this.snackBar.open(`新通知：${data.title}`, '查看', {
      duration: 5000,
      panelClass: ['info-snackbar'],
    });
  }

  /**
   * 应用筛选
   */
  applyFilter(): void {
    switch (this.currentFilter) {
      case 'unread':
        this.filteredNotifications = this.notifications.filter((n) => n.status === 'unread');
        break;
      case 'archived':
        this.filteredNotifications = this.notifications.filter((n) => n.status === 'archived');
        break;
      default:
        this.filteredNotifications = [...this.notifications];
    }
  }

  /**
   * 筛选通知
   */
  filterByStatus(filter: 'all' | 'unread' | 'archived'): void {
    this.currentFilter = filter;
    this.applyFilter();
  }

  /**
   * Tab 切换
   */
  onTabChange(index: number): void {
    this.activeTab = index;
    // TODO: 根据 Tab 加载不同类型的通知
  }

  /**
   * 标记为已读/未读
   */
  toggleReadStatus(notification: Notification): void {
    if (notification.status === 'unread') {
      this.notificationService.markAsRead(notification.id).subscribe(() => {
        notification.status = 'read';
        this.applyFilter();
        this.loadUnreadCount();
      });
    } else {
      // 归档逻辑
      this.notificationService.archiveNotification(notification.id).subscribe(() => {
        notification.status = 'archived';
        this.applyFilter();
      });
    }
  }

  /**
   * 全部已读
   */
  markAllAsRead(): void {
    this.notificationService.markAllAsRead().subscribe(() => {
      this.notifications.forEach((n) => (n.status = 'read'));
      this.applyFilter();
      this.loadUnreadCount();
      this.snackBar.open('已全部标记为已读', '关闭', { duration: 2000 });
    });
  }

  /**
   * 删除通知
   */
  deleteNotification(notification: Notification): void {
    if (!confirm('确定要删除这条通知吗？')) return;

    this.notificationService.deleteNotification(notification.id).subscribe(() => {
      this.notifications = this.notifications.filter((n) => n.id !== notification.id);
      this.applyFilter();
      this.loadUnreadCount();
      this.snackBar.open('通知已删除', '关闭', { duration: 2000 });
    });
  }

  /**
   * 获取通知图标
   */
  getNotificationIcon(type: string): string {
    const icons: Record<string, string> = {
      system: 'settings',
      alert: 'warning',
      reminder: 'alarm',
      announcement: 'campaign',
    };
    return icons[type] || 'notifications';
  }

  /**
   * 获取优先级颜色
   */
  getPriorityColor(priority: string): string {
    const colors: Record<string, string> = {
      low: '',
      medium: 'accent',
      high: 'warn',
      urgent: 'warn',
    };
    return colors[priority] || '';
  }

  /**
   * 获取优先级标签颜色
   */
  getPriorityChipColor(priority: string): string {
    const colors: Record<string, string> = {
      low: 'primary',
      medium: 'accent',
      high: 'warn',
      urgent: 'warn',
    };
    return colors[priority] || 'primary';
  }

  /**
   * 获取优先级文本
   */
  getPriorityLabel(priority: string): string {
    const labels: Record<string, string> = {
      low: '低优先级',
      medium: '中等优先级',
      high: '高优先级',
      urgent: '紧急',
    };
    return labels[priority] || '未知';
  }

  /**
   * 格式化时间
   */
  formatTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;

    return date.toLocaleDateString('zh-CN');
  }
}
