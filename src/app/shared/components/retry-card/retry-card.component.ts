/**
 * 通用错误重试卡片
 *
 * 用于 API 调用失败场景：替代无限 loading 占位，提供明确的错误提示与一键重试按钮。
 * 避免用户在数据加载失败时面对空白 / 转圈无反馈。
 *
 * 用法（示例）：
 * ```html
 * <app-retry-card
 *   *ngIf="loadError"
 *   title="加载课程失败"
 *   message="网络异常或后端服务暂不可用，请稍后重试"
 *   (retry)="loadCourses(userId)"
 * ></app-retry-card>
 * ```
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-retry-card',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div class="retry-card-container" role="alert">
      <div class="retry-card">
        <div class="icon-wrap">
          <mat-icon>{{ icon }}</mat-icon>
        </div>
        <h2 class="title">{{ title }}</h2>
        <p class="message" *ngIf="message">{{ message }}</p>
        <p class="detail" *ngIf="detail">{{ detail }}</p>
        <div class="actions">
          <button mat-flat-button color="primary" (click)="onRetry()" [disabled]="retrying">
            <mat-icon>{{ retrying ? 'hourglass_empty' : 'refresh' }}</mat-icon>
            {{ retrying ? '重试中…' : '重试' }}
          </button>
          <button
            mat-stroked-button
            *ngIf="showHomeButton"
            [attr.aria-label]="'返回首页'"
            (click)="home.emit()"
          >
            <mat-icon>home</mat-icon>
            返回首页
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .retry-card-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 320px;
        padding: 24px;
      }

      .retry-card {
        max-width: 460px;
        width: 100%;
        padding: 40px 28px;
        text-align: center;
        border-radius: 16px;
        background: var(--matux-color-surface, #ffffff);
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.18);
        background: linear-gradient(
          180deg,
          rgba(239, 68, 68, 0.04) 0%,
          rgba(239, 68, 68, 0) 100%
        );
      }

      .icon-wrap {
        width: 64px;
        height: 64px;
        margin: 0 auto 20px;
        border-radius: 50%;
        background: rgba(239, 68, 68, 0.12);
        color: #dc2626;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .icon-wrap mat-icon {
        font-size: 36px;
        width: 36px;
        height: 36px;
      }

      .title {
        margin: 0 0 12px;
        font-size: 18px;
        font-weight: 600;
        color: var(--matux-color-text-primary, #0f172a);
      }

      .message {
        margin: 0 0 8px;
        font-size: 14px;
        line-height: 1.6;
        color: var(--matux-color-text-secondary, #475569);
      }

      .detail {
        margin: 0 0 24px;
        font-size: 12px;
        line-height: 1.5;
        color: var(--matux-color-text-disabled, #94a3b8);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        word-break: break-all;
      }

      .actions {
        display: flex;
        gap: 12px;
        justify-content: center;
        flex-wrap: wrap;
      }

      .actions mat-icon {
        margin-right: 4px;
        vertical-align: middle;
      }
    `,
  ],
})
export class RetryCardComponent {
  /** 错误标题（必填） */
  @Input() title = '加载失败';
  /** 错误简短描述（选填） */
  @Input() message: string | null = '数据加载失败，请稍后重试';
  /** 技术详情（如 HTTP 状态码 / 错误摘要）（选填） */
  @Input() detail: string | null = null;
  /** Material 图标名（默认 cloud_off） */
  @Input() icon = 'cloud_off';
  /** 是否正在重试（按钮显示 hourglass） */
  @Input() retrying = false;
  /** 是否显示"返回首页"按钮 */
  @Input() showHomeButton = false;

  /** 点击重试时触发，由父组件订阅 */
  @Output() retry = new EventEmitter<void>();
  /** 点击"返回首页"时触发 */
  @Output() home = new EventEmitter<void>();

  onRetry(): void {
    if (this.retrying) {
      return;
    }
    this.retry.emit();
  }
}