import { Component, Input, Output, EventEmitter, TemplateRef, OnDestroy, Injectable } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { BehaviorSubject } from 'rxjs';

/**
 * 通知类型枚举
 */
export type NotificationType = 'success' | 'warning' | 'error' | 'info';

/**
 * 通知位置枚举
 */
export type NotificationPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';

/**
 * 通知配置接口
 */
export interface NotificationConfig {
  id?: string;
  type: NotificationType;
  title?: string;
  message: string;
  duration?: number;
  showCloseButton?: boolean;
  icon?: string;
  template?: TemplateRef<any>;
  data?: any;
}

/**
 * 通用通知组件 - Angular版本
 * 提供一致的通知体验，支持多种类型和自定义配置
 */
@Component({
  selector: 'toast-notification',
  template: `
    <div
      class="toast-notification"
      [@slideInSlideOut]="animationState"
      (@slideInSlideOut.done)="onAnimationDone($event)"
      [class.toast-notification--success]="type === 'success'"
      [class.toast-notification--warning]="type === 'warning'"
      [class.toast-notification--error]="type === 'error'"
      [class.toast-notification--info]="type === 'info'"
      [ngStyle]="notificationStyles"
      role="alert"
      aria-live="polite">

      <!-- 图标 -->
      <div class="toast-icon" [ngStyle]="iconStyles">
        <ng-container *ngIf="!iconTemplate; else iconTemplateContent">
          <span class="toast-icon-default" [innerHTML]="defaultIcon"></span>
        </ng-container>
        <ng-template #iconTemplateContent>
          <ng-template [ngTemplateOutlet]="iconTemplate"></ng-template>
        </ng-template>
      </div>

      <!-- 内容区域 -->
      <div class="toast-content">
        <div
          class="toast-title"
          *ngIf="title"
          [ngStyle]="titleStyles">
          {{ title }}
        </div>
        <div
          class="toast-message"
          [ngStyle]="messageStyles">
          <ng-container *ngIf="template; else defaultMessage">
            <ng-template [ngTemplateOutlet]="template" [ngTemplateOutletContext]="{ $implicit: data }"></ng-template>
          </ng-container>
          <ng-template #defaultMessage>
            {{ message }}
          </ng-template>
        </div>
      </div>

      <!-- 关闭按钮 -->
      <button
        *ngIf="showCloseButton"
        class="toast-close-button"
        (click)="close()"
        [attr.aria-label]="'关闭通知'"
        [ngStyle]="closeButtonStyles">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  `,
  styleUrls: ['./toast-notification.component.scss'],
  animations: [
    trigger('slideInSlideOut', [
      state('in', style({ transform: 'translateX(0)', opacity: 1 })),
      state('out', style({ transform: 'translateX(100%)', opacity: 0 })),
      transition('void => in', [
        style({ transform: 'translateX(100%)', opacity: 0 }),
        animate('300ms cubic-bezier(0.68, -0.55, 0.265, 1.55)')
      ]),
      transition('in => out', [
        animate('200ms ease-in', style({ transform: 'translateX(100%)', opacity: 0 }))
      ])
    ])
  ]
})
export class ToastNotificationComponent implements OnDestroy {
  /** 通知唯一标识 */
  @Input() id: string = Math.random().toString(36).substr(2, 9);

  /** 通知类型 */
  @Input() type: NotificationType = 'info';

  /** 通知标题 */
  @Input() title?: string;

  /** 通知消息 */
  @Input() message: string = '';

  /** 显示持续时间 (毫秒) */
  @Input() duration: number = 4000;

  /** 是否显示关闭按钮 */
  @Input() showCloseButton: boolean = true;

  /** 自定义图标 */
  @Input() icon?: string;

  /** 图标模板 */
  @Input() iconTemplate?: TemplateRef<any>;

  /** 自定义内容模板 */
  @Input() template?: TemplateRef<any>;

  /** 模板数据 */
  @Input() data?: any;

  /** 通知位置 */
  @Input() position: NotificationPosition = 'top-right';

  /** 自定义样式 */
  @Input() customStyles?: {
    container?: any;
    icon?: any;
    title?: any;
    message?: any;
    closeButton?: any;
  };

  /** 关闭事件 */
  @Output() closed = new EventEmitter<string>();

  /** 动画状态 */
  animationState: 'in' | 'out' = 'in';

  /** 自动关闭定时器 */
  private autoCloseTimer?: any;

  ngOnInit(): void {
    // 设置自动关闭
    if (this.duration > 0) {
      this.autoCloseTimer = setTimeout(() => {
        this.close();
      }, this.duration);
    }
  }

  ngOnDestroy(): void {
    if (this.autoCloseTimer) {
      clearTimeout(this.autoCloseTimer);
    }
  }

