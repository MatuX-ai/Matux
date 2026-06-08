import { HttpErrorResponse } from '@angular/common/http';
import { HttpClient } from '@angular/common/http';
import { ErrorHandler, Injectable, Injector } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject } from 'rxjs';

import { AuthService } from '../auth.service';
import { ROUTES } from '../../../routes.const';

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'NETWORK', // 网络错误
  HTTP = 'HTTP', // HTTP 错误
  VALIDATION = 'VALIDATION', // 验证错误
  AUTH = 'AUTH', // 认证错误
  PERMISSION = 'PERMISSION', // 权限错误
  NOT_FOUND = 'NOT_FOUND', // 资源不存在
  SERVER = 'SERVER', // 服务器错误
  UNKNOWN = 'UNKNOWN', // 未知错误
}

/**
 * 错误信息接口
 */
export interface AppError {
  type: ErrorType;
  message: string;
  code?: string;
  status?: number;
  url?: string;
  timestamp: number;
  details?: unknown;
}

/**
 * 错误提示配置
 */
export interface ErrorToastConfig {
  duration?: number; // 显示时长 (毫秒)
  position?: 'top' | 'bottom';
  dismissible?: boolean; // 是否可手动关闭
}

/**
 * 可解析的错误对象结构
 */
interface ErrorPayload {
  error?: {
    type?: string;
    message?: string;
    code?: string;
    details?: unknown;
  };
  message?: string;
  code?: string;
  url?: string;
}

/**
 * AI-Edu 错误处理服务
 */
@Injectable({
  providedIn: 'root',
})
export class AIEduErrorHandlerService implements ErrorHandler {
  private router?: Router;
  private http?: HttpClient;

  // 当前错误提示
  private currentToast: HTMLElement | null = null;

  // 错误历史
  private errorHistory: AppError[] = [];
  private readonly MAX_HISTORY = 50;

  // 错误通知主题
  private errorSubject = new BehaviorSubject<AppError | null>(null);
  public error$ = this.errorSubject.asObservable();

  // 全局错误开关
  private globalErrorEnabled = true;

  // 错误日志批量上报配置
  private readonly LOG_BATCH_SIZE = 10; // 批量上报阈值
  private readonly LOG_FLUSH_INTERVAL = 30000; // 30 秒定时上报
  private pendingLogs: AppError[] = [];
  private flushTimer?: ReturnType<typeof setInterval>;

  constructor(private injector: Injector) {
    setTimeout(() => {
      this.router = this.injector.get(Router);
      this.http = this.injector.get(HttpClient);
    }, 0);

    // 启动定时上报
    this.startFlushTimer();
  }

  /**
   * Angular 全局错误处理器
   */
  handleError(error: unknown): void {
    const appError = this.parseError(error);

    // 记录错误历史
    this.recordError(appError);

    // 发布错误通知
    this.errorSubject.next(appError);

    // 显示错误提示
    if (this.globalErrorEnabled) {
      this.showToast(appError);
    }

    // 特殊错误处理
    this.handleSpecialCases(appError);
  }

  /**
   * 解析错误对象
   */
  // eslint-disable-next-line complexity
  private parseError(error: unknown): AppError {
    const baseError: AppError = {
      type: ErrorType.UNKNOWN,
      message: '发生未知错误，请稍后重试',
      timestamp: Date.now(),
    };

    // 非对象类型直接返回
    if (error === null || error === undefined || typeof error !== 'object') {
      return baseError;
    }

    const err = error as ErrorPayload;

    // HTTP 错误
    if (error instanceof HttpErrorResponse) {
      return this.parseHttpError(error);
    }

    // 已知的错误类型
    if (err.error?.type) {
      baseError.type = err.error.type as ErrorType;
    }

    if (err.error?.message) {
      baseError.message = err.error.message;
    } else if (err.message) {
      baseError.message = err.message;
    }

    if (err.code ?? err.error?.code) {
      baseError.code = err.code ?? err.error?.code;
    }

    if (err.url) {
      baseError.url = err.url;
    }

    if (err.error?.details) {
      baseError.details = err.error.details;
    }

    return baseError;
  }

  /**
   * 解析 HTTP 错误
   */
  // eslint-disable-next-line complexity
  private parseHttpError(error: HttpErrorResponse): AppError {
    const httpError: AppError = {
      type: ErrorType.HTTP,
      message: '',
      status: error.status,
      url: error.url ?? undefined,
      timestamp: Date.now(),
    };

    const errBody = error.error as { message?: string } | null | undefined;

    switch (error.status) {
      case 0:
        httpError.type = ErrorType.NETWORK;
        httpError.message = '网络连接失败，请检查网络设置';
        break;

      case 400:
        httpError.type = ErrorType.VALIDATION;
        httpError.message = errBody?.message ?? '请求参数错误';
        break;

      case 401:
        httpError.type = ErrorType.AUTH;
        httpError.message = '未授权，请登录';
        break;

      case 403:
        httpError.type = ErrorType.PERMISSION;
        httpError.message = '无权访问此资源';
        break;

      case 404:
        httpError.type = ErrorType.NOT_FOUND;
        httpError.message = '请求的资源不存在';
        break;

      case 500:
        httpError.type = ErrorType.SERVER;
        httpError.message = '服务器内部错误';
        break;

      case 502:
      case 503:
      case 504:
        httpError.type = ErrorType.SERVER;
        httpError.message = '服务暂时不可用，请稍后重试';
        break;

      default:
        httpError.message = errBody?.message ?? `HTTP 错误：${error.status}`;
    }

    return httpError;
  }

