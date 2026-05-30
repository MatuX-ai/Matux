/**
 * Enhanced Toast Notification Service
 *
 * 增强的 Toast 通知服务，支持多种类型和实时通知集成
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarRef } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';

import { NotificationMessageData } from './websocket-notification.service';

/**
 * 通知类型
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'notification';

/**
 * Toast 配置
 */
export interface ToastConfig {
  /** 持续时间 (毫秒) */
  duration?: number;

  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;

  /** Toast 位置 (水平) */
  horizontalPosition?: 'start' | 'center' | 'end' | 'left' | 'right';

  /** Toast 位置 (垂直) */
  verticalPosition?: 'top' | 'bottom';

  /** 自定义类名 */
  panelClass?: string | string[];

  /** 操作按钮文本 */
  actionText?: string;

  /** 操作回调 */
  onAction?: () => void;
}

const DEFAULT_CONFIG: Required<ToastConfig> = {
  duration: 3000,
  showCloseButton: true,
  horizontalPosition: 'right',
  verticalPosition: 'top',
  panelClass: '',
  actionText: '关闭',
  onAction: () => {},
};

@Injectable({
  providedIn: 'root',
})
export class EnhancedToastService {
  private destroy$ = new Subject<void>();
  private activeToasts: Map<string, MatSnackBarRef<unknown>> = new Map();

  constructor(private snackBar: MatSnackBar) {}

  /**
   * 显示成功 Toast
   */
  success(message: string, config?: Partial<ToastConfig>): void {
    this.show(message, 'success', config);
  }

  /**
   * 显示错误 Toast
   */
  error(message: string, config?: Partial<ToastConfig>): void {
    this.show(message, 'error', { ...config, duration: config?.duration ?? 5000 });
  }

  /**
   * 显示警告 Toast
   */
  warning(message: string, config?: Partial<ToastConfig>): void {
    this.show(message, 'warning', config);
  }

  /**
   * 显示信息 Toast
   */
  info(message: string, config?: Partial<ToastConfig>): void {
    this.show(message, 'info', config);
  }

  /**
   * 显示通知 Toast (来自 WebSocket)
   */
  notification(data: NotificationMessageData, config?: Partial<ToastConfig>): void {
    const toastConfig: ToastConfig = {
      ...DEFAULT_CONFIG,
      ...config,
      duration: 8000, // 通知 Toast 显示更长时间
      panelClass: ['notification-toast'],
    };

    const ref = this.snackBar.open(data.title, data.link ? '查看' : '关闭', {
      duration: toastConfig.duration,
      horizontalPosition: toastConfig.horizontalPosition,
      verticalPosition: toastConfig.verticalPosition,
      panelClass: [
        ...this.getPanelClasses('notification'),
        ...(toastConfig.panelClass as string[]),
      ],
    });

    if (data.link && toastConfig.onAction) {
      ref.onAction().subscribe(() => {
        toastConfig.onAction?.();
        if (data.link) {
          window.location.href = data.link;
        }
      });
    } else {
      ref.onAction().subscribe(() => {
        toastConfig.onAction?.();
      });
    }

    // 自动关闭时从 Map 中移除
    setTimeout(() => {
      if (ref.instance) {
        ref.dismiss();
      }
    }, toastConfig.duration);
  }

  /**
   * 通用显示方法
   */
  private show(message: string, type: ToastType, config?: Partial<ToastConfig>): void {
    const toastConfig: ToastConfig = {
      ...DEFAULT_CONFIG,
      ...config,
    };

    const panelClasses = [
      ...this.getPanelClasses(type),
      ...(Array.isArray(toastConfig.panelClass)
        ? toastConfig.panelClass
        : [toastConfig.panelClass]),
    ].filter((cls): cls is string => cls !== undefined);

    const ref = this.snackBar.open(
      message,
      toastConfig.showCloseButton ? toastConfig.actionText : '',
      {
        duration: toastConfig.duration,
        horizontalPosition: toastConfig.horizontalPosition,
        verticalPosition: toastConfig.verticalPosition,
        panelClass: panelClasses,
      }
    );

    if (toastConfig.onAction) {
      ref
        .onAction()
        .pipe(takeUntil(this.destroy$))
        .subscribe(() => {
          toastConfig.onAction?.();
        });
    }
  }

  /**
   * 获取面板样式类
   */
  private getPanelClasses(type: ToastType): string[] {
    const classes: Record<ToastType, string[]> = {
      success: ['success-toast', 'mat-elevation-z4'],
      error: ['error-toast', 'mat-elevation-z4'],
      warning: ['warning-toast', 'mat-elevation-z4'],
      info: ['info-toast', 'mat-elevation-z4'],
      notification: ['notification-toast', 'mat-elevation-z4'],
    };
    return classes[type] || [];
  }

  /**
   * 显示带操作的 Toast
   */
  withAction(
    message: string,
    actionText: string,
    onAction: () => void,
    type: ToastType = 'info',
    config?: Partial<ToastConfig>
  ): void {
    this.show(message, type, {
      ...config,
      actionText,
      onAction,
    });
  }

  /**
   * 清除所有活跃的 Toast
   */
  clearAll(): void {
    this.activeToasts.forEach((ref) => ref.dismiss());
    this.activeToasts.clear();
  }

  /**
   * 销毁服务
   */
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.clearAll();
  }
}
