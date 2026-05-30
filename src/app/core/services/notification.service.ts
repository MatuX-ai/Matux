/**
 * Notification Service
 *
 * 通知管理服务，处理通知的增删改查和状态管理
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { delay, tap } from 'rxjs/operators';

/**
 * 通知类型
 */
export type NotificationType =
  | 'system' // 系统通知
  | 'alert' // 预警通知
  | 'reminder' // 提醒
  | 'announcement'; // 公告

/**
 * 通知优先级
 */
export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * 通知状态
 */
export type NotificationStatus = 'unread' | 'read' | 'archived';

/**
 * 通知数据模型
 */
export interface Notification {
  /** 通知 ID */
  id: number;

  /** 标题 */
  title: string;

  /** 内容 */
  content: string;

  /** 类型 */
  type: NotificationType;

  /** 优先级 */
  priority: NotificationPriority;

  /** 状态 */
  status: NotificationStatus;

  /** 接收者 ID (用户或机构) */
  recipientId: number;

  /** 接收者类型 (user/organization) */
  recipientType: 'user' | 'organization';

  /** 关联的业务 ID (如课程 ID、订单 ID 等) */
  relatedId?: number;

  /** 关联的业务类型 */
  relatedType?: string;

  /** 是否需要确认 */
  requiresAction?: boolean;

  /** 确认按钮文本 */
  actionText?: string;

  /** 确认按钮路由 */
  actionUrl?: string;

  /** 已读时间 */
  readAt?: string;

  /** 创建时间 */
  createdAt: string;

  /** 更新时间 */
  updatedAt: string;
}

/**
 * 未读通知数量
 */
export interface UnreadCount {
  /** 总未读数 */
  total: number;
  /** 高优先级未读数 */
  urgent: number;
  /** 普通未读数 */
  normal: number;
}

/**
 * 通知查询参数
 */
export interface NotificationQuery {
  /** 页码 */
  page?: number;
  /** 每页数量 */
  size?: number;
  /** 通知类型 */
  type?: NotificationType;
  /** 通知状态 */
  status?: NotificationStatus;
  /** 优先级 */
  priority?: NotificationPriority;
  /** 开始日期 */
  startDate?: string;
  /** 结束日期 */
  endDate?: string;
}

