/**
 * 模块加载遮罩组件
 *
 * 全屏半透明遮罩，显示模块加载进度。
 * 当模块加载时间超过阈值时，显示重试选项。
 *
 * 用法：
 * <app-module-loading-overlay
 *   [visible]="isLoading"
 *   moduleName="AI 服务"
 *   (retry)="onRetry()"
 *   (cancel)="onCancel()">
 * </app-module-loading-overlay>
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-module-loading-overlay',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="overlay" *ngIf="visible" @fadeIn>
      <div class="overlay-content">
        <!-- 加载动画 -->
        <div class="spinner-container" *ngIf="!showTimeout">
          <div class="spinner"></div>
          <h3 class="module-name">正在启动 {{ moduleName }}...</h3>
          <p class="hint">预计需要几秒钟</p>
          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="progress"></div>
          </div>
        </div>

        <!-- 超时提示 -->
        <div class="timeout-container" *ngIf="showTimeout">
          <mat-icon class="timeout-icon">warning</mat-icon>
          <h3>{{ moduleName }} 加载时间较长</h3>
          <p>请检查后端服务是否正常运行</p>
          <div class="actions">
            <button class="btn-retry" (click)="retry.emit()">
              重试
            </button>
            <button class="btn-cancel" (click)="cancel.emit()">
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      backdrop-filter: blur(4px);
    }

    .overlay-content {
      background: #fff;
      border-radius: 16px;
      padding: 40px;
      text-align: center;
      max-width: 400px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .spinner-container {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .spinner {
      width: 48px;
      height: 48px;
      border: 4px solid #e0e0e0;
      border-top: 4px solid #1976d2;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 16px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .module-name {
      margin: 0 0 8px;
      font-size: 18px;
      color: #333;
    }

    .hint {
      color: #666;
      font-size: 14px;
      margin: 0 0 16px;
    }

    .progress-bar {
      width: 100%;
      height: 4px;
      background: #e0e0e0;
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: #1976d2;
      transition: width 0.3s ease;
      border-radius: 2px;
    }

    .timeout-container {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .timeout-icon {
      font-size: 48px;
      color: #ff9800;
      margin-bottom: 16px;
    }

    .timeout-container h3 {
      margin: 0 0 8px;
      color: #333;
    }

    .timeout-container p {
      color: #666;
      margin: 0 0 24px;
    }

    .actions {
      display: flex;
      gap: 12px;
    }

    .btn-retry {
      padding: 10px 24px;
      background: #1976d2;
      color: #fff;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
    }

    .btn-cancel {
      padding: 10px 24px;
      background: transparent;
      color: #666;
      border: 1px solid #ccc;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
    }

    .btn-retry:hover { background: #1565c0; }
    .btn-cancel:hover { background: #f5f5f5; }
  `],
})
export class ModuleLoadingOverlayComponent implements OnChanges, OnDestroy {
  @Input() visible = false;
  @Input() moduleName = '';
  @Output() retry = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  showTimeout = false;
  progress = 0;

  private progressTimer: ReturnType<typeof setInterval> | null = null;
  private timeoutTimer: ReturnType<typeof setTimeout> | null = null;

  /** 超时阈值（毫秒） */
  private readonly TIMEOUT_MS = 10_000;
  private readonly PROGRESS_INTERVAL_MS = 200;

  ngOnChanges(): void {
    this.cleanup();

    if (this.visible) {
      this.startProgress();
      this.startTimeout();
    }
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  private startProgress(): void {
    this.progress = 0;
    this.showTimeout = false;

    this.progressTimer = setInterval(() => {
      // 模拟进度：前 80% 快速，后 20% 缓慢
      if (this.progress < 80) {
        this.progress += 4;
      } else if (this.progress < 95) {
        this.progress += 0.5;
      }
    }, this.PROGRESS_INTERVAL_MS);
  }

  private startTimeout(): void {
    this.timeoutTimer = setTimeout(() => {
      this.showTimeout = true;
      if (this.progressTimer) {
        clearInterval(this.progressTimer);
        this.progressTimer = null;
      }
    }, this.TIMEOUT_MS);
  }

  private cleanup(): void {
    if (this.progressTimer) {
      clearInterval(this.progressTimer);
      this.progressTimer = null;
    }
    if (this.timeoutTimer) {
      clearTimeout(this.timeoutTimer);
      this.timeoutTimer = null;
    }
    this.progress = 0;
    this.showTimeout = false;
  }
}
