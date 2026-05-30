/**
 * 加载状态组件 - 统一的加载指示器
 * 支持多种加载状态：spinner、skeleton、progress
 */

import { CommonModule } from '@angular/common';
import { Component, Injectable, Input, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { finalize } from 'rxjs/operators';

export type LoadingType = 'spinner' | 'skeleton' | 'progress' | 'dots';
export type LoadingSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-loading',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="loading-container" [class.fullscreen]="fullscreen" [class.overlay]="overlay">
      <!-- Spinner 加载器 -->
      <div *ngIf="type === 'spinner'" class="spinner" [class]="size">
        <div class="spinner-circle"></div>
      </div>

      <!-- Dots 加载器 -->
      <div *ngIf="type === 'dots'" class="dots" [class]="size">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>

      <!-- Progress 进度条 -->
      <div *ngIf="type === 'progress'" class="progress" [class]="size">
        <div class="progress-bar" [style.width.%]="value"></div>
      </div>

      <!-- Skeleton 骨架屏 -->
      <div *ngIf="type === 'skeleton'" class="skeleton" [class]="size">
        <div class="skeleton-line"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>

      <!-- 加载文本 -->
      <div class="loading-text" *ngIf="text">{{ text }}</div>
    </div>
  `,
  styles: [
    `
      .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        color: var(--color-brand-400, #6e6e73);
      }

      .loading-container.fullscreen {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        z-index: 9999;
      }

      .loading-container.overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        z-index: 10;
      }

      /* Spinner 样式 */
      .spinner {
        display: inline-block;
        position: relative;
      }

      .spinner.sm {
        width: 20px;
        height: 20px;
      }

      .spinner.md {
        width: 40px;
        height: 40px;
      }

      .spinner.lg {
        width: 60px;
        height: 60px;
      }

      .spinner-circle {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 3px solid rgba(11, 20, 38, 0.1);
        border-top: 3px solid var(--gradient-primary-start, #0b1426);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      /* Dots 样式 */
      .dots {
        display: flex;
        gap: 8px;
      }

      .dots.sm .dot {
        width: 6px;
        height: 6px;
      }

      .dots.md .dot {
        width: 10px;
        height: 10px;
      }

      .dots.lg .dot {
        width: 14px;
        height: 14px;
      }

      .dot {
        background: var(--gradient-primary-start, #0b1426);
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
      }

      .dot:nth-child(1) {
        animation-delay: -0.32s;
      }
      .dot:nth-child(2) {
        animation-delay: -0.16s;
      }

      /* Progress 样式 */
      .progress {
        width: 100%;
        background: var(--color-brand-200, #e5e5ea);
        border-radius: var(--radius-sm, 4px);
        overflow: hidden;
      }

      .progress.sm {
        height: 4px;
        max-width: 100px;
      }

      .progress.md {
        height: 8px;
        max-width: 200px;
      }

      .progress.lg {
        height: 12px;
        max-width: 300px;
      }

      .progress-bar {
        height: 100%;
        background: linear-gradient(
          135deg,
          var(--gradient-primary-start) 0%,
          var(--gradient-primary-end) 100%
        );
        transition: width 0.3s ease;
      }

      /* Skeleton 样式 */
      .skeleton {
        width: 100%;
      }

      .skeleton.sm {
        max-width: 150px;
      }

      .skeleton.md {
        max-width: 250px;
      }

      .skeleton.lg {
        max-width: 350px;
      }

      .skeleton-line {
        height: 12px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        margin-bottom: 12px;
        border-radius: var(--radius-sm, 4px);
      }

      .skeleton-line.short {
        width: 60%;
      }

      .skeleton-line:last-child {
        margin-bottom: 0;
      }

      /* 加载文本 */
      .loading-text {
        margin-top: 1rem;
        font-size: 0.9rem;
        color: var(--color-brand-500, #86868b);
      }

      /* 动画 */
      @keyframes spin {
        0% {
          transform: rotate(0deg);
        }
        100% {
          transform: rotate(360deg);
        }
      }

      @keyframes bounce {
        0%,
        80%,
        100% {
          transform: scale(0);
          opacity: 0.5;
        }
        40% {
          transform: scale(1);
          opacity: 1;
        }
      }

      @keyframes loading {
        0% {
          background-position: 200% 0;
        }
        100% {
          background-position: -200% 0;
        }
      }

      @media (max-width: 768px) {
        .loading-container {
          padding: 1rem;
        }
      }
    `,
  ],
})
export class LoadingComponent implements OnInit {
  @Input() type: LoadingType = 'spinner';
  @Input() size: LoadingSize = 'md';
  @Input() text?: string;
  @Input() value: number = 0; // for progress type
  @Input() fullscreen: boolean = false;
  @Input() overlay: boolean = false;

  ngOnInit(): void {
    // 验证progress类型的值范围
    if (this.type === 'progress') {
      this.value = Math.max(0, Math.min(100, this.value));
    }
  }
}

/**
 * 加载状态服务 - 全局加载状态管理
 */
@Injectable({
  providedIn: 'root',
})
export class LoadingService {
  private loadingSubject = new Subject<boolean>();
  private loadingCount = 0;

  get loading$() {
    return this.loadingSubject.asObservable();
  }

  show(): void {
    this.loadingCount++;
    this.loadingSubject.next(true);
  }

  hide(): void {
    this.loadingCount = Math.max(0, this.loadingCount - 1);
    if (this.loadingCount === 0) {
      this.loadingSubject.next(false);
    }
  }

  reset(): void {
    this.loadingCount = 0;
    this.loadingSubject.next(false);
  }

  wrap<T>(promise: Promise<T>): Promise<T> {
    this.show();
    return promise.finally(() => this.hide());
  }

  wrapObservable<T>(observable: any): any {
    this.show();
    return observable.pipe(finalize(() => this.hide()));
  }
}