const USE_MOCK_DATA = true;

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private readonly API_BASE_URL = '/api/v1/notifications';

  // 未读通知数量缓存
  private unreadCountSubject = new BehaviorSubject<UnreadCount>({ total: 0, urgent: 0, normal: 0 });
  public unreadCount$ = this.unreadCountSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * 获取通知列表
   * @param query 查询参数
   */
  getNotifications(
    query: NotificationQuery = {}
  ): Observable<{ notifications: Notification[]; total: number }> {
    if (USE_MOCK_DATA) {
      const mockData = this.generateMockNotifications(20);
      return of({
        notifications: mockData,
        total: mockData.length,
      }).pipe(delay(600));
    }

    let params = new HttpParams();
    if (query.page) params = params.set('page', query.page.toString());
    if (query.size) params = params.set('size', query.size.toString());
    if (query.type) params = params.set('type', query.type);
    if (query.status) params = params.set('status', query.status);
    if (query.priority) params = params.set('priority', query.priority);
    if (query.startDate) params = params.set('start_date', query.startDate);
    if (query.endDate) params = params.set('end_date', query.endDate);

    return this.http.get<{ notifications: Notification[]; total: number }>(this.API_BASE_URL, {
      params,
    });
  }

  /**
   * 获取单个通知
   * @param id 通知 ID
   */
  getNotificationById(id: number): Observable<Notification> {
    if (USE_MOCK_DATA) {
      const notifications = this.generateMockNotifications(1);
      return of(notifications[0]).pipe(delay(400));
    }

    return this.http.get<Notification>(`${this.API_BASE_URL}/${id}`);
  }

  /**
   * 获取未读通知数量
   * @param recipientId 接收者 ID
   */
  getUnreadCount(recipientId: number): Observable<UnreadCount> {
    if (USE_MOCK_DATA) {
      const count = Math.floor(Math.random() * 10) + 1;
      const result = {
        total: count,
        urgent: Math.floor(count / 3),
        normal: count - Math.floor(count / 3),
      };
      this.unreadCountSubject.next(result);
      return of(result).pipe(delay(300));
    }

    return this.http
      .get<UnreadCount>(`${this.API_BASE_URL}/unread-count`, {
        params: new HttpParams().set('recipient_id', recipientId.toString()),
      })
      .pipe(tap((count) => this.unreadCountSubject.next(count)));
  }

  /**
   * 标记通知为已读
   * @param id 通知 ID
   */
  markAsRead(id: number): Observable<void> {
    if (USE_MOCK_DATA) {
      return of(undefined).pipe(delay(300));
    }

    return this.http.put<void>(`${this.API_BASE_URL}/${id}/read`, {});
  }

  /**
   * 批量标记为已读
   * @param ids 通知 ID 列表
   */
  markMultipleAsRead(ids: number[]): Observable<void> {
    if (USE_MOCK_DATA) {
      return of(undefined).pipe(delay(400));
    }

    return this.http.put<void>(`${this.API_BASE_URL}/mark-multiple-read`, { ids });
  }

  /**
   * 标记所有通知为已读
   */
  markAllAsRead(): Observable<void> {
    if (USE_MOCK_DATA) {
      return of(undefined).pipe(delay(300));
    }

    return this.http.put<void>(`${this.API_BASE_URL}/mark-all-read`, {});
  }

  /**
   * 归档通知
   * @param id 通知 ID
   */
  archiveNotification(id: number): Observable<void> {
    if (USE_MOCK_DATA) {
      return of(undefined).pipe(delay(300));
    }

    return this.http.put<void>(`${this.API_BASE_URL}/${id}/archive`, {});
  }

  /**
   * 删除通知
   * @param id 通知 ID
   */
  deleteNotification(id: number): Observable<void> {
    if (USE_MOCK_DATA) {
      return of(undefined).pipe(delay(300));
    }

    return this.http.delete<void>(`${this.API_BASE_URL}/${id}`);
  }

  /**
   * 创建通知 (管理员功能)
   * @param notification 通知数据
   */
  createNotification(notification: Partial<Notification>): Observable<Notification> {
    if (USE_MOCK_DATA) {
      const newNotification: Notification = {
        id: Date.now(),
        title: notification.title ?? '新通知',
        content: notification.content ?? '',
        type: notification.type ?? 'system',
        priority: notification.priority ?? 'medium',
        status: 'unread',
        recipientId: notification.recipientId ?? 0,
        recipientType: notification.recipientType ?? 'user',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      return of(newNotification).pipe(delay(500));
    }

    return this.http.post<Notification>(this.API_BASE_URL, notification);
  }

  /**
   * 更新未读计数
   */
  refreshUnreadCount(recipientId: number): void {
    this.getUnreadCount(recipientId).subscribe();
  }

  /**
   * 生成模拟数据
   */
  private generateMockNotifications(count: number): Notification[] {
    const priorities: NotificationPriority[] = ['low', 'medium', 'high', 'urgent'];
    const templates = this.getNotificationTemplates();
    const notifications: Notification[] = [];

    for (let i = 0; i < count; i++) {
      const template = templates[i % templates.length];
      const now = new Date();
      now.setMinutes(now.getMinutes() - i * 30);

      notifications.push(this.buildNotification(template, priorities, i, now));
    }

    return notifications;
  }

  /**
   * 获取通知模板
   */
  private getNotificationTemplates(): Array<{
    title: string;
    content: string;
    type: NotificationType;
  }> {
    return [
      {
        title: '系统维护通知',
        content: '系统将于今晚 23:00 进行例行维护，预计持续 2 小时。请提前保存您的工作。',
        type: 'system' as NotificationType,
      },
      {
        title: '许可证即将到期',
        content: '您的机构许可证将在 7 天后到期，请及时续费以避免服务中断。',
        type: 'alert' as NotificationType,
      },
      {
        title: '新课程上线',
        content: '我们新增了 Python 编程课程，欢迎报名参与!',
        type: 'announcement' as NotificationType,
      },
      {
        title: '课程提醒',
        content: '您报名的《Java 高级编程》课程将于明天上午 9:00 开课。',
        type: 'reminder' as NotificationType,
      },
      {
        title: '付款成功通知',
        content: '您的订单 #12345 已付款成功，金额为 ¥299.00。',
        type: 'system' as NotificationType,
      },
    ];
  }

  /**
   * 构建单个通知
   */
  private buildNotification(
    template: { title: string; content: string; type: NotificationType },
    priorities: NotificationPriority[],
    index: number,
    timestamp: Date
  ): Notification {
    return {
      id: Date.now() + index,
      title: template.title,
      content: template.content,
      type: template.type,
      priority: priorities[index % priorities.length],
      status: index % 3 === 0 ? 'read' : 'unread',
      recipientId: 1,
      recipientType: 'user',
      relatedId: index % 2 === 0 ? 100 + index : undefined,
      relatedType: index % 2 === 0 ? 'course' : undefined,
      requiresAction: index % 5 === 0,
      actionText: index % 5 === 0 ? '查看详情' : undefined,
      actionUrl: index % 5 === 0 ? `/courses/${100 + index}` : undefined,
      readAt: index % 3 === 0 ? timestamp.toISOString() : undefined,
      createdAt: timestamp.toISOString(),
      updatedAt: timestamp.toISOString(),
    };
  }
}
