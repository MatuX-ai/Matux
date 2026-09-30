/**
 * 演示数据横幅
 *
 * 当页面渲染的是 mock/演示数据时(未接通真实后端),顶部显示醒目提示
 * 用于:
 * 1. 提醒开发者当前模块未完成对接
 * 2. 避免用户误以为是真实数据
 *
 * 用法:
 *   <app-mock-mode-banner
 *     [module]="'学生仪表盘'"
 *     [note]="'WebSocket 进度同步与真实任务事件未关联'"
 *   ></app-mock-mode-banner>
 */

import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-mock-mode-banner',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  template: `
    <div
      class="mock-banner"
      role="status"
      aria-live="polite"
      [matTooltip]="'此页面渲染的是演示数据，仅用于预览 UI 与交互'"
    >
      <mat-icon class="banner-icon">science</mat-icon>
      <div class="banner-content">
        <span class="banner-title">{{ module }} 当前为演示数据</span>
        <span class="banner-note" *ngIf="note">· {{ note }}</span>
      </div>
    </div>
  `,
  styles: [
    `
      .mock-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        margin-bottom: 16px;
        border: 1px dashed var(--matux-color-warning, #f59e0b);
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.06), rgba(245, 158, 11, 0.03));
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
      }

      .banner-icon {
        color: var(--matux-color-warning, #f59e0b);
        font-size: 20px;
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }

      .banner-content {
        flex: 1;
        min-width: 0;
      }

      .banner-title {
        font-weight: 600;
        color: var(--matux-color-warning-dark, #b45309);
      }

      .banner-note {
        margin-left: 4px;
        color: var(--matux-color-text-secondary, #64748b);
      }

      @media (max-width: 640px) {
        .mock-banner {
          padding: 8px 12px;
          font-size: 12px;
        }
      }
    `,
  ],
})
export class MockModeBannerComponent {
  @Input() module = '此模块';
  @Input() note = '';
}
