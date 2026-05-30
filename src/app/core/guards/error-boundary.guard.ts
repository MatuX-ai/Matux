/**
 * 错误边界守卫 - 捕获组件渲染错误
 * 防止整个应用崩溃，提供友好的错误提示
 */

import { CommonModule } from '@angular/common';
import { Component, Injectable, Input, OnDestroy, OnInit } from '@angular/core';
import { NavigationError, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

export interface ErrorInfo {
  error: any;
  componentName: string;
  stack?: string;
  timestamp: Date;
}

@Component({
  selector: 'app-error-boundary',
  standalone: true,
  imports: [CommonModule],
  template: `
    <ng-container *ngIf="!hasError; else errorTemplate">
      <ng-content></ng-content>
    </ng-container>

    <ng-template #errorTemplate>
      <div class="error-boundary">
        <div class="error-container">
          <div class="error-icon">😵</div>
          <h2 class="error-title">{{ errorTitle || '页面加载出错' }}</h2>
          <p class="error-message">
            {{ errorMessage || '我们正在努力修复这个问题，请稍后再试。' }}
          </p>

          <div class="error-actions">
            <button class="retry-btn" (click)="retry()" *ngIf="retryable">🔄 重新加载</button>
            <button class="home-btn" (click)="goHome()">🏠 返回首页</button>
          </div>

          <!-- 开发环境显示错误详情 -->
          <div class="error-details" *ngIf="isDevelopment && errorInfo">
            <details>
              <summary>错误详情（开发模式）</summary>
              <pre class="error-stack">{{ errorInfo.error?.message || errorInfo.error }}</pre>
              <p class="error-component">组件: {{ errorInfo.componentName }}</p>
              <p class="error-time">
                时间: {{ errorInfo.timestamp | date: 'yyyy-MM-dd HH:mm:ss' }}
              </p>
            </details>
          </div>
        </div>
      </div>
    </ng-template>
  `,
  styles: [
    `
      .error-boundary {
        min-height: 60vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: var(--color-brand-50, #f5f5f7);
      }

      .error-container {
        max-width: 600px;
        text-align: center;
        background: white;
        padding: 3rem 2rem;
        border-radius: var(--radius-xl, 16px);
        box-shadow: var(--shadow-lg, 0 8px 24px rgba(0, 0, 0, 0.12));
      }

      .error-icon {
        font-size: 4rem;
        margin-bottom: 1.5rem;
      }

      .error-title {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--color-brand-800, #1d1d1f);
        margin-bottom: 1rem;
      }

      .error-message {
        font-size: 1.125rem;
        color: var(--color-brand-600, #86868b);
        line-height: 1.6;
        margin-bottom: 2rem;
      }

      .error-actions {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-bottom: 2rem;
      }

      .retry-btn,
      .home-btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: var(--radius-md, 8px);
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s;
      }

      .retry-btn {
        background: var(--color-primary-500, #0b1426);
        color: white;
      }

      .retry-btn:hover {
        background: var(--color-primary-600, #1e3a8a);
        transform: translateY(-2px);
      }

      .home-btn {
        background: var(--color-brand-200, #e5e5ea);
        color: var(--color-brand-800, #1d1d1f);
      }

      .home-btn:hover {
        background: var(--color-brand-300, #d2d2d7);
        transform: translateY(-2px);
      }

      .error-details {
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 1px solid var(--color-brand-200, #e5e5ea);
        text-align: left;
      }

      .error-details summary {
        cursor: pointer;
        color: var(--color-brand-600, #86868b);
        font-size: 0.9rem;
      }

      .error-stack {
        margin: 1rem 0;
        padding: 1rem;
        background: var(--color-brand-100, #f5f5f7);
        border-radius: var(--radius-sm, 4px);
        font-size: 0.85rem;
        overflow-x: auto;
        white-space: pre-wrap;
        color: var(--color-danger-600, #d32f2f);
      }

      .error-component,
      .error-time {
        font-size: 0.8rem;
        color: var(--color-brand-500, #6e6e73);
        margin: 0.25rem 0;
      }

      @media (max-width: 768px) {
        .error-container {
          padding: 2rem 1.5rem;
        }

        .error-actions {
          flex-direction: column;
          align-items: center;
        }

        .retry-btn,
        .home-btn {
          width: 100%;
          max-width: 280px;
        }
      }
    `,
  ],
})
export class ErrorBoundaryComponent implements OnInit, OnDestroy {
  @Input() errorTitle?: string;
  @Input() errorMessage?: string;
  @Input() retryable: boolean = true;
  @Input() fallback?: () => void;

  hasError = false;
  errorInfo: ErrorInfo | null = null;
  isDevelopment = false;

  private destroy$ = new Subject<void>();

  constructor(private router: Router) {}

  ngOnInit(): void {
    // 检测是否为开发环境
    this.isDevelopment = !this.isProduction();

    // 监听路由错误
    this.router.events
      .pipe(
        takeUntil(this.destroy$),
        filter((e): e is NavigationError => e instanceof NavigationError)
      )
      .subscribe((error) => {
        this.handleError({
          error: error.error,
          componentName: 'Router',
          stack: error.error?.stack,
          timestamp: new Date(),
        });
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  handleError(errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', errorInfo);

    this.hasError = true;
    this.errorInfo = errorInfo;

    // 上报错误到监控服务（生产环境）
    if (this.isProduction() && this.errorInfo) {
      this.reportError(this.errorInfo);
    }
  }

  retry(): void {
    if (this.fallback) {
      this.fallback();
    } else {
      // 重新加载当前路由
      this.router.navigate([], {
        queryParams: { _t: Date.now() },
        replaceUrl: true,
      });
    }
    this.reset();
  }

  goHome(): void {
    this.router.navigate(['/']);
    this.reset();
  }

  reset(): void {
    this.hasError = false;
    this.errorInfo = null;
  }

  private isProduction(): boolean {
    return (
      process.env['NODE_ENV'] === 'production' ||
      process.env['NG_ENV'] === 'production' ||
      !window.location.hostname.includes('localhost')
    );
  }

  private reportError(errorInfo: ErrorInfo): void {
    // 实现错误上报逻辑（如Sentry、自定义监控等）
    // console.error('Reporting error:', errorInfo);
  }
}

/**
 * 错误处理守卫 - 在路由级别捕获错误
 */
@Injectable({
  providedIn: 'root',
})
export class ErrorBoundaryGuard {
  constructor(private router: Router) {}

  canActivate(): boolean {
    // 在这里可以实现路由级别的错误处理逻辑
    return true;
  }
}