  /**
   * 记录错误到历史
   */
  private recordError(error: AppError): void {
    this.errorHistory.unshift(error);

    if (this.errorHistory.length > this.MAX_HISTORY) {
      this.errorHistory.pop();
    }

    // ✅ 新增：添加到待上报队列
    this.queueLog(error);
  }

  /**
   * 将错误加入待上报队列
   */
  private queueLog(error: AppError): void {
    this.pendingLogs.push(error);

    // 达到批量阈值时立即上报
    if (this.pendingLogs.length >= this.LOG_BATCH_SIZE) {
      this.flushLogs();
    }
  }

  /**
   * 启动定时上报计时器
   */
  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      if (this.pendingLogs.length > 0) {
        this.flushLogs();
      }
    }, this.LOG_FLUSH_INTERVAL);
  }

  /**
   * 批量上报错误日志
   */
  private flushLogs(): void {
    if (!this.http || this.pendingLogs.length === 0) {
      return;
    }

    const logsToSend = [...this.pendingLogs];
    this.pendingLogs = [];

    const API_BASE = 'http://localhost:8000/api/v1/org/1/logs';

    const currentUser = this.injector.get(AuthService).getCurrentUser();
    const userId = currentUser?.id ? Number(currentUser.id) : 1;
    const orgId = (currentUser as unknown as { org_id?: number })?.org_id ?? 1;

    this.http
      .post(`${API_BASE}/error`, {
        errors: logsToSend.map((err) => ({
          type: err.type,
          message: err.message,
          code: err.code,
          status: err.status,
          url: err.url,
          timestamp: new Date(err.timestamp).toISOString(),
          details: err.details as Record<string, unknown> | undefined,
        })),
        user_id: userId,
        org_id: orgId,
      })
      .subscribe({
        next: () => {
          console.warn(`成功上报 ${logsToSend.length} 条错误日志`);
        },
        error: (error) => {
          console.error('❌ 错误日志上报失败:', error);
          // 上报失败时将日志重新加入队列
          this.pendingLogs.unshift(...logsToSend);
        },
      });
  }

  /**
   * 获取错误历史
   */
  getErrorHistory(): AppError[] {
    return [...this.errorHistory];
  }

  /**
   * 清除错误历史
   */
  clearHistory(): void {
    this.errorHistory = [];
  }

  /**
   * 显示错误提示 Toast
   */
  showToast(error: AppError | string, config: ErrorToastConfig = {}): void {
    const defaultConfig: Required<ErrorToastConfig> = {
      duration: 5000,
      position: 'top',
      dismissible: true,
    };

    const finalConfig = { ...defaultConfig, ...config };

    // 移除旧的提示
    if (this.currentToast) {
      this.currentToast.remove();
    }

    const message = typeof error === 'string' ? error : error.message;
    const type = typeof error === 'string' ? ErrorType.UNKNOWN : error.type;

    // 创建 Toast 元素（使用安全的 DOM 操作，防止 XSS）
    const toast = document.createElement('div');
    toast.className = `ai-edu-toast ai-edu-toast-${type}`;
    
    // 使用安全的 DOM 结构
    const contentDiv = document.createElement('div');
    contentDiv.className = 'toast-content';
    
    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon';
    iconSpan.textContent = this.getErrorIcon(type);  // textContent 自动转义
    
    const messageSpan = document.createElement('span');
    messageSpan.className = 'toast-message';
    messageSpan.textContent = message;  // textContent 自动转义，防止 XSS
    
    contentDiv.appendChild(iconSpan);
    contentDiv.appendChild(messageSpan);
    
    if (finalConfig.dismissible) {
      const closeBtn = document.createElement('button');
      closeBtn.className = 'toast-close';
      closeBtn.textContent = '×';
      closeBtn.addEventListener('click', () => this.removeToast(toast));
      contentDiv.appendChild(closeBtn);
    }
    
    const progressDiv = document.createElement('div');
    progressDiv.className = 'toast-progress';
    
    toast.appendChild(contentDiv);
    toast.appendChild(progressDiv);

    // 添加样式
    this.injectStyles();

    // 设置位置
    toast.style.cssText = `
      position: fixed;
      ${finalConfig.position === 'top' ? 'top: 20px' : 'bottom: 20px'};
      left: 50%;
      transform: translateX(-50%);
      z-index: 10000;
      min-width: 300px;
      max-width: 600px;
      animation: slideIn 0.3s ease-out;
    `;

    // 添加到页面
    document.body.appendChild(toast);
    this.currentToast = toast;

    // 自动关闭
    if (finalConfig.duration > 0) {
      setTimeout(() => this.removeToast(toast), finalConfig.duration);
    }
  }

  /**
   * 移除 Toast
   */
  removeToast(toast: HTMLElement): void {
    if (!toast) return;

    toast.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => {
      toast.remove();
      if (this.currentToast === toast) {
        this.currentToast = null;
      }
    }, 300);
  }

  /**
   * 注入 CSS 样式
   */
  // eslint-disable-next-line max-lines-per-function
  private injectStyles(): void {
    const styleId = 'ai-edu-toast-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(-50%) translateY(-100%);
          opacity: 0;
        }
        to {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
      }

      @keyframes slideOut {
        from {
          transform: translateX(-50%) translateY(0);
          opacity: 1;
        }
        to {
          transform: translateX(-50%) translateY(-100%);
          opacity: 0;
        }
      }

      .ai-edu-toast {
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        overflow: hidden;
      }

      .ai-edu-toast-NETWORK {
        border-left: 4px solid #ef4444;
      }

      .ai-edu-toast-HTTP {
        border-left: 4px solid #f59e0b;
      }

      .ai-edu-toast-VALIDATION {
        border-left: 4px solid #f59e0b;
      }

      .ai-edu-toast-AUTH {
        border-left: 4px solid #ef4444;
      }

      .ai-edu-toast-PERMISSION {
        border-left: 4px solid #f59e0b;
      }

      .ai-edu-toast-NOT_FOUND {
        border-left: 4px solid #3b82f6;
      }

      .ai-edu-toast-SERVER {
        border-left: 4px solid #ef4444;
      }

      .ai-edu-toast-UNKNOWN {
        border-left: 4px solid #94a3b8;
      }

      .toast-content {
        display: flex;
        align-items: center;
        padding: 15px 20px;
        gap: 12px;
      }

      .toast-icon {
        font-size: 20px;
      }

      .toast-message {
        flex: 1;
        font-size: 15px;
        color: #333;
      }

      .toast-close {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #999;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: background 0.2s;
      }

      .toast-close:hover {
        background: #f5f5f5;
      }

      .toast-progress {
        height: 3px;
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        animation: progress 5s linear;
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * 获取错误图标
   */
  private getErrorIcon(type: ErrorType): string {
    const icons: { [key: string]: string } = {
      [ErrorType.NETWORK]: '🌐',
      [ErrorType.HTTP]: '⚠️',
      [ErrorType.VALIDATION]: '❗',
      [ErrorType.AUTH]: '🔒',
      [ErrorType.PERMISSION]: '🚫',
      [ErrorType.NOT_FOUND]: '🔍',
      [ErrorType.SERVER]: '💥',
      [ErrorType.UNKNOWN]: 'ℹ️',
    };
    return icons[type] || 'ℹ️';
  }

  /**
   * 处理特殊情况
   */
  private handleSpecialCases(error: AppError): void {
    // 401 跳转到登录页
    if (error.type === ErrorType.AUTH && this.router) {
      setTimeout(() => {
        void this.router?.navigate([ROUTES.AUTH.LOGIN]);
      }, 2000);
    }

    // ✅ 严重错误记录日志并上报
    if ([ErrorType.SERVER, ErrorType.NETWORK].includes(error.type)) {
      console.error('[严重错误]', error);
      // 已自动加入待上报队列，会在 batchLog 中处理
    }
  }

  /**
   * 禁用全局错误提示
   */
  disableGlobalError(): void {
    this.globalErrorEnabled = false;
  }

  /**
   * 启用全局错误提示
   */
  enableGlobalError(): void {
    this.globalErrorEnabled = true;
  }

  /**
   * 显示成功提示
   */
  showSuccess(message: string, config: ErrorToastConfig = {}): void {
    const successToast: AppError = {
      type: ErrorType.UNKNOWN,
      message,
      timestamp: Date.now(),
    };

    // 创建成功样式的 Toast
    this.showToast(successToast, config);

    // 修改为成功样式
    if (this.currentToast) {
      this.currentToast.className = 'ai-edu-toast ai-edu-toast-success';
      const toastIcon = this.currentToast.querySelector('.toast-icon');
      if (toastIcon) {
        toastIcon.textContent = '✅';
      }
    }
  }

  /**
   * 显示警告提示
   */
  showWarning(message: string, config: ErrorToastConfig = {}): void {
    const warningToast: AppError = {
      type: ErrorType.VALIDATION,
      message,
      timestamp: Date.now(),
    };

    this.showToast(warningToast, config);
  }

  /**
   * 销毁服务，清理资源
   */
  ngOnDestroy(): void {
    // 上报剩余日志
    if (this.pendingLogs.length > 0) {
      this.flushLogs();
    }

    // 停止定时器
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
  }
}