  /** 关闭通知 */
  close(): void {
    this.animationState = 'out';
  }

  /** 动画完成处理 */
  onAnimationDone(event: any): void {
    if (event.toState === 'out') {
      this.closed.emit(this.id);
    }
  }

  /** 获取默认图标 */
  get defaultIcon(): string {
    switch (this.type) {
      case 'success': return '✓';
      case 'warning': return '⚠';
      case 'error': return '✕';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  }

  /** 通知容器样式 */
  get notificationStyles(): any {
    const baseStyles = {
      'background-color': this.getBackgroundColor(),
      'border-left': `4px solid ${this.getBorderColor()}`,
      'box-shadow': '0 4px 12px rgba(0, 0, 0, 0.15)'
    };

    return { ...baseStyles, ...this.customStyles?.container };
  }

  /** 图标样式 */
  get iconStyles(): any {
    const baseStyles = {
      'color': this.getIconColor()
    };

    return { ...baseStyles, ...this.customStyles?.icon };
  }

  /** 标题样式 */
  get titleStyles(): any {
    const baseStyles = {
      'color': 'var(--text-primary-color, #212121)',
      'font-weight': '600'
    };

    return { ...baseStyles, ...this.customStyles?.title };
  }

  /** 消息样式 */
  get messageStyles(): any {
    const baseStyles = {
      'color': 'var(--text-secondary-color, #757575)'
    };

    return { ...baseStyles, ...this.customStyles?.message };
  }

  /** 关闭按钮样式 */
  get closeButtonStyles(): any {
    const baseStyles = {
      'color': 'var(--text-secondary-color, #757575)'
    };

    return { ...baseStyles, ...this.customStyles?.closeButton };
  }

  /** 获取背景颜色 */
  private getBackgroundColor(): string {
    switch (this.type) {
      case 'success': return 'var(--success-bg-color, #e8f5e8)';
      case 'warning': return 'var(--warning-bg-color, #fff8e1)';
      case 'error': return 'var(--error-bg-color, #ffebee)';
      case 'info': return 'var(--info-bg-color, #e3f2fd)';
      default: return 'var(--surface-color, #ffffff)';
    }
  }

  /** 获取边框颜色 */
  private getBorderColor(): string {
    switch (this.type) {
      case 'success': return 'var(--success-color, #4caf50)';
      case 'warning': return 'var(--warning-color, #ff9800)';
      case 'error': return 'var(--error-color, #f44336)';
      case 'info': return 'var(--primary-color, #2196f3)';
      default: return 'var(--border-color, #e0e0e0)';
    }
  }

  /** 获取图标颜色 */
  private getIconColor(): string {
    switch (this.type) {
      case 'success': return 'var(--success-color, #4caf50)';
      case 'warning': return 'var(--warning-color, #ff9800)';
      case 'error': return 'var(--error-color, #f44336)';
      case 'info': return 'var(--primary-color, #2196f3)';
      default: return 'var(--text-secondary-color, #757575)';
    }
  }
}

/**
 * 通知服务
 */
@Injectable({
  providedIn: 'root'
})
export class ToastNotificationService {
  private notifications: NotificationConfig[] = [];
  private notificationSubject = new BehaviorSubject<NotificationConfig[]>([]);

  public notifications$ = this.notificationSubject.asObservable();

  /** 显示成功通知 */
  success(message: string, title?: string, options?: Partial<NotificationConfig>): void {
    this.show({ type: 'success', message, title, ...options });
  }

  /** 显示警告通知 */
  warning(message: string, title?: string, options?: Partial<NotificationConfig>): void {
    this.show({ type: 'warning', message, title, ...options });
  }

  /** 显示错误通知 */
  error(message: string, title?: string, options?: Partial<NotificationConfig>): void {
    this.show({ type: 'error', message, title, duration: 6000, ...options });
  }

  /** 显示信息通知 */
  info(message: string, title?: string, options?: Partial<NotificationConfig>): void {
    this.show({ type: 'info', message, title, ...options });
  }

  /** 显示自定义通知 */
  show(config: NotificationConfig): void {
    const notification: NotificationConfig = {
      id: config.id || Math.random().toString(36).substr(2, 9),
      ...config,
      duration: config.duration ?? 4000,
      showCloseButton: config.showCloseButton ?? true,
    };

    this.notifications.push(notification);
    this.notificationSubject.next([...this.notifications]);

    // 自动移除
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        this.remove(notification.id!);
      }, notification.duration);
    }
  }

  /** 移除通知 */
  remove(id: string): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notificationSubject.next([...this.notifications]);
  }

  /** 清除所有通知 */
  clearAll(): void {
    this.notifications = [];
    this.notificationSubject.next([]);
  }
}
